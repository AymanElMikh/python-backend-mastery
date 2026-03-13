# The Python Import System — `importlib`, `sys.modules`, Circular Imports

## 🎯 Interview Question
Walk me through what happens when Python executes `import mymodule`. What is `sys.modules`, how does `importlib` fit in, and how do circular imports work and fail? How would you implement a custom importer?

## 💡 Short Answer (30 seconds)
`import mymodule` triggers the import machinery: Python checks `sys.modules` first (the module cache) — if found, returns it immediately. Otherwise it uses a chain of **finders** and **loaders** from `sys.meta_path` to find the file, create a module object, add it to `sys.modules` (before executing), then execute the file. Circular imports work only up to the point where the partially-initialized module was added to `sys.modules` — any name not yet defined in the circular dependency raises `ImportError` or `AttributeError`.

## 🔬 Deep Explanation

### The import pipeline
1. `import foo` → calls `__import__('foo')`
2. Checks `sys.modules['foo']` — if present, returns cached module (even if partially initialized!)
3. Iterates `sys.meta_path` finders: `BuiltinImporter`, `FrozenImporter`, `PathFinder`
4. Finder returns a `ModuleSpec` (name, loader, origin path, submodule search locations)
5. `importlib._bootstrap._load(spec)` creates the module object, inserts it into `sys.modules`, then calls `loader.exec_module(module)` to execute the file
6. Module is fully initialized and returned

The critical detail: **the module is added to `sys.modules` BEFORE execution**. This is what makes circular imports partially work.

### `sys.modules` — the module cache
`sys.modules` is a plain dict: `{name: module_object}`. Consequences:
- `import foo` is O(1) after the first import — just a dict lookup
- You can inject fake modules: `sys.modules['foo'] = FakeModule()`
- You can force re-import: `del sys.modules['foo']; import foo`
- You can inspect import state: `'foo' in sys.modules`

### Circular imports — why they partially fail
```
# a.py
from b import B_THING   # imports b, which imports a...

# b.py
from a import A_THING   # a is in sys.modules but A_THING not defined yet!
```
When `a.py` starts: `a` is added to `sys.modules` immediately. Then `from b import B_THING` triggers `b.py`. `b.py` does `from a import A_THING` — Python finds `a` in `sys.modules` (partially initialized), looks for `A_THING` in it — not there yet → `ImportError`.

**Fix**: import the module, not the name. `import a; a.A_THING` defers the attribute lookup to call time, not import time.

### `sys.meta_path` finders
Each finder has `find_spec(name, path, target)` → returns `ModuleSpec` or `None`. Custom finders let you import from:
- Databases
- Zip files
- Remote URLs
- Encrypted bundles

### `importlib` — the public API
- `importlib.import_module('foo.bar')` — programmatic import
- `importlib.reload(module)` — re-execute a module in-place
- `importlib.util.spec_from_file_location(name, path)` — load from arbitrary path
- `importlib.util.module_from_spec(spec)` — create module object

### `__init__.py` and packages
A directory with `__init__.py` is a package. `import pkg.sub` imports `pkg/__init__.py` first, then `pkg/sub.py`. Namespace packages (Python 3.3+, PEP 420) work without `__init__.py`.

### `__all__` and `from module import *`
`__all__` controls what `from module import *` exports. Without it, `*` imports all names not starting with `_`. Defining `__all__` is a best practice for library modules.

### Lazy imports (Python 3.12+ importlib.util)
`importlib.util.LazyLoader` wraps a loader to defer module execution until first attribute access. Speeds up startup for large applications with many rarely-used imports.

## 💻 Code Example

```python
import sys
import importlib
import importlib.util
import types

# Inject a fake module
fake = types.ModuleType('fake_redis')
fake.get = lambda key: f"cached:{key}"
sys.modules['fake_redis'] = fake

import fake_redis
print(fake_redis.get('user:1'))  # "cached:user:1"

# Programmatic import from a file path
spec = importlib.util.spec_from_file_location(
    "my_plugin",
    "/path/to/plugin.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules["my_plugin"] = module
spec.loader.exec_module(module)

# Force reload (dangerous in production)
import json
importlib.reload(json)

# Custom meta_path finder
class PrefixFinder:
    """Intercepts import of 'mock_*' modules."""
    def find_spec(self, name, path, target=None):
        if name.startswith('mock_'):
            return importlib.util.spec_from_loader(
                name, loader=MockLoader(name)
            )
        return None
```

## ⚠️ Common Mistakes & Interview Traps

1. **Circular import with `from x import name`**: This looks up `name` at import time on the partially-initialized module. Use `import x` and access `x.name` at call time.

2. **`importlib.reload` doesn't update existing references**: `reload(foo)` re-executes `foo.py` and updates `sys.modules['foo']`. But any variable `bar = foo.MyClass` that was set before reload still points to the old class.

3. **`sys.modules` is shared across threads**: There's no lock around `sys.modules` access in CPython (beyond the GIL). During module initialization, a second thread may get a partially-initialized module from the cache.

4. **`__init__.py` implicit imports**: Importing a sub-module (`from pkg.sub import X`) imports `pkg/__init__.py` first. Side effects in `__init__.py` run on every first import of any submodule.

5. **Namespace packages and `__path__`**: Namespace packages can span multiple directories. The `__path__` attribute controls where submodule searches look. Modifying `__path__` at runtime changes submodule resolution.

## 🔗 Related Concepts
- `python_core/004_metaclasses` — `importlib` uses metaclasses internally for module types
- `python_core/009_decorator_internals` — module-level decorators run at import time
- `devops_backend/` — virtual environments and `sys.path` manipulation

## 📚 Go Deeper
- PEP 302 — "New Import Hooks" — the meta_path and path_hooks system
- PEP 451 — `ModuleSpec` — the modern import spec design
- Brett Cannon's "How Import Works" talk (PyCon)
