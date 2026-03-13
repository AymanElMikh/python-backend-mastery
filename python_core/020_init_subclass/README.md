# `__init_subclass__` & Class Creation Hooks

## 🎯 Interview Question
What is `__init_subclass__` and when was it introduced? How does it compare to a metaclass for enforcing constraints on subclasses or auto-registering them? What are `__class_getitem__` and `__set_name__`, and where are they useful?

## 💡 Short Answer (30 seconds)
`__init_subclass__` (Python 3.6, PEP 487) is called on the parent class whenever a subclass is created. It replaces 80% of metaclass use cases — auto-registering plugins, enforcing conventions, injecting behavior — without the metaclass conflict risk. `__class_getitem__` enables `MyClass[T]` syntax for generics. `__set_name__` is called on descriptors when the descriptor is assigned as a class attribute, telling it its own name.

## 🔬 Deep Explanation

### `__init_subclass__` — the modern metaclass alternative
When Python creates a class, after `type.__new__` finishes, it calls `parent.__init_subclass__(cls, **kwargs)` for each parent that defines it. The `**kwargs` come from the class definition line:

```python
class Plugin(Base, plugin_type="csv", version=2):
    pass
# triggers: Base.__init_subclass__(Plugin, plugin_type="csv", version=2)
```

Key properties:
- Called on the *parent* class, receiving the *newly created* subclass
- Runs after `type.__new__` so the class is fully formed
- Must call `super().__init_subclass__(**kwargs)` — critical for cooperative multiple inheritance
- Cannot modify the class namespace (that's what `__prepare__` in metaclasses does)

### Use cases

**Plugin registration:**
```python
class Handler(ABC):
    _registry: dict[str, type] = {}

    def __init_subclass__(cls, event_type: str = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if event_type:
            Handler._registry[event_type] = cls

class LoginHandler(Handler, event_type="login"):
    def handle(self, event): ...
```

**Constraint enforcement:**
```python
class Model(ABC):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'table_name'):
            raise TypeError(f"{cls.__name__} must define 'table_name'")
```

**Auto-injection of behavior:**
```python
class Loggable:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        original_init = cls.__init__ if '__init__' in cls.__dict__ else None
        # wrap __init__ to log creation...
```

### `__class_getitem__` — subscript syntax for classes
Called when you write `MyClass[T]`. Returns whatever you want — typically a `GenericAlias` or specialized type. Python's built-in `list`, `dict`, `tuple` support this since 3.9.

```python
class TypedList:
    def __class_getitem__(cls, item_type):
        return f"{cls.__name__}[{item_type.__name__}]"

TypedList[int]   # "TypedList[int]"
TypedList[str]   # "TypedList[str]"
```

For real generic classes, inherit from `Generic[T]` — it implements `__class_getitem__` for you.

### `__set_name__` — descriptor self-awareness
When a descriptor is defined in a class body, Python (via `type.__new__`) calls `descriptor.__set_name__(owner_cls, attr_name)`. This lets the descriptor know:
- Which class it belongs to (`owner`)
- What attribute name it was assigned to (`name`)

Without `__set_name__`, descriptors had to be told their name explicitly.

```python
class Validated:
    def __set_name__(self, owner, name):
        self.name = name
        self.storage_name = f'_{name}'
```

### Class creation timeline (complete)
1. Determine metaclass
2. Call `metaclass.__prepare__(name, bases)` → namespace dict
3. Execute class body in that namespace
4. Call `metaclass(name, bases, namespace)` → calls `type.__new__` which:
   a. Creates the class object
   b. Calls `descriptor.__set_name__(cls, name)` for each descriptor
   c. Calls `parent.__init_subclass__(cls, **kwargs)` for each parent
5. Call `metaclass.__init__(cls, name, bases, namespace)`

### Cooperative `__init_subclass__`
Always pass `**kwargs` to `super().__init_subclass__(**kwargs)` — other classes in the MRO may use the kwargs. If you consume a kwarg (`plugin_type = kwargs.pop('plugin_type', None)`), remove it before calling super.

## 💻 Code Example

```python
from abc import ABC, abstractmethod

class EventHandler(ABC):
    """Plugin base using __init_subclass__ for registration."""
    _registry: dict[str, type] = {}

    def __init_subclass__(cls, event_type: str = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if event_type:
            EventHandler._registry[event_type] = cls

    @classmethod
    def dispatch(cls, event_type: str, payload: dict):
        handler_cls = cls._registry.get(event_type)
        if not handler_cls:
            raise ValueError(f"No handler for event: {event_type!r}")
        return handler_cls().handle(payload)

    @abstractmethod
    def handle(self, payload: dict) -> str: ...

class UserSignupHandler(EventHandler, event_type="user.signup"):
    def handle(self, payload): return f"Welcome {payload['name']}!"

class OrderPlacedHandler(EventHandler, event_type="order.placed"):
    def handle(self, payload): return f"Order #{payload['id']} confirmed"
```

## ⚠️ Common Mistakes & Interview Traps

1. **Not calling `super().__init_subclass__(**kwargs)`**: The most common bug. Other classes in the MRO may define `__init_subclass__` too. Not calling super breaks the cooperative chain and silently ignores their hooks.

2. **`__init_subclass__` runs even for abstract subclasses**: If your base class has `@abstractmethod` and a direct subclass doesn't implement them, `__init_subclass__` still fires — the `TypeError` only comes at instantiation.

3. **`__class_getitem__` vs `Generic`**: If you just want `MyClass[T]` to work for type-hint purposes, inherit from `Generic[T]`. Only implement `__class_getitem__` yourself if you need custom behavior (like returning a different class).

4. **`__set_name__` not called after class creation**: Assigning a descriptor after class creation (`MyClass.attr = MyDescriptor()`) does NOT trigger `__set_name__`. The descriptor won't know its name.

5. **Forgetting kwargs in intermediate classes**: In a multi-level hierarchy where each class uses `__init_subclass__` kwargs, an intermediate class that doesn't pass `**kwargs` to super will cause `TypeError: __init_subclass__() got unexpected keyword argument` in the base class.

## 🔗 Related Concepts
- `python_core/004_metaclasses` — `__init_subclass__` replaces most metaclass use cases
- `python_core/003_descriptors` — `__set_name__` is the descriptor self-registration hook
- `python_core/013_abc_abstract` — `ABCMeta` combines metaclass + `__init_subclass__`-like logic

## 📚 Go Deeper
- PEP 487 — "Simpler customization of class creation" — introduces `__init_subclass__` and `__set_name__`
- Python docs: "Customizing class creation" — full class creation protocol
