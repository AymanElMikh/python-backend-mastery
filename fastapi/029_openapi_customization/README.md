# FastAPI OpenAPI Customization — Tags, Metadata, Security Schemes

## 🎯 Interview Question
How do you customize FastAPI's auto-generated OpenAPI schema? Explain tags, operation metadata, security schemes, custom schema generation, and how to hide routes from the docs.

## 💡 Short Answer (30 seconds)
FastAPI auto-generates an OpenAPI 3.x schema from route decorators, Pydantic models, and docstrings. You customize it via `tags`, `summary`, `description`, `deprecated`, `operation_id`, and `responses` on individual routes; via `tags_metadata` on the `FastAPI()` constructor; and via `app.openapi()` override for schema-level changes. Security schemes like Bearer JWT are added via `SecurityScheme` and `Security()`.

## 🔬 Deep Explanation

### App-level metadata
```python
app = FastAPI(
    title="My API",
    description="Full markdown description — shown on /docs",
    version="2.1.0",
    terms_of_service="https://example.com/terms",
    contact={"name": "API Support", "email": "api@example.com"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    openapi_url="/api/v1/openapi.json",  # change URL
    docs_url="/api/v1/docs",             # change Swagger UI URL
    redoc_url="/api/v1/redoc",           # change ReDoc URL
)
```

### Tags — grouping routes
```python
app = FastAPI(
    openapi_tags=[
        {"name": "users", "description": "User management operations"},
        {"name": "items", "description": "Item CRUD", "externalDocs": {"url": "..."}},
    ]
)

@app.get("/users", tags=["users"])
@app.post("/items", tags=["items"])
```

### Route-level metadata
```python
@app.get(
    "/users/{id}",
    summary="Get user by ID",
    description="Retrieves a single user. Returns 404 if not found.\n\nSupports partial responses.",
    response_description="The requested user object",
    tags=["users"],
    operation_id="get_user_by_id",     # custom operationId for client codegen
    deprecated=True,                    # shows strikethrough in docs
    include_in_schema=False,            # hide from docs entirely
)
```

### Docstring as description
FastAPI uses the route function's docstring as the operation description:
```python
@app.get("/users/{id}")
async def get_user(id: int):
    """
    Get a specific user.

    Returns the full user profile. Use **?fields=** to select specific fields.

    - **id**: unique integer identifier
    """
```

### Security schemes
```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer

bearer_scheme = HTTPBearer()

@app.get("/protected")
async def protected(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = credentials.credentials
    # validate token...
```

This adds a security lock icon in Swagger UI and documents the `Authorization: Bearer <token>` requirement.

### Custom `openapi()` — schema manipulation
Override the schema generator to add custom fields, remove internal routes, or add servers:
```python
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema  # cache

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    # Add custom extension
    schema["info"]["x-logo"] = {"url": "https://example.com/logo.png"}
    # Add security scheme globally
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi
```

### Hiding internal routes
```python
@app.get("/internal/health", include_in_schema=False)
async def health(): return {"ok": True}
```

### `openapi_extra` — inject raw OpenAPI fields
```python
@app.post(
    "/items",
    openapi_extra={
        "requestBody": {
            "content": {"application/xml": {"schema": {"type": "string"}}},
            "required": True,
        }
    }
)
```

## 💻 Code Example

```python
from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

bearer = HTTPBearer()

app = FastAPI(
    title="Backend Mastery API",
    version="1.0.0",
    openapi_tags=[
        {"name": "users", "description": "User management"},
        {"name": "internal", "description": "Internal endpoints"},
    ],
)

@app.get("/users", tags=["users"], summary="List all users")
async def list_users(credentials=Depends(bearer)):
    """
    Returns paginated list of users.

    Requires **Bearer JWT** authentication.
    """
    return [{"id": 1, "name": "Alice"}]

@app.get("/internal/ping", include_in_schema=False)
async def ping(): return "pong"  # hidden from docs
```

## ⚠️ Common Mistakes & Interview Traps

1. **`operation_id` uniqueness**: FastAPI auto-generates operation IDs from the function name + HTTP method + path. Duplicate function names across routers cause duplicate operation IDs — this breaks client code generators. Always set explicit `operation_id` or use `generate_unique_id_function`.

2. **Security scheme vs auth enforcement**: Adding `HTTPBearer` to a route documents it in OpenAPI, but does NOT enforce authentication — that's the dependency's job. The schema and the runtime are separate.

3. **`include_in_schema=False` doesn't disable the route**: It just hides it from docs. The route still accepts requests. Use middleware or DI for actual access control.

4. **`openapi()` cache**: Once `app.openapi_schema` is set, it's cached. Dynamic schema changes after first request won't be reflected without clearing the cache.

5. **`tags` vs `openapi_tags`**: `tags=["users"]` on a route assigns the route to a tag. `openapi_tags=[{"name": "users", ...}]` on the app adds metadata (description, external docs) to the tag. Both are needed for fully documented tags.

## 🔗 Related Concepts
- `fastapi/021_dependency_injection` — `Security(scheme)` is `Depends` + schema annotation
- `fastapi/027_response_models` — `responses=` dict adds documented response schemas
- `fastapi/028_exception_handlers` — document error responses in `responses=`

## 📚 Go Deeper
- OpenAPI 3.1 spec — the full spec FastAPI generates against
- FastAPI docs: "Extending OpenAPI" — `openapi_extra`, custom schema generation
