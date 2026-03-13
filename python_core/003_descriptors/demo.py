"""
Demo: Descriptors — __get__, __set__, __delete__
Run:  python demo.py
"""

# ── Section 1: Minimal descriptor — understand the protocol ───────────────────
class Trace:
    """Logs every get/set/delete — shows exactly when the protocol fires."""

    def __set_name__(self, owner, name):
        self.name = name
        self.storage = f"_{name}_value"

    def __get__(self, obj, objtype=None):
        if obj is None:
            print(f"    Trace.__get__(obj=None) → class access, returning descriptor")
            return self
        val = obj.__dict__.get(self.storage, "<unset>")
        print(f"    Trace.__get__({obj.__class__.__name__}) → {val!r}")
        return val

    def __set__(self, obj, value):
        print(f"    Trace.__set__({obj.__class__.__name__}, {value!r})")
        obj.__dict__[self.storage] = value

    def __delete__(self, obj):
        print(f"    Trace.__delete__({obj.__class__.__name__})")
        obj.__dict__.pop(self.storage, None)


class Config:
    host = Trace()
    port = Trace()

    def __init__(self, host, port):
        self.host = host
        self.port = port


# ── Section 2: Reusable typed field (data descriptor) ─────────────────────────
class TypedField:
    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = f"_{name}"

    def __init__(self, expected_type):
        self.expected_type = expected_type

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name, None)

    def __set__(self, obj, value):
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"'{self.public_name}' expects {self.expected_type.__name__}, "
                f"got {type(value).__name__}: {value!r}"
            )
        setattr(obj, self.private_name, value)


class Product:
    name = TypedField(str)
    price = TypedField(float)
    stock = TypedField(int)

    def __init__(self, name, price, stock):
        self.name = name
        self.price = price
        self.stock = stock

    def __repr__(self):
        return f"Product({self.name!r}, ${self.price}, qty={self.stock})"


# ── Section 3: Non-data descriptor — lazy property (compute once) ──────────────
class LazyProperty:
    """Non-data descriptor: result cached in instance __dict__, shadowing this descriptor."""

    def __init__(self, func):
        self.func = func

    def __set_name__(self, owner, name):
        self.attr_name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        print(f"    (LazyProperty: computing {self.attr_name!r} for the first time)")
        value = self.func(obj)
        # Store in instance __dict__ — this SHADOWS the non-data descriptor on future access
        obj.__dict__[self.attr_name] = value
        return value


class Report:
    def __init__(self, data):
        self.data = data

    @LazyProperty
    def summary(self):
        return f"Report({len(self.data)} items, total={sum(self.data)})"


# ── Section 4: The storage-on-descriptor trap ──────────────────────────────────
class BrokenDescriptor:
    """WRONG: stores value on self (shared across ALL instances)."""

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(self, '_val', None)  # BUG: self is shared!

    def __set__(self, obj, value):
        self._val = value  # BUG: overwrites for every instance


class Broken:
    x = BrokenDescriptor()


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: Descriptors — __get__, __set__, __delete__")
    print("=" * 55)

    # Section 1
    print("\n[1] Protocol tracing:")
    cfg = Config("localhost", 8080)
    print(f"    cfg.host =", end=" "); cfg.host  # triggers __get__
    del cfg.port
    print(f"    Config.host =", end=" "); Config.host  # class access

    # Section 2
    print("\n[2] TypedField — reusable validation:")
    p = Product("Widget", 9.99, 100)
    print(f"    {p}")
    try:
        p.price = "free"  # wrong type
    except TypeError as e:
        print(f"    TypeError: {e}")
    try:
        p.stock = 50.5  # wrong type
    except TypeError as e:
        print(f"    TypeError: {e}")

    # Section 3
    print("\n[3] LazyProperty — compute once, cache in instance __dict__:")
    r = Report([1, 2, 3, 4, 5])
    print(f"    First access:  {r.summary}")
    print(f"    Second access: {r.summary}  (no recompute — pulled from __dict__)")
    print(f"    In __dict__: {'summary' in r.__dict__}")

    # Section 4
    print("\n[4] The storage-on-descriptor trap:")
    b1 = Broken(); b2 = Broken()
    b1.x = "hello"
    b2.x = "world"
    print(f"    b1.x = {b1.x!r}  (expected 'hello', got {b1.x!r} — shared storage!)")
    print(f"    b2.x = {b2.x!r}")
    print("    Both share the same BrokenDescriptor instance → data stomped")

    print("\n" + "=" * 55)
