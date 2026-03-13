# Decorator Internals & `functools.wraps`

## 🎯 Interview Question
How do decorators work at the bytecode level? Why does `functools.wraps` matter, and what breaks without it? How do you write a decorator that accepts arguments, and how does a class-based decorator differ from a function-based one?

## 💡 Short Answer (30 seconds)
A decorator is syntactic sugar: `@dec` is `func = dec(func)`. It replaces the original function with whatever `dec` returns — usually a wrapper. Without `functools.wraps`, the wrapper's `__name__`, `__doc__`, and `__wrapped__` are wrong, breaking introspection, logging, and FastAPI/Flask route detection. Argument-accepting decorators add one more layer of nesting: a function that returns a decorator that returns a wrapper.

## 🔬 Deep Explanation

### Bytecode translation
```python
@decorator
def func():
    pass
```
Compiles to exactly:
```python
def func():
    pass
func = decorator(func)
```
The `@` is purely syntactic — Python executes the decorator expression, calls it with the function, and rebinds the name.

### Why `functools.wraps` is critical
Without it, the wrapper function has:
- `wrapper.__name__` = `'wrapper'` (not `'func'`)
- `wrapper.__doc__` = the wrapper's docstring
- `wrapper.__module__`, `wrapper.__qualname__`, `wrapper.__annotations__` = the wrapper's

This breaks:
- FastAPI: reads `__name__` to deduplicate routes
- `help()` / Sphinx docs
- `pytest` test discovery (finds `'wrapper'` instead of test name)
- `logging` and error reporting
- `functools.lru_cache` introspection

`functools.wraps(func)` copies `__name__`, `__qualname__`, `__doc__`, `__dict__`, `__module__`, `__annotations__`, and sets `__wrapped__ = func`.

### Decorator with arguments — 3-layer nesting
```python
@retry(times=3, delay=1.0)
def fetch(url): ...
```
Calls: `fetch = retry(times=3, delay=1.0)(fetch)`
So `retry(...)` must return a decorator, which returns a wrapper.

### `functools.wraps` preserves `__wrapped__`
`wrapper.__wrapped__` is set to the original function. This lets tools "unwrap" decorator chains. `inspect.unwrap(func)` follows `__wrapped__` all the way to the original.

### Class-based decorators
A class is callable if it has `__call__`. Using a class as a decorator lets you store state between calls:
```python
class Count:
    def __init__(self, func):
        functools.update_wrapper(self, func)  # same as wraps
        self.func = func
        self.calls = 0
    def __call__(self, *args, **kwargs):
        self.calls += 1
        return self.func(*args, **kwargs)
```
Limitation: class-based decorators on methods are tricky — they break `self` binding. Use `__get__` to implement the descriptor protocol.

### Stacking decorators
```python
@a
@b
@c
def f(): ...
# Equivalent to: f = a(b(c(f)))
# Outermost decorator runs last at definition, first at call time
```

### `functools.lru_cache` as a decorator
A decorator with optional arguments (Python 3.8+): `@lru_cache` and `@lru_cache(maxsize=128)` both work. Implemented by checking if the first argument is callable.

## 💻 Code Example

```python
import functools
import time

def retry(times=3, delay=0.0, exceptions=(Exception,)):
    """Three-layer decorator: factory → decorator → wrapper."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < times and delay:
                        time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator


def log_calls(func):
    """Simple decorator — logs entry and exit."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"→ {func.__name__}({args}, {kwargs})")
        result = func(*args, **kwargs)
        print(f"← {func.__name__} returned {result!r}")
        return result
    return wrapper


class Memoize:
    """Class-based decorator with state (call cache)."""
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if args not in self.cache:
            self.cache[args] = self.func(*args)
        return self.cache[args]

    def cache_info(self):
        return f"cache size: {len(self.cache)}"
```

## ⚠️ Common Mistakes & Interview Traps

1. **Forgetting `functools.wraps`**: The single most common decorator mistake in interviews. Always use it. FastAPI specifically breaks without it for route definitions.

2. **Mutable default in decorator factory**: `def retry(exceptions=[Exception])` — mutable default accumulates across calls. Use `exceptions=(Exception,)` (tuple).

3. **Class decorator breaking method binding**: `@MyDecorator` on an instance method replaces it with a `MyDecorator` instance. When accessed on the instance, Python doesn't call `__get__` unless the decorator implements the descriptor protocol (`__get__`).

4. **Stacking order confusion**: `@a @b` means `a(b(func))`. The "outermost" decorator (`a`) wraps the result of `b`. At call time, `a`'s wrapper runs first.

5. **`__wrapped__` chain**: `inspect.unwrap()` follows `__wrapped__` to the original. If a decorator doesn't use `functools.wraps`, the chain is broken and `unwrap` stops prematurely.

## 🔗 Related Concepts
- `python_core/003_descriptors` — class decorators on methods need `__get__`
- `python_core/008_generators_internals` — `@contextmanager` is a generator-based decorator
- `python_core/007_context_managers` — decorators and context managers are often combined

## 📚 Go Deeper
- `functools` module source — `wraps`, `update_wrapper`, `lru_cache` implementation
- PEP 318 — "Decorators for Functions and Methods" — original motivation
