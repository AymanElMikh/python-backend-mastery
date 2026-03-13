# Metaclasses & `type`

## 🎯 Interview Question
What is a metaclass in Python? How does class creation work under the hood, and when would you use a metaclass over a class decorator or `__init_subclass__`?

## 💡 Short Answer (30 seconds)
A metaclass is the class of a class — it controls how classes themselves are created. `type` is the default metaclass: `type(MyClass)` is `type`. You use a custom metaclass to intercept class creation and modify the class body, enforce constraints on subclasses, auto-register subclasses, or add class-level behavior. In modern Python, `__init_subclass__` and class decorators handle most metaclass use cases more simply.

## 🔬 Deep Explanation

### Everything is an object
In Python, classes are objects too. `MyClass = type('MyClass', (Base,), {'method': fn})` creates a class dynamically. `type` is both a function (for `type(obj)`) and a metaclass (for `type('Name', bases, namespace)`).

### Class creation pipeline
When Python sees:
```python
class MyClass(Base, metaclass=Meta):
    x = 1
```
It does:
1. Determine the metaclass: check `metaclass=` kwarg → check `Base`'s metaclass → default to `type`
2. Call `Meta.__prepare__(name, bases, **kwargs)` → returns the namespace dict (usually `{}`)
3. Execute the class body in that namespace
4. Call `Meta(name, bases, namespace)` → calls `Meta.__new__` then `Meta.__init__`

### `__prepare__` — ordered namespace
Before Python 3.6, class body dict was unordered. `__prepare__` lets metaclasses return a custom mapping. `enum.EnumMeta` uses it to detect duplicate member names (which a plain dict would silently overwrite). Python 3.6+ uses insertion-ordered dicts by default.

### `__new__` vs `__init__` on metaclasses
`Meta.__new__(mcs, name, bases, namespace)` — creates the class object itself. `Meta.__init__(cls, name, bases, namespace)` — configures the already-created class. Most metaclass logic goes in `__new__`.

### `__init_subclass__` (Python 3.6+) — the modern alternative
```python
class Plugin:
    _registry = {}
    def __init_subclass__(cls, plugin_name=None, **kwargs):
        super().__init_subclass__(**kwargs)
        if plugin_name:
            Plugin._registry[plugin_name] = cls
```
Called on the *parent* class when a subclass is created. Simpler than a metaclass for registration/validation. Cannot modify the class namespace (that's where metaclasses still win).

### When to use a metaclass (not `__init_subclass__`)
- Need to modify the class *namespace* before class body execution (`__prepare__`)
- Need to intercept attribute definition order
- Building a framework that needs deep class machinery (Django ORM, SQLAlchemy declarative, `enum.Enum`, `abc.ABCMeta`)
- Need to control `__new__` of every class in a hierarchy

### Metaclass conflict
If class `A` uses metaclass `Meta1` and class `B` uses metaclass `Meta2`, a class `C(A, B)` needs a metaclass that is a subclass of BOTH. Python raises `TypeError: metaclass conflict` if it can't find one automatically.

## 💻 Code Example

```python
class RegistryMeta(type):
    """Metaclass that auto-registers all subclasses in a central registry."""
    _registry: dict = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        # Don't register the base class itself
        if bases:
            mcs._registry[name] = cls
        return cls


class EnforcingMeta(type):
    """Metaclass that enforces all methods have docstrings."""

    def __new__(mcs, name, bases, namespace):
        for attr_name, attr_val in namespace.items():
            if callable(attr_val) and not attr_name.startswith('_'):
                if not attr_val.__doc__:
                    raise TypeError(
                        f"Method '{attr_name}' in class '{name}' must have a docstring"
                    )
        return super().__new__(mcs, name, bases, namespace)


# Modern alternative: __init_subclass__
class Handler:
    _handlers: dict = {}

    def __init_subclass__(cls, event_type=None, **kwargs):
        super().__init_subclass__(**kwargs)
        if event_type:
            Handler._handlers[event_type] = cls
```

## ⚠️ Common Mistakes & Interview Traps

1. **Metaclass conflict**: Combining two classes with different metaclasses causes `TypeError`. Fix: create a combined metaclass that inherits from both.

2. **Overusing metaclasses**: Most metaclass use cases in modern Python are better served by `__init_subclass__`, class decorators, or `__class_getitem__`. Reach for metaclasses only when you need `__prepare__` or truly deep class creation control.

3. **Calling `super().__new__`**: Forgetting to call `super().__new__(mcs, name, bases, namespace)` in `Meta.__new__` creates an incomplete class.

4. **`type(cls)` vs `cls.__class__`**: For classes, `type(MyClass)` returns the metaclass. `MyClass.__class__` also works but `type()` is the idiomatic form.

5. **ABCMeta is a metaclass**: `class Foo(ABC)` works because `ABC = ABCMeta('ABC', (), {})`. When you use `ABCMeta` + your own metaclass, you must resolve the conflict manually.

## 🔗 Related Concepts
- `python_core/001_new_vs_init` — metaclass `__call__` invokes `cls.__new__` then `cls.__init__`
- `python_core/003_descriptors` — `__set_name__` is called by the default `type.__new__`
- `python_core/005_mro_super` — MRO applies to metaclass hierarchies too

## 📚 Go Deeper
- PEP 3115 — "Metaclasses in Python 3000" (introduced `__prepare__`)
- CPython source: `Objects/typeobject.c` — `type_new()` is the full class creation pipeline
