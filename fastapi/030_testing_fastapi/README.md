# Testing FastAPI — TestClient, AsyncClient, dependency_overrides

## 🎯 Interview Question
How do you test a FastAPI application? Explain `TestClient`, async testing with `httpx.AsyncClient`, `dependency_overrides`, and how to test auth, background tasks, and error paths without hitting real infrastructure.

## 💡 Short Answer (30 seconds)
FastAPI ships with `TestClient` (a thin `requests`-based wrapper around Starlette's ASGI transport) for sync tests. For async tests use `httpx.AsyncClient` with `ASGITransport`. The key power tool is `app.dependency_overrides` — a dict that swaps real dependencies for test fakes at test time. Override your DB session, auth, or external clients; the route code sees the fake but thinks it's real.

## 🔬 Deep Explanation

### TestClient — sync, zero server spin-up
```python
from fastapi.testclient import TestClient
client = TestClient(app)
```
`TestClient` wraps `httpx.Client` with Starlette's `ASGITransport`. Requests never leave the process — the ASGI app handles them in the same thread. Lifespan events (`startup`/`shutdown`) run on `__enter__`/`__exit__`, so use it as a context manager when you need lifespan:
```python
with TestClient(app) as client:
    # lifespan ran — app.state.db is available
    r = client.get("/items")
```

### AsyncClient — async tests (pytest-anyio / anyio)
```python
import httpx
from httpx import ASGITransport

async def test_async():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/items")
        assert r.status_code == 200
```
Required when your routes use `async def` and you want to test them from an async test function — or when you need true `asyncio.sleep` / task behavior verified.

### dependency_overrides — the canonical DI injection point for tests
```python
def get_db():   # real dep — opens DB session
    ...

def fake_db():  # test fake — returns in-memory data
    return FakeSession()

app.dependency_overrides[get_db] = fake_db

# After tests:
app.dependency_overrides.clear()
```
Key behaviour:
- Overrides are matched by **identity** of the dependency callable, not by name.
- Overrides apply to all routes that `Depends(get_db)` — including transitive deps.
- The override callable's own signature is still resolved (its params are injected from the request).
- Always `clear()` in teardown — stale overrides bleed between tests.

### Testing authentication
Two patterns:

**Pattern A — override the auth dependency:**
```python
app.dependency_overrides[require_auth] = lambda: {"user_id": 99, "name": "TestUser"}
```
The route never sees JWT processing; it gets the fake user dict directly.

**Pattern B — send a real (or mock) token:**
```python
client.get("/protected", headers={"Authorization": "Bearer test-secret"})
```
Useful for testing the auth dependency itself.

### Testing exception handlers
`TestClient` by default re-raises server exceptions (for clean test failure messages). For error-path tests use `raise_server_exceptions=False`:
```python
client = TestClient(app, raise_server_exceptions=False)
r = client.get("/users/999")
assert r.status_code == 404
```
Or pass `raise_server_exceptions=False` to the context manager constructor.

### Testing background tasks
Background tasks run **synchronously** inside `TestClient` after the response is sent (Starlette flushes them before closing the ASGI scope). This means by the time `client.post(...)` returns, all background tasks have completed — you can assert their side-effects immediately.

### Parametrized tests with pytest
```python
import pytest

@pytest.mark.parametrize("user_id,expected", [(1, 200), (999, 404), (-1, 422)])
def test_get_user(user_id, expected):
    r = client.get(f"/users/{user_id}")
    assert r.status_code == expected
```

### Fixtures for shared setup
```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client(app):
    app.dependency_overrides[get_db] = fake_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

## 💻 Code Example

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient

app = FastAPI()

def get_db():
    return {"users": {1: {"id": 1, "name": "Alice"}}}

def require_auth(token: str = ""):
    if token != "valid":
        raise HTTPException(401, "Unauthorized")
    return {"user_id": 1}

@app.get("/users/{uid}")
def get_user(uid: int, db=Depends(get_db), user=Depends(require_auth)):
    if uid not in db["users"]:
        raise HTTPException(404, "Not found")
    return db["users"][uid]

# ── Test: override auth and DB ─────────────────────────────────
app.dependency_overrides[require_auth] = lambda: {"user_id": 99}
app.dependency_overrides[get_db] = lambda: {"users": {1: {"id": 1, "name": "Alice"}}}

client = TestClient(app, raise_server_exceptions=False)

r = client.get("/users/1")
assert r.status_code == 200   # no real JWT needed

r = client.get("/users/99")
assert r.status_code == 404   # not in fake DB

app.dependency_overrides.clear()
```

## ⚠️ Common Mistakes & Interview Traps

1. **Forgetting `raise_server_exceptions=False`**: By default `TestClient` re-raises 5xx exceptions as Python exceptions. Your `assert r.status_code == 500` test crashes before it can check the status code. Use `raise_server_exceptions=False` for error-path tests.

2. **Stale `dependency_overrides`**: Not calling `app.dependency_overrides.clear()` in teardown lets overrides leak into other tests. Use a pytest fixture with `yield` + cleanup, or `app.dependency_overrides = {}`.

3. **Override matched by identity, not name**: If you import `get_db` in two places and override one import, the other import is a different object — the override won't apply. Always import from the same module and override the canonical reference.

4. **Lifespan not running without context manager**: `TestClient(app).get("/")` without `with TestClient(app) as c:` skips lifespan. If your route uses `app.state.db_pool`, it'll `AttributeError`. Always use the context manager when lifespan matters.

5. **Background tasks in async tests**: In `httpx.AsyncClient` (not `TestClient`), background tasks may not complete before `await client.post(...)` returns — they're scheduled on the event loop. Verify via a shared state mock or don't rely on their completion being synchronous.

6. **Testing `response_model` filtering**: The response body is already filtered — you're testing the serialized output, not the raw return value. If `hashed_password` appears in the response, it means `response_model` isn't set correctly, not that the route returned it.

## 🔗 Related Concepts
- `fastapi/021_dependency_injection` — `Depends()` is what `dependency_overrides` patches
- `fastapi/022_lifespan` — lifespan runs in `TestClient` context manager
- `fastapi/024_background_tasks` — background tasks run sync inside `TestClient`
- `fastapi/028_exception_handlers` — test with `raise_server_exceptions=False`

## 📚 Go Deeper
- Starlette test client source: `starlette/testclient.py` — see `_ASGIAdapter` and how it drives the ASGI lifecycle
- `anyio` / `pytest-anyio` — async test runner for true async FastAPI test suites
