"""
Demo: The Python Import System — sys.modules, importlib, circular imports
Run:  python demo.py
"""

import sys
import importlib
import importlib.util
import types

# ── Section 1: sys.modules — the import cache ─────────────────────────────────
def show_sys_modules():
    # json is already imported by the time we access it
    import json
    print(f"  'json' in sys.modules: {'json' in sys.modules}")
    print(f"  sys.modules['json'] is json: {sys.modules['json'] is json}")

    # Injecting a fake module
    fake = types.ModuleType('totally_real_redis')
    fake.get = lambda key: f"FAKE:{key}"
    fake.set = lambda key, val: None
    sys.modules['totally_real_redis'] = fake

    import totally_real_redis
    print(f"  Injected fake module: totally_real_redis.get('user') = {totally_real_redis.get('user')!r}")


# ── Section 2: importlib.import_module — programmatic imports ─────────────────
def show_programmatic_import():
    # Same as 'import json' but string-driven
    json_mod = importlib.import_module('json')
    print(f"  importlib.import_module('json').__name__ = {json_mod.__name__!r}")

    # Submodule import
    html_parser = importlib.import_module('html.parser')
    print(f"  importlib.import_module('html.parser').__name__ = {html_parser.__name__!r}")

    # Relative import equivalent
    os_path = importlib.import_module('os.path')
    print(f"  importlib.import_module('os.path') = {os_path.__name__!r}")


# ── Section 3: Custom meta_path finder ───────────────────────────────────────
class MockModuleFinder:
    """Intercepts 'stub_*' imports and returns an auto-generated stub module."""

    def find_spec(self, fullname, path, target=None):
        if fullname.startswith('stub_'):
            return importlib.util.spec_from_loader(fullname, MockModuleLoader(fullname))
        return None


class MockModuleLoader:
    def __init__(self, name):
        self.name = name

    def create_module(self, spec):
        return None  # use default

    def exec_module(self, module):
        # Auto-generate stub attributes
        service_name = self.name.replace('stub_', '')
        module.NAME = service_name
        module.connect = lambda: f"Mock connection to {service_name}"
        module.query  = lambda q: f"Mock result for: {q}"


# ── Section 4: Circular import simulation ────────────────────────────────────
def demonstrate_circular():
    """
    Simulate what happens during circular imports without actually creating
    circular files. Shows the sys.modules partial-init mechanism.
    """
    # Create a module and add to sys.modules BEFORE fully initializing
    partial_mod = types.ModuleType('partial_module')
    sys.modules['partial_module'] = partial_mod  # added early!

    # Now try to access something not yet set
    try:
        val = sys.modules['partial_module'].NOT_YET_DEFINED
    except AttributeError as e:
        print(f"  Accessing not-yet-set attr on partial module: AttributeError: {e}")
        print("  This is exactly what happens in circular imports!")

    # Now 'finish' initializing the module
    partial_mod.VALUE = 42
    print(f"  After full init: partial_module.VALUE = {sys.modules['partial_module'].VALUE}")


# ── Section 5: inspect module metadata ───────────────────────────────────────
def show_module_metadata():
    import os
    import json

    for mod in [os, json]:
        print(f"  {mod.__name__}:")
        print(f"    __file__    = {getattr(mod, '__file__', 'N/A')}")
        print(f"    __loader__  = {type(mod.__loader__).__name__}")
        print(f"    __spec__    = {mod.__spec__.name if mod.__spec__ else 'N/A'}")
        print(f"    __package__ = {mod.__package__!r}")


# ── Section 6: importlib.reload — doesn't update existing references ──────────
def demonstrate_reload():
    import json
    original_dumps = json.dumps  # grab a reference

    importlib.reload(json)  # re-execute json module

    print(f"  json.dumps is original_dumps: {json.dumps is original_dumps}")
    print("  Reload replaces module attrs, but old references still point to old objects")
    print("  This is why 'reload' is dangerous in production plugin systems")


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: The Python Import System")
    print("=" * 55)

    print("\n[1] sys.modules — the import cache:")
    show_sys_modules()

    print("\n[2] importlib.import_module — programmatic:")
    show_programmatic_import()

    print("\n[3] Custom meta_path finder (stub_* modules):")
    sys.meta_path.insert(0, MockModuleFinder())
    import stub_payments
    import stub_notifications
    print(f"  stub_payments.NAME = {stub_payments.NAME!r}")
    print(f"  stub_payments.connect() = {stub_payments.connect()!r}")
    print(f"  stub_notifications.query('pending') = {stub_notifications.query('pending')!r}")
    sys.meta_path.pop(0)  # cleanup

    print("\n[4] Circular import — partial module in sys.modules:")
    demonstrate_circular()

    print("\n[5] Module metadata:")
    show_module_metadata()

    print("\n[6] importlib.reload — old references not updated:")
    demonstrate_reload()

    print("\n[7] sys.path — where Python looks for modules:")
    print(f"  First 3 entries: {sys.path[:3]}")
    print(f"  Total entries:   {len(sys.path)}")

    print("\n" + "=" * 55)
