"""SQLite persistence: jobs, event log, lab resources (rigs, cobot, partners) and bookings."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(os.environ.get("FACTORY_DB", Path(__file__).resolve().parent.parent / "factory.db"))
_lock = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS machines (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, station TEXT NOT NULL, description TEXT,
  saturday INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS bookings (
  id INTEGER PRIMARY KEY AUTOINCREMENT, machine_id TEXT NOT NULL, job_id TEXT, label TEXT NOT NULL,
  kind TEXT NOT NULL,            -- job | downtime | tentative
  start TEXT NOT NULL, end TEXT NOT NULL, seeded INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY, created_at TEXT NOT NULL, status TEXT NOT NULL, mode TEXT NOT NULL,
  title TEXT, spec TEXT NOT NULL, state TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, ts TEXT NOT NULL, type TEXT NOT NULL,
  agent TEXT, payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_events_job ON events(job_id, id);
"""

from testlab.methods import RESOURCES  # noqa: E402

# (id, name, station/kind, description, saturday-capable)
MACHINES = [(r[0], r[1], r[2], r[3], 1 if r[2] == "cobot" else 0) for r in RESOURCES]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


_conn: sqlite3.Connection | None = None


def conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = connect()
        _conn.executescript(SCHEMA)
    return _conn


def iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def parse(s: str) -> datetime:
    return datetime.fromisoformat(s)


def seed_factory(now: datetime | None = None) -> None:
    """(Re)seed machines and the existing workload relative to `now`, so dates never go stale."""
    now = (now or datetime.now()).replace(minute=0, second=0, microsecond=0)
    day0 = now.replace(hour=0)
    with _lock:
        c = conn()
        c.execute("DELETE FROM bookings")  # clean factory board on every launch
        for m in MACHINES:
            c.execute("INSERT OR REPLACE INTO machines VALUES (?,?,?,?,?)", m)

        workdays = []
        d = day0
        while len(workdays) < 12:
            if d.weekday() < 5:
                workdays.append(d)
            d += timedelta(days=1)

        def at(days: int, hour: float) -> str:
            """`days` counts working days from today (or the next working day)."""
            return iso(workdays[days] + timedelta(hours=hour))

        seed = [  # mock workload so the board is realistic; every label says it is demo data
            ("JIG-1", "M-07 QD connect/disconnect cycling (demo data)", "job", at(0, 6), at(1, 20)),
            ("FLOW-1", "Reference plate check, flow loop (planned)", "downtime", at(0, 8), at(0, 13)),
            ("LEAK-1", "M-06 pressure decay, 3 samples (demo data)", "job", at(0, 9), at(0, 15)),
            ("COBOT-1", "Cobot calibration and gripper service (planned)", "downtime", at(1, 6), at(1, 10)),
            ("HE-1", "Helium detector not yet on site (hire starts)", "downtime", at(0, 0), at(1, 12)),
            ("HYDRO-1", "Pump service and gauge check (planned)", "downtime", at(2, 6), at(2, 11)),
            ("THERM-1", "M-06 thermal resistance (demo data)", "job", at(1, 8), at(1, 16)),
            ("ENV-P", "Partner chamber booked by others (demo data)", "job", at(2, 0), at(7, 0)),
            ("CMM-UNI", "University teaching use (demo data)", "job", at(3, 9), at(3, 17)),
        ]
        for m, label, kind, s, e in seed:
            c.execute("INSERT INTO bookings (machine_id, job_id, label, kind, start, end, seeded) "
                      "VALUES (?,?,?,?,?,?,1)", (m, label.split()[0] if kind == "job" else None, label, kind, s, e))
        c.commit()


def init(reseed: bool = True) -> None:
    conn()
    if reseed:
        seed_factory()


# --- jobs & events ---------------------------------------------------------------

def create_job(job_id: str, title: str, spec: dict, mode: str) -> None:
    with _lock:
        conn().execute("INSERT INTO jobs (id, created_at, status, mode, title, spec) VALUES (?,?,?,?,?,?)",
                       (job_id, iso(datetime.now()), "running", mode, title, json.dumps(spec)))
        conn().commit()


def update_job(job_id: str, status: str | None = None, state: dict | None = None) -> None:
    with _lock:
        if status is not None:
            conn().execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
        if state is not None:
            conn().execute("UPDATE jobs SET state = ? WHERE id = ?", (json.dumps(state, default=str), job_id))
        conn().commit()


def get_job(job_id: str) -> dict | None:
    r = conn().execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["spec"] = json.loads(d["spec"])
    d["state"] = json.loads(d["state"])
    return d


def list_jobs(limit: int = 30) -> list[dict]:
    rows = conn().execute("SELECT id, created_at, status, mode, title FROM jobs ORDER BY created_at DESC LIMIT ?",
                          (limit,)).fetchall()
    return [dict(r) for r in rows]


def add_event(job_id: str, type_: str, agent: str | None, payload: dict) -> dict:
    ts = datetime.now().isoformat(timespec="milliseconds")
    with _lock:
        cur = conn().execute("INSERT INTO events (job_id, ts, type, agent, payload) VALUES (?,?,?,?,?)",
                             (job_id, ts, type_, agent, json.dumps(payload, default=str)))
        conn().commit()
        return {"id": cur.lastrowid, "job_id": job_id, "ts": ts, "type": type_, "agent": agent, "payload": payload}


def get_events(job_id: str) -> list[dict]:
    rows = conn().execute("SELECT * FROM events WHERE job_id = ? ORDER BY id", (job_id,)).fetchall()
    return [{**dict(r), "payload": json.loads(r["payload"])} for r in rows]


# --- factory ----------------------------------------------------------------------

def machines() -> list[dict]:
    return [dict(r) for r in conn().execute("SELECT * FROM machines ORDER BY id").fetchall()]


def bookings(machine_id: str | None = None, include_tentative_for: str | None = None) -> list[dict]:
    q = "SELECT * FROM bookings WHERE (kind != 'tentative' OR job_id = ?)"
    args: list = [include_tentative_for or ""]
    if machine_id:
        q += " AND machine_id = ?"
        args.append(machine_id)
    return [dict(r) for r in conn().execute(q + " ORDER BY start", args).fetchall()]


def busy_for(job_id: str) -> list[dict]:
    """Everything that occupies the cell for scheduling `job_id`: jobs, downtime, other jobs' holds."""
    rows = conn().execute("SELECT * FROM bookings WHERE NOT (kind = 'tentative' AND job_id = ?) ORDER BY start",
                          (job_id,)).fetchall()
    return [dict(r) for r in rows]


def replace_tentative(job_id: str, items: list[dict]) -> None:
    with _lock:
        c = conn()
        c.execute("DELETE FROM bookings WHERE job_id = ? AND kind = 'tentative'", (job_id,))
        for it in items:
            c.execute("INSERT INTO bookings (machine_id, job_id, label, kind, start, end) VALUES (?,?,?,?,?,?)",
                      (it["machine_id"], job_id, it["label"], "tentative", it["start"], it["end"]))
        c.commit()


def commit_tentative(job_id: str) -> int:
    with _lock:
        cur = conn().execute("UPDATE bookings SET kind = 'job' WHERE job_id = ? AND kind = 'tentative'", (job_id,))
        conn().commit()
        return cur.rowcount


def release_tentative(job_id: str) -> None:
    with _lock:
        conn().execute("DELETE FROM bookings WHERE job_id = ? AND kind = 'tentative'", (job_id,))
        conn().commit()
