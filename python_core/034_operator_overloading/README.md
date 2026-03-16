# Operator Overloading — Dunder Arithmetic & Rich Comparisons

## 🎯 Interview Question
Explain Python's operator overloading protocol: how does `a + b` actually work, what is the role of `__radd__`, and when would you return `NotImplemented` instead of raising `TypeError`?

## 💡 Short Answer (30 seconds)
`a + b` first tries `a.__add__(b)`. If that returns `NotImplemented` (or doesn't exist), Python tries `b.__radd__(a)` — the *reflected* operation. Returning `NotImplemented` (not raising) signals Python to try the other operand's method. This is the correct extensibility hook; raising `TypeError` short-circuits the fallback chain.

## 🔬 Deep Explanation
**Lookup order for `a OP b`:**
1. If `type(b)` is a subclass of `type(a)`, Python tries `b.__rop__(a)` *first* (subclass priority).
2. Otherwise: `a.__op__(b)` → if `NotImplemented`, then `b.__rop__(a)` → if still `NotImplemented`, raise `TypeError`.

**Augmented assignment (`+=`, `-=`…):**
- Tries `__iadd__` first (in-place); if absent, falls back to `__add__` + rebind.
- For immutables (int, str, tuple) there is no `__iadd__` — Python always rebinds.

**Rich comparisons (`__lt__`, `__le__`, `__eq__`, `__ne__`, `__gt__`, `__ge__`):**
- Use `functools.total_ordering` to define only `__eq__` + one inequality and get the rest generated.
- `__eq__` returning `NotImplemented` causes Python to try the reflected `other.__eq__(self)`.
- If both return `NotImplemented`, Python falls back to identity comparison (`is`).

**`@functools.total_ordering`** fills in missing methods but has a subtle performance cost — each generated comparison method invokes the base methods dynamically. For hot paths, implement all 6 explicitly.

**Type coercion pattern** — numeric tower (int → float → complex) uses `__radd__` / `__rmul__` to let custom types interoperate with built-ins without modifying built-in classes.

## 💻 Code Example
```python
from functools import total_ordering
import math

@total_ordering
class Vector:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        return NotImplemented          # let Python try other.__radd__

    def __radd__(self, other):
        # e.g. 0 + Vector(...) — used by sum([v1, v2, ...])
        if other == 0:                 # sum() starts with 0 + first_item
            return self
        return NotImplemented

    def __mul__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Vector(self.x * scalar, self.y * scalar)
        return NotImplemented

    def __rmul__(self, scalar):        # allows: 3 * Vector(...)
        return self.__mul__(scalar)

    def __iadd__(self, other):         # in-place, returns self (mutates)
        if isinstance(other, Vector):
            self.x += other.x
            self.y += other.y
            return self
        return NotImplemented

    def __abs__(self):
        return math.hypot(self.x, self.y)

    def __eq__(self, other):
        return isinstance(other, Vector) and (self.x, self.y) == (other.x, other.y)

    def __lt__(self, other):
        return abs(self) < abs(other)

    def __repr__(self):
        return f"Vector({self.x}, {self.y})"

v1 = Vector(1, 2)
v2 = Vector(3, 4)
print(v1 + v2)            # Vector(4, 6)
print(3 * v1)             # Vector(3, 6)  — via __rmul__
print(sum([v1, v2]))      # Vector(4, 6)  — via __radd__(0)
v1 += v2                  # __iadd__
print(v1)                 # Vector(4, 6)
print(v1 > v2)            # total_ordering generates __gt__ from __lt__ + __eq__
```

## ⚠️ Common Mistakes & Interview Traps
- **Raising instead of returning `NotImplemented`** — kills the reflected-method fallback. Always `return NotImplemented`.
- **`__eq__` without `__hash__`** — defining `__eq__` sets `__hash__ = None`, making the object unhashable. Override `__hash__` explicitly.
- **`__iadd__` must return `self`** — forgetting the return causes `x += y` to rebind `x` to `None`.
- **Subclass priority**: if `class B(A)` overrides `__radd__`, `a + b` calls `B.__radd__` first even though `a` is left operand.

## 🔗 Related Concepts
- python_core/016_hash_eq — __eq__ and __hash__ contract
- python_core/003_descriptors — how dunder lookup bypasses normal attribute resolution
- python_core/017_functools_deep — total_ordering lives in functools

## 📚 Go Deeper
- PEP 207 — Rich Comparisons
- CPython `Objects/abstract.c` — `binary_op1()` implements the reflected fallback chain
