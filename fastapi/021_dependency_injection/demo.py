"""
Demo: FastAPI Dependency Injection — Depends
Run:  python demo.py
"""

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.testclient import TestClient
from typing import Annotated

app = FastAPI()

# ── Dependency 1: Generator (yield) — simulated DB session ───────────────────
db_calls = []

async def get_db():
    """Setup before yield, teardown after — like a context manager."""
    session = {"id": id(object()), "open": True}
    db_calls.append(f"OPEN  session {session['id']}")
    try:
        yield session
    finally:
        session["open"] = False
        db_calls.append(f"CLOSE session {session['id']}")


# ── Dependency 2: Class-based — configuration via __init__ ───────────────────
class Paginator:
    def __init__(self, page: int = 1, size: int = 10):
        if page < 1:
            raise HTTPException(status_code=422, detail="page must be >= 1")
        self.page = page
        self.size = size
        self.offset = (page - 1) * size

    def __repr__(self):
        return f"Paginator(page={self.page}, size={self.size}, offset={self.offset})"


# ── Dependency 3: Auth check — raises, no return value needed ────────────────
async def verify_token(x_token: Annotated[str | None, Header()] = None):
    if x_token != "secret-token":
        raise HTTPException(status_code=401, detail="Invalid or missing X-Token")
    return x_token


# ── Dependency 4: Sub-dependency (get_current_user depends on get_db) ─────────
async def get_current_user(db=Depends(get_db)):
    # In real code: query DB using the session
    return {"user_id": 42, "name": "Alice", "db_session_id": db["id"]}


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/items")
async def list_items(
    pages: Annotated[Paginator, Depends(Paginator)],
    db=Depends(get_db),
):
    return {
        "offset": pages.offset,
        "limit": pages.size,
        "db_open": db["open"],
        "items": [f"item_{i}" for i in range(pages.offset, pages.offset + pages.size)],
    }


@app.get("/me", dependencies=[Depends(verify_token)])
async def get_me(user=Depends(get_current_user)):
    # verify_token runs but its return value isn't needed here
    return user


@app.get("/shared-db")
async def shared_db_demo(
    db=Depends(get_db),
    user=Depends(get_current_user),  # also calls Depends(get_db) internally
):
    # get_db is cached — both db and user share THE SAME session
    return {
        "route_db_id":  db["id"],
        "user_db_id":   user["db_session_id"],
        "same_session": db["id"] == user["db_session_id"],
    }


if __name__ == "__main__":
    client = TestClient(app)

    print("=" * 55)
    print("DEMO: FastAPI Dependency Injection — Depends")
    print("=" * 55)

    # Test 1: pagination
    print("\n[1] Paginator class-based dependency:")
    r = client.get("/items?page=2&size=5")
    print(f"  GET /items?page=2&size=5 → {r.status_code}")
    data = r.json()
    print(f"  offset={data['offset']}, limit={data['limit']}, items={data['items']}")

    r = client.get("/items?page=0")
    print(f"  GET /items?page=0 → {r.status_code} {r.json()['detail']}")

    # Test 2: auth dependency
    print("\n[2] Auth dependency — verify_token:")
    r = client.get("/me", headers={"X-Token": "secret-token"})
    print(f"  With valid token:   {r.status_code} → {r.json()}")
    r = client.get("/me", headers={"X-Token": "wrong"})
    print(f"  With invalid token: {r.status_code} → {r.json()}")
    r = client.get("/me")
    print(f"  No token:           {r.status_code} → {r.json()}")

    # Test 3: shared DB session (use_cache=True default)
    print("\n[3] Dependency caching — same DB session shared:")
    db_calls.clear()
    r = client.get("/shared-db")
    data = r.json()
    print(f"  route_db_id == user_db_id: {data['same_session']}  ← same session!")
    print(f"  DB lifecycle: {db_calls}")
    print(f"  (get_db called once despite two Depends(get_db) in tree)")

    # Test 4: generator teardown
    print("\n[4] Generator teardown — runs after response:")
    db_calls.clear()
    r = client.get("/items?page=1&size=3")
    print(f"  DB calls: {db_calls}")
    print(f"  (CLOSE happens after response is sent)")

    print("\n" + "=" * 55)
