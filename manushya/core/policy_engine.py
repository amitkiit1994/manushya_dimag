"""
Production-grade policy engine with JSON-based rules and advanced authorization
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.core.exceptions import AccessDeniedError, PolicyError
from manushya.db.models import Identity, Policy

logger = logging.getLogger(
    __name__
)


class PolicyEngine:
    """Production-grade policy engine with JSON-based rules and advanced authorization."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_permission(
        self,
        identity: Identity,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """
        Check if identity has permission for action on resource.
        Args:
            identity: Identity making the request
            action: Action to perform (create, read, update, delete, etc.)
            resource_type: Type of resource (memory, identity, policy, etc.)
            resource_id: Specific resource ID (optional)
            context: Additional context for policy evaluation
        Returns:
            True if permission granted, False otherwise
        """
        try:
            # Get applicable policies
            policies = await self._get_applicable_policies(
                identity, action, resource_type, context
            )
            if not policies:
                # Default deny if no policies found
                logger.warning(f"No policies found for {action} on {resource_type}")
                return False
            # Evaluate policies
            for policy in policies:
                if await self._evaluate_policy(
                    policy, identity, action, resource_type, resource_id, context
                ):
                    logger.info(
                        f"Policy {policy.id} granted {action} on {resource_type}"
                    )
                    return True
            logger.warning(f"All policies denied {action} on {resource_type}")
            return False
        except Exception as e:
            logger.error(f"Policy evaluation failed: {e}")
            return False

    async def check_memory_access(
        self,
        identity: Identity,
        action: str,
        memory_type: str | None = None,
        memory_metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Check memory access permissions with detailed error handling.
        Args:
            identity: Identity requesting access
            action: Action to perform (create, read, update, delete)
            memory_type: Type of memory (optional)
            memory_metadata: Memory metadata for context (optional)
        Raises:
            AccessDeniedError: If access is denied
        """
        context = {
            "memory_type": memory_type,
            "memory_metadata": memory_metadata or {},
            "timestamp": datetime.now(UTC).isoformat(),
        }
        has_permission = await self.check_permission(
            identity, action, "memory", context=context
        )
        if not has_permission:
            raise AccessDeniedError(
                f"Access denied for {action} on memory",
                details={
                    "identity_id": str(identity.id),
                    "action": action,
                    "resource_type": "memory",
                    "memory_type": memory_type,
                },
            )

    async def check_identity_access(
        self, identity: Identity, action: str, target_identity_id: str | None = None
    ) -> None:
        """
        Check identity management permissions.
        Args:
            identity: Identity making the request
            action: Action to perform
            target_identity_id: Target identity ID (optional)
        Raises:
            AccessDeniedError: If access is denied
        """
        context = {
            "target_identity_id": target_identity_id,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        has_permission = await self.check_permission(
            identity, action, "identity", target_identity_id, context
        )
        if not has_permission:
            raise AccessDeniedError(
                f"Access denied for {action} on identity",
                details={
                    "identity_id": str(identity.id),
                    "action": action,
                    "resource_type": "identity",
                    "target_identity_id": target_identity_id,
                },
            )

    async def check_policy_access(
        self, identity: Identity, action: str, policy_id: str | None = None
    ) -> None:
        """
        Check policy management permissions.
        Args:
            identity: Identity making the request
            action: Action to perform
            policy_id: Target policy ID (optional)
        Raises:
            AccessDeniedError: If access is denied
        """
        context = {
            "policy_id": policy_id,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        has_permission = await self.check_permission(
            identity, action, "policy", policy_id, context
        )
        if not has_permission:
            raise AccessDeniedError(
                f"Access denied for {action} on policy",
                details={
                    "identity_id": str(identity.id),
                    "action": action,
                    "resource_type": "policy",
                    "policy_id": policy_id,
                },
            )

    async def _get_applicable_policies(
        self,
        identity: Identity,
        action: str,
        resource_type: str,
        context: dict[str, Any] | None = None,
    ) -> list[Policy]:
        """Get applicable policies for the request."""
        # Build query for applicable policies
        stmt = select(Policy).where(
            and_(
                Policy.tenant_id == identity.tenant_id,
                Policy.is_active,
                Policy.role == identity.role,
            )
        )
        result = await self.db.execute(stmt)
        policies = result.scalars().all()
        # Sort by priority (highest first)
        policies = sorted(policies, key=lambda p: p.priority or 0, reverse=True)
        logger.debug(
            f"Found {len(policies)} applicable policies for {action} on {resource_type}"
        )
        return policies

    async def _evaluate_policy(
        self,
        policy: Policy,
        identity: Identity,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """
        Evaluate a single policy against the request.
        Args:
            policy: Policy to evaluate
            identity: Identity making the request
            action: Action being performed
            resource_type: Type of resource
            resource_id: Resource ID (optional)
            context: Additional context
        Returns:
            True if policy allows the action
        """
        try:
            # Parse policy rules
            rules = (
                policy.rule
                if isinstance(policy.rule, dict)
                else json.loads(policy.rule)
            )
            # --- ACTION/RESOURCE MATCHING ---
            # Check if action matches
            actions = rules.get("actions", [])
            if isinstance(actions, str):
                actions = [actions]
            if "*" not in actions and action not in actions:
                logger.debug(f"Policy {policy.id} does not allow action {action}")
                return False
            # Check if resource matches
            resource = rules.get("resource", "*")
            if resource != "*" and resource_type != resource:
                logger.debug(f"Policy {policy.id} does not allow resource {resource_type}")
                return False
            # Check conditions
            if not await self._evaluate_conditions(
                rules.get("conditions", {}), identity, context
            ):
                logger.debug(f"Policy {policy.id} conditions not met")
                return False
            # Check effect
            effect = rules.get("effect", "deny")
            if effect.lower() == "allow":
                logger.debug(f"Policy {policy.id} allows action")
                return True
            else:
                logger.debug(f"Policy {policy.id} denies action")
                return False
        except Exception as e:
            logger.error(f"Policy evaluation failed for policy {policy.id}: {e}")
            return False

    async def _evaluate_conditions(
        self,
        conditions: dict[str, Any],
        identity: Identity,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """
        Evaluate policy conditions.
        Args:
            conditions: Policy conditions
            identity: Identity to evaluate against
            context: Additional context
        Returns:
            True if all conditions are met
        """
        if not conditions:
            return True
        context = context or {}
        # Role-based conditions
        if "roles" in conditions:
            allowed_roles = conditions["roles"]
            if identity.role not in allowed_roles:
                logger.debug(
                    f"Role {identity.role} not in allowed roles {allowed_roles}"
                )
                return False
        # Time-based conditions
        if "time_restrictions" in conditions:
            if not await self._evaluate_time_restrictions(
                conditions["time_restrictions"]
            ):
                logger.debug("Time restrictions not met")
                return False
        # IP-based conditions
        if "ip_restrictions" in conditions:
            client_ip = context.get("client_ip")
            if client_ip and not await self._evaluate_ip_restrictions(
                conditions["ip_restrictions"], client_ip
            ):
                logger.debug(f"IP {client_ip} not in allowed ranges")
                return False
        # Resource-based conditions
        if "resource_conditions" in conditions:
            if not await self._evaluate_resource_conditions(
                conditions["resource_conditions"], context
            ):
                logger.debug("Resource conditions not met")
                return False
        # Custom conditions
        if "custom_conditions" in conditions:
            if not await self._evaluate_custom_conditions(
                conditions["custom_conditions"], identity, context
            ):
                logger.debug("Custom conditions not met")
                return False
        return True

    async def _evaluate_time_restrictions(self, restrictions: dict[str, Any]) -> bool:
        """Evaluate time-based restrictions."""
        now = datetime.now(UTC)
        # Check time of day
        if "time_of_day" in restrictions:
            current_hour = now.hour
            allowed_hours = restrictions["time_of_day"]
            if current_hour not in allowed_hours:
                return False
        # Check days of week
        if "days_of_week" in restrictions:
            current_day = now.weekday()  # 0 = Monday
            allowed_days = restrictions["days_of_week"]
            if current_day not in allowed_days:
                return False
        # Check date range
        if "date_range" in restrictions:
            date_range = restrictions["date_range"]
            start_date = datetime.fromisoformat(date_range["start"])
            end_date = datetime.fromisoformat(date_range["end"])
            if not (start_date <= now <= end_date):
                return False
        return True

    async def _evaluate_ip_restrictions(
        self, restrictions: dict[str, Any], client_ip: str
    ) -> bool:
        """Evaluate IP-based restrictions."""
        allowed_ips = restrictions.get("allowed_ips", [])
        allowed_ranges = restrictions.get("allowed_ranges", [])
        # Check exact IP
        if client_ip in allowed_ips:
            return True
        # Check IP ranges
        import ipaddress

        try:
            client_ip_obj = ipaddress.ip_address(client_ip)
            for ip_range in allowed_ranges:
                network = ipaddress.ip_network(ip_range)
                if client_ip_obj in network:
                    return True
        except ValueError:
            logger.warning(f"Invalid IP address: {client_ip}")
            return False
        return False

    async def _evaluate_resource_conditions(
        self, conditions: dict[str, Any], context: dict[str, Any]
    ) -> bool:
        """Evaluate resource-based conditions."""
        # Memory type restrictions
        if "memory_types" in conditions:
            memory_type = context.get("memory_type")
            if memory_type and memory_type not in conditions["memory_types"]:
                return False
        # Metadata restrictions
        if "metadata_requirements" in conditions:
            metadata = context.get("memory_metadata", {})
            requirements = conditions["metadata_requirements"]
            for key, value in requirements.items():
                if metadata.get(key) != value:
                    return False
        return True

    async def _evaluate_custom_conditions(
        self, conditions: dict[str, Any], identity: Identity, context: dict[str, Any]
    ) -> bool:
        """Evaluate custom conditions."""
        # Identity claims conditions
        if "identity_claims" in conditions:
            identity_claims = identity.claims or {}
            required_claims = conditions["identity_claims"]
            for key, value in required_claims.items():
                if identity_claims.get(key) != value:
                    return False
        # Tenant-specific conditions
        if "tenant_conditions" in conditions:
            conditions["tenant_conditions"]
            # Add tenant-specific logic here
        return True

    async def create_policy(
        self,
        tenant_id: str,
        role: str,
        rule: dict[str, Any],
        description: str,
        priority: int = 0,
        is_active: bool = True,
    ) -> Policy:
        """
        Create a new policy.
        Args:
            tenant_id: Tenant ID
            role: Role this policy applies to
            rule: Policy rule in JSON format
            description: Policy description
            priority: Policy priority (higher = more important)
            is_active: Whether policy is active
        Returns:
            Created policy
        """
        policy = Policy(
            tenant_id=tenant_id,
            role=role,
            rule=rule,
            description=description,
            priority=priority,
            is_active=is_active,
        )
        self.db.add(policy)
        await self.db.commit()
        await self.db.refresh(policy)
        logger.info(f"Created policy {policy.id} for tenant {tenant_id}")
        return policy

    async def get_policies(
        self,
        tenant_id: str,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> list[Policy]:
        """Get policies for a tenant with optional filtering."""
        stmt = select(Policy).where(Policy.tenant_id == tenant_id)
        if role:
            stmt = stmt.where(Policy.role == role)
        if is_active is not None:
            stmt = stmt.where(Policy.is_active == is_active)
        stmt = stmt.order_by(Policy.priority.desc(), Policy.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_policy(self, policy_id: str, updates: dict[str, Any]) -> Policy:
        """Update an existing policy."""
        stmt = select(Policy).where(Policy.id == policy_id)
        result = await self.db.execute(stmt)
        policy = result.scalar_one_or_none()
        if not policy:
            raise PolicyError(f"Policy {policy_id} not found")
        # Update fields
        for field, value in updates.items():
            if hasattr(policy, field):
                setattr(policy, field, value)
        policy.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(policy)
        logger.info(f"Updated policy {policy_id}")
        return policy

    async def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy (soft delete)."""
        stmt = select(Policy).where(Policy.id == policy_id)
        result = await self.db.execute(stmt)
        policy = result.scalar_one_or_none()
        if not policy:
            return False
        policy.is_active = False
        await self.db.commit()
        logger.info(f"Deleted policy {policy_id}")
        return True
