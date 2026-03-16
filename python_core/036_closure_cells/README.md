# Closure Cells & nonlocal — LEGB Scope Deep Dive

## 🎯 Interview Question
Explain Python's LEGB scoping rule. What is a closure cell, what is the "late-binding closure" trap, and when would you use `nonlocal` vs returning a mutable container instead?

## 💡 Short Answer (30 seconds)
Python resolves names via LEGB: Local → Enclosing function → Global → Built-in. A *closure* is a function that captures variables from an enclosing scope into *cell objects* — shared references, not value copies. The classic trap: loop-captured variables all reference the *same* cell, so all closures see the final value. Fix with a default argument (`lambda i=i: i`) or `functools.partial`.

## 🔬 Deep Explanation
**Cell objects (`__closure__`)**
When Python compiles a nested function that references an outer variable, the compiler marks that variable as a *free variable* in the inner function and a *cell variable* in the outer function. CPython stores cells in `func.__code__.co_freevars` and the values in `func.__closure__` (a tuple of `cell` objects). Both the outer and inner function share the *same* cell — so mutations in the outer scope are visible inside the closure and vice versa.

```python
def outer():
    x = 1
    def inner():
        return x     # x captured as free variable
    x = 2            # mutates the shared cell
    return inner

f = outer()
f()  # returns 2, not 1 — late binding!
```

**`nonlocal` keyword**
Allows assignment to a variable in an enclosing (non-global) scope. Without `nonlocal`, assigning `x = ...` inside `inner` creates a *new* local variable, shadowing the outer one. `nonlocal x` makes the assignment target the cell of the enclosing scope.

**Late-binding trap in loops**
```python
fns = [lambda: i for i in range(3)]
[f() for f in fns]  # [2, 2, 2] — all share same cell
```
Fix: `[lambda i=i: i for i in range(3)]` — default argument captures value at definition time.

**Counter pattern (production use)**
```python
def make_counter():
    count = 0
    def increment():
        nonlocal count
        count += 1
        return count
    return increment
```

**Thread-safety caveat**: closures over mutable cells are not thread-safe. Use threading.local() or explicit locks for shared state.

## 💻 Code Example
```python
import dis

def outer(x):
    def inner():
        return x      # free variable
    return inner

f = outer(42)
print(f.__code__.co_freevars)   # ('x',)
print(f.__closure__[0].cell_contents)  # 42

# Late-binding — all lambdas share the same 'i' cell
funcs = [lambda: i for i in range(5)]
print([f() for f in funcs])    # [4, 4, 4, 4, 4]

# Fix: capture by default arg
fixed = [lambda i=i: i for i in range(5)]
print([f() for f in fixed])    # [0, 1, 2, 3, 4]
```

## ⚠️ Common Mistakes & Interview Traps
- **`nonlocal` vs `global`**: `nonlocal` targets enclosing function scope; `global` targets module scope. Using `global` in a nested function when you meant `nonlocal` silently modifies module state.
- **Cell is shared, not copied**: Mutating the captured variable from the outer scope after defining the closure changes what the closure sees.
- **Loop variable capture**: The most common interview question on closures. Always demo the `[2,2,2]` vs `[0,1,2]` behavior.
- **`__closure__` is None for non-closures**: Forgetting to check causes `AttributeError` when inspecting functions.

## 🔗 Related Concepts
- python_core/009_decorator_internals — decorators are closures
- python_core/008_generators_internals — generators also use frame/cell objects
- python_core/035_string_interning — LEGB lookup starts with locals

## 📚 Go Deeper
- `dis.dis(inner)` — see `LOAD_DEREF` (load from cell) vs `LOAD_FAST` (local)
- CPython `Include/cellobject.h` — `PyCellObject` struct
