"""
Demo: __call__ & the Callable Protocol
Run:  python demo.py
"""

import functools
import time

# ── Section 1: callable() checks the type, not the instance ───────────────────
class HasCall:
    def __call__(self, x):
        return x * 2

def show_callable_lookup():
    obj = HasCall()
    print(f"  callable(HasCall instance): {callable(obj)}")

    # Instance-dict __call__ does NOT make an object callable
    plain = object()
    plain_dict_hack = type('Hack', (), {})()
    plain_dict_hack.__dict__['__call__'] = lambda: 42
    print(f"  Instance-dict __call__ trick: callable={callable(plain_dict_hack)}")
    print("  (Python looks at type(obj).__call__, not obj.__dict__['__call__'])")


# ── Section 2: Stateful callable — Memoize ────────────────────────────────────
class Memoize:
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

    def stats(self):
        total = self.hits + self.misses
        ratio = self.hits / total if total else 0
        return f"hits={self.hits}, misses={self.misses}, ratio={ratio:.0%}"


@Memoize
def fib(n):
    """Nth Fibonacci number."""
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


# ── Section 3: WSGI-style middleware chain ─────────────────────────────────────
def base_app(request):
    return {"status": 200, "body": f"Hello from {request['path']}"}

class LogMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, request):
        print(f"    LogMiddleware → {request['method']} {request['path']}")
        response = self.app(request)
        print(f"    LogMiddleware ← {response['status']}")
        return response

class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, request):
        if not request.get("token"):
            return {"status": 401, "body": "Unauthorized"}
        return self.app(request)


# ── Section 4: __call__ vs closure — state introspection ──────────────────────
def make_counter_closure(start=0):
    count = start
    def increment(by=1):
        nonlocal count
        count += by
        return count
    return increment

class Counter:
    def __init__(self, start=0):
        self.count = start

    def __call__(self, by=1):
        self.count += by
        return self.count


# ── Section 5: type.__call__ orchestrates __new__ + __init__ ──────────────────
class TracedMeta(type):
    def __call__(cls, *args, **kwargs):
        print(f"    type.__call__ on {cls.__name__} → __new__ then __init__")
        instance = cls.__new__(cls, *args, **kwargs)
        if isinstance(instance, cls):
            instance.__init__(*args, **kwargs)
        return instance

class Traced(metaclass=TracedMeta):
    def __init__(self, value):
        self.value = value


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: __call__ & the Callable Protocol")
    print("=" * 55)

    # Section 1
    print("\n[1] callable() — type-level lookup:")
    show_callable_lookup()

    # Section 2
    print("\n[2] Memoize — stateful callable with inspectable cache:")
    for n in [10, 20, 10, 30, 20]:
        fib(n)
    print(f"  fib(35) = {fib(35)}")
    print(f"  Cache stats: {fib.stats()}")
    print(f"  Cache keys visible: {sorted(fib.cache.keys())[:5]} ...")
    fib.cache_clear()
    print(f"  After cache_clear: {fib.stats()}")
    print(f"  fib.__name__ = {fib.__name__!r}  (functools.update_wrapper preserved it)")

    # Section 3
    print("\n[3] Middleware chain (callable composition):")
    app = LogMiddleware(AuthMiddleware(base_app))
    print("  Request without token:")
    r = app({"method": "GET", "path": "/api/users"})
    print(f"  Response: {r}")
    print("  Request with token:")
    r = app({"method": "GET", "path": "/api/users", "token": "abc"})
    print(f"  Response: {r}")

    # Section 4
    print("\n[4] __call__ class vs closure — state introspection:")
    closure_counter = make_counter_closure(0)
    class_counter = Counter(0)

    for _ in range(3):
        closure_counter()
        class_counter()

    print(f"  Closure: current count = ??? (hidden in nonlocal)")
    print(f"  Class:   current count = {class_counter.count}  (visible, resettable)")
    class_counter.count = 0
    print(f"  Class:   after reset = {class_counter.count}")

    # Section 5
    print("\n[5] type.__call__ — metaclass orchestrates instantiation:")
    t = Traced(42)
    print(f"  Traced(42).value = {t.value}")

    print("\n" + "=" * 55)
