"""FastAPI app: job API, WebSocket event stream, engineer approval gate, static UI."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from agents.core import JobContext, model_name  # noqa: E402
from agents.orchestrator import Orchestrator, resolve_mode, AGENTS  # noqa: E402
from factory import db  # noqa: E402

from .demo_specs import demo_specs  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
STATIC = Path(__file__).resolve().parent / "static"
app = FastAPI(title="Cold plate agent factory")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

_subscribers: set[asyncio.Queue] = set()
_tasks: dict[str, asyncio.Task] = {}


async def broadcast(event: dict) -> None:
    for q in list(_subscribers):
        q.put_nowait(event)


def make_emit(job_id: str):
    async def emit(type_: str, agent: str | None, payload: dict, persist: bool = True) -> None:
        if persist:
            ev = db.add_event(job_id, type_, agent, payload)
        else:
            ev = {"id": None, "job_id": job_id, "ts": datetime.now().isoformat(timespec="milliseconds"),
                  "type": type_, "agent": agent, "payload": payload}
        await broadcast(ev)
    return emit


@app.on_event("startup")
async def startup() -> None:
    db.init(reseed=True)
    # Jobs interrupted by a restart can't resume mid-agent; mark them so the UI doesn't spin forever.
    # Bookings are re-seeded, so jobs awaiting approval lose their tentative holds: mark them expired.
    for j in db.list_jobs(500):
        if j["status"] == "running":
            db.update_job(j["id"], status="interrupted")
        elif j["status"] == "awaiting_approval":
            db.update_job(j["id"], status="expired")


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/config")
async def config():
    mode = resolve_mode()
    return {"mode": mode, "model": model_name(), "has_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "agents": [{"key": a.key, "name": a.name, "role": a.role} for a in AGENTS.values()],
            "demo_specs": demo_specs()}


class JobRequest(BaseModel):
    spec: dict
    mode: str | None = None


@app.post("/api/jobs")
async def create_job(req: JobRequest):
    mode = req.mode or resolve_mode()
    if mode not in ("live", "scripted"):
        raise HTTPException(400, "mode must be live or scripted")
    if mode == "live" and not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(400, "Live mode needs ANTHROPIC_API_KEY in .env")
    job_id = "J-" + uuid.uuid4().hex[:6].upper()
    title = req.spec.get("part_name") or "Cold plate request"
    db.create_job(job_id, title, req.spec, mode)
    ctx = JobContext(job_id=job_id, raw_spec=req.spec, emit_fn=make_emit(job_id), mode=mode)
    _tasks[job_id] = asyncio.create_task(Orchestrator(ctx).run())
    return {"job_id": job_id, "mode": mode}


@app.get("/api/jobs")
async def jobs():
    return db.list_jobs()


@app.get("/api/jobs/{job_id}")
async def job(job_id: str):
    j = db.get_job(job_id)
    if not j:
        raise HTTPException(404, "no such job")
    return {**j, "events": db.get_events(job_id)}


class Decision(BaseModel):
    engineer: str = "Engineer"
    comment: str = ""


@app.post("/api/jobs/{job_id}/approve")
async def approve(job_id: str, d: Decision):
    j = db.get_job(job_id)
    if not j or j["status"] != "awaiting_approval":
        raise HTTPException(409, "job is not awaiting approval")
    n = db.commit_tentative(job_id)
    db.update_job(job_id, status="released")
    await make_emit(job_id)("approved", "engineer", {"engineer": d.engineer, "comment": d.comment,
                                                     "bookings_committed": n})
    return {"status": "released", "bookings_committed": n}


@app.post("/api/jobs/{job_id}/reject")
async def reject(job_id: str, d: Decision):
    j = db.get_job(job_id)
    if not j or j["status"] != "awaiting_approval":
        raise HTTPException(409, "job is not awaiting approval")
    db.release_tentative(job_id)
    db.update_job(job_id, status="returned")
    await make_emit(job_id)("returned", "engineer", {"engineer": d.engineer, "comment": d.comment})
    return {"status": "returned"}


@app.get("/api/factory")
async def factory():
    return {"machines": db.machines(), "bookings": db.busy_for("")}


@app.post("/api/factory/reset")
async def factory_reset():
    db.seed_factory()
    return {"ok": True}


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.add(q)
    try:
        while True:
            ev = await q.get()
            await websocket.send_text(json.dumps(ev, default=str))
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        _subscribers.discard(q)
