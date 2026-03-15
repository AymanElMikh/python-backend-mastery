# FastAPI Lifespan Events — Startup, Shutdown, `@asynccontextmanager`

## 🎯 Interview Question
How do you manage application-level resources in FastAPI? Explain the `lifespan` parameter introduced in FastAPI 0.93, why it replaces `@app.on_event`, and how you share lifespan-managed resources across requests.

## 💡 Short Answer (30 seconds)
`lifespan` is an async context manager passed to `FastAPI()` that runs setup before the app starts serving and teardown when it shuts down. It replaces the deprecated `@app.on_event("startup")` / `@app.on_event("shutdown")` decorators. Resources created in lifespan (DB connection pools, ML models, Redis clients) are shared via `request.app.state` — an attribute bag attached to the app instance.

## 🔬 Deep Explanation

### Why lifespan replaced `on_event`
`@app.on_event` was split into two separate decorators with no relationship — easy to forget one, hard to ensure teardown always runs on startup failure. `lifespan` uses `@asynccontextmanager` so the `finally` block guarantees cleanup regardless of startup errors. It's also testable — `TestClient` runs the lifespan automatically.

### The pattern
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ────────────────────────────────────
    pool = await create_db_pool()
    redis = await aioredis.create_redis_pool(REDIS_URL)
    app.state.db_pool = pool
    app.state.redis = redis

    yield  # ← app is running and serving requests

    # ── SHUTDOWN ───────────────────────────────────
    await pool.close()
    await redis.close()

app = FastAPI(lifespan=lifespan)
```

### `app.state` — sharing resources
`app.state` is a `State` object (from Starlette) that allows arbitrary attribute assignment. It's the standard way to share app-level resources without global variables:
```python
@app.get("/items")
async def get_items(request: Request):
    db = request.app.state.db_pool
    # or via dependency:
async def get_db(request: Request):
    return request.app.state.db_pool
```

### DI + lifespan — the full pattern
Combine lifespan (for pool creation) with `Depends` (for per-request connections from the pool):
```python
async def get_db(request: Request):
    async with request.app.state.db_pool.acquire() as conn:
        yield conn
```

### Multiple resources — composition
Use nested `asynccontextmanager` calls or `AsyncExitStack` for multiple resources:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        app.state.db = await stack.enter_async_context(create_db_pool())
        app.state.cache = await stack.enter_async_context(create_redis())
        yield
    # AsyncExitStack closes all resources on exit
```

### Testing with lifespan
`TestClient` triggers the lifespan automatically:
```python
def test_items():
    with TestClient(app) as client:  # lifespan runs here
        response = client.get("/items")
    # lifespan cleanup runs when TestClient exits
```

### Router-level lifespan (FastAPI 0.99+)
Routers can have their own lifespan — useful for modular apps where each module manages its own resources.

### `@app.on_event` — legacy
Still works but deprecated since 0.93. The problem: if startup raises, shutdown doesn't run. With `lifespan`, the `finally` in `asynccontextmanager` always runs.

## 💻 Code Example

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

startup_log = []
shutdown_log = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──
    startup_log.append("DB pool opened")
    app.state.db_pool = {"pool": "fake-pool", "size": 10}
    app.state.model = {"name": "bert-base", "loaded": True}
    startup_log.append("ML model loaded")

    yield  # app serves requests

    # ── SHUTDOWN ── (always runs)
    shutdown_log.append("DB pool closed")
    shutdown_log.append("ML model unloaded")

app = FastAPI(lifespan=lifespan)

@app.get("/status")
async def status(request: Request):
    return {
        "db_pool": request.app.state.db_pool["pool"],
        "model":   request.app.state.model["name"],
    }
```

## ⚠️ Common Mistakes & Interview Traps

1. **Global variables instead of `app.state`**: Using module-level globals for shared resources works but is not testable or reloadable. `app.state` ties resources to the app instance — multiple test apps don't interfere.

2. **`@app.on_event` doesn't guarantee shutdown on startup failure**: If startup raises mid-way, shutdown never runs. `lifespan`'s `finally` block always runs.

3. **Not yielding in lifespan**: Forgetting the `yield` statement means the app starts but the shutdown code runs immediately. FastAPI raises `RuntimeError: Lifespan generator did not yield`.

4. **Sync vs async lifespan**: If your resource setup is sync (e.g., loading a model from disk), wrap it with `asyncio.to_thread()` inside `async def lifespan`. Don't block the event loop during startup.

5. **`TestClient` as context manager**: When testing lifespan, use `with TestClient(app) as client:`. Using `client = TestClient(app)` without `with` still works but lifespan cleanup timing depends on GC.

## 🔗 Related Concepts
- `fastapi/021_dependency_injection` — `request.app.state` + `Depends` is the access pattern
- `fastapi/023_middleware` — middleware also sees the full request/response lifecycle
- `async_python/` — `asynccontextmanager` is built on generators + `async with`

## 📚 Go Deeper
- FastAPI docs: "Lifespan Events" — includes router-level lifespan
- Starlette source: `applications.py` — `Router.lifespan_context` implementation
