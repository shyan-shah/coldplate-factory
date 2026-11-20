"""Run the agent pipeline headless and print the event stream.  Usage: python -m scripts.run_pipeline [spec_key]"""
import asyncio
import sys
import uuid

from dotenv import load_dotenv

load_dotenv()

from agents.core import JobContext  # noqa: E402
from agents.orchestrator import Orchestrator, resolve_mode  # noqa: E402
from app.demo_specs import demo_specs  # noqa: E402
from factory import db  # noqa: E402


async def main(key: str) -> None:
    db.init()
    spec = demo_specs()[key]["spec"]
    job_id = "J-" + uuid.uuid4().hex[:6].upper()
    mode = resolve_mode()
    db.create_job(job_id, spec["part_name"], spec, mode)

    async def emit(type_, agent, payload, persist=True):
        if persist:
            db.add_event(job_id, type_, agent, payload)
        if type_ in ("agent_delta", "thinking_delta"):
            return
        if type_ == "tool_result":
            print(f"   <- {payload['tool']} {'ERROR ' + str(payload['output']) if payload['is_error'] else ''}")
        elif type_ == "tool_call":
            print(f"   -> {agent}.{payload['tool']}({str(payload['input'])[:120]})")
        elif type_ in ("agent_message", "agent_thinking"):
            print(f"[{agent}] {payload['text']}\n")
        elif type_ == "artifact":
            print(f"   [artifact {payload['kind']}]")
        else:
            print(f"== {type_} {agent or ''} {str(payload)[:300]}")

    ctx = JobContext(job_id=job_id, raw_spec=spec, emit_fn=emit, mode=mode)
    await Orchestrator(ctx).run()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "cp1400"))
