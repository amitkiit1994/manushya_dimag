# Manushya.ai Python SDK

Official Python SDK for the Manushya.ai API.

## Installation

```bash
pip install -e .
```

## Authentication

The SDK supports Bearer (JWT) authentication. You must pass the access token in the `Authorization` header:

```python
from sdk.python.client import Client
client = Client(base_url="http://localhost:8000", headers={"Authorization": "Bearer <your-access-token>"})
```

## Basic Usage Example

```python
from sdk.python.client import Client
from sdk.python.api.identity.create_identity_v1_identity_post import sync_detailed as create_identity
from sdk.python.models.identity_create import IdentityCreate
from sdk.python.models.identity_create_claims import IdentityCreateClaims

# Create an unauthenticated client for identity creation
client = Client(base_url="http://localhost:8000")
claims = IdentityCreateClaims()
claims["email"] = "user@example.com"
identity_data = IdentityCreate(external_id="user-123", role="user", claims=claims)
identity_resp = create_identity(client=client, body=identity_data)
access_token = identity_resp.parsed.access_token

# Use the access token for authenticated requests
client = Client(base_url="http://localhost:8000", headers={"Authorization": f"Bearer {access_token}"})
```

## Regenerating the SDK

To regenerate the SDK from the latest OpenAPI spec:

1. Ensure your FastAPI app is running and serving the OpenAPI spec at `http://localhost:8000/v1/openapi.json`.
2. Run the SDK generation script from the project root:

```bash
python scripts/generate_sdk.py
```

This will:
- Fetch the latest OpenAPI spec
- Patch it for SDK generation
- Generate the Python SDK in `sdk/python/`

If you want to distribute the SDK to others:
- Zip the `sdk/python/` directory or publish it to a package index.
- Provide this README for installation and usage instructions.

## Advanced Usage

- See the generated `client.py` and `api/` submodules for all available endpoints.
- Use the models in `models/` for request/response payloads.
- For business logic flows, see `test_sdk_business_logic.py` for end-to-end examples.

## Support

For questions or issues, contact the Manushya.ai team or open an issue in the main repository. 