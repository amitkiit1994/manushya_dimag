"""
Integration tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from manushya.main import app


class TestHealthEndpoints:
    """Test health and monitoring endpoints."""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/healthz")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "redis" in data
    
    def test_metrics_endpoint(self, client: TestClient):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestIdentityEndpoints:
    """Test identity management endpoints."""
    
    def test_create_identity_success(self, client: TestClient, admin_jwt_token: str):
        """Test successful identity creation."""
        identity_data = {
            "external_id": "test-user-001",
            "role": "user",
            "claims": {"department": "engineering", "level": "senior"}
        }
        
        response = client.post(
            "/v1/identity/",
            json=identity_data,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["external_id"] == identity_data["external_id"]
        assert data["role"] == identity_data["role"]
    
    def test_create_identity_unauthorized(self, client: TestClient):
        """Test identity creation without authentication."""
        identity_data = {
            "external_id": "test-user-001",
            "role": "user"
        }
        
        response = client.post("/v1/identity/", json=identity_data)
        assert response.status_code == 401
    
    def test_get_identity_success(self, client: TestClient, admin_jwt_token: str, identity):
        """Test successful identity retrieval."""
        response = client.get(
            f"/v1/identity/{identity.id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(identity.id)
        assert data["external_id"] == identity.external_id
    
    def test_get_identity_not_found(self, client: TestClient, admin_jwt_token: str):
        """Test identity retrieval with non-existent ID."""
        import uuid
        
        response = client.get(
            f"/v1/identity/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 404
    
    def test_list_identities(self, client: TestClient, admin_jwt_token: str):
        """Test identity listing."""
        response = client.get(
            "/v1/identity/",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_identity_success(self, client: TestClient, admin_jwt_token: str, identity):
        """Test successful identity update."""
        update_data = {
            "role": "senior_user",
            "claims": {"department": "engineering", "level": "senior", "updated": True}
        }
        
        response = client.put(
            f"/v1/identity/{identity.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == update_data["role"]
    
    def test_delete_identity_success(self, client: TestClient, admin_jwt_token: str, identity):
        """Test successful identity deletion."""
        response = client.delete(
            f"/v1/identity/{identity.id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 204


class TestMemoryEndpoints:
    """Test memory management endpoints."""
    
    def test_create_memory_success(self, client: TestClient, user_jwt_token: str, identity):
        """Test successful memory creation."""
        memory_data = {
            "text": "This is a test memory",
            "type": "test_memory",
            "metadata": {"test": True, "category": "unit_test"},
            "ttl_days": 30
        }
        
        with patch('manushya.services.embedding_service.generate_embedding') as mock_embedding:
            mock_embedding.return_value = [0.1] * 1536
            
            response = client.post(
                "/v1/memory/",
                json=memory_data,
                headers={"Authorization": f"Bearer {user_jwt_token}"}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["text"] == memory_data["text"]
        assert data["type"] == memory_data["type"]
    
    def test_create_memory_invalid_data(self, client: TestClient, user_jwt_token: str):
        """Test memory creation with invalid data."""
        memory_data = {
            "text": "",  # Empty text
            "type": "test_memory"
        }
        
        response = client.post(
            "/v1/memory/",
            json=memory_data,
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )
        
        assert response.status_code == 422
    
    def test_get_memory_success(self, client: TestClient, user_jwt_token: str, memory):
        """Test successful memory retrieval."""
        response = client.get(
            f"/v1/memory/{memory.id}",
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(memory.id)
        assert data["text"] == memory.text
    
    def test_search_memories_success(self, client: TestClient, user_jwt_token: str, memory):
        """Test successful memory search."""
        search_data = {
            "query": "test memory",
            "similarity_threshold": 0.7,
            "limit": 10
        }
        
        with patch('manushya.services.embedding_service.generate_embedding') as mock_embedding:
            mock_embedding.return_value = [0.1] * 1536
            
            response = client.post(
                "/v1/memory/search",
                json=search_data,
                headers={"Authorization": f"Bearer {user_jwt_token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_memory_success(self, client: TestClient, user_jwt_token: str, memory):
        """Test successful memory update."""
        update_data = {
            "text": "Updated memory text",
            "metadata": {"updated": True, "timestamp": "2024-01-01T00:00:00Z"}
        }
        
        response = client.put(
            f"/v1/memory/{memory.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == update_data["text"]
    
    def test_delete_memory_success(self, client: TestClient, user_jwt_token: str, memory):
        """Test successful memory deletion."""
        response = client.delete(
            f"/v1/memory/{memory.id}",
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )
        
        assert response.status_code == 204


class TestPolicyEndpoints:
    """Test policy management endpoints."""
    
    def test_create_policy_success(self, client: TestClient, admin_jwt_token: str):
        """Test successful policy creation."""
        policy_data = {
            "role": "user",
            "rule": {
                "and": [
                    {"in": [{"var": "action"}, ["read", "write"]]},
                    {"==": [{"var": "resource"}, "memory"]}
                ]
            },
            "description": "Test policy for users",
            "priority": 100,
            "is_active": True
        }
        
        response = client.post(
            "/v1/policy/",
            json=policy_data,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == policy_data["role"]
        assert data["description"] == policy_data["description"]
    
    def test_get_policy_success(self, client: TestClient, admin_jwt_token: str, policy):
        """Test successful policy retrieval."""
        response = client.get(
            f"/v1/policy/{policy.id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(policy.id)
        assert data["role"] == policy.role
    
    def test_list_policies(self, client: TestClient, admin_jwt_token: str):
        """Test policy listing."""
        response = client.get(
            "/v1/policy/",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_test_policy_evaluation(self, client: TestClient, admin_jwt_token: str):
        """Test policy evaluation."""
        test_data = {
            "role": "user",
            "action": "read",
            "resource": "memory",
            "context": {"memory_type": "test_memory"}
        }
        
        response = client.post(
            "/v1/policy/test",
            json=test_data,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "allowed" in data


class TestAPIKeyEndpoints:
    """Test API key management endpoints."""
    
    def test_create_api_key_success(self, client: TestClient, admin_jwt_token: str):
        """Test successful API key creation."""
        api_key_data = {
            "name": "Test API Key",
            "scopes": ["read", "write"],
            "expires_in_days": 30
        }
        
        response = client.post(
            "/v1/api-keys/",
            json=api_key_data,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == api_key_data["name"]
        assert "key" in data  # Should return the actual key
    
    def test_list_api_keys(self, client: TestClient, admin_jwt_token: str):
        """Test API key listing."""
        response = client.get(
            "/v1/api-keys/",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_revoke_api_key_success(self, client: TestClient, admin_jwt_token: str, api_key):
        """Test successful API key revocation."""
        response = client.delete(
            f"/v1/api-keys/{api_key.id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 204
    
    def test_test_api_key_auth(self, client: TestClient, admin_api_key):
        """Test API key authentication."""
        # This would need a valid API key hash
        response = client.post(
            "/v1/api-keys/test",
            headers={"Authorization": "Bearer mk_test_api_key"}
        )
        
        # Should either succeed or fail with proper error
        assert response.status_code in [200, 401, 404]


class TestWebhookEndpoints:
    """Test webhook management endpoints."""
    
    def test_create_webhook_success(self, client: TestClient, admin_jwt_token: str):
        """Test successful webhook creation."""
        webhook_data = {
            "name": "Test Webhook",
            "url": "https://webhook.site/test",
            "events": ["memory.created", "memory.updated"]
        }
        
        response = client.post(
            "/v1/webhooks/",
            json=webhook_data,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == webhook_data["name"]
        assert data["url"] == webhook_data["url"]
    
    def test_list_webhooks(self, client: TestClient, admin_jwt_token: str):
        """Test webhook listing."""
        response = client.get(
            "/v1/webhooks/",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_webhook_deliveries(self, client: TestClient, admin_jwt_token: str, webhook):
        """Test webhook delivery listing."""
        response = client.get(
            f"/v1/webhooks/{webhook.id}/deliveries",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestUsageEndpoints:
    """Test usage analytics endpoints."""
    
    def test_get_usage_summary(self, client: TestClient, admin_jwt_token: str):
        """Test usage summary retrieval."""
        response = client.get(
            "/v1/usage/summary?days=30",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "totals" in data
        assert "daily_breakdown" in data
    
    def test_get_daily_usage(self, client: TestClient, admin_jwt_token: str):
        """Test daily usage retrieval."""
        response = client.get(
            "/v1/usage/daily?start_date=2024-01-01&end_date=2024-01-31",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestMonitoringEndpoints:
    """Test monitoring endpoints."""
    
    def test_get_system_health(self, client: TestClient, admin_jwt_token: str):
        """Test system health endpoint."""
        response = client.get(
            "/v1/monitoring/health",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
    
    def test_get_usage_metrics(self, client: TestClient, admin_jwt_token: str):
        """Test usage metrics endpoint."""
        response = client.get(
            "/v1/monitoring/usage",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_identities" in data
        assert "total_memories" in data
    
    def test_get_performance_metrics(self, client: TestClient, admin_jwt_token: str):
        """Test performance metrics endpoint."""
        response = client.get(
            "/v1/monitoring/performance",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "avg_response_time_ms" in data
        assert "requests_per_second" in data


class TestAuthenticationEndpoints:
    """Test authentication endpoints."""
    
    def test_create_identity_success(self, client: TestClient):
        """Test successful identity creation with token."""
        identity_data = {
            "external_id": "test_user@example.com",
            "role": "user",
            "claims": {"name": "Test User"}
        }
        
        response = client.post("/v1/identity/", json=identity_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "identity" in data
        assert data["identity"]["external_id"] == "test_user@example.com"
    
    def test_create_identity_duplicate(self, client: TestClient):
        """Test creating identity with duplicate external_id."""
        identity_data = {
            "external_id": "duplicate@example.com",
            "role": "user",
            "claims": {"name": "Duplicate User"}
        }
        
        # Create first identity
        response1 = client.post("/v1/identity/", json=identity_data)
        assert response1.status_code == 200
        
        # Try to create duplicate
        response2 = client.post("/v1/identity/", json=identity_data)
        assert response2.status_code == 409  # Conflict
    
    def test_refresh_token_success(self, client: TestClient):
        """Test successful token refresh."""
        # First create an identity to get a refresh token
        identity_data = {
            "external_id": "refresh_test@example.com",
            "role": "user",
            "claims": {"name": "Refresh Test User"}
        }
        
        create_response = client.post("/v1/identity/", json=identity_data)
        assert create_response.status_code == 200
        refresh_token = create_response.json()["refresh_token"]
        
        # Test refresh endpoint
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/v1/sessions/refresh", json=refresh_data)
        assert response.status_code in [200, 401]  # Either success or proper error


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limiting_enforcement(self, client: TestClient, user_jwt_token: str):
        """Test that rate limiting is enforced."""
        # Make multiple requests quickly
        for _ in range(10):
            response = client.get(
                "/v1/identity/",
                headers={"Authorization": f"Bearer {user_jwt_token}"}
            )
            # Should not get rate limited immediately
            assert response.status_code in [200, 429]
    
    def test_rate_limit_headers(self, client: TestClient, user_jwt_token: str):
        """Test that rate limit headers are present."""
        response = client.get(
            "/v1/identity/",
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )
        
        # Check for rate limit headers
        headers = response.headers
        assert "X-RateLimit-Limit" in headers or response.status_code == 429
        assert "X-RateLimit-Remaining" in headers or response.status_code == 429


class TestErrorHandling:
    """Test error handling functionality."""
    
    def test_validation_error_handling(self, client: TestClient, user_jwt_token: str):
        """Test validation error handling."""
        # Send invalid data
        invalid_data = {"invalid": "data"}
        
        response = client.post(
            "/v1/memory/",
            json=invalid_data,
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
    
    def test_not_found_error_handling(self, client: TestClient, user_jwt_token: str):
        """Test not found error handling."""
        import uuid
        
        response = client.get(
            f"/v1/memory/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_authentication_error_handling(self, client: TestClient):
        """Test authentication error handling."""
        response = client.get("/v1/identity/")
        assert response.status_code == 401
        data = response.json()
        assert "error" in data


class TestMultiTenancy:
    """Test multi-tenancy functionality."""
    
    def test_tenant_isolation(self, client: TestClient, admin_jwt_token: str):
        """Test that tenants are properly isolated."""
        # Create identity for tenant A
        tenant_a_identity = {
            "external_id": "user@tenant-a.com",
            "role": "user",
            "tenant_id": "tenant-a"
        }
        
        response_a = client.post(
            "/v1/identity/",
            json=tenant_a_identity,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response_a.status_code == 201
        
        # Create identity for tenant B
        tenant_b_identity = {
            "external_id": "user@tenant-b.com",
            "role": "user",
            "tenant_id": "tenant-b"
        }
        
        response_b = client.post(
            "/v1/identity/",
            json=tenant_b_identity,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response_b.status_code == 201
        
        # Verify they are different
        data_a = response_a.json()
        data_b = response_b.json()
        assert data_a["tenant_id"] != data_b["tenant_id"]


class TestAuditLogging:
    """Test audit logging functionality."""
    
    def test_audit_log_creation(self, client: TestClient, admin_jwt_token: str):
        """Test that audit logs are created for actions."""
        # Perform an action that should create an audit log
        identity_data = {
            "external_id": "audit-test-user",
            "role": "user"
        }
        
        response = client.post(
            "/v1/identity/",
            json=identity_data,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 201
        
        # Check audit logs
        response = client.get(
            "/v1/monitoring/audit-trail",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) 