"""
Demo: NamedTuple vs dataclass — Choosing the Right Data Container
Run:  python demo.py
"""
import sys
from typing import NamedTuple
from dataclasses import dataclass, field, FrozenInstanceError

# ── Section 1: NamedTuple basics ──────────────────────────────────────────────
print("=" * 50)
print("Section 1: NamedTuple")
print("=" * 50)

class Point(NamedTuple):
    x: float
    y: float = 0.0
    label: str = ""

p = Point(3.0, 4.0, "A")
print("Point      :", p)
print("p.x        :", p.x, "  p[0]:", p[0])   # tuple AND named access
print("Unpack     :", end=" "); x, y, lbl = p; print(x, y, lbl)
print("Hash       :", hash(p))                  # hashable — usable as dict key
print("_asdict()  :", p._asdict())
print("_replace() :", p._replace(x=99.0))       # new tuple, old unchanged
print("isinstance tuple:", isinstance(p, tuple))

# ── Section 2: dataclass basics ──────────────────────────────────────────────
print("\n" + "=" * 50)
print("Section 2: dataclass")
print("=" * 50)

@dataclass
class Config:
    host: str
    port: int = 8080
    tags: list = field(default_factory=list)   # MUST use factory for mutables

c1 = Config("localhost")
c2 = Config("localhost")
c1.tags.append("web")
print("c1:", c1)
print("c2:", c2)          # c2.tags is empty — independent defaults
print("c1 == c2:", c1 == c2)   # False — tags differ

# ── Section 3: frozen dataclass ───────────────────────────────────────────────
print("\n" + "=" * 50)
print("Section 3: frozen=True")
print("=" * 50)

@dataclass(frozen=True)
class ImmutablePoint:
    x: float
    y: float

ip = ImmutablePoint(1.0, 2.0)
print("Hash of frozen:", hash(ip))   # hashable

try:
    ip.x = 99
except FrozenInstanceError as e:
    print("FrozenInstanceError:", e)

# frozen ≠ deep immutable trap
@dataclass(frozen=True)
class Trap:
    items: list = field(default_factory=list)

t = Trap()
t.items.append("sneaky")   # list inside is still mutable!
print("Frozen but list mutated:", t.items)

# ── Section 4: Memory comparison ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("Section 4: Memory sizes")
print("=" * 50)

@dataclass
class MutPoint:
    x: float
    y: float

nt_point  = Point(1.0, 2.0)
dc_point  = MutPoint(1.0, 2.0)
im_point  = ImmutablePoint(1.0, 2.0)

print(f"NamedTuple  : {sys.getsizeof(nt_point)} bytes")
print(f"dataclass   : {sys.getsizeof(dc_point)} bytes")
print(f"frozen dc   : {sys.getsizeof(im_point)} bytes")

# ── Section 5: Mutable default trap ──────────────────────────────────────────
print("\n" + "=" * 50)
print("Section 5: Mutable default trap")
print("=" * 50)

try:
    @dataclass
    class BrokenConfig:
        tags: list = []   # should raise ValueError
except ValueError as e:
    print("ValueError:", e)

if __name__ == "__main__":
    print("\nAll sections complete.")
