"""
Demo: Generator Internals & send() / throw()
Run:  python demo.py
"""

import inspect

# ── Section 1: Generator states ───────────────────────────────────────────────
def simple_gen():
    print("    [gen] before first yield")
    x = yield "first"
    print(f"    [gen] resumed, received x={x!r}")
    yield "second"
    print("    [gen] returning")


# ── Section 2: Coroutine via send() ──────────────────────────────────────────
def running_average():
    """Receives values via send(), yields running average."""
    total = 0
    count = 0
    avg = None
    while True:
        value = yield avg      # send a value in, get average back
        if value is None:
            return             # sentinel: done
        total += value
        count += 1
        avg = total / count


# ── Section 3: throw() — injecting exceptions ────────────────────────────────
def resilient_gen():
    for i in range(10):
        try:
            yield i
        except ValueError as e:
            print(f"    [gen] caught ValueError: {e}, continuing")
            yield f"recovered-{i}"


# ── Section 4: yield from — delegation and tunneling ─────────────────────────
def inner():
    received = yield "from inner"
    yield f"inner got: {received!r}"
    return "inner_done"  # this becomes the value of 'yield from inner()' expression

def outer():
    result = yield from inner()  # tunnels send()/throw(), captures return value
    yield f"outer: inner returned {result!r}"


# ── Section 5: Lazy pipeline — no list materialization ───────────────────────
def read_numbers(n):
    """Source generator."""
    for i in range(n):
        yield i

def only_even(source):
    for x in source:
        if x % 2 == 0:
            yield x

def multiply(factor, source):
    for x in source:
        yield x * factor

def flatten(nested):
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item


# ── Section 6: PEP 479 trap — StopIteration inside generator ─────────────────
def dangerous_gen():
    """StopIteration inside a generator becomes RuntimeError (PEP 479)."""
    items = iter([1, 2, 3])
    while True:
        try:
            yield next(items)  # next() raises StopIteration when exhausted
        except StopIteration:
            return  # correct: catch and return normally


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: Generator Internals & send() / throw()")
    print("=" * 55)

    # Section 1: states
    print("\n[1] Generator states:")
    g = simple_gen()
    print(f"  After creation:      {inspect.getgeneratorstate(g)}")
    val = next(g)
    print(f"  After first next():  {inspect.getgeneratorstate(g)}, yielded: {val!r}")
    val = g.send("hello!")
    print(f"  After send('hello'): yielded: {val!r}")
    try:
        next(g)
    except StopIteration:
        print(f"  After exhaustion:    {inspect.getgeneratorstate(g)}")

    # Section 2: coroutine via send()
    print("\n[2] Coroutine — running_average() via send():")
    avg_gen = running_average()
    next(avg_gen)  # prime
    for n in [10, 20, 30, 40]:
        result = avg_gen.send(n)
        print(f"  sent {n:3d} → avg = {result}")
    try:
        avg_gen.send(None)  # sentinel to stop
    except StopIteration:
        pass

    # Section 3: throw()
    print("\n[3] throw() — injecting exceptions mid-generator:")
    rg = resilient_gen()
    print(f"  next() → {next(rg)}")
    print(f"  next() → {next(rg)}")
    print(f"  throw(ValueError) →", end=" ")
    val = rg.throw(ValueError, ValueError("bad data"))
    print(repr(val))
    print(f"  next() → {next(rg)}")

    # Section 4: yield from
    print("\n[4] yield from — delegation + tunneling:")
    og = outer()
    print(f"  next()        → {next(og)!r}")
    print(f"  send('ping')  → {og.send('ping')!r}")
    try:
        print(f"  next()        → {next(og)!r}")
    except StopIteration:
        pass

    # Section 5: lazy pipeline
    print("\n[5] Lazy pipeline — nothing materialized until consumed:")
    pipeline = multiply(3, only_even(read_numbers(10)))
    results = list(pipeline)
    print(f"  read_numbers(10) → even → x3 = {results}")

    nested = [1, [2, [3, 4], 5], [6, 7]]
    print(f"  flatten({nested}) = {list(flatten(nested))}")

    # Section 6: PEP 479
    print("\n[6] PEP 479 — StopIteration → RuntimeError inside generators:")
    safe = list(dangerous_gen())
    print(f"  dangerous_gen() result: {safe}  (handled correctly with try/except)")
    print("  Note: unhandled StopIteration inside a generator → RuntimeError since Python 3.7")

    print("\n" + "=" * 55)
