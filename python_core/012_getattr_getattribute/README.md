# `__getattr__` vs `__getattribute__`

## 🎯 Interview Question
What is the difference between `__getattr__` and `__getattribute__`? When is each called, and what are the risks of overriding `__getattribute__`? Give a real use case for each.

## 💡 Short Answer (30 seconds)
`__getattribute__` is called on *every* attribute access — it's the entry point for all lookups. `__getattr__` is called only as a *fallback* when the normal lookup fails (attribute not found in instance dict, class dict, or MRO). Override `__getattr__` for lazy/dynamic attributes. Override `__getattribute__` only when you need to intercept *all* access — it's dangerous because calling `self.anything` inside it causes infinite recursion unless you route through `super().__getattribute__`.

## 🔬 Deep Explanation

### Standard attribute lookup chain (simplified)
When you access `obj.attr`, Python calls `type(obj).__getattribute__(obj, 'attr')`. The default `object.__getattribute__` does:
1. Look for `attr` in `type(obj).__mro__` as a **data descriptor** (has `__set__`)
2. Look in `obj.__dict__`
3. Look in `type(obj).__mro__` as a **non-data descriptor** or plain class attribute
4. If all fail → call `type(obj).__getattr__(obj, 'attr')` if defined
5. Else → raise `AttributeError`

### `__getattr__` — the fallback
Only called when normal lookup raises `AttributeError`. Safe to override:
```python
def __getattr__(self, name):
    # Only called if 'name' not found normally
    return self._compute(name)
```
Use cases:
- **Proxy objects**: forward unknown attributes to a wrapped object
- **Lazy initialization**: compute and cache on first access
- **Dynamic attribute sets**: `mock.any_attr_returns_mock`
- **ORM magic**: `row.column_name` where columns are dynamic

### `__getattribute__` — intercepts everything
Called for *every* attribute access, including `self.x` inside the class itself. The critical danger: calling `self.anything` inside `__getattribute__` calls `__getattribute__` again → infinite recursion.

Safe pattern: always delegate to `super().__getattribute__(name)` or use `object.__getattribute__(self, name)`.

```python
def __getattribute__(self, name):
    # WRONG: self.log → infinite recursion
    # RIGHT:
    result = super().__getattribute__(name)
    object.__getattribute__(self, '_log')(name)  # or use super() again
    return result
```

### `__setattr__` and `__delattr__` — the full family
Same pattern: `__setattr__` intercepts all writes, `__delattr__` all deletes. Same recursion danger: use `object.__setattr__(self, name, value)` inside `__setattr__`.

### Proxy pattern with `__getattr__`
```python
class Proxy:
    def __init__(self, target):
        object.__setattr__(self, '_target', target)  # bypass our __setattr__

    def __getattr__(self, name):
        return getattr(self._target, name)  # forward unknown attrs

    def __setattr__(self, name, value):
        setattr(self._target, name, value)  # forward writes too
```

### Access logging with `__getattribute__`
```python
class Audited:
    def __getattribute__(self, name):
        if not name.startswith('_'):
            print(f"ACCESS: {name}")
        return super().__getattribute__(name)
```

## 💻 Code Example

```python
class LazyConfig:
    """__getattr__ for lazy-loaded config values."""

    def __init__(self, data: dict):
        self._data = data
        self._computed = {}

    def __getattr__(self, name):
        # Only called when normal lookup fails
        if name in self._data:
            value = self._data[name].upper()  # simulate expensive transform
            self._computed[name] = value
            return value
        raise AttributeError(f"No config key: {name!r}")


class AuditedModel:
    """__getattribute__ to log every access to non-private attrs."""

    def __init__(self, **kwargs):
        # Must use object.__setattr__ to avoid our own __setattr__
        object.__setattr__(self, '_access_log', [])
        for k, v in kwargs.items():
            object.__setattr__(self, k, v)

    def __getattribute__(self, name):
        if not name.startswith('_'):
            log = object.__getattribute__(self, '_access_log')
            log.append(name)
        return object.__getattribute__(self, name)

    def access_log(self):
        return object.__getattribute__(self, '_access_log')
```

## ⚠️ Common Mistakes & Interview Traps

1. **Infinite recursion in `__getattribute__`**: Any `self.x` inside your override calls `__getattribute__` again. Always use `object.__getattribute__(self, 'x')` or `super().__getattribute__('x')`.

2. **`__getattr__` not called for existing attributes**: If `obj.x` exists in `obj.__dict__`, `__getattr__` is never called. It's only a fallback, not an interceptor.

3. **`__setattr__` for all writes, including `__init__`**: If you define `__setattr__`, `self.x = y` in `__init__` goes through it too. Use `object.__setattr__(self, 'x', y)` in `__init__` if you want to bypass your own `__setattr__`.

4. **Proxy storing `_target` in its own `__setattr__`**: The proxy pattern requires storing `_target` via `object.__setattr__` — otherwise writing `self._target = target` in `__init__` calls your intercepting `__setattr__` before `_target` exists → infinite recursion or `AttributeError`.

5. **`getattr(obj, name, default)` catches AttributeError from `__getattr__`**: If `__getattr__` raises `AttributeError`, `getattr(..., default)` returns the default. Any other exception propagates.

## 🔗 Related Concepts
- `python_core/003_descriptors` — descriptors are part of the `__getattribute__` lookup chain
- `python_core/006_slots` — `__slots__` bypass `__dict__` in the lookup chain
- `python_core/004_metaclasses` — metaclasses use `__getattribute__` too (on class access)

## 📚 Go Deeper
- CPython source: `Objects/object.c` — `_PyObject_GenericGetAttrWithDict()` — the full attribute lookup
- Python data model docs: "Customizing attribute access"
