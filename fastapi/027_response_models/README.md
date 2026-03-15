# FastAPI Response Models & Status Codes

## 🎯 Interview Question
How does `response_model` work in FastAPI? What is the difference between the return type annotation and `response_model`, and when would you use `JSONResponse`, `StreamingResponse`, or `FileResponse` directly?

## 💡 Short Answer (30 seconds)
`response_model` tells FastAPI to filter and validate the route's return value through a Pydantic model before serializing it to JSON — it strips fields not in the model (like passwords) and validates the output. The return type annotation is for editor/mypy, while `response_model` controls the actual HTTP response. Use `JSONResponse` when you need direct control over headers, cookies, or the response body structure.

## 🔬 Deep Explanation

### `response_model` — output filtering and validation
```python
class UserDB(BaseModel):
    id: int
    name: str
    email: str
    hashed_password: str  # NEVER expose this

class UserOut(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users/{id}", response_model=UserOut)
async def get_user(id: int) -> UserDB:
    return UserDB(id=id, name="Alice", email="a@b.com", hashed_password="$2b$...")
    # FastAPI passes the return value through UserOut — hashed_password is stripped
```

The route can return a `UserDB`, a dict, an ORM object, or anything — FastAPI calls `UserOut.model_validate(result)` and serializes that.

### Return type annotation vs `response_model`
- **Return annotation** (`-> UserOut`): tells type checkers and FastAPI to generate docs, but if omitted, `response_model` alone works
- **`response_model`**: controls actual serialization, filtering, and the OpenAPI response schema
- They can differ: return `-> UserDB` (full ORM object), `response_model=UserOut` (filtered output)

In FastAPI 0.89+, if you use the return type annotation directly, FastAPI uses it as `response_model` automatically — but you can still override with `response_model=`.

### `response_model_exclude_unset` — partial updates
```python
@app.patch("/users/{id}", response_model=UserOut, response_model_exclude_unset=True)
async def partial_update(id: int, patch: UserPatch) -> dict:
    ...
```
Only includes fields that were explicitly set (not default values). Essential for PATCH endpoints.

### `response_model_exclude` / `response_model_include`
```python
@app.get("/users/{id}", response_model=User, response_model_exclude={"password", "secret"})
```

### HTTP status codes
```python
@app.post("/items", status_code=201)      # Created
@app.delete("/items/{id}", status_code=204)  # No Content
```

Use `status` from `fastapi` or `http.HTTPStatus` for clarity:
```python
from fastapi import status
@app.post("/items", status_code=status.HTTP_201_CREATED)
```

### Multiple response types — `responses=`
```python
@app.get(
    "/items/{id}",
    response_model=Item,
    responses={
        404: {"model": ErrorDetail, "description": "Item not found"},
        422: {"description": "Validation error"},
    }
)
```
Documents multiple response schemas in OpenAPI.

### `JSONResponse` — direct control
```python
from fastapi.responses import JSONResponse

@app.get("/custom")
async def custom():
    return JSONResponse(
        content={"message": "ok"},
        status_code=200,
        headers={"X-Custom-Header": "value"},
    )
```
When to use: setting cookies, custom headers, non-standard status codes, or when returning pre-serialized data (skip Pydantic overhead).

### Other response types
- `HTMLResponse` — return HTML content
- `PlainTextResponse` — plain text
- `FileResponse(path)` — serve a file with proper Content-Disposition
- `StreamingResponse(generator)` — stream large content (CSV export, video)
- `RedirectResponse(url, status_code=302)` — HTTP redirect

### Default response class
```python
app = FastAPI(default_response_class=ORJSONResponse)  # use orjson for all routes
```

## 💻 Code Example

```python
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

class UserDB(BaseModel):
    id: int; name: str; email: str; hashed_password: str

class UserOut(BaseModel):
    id: int; name: str; email: str

class UserCreate(BaseModel):
    name: str; email: str; password: str

app = FastAPI()

@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate) -> UserDB:
    return UserDB(
        id=1, name=user.name, email=user.email,
        hashed_password=f"hashed:{user.password}"
    )
    # FastAPI filters through UserOut — hashed_password dropped

@app.get("/stream")
async def stream_data():
    async def generate():
        for i in range(5):
            yield f"data: chunk {i}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

## ⚠️ Common Mistakes & Interview Traps

1. **`response_model` doesn't prevent leaks if you use `JSONResponse` directly**: If you `return JSONResponse(content=user.dict())`, FastAPI skips `response_model` filtering — the full dict goes out. Always let FastAPI serialize, or filter manually.

2. **ORM objects and `model_validate`**: If returning SQLAlchemy models, set `model_config = ConfigDict(from_attributes=True)` on the Pydantic model so it can read ORM attributes.

3. **`response_model_exclude_unset` on input vs output**: It excludes unset fields from the *response*, not from what was received. Confusing in PATCH handlers — make sure the DB update also only touches set fields.

4. **`status_code=204` returns no body**: A 204 No Content response must have no body. FastAPI silently drops the return value. Don't return data with 204.

5. **Union response models**: `response_model=Union[TypeA, TypeB]` is supported but generates a merged OpenAPI schema. Better: use separate routes or `responses=` to document alternatives.

## 🔗 Related Concepts
- `fastapi/025_pydantic_v2_validators` — response models are Pydantic models
- `fastapi/028_exception_handlers` — `HTTPException` short-circuits response_model
- `fastapi/029_openapi_customization` — `responses=` enriches the OpenAPI schema

## 📚 Go Deeper
- FastAPI docs: "Response Model — Return Type" — `response_model` vs annotation priority
- Starlette docs: "Responses" — all built-in response types
