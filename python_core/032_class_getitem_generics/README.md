# __class_getitem__ & Generics

## 🎯 Interview Question
How does `list[int]` work in Python 3.9+? What is `__class_getitem__`, and how would you make your own generic class without inheriting from `typing.Generic`?

## 💡 Short Answer (30 seconds)
`list[int]` calls `list.__class_getitem__(int)`, which returns a `types.GenericAlias`. This was introduced in PEP 585 (Python 3.9). Before 3.9, only `typing.Generic` subclasses supported `[]`. You can implement `__class_getitem__` on any class to control what happens when it's subscripted — useful for custom generic containers, DSLs, and framework magic like SQLAlchemy's `Column[int]`.

## 🔬 Deep Explanation
Prior to Python 3.9, `list[int]` raised `TypeError`. The workaround was `from typing import List; List[int]`. PEP 585 added `__class_getitem__` to all built-in collection types as a *classmethod* that returns a `types.GenericAlias`.

**`types.GenericAlias`** carries `__origin__` (the raw class) and `__args__` (the type params). It supports `isinstance` checks only via `__instancecheck__` on the *origin* — `isinstance([], list[int])` raises `TypeError` on older Pythons and returns the same as `isinstance([], list)` on newer ones.

**`typing.Generic`** uses `__class_getitem__` under the hood but returns a richer `typing._GenericAlias` that supports `TypeVar` substitution, `__orig_bases__`, and runtime introspection needed by Pydantic, FastAPI, and mypy.

**When to implement your own `__class_getitem__`:**
1. Parameterized factory — `Repo[User]` returns a repository pre-typed for `User`.
2. Query DSL — `Field[str]` stores the type annotation for schema generation.
3. Validation hooks — intercept `[]` to validate or transform the parameter.

## 💻 Code Example
```python
from __future__ import annotations
import types

class Repo:
    """Parameterized repository factory — Repo[ModelClass]."""

    def __init__(self, model):
        self._model = model

    @classmethod
    def __class_getitem__(cls, item):
        # item is the type parameter (e.g. User)
        # Return a proxy that, when called, constructs a Repo for that type
        class BoundRepo(cls):
            _bound_model = item
            def __init__(self):
                super().__init__(item)
        BoundRepo.__name__ = f"Repo[{item.__name__}]"
        return BoundRepo

    def create(self, **kwargs):
        return self._model(**kwargs)

    def __repr__(self):
        return f"Repo(model={self._model.__name__})"

class User:
    def __init__(self, name=""):
        self.name = name
    def __repr__(self):
        return f"User({self.name!r})"

UserRepo = Repo[User]          # calls __class_getitem__
repo     = UserRepo()          # constructs bound repo
user     = repo.create(name="Alice")
print(user)                    # User('Alice')
print(repr(repo))              # Repo(model=User)

# Standard GenericAlias from built-ins
alias = list[int]
print(type(alias))             # <class 'types.GenericAlias'>
print(alias.__origin__)        # <class 'list'>
print(alias.__args__)          # (int,)
```

## ⚠️ Common Mistakes & Interview Traps
- **`isinstance(x, list[int])`** does NOT check element types — it's identical to `isinstance(x, list)`.
- **`__class_getitem__` vs `__getitem__`**: The former is called on the *class* (`Cls[X]`), the latter on *instances* (`obj[X]`). Mixing them up causes `TypeError: 'type' object is not subscriptable`.
- **Python < 3.9 compatibility**: `list[int]` raises `TypeError`; always guard with `from __future__ import annotations` + `if TYPE_CHECKING:` imports.
- **Returning non-type from `__class_getitem__`**: Tools like Pydantic expect a proper type or `_GenericAlias`; returning a plain object breaks field introspection.

## 🔗 Related Concepts
- python_core/004_metaclasses — `type.__getitem__` hooks
- python_core/019_typing_protocol — TypeVar, Protocol, structural typing
- python_core/014_dataclasses_internals — dataclasses + generic base classes

## 📚 Go Deeper
- PEP 585 — Type Hinting Generics in Standard Collections
- CPython `Lib/typing.py` — `_GenericAlias.__class_getitem__` implementation
