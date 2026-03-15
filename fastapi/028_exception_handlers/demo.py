"""
Demo: FastAPI Exception Handlers — HTTPException, Custom Handlers, 422
Run:  python demo.py
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

# ── Custom exception hierarchy ────────────────────────────────────────────────
class AppError(Exception):
    """Base for all application-level errors."""
    def __init__(self, message: str, code: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status

class NotFoundError(AppError):
    def __init__(self, resource: str, id):
        super().__init__(f"{resource} with id={id!r} not found", "NOT_FOUND", 404)

class ConflictError(AppError):
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT", 409)

class BusinessRuleError(AppError):
    def __init__(self, rule: str, detail: str):
        super().__init__(detail, f"BUSINESS_RULE:{rule}", 422)


# ── Build app ─────────────────────────────────────────────────────────────────
app = FastAPI()

# ── Exception handlers ────────────────────────────────────────────────────────

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """Handles all AppError subclasses — single point of truth."""
    return JSONResponse(
        status_code=exc.status,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "path": str(request.url.path),
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Override the default 422 format with a cleaner structure."""
    fields = []
    for error in exc.errors():
        loc = " → ".join(str(l) for l in error["loc"] if l != "body")
        fields.append({"field": loc or "root", "message": error["msg"], "type": error["type"]})
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_FAILED",
                "message": f"{len(fields)} validation error(s)",
                "fields": fields,
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Enrich HTTPException responses with request path."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "path": str(request.url.path),
            }
        },
        headers=exc.headers or {},
    )


# ── Routes ────────────────────────────────────────────────────────────────────
db: dict[int, dict] = {
    1: {"id": 1, "name": "Alice", "balance": 1000.0},
    2: {"id": 2, "name": "Bob",   "balance": 50.0},
}

class TransferRequest(BaseModel):
    from_id: int = Field(ge=1)
    to_id: int = Field(ge=1)
    amount: float = Field(gt=0)


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    if user_id not in db:
        raise NotFoundError("User", user_id)
    return db[user_id]


@app.post("/users")
async def create_user(name: str):
    existing = [u for u in db.values() if u["name"] == name]
    if existing:
        raise ConflictError(f"User with name {name!r} already exists")
    new_id = max(db.keys()) + 1
    db[new_id] = {"id": new_id, "name": name, "balance": 0.0}
    return db[new_id]


@app.post("/transfer")
async def transfer(req: TransferRequest):
    if req.from_id not in db:
        raise NotFoundError("User", req.from_id)
    if req.to_id not in db:
        raise NotFoundError("User", req.to_id)
    if req.from_id == req.to_id:
        raise BusinessRuleError("SELF_TRANSFER", "Cannot transfer to yourself")
    sender = db[req.from_id]
    if sender["balance"] < req.amount:
        raise BusinessRuleError(
            "INSUFFICIENT_FUNDS",
            f"Balance {sender['balance']} < requested {req.amount}"
        )
    db[req.from_id]["balance"] -= req.amount
    db[req.to_id]["balance"] += req.amount
    return {"status": "ok", "from_balance": db[req.from_id]["balance"]}


@app.get("/crash")
async def crash():
    raise HTTPException(status_code=503, detail="Service temporarily unavailable",
                        headers={"Retry-After": "30"})


if __name__ == "__main__":
    client = TestClient(app, raise_server_exceptions=False)

    print("=" * 55)
    print("DEMO: FastAPI Exception Handlers")
    print("=" * 55)

    # Custom AppError subclasses
    print("\n[1] Custom exception hierarchy:")
    r = client.get("/users/99")
    print(f"  NotFoundError   → {r.status_code}: {r.json()}")

    r = client.post("/users?name=Alice")
    print(f"  ConflictError   → {r.status_code}: {r.json()}")

    r = client.post("/transfer", json={"from_id": 2, "to_id": 1, "amount": 999.0})
    print(f"  BusinessRule    → {r.status_code}: {r.json()}")

    r = client.post("/transfer", json={"from_id": 1, "to_id": 1, "amount": 10.0})
    print(f"  Self-transfer   → {r.status_code}: {r.json()}")

    # Successful transfer
    r = client.post("/transfer", json={"from_id": 1, "to_id": 2, "amount": 100.0})
    print(f"  Valid transfer  → {r.status_code}: {r.json()}")

    # Custom 422 format
    print("\n[2] Custom validation error format (422):")
    r = client.post("/transfer", json={"from_id": -1, "to_id": 0, "amount": -5})
    print(f"  Invalid body → {r.status_code}:")
    err = r.json()["error"]
    print(f"    code: {err['code']!r}")
    print(f"    fields: {err['fields']}")

    # HTTPException enriched
    print("\n[3] HTTPException with enriched format:")
    r = client.get("/crash")
    print(f"  /crash → {r.status_code}: {r.json()}")
    print(f"  Retry-After header: {r.headers.get('retry-after')!r}")

    # Happy path
    print("\n[4] Happy path:")
    r = client.get("/users/1")
    print(f"  GET /users/1 → {r.json()}")

    print("\n" + "=" * 55)
