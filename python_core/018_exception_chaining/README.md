# Exception Chaining — `__cause__`, `__context__`, `__suppress_context__`

## 🎯 Interview Question
What is exception chaining in Python? Explain the difference between `raise X from Y` and a bare `raise X` inside an `except` block. How does Python display chained exceptions, and when would you suppress the chain?

## 💡 Short Answer (30 seconds)
When you `raise NewExc from OrigExc`, Python sets `NewExc.__cause__ = OrigExc` and `__suppress_context__ = True` — this is *explicit* chaining. When you `raise NewExc` inside an `except` block, Python sets `NewExc.__context__ = OrigExc` — *implicit* chaining, showing "during handling of the above exception, another exception occurred." Use `raise NewExc from None` to suppress the chain when the original exception is an implementation detail you don't want to expose.

## 🔬 Deep Explanation

### Three exception attributes
Every exception instance has:
- `__cause__` — set by `raise X from Y`. Indicates the new exception was *caused by* the original.
- `__context__` — automatically set when an exception is raised while another is active. The "while handling X, Y occurred" case.
- `__suppress_context__` — if `True`, Python shows `__cause__` chain but not `__context__`. Set to `True` by `raise X from Y`, and to `True` by `raise X from None` (with `__cause__ = None`).

### Display rules
Python's traceback renderer:
1. If `exc.__cause__` is set → shows cause chain with "The above exception was the direct cause of the following exception"
2. Else if `exc.__context__` is set and `__suppress_context__` is `False` → shows with "During handling of the above exception, another exception occurred"
3. `raise X from None` sets `__cause__ = None` and `__suppress_context__ = True` → no chain shown

### When to use each form

**`raise NewExc from original`** — when you're wrapping an exception with a better message/type:
```python
try:
    conn = db.connect()
except OperationalError as e:
    raise DatabaseUnavailable("Cannot reach database") from e
    # Preserves full traceback context for debugging
```

**`raise NewExc from None`** — when the original exception is an implementation detail:
```python
try:
    value = self._cache[key]
except KeyError:
    raise ValueError(f"Unknown key: {key!r}") from None
    # The KeyError is irrelevant to callers — suppress it
```

**Bare `raise NewExc` inside `except`** — implicit chaining (shows context):
```python
except SomeError as e:
    raise DifferentError("something went wrong")
    # Shows: "During handling of SomeError, DifferentError occurred"
```

### Exception groups (Python 3.11+, PEP 654)
`ExceptionGroup` wraps multiple exceptions that occurred in parallel (e.g., multiple tasks failing in an async context). Handled with `except*` syntax:
```python
try:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(failing_task())
        tg.create_task(another_failing_task())
except* ValueError as eg:
    for exc in eg.exceptions:
        print(f"ValueError: {exc}")
```

### Accessing chain programmatically
```python
try:
    ...
except Exception as e:
    cause = e.__cause__     # explicit chain
    context = e.__context__ # implicit chain
    # Walk the full chain:
    while e:
        print(e)
        e = e.__cause__ or e.__context__
```

### `BaseException` vs `Exception`
`Exception` is a subclass of `BaseException`. `KeyboardInterrupt`, `SystemExit`, `GeneratorExit` inherit directly from `BaseException` — they won't be caught by `except Exception`. Always re-raise `BaseException` subclasses unless you explicitly intend to handle them.

### Custom exception hierarchy
```python
class AppError(Exception): pass
class ValidationError(AppError): pass
class DatabaseError(AppError): pass
class NotFoundError(DatabaseError): pass
```
Catch the base (`AppError`) for broad handling, or the leaf (`NotFoundError`) for specific handling. Avoid catching `Exception` broadly in library code.

## 💻 Code Example

```python
class ServiceError(Exception):
    """Base for all service-layer exceptions."""

class DatabaseError(ServiceError):
    """Raised when DB operations fail."""

class NotFoundError(ServiceError):
    """Raised when a requested resource doesn't exist."""


def get_user(user_id: int):
    try:
        raw = db_query(f"SELECT * FROM users WHERE id={user_id}")
    except ConnectionError as e:
        raise DatabaseError("Database unreachable") from e  # explicit chain

    if raw is None:
        raise NotFoundError(f"User {user_id} not found") from None  # suppress chain

    return raw


# Walking the exception chain
def log_exception_chain(exc):
    chain = []
    current = exc
    while current is not None:
        chain.append(f"{type(current).__name__}: {current}")
        current = current.__cause__ or (
            current.__context__ if not current.__suppress_context__ else None
        )
    return " → ".join(chain)
```

## ⚠️ Common Mistakes & Interview Traps

1. **`except Exception as e` after the block**: In Python 3, `e` is deleted after the `except` block. Storing it: `saved = e` before the block ends — or use `sys.exc_info()` (but beware frame retention).

2. **Catching `BaseException` accidentally**: `except Exception` is almost always correct. `except BaseException` catches `KeyboardInterrupt` and `SystemExit` — usually a bug.

3. **Swallowing exception chain with bare `raise NewExc`**: When you intend explicit causal chaining, use `raise NewExc from original`, not just `raise NewExc`. The `__context__` is set automatically but gives a weaker message.

4. **`raise` vs `raise e`**: Inside an `except e:` block, bare `raise` re-raises the caught exception with its original traceback. `raise e` re-raises but may reset the traceback to the current line (subtle difference in Python 3).

5. **Exception groups and `except*`**: `except*` is Python 3.11+. Using it in 3.10 is a `SyntaxError`. In async backends targeting 3.11+, `TaskGroup` + `ExceptionGroup` replaces `gather(return_exceptions=True)` pattern.

## 🔗 Related Concepts
- `async_python/` — `asyncio.TaskGroup` and `ExceptionGroup` (Python 3.11+)
- `python_core/008_generators_internals` — `generator.throw()` is exception injection
- `unit_tests/` — `pytest.raises()`, `ExceptionInfo.__cause__` checking

## 📚 Go Deeper
- PEP 3134 — "Exception Chaining and Embedded Tracebacks"
- PEP 654 — "Exception Groups and except*" (Python 3.11)
