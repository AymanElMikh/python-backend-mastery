# FastAPI Exception Handlers — `HTTPException`, Custom Handlers, 422 Errors

## 🎯 Interview Question
How does FastAPI's exception handling work? Explain `HTTPException`, `RequestValidationError`, custom exception handlers, and how to override the default 422 validation error response format.

## 💡 Short Answer (30 seconds)
FastAPI has built-in handlers for `HTTPException` (returns `{"detail": ...}`) and `RequestValidationError` (Pydantic validation failures → 422). You add custom handlers with `@app.exception_handler(ExcType)` or `app.add_exception_handler(ExcType, handler)`. To override the 422 format, register a custom handler for `RequestValidationError`. Exception handlers receive the `Request` and exception — they must return a `Response`.

## 🔬 Deep Explanation

### The exception handler chain
When an exception propagates out of a route:
1. FastAPI checks `app.exception_handlers` for a matching type (exact match first, then `__mro__` walk)
2. If found, calls `handler(request, exc)` — must return a `Response`
3. If not found, Starlette's default handler runs (re-raises, resulting in 500)

### `HTTPException`
```python
from fastapi import HTTPException

raise HTTPException(
    status_code=404,
    detail="User not found",       # goes into {"detail": ...}
    headers={"X-Error-Code": "E001"},  # added to response headers
)
```
Default handler returns: `{"detail": "User not found"}` with 404 status.

### `RequestValidationError` — 422 Unprocessable Entity
Raised when Pydantic validation fails on request input. Default response:
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "email"],
      "msg": "Field required",
      "input": {...},
      "url": "https://errors.pydantic.dev/..."
    }
  ]
}
```

### Custom exception handlers
```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"errors": errors})
```

### Custom application exceptions
Best practice: define a hierarchy, register a handler per base class:
```python
class AppError(Exception):
    def __init__(self, message: str, code: str, status: int = 400):
        self.message = message
        self.code = code
        self.status = status

class NotFoundError(AppError):
    def __init__(self, resource: str, id):
        super().__init__(f"{resource} {id} not found", "NOT_FOUND", 404)

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status,
        content={"code": exc.code, "message": exc.message},
    )
```

### Exception handlers and middleware
Exception handlers are registered at the app level. Starlette processes them after middleware. If middleware catches an exception before it reaches the app, the handler never runs. Generally: let route-level exceptions propagate through middleware unhandled, then catch at the app level.

### Catching unexpected exceptions — 500 handler
```python
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Log to Sentry, Datadog, etc.
    logger.error(f"Unhandled: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

**Warning**: This also catches `HTTPException` unless you re-register its handler after.

### Override default HTTP exception handler
```python
from fastapi.exception_handlers import http_exception_handler

@app.exception_handler(HTTPException)
async def custom_http_handler(request: Request, exc: HTTPException):
    # Add request ID, structured logging, etc.
    return await http_exception_handler(request, exc)  # call original
```

## 💻 Code Example

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

class AppError(Exception):
    def __init__(self, message: str, code: str, status: int = 400):
        self.message = message; self.code = code; self.status = status

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(exc.status, {"code": exc.code, "message": exc.message})

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(422, {
        "error": "validation_failed",
        "fields": [{"path": e["loc"], "msg": e["msg"]} for e in exc.errors()],
    })
```

## ⚠️ Common Mistakes & Interview Traps

1. **`Exception` handler swallows `HTTPException`**: Registering a handler for `Exception` catches everything including `HTTPException`. Re-register the HTTP exception handler or check the type inside.

2. **Returning from handler without `JSONResponse`**: The handler must return a `Response` object. Returning a dict raises `TypeError`.

3. **422 vs 400**: FastAPI uses 422 for validation errors (Pydantic) and 400 for general "bad request" semantics. Some teams override to 400 for simplicity. OpenAPI distinguishes them.

4. **`HTTPException` in DI**: Dependencies can raise `HTTPException` — it propagates through the dependency tree and is caught by the exception handler. This is the correct way to do auth checks.

5. **Exception handler order**: FastAPI matches the most specific type first. `NotFoundError(AppError)` handler runs before `AppError` handler for `NotFoundError` instances — if both are registered.

## 🔗 Related Concepts
- `fastapi/021_dependency_injection` — dependencies raise `HTTPException` for auth
- `fastapi/023_middleware` — middleware runs before exception handlers
- `fastapi/025_pydantic_v2_validators` — Pydantic `ValidationError` wraps as `RequestValidationError`

## 📚 Go Deeper
- FastAPI source: `applications.py` — `_get_exception_handler` dispatch logic
- Starlette source: `middleware/exceptions.py` — the ExceptionMiddleware implementation
