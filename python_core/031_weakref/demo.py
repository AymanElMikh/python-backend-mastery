"""
Demo: Weak References — weakref Module
Run:  python demo.py
"""
import gc
import weakref

# ── Section 1: Basic weak ref lifecycle ──────────────────────────────────────
class Node:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"Node({self.name!r})"

strong = Node("alpha")
weak   = weakref.ref(strong, lambda r: print(f"  [callback] ref died: {r}"))

print("Alive?", weak() is not None, "→", weak())   # Node('alpha')
del strong
gc.collect()
print("After del:", weak())   # None

# ── Section 2: WeakValueDictionary as an auto-evicting cache ────────────────
cache: weakref.WeakValueDictionary = weakref.WeakValueDictionary()

def make_big(key):
    obj = Node(key)
    cache[key] = obj
    return obj  # caller holds strong ref

a = make_big("x")
b = make_big("y")
print("\nCache keys (alive):", list(cache.keys()))  # ['x', 'y']
del a
gc.collect()
print("After del a      :", list(cache.keys()))     # ['y']
del b
gc.collect()
print("After del b      :", list(cache.keys()))     # []

# ── Section 3: WeakMethod — the bound-method trap ───────────────────────────
class Listener:
    def on_event(self, data):
        print(f"  Listener.on_event({data!r})")

l = Listener()

# BAD: dies immediately
raw = weakref.ref(l.on_event)
print("\nraw ref alive?", raw() is not None)   # False — already dead!

# GOOD: WeakMethod keeps ref alive while `l` is alive
wm = weakref.WeakMethod(l.on_event)
print("WeakMethod alive?", wm() is not None)  # True
wm()("hello")                                 # calls the method

del l
gc.collect()
print("After del l:", wm())   # None

# ── Section 4: __slots__ + __weakref__ ──────────────────────────────────────
class NoWeak:
    __slots__ = ("x",)            # forgot __weakref__

class WithWeak:
    __slots__ = ("x", "__weakref__")

try:
    weakref.ref(NoWeak())
except TypeError as e:
    print(f"\nNoWeak: {e}")

ref = weakref.ref(WithWeak())
print("WithWeak ref:", ref())

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("DEMO: Weak References")
    print("=" * 50)
    print("All sections executed above — review output for lifecycle events.")
