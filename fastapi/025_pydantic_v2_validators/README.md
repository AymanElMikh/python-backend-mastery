# Pydantic v2 Validators — `field_validator`, `model_validator`, `computed_field`

## 🎯 Interview Question
What changed from Pydantic v1 to v2 in terms of validators? Explain `field_validator`, `model_validator`, `computed_field`, and `model_config`. How does Pydantic v2's Rust core affect performance?

## 💡 Short Answer (30 seconds)
Pydantic v2 rewrote its validation core in Rust (`pydantic-core`), achieving 5–50x speedup. The API shifted from `@validator` (v1) to `@field_validator` and `@model_validator` (v2). `@field_validator` handles single-field validation, `@model_validator` handles cross-field validation and runs before/after field parsing. `computed_field` replaces `@property` for fields that appear in serialization.

## 🔬 Deep Explanation

### Pydantic v1 vs v2 — key changes

| v1 | v2 | Notes |
|---|---|---|
| `@validator('field')` | `@field_validator('field')` | Signature changed: `cls, v` → `cls, v, info` |
| `@root_validator` | `@model_validator(mode='before'\|'after')` | |
| `@property` | `@computed_field` | Shows in `.model_dump()` and schema |
| `class Config:` | `model_config = ConfigDict(...)` | |
| `dict()` | `model_dump()` | `dict()` deprecated |
| `parse_obj()` | `model_validate()` | |
| Pure Python | Rust core | 5–50x faster |

### `@field_validator` — single field
```python
@field_validator('email')
@classmethod
def validate_email(cls, v: str) -> str:
    if '@' not in v:
        raise ValueError('invalid email')
    return v.lower()  # can transform the value
```

`mode='before'` — runs before type coercion (receives raw input)
`mode='after'` — runs after type coercion (receives typed value)
`mode='wrap'` — receives a handler to call the next validator yourself

### `@model_validator` — cross-field validation
```python
@model_validator(mode='after')
def check_dates(self) -> 'MyModel':
    if self.end_date <= self.start_date:
        raise ValueError('end_date must be after start_date')
    return self

@model_validator(mode='before')
@classmethod
def preprocess(cls, data: dict) -> dict:
    # Runs before ANY field parsing — receives raw dict
    data['name'] = data.get('name', '').strip()
    return data
```

`mode='before'` — classmethod, receives raw data
`mode='after'` — instance method, receives fully validated model

### `computed_field` — properties in the schema
```python
class User(BaseModel):
    first_name: str
    last_name: str

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

# full_name appears in model_dump() and JSON schema
```

### `model_config = ConfigDict(...)` — replaces `class Config`
```python
class MyModel(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,   # auto-strip strings
        frozen=True,                 # immutable (like dataclass frozen)
        populate_by_name=True,       # accept both alias and field name
        extra='forbid',              # reject unknown fields
        arbitrary_types_allowed=True,  # allow non-pydantic types
    )
```

### Strict mode
`strict=True` disables coercion — `"42"` won't be accepted for an `int` field. Set per-field via `Field(strict=True)` or globally via `model_config`.

### `Field()` — rich field metadata
```python
from pydantic import Field

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, description="Price in USD")
    tags: list[str] = Field(default_factory=list, max_length=10)
    sku: str = Field(alias="product_sku", serialization_alias="sku")
```

### `model_dump()` and `model_dump_json()` options
```python
user.model_dump(exclude={"password"}, by_alias=True, mode="json")
user.model_dump_json(exclude_none=True, indent=2)
```

### Performance
Pydantic v2's Rust core (`pydantic-core`) pre-compiles the validation schema at class definition time. At runtime, validation is a call into Rust — pure Python overhead is minimal. Benchmark: ~17x faster than v1 for simple models, up to 50x for complex nested models.

## 💻 Code Example

```python
from pydantic import BaseModel, Field, field_validator, model_validator, computed_field
from pydantic import ConfigDict
from datetime import date

class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=2, max_length=50)
    email: str
    age: int = Field(ge=0, le=150)
    password: str = Field(min_length=8, exclude=True)  # excluded from output

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v.lower()

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return v.title()  # "alice" → "Alice"

    @computed_field
    @property
    def username(self) -> str:
        return self.email.split("@")[0]


class DateRange(BaseModel):
    start: date
    end: date

    @model_validator(mode="after")
    def validate_range(self) -> "DateRange":
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self
```

## ⚠️ Common Mistakes & Interview Traps

1. **Forgetting `@classmethod` on `@field_validator`**: Pydantic v2 requires `@classmethod` on field validators. Without it, you get a `PydanticUserError`.

2. **v1 `@validator` syntax in v2**: v1 validators work in v2 via a compatibility shim, but produce deprecation warnings. The signature differs: v1 uses `(cls, v)`, v2 uses `(cls, v, info)` where `info.data` contains already-validated fields.

3. **`mode='before'` vs `mode='after'`**: `before` sees raw (uncoerced) input — useful for normalizing before type conversion. `after` sees the typed value — useful for semantic validation.

4. **`model_dump()` vs `dict()`**: `dict()` is deprecated in v2 and will be removed. Always use `model_dump()`.

5. **`computed_field` requires `@property`**: `@computed_field` must wrap a `@property`. Without `@property`, it raises `PydanticUserError`. The property's return type annotation is required for schema generation.

## 🔗 Related Concepts
- `fastapi/026_path_query_body` — Pydantic models are used for request body parsing
- `fastapi/027_response_models` — `response_model` uses Pydantic for output filtering
- `fastapi/028_exception_handlers` — `RequestValidationError` wraps Pydantic `ValidationError`

## 📚 Go Deeper
- Pydantic v2 migration guide — full list of v1→v2 breaking changes
- `pydantic-core` repo — the Rust validation engine source
