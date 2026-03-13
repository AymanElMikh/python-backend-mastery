"""
Demo: dataclasses Internals — field(), __post_init__, ClassVar
Run:  python demo.py
"""

from dataclasses import dataclass, field, fields, asdict, replace, KW_ONLY
from typing import ClassVar, InitVar

# ── Section 1: Mutable default trap ───────────────────────────────────────────
# @dataclass
# class Bad:
#     items: list = []  # raises ValueError at class definition time!

@dataclass
class Cart:
    items: list = field(default_factory=list)   # correct: new list per instance
    owner: str = "guest"

    def add(self, item):
        self.items.append(item)


# ── Section 2: __post_init__ — validation + derived fields ────────────────────
@dataclass
class Circle:
    radius: float
    # init=False: not passed to __init__, set by __post_init__
    area: float = field(init=False, repr=True)
    circumference: float = field(init=False, repr=False)

    def __post_init__(self):
        if self.radius < 0:
            raise ValueError(f"radius must be >= 0, got {self.radius}")
        import math
        self.area = math.pi * self.radius ** 2
        self.circumference = 2 * math.pi * self.radius


# ── Section 3: ClassVar and InitVar ───────────────────────────────────────────
@dataclass
class Tracked:
    count: ClassVar[int] = 0          # class-level — not an instance field

    name: str
    verbose: InitVar[bool] = False    # in __init__, not stored

    def __post_init__(self, verbose: bool):
        Tracked.count += 1
        if verbose:
            print(f"    Created Tracked({self.name!r}), total={Tracked.count}")


# ── Section 4: frozen=True — immutable + hashable ─────────────────────────────
@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"


# ── Section 5: field() metadata + repr/compare control ───────────────────────
@dataclass
class User:
    INSTANCE_COUNT: ClassVar[int] = 0

    id: int
    name: str
    password: str = field(repr=False, compare=False)  # hidden, excluded from eq
    email: str = field(default="", compare=True)

    def __post_init__(self):
        User.INSTANCE_COUNT += 1


# ── Section 6: dataclass utilities — asdict, replace, fields() ───────────────
@dataclass
class Config:
    host: str = "localhost"
    port: int = 5432
    debug: bool = False


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: dataclasses Internals")
    print("=" * 55)

    # Section 1
    print("\n[1] Mutable default trap:")
    try:
        @dataclass
        class Bad:
            items: list = []
    except ValueError as e:
        print(f"  ValueError: {e}")

    c1 = Cart()
    c2 = Cart()
    c1.add("apple")
    print(f"  c1.items = {c1.items}  (c2 unaffected: {c2.items})")

    # Section 2
    print("\n[2] __post_init__ — validation + derived fields:")
    try:
        Circle(-1.0)
    except ValueError as e:
        print(f"  Circle(-1) → ValueError: {e}")
    c = Circle(5.0)
    print(f"  Circle(5.0): {c}")
    print(f"  circumference (repr=False): {c.circumference:.4f}")

    # Section 3
    print("\n[3] ClassVar and InitVar:")
    t1 = Tracked("alice", verbose=True)
    t2 = Tracked("bob",   verbose=True)
    t3 = Tracked("carol")  # verbose=False default
    print(f"  Tracked.count = {Tracked.count}  (class-level, not in instance)")
    print(f"  't1' in t1.__dict__: {'name' in t1.__dict__}")
    print(f"  'count' in t1.__dict__: {'count' in t1.__dict__}")  # class var, not instance

    # Section 4
    print("\n[4] frozen=True — immutable and hashable:")
    v1 = Version(1, 2, 3)
    v2 = Version(2, 0, 0)
    v3 = Version(1, 2, 3)

    try:
        v1.major = 99
    except Exception as e:
        print(f"  v1.major = 99 → {type(e).__name__}: {e}")

    versions = {v1, v2, v3}  # hashable!
    print(f"  {{v1, v2, v3}} = {{{', '.join(str(v) for v in sorted(versions))}}}")
    print(f"  sorted: {sorted([v2, v1, v3])}")

    # Section 5
    print("\n[5] field() repr/compare control:")
    u1 = User(1, "Alice", "secret123", "alice@x.com")
    u2 = User(2, "Alice", "different!", "alice@x.com")
    u3 = User(3, "Alice", "other",     "other@x.com")
    print(f"  repr(u1): {u1!r}  (password hidden)")
    print(f"  u1 == u2: {u1 == u2}  (same id, name, email — password excluded)")
    print(f"  u1 == u3: {u1 == u3}  (different email)")

    # Section 6
    print("\n[6] dataclass utilities:")
    cfg = Config(host="prod.db", port=5432, debug=False)
    print(f"  asdict:   {asdict(cfg)}")
    new_cfg = replace(cfg, debug=True, port=5433)
    print(f"  replace:  {new_cfg}")
    print(f"  Original unchanged: {cfg}")
    print(f"  fields(): {[f.name for f in fields(Config)]}")

    print("\n" + "=" * 55)
