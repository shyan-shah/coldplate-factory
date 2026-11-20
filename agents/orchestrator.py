"""Orchestrator: runs the test-lab agent pipeline, handles the verification rejection loop, and stops at the
engineer approval gate before anything runs. All artifacts shown to the engineer are assembled from tool outputs."""
from __future__ import annotations

import logging
import os
import traceback

from factory import db

from testlab.report import report_markdown

from . import intake, planner, verification, procedure, scheduling, report
from .common import get_campaign
from .core import AgentDef, JobContext, LiveRunner, run_scripted, model_name

log = logging.getLogger("orchestrator")

PIPELINE = [intake.AGENT, planner.AGENT, verification.AGENT, procedure.AGENT, scheduling.AGENT, report.AGENT]
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
            await self.handoff("intake", "planner", out["summary"])

            for round_ in range(1, MAX_REWORK + 2):
                pl = await self._run(planner.AGENT)
                cid = pl["campaign_id"]
                await ctx.artifact("campaign_selection", {
                    "round": round_, "selected": cid, "rationale": pl["rationale"],
                    "response_to_verification": pl["response_to_verification"], "campaign": get_campaign(ctx, cid)})
                await self.handoff("planner", "verification", f"{cid} submitted for verification (round {round_})")
                vr = await self._run(verification.AGENT)
                v = ctx.outputs["last_verification"]
                await ctx.artifact("verification", {**v, "round": round_, "agent_verdict": vr["verdict"],
                                                    "summary": vr["summary"], "required_changes": vr["required_changes"]})
                if vr["verdict"] == "approve":
                    break
                ctx.verification_feedback.append({"campaign_id": cid, "failures": v["failures"],
                                                  "summary": vr["summary"], "required_changes": vr["required_changes"]})
                await ctx.emit("rejection", "verification", {"from": "verification", "to": "planner",
                                                             "campaign_id": cid, "round": round_,
                                                             "failures": v["failures"],
                                                             "required_changes": vr["required_changes"]})
                if round_ > MAX_REWORK:
                    db.update_job(ctx.job_id, status="escalated", state=self.state())
                    await ctx.emit("job_status", None, {"status": "escalated",
                                                        "message": "Campaign could not pass verification; escalated to engineer"})
                    return
            await self.handoff("verification", "procedure", ctx.outputs["verification"]["summary"])

            pr = await self._run(procedure.AGENT)
            await ctx.artifact("procedure", {**ctx.outputs["procedure_result"], "review": pr})
            await self.handoff("procedure", "scheduling", pr["summary"])

            sc = await self._run(scheduling.AGENT)
            await ctx.artifact("schedule", {**ctx.outputs["schedule_result"], "summary": sc["summary"],
                                            "board": db.busy_for(""), "machines": db.machines()})
            await self.handoff("scheduling", "report", sc["summary"])

            ro = await self._run(report.AGENT)
            rep = ctx.outputs["report_result"]
            await ctx.artifact("report", {**rep, "review": ro, "markdown": report_markdown(rep)})
            await self.handoff("report", "engineer", "Campaign package complete, awaiting engineer release")

            await ctx.artifact("job_package", self.package())
            db.update_job(ctx.job_id, status="awaiting_approval", state=self.state())
            await ctx.emit("gate", None, {"status": "awaiting_approval", "package": self.package()})
        except Exception as e:  # noqa: BLE001 - any failure must reach the UI, not kill the server
            log.exception("pipeline failed")
            db.update_job(ctx.job_id, status="error", state=self.state())
            await ctx.emit("error", None, {"message": str(e), "trace": traceback.format_exc()[-2000:]})

    def package(self) -> dict:
        ctx = self.ctx
        cid = ctx.outputs["planner"]["campaign_id"]
        c = get_campaign(ctx, cid)
        v, sch, pr = ctx.outputs["last_verification"], ctx.outputs["schedule_result"], ctx.outputs["procedure_result"]
        rep = ctx.outputs["report_result"]
        return {
            "job_id": ctx.job_id, "customer": ctx.spec.get("customer"), "part_name": ctx.spec.get("part_name"),
            "component_type": ctx.spec.get("component_type"), "standard": c["standard"],
            "campaign_id": cid, "label": c["label"], "steps": c["totals"]["steps"],
            "samples_used": c["totals"]["samples_used"], "samples_supplied": ctx.spec["samples"],
            "coverage": v["coverage"], "checks_passed": f"{sum(x['pass'] for x in v['checks'])}/{len(v['checks'])}",
            "verification_rounds": len(ctx.verification_feedback) + 1,
            "bench_hours": pr["totals"]["bench_hours"], "partner_hours": pr["totals"]["partner_hours"],
            "cobot_handling_events": pr["totals"]["cobot_handling_events"],
            "cost_excl_partner_gbp": pr["cost_estimate_gbp"]["total_excl_partner"],
            "release": sch["release"], "last_test_end": sch["last_test_end"], "report_due": sch["report_due"],
            "deadline": sch["deadline"], "slack_days": sch["slack_days"],
            "unattended_rig_hours": sch["unattended_rig_hours"],
            "dry_run_counts": rep["counts"], "flagged": rep["flagged"],
            "campaigns_drafted": len(ctx.campaigns),
        }

    def state(self) -> dict:
        return {"outputs": self.ctx.outputs, "campaigns": {k: {"label": v["label"], "totals": v["totals"]}
                                                           for k, v in self.ctx.campaigns.items()},
                "artifact_kinds": list(self.ctx.artifacts)}
