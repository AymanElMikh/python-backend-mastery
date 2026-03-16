# property() vs Descriptors — Attribute Access Control

## 🎯 Interview Question
Explain how `@property` works under the hood. How is it different from a full descriptor, what is `__set_name__`, and when would you write a custom descriptor instead of using `@property`?

## 💡 Short Answer (30 seconds)
`@property` is a built-in non-data descriptor that uses `__get__`, `__set__`, and `__delete__` to intercept attribute access. It's syntactic sugar for writing a descriptor inline on a single class. You write a custom descriptor class when you need the same get/set/delete logic reused across *multiple* attributes or *multiple* classes — like a type-validated field, a unit-converted measurement, or an ORM column.

## 🔬 Deep Explanation
**Descriptor protocol recap:**
- `__get__(self, obj, objtype)` — called on attribute read.
- `__set__(self, obj, value)` — called on attribute write (makes it a *data* descriptor).
- `__delete__(self, obj)` — called on `del obj.attr`.
- `__set_name__(self, owner, name)` — called by `type.__new__` when the class is created; gives the descriptor its own attribute name automatically.

**Data vs non-data descriptors:**
- *Data descriptor* (has `__set__` or `__delete__`): takes priority over instance `__dict__`.
- *Non-data descriptor* (only `__get__`): instance `__dict__` takes priority.
- `@property` is a *data descriptor* (it has `__set__` raising `AttributeError` by default).

**`property()` internals:**
`@property` creates a `property` object (C-level `PyProperty_Type`). The full decorator chain:
```python
@property         # creates property with fget
def x(self): ...

@x.setter         # returns new property with fget + fset
def x(self, v): ...

@x.deleter        # returns new property with all three
def x(self): ...
```
Each decorator returns a *new* property object — a common gotcha when inheriting.

**When `@property` is not enough:**
- Need the same validation on 20 different fields → descriptor class is DRY.
- Need to store metadata (unit, min/max) per-field → descriptor carries it.
- ORM columns, Pydantic fields, Django model fields are all descriptors.

**`__set_name__` (Python 3.6+):**
Called automatically with the class and attribute name when the class body is executed. Before 3.6, descriptors had to be told their own name explicitly.

```python
class Typed:
    def __set_name__(self, owner, name):
        self.name = name
        self.private = f"_{name}"
    def __get__(self, obj, objtype=None):
        if obj is None: return self
        return getattr(obj, self.private, None)
    def __set__(self, obj, value):
        if not isinstance(value, self.type_):
            raise TypeError(f"{self.name} must be {self.type_.__name__}")
        setattr(obj, self.private, value)
```

## 💻 Code Example
```python
class Celsius:
    """Non-data descriptor — temperature stored in Kelvin."""
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None: return self
        return obj._kelvin - 273.15

    def __set__(self, obj, celsius):
        if celsius < -273.15:
            raise ValueError("Below absolute zero")
        obj._kelvin = celsius + 273.15

class Weather:
    temperature = Celsius()   # reusable across many classes

w = Weather()
w.temperature = 100
print(w.temperature)     # 100.0
print(w._kelvin)         # 373.15
```

## ⚠️ Common Mistakes & Interview Traps
- **`@property` in subclasses**: overriding just the setter requires re-declaring the getter via `@ParentClass.prop.getter` or redefining from scratch — forgetting this means the setter silently creates an instance attribute instead.
- **`__get__` called on the class**: when `obj is None`, `obj` is `None` and `objtype` is the class. Always handle `if obj is None: return self`.
- **Data vs non-data priority**: a non-data descriptor (no `__set__`) is *shadowed* by instance `__dict__` entries — writing `obj.attr = x` bypasses it entirely.
- **`__set_name__` not called manually**: if you add a descriptor to a class *after* class creation (e.g., `MyClass.field = MyDesc()`), `__set_name__` is NOT called automatically.

## 🔗 Related Concepts
- python_core/003_descriptors — full descriptor protocol
- python_core/006_slots — __slots__ uses descriptors internally
- python_core/012_getattr_getattribute — attribute lookup order

## 📚 Go Deeper
- Python Data Model — "Invoking Descriptors" section
- CPython `Objects/descrobject.c` — `property_descr_get` implementation
