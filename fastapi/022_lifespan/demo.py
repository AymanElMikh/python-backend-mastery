"""
Demo: FastAPI Lifespan Events — Startup, Shutdown, app.state
Run:  python demo.py
"""

from contextlib import asynccontextmanager, AsyncExitStack
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# ── Shared state tracking ─────────────────────────────────────────────────────
lifecycle_log = []

# ── Section 1: Basic lifespan with app.state ──────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────────────────────────
    lifecycle_log.append("startup: opening DB pool")
    app.state.db_pool = {"name": "postgres-pool", "size": 10, "open": True}

    lifecycle_log.append("startup: loading ML model")
    app.state.ml_model = {"name": "sentiment-v2", "loaded": True, "calls": 0}

    lifecycle_log.append("startup: connecting to Redis")
    app.state.cache = {"name": "redis", "connected": True, "hits": 0}

    lifecycle_log.append("startup: READY")
    yield  # ← app serves requests here

    # ── SHUTDOWN ──────────────────────────────────────────────────────────────
    lifecycle_log.append("shutdown: closing DB pool")
    app.state.db_pool["open"] = False

    lifecycle_log.append("shutdown: unloading ML model")
    app.state.ml_model["loaded"] = False

    lifecycle_log.append("shutdown: disconnecting Redis")
    app.state.cache["connected"] = False

    lifecycle_log.append("shutdown: DONE")


app = FastAPI(lifespan=lifespan, title="Lifespan Demo")


@app.get("/status")
async def status(request: Request):
    return {
        "db_pool":   request.app.state.db_pool["name"],
        "db_open":   request.app.state.db_pool["open"],
        "model":     request.app.state.ml_model["name"],
        "model_ok":  request.app.state.ml_model["loaded"],
        "cache":     request.app.state.cache["name"],
    }


@app.post("/predict")
async def predict(request: Request, text: str = "hello"):
    model = request.app.state.ml_model
    model["calls"] += 1
    cache = request.app.state.cache
    cache["hits"] += 1
    return {"sentiment": "positive", "model": model["name"], "calls": model["calls"]}


# ── Section 2: AsyncExitStack for multiple resources ─────────────────────────
class FakeDB:
    def __init__(self, name):
        self.name = name
        lifecycle_log.append(f"  FakeDB({name}) connected")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        lifecycle_log.append(f"  FakeDB({self.name}) closed")


@asynccontextmanager
async def multi_resource_lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        app.state.primary_db  = await stack.enter_async_context(FakeDB("primary"))
        app.state.replica_db  = await stack.enter_async_context(FakeDB("replica"))
        lifecycle_log.append("  all resources acquired via ExitStack")
        yield
    lifecycle_log.append("  all resources released via ExitStack")


app2 = FastAPI(lifespan=multi_resource_lifespan)

@app2.get("/dbs")
async def list_dbs(request: Request):
    return {
        "primary": request.app.state.primary_db.name,
        "replica": request.app.state.replica_db.name,
    }


# ── Section 3: Legacy @on_event vs lifespan ───────────────────────────────────
app3 = FastAPI()  # no lifespan

@app3.on_event("startup")
async def old_startup():
    lifecycle_log.append("on_event startup (legacy)")
    app3.state.db = {"legacy": True}

@app3.on_event("shutdown")
async def old_shutdown():
    lifecycle_log.append("on_event shutdown (legacy)")

@app3.get("/legacy")
async def legacy_route(request: Request):
    return request.app.state.db


if __name__ == "__main__":
    print("=" * 55)
    print("DEMO: FastAPI Lifespan Events")
    print("=" * 55)

    # Section 1: basic lifespan
    print("\n[1] Basic lifespan with app.state:")
    lifecycle_log.clear()
    with TestClient(app) as client:
        r = client.get("/status")
        print(f"  GET /status → {r.json()}")
        r = client.post("/predict?text=great+product")
        print(f"  POST /predict → {r.json()}")
        r = client.post("/predict?text=terrible")
        print(f"  POST /predict → {r.json()}")
    print(f"  Lifecycle log:")
    for entry in lifecycle_log:
        print(f"    {entry}")

    # Section 2: AsyncExitStack
    print("\n[2] AsyncExitStack — multiple resources:")
    lifecycle_log.clear()
    with TestClient(app2) as client:
        r = client.get("/dbs")
        print(f"  GET /dbs → {r.json()}")
    print(f"  ExitStack lifecycle:")
    for entry in lifecycle_log:
        print(f"    {entry}")

    # Section 3: legacy on_event
    print("\n[3] Legacy @on_event (deprecated):")
    lifecycle_log.clear()
    with TestClient(app3) as client:
        r = client.get("/legacy")
        print(f"  GET /legacy → {r.json()}")
    print(f"  Log: {lifecycle_log}")
    print("  Note: on_event deprecated since FastAPI 0.93 — use lifespan instead")

    print("\n" + "=" * 55)
