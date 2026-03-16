"""
Demo: property() vs Descriptors — Attribute Access Control
Run:  python demo.py
"""

# ── Section 1: @property full cycle ──────────────────────────────────────────
print("=" * 50)
print("Section 1: @property — get / set / delete")
print("=" * 50)

class Temperature:
    def __init__(self, celsius=0.0):
        self._celsius = celsius

    @property
    def celsius(self):
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError(f"Temperature {value} below absolute zero")
        self._celsius = value

    @celsius.deleter
    def celsius(self):
        print("Deleting temperature")
        del self._celsius

    @property
    def fahrenheit(self):                 # computed — no setter
        return self._celsius * 9/5 + 32

t = Temperature(100)
print("Celsius   :", t.celsius)
print("Fahrenheit:", t.fahrenheit)
t.celsius = -10
print("After set :", t.celsius)

try:
    t.celsius = -300
except ValueError as e:
    print("ValueError:", e)

del t.celsius

# ── Section 2: property() is a data descriptor ───────────────────────────────
print("\n" + "=" * 50)
print("Section 2: property is a data descriptor")
print("=" * 50)

class Foo:
    @property
    def x(self):
        return "from property"

f = Foo()
# Instance __dict__ does NOT shadow property (data descriptor wins)
f.__dict__["x"] = "from dict"
print("f.x =", f.x)          # "from property" — descriptor wins
print("f.__dict__:", f.__dict__)

# ── Section 3: Reusable descriptor with __set_name__ ─────────────────────────
print("\n" + "=" * 50)
print("Section 3: Custom descriptor + __set_name__")
print("=" * 50)

class Positive:
    """Descriptor: ensures numeric attribute is positive."""
    def __set_name__(self, owner, name):
        self.public_name  = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self   # class-level access → return descriptor itself
        return getattr(obj, self.private_name, 0)

    def __set__(self, obj, value):
        if value <= 0:
            raise ValueError(f"{self.public_name} must be positive, got {value}")
        setattr(obj, self.private_name, value)

class Rectangle:
    width  = Positive()
    height = Positive()

    def __init__(self, w, h):
        self.width  = w
        self.height = h

    def area(self):
        return self.width * self.height

r = Rectangle(3, 4)
print("Area:", r.area())
print("width descriptor:", Rectangle.width)   # returns descriptor itself

try:
    r.width = -1
except ValueError as e:
    print("ValueError:", e)

# ── Section 4: Non-data descriptor shadowed by instance dict ──────────────────
print("\n" + "=" * 50)
print("Section 4: Non-data descriptor vs instance __dict__")
print("=" * 50)

class NonData:
    def __get__(self, obj, objtype=None):
        return "from non-data descriptor"

class Bar:
    x = NonData()

b = Bar()
print("Before assignment:", b.x)   # descriptor wins
b.x = "from instance dict"         # sets instance __dict__
print("After assignment :", b.x)   # instance dict wins (shadows non-data descriptor!)
print("Instance dict    :", b.__dict__)

# ── Section 5: __set_name__ not called after class creation ──────────────────
print("\n" + "=" * 50)
print("Section 5: __set_name__ not called post-class")
print("=" * 50)

class MyDesc:
    name = None
    def __set_name__(self, owner, name):
        self.name = name
    def __get__(self, obj, objtype=None):
        return f"desc({self.name})"

class Baz:
    field = MyDesc()   # __set_name__ called → name = "field"

print("Via class body:", Baz().field)

class Qux:
    pass

Qux.late_field = MyDesc()   # __set_name__ NOT called
print("Late injection name:", Qux.late_field.name)   # None — trap!

if __name__ == "__main__":
    print("\nAll sections complete.")
