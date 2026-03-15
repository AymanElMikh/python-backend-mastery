"""
Demo: FastAPI Path, Query & Body Parameters
Run:  python demo.py
"""

from fastapi import FastAPI, Path, Query, Body, Header, Cookie
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, computed_field
from typing import Annotated

app = FastAPI()

# ── Reusable param definitions via Annotated ──────────────────────────────────
PageParam = Annotated[int, Query(ge=1, description="Page number (1-based)")]
SizeParam = Annotated[int, Query(ge=1, le=100, description="Items per page")]
ItemID    = Annotated[int, Path(ge=1, description="Unique item identifier")]

# ── Section 1: Path params with validation ────────────────────────────────────
@app.get("/catalog/{category}/{item_id}")
async def get_item(
    category: Annotated[str, Path(min_length=2, pattern=r"^[a-z\-]+$")],
    item_id: ItemID,
    include_tax: Annotated[bool, Query()] = False,
    fields: Annotated[list[str], Query()] = [],
):
    return {
        "category": category,
        "item_id": item_id,
        "include_tax": include_tax,
        "fields": fields,
    }


# ── Section 2: Multi-value query params ──────────────────────────────────────
@app.get("/search")
async def search(
    q: Annotated[str | None, Query(min_length=2, description="Search query")] = None,
    tags: Annotated[list[str], Query(description="Filter by tags")] = [],
    page: PageParam = 1,
    size: SizeParam = 20,
):
    return {
        "query": q,
        "tags": tags,
        "page": page,
        "size": size,
        "offset": (page - 1) * size,
    }


# ── Section 3: Request body ───────────────────────────────────────────────────
class CreateItem(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)
    tax: float | None = Field(default=None, ge=0)
    tags: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def price_with_tax(self) -> float:
        if self.tax is None:
            return self.price
        return round(self.price + self.tax, 2)


@app.post("/items", status_code=201)
async def create_item(item: CreateItem):
    return item


# ── Section 4: Mixed body — model + scalar ────────────────────────────────────
class UpdateItem(BaseModel):
    name: str | None = None
    price: float | None = Field(default=None, gt=0)

@app.put("/items/{item_id}")
async def update_item(
    item_id: ItemID,
    item: Annotated[UpdateItem, Body()],
    reason: Annotated[str, Body(min_length=1)] = "general update",
):
    # Both item (model) and reason (scalar) come from the body
    return {"item_id": item_id, "update": item.model_dump(exclude_none=True), "reason": reason}


# ── Section 5: Headers and cookies ───────────────────────────────────────────
@app.get("/headers")
async def read_headers(
    user_agent: Annotated[str | None, Header()] = None,
    x_request_id: Annotated[str | None, Header(alias="X-Request-ID")] = None,
    accept_language: Annotated[str | None, Header()] = None,
):
    return {
        "user_agent": user_agent,
        "request_id": x_request_id,
        "language": accept_language,
    }

@app.get("/me")
async def read_me(
    session: Annotated[str | None, Cookie()] = None,
):
    if not session:
        return {"authenticated": False}
    return {"authenticated": True, "session": session[:8] + "..."}


if __name__ == "__main__":
    client = TestClient(app)

    print("=" * 55)
    print("DEMO: FastAPI Path, Query & Body Parameters")
    print("=" * 55)

    # Section 1: path params
    print("\n[1] Path params with validation:")
    r = client.get("/catalog/electronics/42?include_tax=true&fields=name&fields=price")
    print(f"  GET /catalog/electronics/42?... → {r.json()}")

    r = client.get("/catalog/INVALID/1")  # fails pattern
    print(f"  Invalid category pattern → {r.status_code}: {r.json()['detail'][0]['msg']}")

    r = client.get("/catalog/books/0")    # fails ge=1
    print(f"  item_id=0 → {r.status_code}: {r.json()['detail'][0]['msg']}")

    # Section 2: multi-value query params
    print("\n[2] Multi-value query params:")
    r = client.get("/search?q=python&tags=backend&tags=api&tags=fastapi&page=2&size=5")
    print(f"  GET /search?q=python&tags=... → {r.json()}")

    r = client.get("/search?q=x")  # q too short (min_length=2)
    print(f"  q too short → {r.status_code}: {r.json()['detail'][0]['msg']}")

    # Section 3: request body
    print("\n[3] Request body (Pydantic model):")
    r = client.post("/items", json={"name": "Widget", "price": 9.99, "tax": 0.89, "tags": ["sale"]})
    print(f"  POST /items → {r.status_code}: {r.json()}")

    r = client.post("/items", json={"name": "", "price": -1})
    print(f"  Invalid body → {r.status_code}: {len(r.json()['detail'])} errors")

    # Section 4: mixed body
    print("\n[4] Mixed body — model + scalar:")
    r = client.put("/items/5", json={
        "item": {"name": "Updated Widget", "price": 12.99},
        "reason": "price adjustment"
    })
    print(f"  PUT /items/5 → {r.json()}")

    # Section 5: headers
    print("\n[5] Headers and cookies:")
    r = client.get("/headers", headers={
        "User-Agent": "DemoClient/1.0",
        "X-Request-ID": "req-abc",
        "Accept-Language": "en-US",
    })
    print(f"  Headers → {r.json()}")

    r = client.get("/me", cookies={"session": "abcdef1234567890"})
    print(f"  Cookie session → {r.json()}")

    r = client.get("/me")
    print(f"  No cookie → {r.json()}")

    print("\n" + "=" * 55)
