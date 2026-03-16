# Async Generators — async def + yield

## 🎯 Interview Question
What is an async generator in Python, how does it differ from a regular async coroutine and a synchronous generator, and when would you use `async for` with one in a production FastAPI or data pipeline context?

## 💡 Short Answer (30 seconds)
An async generator is a function using both `async def` and `yield`. Each `yield` suspends the coroutine and gives control back to the event loop, while the caller advances it with `async for` or `await anext()`. They're ideal for streaming large datasets, paginating async APIs, or producing items from async sources without loading everything into memory.

## 🔬 Deep Explanation
**How it works under the hood**
An `async def` function with `yield` compiles to an *async generator object* (type `async_generator`). Calling `__aiter__()` on it returns itself; calling `__anext__()` returns an awaitable that, when awaited, resumes the generator until the next `yield` or `StopAsyncIteration`.

CPython's `ag_running` flag prevents re-entering a running async generator. The frame is suspended at the `yield` bytecode just like synchronous generators, but re-entering requires an `await` (i.e., event loop cooperation).

**`aclose()` and finalisation**
Async generators are NOT automatically finalised by the GC the way sync generators are (CPython has no `asend` analogue for GC). You must either:
1. Exhaust the generator (let it hit `StopAsyncIteration`).
2. Call `await agen.aclose()` explicitly.
3. Register `asyncio.get_event_loop().shutdown_asyncgens()` — called automatically by `asyncio.run()`.

**Production patterns:**
1. **Streaming DB rows**: yield rows in batches, avoid loading all into RAM.
2. **Paginated API client**: yield pages without accumulating.
3. **SSE / WebSocket streaming**: yield events and send as they arrive.
4. **Rate-limited queue consumer**: yield items with backpressure via `asyncio.sleep`.

**`yield from` vs `async for`**
You cannot use `yield from` inside an async generator — use `async for item in sub_agen: yield item`.

**`@asynccontextmanager`** from `contextlib` is implemented using an async generator with exactly one `yield`.

## 💻 Code Example
```python
import asyncio

async def paginate(total: int, page_size: int = 3):
    """Async generator simulating paginated API calls."""
    for offset in range(0, total, page_size):
        await asyncio.sleep(0)    # simulate I/O
        page = list(range(offset, min(offset + page_size, total)))
        for item in page:
            yield item

async def main():
    async for item in paginate(10):
        print(item, end=" ")
    print()

asyncio.run(main())
```

## ⚠️ Common Mistakes & Interview Traps
- **Not closing async generators** — resource leaks if the generator holds a DB cursor or HTTP session.
- **`return value` in async generator** — `return` terminates iteration but the value is NOT accessible to the caller (unlike `send()` in sync generators). Use `StopAsyncIteration` catching if you need a final value.
- **`yield from` is invalid** — use `async for ... yield` pattern to delegate.
- **`async for` in sync code** — you cannot use `async for` outside a coroutine. Wrap in `asyncio.run()`.
- **Thread-safety**: async generators share the event loop — running them from different threads without proper synchronisation is unsafe.

## 🔗 Related Concepts
- python_core/008_generators_internals — synchronous generator internals
- python_core/007_context_managers — asynccontextmanager uses async generators
- fastapi/024_background_tasks — async streaming responses use async generators

## 📚 Go Deeper
- PEP 525 — Asynchronous Generators
- CPython `Objects/genobject.c` — `async_gen_asend` and `ag_running` flag
