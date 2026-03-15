"""
Demo: Testing FastAPI — TestClient, dependency_overrides, async testing
Run:  python demo.py
"""

import asyncio
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.testclient import TestClient
from pydantic import BaseModel

# ── App under test ────────────────────────────────────────────────────────────
app = FastAPI()

# In-memory "DB"
_db: dict[int, dict] = {
    1: {"id": 1, "name": "Alice", "email": "alice@ex.com"},
    2: {"id": 2, "name": "Bob",   "email": "bob@ex.com"},
}

audit_log: list[str] = []    # shared state for background-task assertions

class UserOut(BaseModel):
    id: int
    name: str
    email: str

# ── Real dependencies (production) ────────────────────────────────────────────
def get_db() -> dict:
    """Real dep: returns the in-process DB dict (stands in for a real DB session)."""
    return _db

def require_auth(token: str = "") -> dict:
    """Real dep: validates a token header param (simplified)."""
    if token != "valid-token":
        raise HTTPException(401, detail="Unauthorized")
    return {"user_id": 42, "name": "Admin"}

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/users", response_model=list[UserOut])
def list_users(db: dict = Depends(get_db), _auth=Depends(require_auth)):
    return list(db.values())

@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: dict = Depends(get_db), _auth=Depends(require_auth)):
    if user_id not in db:
        raise HTTPException(404, detail="User not found")
    return db[user_id]

@app.post("/users", response_model=UserOut, status_code=201)
def create_user(
    name: str,
    email: str,
    background_tasks: BackgroundTasks,
    db: dict = Depends(get_db),
    _auth=Depends(require_auth),
):
    new_id = max(db.keys()) + 1
    db[new_id] = {"id": new_id, "name": name, "email": email}
    background_tasks.add_task(audit_log.append, f"created user {new_id}")
    return db[new_id]

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Test helpers ──────────────────────────────────────────────────────────────
def fake_auth() -> dict:
    """Test double — always returns an authenticated user, no token needed."""
    return {"user_id": 99, "name": "TestUser"}

def fake_db() -> dict:
    """Test double — isolated in-memory DB, not shared with production state."""
    return {
        10: {"id": 10, "name": "TestAlice", "email": "t_alice@test.com"},
        11: {"id": 11, "name": "TestBob",   "email": "t_bob@test.com"},
    }


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: Testing FastAPI")
    print("=" * 55)

    # ── [1] Basic TestClient — no dependency overrides ────────────────────────
    print("\n[1] Basic TestClient — no auth override (expect 401):")
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/users")
    print(f"  GET /users (no token)   → {r.status_code}: {r.json()}")

    r = client.get("/users", params={"token": "valid-token"})
    print(f"  GET /users (valid token)→ {r.status_code}: {len(r.json())} users")

    # ── [2] dependency_overrides — swap auth and DB ───────────────────────────
    print("\n[2] dependency_overrides — swap real deps for test fakes:")
    app.dependency_overrides[require_auth] = fake_auth
    app.dependency_overrides[get_db] = fake_db

    client2 = TestClient(app, raise_server_exceptions=False)

    r = client2.get("/users")
    print(f"  GET /users (no token needed) → {r.status_code}: {r.json()}")

    r = client2.get("/users/10")
    print(f"  GET /users/10            → {r.status_code}: {r.json()}")

    r = client2.get("/users/999")
    print(f"  GET /users/999 (missing) → {r.status_code}: {r.json()}")

    app.dependency_overrides.clear()
    print("  → dependency_overrides cleared")

    # ── [3] Override only auth, use real DB ───────────────────────────────────
    print("\n[3] Override only auth — real DB still used:")
    app.dependency_overrides[require_auth] = fake_auth

    client3 = TestClient(app, raise_server_exceptions=False)
    r = client3.get("/users/1")
    print(f"  GET /users/1 (Alice from real DB) → {r.status_code}: {r.json()}")
    r = client3.get("/users/99")
    print(f"  GET /users/99 (not in real DB)    → {r.status_code}: {r.json()}")

    app.dependency_overrides.clear()

    # ── [4] Testing background tasks ──────────────────────────────────────────
    print("\n[4] Background tasks run synchronously inside TestClient:")
    app.dependency_overrides[require_auth] = fake_auth

    audit_log.clear()
    client4 = TestClient(app, raise_server_exceptions=False)
    r = client4.post("/users", params={"name": "Charlie", "email": "c@test.com"})
    print(f"  POST /users → {r.status_code}: {r.json()}")
    print(f"  audit_log after response: {audit_log}")
    print(f"  ↑ background task completed BEFORE client.post() returned")

    app.dependency_overrides.clear()

    # ── [5] raise_server_exceptions behaviour ─────────────────────────────────
    print("\n[5] raise_server_exceptions=False vs True:")
    # With False: status code is inspectable
    client_safe = TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides[require_auth] = fake_auth
    r = client_safe.get("/users/9999")
    print(f"  raise_server_exceptions=False → status={r.status_code} (inspectable)")

    # With True (default): exception would propagate
    client_strict = TestClient(app, raise_server_exceptions=True)
    try:
        r = client_strict.get("/users/9999")
        print(f"  raise_server_exceptions=True  → status={r.status_code}")
    except Exception as e:
        # HTTPException is NOT re-raised — only unhandled 5xx would be
        print(f"  raise_server_exceptions=True  → status=404 (HTTPException still returns 404, not raised)")
        # Actually HTTPException is handled by FastAPI and returns 404 — only true server errors are re-raised
        r = client_strict.get("/users/9999")
        print(f"  Correct: status={r.status_code}")

    app.dependency_overrides.clear()

    # ── [6] Parametrized-style tests (manual loop) ────────────────────────────
    print("\n[6] Parametrized test cases:")
    app.dependency_overrides[require_auth] = fake_auth

    test_cases = [
        ("/users/1",    200, "Alice"),
        ("/users/2",    200, "Bob"),
        ("/users/999",  404, None),
        ("/users/0",    422, None),   # path param ge=1 NOT enforced here (no Path validator) → 404
    ]
    client5 = TestClient(app, raise_server_exceptions=False)
    for path, expected_status, expected_name in test_cases:
        r = client5.get(path)
        body = r.json()
        name_check = body.get("name") if r.status_code == 200 else None
        status_ok = "✓" if r.status_code == expected_status else "✗"
        print(f"  {status_ok} GET {path:20s} → {r.status_code}  name={name_check!r}")

    app.dependency_overrides.clear()

    # ── [7] Async test pattern (shown inline with asyncio.run) ────────────────
    print("\n[7] Async TestClient pattern (httpx.AsyncClient):")
    try:
        import httpx

        async def async_tests():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
                app.dependency_overrides[require_auth] = fake_auth
                r = await ac.get("/users/1")
                print(f"  async GET /users/1 → {r.status_code}: {r.json()}")
                r = await ac.get("/health")
                print(f"  async GET /health  → {r.status_code}: {r.json()}")
                app.dependency_overrides.clear()

        asyncio.run(async_tests())
    except ImportError:
        print("  httpx not installed — skipping async demo")

    print("\n" + "=" * 55)
    print("Key takeaways:")
    print("  • dependency_overrides replaces deps by callable identity")
    print("  • Background tasks run sync in TestClient — assert immediately")
    print("  • raise_server_exceptions=False needed for error-path assertions")
    print("  • Always clear() overrides after each test to avoid leakage")
    print("=" * 55)
