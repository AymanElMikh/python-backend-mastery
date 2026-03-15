# FastAPI Dependency Injection — `Depends`

## 🎯 Interview Question
How does FastAPI's dependency injection system work? Explain the dependency resolution tree, the difference between function dependencies and class dependencies, and how dependency scoping (per-request vs cached) works.

## 💡 Short Answer (30 seconds)
FastAPI's DI uses `Depends(callable)` — at request time, FastAPI inspects the route function's signature, finds `Depends` annotations, calls each dependency (recursively resolving their own dependencies), and injects the results. Dependencies are called once per request by default — if the same dependency appears multiple times in the tree, FastAPI calls it only once and caches the result within that request (`use_cache=True`). Class-based dependencies use `__call__` or `__init__` for configuration.

## 🔬 Deep Explanation

### How `Depends` works
FastAPI uses Python's `inspect.signature` to analyze route function parameters. When a parameter is annotated with `Depends(some_callable)`:
1. FastAPI calls `some_callable` with its own parameters (which may themselves have `Depends`)
2. The return value is injected as the parameter's value
3. This is recursive — a full dependency tree is resolved before the route runs

The callable can be:
- A plain function (`def` or `async def`)
- A class (called via `__init__`, instance is injected)
- Any callable (class with `__call__`)

### Request-scoped caching
`Depends(dep, use_cache=True)` (default) — if the same dependency appears multiple times in a request's dependency tree, it's called once and the result cached. `use_cache=False` forces a fresh call each time.

```python
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Both route and sub-dependency get the SAME db session within one request:
async def get_user(db=Depends(get_db)): ...
async def route(db=Depends(get_db), user=Depends(get_user)): ...
# get_db() called once — both db and user's db are the same session
```

### Generator dependencies (yield)
Dependencies that `yield` act as context managers:
- Code before `yield` = setup (runs before route handler)
- The yielded value is injected
- Code after `yield` = teardown (runs after response is sent, even on exception)

This is the pattern for DB sessions, acquiring locks, etc.

### Class-based dependencies — configuration
```python
class Paginator:
    def __init__(self, page: int = 1, page_size: int = 20):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size

# Usage: Depends(Paginator) — FastAPI calls Paginator(page=..., page_size=...)
# The Paginator INSTANCE is injected (not the class)
```

### Path operation dependencies (`dependencies=`)
Dependencies that don't need to return a value (auth checks, rate limiting, logging):
```python
@app.get("/items", dependencies=[Depends(verify_token), Depends(check_rate_limit)])
async def get_items(): ...
```
No parameter needed in the route signature.

### Global dependencies
`app = FastAPI(dependencies=[Depends(verify_api_key)])` — applied to every route.

### Sub-applications and dependency overriding
`app.dependency_overrides[original_dep] = mock_dep` — used in tests to swap dependencies (e.g., real DB → in-memory DB) without modifying route code.

## 💻 Code Example

```python
from fastapi import FastAPI, Depends, HTTPException, Header
from typing import Annotated

app = FastAPI()

# Simple function dependency
async def get_db():
    """Yield a DB session; close after request."""
    db = {"connected": True}  # simulate DB
    try:
        yield db
    finally:
        db["connected"] = False

# Class-based dependency for config
class Paginator:
    def __init__(self, page: int = 1, size: int = 20):
        self.offset = (page - 1) * size
        self.limit = size

# Auth dependency — raises if invalid
async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "secret":
        raise HTTPException(status_code=401, detail="Invalid token")
    return x_token

# Dependency tree: route → verify_token + paginator + db
@app.get("/users")
async def list_users(
    token: Annotated[str, Depends(verify_token)],
    pages: Annotated[Paginator, Depends(Paginator)],
    db=Depends(get_db),
):
    return {"offset": pages.offset, "limit": pages.limit, "db": db["connected"]}
```

## ⚠️ Common Mistakes & Interview Traps

1. **`Depends` in a type annotation vs as a default**: Modern FastAPI uses `Annotated[Type, Depends(...)]`. The old style `param: Type = Depends(...)` still works but `Annotated` is preferred (clearer, composable).

2. **Async vs sync dependencies**: FastAPI runs sync dependencies in a thread pool (`run_in_executor`). Mixing sync DB calls in an async app adds latency. Always use async-compatible dependencies in async apps.

3. **`yield` dependencies and exceptions**: If the route raises an exception, teardown code (after `yield`) still runs. Wrap teardown in `try/finally` to handle both normal and error paths.

4. **`use_cache=False` for stateful dependencies**: If a dependency maintains state (e.g., a counter), you may need `use_cache=False` to get a fresh instance per call site.

5. **Class dependencies inject the instance, not the class**: `Depends(MyClass)` calls `MyClass(...)` and injects the resulting instance. It does NOT inject the class itself.

## 🔗 Related Concepts
- `fastapi/022_lifespan` — lifespan manages app-level resources, DI manages request-level
- `fastapi/028_exception_handlers` — DI dependencies can raise `HTTPException`
- `fastapi/030_testing_fastapi` — `dependency_overrides` is the test pattern for DI

## 📚 Go Deeper
- FastAPI docs: "Dependencies" — full coverage including security dependencies
- Starlette source: `routing.py` — how `Depends` is resolved in `run_endpoint_function`
