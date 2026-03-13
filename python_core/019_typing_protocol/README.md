# `typing` Module — `Protocol`, `TypeVar`, `Literal`, Type Narrowing

## 🎯 Interview Question
What is a `Protocol` in Python's `typing` module, and how does it differ from `ABC`? Explain `TypeVar`, `Generic`, `Literal`, and `TypeGuard`. How does type narrowing work with `isinstance`?

## 💡 Short Answer (30 seconds)
`Protocol` enables structural subtyping — a class satisfies a Protocol if it has the right methods/attributes, without any inheritance. This is duck typing with static analysis support. `TypeVar` creates type variables for generics. `Literal` restricts a value to a specific set of constants. Type narrowing is when the type checker refines a type within a conditional block based on runtime checks like `isinstance`.

## 🔬 Deep Explanation

### `Protocol` — structural subtyping (duck typing + static analysis)
```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None: ...
```
Any class with a `draw()` method satisfies `Drawable` — no inheritance needed. The type checker verifies this statically. At runtime, `isinstance(obj, Drawable)` only works if `Drawable` is decorated with `@runtime_checkable`.

**`Protocol` vs `ABC`:**
- `ABC` — nominal subtyping (must inherit or register)
- `Protocol` — structural subtyping (must have the right shape)
- `Protocol` is a static analysis concept; enforcement is via mypy/pyright, not Python itself
- `ABC` raises `TypeError` at runtime for missing abstract methods; `Protocol` doesn't

### `TypeVar` — generic type variables
```python
T = TypeVar('T')
def first(lst: list[T]) -> T:
    return lst[0]
```
`T` is a placeholder for a concrete type inferred at call time. Constraints:
- `T = TypeVar('T', int, str)` — only `int` or `str`
- `T = TypeVar('T', bound=Comparable)` — `T` must be a subtype of `Comparable`
- `covariant=True` / `contravariant=True` — for variance in generics

### `Generic[T]` — parameterized classes
```python
class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []
    def push(self, item: T) -> None:
        self._items.append(item)
    def pop(self) -> T:
        return self._items.pop()
```
`Stack[int]` is a specialized Stack that only holds ints (statically).

### `Literal` — restrict to specific values
```python
from typing import Literal

def set_log_level(level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]) -> None: ...
```
Type checkers verify that only the listed values are passed. Useful for:
- HTTP methods: `Literal["GET", "POST", "PUT", "DELETE"]`
- Status strings: `Literal["active", "inactive", "pending"]`
- Sentinel values

### Type narrowing — `isinstance`, `assert`, `TypeGuard`
```python
def process(value: int | str) -> str:
    if isinstance(value, int):
        return str(value * 2)  # here, value is narrowed to int
    return value.upper()       # here, value is narrowed to str
```
Type checkers track the narrowing. Other narrowers: `type()`, `assert`, `is None`, `is not None`, truthiness.

`TypeGuard[T]` — a function that returns `bool` and tells the type checker to narrow:
```python
def is_list_of_str(val: list) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in val)
```

### `Annotated` — metadata in type hints
```python
from typing import Annotated
from pydantic import Field

UserID = Annotated[int, Field(gt=0, description="Positive user ID")]
```
The first arg is the actual type; subsequent args are metadata for tools (Pydantic, FastAPI, etc.) to interpret. Pydantic v2 uses `Annotated` extensively.

### `overload` — multiple signatures
```python
@overload
def process(x: int) -> int: ...
@overload
def process(x: str) -> str: ...
def process(x):
    return x  # actual implementation
```
Only the `@overload` stubs are visible to the type checker; the real implementation is untyped.

### Runtime cost
Type hints are stored in `__annotations__` and are **not evaluated at import time** by default (PEP 563 `from __future__ import annotations` makes them strings). `get_type_hints(func)` evaluates them. This matters for performance: avoid `get_type_hints` in hot paths.

## 💻 Code Example

```python
from typing import Protocol, TypeVar, Generic, Literal, runtime_checkable, overload

@runtime_checkable
class Serializable(Protocol):
    def to_dict(self) -> dict: ...

T = TypeVar('T')

class Repository(Generic[T]):
    def __init__(self) -> None:
        self._store: dict[int, T] = {}

    def save(self, id: int, item: T) -> None:
        self._store[id] = item

    def get(self, id: int) -> T | None:
        return self._store.get(id)

def process_status(status: Literal["active", "inactive", "pending"]) -> str:
    if status == "active":
        return "Processing..."
    return f"Skipping {status} record"

@overload
def stringify(x: int) -> str: ...
@overload
def stringify(x: list[int]) -> list[str]: ...
def stringify(x):
    if isinstance(x, int):
        return str(x)
    return [str(i) for i in x]
```

## ⚠️ Common Mistakes & Interview Traps

1. **`Protocol` is not enforced at runtime (without `@runtime_checkable`)**: `isinstance(obj, Drawable)` raises `TypeError` unless `Drawable` is `@runtime_checkable`. Even with it, only the presence of methods is checked — not their signatures.

2. **`TypeVar` name must match the variable name**: `T = TypeVar('T')` — the string arg should match. Mismatches confuse type checkers.

3. **`from __future__ import annotations` breaks `get_type_hints` in some cases**: Annotations become strings. `get_type_hints` re-evaluates them — but forward references in different scopes can fail.

4. **`list[int]` vs `List[int]`**: In Python 3.9+, `list[int]` is valid in type hints. Before 3.9, you needed `from typing import List`. `List[int]` is now deprecated but still works.

5. **`Union[X, Y]` vs `X | Y`**: `X | Y` syntax requires Python 3.10+ at runtime (or `from __future__ import annotations`). In 3.9 code without the future import, use `Union[X, Y]` or `Optional[X]`.

## 🔗 Related Concepts
- `python_core/013_abc_abstract` — `ABC` vs `Protocol` — nominal vs structural typing
- `python_core/014_dataclasses_internals` — `@dataclass` uses `__annotations__`
- `fastapi/` — FastAPI uses `Annotated` and `TypeVar` extensively for DI

## 📚 Go Deeper
- PEP 544 — "Protocols: Structural subtyping (static duck typing)"
- PEP 695 — "Type Parameter Syntax" (Python 3.12) — `class Stack[T]:`
