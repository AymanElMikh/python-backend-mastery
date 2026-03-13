"""
Demo: Metaclasses & type
Run:  python demo.py
"""

# ── Section 1: type() is the default metaclass ────────────────────────────────
class Normal:
    x = 42

# Classes are objects; type() reveals the metaclass
def show_type_chain():
    print(f"  type(Normal)     = {type(Normal)}")      # <class 'type'>
    print(f"  type(type)       = {type(type)}")        # <class 'type'> — type is its own metaclass
    print(f"  type(42)         = {type(42)}")          # <class 'int'>
    print(f"  type(int)        = {type(int)}")         # <class 'type'>

    # Dynamic class creation — equivalent to 'class Dyn: x = 10'
    Dyn = type('Dyn', (object,), {'x': 10, 'greet': lambda self: f"hi from {type(self).__name__}"})
    obj = Dyn()
    print(f"  Dynamic class:   Dyn().x = {obj.x}, Dyn().greet() = {obj.greet()!r}")


# ── Section 2: Auto-registering metaclass ─────────────────────────────────────
class PluginMeta(type):
    registry: dict = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if bases:  # skip the base class itself
            mcs.registry[name] = cls
            print(f"  Registered plugin: {name!r}")
        return cls


class BasePlugin(metaclass=PluginMeta):
    def run(self):
        raise NotImplementedError

class CSVPlugin(BasePlugin):
    def run(self): return "parsing CSV"

class JSONPlugin(BasePlugin):
    def run(self): return "parsing JSON"

class XMLPlugin(BasePlugin):
    def run(self): return "parsing XML"


# ── Section 3: Enforcing contracts via metaclass ──────────────────────────────
class ContractMeta(type):
    """Reject class creation if any public method lacks a docstring."""

    def __new__(mcs, name, bases, namespace):
        for attr, val in namespace.items():
            if callable(val) and not attr.startswith('_') and not val.__doc__:
                raise TypeError(
                    f"Class '{name}': method '{attr}' must have a docstring"
                )
        return super().__new__(mcs, name, bases, namespace)


# ── Section 4: __init_subclass__ — the modern alternative ────────────────────
class Event:
    """Modern registration pattern — no metaclass needed."""
    _handlers: dict = {}

    def __init_subclass__(cls, event_type=None, **kwargs):
        super().__init_subclass__(**kwargs)
        if event_type:
            Event._handlers[event_type] = cls
            print(f"  Registered handler: {cls.__name__!r} → event_type={event_type!r}")


class LoginEvent(Event, event_type="login"):
    pass

class LogoutEvent(Event, event_type="logout"):
    pass

class PurchaseEvent(Event, event_type="purchase"):
    pass


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: Metaclasses & type")
    print("=" * 55)

    print("\n[1] type() chain — everything is an object:")
    show_type_chain()

    print("\n[2] Auto-registration via metaclass (PluginMeta):")
    print(f"  Registry: {list(PluginMeta.registry.keys())}")
    for name, cls in PluginMeta.registry.items():
        print(f"    {name}: {cls().run()}")

    print("\n[3] Enforcing docstrings via ContractMeta:")
    try:
        class BadService(metaclass=ContractMeta):
            def process(self):  # no docstring!
                pass
    except TypeError as e:
        print(f"  TypeError caught: {e}")

    class GoodService(metaclass=ContractMeta):
        def process(self):
            """Processes the request."""
            return "ok"
    print(f"  GoodService accepted — GoodService().process() = {GoodService().process()!r}")

    print("\n[4] __init_subclass__ — modern alternative (no metaclass):")
    print(f"  Event._handlers = {list(Event._handlers.keys())}")
    handler_cls = Event._handlers["login"]
    print(f"  Dispatching 'login' → {handler_cls.__name__}")

    print("\n[5] Metaclass conflict demonstration:")
    from abc import ABCMeta
    try:
        # ABCMeta and PluginMeta are both metaclasses — conflict!
        class Conflict(metaclass=type('Combined', (ABCMeta, PluginMeta), {})):
            pass
        print("  Combined metaclass created successfully")
    except TypeError as e:
        print(f"  TypeError: {e}")

    print("\n" + "=" * 55)
