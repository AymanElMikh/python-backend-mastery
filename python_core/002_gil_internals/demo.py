"""
Demo: The GIL — Global Interpreter Lock
Run:  python demo.py
"""

import threading
import time
import sys

# ── Section 1: GIL switch interval ────────────────────────────────────────────
def show_switch_interval():
    interval = sys.getswitchinterval()
    print(f"  GIL switch interval: {interval*1000:.1f} ms")
    print(f"  (threads release GIL every ~{interval*1000:.0f}ms at bytecode boundaries)")


# ── Section 2: CPU-bound — threads do NOT speed things up ─────────────────────
def cpu_task(n):
    """Pure Python counter loop — holds the GIL throughout."""
    count = 0
    for _ in range(n):
        count += 1
    return count

def benchmark_cpu(n=5_000_000):
    # Single-threaded
    start = time.perf_counter()
    cpu_task(n)
    single = time.perf_counter() - start

    # Two threads — should be ~same or slower due to GIL contention
    start = time.perf_counter()
    t1 = threading.Thread(target=cpu_task, args=(n // 2,))
    t2 = threading.Thread(target=cpu_task, args=(n // 2,))
    t1.start(); t2.start()
    t1.join(); t2.join()
    threaded = time.perf_counter() - start

    print(f"  Single-threaded:  {single:.3f}s")
    print(f"  Two threads:      {threaded:.3f}s  ({'slower' if threaded > single else 'faster'} — GIL prevents true parallelism)")


# ── Section 3: I/O-bound — threads DO speed things up ─────────────────────────
def io_task(duration):
    """Sleeps release the GIL — true concurrency for I/O."""
    time.sleep(duration)

def benchmark_io(tasks=4, duration=0.1):
    # Sequential
    start = time.perf_counter()
    for _ in range(tasks):
        io_task(duration)
    sequential = time.perf_counter() - start

    # Threaded — GIL is released during sleep, so threads overlap
    start = time.perf_counter()
    threads = [threading.Thread(target=io_task, args=(duration,)) for _ in range(tasks)]
    for t in threads: t.start()
    for t in threads: t.join()
    threaded = time.perf_counter() - start

    print(f"  {tasks} tasks × {duration}s sleep, sequential: {sequential:.3f}s")
    print(f"  {tasks} tasks × {duration}s sleep, threaded:   {threaded:.3f}s  (all overlap — GIL released during sleep)")


# ── Section 4: The "not thread-safe even with GIL" trap ───────────────────────
counter = 0

def unsafe_increment(n):
    """check-then-act is NOT atomic, even with the GIL."""
    global counter
    for _ in range(n):
        # GIL CAN switch between these two lines:
        temp = counter   # bytecode: LOAD_GLOBAL
        counter = temp + 1  # bytecode: STORE_GLOBAL (GIL may switch here)

def demonstrate_race():
    global counter
    counter = 0
    n = 100_000
    threads = [threading.Thread(target=unsafe_increment, args=(n // 4,)) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    return counter

# Safe version using a lock
lock = threading.Lock()
safe_counter = 0

def safe_increment(n):
    global safe_counter
    for _ in range(n):
        with lock:
            safe_counter += 1


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: The GIL — Global Interpreter Lock")
    print("=" * 55)

    print("\n[1] GIL configuration:")
    show_switch_interval()

    print("\n[2] CPU-bound work — threading does NOT help:")
    benchmark_cpu()

    print("\n[3] I/O-bound work — threading DOES help (GIL released):")
    benchmark_io()

    print("\n[4] Thread safety trap — GIL ≠ data structure safety:")
    result = demonstrate_race()
    print(f"  Expected counter: 100000")
    print(f"  Actual counter:   {result}  {'(race condition!)' if result != 100_000 else '(got lucky this run)'}")
    print("  Note: result varies per run — GIL allows switches mid-compound-op")

    print("\n[5] Summary:")
    print("  Use threads for:       I/O-bound work (network, disk, DB queries)")
    print("  Use multiprocessing:   CPU-bound work (parsing, math, image processing)")
    print("  Use asyncio:           High-concurrency I/O (thousands of connections)")

    print("\n" + "=" * 55)
