"""
Demo: __init_subclass__ & Class Creation Hooks
Run:  python demo.py
"""

from abc import ABC, abstractmethod

# ── Section 1: __init_subclass__ — plugin registration ───────────────────────
class Serializer(ABC):
    """Auto-registers subclasses by their format name."""
    _registry: dict = {}

    def __init_subclass__(cls, format: str = None, **kwargs):
        super().__init_subclass__(**kwargs)  # ALWAYS call super!
        if format is not None:
            Serializer._registry[format] = cls
            print(f"    Registered Serializer: {cls.__name__!r} → format={format!r}")

    @abstractmethod
    def serialize(self, data: dict) -> str: ...

    @abstractmethod
    def deserialize(self, text: str) -> dict: ...

    @classmethod
    def for_format(cls, format: str):
        if format not in cls._registry:
            raise ValueError(f"No serializer for format {format!r}")
        return cls._registry[format]()


class JsonSerializer(Serializer, format="json"):
    def serialize(self, data: dict) -> str:
        import json
        return json.dumps(data)

    def deserialize(self, text: str) -> dict:
        import json
        return json.loads(text)


class CsvSerializer(Serializer, format="csv"):
    def serialize(self, data: dict) -> str:
        keys = list(data.keys())
        return ",".join(keys) + "\n" + ",".join(str(data[k]) for k in keys)

    def deserialize(self, text: str) -> dict:
        lines = text.strip().split("\n")
        keys = lines[0].split(",")
        vals = lines[1].split(",")
        return dict(zip(keys, vals))


# ── Section 2: Enforcement — require class-level attributes ──────────────────
class DBModel(ABC):
    """Every subclass must declare table_name and primary_key."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        missing = [attr for attr in ('table_name', 'primary_key')
                   if not hasattr(cls, attr)]
        if missing:
            raise TypeError(
                f"Class {cls.__name__!r} must define: {', '.join(missing)}"
            )


# ── Section 3: Cooperative chain — multi-level hierarchy ─────────────────────
class Base:
    def __init_subclass__(cls, tag: str = None, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._tag = tag or cls.__name__.lower()
        print(f"    Base.__init_subclass__: {cls.__name__!r}, tag={cls._tag!r}")

class Middleware(Base):
    def __init_subclass__(cls, priority: int = 50, **kwargs):
        super().__init_subclass__(**kwargs)  # passes tag kwarg up to Base
        cls._priority = priority
        print(f"    Middleware.__init_subclass__: {cls.__name__!r}, priority={cls._priority}")

class AuthMiddleware(Middleware, tag="auth", priority=10):
    pass

class LogMiddleware(Middleware, tag="log", priority=90):
    pass


# ── Section 4: __class_getitem__ — subscript syntax ──────────────────────────
class TypedQueue:
    """A queue that supports TypedQueue[int] syntax."""

    def __class_getitem__(cls, item_type):
        # Returns a specialized description (real generics would use Generic[T])
        name = item_type.__name__ if hasattr(item_type, '__name__') else str(item_type)
        return type(f"TypedQueue[{name}]", (cls,), {"_item_type": item_type})

    def __init__(self):
        self._items = []

    def enqueue(self, item):
        if hasattr(self.__class__, '_item_type'):
            if not isinstance(item, self.__class__._item_type):
                raise TypeError(f"Expected {self.__class__._item_type.__name__}, got {type(item).__name__}")
        self._items.append(item)

    def dequeue(self):
        return self._items.pop(0)


# ── Section 5: __set_name__ — descriptor self-registration ───────────────────
class Column:
    """ORM-style descriptor that learns its name via __set_name__."""

    def __init__(self, col_type, nullable=True):
        self.col_type = col_type
        self.nullable = nullable
        self.name = None       # set by __set_name__
        self.attr = None

    def __set_name__(self, owner, name):
        self.name = name
        self.attr = f"_{name}"
        print(f"    Column.__set_name__: {name!r} on {owner.__name__!r}")

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.attr, None)

    def __set__(self, obj, value):
        if value is None and not self.nullable:
            raise ValueError(f"Column {self.name!r} is NOT NULL")
        if value is not None and not isinstance(value, self.col_type):
            raise TypeError(f"Column {self.name!r}: expected {self.col_type.__name__}")
        setattr(obj, self.attr, value)


class UserRecord:
    name  = Column(str, nullable=False)
    age   = Column(int, nullable=True)
    email = Column(str, nullable=False)

    def __init__(self, name, age, email):
        self.name  = name
        self.age   = age
        self.email = email


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: __init_subclass__ & Class Creation Hooks")
    print("=" * 55)

    print("\n[1] Plugin registration via __init_subclass__:")
    print(f"  Registered formats: {list(Serializer._registry.keys())}")
    data = {"user": "alice", "age": 30}

    s = Serializer.for_format("json")
    serialized = s.serialize(data)
    print(f"  JSON: {serialized!r}")
    print(f"  Roundtrip: {s.deserialize(serialized)}")

    s2 = Serializer.for_format("csv")
    serialized2 = s2.serialize(data)
    print(f"  CSV: {serialized2!r}")

    print("\n[2] Enforcement — required class attributes:")
    try:
        class BadModel(DBModel):
            pass  # missing table_name and primary_key
    except TypeError as e:
        print(f"  BadModel → TypeError: {e}")

    class UserModel(DBModel):
        table_name = "users"
        primary_key = "id"
    print(f"  UserModel accepted ✓  (table_name={UserModel.table_name!r})")

    print("\n[3] Cooperative multi-level __init_subclass__:")
    print(f"  AuthMiddleware._tag={AuthMiddleware._tag!r}, _priority={AuthMiddleware._priority}")
    print(f"  LogMiddleware._tag={LogMiddleware._tag!r},  _priority={LogMiddleware._priority}")

    print("\n[4] __class_getitem__ — subscript syntax:")
    IntQueue = TypedQueue[int]
    print(f"  TypedQueue[int] → {IntQueue.__name__!r}")
    q = IntQueue()
    q.enqueue(1)
    q.enqueue(2)
    try:
        q.enqueue("hello")
    except TypeError as e:
        print(f"  q.enqueue('hello') → TypeError: {e}")
    print(f"  q.dequeue() = {q.dequeue()}")

    print("\n[5] __set_name__ — descriptor self-registration:")
    u = UserRecord("Alice", 30, "alice@example.com")
    print(f"  UserRecord(Alice, 30, alice@...) = name={u.name!r}, age={u.age}, email={u.email!r}")
    try:
        u.name = None  # NOT NULL column
    except ValueError as e:
        print(f"  u.name = None → ValueError: {e}")
    try:
        u.age = "thirty"  # wrong type
    except TypeError as e:
        print(f"  u.age = 'thirty' → TypeError: {e}")
    print(f"  Column descriptors: {[f.name for f in (UserRecord.name, UserRecord.age, UserRecord.email)]}")

    print("\n" + "=" * 55)
