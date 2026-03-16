# 🐍 Python Backend Mastery

> A structured, self-paced interview preparation system.
> Each concept lives in its own folder with a deep explanation (`README.md`) and runnable code (`demo.py`).

---

## 📁 Categories

| Folder | What It Covers |
|--------|---------------|
| `python_core/` | Intermediate & advanced Python internals |
| `oop/` | Object-Oriented Programming, SOLID, principles |
| `design_patterns/` | GoF patterns, enterprise patterns |
| `clean_architecture/` | Layered arch, DDD, hexagonal, CQRS |
| `fastapi/` | Async APIs, dependency injection, middleware, lifespan |
| `flask/` | Blueprints, extensions, app factory, testing |
| `unit_tests/` | pytest, mocking, fixtures, TDD, coverage |
| `async_python/` | asyncio, concurrency, event loop, queues, tasks |
| `databases/` | SQLAlchemy, Alembic, query optimization, ORM patterns |
| `security/` | Auth, JWT, OAuth2, hashing, rate limiting |
| `performance/` | Profiling, caching, Redis, Celery, background tasks |
| `data_structures_algorithms/` | DSA applied to backend problems |
| `api_design/` | REST best practices, versioning, pagination, error handling |
| `testing_advanced/` | Integration tests, test containers, property-based testing |

---

## 📊 Coverage Tracker

| # | Category | Concept | Folder | Date |
|---|----------|---------|--------|------|
| 001 | python_core | `__new__` vs `__init__` | python_core/001_new_vs_init | 2026-03-13 |
| 002 | python_core | The GIL — Global Interpreter Lock | python_core/002_gil_internals | 2026-03-13 |
| 003 | python_core | Descriptors (`__get__`, `__set__`, `__delete__`) | python_core/003_descriptors | 2026-03-13 |
| 004 | python_core | Metaclasses & `type` | python_core/004_metaclasses | 2026-03-13 |
| 005 | python_core | MRO & C3 Linearization with `super()` | python_core/005_mro_super | 2026-03-13 |
| 006 | python_core | `__slots__` & Memory Layout | python_core/006_slots | 2026-03-13 |
| 007 | python_core | Context Managers & `contextlib` | python_core/007_context_managers | 2026-03-13 |
| 008 | python_core | Generator Internals & `send()` / `throw()` | python_core/008_generators_internals | 2026-03-13 |
| 009 | python_core | Decorator Internals & `functools.wraps` | python_core/009_decorator_internals | 2026-03-13 |
| 010 | python_core | Python Memory Model & Garbage Collection | python_core/010_memory_model_gc | 2026-03-13 |
| 011 | python_core | `__call__` & the Callable Protocol | python_core/011_call_callable | 2026-03-13 |
| 012 | python_core | `__getattr__` vs `__getattribute__` | python_core/012_getattr_getattribute | 2026-03-13 |
| 013 | python_core | Abstract Base Classes (ABC) & Virtual Subclasses | python_core/013_abc_abstract | 2026-03-13 |
| 014 | python_core | `dataclasses` Internals — `field()`, `__post_init__`, `ClassVar` | python_core/014_dataclasses_internals | 2026-03-13 |
| 015 | python_core | The Python Import System — `importlib`, `sys.modules`, Circular Imports | python_core/015_import_system | 2026-03-13 |
| 016 | python_core | `__hash__` and `__eq__` — The Hashability Contract | python_core/016_hash_eq | 2026-03-13 |
| 017 | python_core | `functools` Deep Dive — `lru_cache`, `partial`, `cached_property`, `reduce` | python_core/017_functools_deep | 2026-03-13 |
| 018 | python_core | Exception Chaining — `__cause__`, `__context__`, `__suppress_context__` | python_core/018_exception_chaining | 2026-03-13 |
| 019 | python_core | `typing` Module — `Protocol`, `TypeVar`, `Literal`, Type Narrowing | python_core/019_typing_protocol | 2026-03-13 |
| 020 | python_core | `__init_subclass__` & Class Creation Hooks | python_core/020_init_subclass | 2026-03-13 |
| 021 | fastapi | Dependency Injection — `Depends()`, yield deps, scoped DI | fastapi/021_dependency_injection | 2026-03-13 |
| 022 | fastapi | Lifespan Events — startup, shutdown, `app.state` | fastapi/022_lifespan | 2026-03-13 |
| 023 | fastapi | Middleware — `BaseHTTPMiddleware`, pure ASGI, ordering | fastapi/023_middleware | 2026-03-13 |
| 024 | fastapi | `BackgroundTasks` — async fire-and-forget, ordering, failure isolation | fastapi/024_background_tasks | 2026-03-13 |
| 025 | fastapi | Pydantic v2 Validators — `field_validator`, `model_validator`, `computed_field` | fastapi/025_pydantic_v2_validators | 2026-03-13 |
| 026 | fastapi | Path, Query & Body Parameters — validation, `Annotated`, reusable params | fastapi/026_path_query_body | 2026-03-13 |
| 027 | fastapi | Response Models & Status Codes — `response_model`, `StreamingResponse`, 204 | fastapi/027_response_models | 2026-03-13 |
| 028 | fastapi | Exception Handlers — `HTTPException`, custom handlers, 422 override | fastapi/028_exception_handlers | 2026-03-13 |
| 029 | fastapi | OpenAPI Customization — tags, metadata, security schemes, custom schema | fastapi/029_openapi_customization | 2026-03-13 |
| 030 | fastapi | Testing FastAPI — `TestClient`, `dependency_overrides`, `AsyncClient` | fastapi/030_testing_fastapi | 2026-03-13 |

---

## 🚀 How to Use

```bash
# Run any concept demo
python python_core/001_new_vs_init/demo.py

# Start a new session (in VS Code Claude agent)
"New session — python_core"
"New session — async_python"
"New session"  # agent picks the next category automatically
```

---

## 📅 Session Log

| Session | Date | Category | Concepts Added |
|---------|------|----------|---------------|
| 1 | 2026-03-13 | python_core | 001–010 |
| 2 | 2026-03-13 | python_core | 011–020 |
| 3 | 2026-03-13 | fastapi | 021–030 |