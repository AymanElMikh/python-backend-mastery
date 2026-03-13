# `__hash__` and `__eq__` — The Hashability Contract

## 🎯 Interview Question
What is the contract between `__hash__` and `__eq__` in Python? What happens to `__hash__` when you define `__eq__`? When can two objects that are not equal have the same hash, and when must equal objects have the same hash?

## 💡 Short Answer (30 seconds)
The contract: objects that compare equal MUST have the same hash. The converse is NOT required — hash collisions are allowed. When you define `__eq__` without `__hash__`, Python sets `__hash__ = None`, making the class unhashable — because it can no longer guarantee the contract. You must define both, or use `frozen=True` in `@dataclass`, or explicitly set `__hash__` via `unsafe_hash=True`.

## 🔬 Deep Explanation

### Why the contract exists
Hash tables (Python's `dict` and `set`) use hash values to determine which bucket an object lands in. Equality is used to resolve collisions within a bucket. The algorithm:
1. `hash(key)` → bucket index
2. Check `key == stored_key` for each item in that bucket

If two equal objects had different hashes, they'd land in different buckets and a dict lookup `d[obj]` would fail even if `d[equal_obj]` existed. This is why: **equal objects must hash equally**.

The reverse — different objects having the same hash — is a collision. It degrades performance (O(n) in worst case) but is never a correctness issue.

### Default behavior
- `object.__hash__`: returns `id(obj) // 16` — unique per object identity
- `object.__eq__`: returns `self is other` — identity comparison

### When you define `__eq__`:
- Python automatically sets `__hash__ = None` (unhashable)
- Rationale: you've broken identity-based equality, so the identity-based hash is no longer valid
- Fix: explicitly define `__hash__` alongside `__eq__`

### What makes a good hash function
1. **Consistent**: same object → same hash for its lifetime (while in a dict/set)
2. **Equal objects → equal hashes** (the contract)
3. **Fast to compute**
4. **Distributes well** — minimizes collisions

The standard pattern: `hash(tuple_of_fields)`.

### Mutable objects and hashability
Mutable objects should generally NOT be hashable — because mutating them changes their equality, but if they're in a dict/set, the hash doesn't update. This is why `list` is unhashable but `tuple` is. This is why `dict` is unhashable but `frozenset` is.

### `__hash__` returning `None`
Setting `__hash__ = None` on a class makes `hash(instance)` raise `TypeError: unhashable type`. This is intentional and different from "returns None" — it's a sentinel that disables hashing.

### `unsafe_hash=True` in `@dataclass`
Forces hash generation even with mutable fields. Named "unsafe" because mutating a field after inserting into a dict/set violates the contract. Use only when you KNOW instances won't be mutated while in a hash collection.

### Value objects and the contract
Value objects (representing concepts like `Money`, `Color`, `IP`) should implement `__eq__` and `__hash__` together:
```python
class Money:
    def __init__(self, amount, currency):
        self.amount = amount
        self.currency = currency

    def __eq__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __hash__(self):
        return hash((self.amount, self.currency))
```

### `NotImplemented` vs `NotImplementedError`
`__eq__` should return `NotImplemented` (the singleton) when it can't compare with the other type — NOT `False`. Python will then try the reflected operation `other.__eq__(self)`. Returning `False` directly preempts this and can cause asymmetric comparisons.

### `__eq__` and inheritance
If a subclass adds fields and inherits `__hash__` from a parent, the hash no longer reflects all equality-relevant fields — silent correctness bug.

## 💻 Code Example

```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented  # NOT False!
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))  # tuple hash — distributes well


class BadPoint:
    """Only defines __eq__ — accidentally unhashable."""
    def __init__(self, x, y):
        self.x = x; self.y = y

    def __eq__(self, other):
        return isinstance(other, BadPoint) and (self.x, self.y) == (other.x, other.y)
    # __hash__ is now None — Python set it to None automatically


# The mutable-in-dict trap
class MutableKey:
    def __init__(self, val):
        self.val = val

    def __eq__(self, other):
        return isinstance(other, MutableKey) and self.val == other.val

    def __hash__(self):
        return hash(self.val)

d = {}
key = MutableKey(1)
d[key] = "found"
key.val = 2           # mutate the key — hash changed!
print(d.get(key))     # None — key is now in the wrong bucket
print(d.get(MutableKey(1)))  # also None — original hash bucket is stale
```

## ⚠️ Common Mistakes & Interview Traps

1. **Returning `False` instead of `NotImplemented` in `__eq__`**: `return False` stops Python from trying the reflected operation. `return NotImplemented` lets Python try `other.__eq__(self)` — essential for cross-type comparisons.

2. **Not updating `__hash__` when adding fields to a subclass**: If `Child(Parent)` adds a field that affects equality, it MUST override `__hash__` too. Silent correctness bug.

3. **Hashing mutable objects**: Using a mutable object as a dict key, then mutating it, causes the object to be "lost" in the dict — it's in the wrong bucket for its new hash.

4. **`@dataclass` default is unhashable**: `@dataclass` with `eq=True` (default) sets `__hash__ = None`. You must use `frozen=True` or `unsafe_hash=True` to get a hashable dataclass.

5. **Hash collisions are O(n)**: If many objects hash to the same value, dict operations degrade from O(1) to O(n). Python 3.3+ added hash randomization (PYTHONHASHSEED) to mitigate hash DoS attacks — `hash("abc")` changes between interpreter runs.

## 🔗 Related Concepts
- `python_core/014_dataclasses_internals` — `frozen=True` / `unsafe_hash=True` interaction
- `python_core/006_slots` — slotted value objects for memory-efficient hashable types
- `data_structures_algorithms/` — hash table implementation, collision resolution

## 📚 Go Deeper
- Python docs: "object.__hash__" — full contract description
- PEP 3107 + data model: why defining `__eq__` sets `__hash__ = None`
