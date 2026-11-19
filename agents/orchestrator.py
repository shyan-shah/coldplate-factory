"""Orchestrator: runs the agent pipeline, handles the verification rejection loop, and stops at the
engineer approval gate.  All artifacts shown to the engineer are assembled from tool outputs."""
from __future__ import annotations

import logging
import os
import traceback

from factory import db

from . import intake, thermal_design, verification, process_planning, scheduling, qa
from .common import get_design
from .core import AgentDef, JobContext, LiveRunner, run_scripted, model_name

log = logging.getLogger("orchestrator")

PIPELINE = [intake.AGENT, thermal_design.AGENT, verification.AGENT, process_planning.AGENT, scheduling.AGENT, qa.AGENT]
AGENTS = {a.key: a for a in PIPELINE}
MAX_REWORK = 3


def resolve_mode() -> str:
    mode = os.environ.get("AGENT_MODE", "auto").lower()
    if mode == "auto":
        return "live" if os.environ.get("ANTHROPIC_API_KEY") else "scripted"
    return mode


class Orchestrator:
    def __init__(self, ctx: JobContext, live_runner: LiveRunner | None = None):
        self.ctx = ctx
        self.live = live_runner

    async def _run(self, agent: AgentDef) -> dict:
        await self.ctx.emit("agent_started", agent.key, {"name": agent.name, "role": agent.role})
        if self.ctx.mode == "live":
            if self.live is None:
                self.live = LiveRunner()
            out = await self.live.run(agent, self.ctx)
        else:
            out = await run_scripted(agent, self.ctx)
        await self.ctx.emit("agent_finished", agent.key, {"name": agent.name, "output": out})
        return out

    async def handoff(self, src: str, dst: str, note: str) -> None:
        await self.ctx.emit("handoff", src, {"from": src, "to": dst, "note": note})

    async def run(self) -> None:
        ctx = self.ctx
        try:
            await ctx.emit("job_started", None, {"mode": ctx.mode, "model": model_name() if ctx.mode == "live" else None,
                                                 "spec": ctx.raw_spec})
            out = await self._run(intake.AGENT)
            check = ctx.outputs["intake_check"]
            await ctx.artifact("spec_check", {**check, "decision": out["decision"], "summary": out["summary"],
                                              "customer_questions": out["customer_questions"]})
            if out["decision"] != "accept":
                db.update_job(ctx.job_id, status="needs_clarification", state=self.state())
                await ctx.emit("job_status", None, {"status": "needs_clarification",
                                                    "message": "Returned to customer for clarification"})
                return
            await self.handoff("intake", "thermal_design", out["summary"])

            for round_ in range(1, MAX_REWORK + 2):
                td = await self._run(thermal_design.AGENT)
                sel = td["selected_design_id"]
                await ctx.artifact("design_selection", {
                    "round": round_, "selected": sel, "rationale": td["rationale"],
                    "response_to_verification": td["response_to_verification"],
                    "candidates": [{k: v for k, v in c.items() if k != "full"} for c in ctx.artifacts["design_candidates"]],
                    "selected_full": get_design(ctx, sel)["result"]})
                await self.handoff("thermal_design", "verification", f"{sel} submitted for verification (round {round_})")
                vr = await self._run(verification.AGENT)
                v = ctx.outputs["last_verification"]
                await ctx.artifact("verification", {**v, "round": round_, "agent_verdict": vr["verdict"],
                                                    "summary": vr["summary"], "required_changes": vr["required_changes"]})
                if vr["verdict"] == "approve":
                    break
                ctx.verification_feedback.append({"design_id": sel, "failures": v["failures"],
                                                  "summary": vr["summary"], "required_changes": vr["required_changes"]})
                await ctx.emit("rejection", "verification", {"from": "verification", "to": "thermal_design",
                                                             "design_id": sel, "round": round_,
                                                             "failures": v["failures"],
                                                             "required_changes": vr["required_changes"]})
                if round_ > MAX_REWORK:
                    db.update_job(ctx.job_id, status="escalated", state=self.state())
                    await ctx.emit("job_status", None, {"status": "escalated",
                                                        "message": "Design could not pass verification; escalated to engineer"})
                    return
            await self.handoff("verification", "process_planning", ctx.outputs["verification"]["summary"])

            pp = await self._run(process_planning.AGENT)
            await ctx.artifact("process_plan", {**ctx.outputs["process_plan_result"], "review": pp})
            await self.handoff("process_planning", "scheduling", pp["summary"])

            sc = await self._run(scheduling.AGENT)
            await ctx.artifact("schedule", {**ctx.outputs["schedule_result"], "summary": sc["summary"],
                                            "board": db.bookings(include_tentative_for=ctx.job_id),
                                            "machines": db.machines()})
            await self.handoff("scheduling", "qa", sc["summary"])

            qo = await self._run(qa.AGENT)
            await ctx.artifact("qa_plan", {**ctx.outputs["qa_result"], "review": qo})
            await self.handoff("qa", "engineer", "Job package complete, awaiting engineer approval")

            await ctx.artifact("job_package", self.package())
            db.update_job(ctx.job_id, status="awaiting_approval", state=self.state())
            await ctx.emit("gate", None, {"status": "awaiting_approval", "package": self.package()})
        except Exception as e:  # noqa: BLE001 - any failure must reach the UI, not kill the server
            log.exception("pipeline failed")
            db.update_job(ctx.job_id, status="error", state=self.state())
            await ctx.emit("error", None, {"message": str(e), "trace": traceback.format_exc()[-2000:]})

    def package(self) -> dict:
        ctx = self.ctx
        sel = ctx.outputs["thermal_design"]["selected_design_id"]
        d = get_design(ctx, sel)
        r, sch, pp = d["result"], ctx.outputs["schedule_result"], ctx.outputs["process_plan_result"]
        v = ctx.outputs["last_verification"]
        return {
            "job_id": ctx.job_id, "customer": ctx.spec.get("customer"), "part_name": ctx.spec.get("part_name"),
            "design_id": sel, "design_params": d["params"], "label": d["label"],
            "t_case_c": r["thermal"]["t_case_c"], "dp_kpa": r["hydraulics"]["dp_kpa"],
            "worst_case": v["worst_case"], "r_case_to_inlet_k_w": r["thermal"]["r_case_to_inlet_k_w"],
            "limits": {"max_case_c": ctx.spec["max_case_temp_c"], "max_dp_kpa": ctx.spec["max_pressure_drop_kpa"]},
            "verification_rounds": len(ctx.verification_feedback) + 1,
            "cost_per_part_usd": pp["cost_per_part_usd"]["total"], "batch_cost_usd": pp["batch_cost_usd"],
            "cycle_time_min": pp["cycle_time_min_per_part"],
            "delivery_date": sch["delivery_date"], "deadline": sch["deadline"], "slack_days": sch["slack_days"],
            "quantity": ctx.spec["quantity"], "designs_evaluated": len(ctx.designs),
            "sweep_variants": sum(len(s["points"]) for s in ctx.artifacts.get("sweeps", [])),
        }

    def state(self) -> dict:
        return {"outputs": self.ctx.outputs, "designs": {k: {"params": v["params"], "label": v["label"]}
                                                         for k, v in self.ctx.designs.items()},
                "artifact_kinds": list(self.ctx.artifacts)}
