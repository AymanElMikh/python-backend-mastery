# NamedTuple vs dataclass — Choosing the Right Data Container

## 🎯 Interview Question
When would you choose `collections.namedtuple` or `typing.NamedTuple` over `@dataclass`, and vice versa? What are the performance, mutability, and inheritance trade-offs?

## 💡 Short Answer (30 seconds)
`NamedTuple` is a tuple subclass — immutable, memory-efficient, iterable/unpackable, and works as a dict key. `@dataclass` is a regular class — mutable by default, supports `__post_init__`, inheritance, and optional `frozen=True`. Use `NamedTuple` for value objects, coordinate pairs, and DB row results where immutability and tuple interop matter. Use `@dataclass` when you need methods, inheritance, optional fields, or mutations.

## 🔬 Deep Explanation
**`collections.namedtuple` (classic)**
- Factory function that generates a new class — subclass of `tuple`.
- Ultra-fast positional access (C-level tuple indexing).
- Immutable — `obj.x = 1` raises `AttributeError`.
- Can be unpacked: `x, y = point`.
- Picklable, hashable (if all fields are hashable).
- No default values in Python < 3.6.1 (workaround: `_field_defaults`).
- `__repr__`, `__eq__`, `_asdict()`, `_replace()` generated automatically.

**`typing.NamedTuple` (modern)**
- Class-based syntax, supports type annotations and default values.
- Still a tuple subclass — all the same performance characteristics.
- Can add methods but cannot override `__new__` in a useful way.

**`@dataclass`**
- Uses `__init__`, `__repr__`, `__eq__` generated via the `dataclasses` module.
- Stores data in `__dict__` (or `__slots__` if `slots=True` added in 3.10).
- `frozen=True` → immutable + `__hash__` added (sets `__delattr__`/`__setattr__` to raise).
- `field(default_factory=list)` for mutable defaults.
- `__post_init__` for post-construction validation.
- `@dataclass(slots=True)` (Python 3.10+) for slot-based storage = faster attribute access + lower memory.

**Memory & speed:**
- `namedtuple`: tuple storage → ~56 bytes for 2-field, no `__dict__`.
- `dataclass`: regular class → ~104 bytes for 2-field with `__dict__`.
- `dataclass(slots=True)`: ~72 bytes — close to namedtuple, mutable.

**Inheritance:**
- `NamedTuple` inheritance is deeply broken (adding fields in subclasses doesn't work as expected).
- `@dataclass` inheritance works naturally; parent fields come first in `__init__`.

## 💻 Code Example
```python
from typing import NamedTuple
from dataclasses import dataclass, field
import sys

class Point(NamedTuple):
    x: float
    y: float = 0.0   # default value

@dataclass
class Config:
    host: str
    port: int = 8080
    tags: list = field(default_factory=list)

p = Point(1.0, 2.0)
print(p.x, p[0])            # same — it's a tuple
x, y = p                     # unpackable
print(hash(p))               # hashable

cfg = Config("localhost")
cfg.tags.append("web")      # mutable

@dataclass(frozen=True, slots=True)
class ImmutablePoint:
    x: float
    y: float

ip = ImmutablePoint(3.0, 4.0)
# ip.x = 5  # raises FrozenInstanceError
print(sys.getsizeof(p), sys.getsizeof(ip))  # size comparison
```

## ⚠️ Common Mistakes & Interview Traps
- **Mutable defaults in `@dataclass`**: `tags: list = []` raises `ValueError` — use `field(default_factory=list)`.
- **`NamedTuple` subclass fields**: Subclassing a `NamedTuple` and adding fields doesn't extend the tuple — you get `TypeError` or silent wrong behavior.
- **`frozen=True` ≠ deep immutability**: A `frozen` dataclass with a `list` field — the list itself is still mutable.
- **`@dataclass` doesn't add `__hash__` if `__eq__` is defined without `frozen=True`**: It sets `__hash__ = None`.
- **`_replace()` on NamedTuple** creates a new tuple — doesn't mutate. Forgetting to capture the return value is a common bug.

## 🔗 Related Concepts
- python_core/014_dataclasses_internals — field(), __post_init__, ClassVar
- python_core/016_hash_eq — __hash__ and frozen dataclasses
- python_core/006_slots — __slots__ and dataclass(slots=True)

## 📚 Go Deeper
- PEP 557 — Data Classes
- CPython `Lib/dataclasses.py` — `_process_class()` — how `@dataclass` rewrites the class
