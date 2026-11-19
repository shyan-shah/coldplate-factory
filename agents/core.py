"""Agent runtime: tool definitions, job context, live (Claude) and scripted runners.

Both runners go through the same `execute_tool`, so every number the UI shows comes
from a deterministic tool function, whichever runner drives the agent.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

log = logging.getLogger("agents")


class ToolError(Exception):
    """Raised by a tool handler for bad input; returned to the model as is_error."""


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    handler: Callable[["JobContext", dict], dict]
    terminal: bool = False          # a submit_* tool: a valid call ends the agent's turn
    artifact: Callable[["JobContext"], tuple[str, dict]] | None = None  # UI artifact refreshed after each call

    def api_def(self) -> dict:
        d = {"name": self.name, "description": self.description, "input_schema": self.input_schema,
             "eager_input_streaming": True}
        if self.terminal:
            d["strict"] = True
        return d


@dataclass
class AgentDef:
    key: str
    name: str
    role: str
    system_prompt: str
    tools: list[Tool]
    build_task: Callable[["JobContext"], str]
    scripted: Callable[["ScriptedSession"], Awaitable[None]]
    effort_env: str = "AGENT_EFFORT"

    def tool(self, name: str) -> Tool:
        for t in self.tools:
            if t.name == name:
                return t
        raise ToolError(f"Unknown tool '{name}'")

    @property
    def submit_tool(self) -> Tool:
        return next(t for t in self.tools if t.terminal)


Emit = Callable[[str, str | None, dict, bool], Awaitable[None]]


@dataclass
class JobContext:
    job_id: str
    raw_spec: dict
    emit_fn: Emit
    mode: str
    spec: dict = field(default_factory=dict)          # normalized spec (after intake)
    designs: dict = field(default_factory=dict)       # design_id -> {"params", "result", "label"}
    schedule_options: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)       # agent key -> submitted output
    artifacts: dict = field(default_factory=dict)     # deterministic artifacts for the UI
    verification_feedback: list = field(default_factory=list)
    _counters: dict = field(default_factory=dict)

    def next_id(self, prefix: str) -> str:
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        return f"{prefix}{self._counters[prefix]}"

    async def emit(self, type_: str, agent: str | None, payload: dict, persist: bool = True) -> None:
        await self.emit_fn(type_, agent, payload, persist)

    async def artifact(self, kind: str, data: dict) -> None:
        self.artifacts[kind] = data
        await self.emit("artifact", None, {"kind": kind, "data": data})


def compact(obj: Any, sig: int = 4) -> Any:
    """Round floats to `sig` significant digits for model-facing tool output."""
    if isinstance(obj, float):
        if obj == 0 or obj != obj:
            return obj
        return float(f"{obj:.{sig}g}")
    if isinstance(obj, dict):
        return {k: compact(v, sig) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [compact(v, sig) for v in obj]
    return obj


async def execute_tool(agent: AgentDef, ctx: JobContext, name: str, tool_input: dict,
                       call_id: str) -> tuple[dict, bool, bool]:
    """Run a tool, emit call/result events. Returns (result, is_error, terminal_ok)."""
    await ctx.emit("tool_call", agent.key, {"tool": name, "input": tool_input, "call_id": call_id})
    try:
        tool = agent.tool(name)
        if not isinstance(tool_input, dict):
            raise ToolError("tool input must be a JSON object")
        result = tool.handler(ctx, tool_input)
        is_error, terminal_ok = False, tool.terminal
    except (ToolError, ValueError, KeyError, TypeError) as e:
        result, is_error, terminal_ok = {"error": str(e)}, True, False
    except Exception as e:  # noqa: BLE001 - surface unexpected tool failures to the model, not the UI
        log.exception("tool %s crashed", name)
        result, is_error, terminal_ok = {"error": f"internal tool error: {e}"}, True, False
    await ctx.emit("tool_result", agent.key, {"tool": name, "call_id": call_id, "output": compact(result),
                                              "is_error": is_error})
    if not is_error and tool.artifact is not None:
        await ctx.artifact(*tool.artifact(ctx))
    return result, is_error, terminal_ok


# --- scripted runner -----------------------------------------------------------------

class ScriptedSession:
    """Deterministic stand-in for the LLM: scripted choices and prose, real tools."""

    def __init__(self, agent: AgentDef, ctx: JobContext):
        self.agent, self.ctx = agent, ctx
        self.delay = float(os.environ.get("SCRIPTED_STEP_DELAY", "0.6"))
        self.submitted: dict | None = None
        self._n = 0

    async def pause(self, factor: float = 1.0) -> None:
        if self.delay > 0:
            await asyncio.sleep(self.delay * factor)

    async def say(self, text: str) -> None:
        # Stream in chunks so the UI shows the agent "typing", then persist the full message.
        words = text.split(" ")
        for i in range(0, len(words), 6):
            await self.ctx.emit("agent_delta", self.agent.key, {"text": " ".join(words[i:i + 6]) + " "},
                                persist=False)
            if self.delay > 0:
                await asyncio.sleep(min(0.05, self.delay / 10))
        await self.ctx.emit("agent_message", self.agent.key, {"text": text})
        await self.pause(0.5)

    async def tool(self, name: str, tool_input: dict) -> dict:
        self._n += 1
        result, is_error, terminal_ok = await execute_tool(self.agent, self.ctx, name, tool_input,
                                                           f"s-{self.agent.key}-{self._n}")
        if is_error:
            raise RuntimeError(f"scripted call {name} failed: {result}")
        if terminal_ok:
            self.submitted = tool_input
        await self.pause()
        return result


async def run_scripted(agent: AgentDef, ctx: JobContext) -> dict:
    s = ScriptedSession(agent, ctx)
    await agent.scripted(s)
    if s.submitted is None:
        raise RuntimeError(f"{agent.name} script ended without submitting")
    return s.submitted


# --- live runner (Claude via Anthropic Messages API, manual tool loop) ------------------

FALLBACK_BETA = "server-side-fallback-2026-07-01"
_ADAPTIVE_MARKERS = ("opus-4-6", "sonnet-4-6", "opus-4-7", "opus-4-8", "opus-5", "sonnet-5", "fable", "mythos",
                     "haiku-5")
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-fable-5-2", "claude-sonnet-5-5"}
_fallbacks_disabled = False


def model_name() -> str:
    return os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")


def _request_options(agent: AgentDef) -> dict:
    m = model_name().lower()
    opts: dict = {}
    if any(x in m for x in _ADAPTIVE_MARKERS):
        opts["thinking"] = {"type": "adaptive", "display": "summarized"}
        effort = os.environ.get(agent.effort_env) or os.environ.get("AGENT_EFFORT", "low")
        opts["output_config"] = {"effort": effort}
    return opts


def _use_fallbacks() -> bool:
    return (not _fallbacks_disabled and model_name() in _FALLBACK_MODELS
            and os.environ.get("ENABLE_FALLBACKS", "1") != "0")


class LiveRunner:
    def __init__(self, client=None):
        if client is None:
            import anthropic
            client = anthropic.AsyncAnthropic()
        self.client = client

    def _stream(self, agent: AgentDef, messages: list, use_fallbacks: bool):
        kwargs = dict(model=model_name(), max_tokens=32000, system=agent.system_prompt,
                      tools=[t.api_def() for t in agent.tools], messages=messages, **_request_options(agent))
        if use_fallbacks:
            return self.client.beta.messages.stream(betas=[FALLBACK_BETA], fallbacks="default", **kwargs)
        return self.client.messages.stream(**kwargs)

    async def _call(self, agent: AgentDef, ctx: JobContext, messages: list):
        global _fallbacks_disabled
        import anthropic
        use_fb = _use_fallbacks()
        try:
            return await self._stream_once(agent, ctx, messages, use_fb)
        except anthropic.BadRequestError as e:
            if not use_fb:
                raise
            log.warning("request with fallbacks rejected (%s); retrying without", e)
            _fallbacks_disabled = True
            return await self._stream_once(agent, ctx, messages, False)

    async def _stream_once(self, agent: AgentDef, ctx: JobContext, messages: list, use_fb: bool):
        async with self._stream(agent, messages, use_fb) as stream:
            async for event in stream:
                if getattr(event, "type", None) != "content_block_delta":
                    continue
                d = event.delta
                if d.type == "text_delta" and d.text:
                    await ctx.emit("agent_delta", agent.key, {"text": d.text}, persist=False)
                elif d.type == "thinking_delta" and getattr(d, "thinking", ""):
                    await ctx.emit("thinking_delta", agent.key, {"text": d.thinking}, persist=False)
            return await stream.get_final_message()

    async def run(self, agent: AgentDef, ctx: JobContext, max_turns: int = 16) -> dict:
        messages: list = [{"role": "user", "content": agent.build_task(ctx)}]
        nudges = 0
        for _turn in range(max_turns):
            msg = await self._call(agent, ctx, messages)
            thinking = "".join(getattr(b, "thinking", "") or "" for b in msg.content if b.type == "thinking")
            text = "".join(b.text for b in msg.content if b.type == "text")
            if thinking.strip():
                await ctx.emit("agent_thinking", agent.key, {"text": thinking})
            if text.strip():
                await ctx.emit("agent_message", agent.key, {"text": text})

            if msg.stop_reason == "refusal":
                details = getattr(msg, "stop_details", None)
                raise RuntimeError(f"{agent.name}: model declined the request ({details})")
            if msg.stop_reason == "max_tokens":
                raise RuntimeError(f"{agent.name}: response hit max_tokens before finishing")

            messages.append({"role": "assistant", "content": msg.content})
            if msg.stop_reason == "pause_turn":
                continue
            uses = [b for b in msg.content if b.type == "tool_use"]
            if not uses:
                if nudges >= 2:
                    raise RuntimeError(f"{agent.name} stopped without calling {agent.submit_tool.name}")
                nudges += 1
                messages.append({"role": "user", "content":
                                 f"Finish by calling the {agent.submit_tool.name} tool with your decision."})
                continue
            results, submitted = [], None
            for u in uses:  # all results go back in one user message
                res, is_err, terminal_ok = await execute_tool(agent, ctx, u.name, u.input, u.id)
                results.append({"type": "tool_result", "tool_use_id": u.id,
                                "content": json.dumps(compact(res)), "is_error": is_err})
                if terminal_ok:
                    submitted = u.input
            if submitted is not None:
                return submitted
            messages.append({"role": "user", "content": results})
        raise RuntimeError(f"{agent.name} did not finish within {max_turns} turns")
