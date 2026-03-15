"""
Demo: FastAPI Middleware — Request/Response Lifecycle
Run:  python demo.py
"""

import time
import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse

# ── Shared state ──────────────────────────────────────────────────────────────
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
middleware_log = []

# ── Section 1: Timing middleware ──────────────────────────────────────────────
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.3f}"
        middleware_log.append(f"TimingMiddleware: {request.url.path} took {elapsed_ms:.2f}ms")
        return response


# ── Section 2: Correlation ID middleware ──────────────────────────────────────
class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Use provided ID or generate a new one
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request_id_var.set(req_id)
        request.state.request_id = req_id  # accessible in route handlers

        middleware_log.append(f"CorrelationID: set {req_id!r}")
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id  # echo back
        return response


# ── Section 3: Auth middleware ────────────────────────────────────────────────
class SimpleAuthMiddleware(BaseHTTPMiddleware):
    PUBLIC_PATHS = {"/", "/health", "/docs", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if api_key != "valid-key":
            middleware_log.append(f"Auth: REJECTED {request.url.path}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Forbidden: invalid API key"},
                headers={"X-Request-ID": request_id_var.get()},
            )

        request.state.authenticated = True
        middleware_log.append(f"Auth: ALLOWED {request.url.path}")
        return await call_next(request)


# ── Section 4: Pure ASGI middleware (no buffering) ────────────────────────────
class RequestCounterASGI:
    """Pure ASGI — no BaseHTTPMiddleware overhead, no body buffering."""
    def __init__(self, app):
        self.app = app
        self.count = 0

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            self.count += 1
        await self.app(scope, receive, send)


# ── Build app — middleware order matters! ─────────────────────────────────────
counter = RequestCounterASGI(None)  # placeholder, wired below

app = FastAPI()

# Added last = outermost (runs first on request)
app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(TimingMiddleware)
app.add_middleware(SimpleAuthMiddleware)
# Middleware order (outermost → innermost):
# CorrelationID → Timing → Auth → Route Handler


@app.get("/")
async def root():
    return {"message": "public endpoint"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/protected")
async def protected(request: Request):
    return {
        "data": "secret data",
        "request_id": request.state.request_id,
        "authenticated": getattr(request.state, "authenticated", False),
    }

@app.get("/echo-headers")
async def echo_headers(request: Request):
    return {
        "request_id": request.state.request_id,
        "ctx_var": request_id_var.get(),
    }


if __name__ == "__main__":
    client = TestClient(app)

    print("=" * 55)
    print("DEMO: FastAPI Middleware")
    print("=" * 55)

    # Section 1+2: timing + correlation ID
    print("\n[1] Timing + Correlation ID middleware:")
    middleware_log.clear()
    r = client.get("/", headers={"X-Request-ID": "test-123"})
    print(f"  GET / → {r.status_code}")
    print(f"  X-Process-Time-Ms: {r.headers.get('X-Process-Time-Ms')}")
    print(f"  X-Request-ID: {r.headers.get('X-Request-ID')}")

    # Auto-generated ID
    r = client.get("/health")
    req_id = r.headers.get("X-Request-ID", "")
    print(f"  GET /health (no ID header) → generated ID: {req_id!r}")

    # Section 3: auth middleware
    print("\n[2] Auth middleware:")
    middleware_log.clear()
    r = client.get("/protected")
    print(f"  No API key:    {r.status_code} → {r.json()}")

    r = client.get("/protected", headers={"X-API-Key": "wrong-key"})
    print(f"  Wrong API key: {r.status_code} → {r.json()}")

    r = client.get("/protected", headers={"X-API-Key": "valid-key"})
    print(f"  Valid API key: {r.status_code} → {r.json()}")

    # Section 4: middleware log showing execution order
    print("\n[3] Middleware execution log (last request):")
    for entry in middleware_log:
        print(f"  {entry}")

    # Section 5: middleware order demonstration
    print("\n[4] Middleware execution order (outermost → innermost):")
    print("  Request:  CorrelationID → Timing → Auth → Route")
    print("  Response: Route → Auth → Timing → CorrelationID")
    print("  (add_middleware: last added = outermost = first to see request)")

    # Section 6: echo to verify ContextVar works across async boundary
    print("\n[5] ContextVar works across async request:")
    r = client.get("/echo-headers", headers={"X-Request-ID": "ctx-test"})
    data = r.json()
    print(f"  request.state.request_id = {data['request_id']!r}")
    print(f"  request_id_var.get()     = {data['ctx_var']!r}")
    print(f"  Both match: {data['request_id'] == data['ctx_var']}")

    print("\n" + "=" * 55)
