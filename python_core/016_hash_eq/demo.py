"""
Demo: __hash__ and __eq__ — The Hashability Contract
Run:  python demo.py
"""

# ── Section 1: The basic contract ────────────────────────────────────────────
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented  # let Python try the reflected op
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self):
        return hash((self.x, self.y))  # hash = hash of equality-defining tuple

    def __repr__(self):
        return f"Point({self.x}, {self.y})"


# ── Section 2: Defining __eq__ without __hash__ → unhashable ─────────────────
class BadPoint:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __eq__(self, other):
        return isinstance(other, BadPoint) and (self.x, self.y) == (other.x, other.y)
    # Python auto-sets __hash__ = None here!


# ── Section 3: NotImplemented vs False in __eq__ ─────────────────────────────
class Celsius:
    def __init__(self, temp):
        self.temp = temp

    def __eq__(self, other):
        if isinstance(other, Celsius):
            return self.temp == other.temp
        if isinstance(other, Fahrenheit):
            return self.temp == (other.temp - 32) * 5 / 9
        return NotImplemented  # not False — let other type try

    def __hash__(self):
        return hash(round(self.temp, 6))

    def __repr__(self):
        return f"{self.temp}°C"


class Fahrenheit:
    def __init__(self, temp):
        self.temp = temp

    def __eq__(self, other):
        if isinstance(other, Fahrenheit):
            return self.temp == other.temp
        if isinstance(other, Celsius):
            return self.temp == other.temp * 9 / 5 + 32
        return NotImplemented

    def __hash__(self):
        celsius = (self.temp - 32) * 5 / 9
        return hash(round(celsius, 6))

    def __repr__(self):
        return f"{self.temp}°F"


# ── Section 4: Mutable-in-dict trap ──────────────────────────────────────────
class MutableKey:
    def __init__(self, val):
        self.val = val

    def __eq__(self, other):
        return isinstance(other, MutableKey) and self.val == other.val

    def __hash__(self):
        return hash(self.val)  # DANGER: changes when val changes

    def __repr__(self):
        return f"MutableKey({self.val!r})"


# ── Section 5: Inheritance hash trap ─────────────────────────────────────────
class ColoredPoint(Point):
    def __init__(self, x, y, color):
        super().__init__(x, y)
        self.color = color

    def __eq__(self, other):
        if not isinstance(other, ColoredPoint):
            return NotImplemented
        return (self.x, self.y, self.color) == (other.x, other.y, other.color)
    # BUG: inherits Point.__hash__ which doesn't include color!

class FixedColoredPoint(Point):
    def __init__(self, x, y, color):
        super().__init__(x, y)
        self.color = color

    def __eq__(self, other):
        if not isinstance(other, FixedColoredPoint):
            return NotImplemented
        return (self.x, self.y, self.color) == (other.x, other.y, other.color)

    def __hash__(self):
        return hash((self.x, self.y, self.color))  # includes all equality fields


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: __hash__ and __eq__ — Hashability Contract")
    print("=" * 55)

    # Section 1
    print("\n[1] Correct __hash__ + __eq__:")
    p1 = Point(1, 2)
    p2 = Point(1, 2)
    p3 = Point(3, 4)
    print(f"  p1 == p2: {p1 == p2}  (same coords)")
    print(f"  hash(p1) == hash(p2): {hash(p1) == hash(p2)}  (contract satisfied)")
    print(f"  p1 is p2: {p1 is p2}  (different objects)")
    point_set = {p1, p2, p3}
    print(f"  {{p1, p2, p3}} = {point_set}  (p1 and p2 deduplicated)")
    point_dict = {p1: "origin-ish", p3: "far"}
    print(f"  dict[p2] = {point_dict[p2]!r}  (p2 looks up p1's value)")

    # Section 2
    print("\n[2] __eq__ without __hash__ → unhashable:")
    print(f"  BadPoint.__hash__ = {BadPoint.__hash__}")  # None
    bp = BadPoint(1, 2)
    try:
        {bp}
    except TypeError as e:
        print(f"  {{BadPoint()}} → TypeError: {e}")

    # Section 3
    print("\n[3] NotImplemented enables cross-type equality:")
    boiling_c = Celsius(100)
    boiling_f = Fahrenheit(212)
    print(f"  Celsius(100) == Fahrenheit(212): {boiling_c == boiling_f}")
    print(f"  Fahrenheit(212) == Celsius(100): {boiling_f == boiling_c}")
    # They can coexist in a set because their hashes match:
    temp_set = {boiling_c, boiling_f}
    print(f"  {{Celsius(100), Fahrenheit(212)}} = {temp_set}  (same hash → deduplicated)")

    # Section 4
    print("\n[4] Mutable-in-dict trap:")
    key = MutableKey("user:1")
    d = {key: "Alice"}
    print(f"  d[key] = {d[key]!r}  (before mutation)")
    key.val = "user:999"  # mutate — hash changes!
    result = d.get(key)
    print(f"  d.get(key) after mutation = {result!r}  (key is in wrong bucket now)")
    print(f"  d.get(MutableKey('user:1')) = {d.get(MutableKey('user:1'))!r}  (original hash bucket is stale)")
    print(f"  d contents: {list(d.items())}  (entry is still there, just unreachable)")

    # Section 5
    print("\n[5] Inheritance hash trap:")
    cp1 = ColoredPoint(1, 2, "red")
    cp2 = ColoredPoint(1, 2, "blue")
    print(f"  ColoredPoint(1,2,red) == ColoredPoint(1,2,blue): {cp1 == cp2}  (correct: False)")
    print(f"  hash(cp1) == hash(cp2): {hash(cp1) == hash(cp2)}  (WRONG: inherited hash ignores color!)")
    print(f"  → These could collide in a set, degrading to O(n) lookup")

    fcp1 = FixedColoredPoint(1, 2, "red")
    fcp2 = FixedColoredPoint(1, 2, "blue")
    print(f"  FixedColoredPoint: hash equality = {hash(fcp1) == hash(fcp2)}  (correct: hashes differ)")

    print("\n" + "=" * 55)
