# Context Managers & `contextlib`

## 🎯 Interview Question
Explain how the `with` statement works under the hood. How do you implement a context manager using both the class protocol and `contextlib.contextmanager`? What happens when an exception is raised inside a `with` block?

## 💡 Short Answer (30 seconds)
The `with` statement calls `__enter__` on entry and `__exit__` on exit — even if an exception occurs. `__exit__` receives the exception info and can suppress it by returning a truthy value. `contextlib.contextmanager` converts a generator function into a context manager: code before `yield` is `__enter__`, code after is `__exit__`. Use context managers to guarantee resource cleanup, manage transactions, and isolate side effects.

## 🔬 Deep Explanation

### The Protocol
```python
with expr as target:
    body
```
Is roughly equivalent to:
```python
mgr = expr
target = mgr.__enter__()
try:
    body
except:
    if not mgr.__exit__(*sys.exc_info()):
        raise
else:
    mgr.__exit__(None, None, None)
```

### `__exit__` signature
`__exit__(self, exc_type, exc_val, exc_tb)`:
- Called with `(None, None, None)` on normal exit
- Called with exception info on exception exit
- Return `True` (or truthy) to **suppress** the exception
- Return `False`/`None` to **propagate** it

Suppressing exceptions is powerful but dangerous — typically only used in specific retry/ignore-list scenarios.

### `contextlib.contextmanager`
Converts a generator function into a context manager via `@contextmanager`:
```python
@contextmanager
def managed():
    setup()
    try:
        yield value   # becomes the 'as' target
    except SomeError:
        handle()      # can suppress by not re-raising
    finally:
        teardown()    # guaranteed cleanup
```
The generator must `yield` exactly once. If it yields 0 or 2+ times, `RuntimeError` is raised.

### `contextlib.asynccontextmanager`
Same pattern for async context managers (`async with`), using `async def` + `yield`.

### Nested context managers
Python 3.10+ supports parenthesized `with` for clarity:
```python
with (open("a") as f, open("b") as g, lock):
    ...
```

### `contextlib.ExitStack`
For dynamic numbers of context managers — push context managers at runtime and they're all cleaned up on exit. Critical for "open N files where N is unknown at code time."

### `contextlib.suppress(*exceptions)`
Clean idiom for "ignore these specific exceptions":
```python
with suppress(FileNotFoundError):
    os.remove("temp.txt")
```

### Production patterns
- **Database transactions**: enter opens txn, normal exit commits, exception rolls back
- **Distributed locks** (Redis `SET NX EX`): enter acquires, exit releases
- **Profiling/timing**: capture start time in `__enter__`, log duration in `__exit__`
- **Mocking in tests**: `unittest.mock.patch` is a context manager
- **Temporary directory/file**: `tempfile.TemporaryDirectory`

## 💻 Code Example

```python
import time
import contextlib

class Timer:
    """Class-based context manager for timing a block."""

    def __enter__(self):
        self._start = time.perf_counter()
        return self  # 'as' target

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self._start
        # Return False (don't suppress exceptions)
        return False


@contextlib.contextmanager
def database_transaction(conn):
    """Generator-based transaction manager."""
    txn = conn.begin()
    try:
        yield txn          # caller operates on txn
        conn.commit()      # only reached if no exception
    except Exception:
        conn.rollback()    # exception → rollback
        raise              # re-raise (don't suppress)
    finally:
        txn.close()        # always runs


@contextlib.contextmanager
def suppress_and_log(logger, *exc_types):
    """Suppress specific exceptions and log them."""
    try:
        yield
    except exc_types as e:
        logger.warning(f"Suppressed {type(e).__name__}: {e}")
        # Return from contextmanager suppresses the exception


# ExitStack for dynamic resources
def process_files(paths):
    with contextlib.ExitStack() as stack:
        files = [stack.enter_context(open(p)) for p in paths]
        return [f.read() for f in files]
        # All files closed on exit, even if open() fails midway
```

## ⚠️ Common Mistakes & Interview Traps

1. **`__exit__` return value**: Not returning `True` when you want to suppress is the classic bug. The default `return None` propagates exceptions.

2. **`@contextmanager` without `try/finally`**: If the generator doesn't wrap `yield` in `try/finally`, cleanup code won't run if an exception is raised in the `with` block.

3. **Multiple `yield` in `@contextmanager`**: The generator must yield exactly once. A second yield causes `RuntimeError: generator didn't stop after throw()`.

4. **`as` target vs return value confusion**: `__enter__` returns the target (not `self` necessarily). `open()` returns `self`, but `lock.__enter__()` returns the lock, and some managers return something else entirely (e.g., `subprocess.Popen`).

5. **Not using context managers for DB sessions**: Opening a DB connection without a context manager leads to connection leaks. SQLAlchemy's `Session` is a context manager for this reason.

## 🔗 Related Concepts
- `python_core/008_generators_internals` — `@contextmanager` is built on generators
- `databases/` — SQLAlchemy sessions and transactions use context managers
- `unit_tests/` — `unittest.mock.patch` is a context manager

## 📚 Go Deeper
- `contextlib` module docs — `AsyncExitStack`, `redirect_stdout`, `nullcontext`
- PEP 343 — "The 'with' statement" — original design rationale
