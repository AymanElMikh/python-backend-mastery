"""
Demo: Decorator Internals & functools.wraps
Run:  python demo.py
"""

import functools
import time
import inspect

# ── Section 1: What a decorator IS (desugared) ───────────────────────────────
def simple_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"    Before {func.__name__}")
        result = func(*args, **kwargs)
        print(f"    After {func.__name__}")
        return result
    return wrapper


# ── Section 2: The wraps trap — what breaks without it ───────────────────────
def bad_decorator(func):
    def wrapper(*args, **kwargs):  # no @functools.wraps!
        return func(*args, **kwargs)
    return wrapper

def good_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


# ── Section 3: Decorator with arguments — 3 layers ───────────────────────────
def retry(times=3, delay=0.0, exceptions=(Exception,)):
    """Factory → decorator → wrapper."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    print(f"    Attempt {attempt}/{times} failed: {e}")
            raise last_exc
        return wrapper
    return decorator


# ── Section 4: Stacking decorators ───────────────────────────────────────────
def bold(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return f"**{func(*args, **kwargs)}**"
    return wrapper

def upper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs).upper()
    return wrapper


# ── Section 5: Class-based decorator ─────────────────────────────────────────
class CountCalls:
    """Stateful decorator — tracks call count."""
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        return self.func(*args, **kwargs)

    def reset(self):
        self.calls = 0


# ── Section 6: inspect.unwrap follows __wrapped__ chain ──────────────────────
def wrap_twice(func):
    @functools.wraps(func)
    def w1(*a, **kw): return func(*a, **kw)
    @functools.wraps(w1)
    def w2(*a, **kw): return w1(*a, **kw)
    return w2


# ── Demo functions ────────────────────────────────────────────────────────────
@simple_decorator
def greet(name):
    """Greet a person."""
    return f"Hello, {name}!"


@bad_decorator
def original_bad():
    """I am original_bad."""
    pass

@good_decorator
def original_good():
    """I am original_good."""
    pass


attempt_count = 0
@retry(times=3, exceptions=(ValueError,))
def flaky_function():
    """Fails twice then succeeds."""
    global attempt_count
    attempt_count += 1
    if attempt_count < 3:
        raise ValueError(f"not ready (attempt {attempt_count})")
    return "success!"


@bold
@upper
def title():
    return "hello world"


@CountCalls
def add(a, b):
    return a + b


@wrap_twice
def original():
    """The original function."""
    return 42


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: Decorator Internals & functools.wraps")
    print("=" * 55)

    # Section 1
    print("\n[1] Basic decorator — desugared:")
    result = greet("Alice")
    print(f"    greet('Alice') = {result!r}")

    # Section 2
    print("\n[2] The wraps trap:")
    print(f"  bad_decorator:  __name__={original_bad.__name__!r}, __doc__={original_bad.__doc__!r}")
    print(f"  good_decorator: __name__={original_good.__name__!r}, __doc__={original_good.__doc__!r}")
    print(f"  __wrapped__ present on good: {'__wrapped__' in dir(original_good)}")

    # Section 3
    print("\n[3] @retry(times=3) — argument-accepting decorator:")
    attempt_count = 0
    result = flaky_function()
    print(f"    Final result: {result!r}")
    print(f"    Name preserved: {flaky_function.__name__!r}")

    # Section 4
    print("\n[4] Stacking @bold @upper — order matters:")
    print(f"    title() = {title()!r}")
    print("    Order: upper runs first (inner), bold wraps result (outer)")
    print("    i.e., bold(upper(title))() → upper applies first at call time")

    # Section 5
    print("\n[5] Class-based decorator — stateful call counting:")
    print(f"    add(1,2) = {add(1, 2)}, add(3,4) = {add(3,4)}, add(5,6) = {add(5,6)}")
    print(f"    add.calls = {add.calls}")
    print(f"    add.__name__ = {add.__name__!r}  (update_wrapper preserved it)")

    # Section 6
    print("\n[6] inspect.unwrap() follows __wrapped__ chain:")
    print(f"    original.__name__ = {original.__name__!r}")
    unwrapped = inspect.unwrap(original)
    print(f"    inspect.unwrap(original).__name__ = {unwrapped.__name__!r}")
    print(f"    They are same: {original.__wrapped__.__wrapped__ is unwrapped}")

    print("\n" + "=" * 55)
