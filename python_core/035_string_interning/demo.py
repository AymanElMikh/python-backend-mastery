"""
Demo: String Interning — CPython's String Cache
Run:  python demo.py
"""
import sys

# ── Section 1: Automatic interning of identifier-like strings ────────────────
print("=" * 50)
print("Section 1: Automatic interning")
print("=" * 50)

a = "hello"
b = "hello"
print(f"'hello' is 'hello' : {a is b}")   # True — interned

c = "hello world"
d = "hello world"
# Same module compile-time folding often makes this True, but DON'T rely on it
print(f"'hello world' is 'hello world' : {c is d}  (implementation detail!)")

# ── Section 2: Runtime-constructed strings are NOT interned ──────────────────
print("\n" + "=" * 50)
print("Section 2: Runtime construction — not interned")
print("=" * 50)

prefix = "hel"
suffix = "lo"
runtime_str = prefix + suffix      # built at runtime, NOT interned
static_str  = "hello"

print(f"runtime == static : {runtime_str == static_str}")   # True
print(f"runtime is static : {runtime_str is static_str}")   # False

# ── Section 3: sys.intern() forces canonical sharing ─────────────────────────
print("\n" + "=" * 50)
print("Section 3: sys.intern()")
print("=" * 50)

s1 = sys.intern(prefix + suffix)   # intern the runtime string
s2 = sys.intern("hello")           # intern the literal
print(f"After sys.intern: s1 is s2 : {s1 is s2}")   # True

# ── Section 4: The is-for-string TRAP ────────────────────────────────────────
print("\n" + "=" * 50)
print("Section 4: The dangerous 'is' trap")
print("=" * 50)

def is_admin_WRONG(role: str) -> bool:
    return role is "admin"   # BUG — never do this

def is_admin_correct(role: str) -> bool:
    return role == "admin"   # correct

user_role = "adm" + "in"    # runtime string
print(f"is_admin_WRONG (runtime): {is_admin_WRONG(user_role)}")    # False — security bug!
print(f"is_admin_correct        : {is_admin_correct(user_role)}")  # True

# ── Section 5: Performance — interned dict key lookups ───────────────────────
print("\n" + "=" * 50)
print("Section 5: Interning & dict lookup speed")
print("=" * 50)
import timeit

big_dict = {f"key_{i}": i for i in range(1000)}
key_interned = sys.intern("key_500")
key_runtime  = "key_" + "500"        # not interned

t1 = timeit.timeit(lambda: big_dict[key_interned], number=500_000)
t2 = timeit.timeit(lambda: big_dict[key_runtime],  number=500_000)
print(f"Interned key lookup  : {t1:.4f}s")
print(f"Non-interned key     : {t2:.4f}s")
print("(Difference is small but consistent in attribute-heavy workloads)")

if __name__ == "__main__":
    print("\nAll sections complete.")
