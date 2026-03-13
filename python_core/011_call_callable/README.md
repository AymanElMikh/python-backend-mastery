# `__call__` & the Callable Protocol

## 🎯 Interview Question
What makes an object callable in Python? How does `__call__` work, and when would you implement it on a class instead of using a plain function? What are the performance and design implications?

## 💡 Short Answer (30 seconds)
Any object with a `__call__` method is callable — `obj(args)` translates to `type(obj).__call__(obj, args)`. You use a class with `__call__` when you need a callable that carries state between invocations: rate limiters, memoizers, partially-applied functions, or middleware handlers. The design trade-off versus closures is readability and testability: a class is inspectable; a closure's state is hidden.

## 🔬 Deep Explanation

### The callable protocol
`callable(obj)` returns `True` if `type(obj)` defines `__call__`. Python checks the *type*, not the instance — you can't make an individual instance callable by adding `__call__` to `obj.__dict__`. This is consistent with how all dunder methods work: they're looked up on the type, not the instance.

```python
obj = object()
obj.__call__ = lambda: 42  # doesn't make obj callable!
callable(obj)  # False — type(obj) doesn't define __call__
```

### Dispatch chain: `obj(args)` → `type(obj).__call__(obj, args)`
When you write `f(x)`, CPython executes the `CALL` bytecode, which:
1. Looks up `__call__` on `type(f)` (not `f` itself)
2. Invokes it

This means `type.__call__` is what makes `MyClass(args)` create instances — `type.__call__` calls `MyClass.__new__` then `MyClass.__init__`.

### Callable classes vs closures
Both achieve the same goal (a callable with state), but differ:

| | Class with `__call__` | Closure |
|---|---|---|
| State introspection | `obj.counter` — visible | Hidden in `nonlocal` |
| Testability | Reset state via `obj.counter = 0` | Hard to reset |
| Serialization | Can implement `__getstate__` | Can't pickle |
| Overhead | Slightly higher (object allocation) | Lighter |
| Readability | Explicit | Terse |

### `functools.partial` as a callable
`partial(func, *args, **kwargs)` returns a callable object (not a function) that calls `func` with the pre-applied args. It's a class with `__call__`. `partial(func, x).__call__(y)` = `func(x, y)`.

### `__call__` in middleware and hooks
WSGI middleware wraps an app: `class Middleware: def __call__(self, environ, start_response): ...`. Each middleware layer is a callable — the framework just calls it with the request. This pattern is everywhere: Flask/Django middleware, Celery task chains, pytest fixtures.

### `operator.methodcaller` and `operator.itemgetter`
Both are callable objects returned by factory functions. `operator.itemgetter('name')` returns an object whose `__call__` does `obj['name']`. Used as sort keys: `sorted(items, key=operator.itemgetter('age'))`.

### Checking callability
`callable(obj)` is faster than `hasattr(obj, '__call__')` and handles edge cases correctly (e.g., `__call__` defined on the instance dict doesn't make it callable, but `callable()` accounts for this).

## 💻 Code Example

```python
import functools
import time

class RateLimiter:
    """Callable that enforces a minimum interval between calls."""

    def __init__(self, func, min_interval=1.0):
        functools.update_wrapper(self, func)
        self.func = func
        self.min_interval = min_interval
        self._last_called = 0.0

    def __call__(self, *args, **kwargs):
        now = time.monotonic()
        since_last = now - self._last_called
        if since_last < self.min_interval:
            raise RuntimeError(
                f"Rate limit: must wait {self.min_interval - since_last:.2f}s"
            )
        self._last_called = now
        return self.func(*args, **kwargs)


class Memoize:
    """Callable with persistent cache — state visible and resettable."""

    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.cache: dict = {}
        self.hits = 0
        self.misses = 0

    def __call__(self, *args):
        if args in self.cache:
            self.hits += 1
            return self.cache[args]
        self.misses += 1
        result = self.func(*args)
        self.cache[args] = result
        return result

    def cache_clear(self):
        self.cache.clear()
        self.hits = self.misses = 0


# WSGI-style middleware pattern
class RequestLogger:
    def __init__(self, app):
        self.app = app  # next callable in chain

    def __call__(self, request):
        print(f"  → {request['method']} {request['path']}")
        response = self.app(request)
        print(f"  ← {response['status']}")
        return response
```

## ⚠️ Common Mistakes & Interview Traps

1. **`__call__` on instance dict doesn't work**: `obj.__call__ = lambda: 42` — Python looks up `__call__` on `type(obj)`, not `obj.__dict__`. The instance dict assignment is silently ignored for callability.

2. **`callable()` vs `hasattr(type(obj), '__call__')`**: They are equivalent for type-defined `__call__`, but `callable()` is the correct idiom. Some objects (like some `__call__`-less C types) report differently.

3. **Class-based decorator on methods**: A class with `__call__` used as a decorator on an instance method breaks `self` binding unless you implement `__get__` to return a bound version.

4. **Forgetting `functools.update_wrapper`**: A class with `__call__` that wraps a function loses `__name__`, `__doc__`, etc. Use `functools.update_wrapper(self, func)` in `__init__`.

5. **`type.__call__` is the class creation mechanism**: `MyClass(args)` calls `type.__call__(MyClass, args)` which calls `MyClass.__new__` then `MyClass.__init__`. Overriding `__call__` on a metaclass changes how class instantiation works — a metaclass trap.

## 🔗 Related Concepts
- `python_core/009_decorator_internals` — class-based decorators use `__call__`
- `python_core/004_metaclasses` — `type.__call__` orchestrates class instantiation
- `python_core/003_descriptors` — `__call__` on a descriptor enables method binding

## 📚 Go Deeper
- CPython source: `Objects/typeobject.c` — `slot_tp_call()` and `type_call()`
- `functools.partial` source — a clean production example of `__call__`
