#!/usr/bin/env python3
"""
SDK Generation Pipeline for Manushya.ai

Generates Python and TypeScript SDKs from OpenAPI specification.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
OPENAPI_URL = f"{API_BASE_URL}/v1/openapi.json"
SDK_DIR = Path("sdk")
PYTHON_SDK_DIR = SDK_DIR / "python"
TYPESCRIPT_SDK_DIR = SDK_DIR / "typescript"


def run_command(cmd: list[str], cwd: Path = None) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running command: {result.stderr}")
        sys.exit(1)
    
    return result


def fetch_openapi_spec() -> Dict[str, Any]:
    """Fetch OpenAPI specification from the running API."""
    import requests
    
    try:
        response = requests.get(OPENAPI_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching OpenAPI spec: {e}")
        print("Make sure the API is running on localhost:8000")
        sys.exit(1)


def patch_openapi_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Patch OpenAPI spec for better SDK generation."""
    
    # Add security schemes
    if "components" not in spec:
        spec["components"] = {}
    
    if "securitySchemes" not in spec["components"]:
        spec["components"]["securitySchemes"] = {}
    
    # Add API key authentication
    spec["components"]["securitySchemes"]["ApiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key"
    }
    
    # Add JWT authentication
    spec["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
    }
    
    # Add global security
    spec["security"] = [
        {"ApiKeyAuth": []},
        {"BearerAuth": []}
    ]
    
    # Add server configuration
    spec["servers"] = [
        {
            "url": API_BASE_URL,
            "description": "Development server"
        }
    ]
    
    return spec


def generate_python_sdk(spec: Dict[str, Any]) -> None:
    """Generate Python SDK using openapi-python-client."""
    
    # Create output directory (let openapi-python-client handle this)
    # PYTHON_SDK_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save patched spec
    spec_file = SDK_DIR / "openapi_patched.json"
    with open(spec_file, "w") as f:
        json.dump(spec, f, indent=2)
    
    # Generate Python SDK
    cmd = [
        "poetry", "run", "openapi-python-client", "generate",
        "--url", "http://localhost:8000/v1/openapi.json",
        "--output-path", str(PYTHON_SDK_DIR),
        "--meta", "none",
        "--overwrite"
    ]
    
    run_command(cmd)
    
    # Create custom client wrapper
    create_python_client_wrapper()


def create_python_client_wrapper() -> None:
    """Create a custom client wrapper with better authentication."""
    
    wrapper_content = '''"""
Manushya.ai Python SDK Client

A high-level client for the Manushya.ai API with authentication support.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path

# Import the generated client
try:
    from .client import Client
    from .types import Unset
except ImportError:
    # Fallback for development
    from client import Client
    from types import Unset


class ManushyaClient:
    """High-level client for Manushya.ai API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        jwt_token: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        timeout: int = 30
    ):
        """Initialize the client.
        
        Args:
            api_key: API key for authentication
            jwt_token: JWT token for authentication
            base_url: Base URL for the API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("MANUSHYA_API_KEY")
        self.jwt_token = jwt_token or os.getenv("MANUSHYA_JWT_TOKEN")
        self.base_url = base_url
        self.timeout = timeout
        
        # Initialize the generated client
        self._client = Client(
            base_url=base_url,
            timeout=timeout,
            headers=self._get_headers()
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        headers = {}
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        
        return headers
    
    def update_auth(self, api_key: Optional[str] = None, jwt_token: Optional[str] = None) -> None:
        """Update authentication credentials."""
        if api_key is not None:
            self.api_key = api_key
        if jwt_token is not None:
            self.jwt_token = jwt_token
        
        # Update client headers
        self._client.headers = self._get_headers()
    
    # Health check
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        return self._client.health_check()
    
    # Identity management
    def create_identity(self, external_id: str, role: str, claims: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new identity."""
        from .types import IdentityCreate
        
        data = IdentityCreate(
            external_id=external_id,
            role=role,
            claims=claims or {}
        )
        
        return self._client.v1_identity_create(data=data)
    
    def get_identity(self, identity_id: str) -> Dict[str, Any]:
        """Get identity by ID."""
        return self._client.v1_identity_get(identity_id=identity_id)
    
    # Memory management
    def create_memory(
        self,
        identity_id: str,
        text: str,
        memory_type: str,
        metadata: Dict[str, Any] = None,
        ttl_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new memory."""
        from .types import MemoryCreate
        
        data = MemoryCreate(
            identity_id=identity_id,
            text=text,
            type=memory_type,
            meta_data=metadata or {},
            ttl_days=ttl_days
        )
        
        return self._client.v1_memory_create(data=data)
    
    def search_memories(
        self,
        identity_id: str,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Search memories."""
        return self._client.v1_memory_search(
            identity_id=identity_id,
            query=query,
            type=memory_type,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
    
    # API Key management
    def create_api_key(
        self,
        identity_id: str,
        name: str,
        scopes: list[str] = None
    ) -> Dict[str, Any]:
        """Create a new API key."""
        from .types import ApiKeyCreate
        
        data = ApiKeyCreate(
            identity_id=identity_id,
            name=name,
            scopes=scopes or []
        )
        
        return self._client.v1_api_keys_create(data=data)
    
    # Usage analytics
    def get_usage_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get usage summary."""
        return self._client.v1_usage_summary_get(days=days)
    
    def get_usage_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get usage events."""
        return self._client.v1_usage_events_get(
            start_date=start_date,
            end_date=end_date,
            event_type=event_type,
            limit=limit,
            offset=offset
        )


# Convenience function for quick setup
def create_client(
    api_key: Optional[str] = None,
    jwt_token: Optional[str] = None,
    base_url: str = "http://localhost:8000"
) -> ManushyaClient:
    """Create a Manushya client instance."""
    return ManushyaClient(
        api_key=api_key,
        jwt_token=jwt_token,
        base_url=base_url
    )
'''
    
    wrapper_file = PYTHON_SDK_DIR / "manushya_client.py"
    with open(wrapper_file, "w") as f:
        f.write(wrapper_content)
    
    # Create setup.py
    setup_content = '''"""
Setup script for Manushya.ai Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="manushya-sdk",
    version="1.0.0",
    author="Manushya.ai",
    author_email="support@manushya.ai",
    description="Python SDK for Manushya.ai API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/manushya-ai/sdk-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
        ]
    }
)
'''
    
    setup_file = PYTHON_SDK_DIR / "setup.py"
    with open(setup_file, "w") as f:
        f.write(setup_content)
    
    # Create README
    readme_content = '''# Manushya.ai Python SDK

Official Python SDK for the Manushya.ai API.

## Installation

```bash
pip install manushya-sdk
```

## Quick Start

```python
from manushya_sdk import create_client

# Initialize client with API key
client = create_client(api_key="your-api-key")

# Create an identity
identity = client.create_identity(
    external_id="user123",
    role="user",
    claims={"email": "user@example.com"}
)

# Create a memory
memory = client.create_memory(
    identity_id=identity["id"],
    text="User prefers dark mode interface",
    memory_type="preference",
    metadata={"source": "ui_interaction"}
)

# Search memories
results = client.search_memories(
    identity_id=identity["id"],
    query="dark mode",
    limit=5
)

# Get usage summary
usage = client.get_usage_summary(days=30)
```

## Authentication

The SDK supports two authentication methods:

1. **API Key**: Set via `api_key` parameter or `MANUSHYA_API_KEY` environment variable
2. **JWT Token**: Set via `jwt_token` parameter or `MANUSHYA_JWT_TOKEN` environment variable

## Features

- ✅ Full API coverage
- ✅ Type-safe operations
- ✅ Automatic authentication
- ✅ Usage analytics
- ✅ Memory management
- ✅ Identity management
- ✅ API key management

## Documentation

For detailed API documentation, visit: https://docs.manushya.ai
'''
    
    readme_file = PYTHON_SDK_DIR / "README.md"
    with open(readme_file, "w") as f:
        f.write(readme_content)


def generate_typescript_sdk(spec: Dict[str, Any]) -> None:
    """Generate TypeScript SDK using openapi-typescript-codegen."""
    
    # Create output directory
    TYPESCRIPT_SDK_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save patched spec
    spec_file = SDK_DIR / "openapi_patched.json"
    with open(spec_file, "w") as f:
        json.dump(spec, f, indent=2)
    
    # Generate TypeScript SDK
    cmd = [
        "npx", "openapi-typescript-codegen",
        "--input", str(spec_file),
        "--output", str(TYPESCRIPT_SDK_DIR),
        "--name", "manushya-sdk",
        "--client", "fetch"
    ]
    
    run_command(cmd)
    
    # Create custom client wrapper
    create_typescript_client_wrapper()


def create_typescript_client_wrapper() -> None:
    """Create a custom TypeScript client wrapper."""
    
    wrapper_content = '''/**
 * Manushya.ai TypeScript SDK Client
 * 
 * A high-level client for the Manushya.ai API with authentication support.
 */

import { ApiError, ApiRequestOptions, ApiResult } from './core/ApiError';
import { OpenAPI } from './core/OpenAPI';
import { request as __request } from './core/request';

export interface ManushyaConfig {
    apiKey?: string;
    jwtToken?: string;
    baseUrl?: string;
    timeout?: number;
}

export class ManushyaClient {
    private apiKey?: string;
    private jwtToken?: string;
    private baseUrl: string;
    private timeout: number;

    constructor(config: ManushyaConfig = {}) {
        this.apiKey = config.apiKey || process.env.MANUSHYA_API_KEY;
        this.jwtToken = config.jwtToken || process.env.MANUSHYA_JWT_TOKEN;
        this.baseUrl = config.baseUrl || 'http://localhost:8000';
        this.timeout = config.timeout || 30000;

        // Configure OpenAPI
        OpenAPI.BASE = this.baseUrl;
        OpenAPI.TIMEOUT = this.timeout;
        OpenAPI.WITH_CREDENTIALS = true;
    }

    private getHeaders(): Record<string, string> {
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        };

        if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }

        if (this.jwtToken) {
            headers['Authorization'] = `Bearer ${this.jwtToken}`;
        }

        return headers;
    }

    updateAuth(config: { apiKey?: string; jwtToken?: string }) {
        if (config.apiKey !== undefined) {
            this.apiKey = config.apiKey;
        }
        if (config.jwtToken !== undefined) {
            this.jwtToken = config.jwtToken;
        }
    }

    // Health check
    async healthCheck(): Promise<any> {
        const options: ApiRequestOptions = {
            method: 'GET',
            path: '/health',
            headers: this.getHeaders(),
        };
        return __request(options);
    }

    // Identity management
    async createIdentity(externalId: string, role: string, claims: Record<string, any> = {}): Promise<any> {
        const options: ApiRequestOptions = {
            method: 'POST',
            path: '/v1/identity',
            headers: this.getHeaders(),
            body: {
                external_id: externalId,
                role,
                claims,
            },
        };
        return __request(options);
    }

    async getIdentity(identityId: string): Promise<any> {
        const options: ApiRequestOptions = {
            method: 'GET',
            path: `/v1/identity/${identityId}`,
            headers: this.getHeaders(),
        };
        return __request(options);
    }

    // Memory management
    async createMemory(
        identityId: string,
        text: string,
        type: string,
        metadata: Record<string, any> = {},
        ttlDays?: number
    ): Promise<any> {
        const options: ApiRequestOptions = {
            method: 'POST',
            path: '/v1/memory',
            headers: this.getHeaders(),
            body: {
                identity_id: identityId,
                text,
                type,
                meta_data: metadata,
                ttl_days: ttlDays,
            },
        };
        return __request(options);
    }

    async searchMemories(
        identityId: string,
        query: string,
        type?: string,
        limit: number = 10,
        similarityThreshold?: number
    ): Promise<any> {
        const options: ApiRequestOptions = {
            method: 'GET',
            path: '/v1/memory/search',
            headers: this.getHeaders(),
            query: {
                identity_id: identityId,
                query,
                type,
                limit: limit.toString(),
                similarity_threshold: similarityThreshold?.toString(),
            },
        };
        return __request(options);
    }

    // API Key management
    async createApiKey(identityId: string, name: string, scopes: string[] = []): Promise<any> {
        const options: ApiRequestOptions = {
            method: 'POST',
            path: '/v1/api-keys',
            headers: this.getHeaders(),
            body: {
                identity_id: identityId,
                name,
                scopes,
            },
        };
        return __request(options);
    }

    // Usage analytics
    async getUsageSummary(days: number = 30): Promise<any> {
        const options: ApiRequestOptions = {
            method: 'GET',
            path: '/v1/usage/summary',
            headers: this.getHeaders(),
            query: {
                days: days.toString(),
            },
        };
        return __request(options);
    }

    async getUsageEvents(params: {
        startDate?: string;
        endDate?: string;
        eventType?: string;
        limit?: number;
        offset?: number;
    } = {}): Promise<any> {
        const options: ApiRequestOptions = {
            method: 'GET',
            path: '/v1/usage/events',
            headers: this.getHeaders(),
            query: {
                start_date: params.startDate,
                end_date: params.endDate,
                event_type: params.eventType,
                limit: params.limit?.toString() || '100',
                offset: params.offset?.toString() || '0',
            },
        };
        return __request(options);
    }
}

// Convenience function for quick setup
export function createClient(config: ManushyaConfig = {}): ManushyaClient {
    return new ManushyaClient(config);
}
'''
    
    wrapper_file = TYPESCRIPT_SDK_DIR / "src" / "manushya-client.ts"
    wrapper_file.parent.mkdir(parents=True, exist_ok=True)
    with open(wrapper_file, "w") as f:
        f.write(wrapper_content)
    
    # Create package.json
    package_content = {
        "name": "manushya-sdk",
        "version": "1.0.0",
        "description": "TypeScript SDK for Manushya.ai API",
        "main": "dist/index.js",
        "types": "dist/index.d.ts",
        "scripts": {
            "build": "tsc",
            "dev": "tsc --watch",
            "test": "jest",
            "lint": "eslint src --ext .ts",
            "format": "prettier --write src"
        },
        "keywords": [
            "manushya",
            "ai",
            "memory",
            "sdk",
            "typescript"
        ],
        "author": "Manushya.ai",
        "license": "MIT",
        "devDependencies": {
            "@types/node": "^18.0.0",
            "typescript": "^4.9.0",
            "jest": "^29.0.0",
            "@types/jest": "^29.0.0",
            "eslint": "^8.0.0",
            "@typescript-eslint/eslint-plugin": "^5.0.0",
            "@typescript-eslint/parser": "^5.0.0",
            "prettier": "^2.8.0"
        },
        "dependencies": {
            "form-data": "^4.0.0"
        }
    }
    
    package_file = TYPESCRIPT_SDK_DIR / "package.json"
    with open(package_file, "w") as f:
        json.dump(package_content, f, indent=2)
    
    # Create README
    readme_content = '''# Manushya.ai TypeScript SDK

Official TypeScript SDK for the Manushya.ai API.

## Installation

```bash
npm install manushya-sdk
```

## Quick Start

```typescript
import { createClient } from 'manushya-sdk';

// Initialize client with API key
const client = createClient({ apiKey: 'your-api-key' });

// Create an identity
const identity = await client.createIdentity(
    'user123',
    'user',
    { email: 'user@example.com' }
);

// Create a memory
const memory = await client.createMemory(
    identity.id,
    'User prefers dark mode interface',
    'preference',
    { source: 'ui_interaction' }
);

// Search memories
const results = await client.searchMemories(
    identity.id,
    'dark mode',
    undefined,
    5
);

// Get usage summary
const usage = await client.getUsageSummary(30);
```

## Authentication

The SDK supports two authentication methods:

1. **API Key**: Set via `apiKey` parameter or `MANUSHYA_API_KEY` environment variable
2. **JWT Token**: Set via `jwtToken` parameter or `MANUSHYA_JWT_TOKEN` environment variable

## Features

- ✅ Full API coverage
- ✅ Type-safe operations
- ✅ Automatic authentication
- ✅ Usage analytics
- ✅ Memory management
- ✅ Identity management
- ✅ API key management

## Documentation

For detailed API documentation, visit: https://docs.manushya.ai
'''
    
    readme_file = TYPESCRIPT_SDK_DIR / "README.md"
    with open(readme_file, "w") as f:
        f.write(readme_content)


def main():
    """Main function to generate SDKs."""
    print("🚀 Generating Manushya.ai SDKs...")
    
    # Create SDK directory
    SDK_DIR.mkdir(exist_ok=True)
    
    # Fetch and patch OpenAPI spec
    print("📡 Fetching OpenAPI specification...")
    spec = fetch_openapi_spec()
    spec = patch_openapi_spec(spec)
    
    # Generate Python SDK
    print("🐍 Generating Python SDK...")
    generate_python_sdk(spec)
    
    # Generate TypeScript SDK
    print("📘 Generating TypeScript SDK...")
    generate_typescript_sdk(spec)
    
    print("✅ SDK generation complete!")
    print(f"📁 Python SDK: {PYTHON_SDK_DIR}")
    print(f"📁 TypeScript SDK: {TYPESCRIPT_SDK_DIR}")
    
    # Print usage instructions
    print("\n📖 Usage Instructions:")
    print("1. Python SDK: cd sdk/python && pip install -e .")
    print("2. TypeScript SDK: cd sdk/typescript && npm install && npm run build")


if __name__ == "__main__":
    main() 