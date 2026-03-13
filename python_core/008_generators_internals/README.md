# Generator Internals & `send()` / `throw()`

## 🎯 Interview Question
How do Python generators work internally? What is the difference between `next()`, `send()`, and `throw()`? How do generators enable coroutines, and what problem does `yield from` solve?

## 💡 Short Answer (30 seconds)
A generator is a suspended function — calling `yield` serializes the frame (locals, instruction pointer) to a `PyGenObject` and pauses execution. `next()` resumes and gets the yielded value. `send(value)` resumes AND injects a value as the result of the `yield` expression — this is how coroutines communicate. `throw()` injects an exception at the yield point. `yield from` delegates to a sub-generator and tunnels `send()`/`throw()` through automatically.

## 🔬 Deep Explanation

### Generator execution model
When you call a generator function, Python does NOT execute it — it creates a `generator` object wrapping the code frame in `GEN_CREATED` state. Each `next()` call:
1. Sets state to `GEN_RUNNING`
2. Resumes the frame from where it paused
3. Runs until the next `yield` (state → `GEN_SUSPENDED`) or `return`/`StopIteration` (state → `GEN_CLOSED`)

The frame is a `PyFrameObject` containing locals, bytecode pointer (`f_lasti`), and value stack — all preserved across yields.

### `send(value)` — bidirectional communication
The `yield` expression has a *value*: `x = yield something`. After `yield something` suspends:
- `next(gen)` resumes with the yield expression evaluating to `None`
- `gen.send(42)` resumes with the yield expression evaluating to `42`

First call must use `next()` or `send(None)` — the generator hasn't reached a `yield` yet.

### `throw(type, value, traceback)` — injecting exceptions
Injects an exception at the current `yield` point. The generator can catch it with `try/except` around the `yield`, handle it, and continue — or let it propagate (turning the generator into `GEN_CLOSED`).

### `close()` — orderly shutdown
`gen.close()` calls `gen.throw(GeneratorExit)`. The generator should either handle it and return, or let it propagate. `finally` blocks still run.

### `yield from` — delegation and tunneling
`yield from subgen` does:
1. Iterates `subgen`, yielding each value to the outer consumer
2. Forwards `send()` values to `subgen`
3. Forwards `throw()` exceptions to `subgen`
4. When `subgen` returns, the `return` value becomes the value of the `yield from` expression

This is what makes `asyncio` work: `await expr` is `yield from expr` under the hood, and the event loop sends wakeup values through the chain.

### Generator as lazy pipeline
Generators enable lazy evaluation — a pipeline of `(x for x in source if ...)` processes one item at a time, never materializing the full list. Critical for streaming large datasets.

### `inspect.getgeneratorstate(gen)`
Returns `'GEN_CREATED'`, `'GEN_RUNNING'`, `'GEN_SUSPENDED'`, or `'GEN_CLOSED'`.

## 💻 Code Example

```python
def counter(start=0):
    """Simple generator — one value per next()."""
    while True:
        yield start
        start += 1

def accumulator():
    """Coroutine — receives values via send(), yields running total."""
    total = 0
    while True:
        value = yield total   # suspends, returns total; receives next send() value
        if value is None:
            break
        total += value

def pipeline(source, *transforms):
    """Lazy streaming pipeline — no list materialization."""
    stream = source
    for transform in transforms:
        stream = transform(stream)
    return stream

# yield from — delegation
def flatten(nested):
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)  # delegates recursively
        else:
            yield item
```

## ⚠️ Common Mistakes & Interview Traps

1. **`send()` before first `next()`**: Calling `gen.send(42)` on a fresh generator raises `TypeError: can't send non-None value to a just-started generator`. Always prime with `next(gen)` or `send(None)`.

2. **Assuming `return` in a generator raises `StopIteration` with the value**: It does, but in Python 3.7+, `StopIteration` propagating out of a coroutine is converted to `RuntimeError` (PEP 479). This catches the common bug of accidentally raising `StopIteration` inside an async function.

3. **Generator vs list comprehension**: `[x for x in ...]` materializes immediately; `(x for x in ...)` is lazy. Using a list comprehension in a `yield from` context defeats the purpose.

4. **`yield from` vs chained `yield`**: `yield from gen` forwards `send()`/`throw()` correctly. A manual loop `for x in gen: yield x` does NOT — `send()` values are lost.

5. **Generator finalization**: If a generator is garbage collected while `GEN_SUSPENDED`, Python calls `close()` → throws `GeneratorExit`. If the generator swallows `GeneratorExit` (catches it and yields again), `RuntimeError` is raised.

## 🔗 Related Concepts
- `python_core/007_context_managers` — `@contextmanager` is built on generator `send()`/`throw()`
- `async_python/` — `async def` / `await` is generators + event loop integration
- `python_core/009_decorator_internals` — `functools.wraps` is important for generator wrappers

## 📚 Go Deeper
- PEP 342 — "Coroutines via Enhanced Generators" — introduced `send()` and `throw()`
- PEP 380 — "Syntax for Delegating to a Subgenerator" — introduced `yield from`
