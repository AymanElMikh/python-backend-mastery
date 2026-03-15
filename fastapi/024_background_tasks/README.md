# FastAPI Background Tasks

## 🎯 Interview Question
What are FastAPI's `BackgroundTasks` and when would you use them over Celery? What guarantees do they make about execution, and what are the failure modes?

## 💡 Short Answer (30 seconds)
`BackgroundTasks` runs work after the HTTP response is sent — in the same process, on the same event loop. It's ideal for lightweight post-response work: sending a confirmation email, writing to an audit log, updating a cache. It's NOT suitable for long-running, CPU-heavy, or critical work that must survive server restarts or failures — for that, use Celery with a message broker.

## 🔬 Deep Explanation

### How `BackgroundTasks` works internally
Starlette's `BackgroundTasks` is a simple list of callables. After the route handler returns a response, Starlette's `run` method iterates the list and calls each task sequentially. The tasks run in the same event loop — `async` tasks are awaited, sync tasks are run in a thread pool.

```python
class BackgroundTasks:
    def add_task(self, func, *args, **kwargs): ...
    async def __call__(self, scope, receive, send): ...  # runs tasks after response
```

### What it guarantees — and what it doesn't
- **Runs after response is sent**: client gets their response immediately; task runs asynchronously
- **Same process**: if the server restarts or crashes mid-task, the task is lost
- **No retry logic**: if the task raises, the exception is logged but the response already went
- **No visibility**: no task ID, no progress tracking, no result storage
- **Sequential**: tasks in a single `BackgroundTasks` instance run one after another

### Dependency injection in background tasks
Background tasks don't go through FastAPI's DI — they're called directly. If a task needs a DB session, you must create it inside the task function:
```python
async def send_email_task(user_id: int):
    async with AsyncSession(engine) as session:
        user = await session.get(User, user_id)
        await email_service.send(user.email, ...)
    # Session managed explicitly — no Depends() here
```

### Adding tasks
```python
@app.post("/register")
async def register(background_tasks: BackgroundTasks, user: UserCreate):
    user_id = await create_user(user)
    background_tasks.add_task(send_welcome_email, user_id)
    background_tasks.add_task(update_analytics, user_id, event="signup")
    return {"id": user_id}  # response sent immediately
```

Tasks can also come from dependencies:
```python
async def get_audit_log(background_tasks: BackgroundTasks):
    # dependency injects its own tasks
    background_tasks.add_task(log_to_audit_db, ...)
```

### When to use `BackgroundTasks` vs Celery

| | `BackgroundTasks` | Celery |
|---|---|---|
| Setup | Zero | Redis/RabbitMQ broker + worker process |
| Survives restart | No | Yes (tasks in queue) |
| Long-running | No | Yes |
| CPU-bound | No (blocks event loop if sync) | Yes (separate process) |
| Retry on failure | No | Yes (`max_retries`) |
| Task monitoring | No | Flower, Celery Inspect |
| Result storage | No | Redis/DB backend |
| Scale | Single process | Horizontally scalable workers |

**Rule of thumb**: Use `BackgroundTasks` for < 1 second, non-critical work. Use Celery for anything else.

### Sync vs async background tasks
Both work with `add_task`:
- `async def task()` — awaited on the event loop (no thread)
- `def task()` — run in a thread pool via `run_in_executor` (doesn't block event loop)

A CPU-heavy sync task still blocks the executor thread — for CPU work, use multiprocessing or offload to Celery.

## 💻 Code Example

```python
from fastapi import FastAPI, BackgroundTasks
import asyncio
import time

app = FastAPI()

task_log = []  # track execution order

async def async_task(name: str, delay: float = 0):
    await asyncio.sleep(delay)
    task_log.append(f"async_task({name}) done")

def sync_task(name: str):
    time.sleep(0.01)  # runs in threadpool — doesn't block event loop
    task_log.append(f"sync_task({name}) done")

@app.post("/process/{item_id}")
async def process(item_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(async_task, f"notify-{item_id}")
    background_tasks.add_task(sync_task, f"audit-{item_id}")
    task_log.append("response sent")
    return {"id": item_id, "status": "processing"}
```

## ⚠️ Common Mistakes & Interview Traps

1. **"It runs in parallel" — wrong**: Tasks run sequentially after the response. If task 1 takes 10 seconds, task 2 waits. Truly parallel work needs Celery or `asyncio.create_task`.

2. **DB session from Depends in background task**: The DI session is closed when the request ends — before or right as the background task starts. Always create a new session inside background tasks.

3. **CPU-bound sync task blocks the thread pool**: FastAPI's thread pool has a limited number of threads. A sync background task that runs for 30 seconds occupies a thread, potentially starving other sync routes.

4. **No error propagation to client**: If a background task raises, the exception is logged by Starlette but the client already received 200 OK. There's no way to notify the client.

5. **Multiple `BackgroundTasks` in DI chain**: If a dependency adds tasks to `background_tasks` and the route also adds tasks, they're all in the same `BackgroundTasks` instance — all run after the response.

## 🔗 Related Concepts
- `fastapi/021_dependency_injection` — `BackgroundTasks` can be injected via `Depends`
- `performance/` — Celery for durable, scalable background work
- `async_python/` — `asyncio.create_task` for truly concurrent in-process tasks

## 📚 Go Deeper
- Starlette source: `background.py` — `BackgroundTasks` implementation (~30 lines)
- FastAPI docs: "Background Tasks" — dependency injection pattern
