# `__slots__` & Memory Layout

## 🎯 Interview Question
What does `__slots__` do in Python, why does it reduce memory usage, and what are the trade-offs? When would you use it in a production backend, and what breaks when you add it to an existing class?

## 💡 Short Answer (30 seconds)
`__slots__` replaces the per-instance `__dict__` with a fixed array of slots — essentially C struct fields. This eliminates the hash table overhead of `__dict__` (~200 bytes per instance), making it critical when you create millions of small objects. The trade-off: you lose dynamic attribute assignment, `__weakref__` (unless explicitly listed), and pickling by default. Use it for value objects, data transfer objects, and hot-path model classes.

## 🔬 Deep Explanation

### Why `__dict__` is expensive
Every normal Python object carries a `__dict__` — a hash table (`PyDictObject`) that stores attribute names as string keys. Even an empty `__dict__` costs ~232 bytes in CPython 3.11+. With 1 million instances, that's ~232 MB just for empty dicts.

### What `__slots__` does
When you declare `__slots__ = ('x', 'y')`:
1. The class body stores the slot names
2. CPython creates **member descriptors** (a type of descriptor) for each slot
3. Instances get a compact C array instead of a `__dict__`
4. Attribute access goes directly to an offset in the object's memory block

Result: instance size drops from `sizeof(object) + sizeof(dict) + dict_overhead` to `sizeof(object) + n_slots * sizeof(pointer)`.

### `sys.getsizeof` comparison
```python
import sys
class WithDict:   x = 0; y = 0
class WithSlots: __slots__ = ('x', 'y')

obj_d = WithDict();   obj_d.x = 1; obj_d.y = 2
obj_s = WithSlots();  obj_s.x = 1; obj_s.y = 2

sys.getsizeof(obj_d)  # typically 48 bytes + 232 for __dict__ = ~280
sys.getsizeof(obj_s)  # typically 56 bytes total
```

### What breaks with `__slots__`

| Feature | Breaks? | Fix |
|---------|---------|-----|
| Dynamic attributes | Yes | Add `'__dict__'` to `__slots__` |
| Weak references | Yes | Add `'__weakref__'` to `__slots__` |
| Default `__repr__` via `__dict__` | Not directly | Unaffected |
| Multiple inheritance with another slotted class | Sometimes | Align slot definitions |
| `copy.copy` / `pickle` | Partially | Implement `__getstate__`/`__setstate__` |

### `__slots__` in inheritance
If a parent doesn't define `__slots__`, subclasses get a `__dict__` regardless. The parent's `__dict__` is always present. `__slots__` only eliminates `__dict__` when the *entire* chain defines it.

### `__slots__` with `dataclasses`
`@dataclass(slots=True)` (Python 3.10+) auto-generates `__slots__`. This is the modern idiomatic way to get slotted data classes.

### Real-world use
- FastAPI/Pydantic v2 uses `__slots__` in internal validators for throughput
- `datetime`, `decimal.Decimal`, and most built-ins are implemented in C with slot-equivalent layout
- Cache-heavy microservices that hold millions of small model objects in memory

## 💻 Code Example

```python
import sys

class Point:
    """Normal class — has __dict__."""
    def __init__(self, x, y):
        self.x = x
        self.y = y

class SlottedPoint:
    """Slotted class — no __dict__, fixed memory layout."""
    __slots__ = ('x', 'y')

    def __init__(self, x, y):
        self.x = x
        self.y = y

class FlexSlotted:
    """Slots + __dict__ — reduced but flexible."""
    __slots__ = ('x', 'y', '__dict__', '__weakref__')

    def __init__(self, x, y):
        self.x = x
        self.y = y

# Memory comparison
p = Point(1, 2)
sp = SlottedPoint(1, 2)
print(sys.getsizeof(p))   # instance header only — but __dict__ is separate
print(sys.getsizeof(sp))  # includes slot storage — smaller

# Can't add dynamic attrs to slotted class
try:
    sp.z = 3  # AttributeError: 'SlottedPoint' has no attribute 'z'
except AttributeError as e:
    print(e)

# __slots__ doesn't inherit automatically
class ExtPoint(SlottedPoint):
    pass  # no __slots__ → gets __dict__ back!
    # Only SlottedPoint's x, y are slotted; ExtPoint gets a __dict__
```

## ⚠️ Common Mistakes & Interview Traps

1. **`__slots__` in a subclass of a non-slotted class has no effect**: The parent's `__dict__` is always present. You save slot overhead for the new attributes, but `__dict__` persists.

2. **Forgetting `__weakref__`**: Libraries using weak references (e.g., `weakref.finalize`, some caches) break silently. Always add `'__weakref__'` to `__slots__` unless you're certain it's not needed.

3. **Class variables vs slots**: `__slots__` are instance storage. If you add a class-level default (`class Foo: __slots__ = ('x',); x = 0`), the class attribute shadows the slot descriptor.

4. **Multiple inheritance with different slots**: `class C(A, B)` where both `A` and `B` have `__slots__` causes a layout conflict if both have non-empty slots. CPython raises `TypeError`.

5. **Pickling**: `pickle` uses `__dict__` by default. Slotted objects need `__getstate__`/`__setstate__` or `__reduce__`.

## 🔗 Related Concepts
- `python_core/003_descriptors` — slots are implemented as member descriptors
- `python_core/001_new_vs_init` — `__new__` allocates the fixed-size slot array
- `python_core/010_memory_model_gc` — slots interact with reference counting layout

## 📚 Go Deeper
- CPython source: `Include/cpython/object.h` — `PyMemberDef` struct (slot definition)
- Python docs: `@dataclass(slots=True)` — modern slotted dataclasses (Python 3.10+)
