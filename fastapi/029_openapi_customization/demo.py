"""
Demo: FastAPI OpenAPI Customization — Tags, Metadata, Security, Schema
Run:  python demo.py
"""

import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi
from fastapi.testclient import TestClient
from pydantic import BaseModel

# ── App with full metadata ────────────────────────────────────────────────────
app = FastAPI(
    title="Backend Mastery API",
    description="""
## Overview

A demo API showcasing FastAPI OpenAPI customization.

### Features
- **User management** with JWT auth
- **Item catalog** with pagination
- Rich OpenAPI documentation
""",
    version="2.0.0",
    contact={"name": "API Team", "email": "api@example.com"},
    license_info={"name": "MIT"},
    openapi_tags=[
        {
            "name": "users",
            "description": "User registration, profile, and authentication",
        },
        {
            "name": "items",
            "description": "Item catalog — browse and manage items",
        },
        {
            "name": "health",
            "description": "Internal health and readiness endpoints",
        },
    ],
)

# ── Security scheme ───────────────────────────────────────────────────────────
bearer_scheme = HTTPBearer(
    description="JWT Bearer token. Format: `Bearer <token>`",
    auto_error=False,
)

async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if not credentials or credentials.credentials != "valid-jwt":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"user_id": 42, "name": "Alice"}

# ── Models ────────────────────────────────────────────────────────────────────
class User(BaseModel):
    id: int
    name: str
    email: str

class Item(BaseModel):
    id: int
    name: str
    price: float

class ErrorResponse(BaseModel):
    code: str
    message: str

# ── Routes — well-documented ──────────────────────────────────────────────────
@app.get(
    "/users",
    tags=["users"],
    summary="List users",
    response_model=list[User],
    responses={401: {"model": ErrorResponse, "description": "Unauthorized"}},
    operation_id="list_users",
)
async def list_users(current_user=Depends(require_auth)):
    """
    Retrieve all users.

    Requires a valid **Bearer JWT** token.
    Returns an array of user objects.
    """
    return [User(id=1, name="Alice", email="alice@ex.com")]


@app.get(
    "/users/{user_id}",
    tags=["users"],
    summary="Get user",
    response_model=User,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
    operation_id="get_user",
)
async def get_user(user_id: int, current_user=Depends(require_auth)):
    """Get a specific user by ID."""
    if user_id != 1:
        raise HTTPException(404, detail="User not found")
    return User(id=1, name="Alice", email="alice@ex.com")


@app.get(
    "/items",
    tags=["items"],
    summary="Browse catalog",
    response_model=list[Item],
    operation_id="list_items",
    deprecated=False,
)
async def list_items(page: int = 1, size: int = 20):
    """Browse the item catalog with pagination."""
    return [Item(id=i, name=f"Item {i}", price=i * 9.99) for i in range(1, 4)]


@app.get(
    "/items/v1/list",
    tags=["items"],
    summary="Browse catalog (v1 - deprecated)",
    deprecated=True,      # shows strikethrough in Swagger UI
    include_in_schema=True,
    operation_id="list_items_v1",
)
async def list_items_v1():
    """**Deprecated.** Use `/items` instead."""
    return []


# ── Hidden internal route ─────────────────────────────────────────────────────
@app.get("/internal/health", include_in_schema=False, tags=["health"])
async def health():
    return {"status": "ok"}


@app.get("/health", tags=["health"], summary="Health check", operation_id="health_check")
async def public_health():
    """Public health endpoint for load balancer probes."""
    return {"status": "healthy", "version": app.version}


# ── Custom openapi() — inject extra schema fields ────────────────────────────
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        contact=app.contact,
        license_info=app.license_info,
        tags=app.openapi_tags,
        routes=app.routes,
    )

    # Add custom extension fields
    schema["info"]["x-api-id"] = "backend-mastery-api"
    schema["info"]["x-audience"] = "external"

    # Add servers
    schema["servers"] = [
        {"url": "https://api.example.com", "description": "Production"},
        {"url": "https://staging.api.example.com", "description": "Staging"},
        {"url": "http://localhost:8000", "description": "Local dev"},
    ]

    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi


if __name__ == "__main__":
    client = TestClient(app)

    print("=" * 55)
    print("DEMO: FastAPI OpenAPI Customization")
    print("=" * 55)

    # Fetch and inspect the generated schema
    r = client.get("/openapi.json")
    schema = r.json()

    print("\n[1] App metadata in schema:")
    info = schema["info"]
    print(f"  title:   {info['title']!r}")
    print(f"  version: {info['version']!r}")
    print(f"  x-api-id: {info.get('x-api-id')!r}  (custom extension)")
    print(f"  x-audience: {info.get('x-audience')!r}")

    print("\n[2] Servers in schema:")
    for s in schema.get("servers", []):
        print(f"  {s['url']} — {s['description']}")

    print("\n[3] Tags defined:")
    for tag in schema.get("tags", []):
        print(f"  {tag['name']!r}: {tag['description']!r}")

    print("\n[4] Route operation IDs and tags:")
    for path, methods in schema["paths"].items():
        for method, op in methods.items():
            print(f"  {method.upper():6s} {path:35s} → id={op.get('operationId')!r}, tags={op.get('tags')}, deprecated={op.get('deprecated', False)}")

    print("\n[5] Hidden route not in schema:")
    hidden_in_schema = "/internal/health" in schema["paths"]
    print(f"  /internal/health in schema: {hidden_in_schema}  (include_in_schema=False)")
    r = client.get("/internal/health")
    print(f"  But route still works: {r.status_code} {r.json()}")

    print("\n[6] Security scheme — bearer auth:")
    r = client.get("/users", headers={"Authorization": "Bearer valid-jwt"})
    print(f"  Valid token → {r.status_code}: {r.json()}")
    r = client.get("/users")
    print(f"  No token   → {r.status_code}: {r.json()}")

    print("\n[7] Schema security requirements on protected routes:")
    user_get_op = schema["paths"].get("/users", {}).get("get", {})
    print(f"  /users GET security: {user_get_op.get('security', 'not set')}")

    print("\n" + "=" * 55)
