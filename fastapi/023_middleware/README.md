# FastAPI Middleware — Request/Response Lifecycle

## 🎯 Interview Question
How does middleware work in FastAPI/Starlette? Explain the difference between `BaseHTTPMiddleware`, pure ASGI middleware, and `add_middleware`. What are the performance trade-offs, and what are common patterns?

## 💡 Short Answer (30 seconds)
Middleware wraps every request — it runs before the route handler and can modify the request, then runs after and can modify the response. FastAPI inherits Starlette's middleware stack. `BaseHTTPMiddleware` is the convenient Python class-based approach. Pure ASGI middleware is faster (no request body buffering) but more complex. Common patterns: request timing, correlation IDs, CORS, authentication, rate limiting, compression.

## 🔬 Deep Explanation

### The ASGI middleware model
FastAPI is an ASGI app. Every middleware wraps the app in a chain:

```
request → MW1 → MW2 → MW3 → Route Handler → MW3 → MW2 → MW1 → response
```

Each middleware is called with `(scope, receive, send)`. It calls `await call_next(request)` to pass control down the chain.

### `BaseHTTPMiddleware` — class-based, convenient
```python
from starlette.middleware.base import BaseHTTPMiddleware

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = str(elapsed)
        return response
```

**`BaseHTTPMiddleware` limitation**: It buffers the entire response body in memory before you can access it. For streaming responses, this is a problem. It also uses an extra `asyncio.Task` per request, adding overhead.

### Pure ASGI middleware — performant
```python
class RawASGIMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # modify scope/receive/send as needed
            await self.app(scope, receive, send)
        else:
            await self.app(scope, receive, send)
```
More control, no buffering, works with WebSockets — but you must handle raw ASGI directly.

### Adding middleware
```python
# Class-based (Starlette style):
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Or @app.middleware decorator:
@app.middleware("http")
async def my_middleware(request: Request, call_next):
    ...
    return await call_next(request)
```

**Order matters**: middleware added last runs outermost (first to see the request).

### Correlation ID pattern
Standard production pattern — inject a unique request ID:
```python
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(req_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
```

### Modifying the request — it's read-only
`Request` objects are read-only in Starlette. You can't add headers to an incoming request. The workaround: store data in `request.state` (a mutable State object per-request).

```python
request.state.user_id = 42  # accessible downstream in route handlers
```

### Exception handling in middleware
If a route handler raises, the exception propagates through the middleware chain. Middleware can catch and handle exceptions — but this runs before FastAPI's own exception handlers. Usually better to use `app.add_exception_handler()` instead.

## 💻 Code Example

```python
import time
import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, Request

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-Ms"] = f"{ms:.2f}"
        return response

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(req_id)
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

app = FastAPI()
app.add_middleware(TimingMiddleware)       # inner (closer to route)
app.add_middleware(CorrelationIDMiddleware)  # outer (sees request first)
```

## ⚠️ Common Mistakes & Interview Traps

1. **Middleware order is reversed**: `add_middleware` adds to the front of the chain. The last `add_middleware` call runs outermost (first for requests, last for responses).

2. **`BaseHTTPMiddleware` + streaming responses**: Buffering the whole body in memory breaks streaming. Use pure ASGI middleware or avoid reading the response body in middleware.

3. **Mutating `Request` headers**: You can't add headers to `request.headers` — it's immutable. Use `request.state` to pass data downstream, or build a new request via ASGI middleware.

4. **Exception handling in middleware vs exception handlers**: Catching exceptions in middleware bypasses FastAPI's own `RequestValidationError` and `HTTPException` handlers. Usually unintentional.

5. **`@app.middleware("http")` vs `BaseHTTPMiddleware`**: Both create `BaseHTTPMiddleware`-style middleware internally. The decorator is syntactic sugar.

## 🔗 Related Concepts
- `fastapi/021_dependency_injection` — per-request data better stored via `request.state` or `Depends`
- `fastapi/028_exception_handlers` — exceptions propagate through middleware before handlers
- `fastapi/022_lifespan` — middleware setup vs lifespan setup

## 📚 Go Deeper
- Starlette docs: "Middleware" — full list of built-in middleware
- ASGI spec: `asgiref.readthedocs.io` — the raw protocol middleware implements
