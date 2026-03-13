# `functools` Deep Dive — `lru_cache`, `partial`, `reduce`, `cached_property`

## 🎯 Interview Question
Walk me through `functools.lru_cache` — how does it work internally, what are its limitations, and when does it break? Also explain `partial`, `cached_property`, and `reduce`.

## 💡 Short Answer (30 seconds)
`lru_cache` wraps a function with a dictionary-backed Least Recently Used cache keyed on the function arguments. Arguments must be hashable. It's a bounded cache — once full, the least recently used entry is evicted. `partial` pre-fills arguments on a callable, returning a new callable. `cached_property` computes a property once per instance and stores the result in the instance's `__dict__`, bypassing the property on future access.

## 🔬 Deep Explanation

### `lru_cache` — implementation internals
`lru_cache` stores results in a dict keyed on `(args, frozenset(kwargs.items()))`. Under the hood (CPython), it uses a circular doubly-linked list to track access order — moving accessed items to the front, evicting from the back when `maxsize` is reached. The C implementation is in `_functools.c`.

Key behaviors:
- `maxsize=None` → unbounded cache (no LRU eviction, faster — uses a plain dict)
- `maxsize=0` → disables caching entirely (useful for testing)
- Cache is per-function-object — each function instance has its own cache
- Thread-safe in CPython (GIL protects the dict)

```python
@lru_cache(maxsize=128)
def expensive(n):
    return sum(range(n))

expensive.cache_info()   # CacheInfo(hits=0, misses=0, maxsize=128, currsize=0)
expensive.cache_clear()  # clear the cache
```

### `lru_cache` limitations
1. **Arguments must be hashable**: `lru_cache` can't cache calls with list, dict, or set arguments
2. **No TTL (time-to-live)**: cached forever until `cache_clear()` or process restart
3. **Memory unbounded with `maxsize=None`**: grows until the process runs out of memory
4. **Doesn't work well with methods**: the `self` argument is part of the cache key — every instance gets cached entries. If instances are short-lived but the function is long-lived, this is a memory leak (old `self` objects kept alive by the cache)

### `partial` — partial application
`functools.partial(func, *args, **kwargs)` returns a `partial` object — a callable that calls `func` with the pre-applied args prepended. Equivalent to a closure but:
- The original function is accessible as `p.func`
- Pre-applied args/kwargs are inspectable as `p.args`, `p.keywords`
- Works with `callable()`, `inspect.signature()` (partially)

```python
from functools import partial

def power(base, exponent):
    return base ** exponent

square = partial(power, exponent=2)
cube   = partial(power, exponent=3)
# square(5) == 25, cube(3) == 27
```

### `cached_property` — per-instance lazy compute
A descriptor that computes a value on first access and stores it in the instance's `__dict__`. On subsequent access, `__dict__` lookup short-circuits the descriptor (non-data descriptor — instance dict wins).

```python
class Circle:
    def __init__(self, radius):
        self.radius = radius

    @cached_property
    def area(self):
        import math
        return math.pi * self.radius ** 2
```

**Limitation**: doesn't work on classes with `__slots__` (no `__dict__`). Not thread-safe by default (Python 3.12 added a lock parameter).

### `reduce` — left fold
`functools.reduce(func, iterable[, initializer])` applies `func(acc, item)` cumulatively. The functional equivalent of a for-loop accumulator. Interviewers sometimes ask to implement `sum`, `max`, or `all` with `reduce`.

```python
from functools import reduce
import operator

product = reduce(operator.mul, [1, 2, 3, 4, 5], 1)  # 120
```

### `singledispatch` — function overloading by type
Registers different implementations for different argument types:
```python
@singledispatch
def serialize(obj):
    raise TypeError(f"No serializer for {type(obj)}")

@serialize.register(int)
def _(obj): return str(obj)

@serialize.register(list)
def _(obj): return "[" + ", ".join(serialize(x) for x in obj) + "]"
```

## 💻 Code Example

```python
from functools import lru_cache, partial, cached_property, reduce
import operator
import time

@lru_cache(maxsize=256)
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# partial for route handler factories
def make_response(status_code, content_type, body):
    return {"status": status_code, "content_type": content_type, "body": body}

json_ok    = partial(make_response, 200, "application/json")
html_ok    = partial(make_response, 200, "text/html")
not_found  = partial(make_response, 404, "application/json")

# cached_property for expensive computation
class DataSet:
    def __init__(self, values):
        self.values = values

    @cached_property
    def statistics(self):
        print("  (computing statistics...)")
        n = len(self.values)
        mean = sum(self.values) / n
        variance = sum((x - mean) ** 2 for x in self.values) / n
        return {"mean": mean, "variance": variance, "n": n}
```

## ⚠️ Common Mistakes & Interview Traps

1. **`lru_cache` on instance methods leaks memory**: `@lru_cache` on a method caches `self` as part of the key. The cache holds strong references to `self` — old instances are never freed. Use `@cached_property` instead for per-instance caching, or `methodtools.lru_cache` (third-party).

2. **`lru_cache` with unhashable args**: `lru_cache()(func)([1,2,3])` raises `TypeError: unhashable type: 'list'`. Wrap lists in tuples before calling.

3. **`cached_property` with `__slots__`**: Requires `__dict__` to store the cached value. Slots classes have no `__dict__` → `AttributeError`.

4. **`partial` vs lambda**: `partial(f, x)` preserves `f.__name__` (partially) and is picklable. `lambda: f(x)` is not picklable (no stable `__qualname__`).

5. **`reduce` with empty iterable and no initializer**: `reduce(op, [])` raises `TypeError`. Always pass an initializer for operations over potentially empty sequences.

## 🔗 Related Concepts
- `python_core/009_decorator_internals` — `lru_cache` is a decorator with arguments
- `python_core/003_descriptors` — `cached_property` is a non-data descriptor
- `python_core/011_call_callable` — `partial` is a callable class

## 📚 Go Deeper
- CPython source: `Modules/_functoolsmodule.c` — LRU cache C implementation
- `methodtools` — third-party library fixing `lru_cache` on instance methods
