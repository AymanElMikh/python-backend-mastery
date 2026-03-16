"""
Demo: __class_getitem__ & Generics
Run:  python demo.py
"""
import types
import sys

# ── Section 1: Built-in GenericAlias (Python 3.9+) ──────────────────────────
alias = list[int]
print("type(list[int])   :", type(alias))
print("__origin__        :", alias.__origin__)
print("__args__          :", alias.__args__)
print("isinstance([], list[int]):", isinstance([], list[int]))  # same as isinstance([], list)

# ── Section 2: Custom __class_getitem__ ─────────────────────────────────────
class TypedStack:
    """Stack that remembers its element type at the class level."""

    _element_type = object

    @classmethod
    def __class_getitem__(cls, item):
        ns = {"_element_type": item, "__annotations__": {}}
        return type(f"TypedStack[{item.__name__}]", (cls,), ns)

    def __init__(self):
        self._data = []

    def push(self, value):
        if not isinstance(value, self.__class__._element_type):
            raise TypeError(f"Expected {self.__class__._element_type.__name__}, got {type(value).__name__}")
        self._data.append(value)

    def pop(self):
        return self._data.pop()

IntStack = TypedStack[int]
s = IntStack()
s.push(1)
s.push(2)
print("\nIntStack pop:", s.pop(), s.pop())

try:
    s.push("oops")
except TypeError as e:
    print("Type error caught:", e)

# ── Section 3: Trap — isinstance with parameterized alias ───────────────────
print("\n--- isinstance trap ---")
print("isinstance('hi', str)      :", isinstance("hi", str))        # True
print("isinstance([1,2], list[int]):", isinstance([1, 2], list[int]))  # True — doesn't check elements!
print("isinstance(['a'], list[int]):", isinstance(["a"], list[int]))   # Also True — NO element check!

# ── Section 4: __class_getitem__ vs __getitem__ ─────────────────────────────
class Confused:
    def __getitem__(self, key):          # called on INSTANCES
        return f"instance[{key}]"

    @classmethod
    def __class_getitem__(cls, item):    # called on the CLASS
        return f"class[{item}]"

obj = Confused()
print("\nobj['x']          :", obj["x"])        # instance[x]
print("Confused[int]      :", Confused[int])    # class[<class 'int'>]

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("DEMO: __class_getitem__ & Generics")
    print("=" * 50)
    print("All sections above demonstrate parameterized class subscript mechanics.")
