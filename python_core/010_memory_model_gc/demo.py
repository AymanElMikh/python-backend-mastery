"""
Demo: Python Memory Model & Garbage Collection
Run:  python demo.py
"""

import gc
import sys
import weakref
import tracemalloc

# ── Section 1: Reference counting ─────────────────────────────────────────────
def show_refcounts():
    x = [1, 2, 3]
    print(f"  After x=[1,2,3]:         refcount={sys.getrefcount(x)} (x + getrefcount temp)")
    y = x
    print(f"  After y=x:               refcount={sys.getrefcount(x)} (x, y + temp)")
    z = x
    print(f"  After z=x:               refcount={sys.getrefcount(x)} (x, y, z + temp)")
    del y
    print(f"  After del y:             refcount={sys.getrefcount(x)}")
    lst = [x, x, x]  # 3 more refs
    print(f"  After lst=[x,x,x]:       refcount={sys.getrefcount(x)}")
    del lst
    del z
    print(f"  After del lst, z:        refcount={sys.getrefcount(x)}")


# ── Section 2: Cyclic reference — refcounting fails ──────────────────────────
class Node:
    def __init__(self, name):
        self.name = name
        self.ref = None

    def __repr__(self):
        return f"Node({self.name!r})"


def demonstrate_cycle():
    gc.disable()  # turn off cyclic GC to show the leak
    gc.collect()  # clean slate

    before = len(gc.get_objects())

    a = Node("a")
    b = Node("b")
    a.ref = b   # a → b
    b.ref = a   # b → a  (cycle)

    # Both refcounts are now 2 (a has: 'a' var + b.ref; b has: 'b' var + a.ref)
    print(f"  refcount(a) before del: {sys.getrefcount(a)}")

    del a, b  # drops to 1 each — NOT 0, cycle prevents freeing

    after_del = len(gc.get_objects())
    leaked = after_del - before
    print(f"  Objects after del (GC disabled): +{leaked} (nodes still alive in cycle)")

    gc.enable()
    collected = gc.collect()
    after_gc = len(gc.get_objects())
    print(f"  gc.collect() freed: {collected} objects")
    print(f"  Objects after GC:   {after_gc - before} delta (back to baseline)")


# ── Section 3: __del__ and finalization ───────────────────────────────────────
class WithFinalizer:
    def __init__(self, name):
        self.name = name

    def __del__(self):
        print(f"  __del__ called for {self.name!r}")


def demonstrate_del():
    print("  Creating obj1 (no cycle):")
    obj1 = WithFinalizer("obj1")
    del obj1  # immediate — refcount hits 0

    print("  Creating cycle with __del__:")
    c1 = WithFinalizer("cycle-1")
    c2 = WithFinalizer("cycle-2")
    c1.other = c2
    c2.other = c1
    del c1, c2
    print("  Before gc.collect()...")
    gc.collect()  # PEP 442: __del__ now called even for cyclic garbage (Python 3.4+)
    print("  (both __del__ were called — PEP 442 fix)")


# ── Section 4: Weak references ────────────────────────────────────────────────
class Session:
    def __init__(self, session_id):
        self.id = session_id

def demonstrate_weakref():
    sessions = weakref.WeakValueDictionary()

    s1 = Session("abc123")
    s2 = Session("def456")
    sessions["abc123"] = s1
    sessions["def456"] = s2

    print(f"  Active sessions: {list(sessions.keys())}")

    del s1  # s1's refcount → 0, immediately freed, weak ref becomes dead
    print(f"  After del s1: sessions = {list(sessions.keys())}  (s1 auto-removed)")

    del s2
    print(f"  After del s2: sessions = {list(sessions.keys())}  (all gone)")


# ── Section 5: tracemalloc — find allocation hotspots ────────────────────────
def demonstrate_tracemalloc():
    tracemalloc.start()

    data = {i: list(range(100)) for i in range(1000)}

    snapshot = tracemalloc.take_snapshot()
    stats = snapshot.statistics("lineno")

    print(f"  Top allocation in this demo:")
    for stat in stats[:2]:
        print(f"    {stat}")

    tracemalloc.stop()
    del data


# ── Section 6: Frame retention trap ──────────────────────────────────────────
def frame_retention_trap():
    import sys

    def inner():
        big_local = list(range(10_000))  # 10k items in frame locals
        raise ValueError("boom")

    try:
        inner()
    except ValueError:
        exc_info = sys.exc_info()  # TRAPS THE FRAME — big_local stays alive!
        tb = exc_info[2]
        frame = tb.tb_frame
        print(f"  Frame locals kept alive: 'big_local' in frame.f_locals = {'big_local' in frame.f_locals}")
        print("  Always del exc_info / tb after use, or use 'raise ... from None'")


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: Python Memory Model & Garbage Collection")
    print("=" * 55)

    print("\n[1] Reference counting:")
    show_refcounts()

    print("\n[2] Cyclic reference — refcounting fails without GC:")
    demonstrate_cycle()

    print("\n[3] __del__ and cycle finalization (PEP 442):")
    demonstrate_del()

    print("\n[4] Weak references — non-owning cache:")
    demonstrate_weakref()

    print("\n[5] tracemalloc — allocation profiling:")
    demonstrate_tracemalloc()

    print("\n[6] Frame retention via sys.exc_info():")
    frame_retention_trap()

    print("\n[7] GC generations:")
    print(f"  gc.get_count() = {gc.get_count()}  (gen0, gen1, gen2 allocation deltas)")
    print(f"  gc.get_threshold() = {gc.get_threshold()}  (thresholds to trigger collection)")

    print("\n" + "=" * 55)
