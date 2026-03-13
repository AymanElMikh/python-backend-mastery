# `__new__` vs `__init__`

## 🎯 Interview Question
What is the difference between `__new__` and `__init__` in Python? When would you override `__new__` instead of `__init__`, and what are the consequences of getting this wrong?

## 💡 Short Answer (30 seconds)
`__new__` is the object *allocator* — it creates and returns the instance. `__init__` is the object *initializer* — it configures the already-created instance. You override `__new__` when you need to control object creation itself: implementing singletons, immutable types (subclassing `int`, `str`, `tuple`), or custom memory allocation.

## 🔬 Deep Explanation

Python's object creation is a two-phase protocol:

1. **`cls.__new__(cls, *args, **kwargs)`** — called on the *class*, returns a new instance. If it returns an instance of `cls`, Python then calls `__init__` on it automatically.
2. **`self.__init__(*args, **kwargs)`** — called on the *instance*, returns `None` (always).

### Why does this matter?

**Immutable types** (`int`, `str`, `tuple`, `frozenset`) are set in stone after `__new__` because CPython stores their value in the C struct at allocation time. By the time `__init__` is called, you can't change a `str`'s characters. That's why `str.__new__` accepts the value — `str.__init__` ignores it.

```python
class UpperStr(str):
    def __new__(cls, value):
        return super().__new__(cls, value.upper())  # must happen here
    # __init__ is too late — the string is already immutable
```

**Singleton pattern** requires `__new__` — you need to intercept allocation and return the cached instance before `__init__` runs a second time.

**`__new__` return type** is critical: if `__new__` returns something that is *not* an instance of `cls`, Python skips `__init__` entirely. This is a common source of bugs when chaining metaclass hierarchies.

### CPython internals
`object.__new__` calls `tp_alloc` in C, zeroing memory and setting the refcount. It's equivalent to `malloc` + type setup. `object.__init__` is essentially a no-op for the base case.

### When `__new__` and `__init__` receive arguments
Both are passed the same `*args, **kwargs`. If you override `__new__` and `__init__` independently, you must be careful — Python will pass all constructor args to both. This causes `TypeError` if the base class doesn't expect them.

## 💻 Code Example

```python
class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Control allocation — only create once
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance  # __init__ will still be called each time!

    def __init__(self, value):
        self.value = value  # WARNING: called on every Singleton() call


class BoundedInt(int):
    """An int that clamps itself to [0, 100] at creation time."""
    def __new__(cls, value):
        clamped = max(0, min(100, value))
        return super().__new__(cls, clamped)
        # No __init__ needed — int is immutable, value is baked in


class SkipInit:
    def __new__(cls):
        print("__new__ called")
        return 42  # not an instance of cls!

    def __init__(self):
        print("__init__ called")  # never runs — __new__ returned non-cls type
```

## ⚠️ Common Mistakes & Interview Traps

1. **Singleton `__init__` re-runs**: The singleton `__new__` returns the cached instance, but `__init__` runs again on every `Singleton()` call, resetting state. Fix: use a flag `_initialized` or move state to `__new__`.

2. **Immutable subclass confusion**: Trying to modify an immutable type in `__init__` doesn't work. Interviewers love asking "why does `class MyStr(str): def __init__(self, v): self.data = v.upper()` not change the string value?"

3. **`super().__new__` with extra args**: `object.__new__` in Python 3 complains if you pass extra args when `__init__` is not the default, and vice versa. The protocol changed subtly in 3.3+.

4. **`__new__` must return something**: Forgetting `return` in `__new__` returns `None`, making `__init__` crash with `AttributeError` or get skipped.

## 🔗 Related Concepts
- `python_core/004_metaclasses` — metaclass `__call__` orchestrates `__new__` + `__init__`
- `python_core/003_descriptors` — descriptors are often initialized in `__new__`
- `python_core/010_memory_model_gc` — how `__new__` interacts with CPython's allocator

## 📚 Go Deeper
- CPython source: `Objects/typeobject.c` — `type_call()` shows the `__new__` → `__init__` orchestration
- PEP 3107 + data model docs: "Customizing class creation" section
