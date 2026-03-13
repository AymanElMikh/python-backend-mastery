# Python Memory Model & Garbage Collection

## 🎯 Interview Question
How does CPython manage memory? Explain reference counting, the cyclic garbage collector, and `__del__`. When does reference counting fail, and how does the GC resolve it? What are common memory leak patterns in Python backends?

## 💡 Short Answer (30 seconds)
CPython uses **reference counting** as its primary memory manager: every object has a `ob_refcnt` field; when it hits 0, the object is immediately freed. But reference counting can't detect cycles — two objects referencing each other never reach refcount 0. The **cyclic garbage collector** (`gc` module) runs periodically to detect and break cycles. `__del__` finalizers and `weakref` interact with both mechanisms in non-obvious ways.

## 🔬 Deep Explanation

### Reference Counting
Every `PyObject` has:
- `ob_refcnt` — reference count
- `ob_type` — pointer to type object

`Py_INCREF` increments, `Py_DECREF` decrements. When `ob_refcnt` drops to 0:
1. `tp_dealloc` is called (the type's destructor)
2. Memory is returned to CPython's internal allocator (`pymalloc`) or the OS

This is **deterministic** — objects are freed the instant the last reference drops. No "stop the world" pause. This is why Python is popular for systems programming despite having GC.

### Reference counting fails with cycles
```python
a = []
b = [a]
a.append(b)  # a → b → a — circular reference
del a, del b
# Both refcounts drop from 2 to 1, not 0 — memory leaked
```
A self-referencing object (`obj.self = obj`) has the same problem.

### The Cyclic Garbage Collector (gc module)
CPython tracks all "container" objects (lists, dicts, sets, custom objects with `__dict__`) in doubly-linked generational lists. The GC runs periodically and:
1. Marks all objects in the tracked set
2. Subtracts the internal references (references from within the cycle)
3. Objects with no external references remaining → cycle → collected

Three generations (0, 1, 2). Young objects (gen 0) are collected most frequently. Objects that survive gen 0 move to gen 1, etc. (generational hypothesis: most objects die young).

`gc.collect()` — force a full collection
`gc.get_count()` — `(gen0, gen1, gen2)` allocation counters
`gc.disable()` — disable the cyclic GC (CPython still does refcounting; only cycle detection disabled)

### `__del__` — finalizers
`__del__` is called just before an object is destroyed. **Pitfalls**:
- If two objects in a cycle both have `__del__`, CPython historically couldn't safely order their destruction → they were placed in `gc.garbage` (a list of uncollectable objects). Fixed in Python 3.4 via PEP 442 — now `__del__` is called even for cyclic garbage, in a safe order.
- `__del__` can resurrect an object by storing `self` somewhere — this prevents destruction (once).
- `__del__` is not guaranteed to run at interpreter shutdown.

### `weakref` — non-owning references
`weakref.ref(obj)` creates a reference that doesn't increment `ob_refcnt`. When the referent is destroyed, the weak ref becomes `None`. Essential for:
- Caches that shouldn't prevent GC
- Observer patterns (observers don't keep subjects alive)
- `__slots__` + `__weakref__` for slotted objects

### Memory arenas and `pymalloc`
CPython doesn't call `malloc` for every small allocation. Objects ≤ 512 bytes go through `pymalloc` — a slab allocator organized as pools → arenas. Memory is rarely returned to the OS even after Python objects are freed (CPython keeps the pools for reuse). This can cause apparent memory growth in long-running services.

### Common backend memory leaks
1. **Global caches without eviction** — `dict` accumulating session data
2. **Circular references with `__del__`** — pre-3.4
3. **C extension leaks** — `Py_DECREF` not called on error paths
4. **SQLAlchemy sessions not closed** — ORM keeps mapped objects alive
5. **Thread-local storage** — data in `threading.local()` lives until thread dies
6. **Large tracebacks** — `sys.exc_info()` keeps the frame (and all locals) alive

### Profiling tools
- `tracemalloc` — stdlib; trace allocation sites
- `objgraph` — visualize object references (external lib)
- `gc.get_objects()` — list all tracked objects
- `sys.getrefcount(obj)` — refcount (note: +1 for the getrefcount call itself)

## 💻 Code Example

```python
import gc
import sys
import weakref

# Reference counting
x = [1, 2, 3]
print(sys.getrefcount(x))  # 2: x + the getrefcount argument

y = x
print(sys.getrefcount(x))  # 3: x, y, getrefcount

del y
print(sys.getrefcount(x))  # 2 again

# Cycle creation and detection
class Node:
    def __init__(self, name):
        self.name = name
        self.ref = None

a = Node("a"); b = Node("b")
a.ref = b; b.ref = a  # cycle
del a, del b           # refcounts drop to 1, not 0 — cycle persists

gc.collect()           # cyclic GC detects and clears the cycle

# Weak references for caches
class Cache:
    def __init__(self):
        self._cache = weakref.WeakValueDictionary()

    def get_or_create(self, key, factory):
        obj = self._cache.get(key)
        if obj is None:
            obj = factory()
            self._cache[key] = obj
        return obj
```

## ⚠️ Common Mistakes & Interview Traps

1. **`sys.getrefcount` returns count+1**: The function call itself creates a temporary reference. `sys.getrefcount(x) == 2` means there's only one external reference (x).

2. **Assuming `del` frees memory**: `del x` decrements the refcount. Memory is freed only if refcount reaches 0. In a cycle, `del` doesn't free.

3. **`__del__` for cleanup in cycles** (pre-3.4): Objects with `__del__` in cycles ended up in `gc.garbage` permanently. Fixed in Python 3.4, but be aware of legacy code.

4. **`gc.disable()` for performance**: Disabling the cyclic GC is sometimes done in batch scripts that create no cycles. Never do this in a long-running service without understanding the memory implications.

5. **Frame retention via exceptions**: `try: ... except Exception as e: ...` — after the `except` block, `e` is deleted, but if you store `sys.exc_info()`, the traceback keeps the entire frame (and all locals) alive.

## 🔗 Related Concepts
- `python_core/001_new_vs_init` — `tp_dealloc` is the C-level `__del__`
- `python_core/006_slots` — slots interact with the GC tracking list
- `python_core/003_descriptors` — descriptor objects are GC-tracked containers

## 📚 Go Deeper
- CPython source: `Modules/gcmodule.c` — the full generational GC implementation
- PEP 442 — "Safe object finalization" — the fix for `__del__` in cycles
