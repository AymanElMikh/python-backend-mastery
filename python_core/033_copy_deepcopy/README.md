# copy & deepcopy — Python's Object Copying Protocol

## 🎯 Interview Question
What is the difference between `copy.copy()` and `copy.deepcopy()`? How do you customize copying behavior for a class that holds both mutable state and external resources like database connections?

## 💡 Short Answer (30 seconds)
`copy.copy()` creates a shallow copy — a new container object but references to the *same* inner objects. `copy.deepcopy()` recursively clones the entire object graph, breaking all shared references. You customize behavior by implementing `__copy__` and `__deepcopy__` — critical for classes that hold resources (sockets, locks, DB sessions) that must not be duplicated.

## 🔬 Deep Explanation
**Shallow copy (`copy.copy`)**
- Creates a new top-level object.
- Inner mutable objects (lists, dicts, custom objects) are *shared*, not cloned.
- Calls `__copy__()` if defined; otherwise falls back to `__reduce_ex__`.

**Deep copy (`copy.deepcopy`)**
- Recursively copies every object in the graph.
- Maintains a *memo* dict (`id → copy`) to handle cycles and avoid infinite recursion.
- Calls `__deepcopy__(memo)` if defined.
- Does NOT copy: modules, functions, classes, `None`, singletons — these are returned as-is.

**Production use cases:**
1. **Config cloning** — deepcopy a base config dict before per-request mutation.
2. **Test isolation** — deepcopy shared fixtures to prevent cross-test pollution.
3. **Undo/redo** — snapshot mutable domain objects.
4. **Thread safety** — pass deep copies to worker threads to avoid shared-state races.

**`__copy__` / `__deepcopy__` protocol:**
```python
def __copy__(self):
    cls = self.__class__
    result = cls.__new__(cls)
    result.__dict__.update(self.__dict__)
    return result

def __deepcopy__(self, memo):
    cls = self.__class__
    result = cls.__new__(cls)
    memo[id(self)] = result       # register BEFORE recursing to handle cycles
    for k, v in self.__dict__.items():
        setattr(result, k, copy.deepcopy(v, memo))
    return result
```

**Resource handle pattern** — exclude non-copyable fields (locks, connections) by rebuilding them:
```python
def __deepcopy__(self, memo):
    new = MyClass.__new__(MyClass)
    memo[id(self)] = new
    new.data = copy.deepcopy(self.data, memo)   # copy state
    new._lock = threading.Lock()                # fresh lock — never copy
    new._conn = None                            # don't copy DB connection
    return new
```

## 💻 Code Example
```python
import copy

original = {"users": [1, 2, 3], "meta": {"v": 1}}

shallow = copy.copy(original)
deep    = copy.deepcopy(original)

original["users"].append(99)

print("shallow['users']:", shallow["users"])  # [1, 2, 3, 99] — shared!
print("deep['users']   :", deep["users"])     # [1, 2, 3]     — independent
```

## ⚠️ Common Mistakes & Interview Traps
- **`dict.copy()` is shallow** — not the same as `deepcopy`. Nested mutables are still shared.
- **Forgetting `memo[id(self)] = result` before recursing** — causes infinite loops on cyclic graphs.
- **Copying threading.Lock** — raises `TypeError`. Always reconstruct non-picklable resources.
- **`__deepcopy__` called once per object**: CPython skips the call if `id(obj)` is already in `memo`, which is why registering early is critical.

## 🔗 Related Concepts
- python_core/010_memory_model_gc — object identity and reference counting
- python_core/031_weakref — weak references and object lifetime
- python_core/008_generators_internals — generator state cannot be deep-copied

## 📚 Go Deeper
- `copy.py` source: the `_reconstruct` fallback path via `__reduce_ex__`
- `pickle` protocol — `__getstate__` / `__setstate__` used by both pickle and deepcopy
