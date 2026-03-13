"""
Demo: typing module — Protocol, TypeVar, Generic, Literal, TypeGuard
Run:  python demo.py
"""

from typing import (
    Protocol, TypeVar, Generic, Literal, runtime_checkable,
    overload, get_type_hints, Annotated, TypeGuard, Union
)
import sys

# ── Section 1: Protocol — structural typing ───────────────────────────────────
@runtime_checkable
class Drawable(Protocol):
    def draw(self) -> str: ...

@runtime_checkable
class Saveable(Protocol):
    def save(self) -> bool: ...
    def load(self, id: int) -> dict: ...


class Circle:
    """Satisfies Drawable without inheriting from it."""
    def draw(self) -> str:
        return "○"

class Square:
    def draw(self) -> str:
        return "□"

class Button:
    """Has draw but NOT save/load — satisfies Drawable, not Saveable."""
    def draw(self) -> str:
        return "[btn]"


# ── Section 2: TypeVar + Generic ───────────────────────────────────────────────
T = TypeVar('T')
KT = TypeVar('KT')
VT = TypeVar('VT')

class Stack(Generic[T]):
    """Type-safe stack — static analysis knows what type items are."""

    def __init__(self) -> None:
        self._items: list = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> T:
        return self._items[-1]

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        return f"Stack({self._items!r})"


def first(lst: list[T], default: T) -> T:
    """Generic function — return type matches list element type."""
    return lst[0] if lst else default


# ── Section 3: Literal — restrict values ──────────────────────────────────────
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]

def log(message: str, level: LogLevel = "INFO") -> str:
    return f"[{level}] {message}"

def make_request(method: HttpMethod, path: str) -> dict:
    return {"method": method, "path": path, "status": 200}


# ── Section 4: Type narrowing ──────────────────────────────────────────────────
def process_value(value: Union[int, str, list]) -> str:
    """Type checker narrows type in each branch."""
    if isinstance(value, int):
        # value is int here
        return f"int: {value * 2}"
    elif isinstance(value, str):
        # value is str here
        return f"str: {value.upper()}"
    else:
        # value is list here
        return f"list: {len(value)} items"


def is_list_of_ints(val: list) -> TypeGuard[list[int]]:
    """TypeGuard — narrow to list[int] when True."""
    return all(isinstance(x, int) for x in val)


# ── Section 5: overload — multiple type signatures ───────────────────────────
@overload
def double(x: int) -> int: ...
@overload
def double(x: str) -> str: ...
@overload
def double(x: list) -> list: ...
def double(x):
    """Single implementation, multiple type signatures for the type checker."""
    if isinstance(x, int):
        return x * 2
    elif isinstance(x, str):
        return x * 2
    else:
        return x + x


# ── Section 6: Annotated — metadata in type hints ────────────────────────────
PositiveInt = Annotated[int, "must be > 0"]
EmailStr = Annotated[str, "must contain @"]

def create_user(
    user_id: PositiveInt,
    email: EmailStr,
    role: Literal["admin", "user", "viewer"] = "user"
) -> dict:
    # Runtime validation (Pydantic would do this automatically)
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError(f"user_id must be positive int, got {user_id!r}")
    if "@" not in email:
        raise ValueError(f"email must contain @, got {email!r}")
    return {"id": user_id, "email": email, "role": role}


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: typing — Protocol, TypeVar, Generic, Literal")
    print("=" * 55)

    # Section 1
    print("\n[1] Protocol — structural typing:")
    shapes = [Circle(), Square(), Button()]
    for shape in shapes:
        is_drawable = isinstance(shape, Drawable)
        is_saveable = isinstance(shape, Saveable)
        print(f"  {type(shape).__name__:8s}: Drawable={is_drawable}, Saveable={is_saveable}")
    print("  (No inheritance from Drawable/Saveable — purely structural)")

    # Section 2
    print("\n[2] TypeVar + Generic — Stack[T]:")
    int_stack: Stack[int] = Stack()
    int_stack.push(1)
    int_stack.push(2)
    int_stack.push(3)
    print(f"  {int_stack}")
    print(f"  pop() → {int_stack.pop()}")
    print(f"  peek() → {int_stack.peek()}")

    str_stack: Stack[str] = Stack()
    str_stack.push("hello")
    str_stack.push("world")
    print(f"  {str_stack}")

    print(f"  first([10,20,30], 0) → {first([10, 20, 30], 0)}")
    print(f"  first([], 'N/A') → {first([], 'N/A')!r}")

    # Section 3
    print("\n[3] Literal — restricted values:")
    print(f"  {log('Server started', 'INFO')}")
    print(f"  {log('Disk 90% full', 'WARNING')}")
    print(f"  {make_request('GET', '/api/users')}")
    # Type checker would flag: log("msg", "VERBOSE") — not in Literal

    # Section 4
    print("\n[4] Type narrowing:")
    for val in [42, "hello", [1, 2, 3]]:
        print(f"  process_value({val!r}) → {process_value(val)!r}")

    data1 = [1, 2, 3]
    data2 = [1, "two", 3]
    print(f"  is_list_of_ints({data1}) → {is_list_of_ints(data1)}")
    print(f"  is_list_of_ints({data2}) → {is_list_of_ints(data2)}")

    # Section 5
    print("\n[5] @overload — multiple signatures, single implementation:")
    print(f"  double(5)       → {double(5)!r}")
    print(f"  double('abc')   → {double('abc')!r}")
    print(f"  double([1,2,3]) → {double([1, 2, 3])!r}")

    # Section 6
    print("\n[6] Annotated + runtime validation:")
    user = create_user(42, "alice@example.com", "admin")
    print(f"  create_user(42, 'alice@...', 'admin') → {user}")
    try:
        create_user(-1, "alice@example.com")
    except ValueError as e:
        print(f"  create_user(-1, ...) → ValueError: {e}")
    try:
        create_user(1, "not-an-email")
    except ValueError as e:
        print(f"  create_user(1, 'not-an-email') → ValueError: {e}")

    print("\n[7] __annotations__ — hints stored on functions:")
    print(f"  create_user.__annotations__ = {create_user.__annotations__}")

    print("\n" + "=" * 55)
