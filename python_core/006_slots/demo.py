"""
Demo: __slots__ & Memory Layout
Run:  python demo.py
"""

import sys
import tracemalloc

# ── Section 1: Memory comparison ───────────────────────────────────────────────
class Point:
    """Normal instance — carries __dict__."""
    def __init__(self, x, y):
        self.x = x
        self.y = y

class SlottedPoint:
    """Slotted instance — compact fixed layout."""
    __slots__ = ('x', 'y')

    def __init__(self, x, y):
        self.x = x
        self.y = y


# ── Section 2: Dynamic attribute restriction ───────────────────────────────────
class Config:
    __slots__ = ('host', 'port', 'debug')

    def __init__(self, host, port, debug=False):
        self.host = host
        self.port = port
        self.debug = debug


# ── Section 3: Inheritance trap — parent without slots ────────────────────────
class SlottedBase:
    __slots__ = ('x',)

class GetsDict(SlottedBase):
    """No __slots__ here → __dict__ is back! Slots only help for SlottedBase attrs."""
    pass

class FullySlotted(SlottedBase):
    """Extends slots — avoids __dict__ at this level."""
    __slots__ = ('y',)  # 'x' comes from SlottedBase


# ── Section 4: Mass allocation — real memory difference ───────────────────────
def measure_allocation(cls, n=100_000):
    tracemalloc.start()
    objects = [cls(i, i * 2) for i in range(n)]
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    del objects
    return peak


# ── Section 5: __weakref__ and pickling traps ─────────────────────────────────
import weakref
import pickle

class NoWeakref:
    __slots__ = ('x',)
    def __init__(self, x): self.x = x

class WithWeakref:
    __slots__ = ('x', '__weakref__')
    def __init__(self, x): self.x = x

class Picklable:
    __slots__ = ('x', 'y')
    def __init__(self, x, y): self.x = x; self.y = y
    def __getstate__(self): return {'x': self.x, 'y': self.y}
    def __setstate__(self, state): self.x = state['x']; self.y = state['y']


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: __slots__ & Memory Layout")
    print("=" * 55)

    # Section 1
    print("\n[1] Instance size comparison:")
    p  = Point(1, 2)
    sp = SlottedPoint(1, 2)
    print(f"  Point (normal):        sys.getsizeof = {sys.getsizeof(p)} bytes")
    print(f"  Point.__dict__:        sys.getsizeof = {sys.getsizeof(p.__dict__)} bytes")
    print(f"  Total with __dict__:   ~{sys.getsizeof(p) + sys.getsizeof(p.__dict__)} bytes")
    print(f"  SlottedPoint:          sys.getsizeof = {sys.getsizeof(sp)} bytes (no __dict__)")
    print(f"  has __dict__: Point={hasattr(p, '__dict__')}, SlottedPoint={hasattr(sp, '__dict__')}")

    # Section 2
    print("\n[2] Dynamic attribute restriction:")
    cfg = Config("localhost", 8080)
    print(f"  cfg.host = {cfg.host!r}, cfg.port = {cfg.port}")
    try:
        cfg.timeout = 30  # not in __slots__
    except AttributeError as e:
        print(f"  AttributeError: {e}")

    # Section 3
    print("\n[3] Inheritance trap:")
    gd = GetsDict()
    fs = FullySlotted()
    print(f"  GetsDict has __dict__:    {hasattr(gd, '__dict__')}  (slots lost in subclass)")
    print(f"  FullySlotted has __dict__: {hasattr(fs, '__dict__')} (properly extended)")
    print(f"  FullySlotted slots: {FullySlotted.__slots__}, inherits: {SlottedBase.__slots__}")

    # Section 4
    print("\n[4] Real memory impact (100,000 instances):")
    normal_peak  = measure_allocation(Point, 100_000)
    slotted_peak = measure_allocation(SlottedPoint, 100_000)
    print(f"  Point peak memory:        {normal_peak / 1024 / 1024:.1f} MB")
    print(f"  SlottedPoint peak memory: {slotted_peak / 1024 / 1024:.1f} MB")
    savings = (1 - slotted_peak / normal_peak) * 100
    print(f"  Memory reduction:         ~{savings:.0f}%")

    # Section 5
    print("\n[5] weakref and pickle traps:")
    nw = NoWeakref(42)
    try:
        ref = weakref.ref(nw)
    except TypeError as e:
        print(f"  weakref(NoWeakref) → TypeError: {e}")

    ww = WithWeakref(42)
    ref = weakref.ref(ww)
    print(f"  weakref(WithWeakref) → {ref()} ✓")

    obj = Picklable(10, 20)
    data = pickle.dumps(obj)
    restored = pickle.loads(data)
    print(f"  Pickle round-trip: x={restored.x}, y={restored.y} ✓")

    try:
        plain = SlottedPoint(1, 2)
        pickle.dumps(plain)
    except Exception as e:
        print(f"  pickle(SlottedPoint) → {type(e).__name__}: {e}")

    print("\n" + "=" * 55)
