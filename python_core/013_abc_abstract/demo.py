"""
Demo: Abstract Base Classes (ABC) & Virtual Subclasses
Run:  python demo.py
"""

from abc import ABC, abstractmethod, ABCMeta
from collections.abc import Sized, Iterable, Mapping

# ── Section 1: ABC enforcement — partial implementation stays abstract ─────────
class Storage(ABC):
    @abstractmethod
    def read(self, key: str): ...

    @abstractmethod
    def write(self, key: str, value) -> None: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    # Concrete shared method — free for all subclasses
    def read_or_default(self, key: str, default=None):
        try:
            return self.read(key)
        except KeyError:
            return default


class PartialStorage(Storage):
    """Only implements read — still abstract!"""
    def read(self, key): return f"value:{key}"
    # write and delete missing → still abstract


class InMemoryStorage(Storage):
    def __init__(self):
        self._store = {}

    def read(self, key):
        if key not in self._store:
            raise KeyError(key)
        return self._store[key]

    def write(self, key, value):
        self._store[key] = value

    def delete(self, key):
        self._store.pop(key, None)


# ── Section 2: Abstract properties and classmethods ──────────────────────────
class Serializable(ABC):
    @property
    @abstractmethod
    def schema(self) -> dict:
        """Return JSON schema for this model."""
        ...

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict):
        """Construct from a dict."""
        ...


class User(Serializable):
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    @property
    def schema(self) -> dict:
        return {"name": str, "age": int}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data["name"], data["age"])


# ── Section 3: Virtual subclasses — register without inheritance ──────────────
class Drawable(ABC):
    @abstractmethod
    def draw(self) -> str: ...

    @classmethod
    def __subclasshook__(cls, C):
        if cls is Drawable:
            # Accept anything with a 'draw' method
            if any("draw" in B.__dict__ for B in C.__mro__):
                return True
        return NotImplemented


class Canvas:
    """Third-party class — no Drawable inheritance."""
    def draw(self) -> str:
        return "Canvas.draw()"


class Shape:
    """No draw method."""
    pass


# ── Section 4: collections.abc — __subclasshook__ in the wild ─────────────────
class CustomContainer:
    """Has __len__ and __iter__ — satisfies Sized and Iterable structurally."""
    def __init__(self, items):
        self._items = list(items)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)


# ── Section 5: __abstractmethods__ frozenset ─────────────────────────────────
def show_abstract_methods(cls):
    methods = getattr(cls, '__abstractmethods__', frozenset())
    print(f"  {cls.__name__}.__abstractmethods__ = {set(methods)}")


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: Abstract Base Classes (ABC) & Virtual Subclasses")
    print("=" * 55)

    # Section 1
    print("\n[1] ABC enforcement:")
    try:
        Storage()  # TypeError — all 3 methods abstract
    except TypeError as e:
        print(f"  Storage() → TypeError: {e}")

    show_abstract_methods(Storage)
    show_abstract_methods(PartialStorage)  # still has write, delete abstract

    try:
        PartialStorage()  # still abstract!
    except TypeError as e:
        print(f"  PartialStorage() → TypeError: {e}")

    store = InMemoryStorage()
    store.write("key1", "hello")
    print(f"  InMemoryStorage works: read('key1') = {store.read('key1')!r}")
    print(f"  read_or_default('missing', 'N/A') = {store.read_or_default('missing', 'N/A')!r}")

    # Section 2
    print("\n[2] Abstract property and classmethod:")
    u = User.from_dict({"name": "Alice", "age": 30})
    print(f"  User.from_dict(...) = User({u.name!r}, {u.age})")
    print(f"  user.schema = {u.schema}")

    try:
        class BadUser(Serializable):
            pass  # doesn't implement either abstract member
        BadUser()
    except TypeError as e:
        print(f"  BadUser() → TypeError: {e}")

    # Section 3
    print("\n[3] Virtual subclasses via __subclasshook__:")
    canvas = Canvas()
    shape = Shape()
    print(f"  isinstance(Canvas(), Drawable) = {isinstance(canvas, Drawable)}")
    print(f"  isinstance(Shape(),  Drawable) = {isinstance(shape, Drawable)}")
    print(f"  Canvas inherits Drawable: {'Drawable' in [c.__name__ for c in Canvas.__mro__]}")
    print(f"  (structural check — no inheritance needed)")

    # Section 4
    print("\n[4] collections.abc __subclasshook__ in the wild:")
    cc = CustomContainer([1, 2, 3])
    print(f"  isinstance(CustomContainer, Sized):    {isinstance(cc, Sized)}")
    print(f"  isinstance(CustomContainer, Iterable): {isinstance(cc, Iterable)}")
    print(f"  isinstance(CustomContainer, Mapping):  {isinstance(cc, Mapping)}")
    print(f"  isinstance([],  Sized):    {isinstance([], Sized)}")
    print(f"  isinstance({{}}, Mapping):  {isinstance({}, Mapping)}")

    # Section 5
    print("\n[5] __abstractmethods__ frozenset is the enforcement mechanism:")
    print(f"  InMemoryStorage.__abstractmethods__ = {InMemoryStorage.__abstractmethods__}")
    print(f"  (empty frozenset → concrete, can instantiate)")

    print("\n" + "=" * 55)
