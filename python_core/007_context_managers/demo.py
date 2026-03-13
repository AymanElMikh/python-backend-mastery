"""
Demo: Context Managers & contextlib
Run:  python demo.py
"""

import time
import contextlib
import sys

# ── Section 1: Class-based context manager ────────────────────────────────────
class Timer:
    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self._start
        if exc_type:
            print(f"    __exit__ called with exception: {exc_type.__name__}: {exc_val}")
        else:
            print(f"    __exit__ called normally — elapsed {self.elapsed*1000:.2f}ms")
        return False  # don't suppress exceptions


# ── Section 2: Exception suppression ─────────────────────────────────────────
class Suppress:
    """Suppress specific exception types."""
    def __init__(self, *exc_types):
        self.exc_types = exc_types
        self.suppressed = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, self.exc_types):
            self.suppressed = exc_val
            print(f"    Suppressed {exc_type.__name__}: {exc_val}")
            return True  # suppress!
        return False


# ── Section 3: Generator-based via @contextmanager ────────────────────────────
@contextlib.contextmanager
def managed_resource(name):
    print(f"    [{name}] __enter__ — acquiring")
    resource = {"name": name, "active": True}
    try:
        yield resource
        print(f"    [{name}] normal exit — releasing cleanly")
    except ValueError as e:
        print(f"    [{name}] ValueError caught — rolling back: {e}")
        resource["active"] = False
        # Not re-raising → suppresses ValueError
    finally:
        print(f"    [{name}] finally — always runs")
        resource["active"] = False


# ── Section 4: contextlib.ExitStack — dynamic resources ──────────────────────
def open_configs(names):
    """Open multiple StringIO 'files' dynamically."""
    import io
    with contextlib.ExitStack() as stack:
        streams = []
        for name in names:
            buf = io.StringIO(f"config:{name}")
            # Enter each context manager — all cleaned up on ExitStack exit
            streams.append(stack.enter_context(buf))
        contents = [s.read() for s in streams]
    # All streams are closed here
    return contents


# ── Section 5: contextlib.suppress and nullcontext ───────────────────────────
def demo_contextlib_utils():
    # suppress — ignore specific exceptions
    with contextlib.suppress(ZeroDivisionError):
        result = 1 / 0  # silently ignored
    print("    contextlib.suppress(ZeroDivisionError) — execution continues")

    # nullcontext — placeholder context manager (useful in conditional with-blocks)
    def get_lock(use_lock):
        import threading
        return threading.Lock() if use_lock else contextlib.nullcontext()

    with get_lock(False) as maybe_lock:
        print(f"    nullcontext as target: {maybe_lock!r}")


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: Context Managers & contextlib")
    print("=" * 55)

    # Section 1
    print("\n[1] Class-based Timer:")
    with Timer() as t:
        total = sum(range(100_000))
    print(f"    sum(range(100000)) = {total}, took {t.elapsed*1000:.2f}ms")

    print("\n[1b] Timer with exception inside with block:")
    try:
        with Timer() as t:
            raise RuntimeError("something broke")
    except RuntimeError:
        print(f"    Exception propagated after {t.elapsed*1000:.2f}ms")

    # Section 2
    print("\n[2] Custom Suppress context manager:")
    s = Suppress(KeyError, ValueError)
    with s:
        raise ValueError("bad value")
    print(f"    Suppressed exception stored: {s.suppressed!r}")
    print(f"    Execution continues normally after suppression")

    # Section 3
    print("\n[3] @contextmanager — normal exit:")
    with managed_resource("DB-txn") as r:
        print(f"    Inside with block: resource active={r['active']}")
    print(f"    After with: resource active={r['active']}")

    print("\n[3b] @contextmanager — exception suppressed inside generator:")
    with managed_resource("DB-txn-2") as r:
        raise ValueError("constraint violation")
    print(f"    ValueError was suppressed by the context manager")

    # Section 4
    print("\n[4] ExitStack — dynamic resource management:")
    results = open_configs(["app", "db", "cache"])
    print(f"    Read {len(results)} configs: {results}")

    # Section 5
    print("\n[5] contextlib utilities:")
    demo_contextlib_utils()

    print("\n" + "=" * 55)
