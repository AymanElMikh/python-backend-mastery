"""
Demo: Closure Cells & nonlocal — LEGB Scope Deep Dive
Run:  python demo.py
"""
import dis

# ── Section 1: Cell object inspection ────────────────────────────────────────
print("=" * 50)
print("Section 1: Cell objects & __closure__")
print("=" * 50)

def outer(x):
    multiplier = 10
    def inner(y):
        return x * multiplier + y    # x, multiplier are free vars
    return inner

f = outer(3)
print("co_freevars :", f.__code__.co_freevars)
print("cell values :", [c.cell_contents for c in f.__closure__])
print("f(5)        :", f(5))    # 3*10 + 5 = 35

# ── Section 2: Late-binding trap ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("Section 2: Late-binding trap in loops")
print("=" * 50)

bad_fns  = [lambda: i for i in range(5)]
good_fns = [lambda i=i: i for i in range(5)]

print("Bad  (late binding):", [f() for f in bad_fns])    # [4,4,4,4,4]
print("Good (default arg) :", [f() for f in good_fns])   # [0,1,2,3,4]

# ── Section 3: nonlocal for mutable counter ───────────────────────────────────
print("\n" + "=" * 50)
print("Section 3: nonlocal counter")
print("=" * 50)

def make_counter(start=0):
    count = start
    def increment(by=1):
        nonlocal count
        count += by
        return count
    def reset():
        nonlocal count
        count = start
    increment.reset = reset
    return increment

c = make_counter(10)
print(c())     # 11
print(c(5))    # 16
c.reset()
print(c())     # 11

# ── Section 4: nonlocal vs global trap ────────────────────────────────────────
print("\n" + "=" * 50)
print("Section 4: nonlocal vs global")
print("=" * 50)

state = "module-level"

def outer_scope():
    state = "outer"
    def inner_nonlocal():
        nonlocal state
        state = "inner modified outer"    # modifies outer_scope's state
    def inner_global():
        global state
        state = "inner modified global"   # modifies module-level state!
    inner_nonlocal()
    print("after nonlocal:", state)       # "inner modified outer"
    inner_global()
    print("global state  :", globals()["state"])  # "inner modified global"

outer_scope()

# ── Section 5: Bytecode — LOAD_DEREF for cells ───────────────────────────────
print("\n" + "=" * 50)
print("Section 5: Bytecode LOAD_DEREF")
print("=" * 50)

def enclosing():
    value = 42
    def reader():
        return value
    return reader

reader = enclosing()
print("Bytecode for reader:")
dis.dis(reader)

if __name__ == "__main__":
    print("\nAll sections complete.")
