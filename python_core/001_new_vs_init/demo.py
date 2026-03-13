"""
Demo: __new__ vs __init__
Run:  python demo.py
"""

# ── Section 1: Basic two-phase protocol ───────────────────────────────────────
class Verbose:
    def __new__(cls, value):
        print(f"  __new__  called  → allocating instance of {cls.__name__}")
        instance = super().__new__(cls)
        return instance

    def __init__(self, value):
        print(f"  __init__ called  → setting self.value = {value!r}")
        self.value = value


# ── Section 2: Immutable subclass — must use __new__ ──────────────────────────
class BoundedInt(int):
    """An int clamped to [0, 100]. __init__ is too late for immutable types."""
    def __new__(cls, value):
        clamped = max(0, min(100, value))
        return super().__new__(cls, clamped)


class UpperStr(str):
    """A str that is always uppercase. The value must be set in __new__."""
    def __new__(cls, value):
        return super().__new__(cls, value.upper())


# ── Section 3: Singleton — the __init__ re-run trap ───────────────────────────
class SingletonBad:
    """Naive singleton — __init__ still resets state on every call."""
    _instance = None

    def __new__(cls, value):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, value):
        self.value = value  # BUG: runs every time, resetting value


class SingletonFixed:
    """Fixed singleton — uses _initialized flag to protect __init__."""
    _instance = None

    def __new__(cls, value):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, value):
        if not self._initialized:
            self.value = value
            self._initialized = True


# ── Section 4: __new__ returning wrong type skips __init__ ────────────────────
class WrongReturn:
    def __new__(cls):
        return 42  # not an instance of cls → __init__ is skipped

    def __init__(self):
        print("  __init__ called")  # never reached


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: __new__ vs __init__")
    print("=" * 55)

    # Section 1
    print("\n[1] Two-phase protocol:")
    obj = Verbose("hello")
    print(f"    obj.value = {obj.value!r}")

    # Section 2
    print("\n[2] Immutable subclass — BoundedInt and UpperStr:")
    bi = BoundedInt(150)
    print(f"    BoundedInt(150) → {bi}  (clamped to 100)")
    bi2 = BoundedInt(-5)
    print(f"    BoundedInt(-5)  → {bi2}  (clamped to 0)")
    us = UpperStr("hello world")
    print(f"    UpperStr('hello world') → {us!r}")

    # Section 3
    print("\n[3] Singleton __init__ re-run trap:")
    s1 = SingletonBad("first")
    s2 = SingletonBad("second")
    print(f"    s1 is s2 → {s1 is s2}  (same object)")
    print(f"    s1.value → {s1.value!r}  (WRONG: 'second' overwrote 'first')")

    print()
    f1 = SingletonFixed("first")
    f2 = SingletonFixed("second")
    print(f"    f1 is f2 → {f1 is f2}  (same object)")
    print(f"    f1.value → {f1.value!r}  (CORRECT: 'first' preserved)")

    # Section 4
    print("\n[4] __new__ returning non-cls type skips __init__:")
    result = WrongReturn()
    print(f"    WrongReturn() returned: {result!r}  (int, not WrongReturn)")
    print(f"    isinstance(result, WrongReturn): {isinstance(result, WrongReturn)}")
    print("    → __init__ was never called")

    print("\n" + "=" * 55)
