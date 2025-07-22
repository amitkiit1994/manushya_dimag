from sdk.python.client import Client
from sdk.python.api.identity.create_identity_v1_identity_post import sync_detailed as create_identity
from sdk.python.api.policy.create_policy_v1_policy_post import sync_detailed as create_policy
from sdk.python.api.memory.create_memory_v1_memory_post import sync_detailed as create_memory
from sdk.python.api.policy.update_policy_v1_policy_policy_id_put import sync_detailed as update_policy
from sdk.python.api.identity.update_current_identity_v1_identity_me_put import sync_detailed as update_identity
from sdk.python.models.identity_create import IdentityCreate
from sdk.python.models.policy_create import PolicyCreate
from sdk.python.models.memory_create import MemoryCreate
from sdk.python.models.policy_update import PolicyUpdate
from sdk.python.models.identity_update import IdentityUpdate
from sdk.python.models.identity_create_claims import IdentityCreateClaims
from sdk.python.models.policy_create_rule import PolicyCreateRule
from sdk.python.models.memory_create_metadata import MemoryCreateMetadata
import uuid

def print_result(label, response):
    print(f"\n--- {label} ---")
    print("Status:", response.status_code)
    print("Parsed:", response.parsed)
    print("Raw:", response.content)

# 1. Create an admin identity (for policy creation)
admin_claims = IdentityCreateClaims()
admin_claims["email"] = f"admin-{uuid.uuid4()}@example.com"
admin_identity_data = IdentityCreate(
    external_id=f"admin-{uuid.uuid4()}",
    role="admin",
    claims=admin_claims
)
unauth_client = Client(base_url="http://localhost:8000")
admin_identity_resp = create_identity(client=unauth_client, body=admin_identity_data)
print_result("Create Admin Identity", admin_identity_resp)
admin_access_token = admin_identity_resp.parsed.access_token
admin_client = Client(base_url="http://localhost:8000", headers={"Authorization": f"Bearer {admin_access_token}"})

# 2. Create a user identity (for memory operations)
user_claims = IdentityCreateClaims()
user_claims["email"] = f"user-{uuid.uuid4()}@example.com"
user_identity_data = IdentityCreate(
    external_id=f"user-{uuid.uuid4()}",
    role="user",
    claims=user_claims
)
user_identity_resp = create_identity(client=unauth_client, body=user_identity_data)
print_result("Create User Identity", user_identity_resp)
user_access_token = user_identity_resp.parsed.access_token
user_client = Client(base_url="http://localhost:8000", headers={"Authorization": f"Bearer {user_access_token}"})

# 3. Create a policy for the user role (as admin)
rule = PolicyCreateRule()
rule["=="] = [{"var": "action"}, "write"]
policy_data = PolicyCreate(
    role="user",
    rule=rule,
    description="Allow write for user role",
    priority=1,
    is_active=True
)
policy_resp = create_policy(client=admin_client, body=policy_data)
print_result("Create Policy", policy_resp)
policy_id = policy_resp.parsed.id

# 4. Create a memory as user (should succeed)
metadata = MemoryCreateMetadata()
metadata["source"] = "sdk-test"
memory_data = MemoryCreate(
    text="Business logic test memory.",
    type_="note",
    metadata=metadata
)
memory_resp = create_memory(client=user_client, body=memory_data)
print_result("Create Memory (should succeed)", memory_resp)

# 5. Deactivate the policy as admin, then try to create a memory as user (should fail)
policy_update = PolicyUpdate(is_active=False)
update_policy(client=admin_client, policy_id=policy_id, body=policy_update)
try:
    memory_resp2 = create_memory(client=user_client, body=memory_data)
    print_result("Create Memory (should fail, policy inactive)", memory_resp2)
except Exception as e:
    print("Expected failure (policy inactive):", e)

# 6. Reactivate policy as admin, deactivate user, try to create memory as user (should fail)
policy_update = PolicyUpdate(is_active=True)
update_policy(client=admin_client, policy_id=policy_id, body=policy_update)
identity_update = IdentityUpdate(is_active=False)
update_identity(client=user_client, body=identity_update)
try:
    memory_resp3 = create_memory(client=user_client, body=memory_data)
    print_result("Create Memory (should fail, user inactive)", memory_resp3)
except Exception as e:
    print("Expected failure (user inactive):", e) 