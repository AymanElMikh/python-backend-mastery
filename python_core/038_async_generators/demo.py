"""
Demo: Async Generators — async def + yield
Run:  python demo.py
"""
import asyncio
import types

# ── Section 1: Basic async generator & async for ────────────────────────────
print("=" * 50)
print("Section 1: Basic async generator")
print("=" * 50)

async def count_up(n: int):
    for i in range(n):
        await asyncio.sleep(0)   # yield to event loop each iteration
        yield i

async def demo_basic():
    results = []
    async for val in count_up(5):
        results.append(val)
    print("Items:", results)
    print("Type:", type(count_up(1)))  # <class 'async_generator'>

asyncio.run(demo_basic())

# ── Section 2: anext() and aclose() ──────────────────────────────────────────
print("\n" + "=" * 50)
print("Section 2: anext() and aclose()")
print("=" * 50)

async def demo_anext():
    gen = count_up(3)
    print("First:", await anext(gen))
    print("Second:", await anext(gen))
    await gen.aclose()       # must close to release resources
    try:
        await anext(gen)
    except StopAsyncIteration:
        print("Generator closed — StopAsyncIteration raised")

asyncio.run(demo_anext())

# ── Section 3: Streaming paginated API simulation ───────────────────────────
print("\n" + "=" * 50)
print("Section 3: Paginated streaming")
print("=" * 50)

async def fetch_pages(total: int, page_size: int = 4):
    """Simulates async paginated API — yields one item at a time."""
    page_num = 0
    for offset in range(0, total, page_size):
        await asyncio.sleep(0)   # simulate network I/O
        page = list(range(offset, min(offset + page_size, total)))
        print(f"  [fetched page {page_num}: {page}]")
        page_num += 1
        for item in page:
            yield item

async def demo_pagination():
    total = 0
    async for item in fetch_pages(11, page_size=4):
        total += item
    print("Sum of streamed items:", total)

asyncio.run(demo_pagination())

# ── Section 4: yield from is INVALID in async generators ─────────────────────
print("\n" + "=" * 50)
print("Section 4: Delegating — async for + yield pattern")
print("=" * 50)

async def even_numbers(limit):
    for i in range(0, limit, 2):
        await asyncio.sleep(0)
        yield i

async def combined(limit):
    # Cannot use `yield from even_numbers(limit)` in async gen!
    async for item in even_numbers(limit):
        yield item   # explicit delegation

async def demo_delegation():
    results = [v async for v in combined(10)]
    print("Even numbers:", results)

asyncio.run(demo_delegation())

# ── Section 5: asynccontextmanager is an async generator ─────────────────────
print("\n" + "=" * 50)
print("Section 5: asynccontextmanager under the hood")
print("=" * 50)

from contextlib import asynccontextmanager

@asynccontextmanager
async def managed_resource(name: str):
    print(f"  [acquire] {name}")
    try:
        yield name.upper()
    finally:
        print(f"  [release] {name}")

async def demo_ctx():
    async with managed_resource("db_connection") as resource:
        print(f"  Using: {resource}")

asyncio.run(demo_ctx())

if __name__ == "__main__":
    print("\nAll sections complete.")
