# Descriptors (`__get__`, `__set__`, `__delete__`)

## 🎯 Interview Question
What is a Python descriptor? Explain the descriptor protocol, the difference between data and non-data descriptors, and give a real-world use case where you'd implement one over using a property.

## 💡 Short Answer (30 seconds)
A descriptor is any object that defines `__get__`, `__set__`, or `__delete__`. When placed as a class attribute, Python calls these methods instead of returning/setting the attribute directly. Properties, classmethods, staticmethods, and `__slots__` are all implemented via descriptors. You write custom descriptors when you need reusable attribute logic — like type validation, lazy loading, or access logging — across many classes.

## 🔬 Deep Explanation

### The Descriptor Protocol
Attribute lookup on `obj.attr` follows this chain (simplified):
1. `type(obj).__mro__` is searched for `attr`
2. If found on a class and it's a **data descriptor** (`__get__` + `__set__`/`__delete__`), call `__get__`
3. Otherwise check `obj.__dict__['attr']`
4. If found on a class and it's a **non-data descriptor** (only `__get__`), call `__get__`
5. Raise `AttributeError`

### Data vs Non-data Descriptors

| Type | Defines | Priority vs instance `__dict__` |
|------|---------|----------------------------------|
| Data descriptor | `__get__` + `__set__` (and/or `__delete__`) | **Higher** — overrides instance dict |
| Non-data descriptor | Only `__get__` | **Lower** — instance dict wins |

**Implication**: A property is a data descriptor. If you do `obj.x = 5`, Python calls `property.__set__`, not `obj.__dict__['x'] = 5`. A regular method is a non-data descriptor — that's why `obj.method = lambda: None` can shadow a class method in the instance dict.

### `__set_name__` (Python 3.6+)
When a descriptor is assigned as a class body attribute, Python calls `descriptor.__set_name__(owner_cls, attr_name)`. This lets the descriptor know which attribute name it's managing — critical for validation descriptors that need to store per-instance values without hardcoding the attribute name.

### How `property` is a descriptor
```python
# property is roughly equivalent to:
class property:
    def __init__(self, fget=None, fset=None, fdel=None):
        self.fget, self.fset, self.fdel = fget, fset, fdel
    def __get__(self, obj, objtype=None):
        if obj is None: return self  # class access → return descriptor
        return self.fget(obj)
    def __set__(self, obj, value):
        self.fset(obj, value)
    def __delete__(self, obj):
        self.fdel(obj)
```

### `obj is None` check
When the descriptor is accessed on the class itself (`MyClass.attr`), `obj` is `None`. Descriptors should return `self` in this case to allow introspection.

### Real-world use cases
- **ORM field types** (SQLAlchemy `Column`, Django `Field`) — validate, coerce, track dirty state
- **Lazy properties** — compute expensive values once and cache in `obj.__dict__`
- **Type-checked attributes** — enforce types without repeating validation logic
- **Audit logging** — record every write to a sensitive field

## 💻 Code Example

```python
class TypedField:
    """Reusable type-checking descriptor. Works on any class."""

    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = f"_{name}"  # store value in obj.__dict__

    def __init__(self, expected_type):
        self.expected_type = expected_type

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self  # class-level access
        return getattr(obj, self.private_name, None)

    def __set__(self, obj, value):
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"{self.public_name} must be {self.expected_type.__name__}, "
                f"got {type(value).__name__}"
            )
        setattr(obj, self.private_name, value)


class LazyProperty:
    """Non-data descriptor: compute once, cache in instance __dict__."""

    def __init__(self, func):
        self.func = func
        self.attr_name = None

    def __set_name__(self, owner, name):
        self.attr_name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        # Store result in instance __dict__ — shadows this non-data descriptor
        value = self.func(obj)
        obj.__dict__[self.attr_name] = value
        return value


class User:
    name = TypedField(str)
    age = TypedField(int)

    def __init__(self, name, age):
        self.name = name  # calls TypedField.__set__
        self.age = age

    @LazyProperty
    def initials(self):
        print("    (computing initials...)")
        return "".join(p[0].upper() for p in self.name.split())
```

## ⚠️ Common Mistakes & Interview Traps

1. **Storing value on `self` (the descriptor), not `obj`**: A descriptor is a class-level object shared by all instances. `self.value = x` in `__set__` stores ONE value for ALL instances. Always store on `obj`.

2. **Forgetting `__set__` makes it a data descriptor**: Adding `__set__` changes lookup priority. If you only need `__get__`, don't add `__set__` — let instance `__dict__` win (lazy caching pattern).

3. **Forgetting `if obj is None: return self`**: Without this, `MyClass.attr` crashes instead of returning the descriptor object.

4. **`__set_name__` not called on manual assignment**: `MyClass.attr = MyDescriptor()` after class creation does NOT call `__set_name__`. Only class body definitions trigger it.

5. **Confusing `property` with descriptor**: `property` IS a descriptor. Understanding this is the senior-level answer; just saying "use `@property`" is the junior answer.

## 🔗 Related Concepts
- `python_core/001_new_vs_init` — `__new__` can be used to configure descriptors
- `python_core/004_metaclasses` — metaclasses use `__set_name__` implicitly
- `python_core/006_slots` — `__slots__` are implemented via member descriptors

## 📚 Go Deeper
- Raymond Hettinger's "Descriptor HowTo Guide" in Python docs
- CPython source: `Objects/object.c` — `_PyObject_GenericGetAttrWithDict`
