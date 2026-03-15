"""
Demo: FastAPI Response Models & Status Codes
Run:  python demo.py
"""

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, ConfigDict

app = FastAPI()

# ── Models ────────────────────────────────────────────────────────────────────
class UserDB(BaseModel):
    """Internal model — includes sensitive fields."""
    id: int
    name: str
    email: str
    hashed_password: str
    internal_notes: str = ""

class UserOut(BaseModel):
    """Public model — what the API returns."""
    id: int
    name: str
    email: str

class UserCreate(BaseModel):
    name: str = Field(min_length=2)
    email: str
    password: str = Field(min_length=8)

class UserPatch(BaseModel):
    name: str | None = None
    email: str | None = None

class ErrorDetail(BaseModel):
    code: str
    message: str
    detail: dict = {}

# ── In-memory "database" ──────────────────────────────────────────────────────
db: dict[int, UserDB] = {
    1: UserDB(id=1, name="Alice", email="alice@ex.com",
              hashed_password="$2b$hash1", internal_notes="VIP"),
    2: UserDB(id=2, name="Bob",   email="bob@ex.com",
              hashed_password="$2b$hash2", internal_notes="suspended"),
}
next_id = 3

# ── Section 1: response_model strips sensitive fields ─────────────────────────
@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(body: UserCreate):
    global next_id
    user = UserDB(
        id=next_id,
        name=body.name,
        email=body.email,
        hashed_password=f"hashed:{body.password}",
    )
    db[next_id] = user
    next_id += 1
    return user  # FastAPI filters through UserOut — hashed_password stripped


@app.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int):
    if user_id not in db:
        return JSONResponse(status_code=404, content={"detail": "User not found"})
    return db[user_id]


# ── Section 2: response_model_exclude_unset for PATCH ─────────────────────────
@app.patch(
    "/users/{user_id}",
    response_model=UserOut,
    response_model_exclude_unset=True,  # only include fields that were set
)
async def patch_user(user_id: int, patch: UserPatch):
    if user_id not in db:
        return JSONResponse(status_code=404, content={"detail": "not found"})
    user = db[user_id]
    update_data = patch.model_dump(exclude_unset=True)  # only explicitly set fields
    updated = user.model_copy(update=update_data)
    db[user_id] = updated
    return updated


# ── Section 3: 204 No Content — no body ──────────────────────────────────────
@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    db.pop(user_id, None)
    # Return value is ignored — 204 has no body


# ── Section 4: Multiple response types documented ─────────────────────────────
@app.get(
    "/users/{user_id}/export",
    response_model=UserOut,
    responses={
        200: {"description": "User data as JSON"},
        404: {"model": ErrorDetail, "description": "User not found"},
    },
)
async def export_user(user_id: int, fmt: str = "json"):
    if user_id not in db:
        return JSONResponse(
            status_code=404,
            content=ErrorDetail(code="NOT_FOUND", message=f"User {user_id} not found").model_dump()
        )
    user = db[user_id]
    if fmt == "text":
        return PlainTextResponse(f"ID: {user.id}\nName: {user.name}\nEmail: {user.email}")
    return user


# ── Section 5: StreamingResponse ──────────────────────────────────────────────
@app.get("/users/export/csv")
async def export_csv():
    async def generate():
        yield "id,name,email\n"
        for user in db.values():
            yield f"{user.id},{user.name},{user.email}\n"
    return StreamingResponse(generate(), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=users.csv"})


if __name__ == "__main__":
    client = TestClient(app)

    print("=" * 55)
    print("DEMO: FastAPI Response Models & Status Codes")
    print("=" * 55)

    # Section 1: response_model strips sensitive fields
    print("\n[1] response_model — strips hashed_password and internal_notes:")
    r = client.post("/users", json={"name": "Charlie", "email": "c@x.com", "password": "s3cr3t!1"})
    print(f"  POST /users → {r.status_code}: {r.json()}")
    print(f"  'hashed_password' in response: {'hashed_password' in r.json()}")
    print(f"  'internal_notes' in response:  {'internal_notes' in r.json()}")

    r = client.get("/users/1")
    print(f"  GET /users/1 → {r.json()}")
    print(f"  'hashed_password' leaked: {'hashed_password' in r.json()}")

    # Section 2: PATCH with exclude_unset
    print("\n[2] PATCH + response_model_exclude_unset:")
    r = client.patch("/users/1", json={"name": "Alice Updated"})
    data = r.json()
    print(f"  PATCH name only → {data}")
    print(f"  'email' in response: {'email' in data}  (exclude_unset drops unchanged fields)")

    # Section 3: 204 No Content
    print("\n[3] DELETE → 204 No Content:")
    r = client.delete("/users/2")
    print(f"  DELETE /users/2 → {r.status_code}, body={r.text!r}")

    # Section 4: multiple response types
    print("\n[4] Multiple response formats:")
    r = client.get("/users/1/export")
    print(f"  JSON: {r.json()}")
    r = client.get("/users/1/export?fmt=text")
    print(f"  Text: {r.text!r}")
    r = client.get("/users/99/export")
    print(f"  Not found: {r.status_code} {r.json()}")

    # Section 5: streaming
    print("\n[5] StreamingResponse — CSV export:")
    r = client.get("/users/export/csv")
    print(f"  Content-Type: {r.headers['content-type']}")
    print(f"  Body:\n{r.text}")

    print("\n" + "=" * 55)
