"""
Demo: __getattr__ vs __getattribute__
Run:  python demo.py
"""

# ── Section 1: __getattr__ — fallback only ────────────────────────────────────
class DynamicRow:
    """DB row where column names are dynamic — __getattr__ as fallback."""

    def __init__(self, data: dict):
        self._data = data  # goes to __dict__ normally

    def __getattr__(self, name):
        # ONLY called when normal lookup fails
        print(f"    __getattr__ called for {name!r}")
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"No column {name!r}")


# ── Section 2: __getattribute__ — intercepts everything ──────────────────────
class AccessLogger:
    """Log every access to non-private attributes."""

    def __init__(self, name, age):
        # MUST bypass our __getattribute__ when writing
        object.__setattr__(self, '_log', [])
        object.__setattr__(self, 'name', name)
        object.__setattr__(self, 'age', age)

    def __getattribute__(self, attr_name):
        if not attr_name.startswith('_'):
            # Safe: use object.__getattribute__ to avoid recursion
            log = object.__getattribute__(self, '_log')
            log.append(attr_name)
        return object.__getattribute__(self, attr_name)

    def get_log(self):
        return object.__getattribute__(self, '_log')


# ── Section 3: Proxy pattern — combining both ────────────────────────────────
class ReadOnlyProxy:
    """Forwards attribute reads; blocks writes."""

    def __init__(self, target):
        # Must use object.__setattr__ — we're about to define __setattr__
        object.__setattr__(self, '_target', target)

    def __getattr__(self, name):
        # Forwards unknown attrs to target
        return getattr(object.__getattribute__(self, '_target'), name)

    def __setattr__(self, name, value):
        raise AttributeError(f"ReadOnlyProxy: cannot set {name!r}")


# ── Section 4: The infinite recursion trap ────────────────────────────────────
class InfiniteRecursionTrap:
    def __getattribute__(self, name):
        # WRONG: accessing self.anything calls __getattribute__ again
        # self._logger  # ← would recurse
        # RIGHT:
        val = object.__getattribute__(self, name)
        return val


# ── Section 5: __getattr__ not called for existing attrs ─────────────────────
class ShowFallback:
    existing = "I'm in the class dict"

    def __getattr__(self, name):
        print(f"    __getattr__ fallback: {name!r}")
        return f"dynamic:{name}"


# ── Section 6: __setattr__ intercepts __init__ too ───────────────────────────
class TypeChecked:
    _types = {'x': int, 'y': float}

    def __init__(self, x, y):
        self.x = x  # goes through __setattr__!
        self.y = y

    def __setattr__(self, name, value):
        expected = self._types.get(name)
        if expected and not isinstance(value, expected):
            raise TypeError(f"{name}: expected {expected.__name__}, got {type(value).__name__}")
        object.__setattr__(self, name, value)  # safe base write


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: __getattr__ vs __getattribute__")
    print("=" * 55)

    # Section 1
    print("\n[1] __getattr__ — fallback for missing attrs:")
    row = DynamicRow({"user_id": 42, "email": "alice@example.com"})
    print(f"  row._data access (in __dict__, no fallback): {row._data}")
    print(f"  row.user_id  → {row.user_id}")
    print(f"  row.email    → {row.email}")
    try:
        _ = row.missing
    except AttributeError as e:
        print(f"  row.missing  → AttributeError: {e}")

    # Section 2
    print("\n[2] __getattribute__ — every access logged:")
    user = AccessLogger("Alice", 30)
    _ = user.name
    _ = user.age
    _ = user.name  # second access
    print(f"  user.name = {user.name}")
    print(f"  Access log: {user.get_log()}")

    # Section 3
    print("\n[3] ReadOnlyProxy — forward reads, block writes:")
    class Config:
        host = "localhost"
        port = 5432

    proxy = ReadOnlyProxy(Config())
    print(f"  proxy.host = {proxy.host}")
    print(f"  proxy.port = {proxy.port}")
    try:
        proxy.host = "prod.db"
    except AttributeError as e:
        print(f"  proxy.host = 'x' → AttributeError: {e}")

    # Section 4
    print("\n[4] Infinite recursion trap — safe pattern:")
    safe = InfiniteRecursionTrap()
    object.__setattr__(safe, 'value', 99)
    print(f"  safe.value = {safe.value}  (accessed safely via object.__getattribute__)")

    # Section 5
    print("\n[5] __getattr__ skipped for existing attrs:")
    sf = ShowFallback()
    print(f"  sf.existing = {sf.existing!r}  (no __getattr__ call)")
    print(f"  sf.dynamic  = {sf.dynamic!r}   (__getattr__ called)")

    # Section 6
    print("\n[6] __setattr__ intercepts __init__:")
    p = TypeChecked(x=10, y=3.14)
    print(f"  TypeChecked(10, 3.14) → x={p.x}, y={p.y}")
    try:
        p.x = "hello"
    except TypeError as e:
        print(f"  p.x = 'hello' → TypeError: {e}")

    print("\n" + "=" * 55)
