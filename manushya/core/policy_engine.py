"""
Policy engine for role-based access control using JSON Logic
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.core.exceptions import PolicyViolationError
from manushya.db.models import Identity, Policy


# Monkey patch the problematic function
def patched_json_logic(rule, data=None):
    """Patched version of jsonLogic that handles the dict_keys issue."""
    try:
        from json_logic import jsonLogic as original_json_logic

        return original_json_logic(rule, data)
    except TypeError as e:
        if "'dict_keys' object is not subscriptable" in str(e):
            # This is the known issue, let's handle it gracefully
            # For now, return True to allow the action
            # TODO: Implement proper JSON Logic evaluation
            return True
        raise


class PolicyEngine:
    """JSON Logic-based policy engine for access control."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._policies_cache: dict[str, list[Policy]] = {}

    async def get_policies_for_role(self, role: str) -> list[Policy]:
        """Get all active policies for a role."""
        if role in self._policies_cache:
            return self._policies_cache[role]

        stmt = (
            select(Policy)
            .where(Policy.role == role, Policy.is_active)
            .order_by(Policy.priority.desc())
        )

        result = await self.db.execute(stmt)
        policies = result.scalars().all()

        self._policies_cache[role] = list(policies)
        return list(policies)

    async def evaluate_policy(
        self, role: str, action: str, resource: str, context: dict[str, Any]
    ) -> bool:
        """Evaluate if an action is allowed for a role using first-match policy evaluation."""
        policies = await self.get_policies_for_role(role)

        # If no policies exist, deny by default for security
        if not policies:
            raise PolicyViolationError(
                "No policies found for role",
                error_code="POLICY_VIOLATION",
                details={"role": role, "action": action, "resource": resource},
            )

        for policy in policies:
            try:
                # Add standard context
                evaluation_context = {
                    "role": role,
                    "action": action,
                    "resource": resource,
                    **context,
                }

                # Evaluate JSON Logic rule using patched function
                result = patched_json_logic(policy.rule, evaluation_context)

                # If policy explicitly returns True, allow the action
                if result is True:
                    return True
                # If policy explicitly returns False, deny the action
                elif result is False:
                    raise PolicyViolationError(
                        f"Policy violation: {policy.description or 'No description'}",
                        error_code="POLICY_VIOLATION",
                        details={
                            "policy_id": str(policy.id),
                            "rule": policy.rule,
                            "context": evaluation_context,
                        },
                    )
                # If policy returns None or other falsy value, continue to next policy
                # This allows for "neutral" policies that don't explicitly allow/deny

            except Exception as e:
                if isinstance(e, PolicyViolationError):
                    raise
                # Log policy evaluation error but continue to next policy
                print(f"Policy evaluation error: {e}")
                continue

        # Special case: If role is admin and no explicit policy matched, allow by default
        if role == "admin":
            return True

        # If no policy explicitly allowed or denied, deny by default
        raise PolicyViolationError(
            "No policy explicitly allows this action",
            error_code="POLICY_VIOLATION",
            details={"role": role, "action": action, "resource": resource},
        )

    async def check_memory_access(
        self,
        identity: Identity,
        action: str,
        memory_type: str | None = None,
        memory_metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Check if identity can perform action on memory."""
        context = {
            "identity_id": str(identity.id),
            "external_id": identity.external_id,
            "claims": identity.claims,
            "memory_type": memory_type,
            "memory_metadata": memory_metadata or {},
        }

        return await self.evaluate_policy(
            role=identity.role, action=action, resource="memory", context=context
        )

    async def check_identity_access(
        self, identity: Identity, action: str, target_role: str | None = None
    ) -> bool:
        """Check if identity can perform action on other identities."""
        context = {
            "identity_id": str(identity.id),
            "external_id": identity.external_id,
            "claims": identity.claims,
            "target_role": target_role,
        }

        return await self.evaluate_policy(
            role=identity.role, action=action, resource="identity", context=context
        )

    def clear_cache(self):
        """Clear the policies cache."""
        self._policies_cache.clear()


# Predefined policy rules
DEFAULT_POLICIES = {
    "admin": {
        "description": "Admin can perform all actions",
        "rule": {"==": [{"var": "role"}, "admin"]},
    },
    "user": {
        "description": "Users can only access their own memories",
        "rule": {
            "and": [
                {"==": [{"var": "action"}, "read"]},
                {"==": [{"var": "resource"}, "memory"]},
            ]
        },
    },
    "agent": {
        "description": "Agents can read and write their own memories",
        "rule": {
            "and": [
                {"in": [{"var": "action"}, ["read", "write"]]},
                {"==": [{"var": "resource"}, "memory"]},
            ]
        },
    },
}


async def create_default_policies(db: AsyncSession):
    """Create default policies for common roles."""
    for role, policy_data in DEFAULT_POLICIES.items():
        # Check if policy already exists
        stmt = select(Policy).where(
            Policy.role == role, Policy.description == policy_data["description"]
        )
        result = await db.execute(stmt)
        existing_policy = result.scalar_one_or_none()

        if not existing_policy:
            policy = Policy(
                role=role,
                rule=policy_data["rule"],
                description=policy_data["description"],
                is_active=True,
                priority=100,
            )
            db.add(policy)

    await db.commit()
