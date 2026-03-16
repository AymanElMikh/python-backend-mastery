# String Interning — CPython's String Cache

## 🎯 Interview Question
What is string interning in CPython, why does `"hello" is "hello"` return `True` while `"hello world" is "hello world"` might return `False`, and what are the production implications of relying on `is` for string comparison?

## 💡 Short Answer (30 seconds)
CPython automatically interns string literals that look like identifiers (letters, digits, underscores, ≤ ~20 chars) by caching them in a global dict so identical strings share one object. This means `is` can return `True` for interned strings — but it's an implementation detail. Always use `==` for string equality; `is` only tests *identity*, and interning rules are not guaranteed across Python versions, interpreters, or runtime-constructed strings.

## 🔬 Deep Explanation
**How interning works:**
CPython maintains `interned` — a dict in `Objects/unicodeobject.c` mapping string value → canonical string object. When a string is interned:
1. If it already exists in `interned`, the existing object is returned (refcount bumped).
2. Otherwise, the string is added and returned.

**Automatic interning triggers:**
- String literals that are valid Python identifiers (`[a-zA-Z_][a-zA-Z0-9_]*`).
- Strings used as attribute names, function names, keyword argument names.
- Short strings (implementation-defined threshold, typically ≤ 20 chars with no spaces).
- Compile-time constant folding: `"abc" * 2` → `"abcabc"` may be interned if short enough.

**Manual interning:** `sys.intern(s)` — forces a string into the intern dict. Returns the canonical copy.

**Performance impact:**
- Dictionary key lookups with interned strings use *pointer equality* before hash comparison — measurable speedup in attribute lookup-heavy code.
- Memory savings when many identical strings exist (e.g., repeated JSON keys parsed from the network).

**Runtime-constructed strings are NOT automatically interned:**
```python
a = "hello"
b = "hel" + "lo"   # compile-time constant folding → same object
c = input_data[:5]  # runtime slice → separate object, NOT interned
```

**In production:** ORM column names, enum values, and config keys are often interned. Never use `is` for string equality in business logic — only use it to check `None`, `True`, `False`.

## 💻 Code Example
```python
import sys

# Automatically interned (identifier-like)
a = "hello"
b = "hello"
print(a is b)   # True in CPython — same object

# NOT automatically interned (has space)
x = "hello world"
y = "hello world"
print(x is y)   # Likely False (CPython may fold at compile time in same module — trap!)

# Definitely NOT interned: runtime-constructed
s1 = "hel" + chr(108) + "o"   # runtime construction
s2 = "hello"
print(s1 == s2, s1 is s2)     # True, False

# Manual interning
s3 = sys.intern("hel" + chr(108) + "o")
s4 = sys.intern("hello")
print(s3 is s4)   # True — both now point to same canonical object
```

## ⚠️ Common Mistakes & Interview Traps
- **"Same module" folding trick**: CPython may intern `"hello world"` within a single `.py` file at compile time, but not across modules or when constructed at runtime. Tests that pass locally can fail in production.
- **`is` for user-supplied strings**: Silently broken. `user_input is "admin"` will always be `False` for runtime strings.
- **`sys.intern` returns the canonical string**: You must use the return value — `sys.intern(s)` doesn't mutate `s` in place.
- **PyPy, Jython, GraalPy**: Different interning rules. Code relying on `is` for strings is non-portable.

## 🔗 Related Concepts
- python_core/016_hash_eq — __hash__ and object identity
- python_core/010_memory_model_gc — CPython reference counting
- python_core/036_closure_cells — LEGB lookup and name binding

## 📚 Go Deeper
- CPython `Objects/unicodeobject.c` — `PyUnicode_InternInPlace()`
- PEP 3120 — UTF-8 as default source encoding (affects which chars trigger interning)
