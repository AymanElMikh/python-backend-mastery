# `dataclasses` Internals — `field()`, `__post_init__`, `ClassVar`

## 🎯 Interview Question
How does `@dataclass` work under the hood? Explain `field()` defaults, `__post_init__`, `ClassVar`, `InitVar`, and the difference between `eq=True`, `frozen=True`, and `slots=True`. When would you NOT use a dataclass?

## 💡 Short Answer (30 seconds)
`@dataclass` is a class decorator that inspects `__annotations__` at class creation time and auto-generates `__init__`, `__repr__`, `__eq__`, and optionally `__hash__`, `__lt__`, and `__slots__`. `field()` gives per-field control: `default_factory` for mutable defaults, `init=False` to exclude from `__init__`, `repr=False` to hide from repr. `__post_init__` runs after the generated `__init__` for validation and derived-field setup.

## 🔬 Deep Explanation

### What `@dataclass` generates
The decorator reads `cls.__annotations__` (ordered since Python 3.7) and synthesizes:
- `__init__` — a function with parameters matching annotated fields
- `__repr__` — `ClassName(field1=val, field2=val)`
- `__eq__` — compares all fields (unless `eq=False`)

It does NOT generate `__hash__` unless you set `frozen=True` or `unsafe_hash=True`. If `eq=True` (default) and you don't define `__hash__`, Python sets `__hash__ = None` (making instances unhashable) — consistent with the rule that equal objects must hash equally.

### `field()` — per-field control

| Parameter | Effect |
|-----------|--------|
| `default` | Static default value |
| `default_factory` | Called each time — for mutable defaults |
| `init` | `False` → excluded from `__init__` |
| `repr` | `False` → excluded from `__repr__` |
| `compare` | `False` → excluded from `__eq__` and ordering |
| `hash` | Override hash inclusion |
| `metadata` | Arbitrary read-only mapping (for frameworks) |
| `kw_only` | Force keyword-only in `__init__` (3.10+) |

### The mutable default trap
```python
@dataclass
class Bad:
    items: list = []  # SyntaxError — dataclass catches this!
    # Use field(default_factory=list) instead
```
`@dataclass` raises `ValueError: mutable default <class 'list'>` at class definition time. This is a deliberate safety check.

### `__post_init__` — validation and derived fields
Called by the generated `__init__` as its last step. Use it for:
- Input validation
- Computing derived fields (`field(init=False)`)
- Calling parent's `__post_init__` in inheritance

```python
@dataclass
class Circle:
    radius: float
    area: float = field(init=False)  # not in __init__

    def __post_init__(self):
        if self.radius < 0:
            raise ValueError("radius must be non-negative")
        self.area = 3.14159 * self.radius ** 2
```

### `ClassVar` and `InitVar`
- `ClassVar[T]` — tells `@dataclass` to ignore this annotation (it's a class variable, not an instance field)
- `InitVar[T]` — appears in `__init__` but NOT stored as an instance attribute; passed to `__post_init__` for setup logic

### `frozen=True` — immutable dataclass
Generates `__setattr__` and `__delattr__` that raise `FrozenInstanceError`. Also generates `__hash__` (since frozen instances are safely hashable). Use for value objects, dict keys, set members.

### `slots=True` (Python 3.10+)
Generates `__slots__` automatically. The class is recreated internally (a new type is created) to support `__slots__` + inheritance cleanly. Saves significant memory for large collections of instances.

### `order=True`
Generates `__lt__`, `__le__`, `__gt__`, `__ge__` based on a tuple of all fields in definition order. Useful for `sorted()` and `heapq`.

### When NOT to use `@dataclass`
- When you need complex `__init__` logic that can't be expressed via `__post_init__`
- When you need a real ORM model (SQLAlchemy models have their own metaclass machinery)
- For pure value objects that are already well-served by `NamedTuple` (immutable, tuplelike, lighter)
- When field order for comparison matters differently from definition order

## 💻 Code Example

```python
from dataclasses import dataclass, field, fields, asdict, astuple, replace
from typing import ClassVar, InitVar

@dataclass(order=True, frozen=True)
class Priority:
    level: int
    label: str = field(compare=False)  # excluded from ordering

@dataclass
class Order:
    COUNTER: ClassVar[int] = 0  # class variable — ignored by dataclass

    order_id: int = field(init=False)  # generated, not passed in
    items: list = field(default_factory=list)
    discount: float = 0.0
    _secret: str = field(default="", repr=False)  # hidden from repr

    db: InitVar[object] = None  # passed to __post_init__, not stored

    def __post_init__(self, db):
        Order.COUNTER += 1
        object.__setattr__(self, 'order_id', Order.COUNTER)  # frozen needs this
        if db:
            db.register(self)

# Utility functions
order = Order(items=["a", "b"], discount=0.1)
asdict(order)    # → recursive dict
astuple(order)   # → recursive tuple
replace(order, discount=0.2)  # new instance with changed field (like copy-with)
fields(Order)    # → tuple of Field objects with metadata
```

## ⚠️ Common Mistakes & Interview Traps

1. **Mutable defaults**: `field(default=[])` also fails — `default_factory=list` is always the answer for mutable defaults.

2. **`frozen=True` + inheritance**: A frozen dataclass can only inherit from another frozen dataclass or a plain non-dataclass. Mixing frozen with non-frozen subclasses raises `TypeError`.

3. **`__hash__` behavior**: If `eq=True` (default) and you don't set `frozen=True` or `unsafe_hash=True`, `__hash__` is set to `None`. The instance is unhashable. Many devs are surprised that `{MyDataclass()}` raises `TypeError`.

4. **`ClassVar` without import**: `ClassVar` must be from `typing`. Writing `x: ClassVar[int]` without importing `ClassVar` makes the field treated as a regular instance field.

5. **`replace()` and frozen instances**: `dataclasses.replace(instance, field=new_val)` creates a new frozen instance — the correct way to "mutate" an immutable dataclass.

## 🔗 Related Concepts
- `python_core/006_slots` — `slots=True` in dataclasses generates `__slots__`
- `python_core/016_hash_eq` — `eq=True` + `frozen=True` interaction with `__hash__`
- `python_core/009_decorator_internals` — `@dataclass` is a class decorator

## 📚 Go Deeper
- CPython source: `Lib/dataclasses.py` — the full code generation is readable and instructive
- PEP 557 — "Data Classes" — design decisions and rejected alternatives
