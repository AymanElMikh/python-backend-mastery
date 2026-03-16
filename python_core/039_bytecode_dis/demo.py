"""
Demo: Bytecode & the dis Module — CPython Internals
Run:  python demo.py
"""
import dis
import types

# ── Section 1: Basic disassembly ──────────────────────────────────────────────
print("=" * 50)
print("Section 1: Basic disassembly — add(a, b)")
print("=" * 50)

def add(a, b):
    return a + b

dis.dis(add)

# ── Section 2: LOAD_FAST vs LOAD_GLOBAL vs LOAD_DEREF ────────────────────────
print("\n" + "=" * 50)
print("Section 2: LOAD_FAST vs LOAD_GLOBAL vs LOAD_DEREF")
print("=" * 50)

X = 100   # global

def scope_demo():
    local = 1
    def inner():
        return local + X   # LOAD_DEREF (local) + LOAD_GLOBAL (X)
    return inner

inner_fn = scope_demo()
print("\ninner() bytecode:")
dis.dis(inner_fn)
print("co_freevars:", inner_fn.__code__.co_freevars)

# ── Section 3: UnboundLocalError trap ─────────────────────────────────────────
print("\n" + "=" * 50)
print("Section 3: UnboundLocalError trap")
print("=" * 50)

x = 10

def trap():
    # print(x)    # would raise UnboundLocalError because x is assigned below
    x = 20        # this assignment makes x LOCAL throughout the function
    return x

print("No error here (assignment before use):", trap())

def trigger_error():
    try:
        print(x)  # x is local (assigned below) but not yet bound
    except UnboundLocalError as e:
        print("UnboundLocalError:", e)
    x = 20

trigger_error()

print("\nbytecode of trigger_error:")
dis.dis(trigger_error)

# ── Section 4: Constant folding ───────────────────────────────────────────────
print("\n" + "=" * 50)
print("Section 4: Constant folding")
print("=" * 50)

def with_folding():
    return 3 * 7 + 1    # compiler folds to 22

def no_folding(n):
    return n * 7 + 1    # runtime computation

print("Folded constants:", with_folding.__code__.co_consts)
dis.dis(with_folding)

# ── Section 5: Code object attributes ────────────────────────────────────────
print("\n" + "=" * 50)
print("Section 5: Code object introspection")
print("=" * 50)

def example(a, b=10, *args, **kwargs):
    local = a + b
    return local

code = example.__code__
print("co_varnames  :", code.co_varnames)
print("co_argcount  :", code.co_argcount)
print("co_consts    :", code.co_consts)
print("co_stacksize :", code.co_stacksize)
print("co_flags     :", bin(code.co_flags))

# ── Section 6: get_instructions ───────────────────────────────────────────────
print("\n" + "=" * 50)
print("Section 6: Iterating instructions")
print("=" * 50)

load_ops = [i for i in dis.get_instructions(add) if i.opname.startswith("LOAD")]
print("LOAD instructions in add():")
for instr in load_ops:
    print(f"  {instr.opname:20s} {instr.argval}")

if __name__ == "__main__":
    print("\nAll sections complete.")
