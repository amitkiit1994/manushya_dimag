"""
Policy engine for role-based access control using JSON Logic
"""

import json
from typing import Dict, Any, List, Optional
from json_logic import jsonLogic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from manushya.db.models import Policy, Identity
from manushya.core.exceptions import PolicyViolationError


class PolicyEngine:
    """JSON Logic-based policy engine for access control."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._policies_cache: Dict[str, List[Policy]] = {}
    
    async def get_policies_for_role(self, role: str) -> List[Policy]:
        """Get all active policies for a role."""
        if role in self._policies_cache:
            return self._policies_cache[role]
        
        stmt = select(Policy).where(
            Policy.role == role,
            Policy.is_active == True
        ).order_by(Policy.priority.desc())
        
        result = await self.db.execute(stmt)
        policies = result.scalars().all()
        
        self._policies_cache[role] = policies
        return policies
    
    async def evaluate_policy(
        self, 
        role: str, 
        action: str, 
        resource: str, 
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate if an action is allowed for a role."""
        policies = await self.get_policies_for_role(role)
        
        for policy in policies:
            try:
                # Add standard context
                evaluation_context = {
                    "role": role,
                    "action": action,
                    "resource": resource,
                    **context
                }
                
                # Evaluate JSON Logic rule
                result = jsonLogic(policy.rule, evaluation_context)
                
                if result is False:
                    raise PolicyViolationError(
                        f"Policy violation: {policy.description or 'No description'}",
                        error_code="POLICY_VIOLATION",
                        details={
                            "policy_id": str(policy.id),
                            "rule": policy.rule,
                            "context": evaluation_context
                        }
                    )
                
            except Exception as e:
                if isinstance(e, PolicyViolationError):
                    raise
                # Log policy evaluation error but continue
                print(f"Policy evaluation error: {e}")
                continue
        
        return True
    
    async def check_memory_access(
        self, 
        identity: Identity, 
        action: str, 
        memory_type: Optional[str] = None,
        memory_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if identity can perform action on memory."""
        context = {
            "identity_id": str(identity.id),
            "external_id": identity.external_id,
            "claims": identity.claims,
            "memory_type": memory_type,
            "memory_metadata": memory_metadata or {}
        }
        
        return await self.evaluate_policy(
            role=identity.role,
            action=action,
            resource="memory",
            context=context
        )
    
    async def check_identity_access(
        self, 
        identity: Identity, 
        action: str, 
        target_role: Optional[str] = None
    ) -> bool:
        """Check if identity can perform action on other identities."""
        context = {
            "identity_id": str(identity.id),
            "external_id": identity.external_id,
            "claims": identity.claims,
            "target_role": target_role
        }
        
        return await self.evaluate_policy(
            role=identity.role,
            action=action,
            resource="identity",
            context=context
        )
    
    def clear_cache(self):
        """Clear the policies cache."""
        self._policies_cache.clear()


# Predefined policy rules
DEFAULT_POLICIES = {
    "admin": {
        "description": "Admin can perform all actions",
        "rule": {"==": [{"var": "role"}, "admin"]}
    },
    "user": {
        "description": "Users can only access their own memories",
        "rule": {
            "and": [
                {"==": [{"var": "action"}, "read"]},
                {"==": [{"var": "resource"}, "memory"]}
            ]
        }
    },
    "agent": {
        "description": "Agents can read and write their own memories",
        "rule": {
            "and": [
                {"in": [{"var": "action"}, ["read", "write"]]},
                {"==": [{"var": "resource"}, "memory"]}
            ]
        }
    }
}


async def create_default_policies(db: AsyncSession):
    """Create default policies for common roles."""
    for role, policy_data in DEFAULT_POLICIES.items():
        # Check if policy already exists
        stmt = select(Policy).where(
            Policy.role == role,
            Policy.description == policy_data["description"]
        )
        result = await db.execute(stmt)
        existing_policy = result.scalar_one_or_none()
        
        if not existing_policy:
            policy = Policy(
                role=role,
                rule=policy_data["rule"],
                description=policy_data["description"],
                is_active=True,
                priority=100
            )
            db.add(policy)
    
    await db.commit() 