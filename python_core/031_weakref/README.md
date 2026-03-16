# Weak References — weakref Module

## 🎯 Interview Question
What are weak references in Python, when would you use `weakref.WeakValueDictionary` in a production service, and what happens when the last strong reference to an object is dropped?

## 💡 Short Answer (30 seconds)
A weak reference lets you reference an object without preventing its garbage collection. When the last *strong* reference is dropped the GC collects the object and the weak reference becomes `None`. This is critical for caches, listener registries, and circular-reference-heavy graphs where you want automatic eviction without manual bookkeeping.

## 🔬 Deep Explanation
CPython's reference counter only collects an object when its `ob_refcnt` drops to zero. A normal reference increments that counter; a `weakref.ref` does *not*. The `weakref` module hooks into CPython's `tp_weaklistoffset` slot — most built-in types and all user-defined classes support it (except those with `__slots__` that omit `__weakref__`).

**Key containers:**
- `weakref.ref(obj, callback)` — raw weak ref; callable, returns `None` after GC.
- `weakref.WeakValueDictionary` — values are weak; entry evicted automatically.
- `weakref.WeakKeyDictionary` — keys are weak; useful for per-object metadata.
- `weakref.WeakSet` — set whose members can be collected.

**Production patterns:**
1. **Observer/event bus** — store listeners as weak refs so dropped subscribers don't leak.
2. **Memoization cache** — cache expensive objects but let the GC reclaim them under memory pressure.
3. **Object pool / flyweight** — `WeakValueDictionary` as the pool; only alive objects share the pool slot.

**Gotchas:**
- `int`, `str`, `tuple` (small/interned) don't support weak refs by default.
- Lambda/bound-method weak refs die immediately unless you keep the method object alive.
- Callbacks fire *during* GC; avoid allocating new objects there.

## 💻 Code Example
```python
import weakref

class Cache:
    _store: weakref.WeakValueDictionary = weakref.WeakValueDictionary()

    @classmethod
    def get_or_create(cls, key, factory):
        obj = cls._store.get(key)
        if obj is None:
            obj = factory()          # strong ref returned to caller
            cls._store[key] = obj    # only weak ref kept in cache
        return obj

class BigData:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"BigData({self.value})"

# As long as caller holds `a`, cache hit is guaranteed
a = Cache.get_or_create("x", lambda: BigData(42))
b = Cache.get_or_create("x", lambda: BigData(99))   # same object
assert a is b

del a, b   # drop strong refs → GC collects → cache evicts automatically
print(Cache._store.get("x"))   # None
```

## ⚠️ Common Mistakes & Interview Traps
- **Bound method trap**: `weakref.ref(obj.method)` dies instantly because `obj.method` is a temporary object. Use `weakref.WeakMethod` instead.
- **`__slots__` without `__weakref__`**: Adding `__slots__` removes the default `__weakref__` slot — your class becomes non-weakref-able.
- **Assuming thread safety**: `WeakValueDictionary` is *not* thread-safe for compound operations; wrap with a lock.
- **Callback re-entrancy**: The finalizer callback runs inside the GC lock; raising an exception there is silently swallowed.

## 🔗 Related Concepts
- python_core/010_memory_model_gc — reference counting & cyclic GC
- python_core/006_slots — how __slots__ affects __weakref__
- python_core/003_descriptors — WeakValueDictionary uses descriptor protocol internally

## 📚 Go Deeper
- CPython source: `Objects/weakrefobject.c` — `tp_weaklistoffset` mechanics
- `weakref.finalize()` — higher-level alternative to raw callbacks, with atexit integration
