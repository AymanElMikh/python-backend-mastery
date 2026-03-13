"""
Demo: functools Deep Dive — lru_cache, partial, cached_property, reduce
Run:  python demo.py
"""

from functools import lru_cache, partial, cached_property, reduce, singledispatch
import operator
import time
import sys

# ── Section 1: lru_cache — internals and cache_info ──────────────────────────
@lru_cache(maxsize=64)
def fibonacci(n: int) -> int:
    """Recursive fib — only works because lru_cache prevents exponential blowup."""
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


call_count = 0

@lru_cache(maxsize=4)  # tiny cache to demonstrate LRU eviction
def tracked_compute(n):
    global call_count
    call_count += 1
    return n * n


# ── Section 2: lru_cache on methods — the memory leak ────────────────────────
class DataProcessor:
    def __init__(self, name):
        self.name = name

    @lru_cache(maxsize=None)  # BAD: caches 'self' — prevents GC!
    def process(self, value):
        return f"{self.name}:{value}"


# ── Section 3: partial — partial application ──────────────────────────────────
def make_response(status: int, content_type: str, body: str) -> dict:
    return {"status": status, "content_type": content_type, "body": body}

json_200   = partial(make_response, 200, "application/json")
html_200   = partial(make_response, 200, "text/html")
json_404   = partial(make_response, 404, "application/json")
json_500   = partial(make_response, 500, "application/json")


# ── Section 4: cached_property — per-instance lazy compute ───────────────────
class DataSet:
    def __init__(self, name, values):
        self.name = name
        self.values = values

    @cached_property
    def stats(self):
        print(f"    (computing stats for {self.name!r}...)")
        n = len(self.values)
        mean = sum(self.values) / n
        variance = sum((x - mean) ** 2 for x in self.values) / n
        return {"n": n, "mean": round(mean, 4), "variance": round(variance, 4)}


# ── Section 5: reduce — left fold ────────────────────────────────────────────
def show_reduce():
    nums = [1, 2, 3, 4, 5]

    product = reduce(operator.mul, nums, 1)
    total   = reduce(operator.add, nums, 0)

    # Build a pipeline of transforms using reduce
    transforms = [str.strip, str.lower, lambda s: s.replace(" ", "_")]
    pipeline = lambda s: reduce(lambda v, f: f(v), transforms, s)

    return product, total, pipeline("  Hello World  ")


# ── Section 6: singledispatch — type-based overloading ───────────────────────
@singledispatch
def serialize(obj) -> str:
    raise TypeError(f"No serializer for {type(obj).__name__}")

@serialize.register(int)
@serialize.register(float)
def _(obj) -> str:
    return str(obj)

@serialize.register(str)
def _(obj) -> str:
    return f'"{obj}"'

@serialize.register(list)
def _(obj) -> str:
    return "[" + ", ".join(serialize(x) for x in obj) + "]"

@serialize.register(dict)
def _(obj) -> str:
    pairs = ", ".join(f"{serialize(k)}: {serialize(v)}" for k, v in obj.items())
    return "{" + pairs + "}"


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: functools Deep Dive")
    print("=" * 55)

    # Section 1
    print("\n[1] lru_cache — cache_info and LRU eviction:")
    result = fibonacci(30)
    info = fibonacci.cache_info()
    print(f"  fibonacci(30) = {result}")
    print(f"  cache_info: hits={info.hits}, misses={info.misses}, size={info.currsize}")

    # Demonstrate LRU eviction (maxsize=4)
    global call_count
    call_count = 0
    for n in [1, 2, 3, 4, 1, 2, 5]:  # 5 evicts something
        tracked_compute(n)
    info2 = tracked_compute.cache_info()
    print(f"  Tiny cache (maxsize=4): hits={info2.hits}, misses={info2.misses}, actual_calls={call_count}")
    print(f"  (only {call_count} actual computations for 7 calls — caching works)")

    # Section 2
    print("\n[2] lru_cache on methods — memory leak risk:")
    dp = DataProcessor("proc")
    dp.process("input")
    dp.process("input")  # cached
    # dp is now referenced by the lru_cache — GC won't collect it!
    print(f"  DataProcessor.process.cache_info(): {DataProcessor.process.cache_info()}")
    print("  WARNING: 'self' (dp) is kept alive by the cache — memory leak pattern")
    print("  FIX: use @cached_property or per-instance caching instead")

    # Section 3
    print("\n[3] partial — pre-filled callables:")
    print(f"  json_200('{{}}'): {json_200('{}')}")
    print(f"  json_404('Not found'): {json_404('Not found')}")
    print(f"  partial.func: {json_200.func.__name__!r}")
    print(f"  partial.args: {json_200.args}")
    print(f"  partial.keywords: {json_200.keywords}")

    # Section 4
    print("\n[4] cached_property — computes once, stores in __dict__:")
    ds = DataSet("sample", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    print(f"  First access:  {ds.stats}")
    print(f"  Second access: {ds.stats}  (no recompute)")
    print(f"  Stored in __dict__: {'stats' in ds.__dict__}")

    # Section 5
    print("\n[5] reduce — left fold:")
    product, total, cleaned = show_reduce()
    print(f"  reduce(mul, [1..5]) = {product}")
    print(f"  reduce(add, [1..5]) = {total}")
    print(f"  pipeline('  Hello World  ') = {cleaned!r}")

    # Section 6
    print("\n[6] singledispatch — type-based overloading:")
    data = {"name": "Alice", "scores": [95, 87, 92], "age": 30}
    print(f"  serialize(42) = {serialize(42)}")
    print(f"  serialize('hi') = {serialize('hi')}")
    print(f"  serialize([1,2,3]) = {serialize([1, 2, 3])}")
    print(f"  serialize(data) = {serialize(data)}")

    print("\n" + "=" * 55)
