# MRO & C3 Linearization with `super()`

## 🎯 Interview Question
How does Python's Method Resolution Order (MRO) work with multiple inheritance? Explain C3 linearization and how `super()` uses it. What goes wrong when you call `super().__init__()` incorrectly in a diamond hierarchy?

## 💡 Short Answer (30 seconds)
Python uses C3 linearization to compute a consistent MRO — the order in which classes are searched for a method. `super()` doesn't mean "call my parent" — it means "call the next class in the MRO." In a diamond hierarchy, every class in the chain must call `super().__init__()` for cooperative multiple inheritance to work correctly; if any class breaks the chain, some base classes' `__init__` methods are silently skipped.

## 🔬 Deep Explanation

### C3 Linearization Algorithm
Given `class C(A, B)`, the MRO is computed as:
```
L[C] = C + merge(L[A], L[B], [A, B])
```
`merge` picks the head of each list if it doesn't appear in the tail of any other list, removes it from all lists, and repeats. The algorithm guarantees:
1. A class always appears before its parents
2. The order of bases in `class C(A, B)` is preserved
3. Monotonicity: if `D` inherits from `C`, `D`'s MRO includes `C`'s MRO in order

`MyClass.__mro__` or `MyClass.mro()` exposes the computed order.

### `super()` — it's not "call parent"
`super()` returns a proxy that delegates attribute lookup to the **next class in the MRO** of the *instance's actual class*, not the class where `super()` is written. This is why cooperative multiple inheritance works: each class says "do my part, then pass to whoever is next in the chain."

### The diamond problem
```
     Base
    /    \
   A      B
    \    /
      C
```
`C.__mro__ = [C, A, B, Base, object]`

If all classes call `super().__init__()`, `Base.__init__` is called exactly once. If `A.__init__` calls `Base.__init__` directly (bypassing `super()`), `B.__init__` is never called.

### `super()` arguments (pre-3.x)
In Python 3, `super()` with no arguments works via cell magic (`__class__` implicit closure). In Python 2, you had to write `super(MyClass, self)`. The zero-argument form is almost always correct in Python 3.

### When `super()` calls the wrong thing
If class `A` doesn't expect extra kwargs but `B` passes them via `super().__init__(**kwargs)`, you'll get `TypeError`. Solution: use `**kwargs` all the way up and have `object.__init__` accept nothing (or use keyword-only args cleanly).

### MRO with `__mixin__` pattern
Mixins are designed for cooperative inheritance — they should always call `super()` even if they don't know what comes next. A mixin that doesn't call `super()` breaks the chain.

## 💻 Code Example

```python
class Base:
    def __init__(self):
        print("  Base.__init__")
        super().__init__()  # calls object.__init__

class A(Base):
    def __init__(self):
        print("  A.__init__")
        super().__init__()  # calls B.__init__ (not Base!) in diamond

class B(Base):
    def __init__(self):
        print("  B.__init__")
        super().__init__()  # calls Base.__init__

class Diamond(A, B):
    def __init__(self):
        print("  Diamond.__init__")
        super().__init__()  # starts the chain: A → B → Base → object

# Diamond.__mro__ = [Diamond, A, B, Base, object]
# Each __init__ runs exactly once
d = Diamond()

# Mixin pattern
class LogMixin:
    def save(self):
        print(f"  [{type(self).__name__}] logging before save")
        super().save()  # pass to next in MRO — doesn't know what that is

class Model:
    def save(self):
        print("  Model.save() called")

class AuditedModel(LogMixin, Model):
    pass  # MRO: [AuditedModel, LogMixin, Model, object]
```

## ⚠️ Common Mistakes & Interview Traps

1. **`super()` in a mixin that doesn't call `super()`**: Breaks the cooperative chain silently. Every class in a multiple inheritance hierarchy must call `super()` for the pattern to work.

2. **Calling the parent directly**: `Base.__init__(self)` instead of `super().__init__()` bypasses the MRO and causes duplicate or missing `__init__` calls in diamond hierarchies.

3. **Inconsistent MRO raises TypeError**: Python raises `TypeError: Cannot create a consistent method resolution order` if the C3 algorithm fails (e.g., `class C(A, B)` where `B` is a parent of `A` but listed after it).

4. **`super()` in `@staticmethod`**: `super()` uses the `__class__` implicit closure — not available in `@staticmethod`. Use `super(MyClass, cls)` explicitly or switch to `@classmethod`.

5. **Assuming `super()` always calls the direct parent**: The most common misconception. In a diamond with 4 classes, `A`'s `super()` may call `B` (a sibling), not `Base`.

## 🔗 Related Concepts
- `python_core/004_metaclasses` — MRO applies to metaclass hierarchies too
- `python_core/001_new_vs_init` — `super().__new__` vs `super().__init__` in cooperative hierarchies
- `oop/` — SOLID, ABC — mixin patterns rely on correct MRO usage

## 📚 Go Deeper
- Michele Simionato's "The Python 2.3 Method Resolution Order" — the definitive explanation of C3
- Python docs: "super() considered super!" by Raymond Hettinger
