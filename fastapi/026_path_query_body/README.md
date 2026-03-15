# FastAPI Path, Query & Body Parameters

## 🎯 Interview Question
How does FastAPI distinguish between path parameters, query parameters, and request body? Explain `Path()`, `Query()`, `Body()`, `Header()`, `Cookie()`, and how `Annotated` makes them composable.

## 💡 Short Answer (30 seconds)
FastAPI inspects the route function signature to determine parameter sources: path parameters match the `{name}` placeholders in the URL, simple scalars become query parameters, and Pydantic model parameters become the request body. `Path()`, `Query()`, `Body()`, `Header()`, and `Cookie()` are `FieldInfo` objects that add validation metadata and override the auto-detection. `Annotated[int, Query(ge=0)]` is the modern, composable way to attach these — separating type from metadata.

## 🔬 Deep Explanation

### How FastAPI auto-detects parameter sources
1. If the parameter name matches a `{placeholder}` in the path → **path parameter**
2. If the parameter type is a Pydantic `BaseModel` → **request body**
3. Everything else → **query parameter**

You can override this with explicit `Path()`, `Query()`, `Body()`, etc.

### `Path()` — path parameter with validation
```python
@app.get("/items/{item_id}")
async def get_item(
    item_id: Annotated[int, Path(ge=1, le=1000, title="Item ID")]
):
    ...
```

### `Query()` — query parameter with validation
```python
@app.get("/search")
async def search(
    q: Annotated[str | None, Query(min_length=2, max_length=50)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    ...
```

### Multiple values for one query param
```python
@app.get("/filter")
async def filter_items(
    tags: Annotated[list[str], Query()] = [],
):
    # GET /filter?tags=a&tags=b&tags=c → tags=["a","b","c"]
    ...
```

### `Body()` — body parameters
When you have multiple body fields (not one Pydantic model):
```python
@app.post("/items")
async def create(
    item: Annotated[ItemModel, Body(embed=True)],
    importance: Annotated[int, Body(ge=1, le=5)],
):
    # Request body: {"item": {...}, "importance": 3}
    # embed=True wraps the model in its key
    ...
```

`Body(embed=True)` wraps the body in `{"model_name": {...}}` — useful when mixing model + scalar body fields.

### `Header()` — HTTP headers
```python
async def route(
    user_agent: Annotated[str | None, Header()] = None,
    x_request_id: Annotated[str, Header(alias="X-Request-ID")] = "",
):
    ...
```
FastAPI automatically converts `user_agent` → `User-Agent` header (underscores to hyphens).

### `Cookie()` — cookie values
```python
async def route(session_id: Annotated[str | None, Cookie()] = None): ...
```

### `Annotated` composability — reusable parameter definitions
```python
# Define once, reuse anywhere
PageQuery = Annotated[int, Query(ge=1, description="Page number")]
SizeQuery = Annotated[int, Query(ge=1, le=100, description="Page size")]

@app.get("/users")
async def list_users(page: PageQuery = 1, size: SizeQuery = 20): ...

@app.get("/items")
async def list_items(page: PageQuery = 1, size: SizeQuery = 20): ...
```

### Request body with `model_validator` and `Field`
```python
class CreateItem(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)
    tax: float | None = Field(default=None, ge=0)

    @computed_field
    @property
    def price_with_tax(self) -> float:
        return self.price + (self.tax or 0)

@app.post("/items", status_code=201)
async def create_item(item: CreateItem) -> CreateItem:
    return item
```

## 💻 Code Example

```python
from fastapi import FastAPI, Path, Query, Body, Header, Cookie
from typing import Annotated

app = FastAPI()

@app.get("/catalog/{category}/{item_id}")
async def get_item(
    category: Annotated[str, Path(min_length=2, pattern=r"^[a-z\-]+$")],
    item_id: Annotated[int, Path(ge=1)],
    include_tax: Annotated[bool, Query()] = False,
    fields: Annotated[list[str], Query()] = [],
):
    return {
        "category": category,
        "item_id": item_id,
        "include_tax": include_tax,
        "fields": fields,
    }
```

## ⚠️ Common Mistakes & Interview Traps

1. **Multiple Pydantic body models create a nested JSON body**: If you have `def route(item: Item, user: User)`, FastAPI expects `{"item": {...}, "user": {...}}` — not two top-level bodies. Use `Body(embed=False)` carefully.

2. **`list[str]` query param without `Query()`**: `tags: list[str] = []` is treated as a body field, not a multi-value query param. Must be `tags: Annotated[list[str], Query()] = []`.

3. **Header name conversion**: `user_agent` (Python param name) maps to `User-Agent` header. FastAPI auto-converts underscores to hyphens. Use `alias=` for non-standard header names.

4. **`Optional[str]` vs `str | None`**: Both work in Python 3.10+. In Python 3.9, use `Optional[str]` from `typing`. `str | None` is cleaner and preferred.

5. **Path parameters must match the route template exactly**: `@app.get("/items/{id}")` with parameter `item_id` raises `FastAPIError` — the parameter name must be `id`.

## 🔗 Related Concepts
- `fastapi/025_pydantic_v2_validators` — Pydantic models power body parsing and validation
- `fastapi/027_response_models` — `response_model` mirrors the input model pattern
- `fastapi/028_exception_handlers` — `RequestValidationError` on bad params

## 📚 Go Deeper
- FastAPI docs: "Query Parameters and String Validations" — full `Query()` options
- Starlette source: `routing.py` — how path parameters are extracted from URL
