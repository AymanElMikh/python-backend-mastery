"""
Demo: Pydantic v2 Validators — field_validator, model_validator, computed_field
Run:  python demo.py
"""

from pydantic import (
    BaseModel, Field, field_validator, model_validator,
    computed_field, ConfigDict, ValidationError
)
from datetime import date
from typing import Any

# ── Section 1: field_validator — single field, mode='before' and 'after' ──────
class Product(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, description="Price in USD")
    sku: str
    tags: list[str] = Field(default_factory=list)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, v: Any) -> str:
        """before: receives raw input before type coercion."""
        return str(v).title()

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v: str) -> str:
        """after (default): receives typed str."""
        v = v.upper().strip()
        if not v.startswith("SKU-"):
            raise ValueError("SKU must start with 'SKU-'")
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v: Any) -> list:
        """Accept comma-separated string OR list."""
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        return v

    @computed_field
    @property
    def display_name(self) -> str:
        return f"{self.name} [{self.sku}] ${self.price:.2f}"


# ── Section 2: model_validator — cross-field ──────────────────────────────────
class DateRange(BaseModel):
    start: date
    end: date
    label: str = ""

    @model_validator(mode="before")
    @classmethod
    def preprocess(cls, data: dict) -> dict:
        """Runs before field parsing — normalize raw dict."""
        if isinstance(data.get("label"), str):
            data["label"] = data["label"].strip().upper()
        return data

    @model_validator(mode="after")
    def validate_range(self) -> "DateRange":
        """Runs after all fields parsed — cross-field check."""
        if self.end <= self.start:
            raise ValueError(f"end ({self.end}) must be after start ({self.start})")
        return self

    @computed_field
    @property
    def duration_days(self) -> int:
        return (self.end - self.start).days


# ── Section 3: model_config options ──────────────────────────────────────────
class StrictUser(BaseModel):
    model_config = ConfigDict(
        extra="forbid",              # reject unknown fields
        str_strip_whitespace=True,   # auto-strip strings
        frozen=True,                 # immutable after creation
    )

    name: str = Field(min_length=2)
    email: str
    age: int = Field(ge=0, le=150)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("must contain @")
        return v.lower()


# ── Section 4: Field exclusion, aliases, serialization ───────────────────────
class UserCreate(BaseModel):
    username: str = Field(alias="user_name")    # accept 'user_name' as input key
    email: str
    password: str = Field(exclude=True)         # never appears in output

    model_config = ConfigDict(populate_by_name=True)  # also accept 'username'


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: Pydantic v2 Validators")
    print("=" * 55)

    # Section 1
    print("\n[1] field_validator — single field:")
    p = Product(name="  widget pro  ", price=9.99, sku="sku-abc123", tags="python,web,api")
    print(f"  name (normalized):    {p.name!r}")
    print(f"  sku (uppercased):     {p.sku!r}")
    print(f"  tags (from string):   {p.tags}")
    print(f"  display_name (computed): {p.display_name!r}")

    try:
        Product(name="x", price=-1, sku="wrong")
    except ValidationError as e:
        print(f"\n  Validation errors:")
        for err in e.errors():
            print(f"    [{err['loc']}] {err['msg']}")

    # Section 2
    print("\n[2] model_validator — cross-field + before/after:")
    dr = DateRange(start="2026-01-01", end="2026-12-31", label="  q4 budget  ")
    print(f"  start={dr.start}, end={dr.end}")
    print(f"  label (before validator): {dr.label!r}  (uppercased)")
    print(f"  duration_days (computed): {dr.duration_days}")

    try:
        DateRange(start="2026-12-31", end="2026-01-01")
    except ValidationError as e:
        for err in e.errors():
            print(f"  Invalid range → {err['msg']}")

    # Section 3
    print("\n[3] model_config — extra=forbid, frozen, strip_whitespace:")
    user = StrictUser(name="  Alice  ", email="ALICE@EXAMPLE.COM", age=30)
    print(f"  name (stripped):  {user.name!r}")
    print(f"  email (lowered):  {user.email!r}")

    try:
        user.name = "Bob"  # frozen=True
    except Exception as e:
        print(f"  Mutation attempt → {type(e).__name__}: {e}")

    try:
        StrictUser(name="Bob", email="b@b.com", age=25, unknown_field="x")
    except ValidationError as e:
        for err in e.errors():
            print(f"  Extra field → {err['msg']}")

    # Section 4
    print("\n[4] Field alias, exclude:")
    # Accept input via alias 'user_name'
    u = UserCreate.model_validate({"user_name": "alice", "email": "a@b.com", "password": "s3cr3t!"})
    print(f"  model_validate({{user_name:...}}) → username={u.username!r}")
    dumped = u.model_dump()
    print(f"  model_dump() → {dumped}  (password excluded)")
    print(f"  'password' in output: {'password' in dumped}")

    # Also accept via field name when populate_by_name=True
    u2 = UserCreate(username="bob", email="b@b.com", password="pass1234")
    print(f"  UserCreate(username=...) → {u2.model_dump()}")

    print("\n[5] model_dump() options:")
    print(f"  model_dump(mode='json'): {dr.model_dump(mode='json')}")
    print(f"  model_dump_json(): {dr.model_dump_json()}")

    print("\n" + "=" * 55)
