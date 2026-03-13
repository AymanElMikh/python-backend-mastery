# Abstract Base Classes (ABC) & Virtual Subclasses

## 🎯 Interview Question
What is an Abstract Base Class in Python, how does `ABCMeta` enforce abstract methods, and what is a virtual subclass? When would you use `ABC` over a plain interface protocol?

## 💡 Short Answer (30 seconds)
An Abstract Base Class uses `ABCMeta` as its metaclass to track which methods are decorated with `@abstractmethod`. Any class that inherits from an ABC without implementing all abstract methods cannot be instantiated — Python raises `TypeError`. Virtual subclasses (`ABC.register(cls)`) let you declare that a class conforms to an interface *without* inheritance — enabling `isinstance`/`issubclass` checks on classes you don't control.

## 🔬 Deep Explanation

### How `ABCMeta` enforces abstraction
`ABCMeta.__new__` scans the class namespace and all inherited classes for `__isabstractmethod__ = True` markers (set by `@abstractmethod`). The result is stored in `cls.__abstractmethods__` — a `frozenset` of names. `object.__new__` checks this frozenset before allocating: if non-empty, raises `TypeError: Can't instantiate abstract class`.

```python
class MyABC(ABC):
    @abstractmethod
    def process(self): ...

class Concrete(MyABC): pass   # doesn't implement process
Concrete()  # TypeError: Can't instantiate abstract class Concrete
            # with abstract method process
```

### `@abstractmethod` combinators
- `@abstractmethod` alone — must be overridden
- `@property` + `@abstractmethod` — subclass must define a property
- `@classmethod` + `@abstractmethod` — subclass must define a classmethod
- `@staticmethod` + `@abstractmethod` — subclass must define a staticmethod

**Order matters**: `@abstractmethod` must be the *innermost* decorator.

### Virtual subclasses — `register()`
`ABC.register(SomeClass)` makes `isinstance(obj, ABC)` return `True` for `SomeClass` instances — without `SomeClass` inheriting from `ABC`. The registered class is not checked for abstract method implementation. Useful for:
- Retrofitting third-party classes to satisfy an interface
- `collections.abc` recognizing built-in types: `isinstance([], MutableSequence)` → `True`

```python
class Drawable(ABC):
    @abstractmethod
    def draw(self): ...

class ThirdPartyWidget:  # no inheritance
    def draw(self): print("drawing")

Drawable.register(ThirdPartyWidget)
isinstance(ThirdPartyWidget(), Drawable)  # True — virtual subclass
```

### `__subclasshook__` — custom isinstance logic
`ABCMeta` checks `__subclasshook__` before consulting the MRO. Return `True` to accept, `False` to reject, `NotImplemented` to fall back to normal checks. Used by `collections.abc`:
```python
class Sized(ABC):
    @classmethod
    def __subclasshook__(cls, C):
        if cls is Sized:
            return any("__len__" in B.__dict__ for B in C.__mro__)
        return NotImplemented
```
This is why `isinstance([], Sized)` is `True` without `list` ever explicitly registering.

### `ABC` vs `Protocol` (typing)
| | `ABC` | `Protocol` |
|---|---|---|
| Enforcement | `TypeError` at instantiation | Static analysis only (mypy) |
| Virtual subclasses | `register()` | Structural — any class with matching attrs |
| Runtime `isinstance` | Yes | Yes (with `@runtime_checkable`) |
| Inheritance required | For full enforcement | No |

Use `ABC` when you want **runtime enforcement**. Use `Protocol` when you want **structural typing** (duck typing with static analysis).

### Real-world use
- `collections.abc` — `Iterable`, `Mapping`, `Sequence`, `MutableSet`
- FastAPI/Pydantic validators — base classes with abstract `validate()`
- Repository pattern — `AbstractRepository` with abstract `find`, `save`, `delete`
- Plugin systems — enforce required interface on all plugins

## 💻 Code Example

```python
from abc import ABC, abstractmethod

class Repository(ABC):
    """Abstract repository — enforces the interface without dictating storage."""

    @abstractmethod
    def find_by_id(self, id: int):
        """Return entity by ID or None."""
        ...

    @abstractmethod
    def save(self, entity) -> None:
        """Persist entity."""
        ...

    @abstractmethod
    def delete(self, id: int) -> None:
        """Remove entity by ID."""
        ...

    # Concrete method — shared logic available to all implementations
    def find_or_raise(self, id: int):
        entity = self.find_by_id(id)
        if entity is None:
            raise KeyError(f"Entity {id} not found")
        return entity


class InMemoryRepository(Repository):
    def __init__(self):
        self._store: dict = {}

    def find_by_id(self, id):
        return self._store.get(id)

    def save(self, entity):
        self._store[entity["id"]] = entity

    def delete(self, id):
        self._store.pop(id, None)
```

## ⚠️ Common Mistakes & Interview Traps

1. **Partial implementation still raises TypeError**: If a concrete class implements only *some* abstract methods, it remains abstract. `cls.__abstractmethods__` will still be non-empty.

2. **Virtual subclasses bypass enforcement**: `ABC.register(Cls)` does NOT check that `Cls` implements the abstract methods. It's purely a declaration — used for `isinstance` compatibility, not enforcement.

3. **`@abstractmethod` order**: `@property @abstractmethod` is WRONG (silently ignored). `@abstractmethod @property` is also wrong. Correct: first `@property`, then `@abstractmethod` on the getter... actually in Python 3.3+ the correct form is:
   ```python
   @property
   @abstractmethod
   def x(self): ...
   ```
   `@abstractmethod` must be the innermost (closest to `def`).

4. **`ABCMeta` vs `ABC`**: `ABC = ABCMeta('ABC', (object,), {})`. Using `class Foo(ABC)` and `class Foo(metaclass=ABCMeta)` are equivalent. Mixing with another metaclass needs a combined metaclass.

5. **Concrete methods in ABCs are inherited**: ABCs can have full implementations. Subclasses get them for free. This is the Template Method pattern — define the algorithm in the ABC, defer steps to subclasses.

## 🔗 Related Concepts
- `python_core/004_metaclasses` — `ABCMeta` is a metaclass; mixing it requires metaclass resolution
- `python_core/005_mro_super` — multiple inheritance from ABCs requires cooperative `super()`
- `python_core/019_typing_protocol` — `Protocol` as the structural alternative to ABC

## 📚 Go Deeper
- `collections.abc` source — `__subclasshook__` implementations for all built-in ABCs
- PEP 3119 — "Introducing Abstract Base Classes" — design rationale
