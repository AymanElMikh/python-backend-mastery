"""
Demo: FastAPI Background Tasks
Run:  python demo.py
"""

import asyncio
import time
import threading
from fastapi import FastAPI, BackgroundTasks, Depends, Request
from fastapi.testclient import TestClient

app = FastAPI()

# ── Execution log to verify ordering ─────────────────────────────────────────
log = []

# ── Section 1: Async and sync background tasks ────────────────────────────────
async def send_email(to: str, subject: str):
    """Async task — runs on event loop, no thread."""
    await asyncio.sleep(0.01)  # simulate network I/O
    log.append(f"EMAIL → {to}: {subject!r}  [thread={threading.current_thread().name}]")

def write_audit_log(user_id: int, action: str):
    """Sync task — runs in thread pool via run_in_executor."""
    time.sleep(0.005)  # simulate DB write
    log.append(f"AUDIT user={user_id} action={action!r}  [thread={threading.current_thread().name}]")

async def update_stats(event: str):
    log.append(f"STATS event={event!r}")


# ── Section 2: Tasks from route ───────────────────────────────────────────────
@app.post("/register")
async def register(email: str, background_tasks: BackgroundTasks):
    user_id = 42
    # Queue post-response tasks
    background_tasks.add_task(send_email, email, "Welcome!")
    background_tasks.add_task(write_audit_log, user_id, "registered")
    background_tasks.add_task(update_stats, "user.registered")

    log.append(f"RESPONSE sent for {email!r}")
    return {"user_id": user_id, "email": email}


# ── Section 3: Tasks from dependency ─────────────────────────────────────────
async def audit_dependency(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Dependency that adds its own background tasks."""
    background_tasks.add_task(write_audit_log, 0, f"dependency_audit:{request.url.path}")
    return {"path": str(request.url.path)}


@app.get("/items")
async def get_items(
    audit=Depends(audit_dependency),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    background_tasks.add_task(update_stats, "items.listed")
    return {"items": ["a", "b", "c"], "audit": audit}


# ── Section 4: Failure in background task ────────────────────────────────────
async def failing_task(should_fail: bool):
    if should_fail:
        raise RuntimeError("Background task failed!")
    log.append("TASK completed successfully")

@app.post("/risky")
async def risky_endpoint(fail: bool, background_tasks: BackgroundTasks):
    background_tasks.add_task(failing_task, fail)
    log.append("RESPONSE sent before task runs")
    return {"status": "accepted", "will_fail": fail}


# ── Section 5: Demonstrating sequential execution ────────────────────────────
async def slow_task(name: str, delay: float):
    await asyncio.sleep(delay)
    log.append(f"SLOW_TASK {name!r} done after {delay}s")

@app.post("/sequential")
async def sequential(background_tasks: BackgroundTasks):
    background_tasks.add_task(slow_task, "first",  0.02)
    background_tasks.add_task(slow_task, "second", 0.01)
    background_tasks.add_task(slow_task, "third",  0.005)
    return {"message": "tasks queued sequentially"}


if __name__ == "__main__":
    client = TestClient(app)

    print("=" * 55)
    print("DEMO: FastAPI Background Tasks")
    print("=" * 55)

    # Section 1+2: basic tasks
    print("\n[1] Background tasks — response sent before tasks run:")
    log.clear()
    r = client.post("/register?email=alice@example.com")
    print(f"  POST /register → {r.status_code} {r.json()}")
    print(f"  Execution log:")
    for entry in log:
        print(f"    {entry}")
    print(f"  'RESPONSE' appears before task entries (tasks run post-response)")

    # Section 3: tasks from dependency
    print("\n[2] Tasks added by a dependency:")
    log.clear()
    r = client.get("/items")
    print(f"  GET /items → {r.status_code}")
    for entry in log:
        print(f"    {entry}")

    # Section 4: failure doesn't affect client
    print("\n[3] Background task failure — client still gets 200:")
    log.clear()
    r = client.post("/risky?fail=false")
    print(f"  fail=false → {r.status_code} {r.json()}")
    for entry in log:
        print(f"    {entry}")

    log.clear()
    # Starlette logs the error but doesn't raise to client
    try:
        r = client.post("/risky?fail=true")
        print(f"  fail=true  → {r.status_code} {r.json()}  (client got 200 despite task failure)")
    except Exception as e:
        print(f"  Exception propagated in TestClient: {e}")

    # Section 5: sequential execution
    print("\n[4] Tasks run SEQUENTIALLY (not in parallel):")
    log.clear()
    r = client.post("/sequential")
    print(f"  POST /sequential → {r.json()}")
    for entry in log:
        print(f"    {entry}")
    print("  Note: 'first' (0.02s) finishes before 'second' (0.01s) — sequential!")

    # Section 6: comparison summary
    print("\n[5] BackgroundTasks vs Celery:")
    print("  BackgroundTasks: zero setup, in-process, no retry, < 1s work only")
    print("  Celery:          broker + worker, durable, retryable, scales out")

    print("\n" + "=" * 55)
