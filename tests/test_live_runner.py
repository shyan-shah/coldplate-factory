"""Exercise the live (Claude) tool loop against a fake client that emits tool_use blocks."""
import asyncio
from types import SimpleNamespace as NS

import pytest

from agents import core
from agents.core import JobContext, LiveRunner
from agents.intake import AGENT as INTAKE
from app.demo_specs import demo_specs


def _msg(blocks, stop):
    return NS(content=blocks, stop_reason=stop, stop_details=None)


def text(t):
    return NS(type="text", text=t)


def think(t):
    return NS(type="thinking", thinking=t)


def use(i, name, inp):
    return NS(type="tool_use", id=i, name=name, input=inp)


class FakeStream:
    def __init__(self, msg):
        self.msg = msg

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def __aiter__(self):
        async def gen():
            for b in self.msg.content:
                if b.type == "text":
                    yield NS(type="content_block_delta", delta=NS(type="text_delta", text=b.text))
                elif b.type == "thinking":
                    yield NS(type="content_block_delta", delta=NS(type="thinking_delta", thinking=b.thinking))
        return gen()

    async def get_final_message(self):
        return self.msg


class FakeClient:
    def __init__(self, script, reject_fallbacks=False):
        self.script = list(script)
        self.calls = []
        self.reject_fallbacks = reject_fallbacks
        outer = self

        class _Messages:
            def stream(self, **kw):
                outer.calls.append(("std", {**kw, "messages": list(kw["messages"])}))
                return FakeStream(outer.script.pop(0))

        class _BetaMessages:
            def stream(self, **kw):
                outer.calls.append(("beta", {**kw, "messages": list(kw["messages"])}))
                if outer.reject_fallbacks:
                    import anthropic
                    import httpx2 as httpx  # anthropic 1.x+/2.x is built on httpx2
                    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
                    raise anthropic.BadRequestError("fallbacks not allowed",
                                                    response=httpx.Response(400, request=req), body=None)
                return FakeStream(outer.script.pop(0))

        self.messages = _Messages()
        self.beta = NS(messages=_BetaMessages())


def _ctx(events):
    async def emit(t, a, p, persist=True):
        events.append((t, a, p))
    return JobContext(job_id="T", raw_spec=demo_specs()["hx1200"]["spec"], emit_fn=emit, mode="live")


SCRIPT = [
    _msg([think("Need to validate first."), text("Checking the spec."), use("u1", "check_spec", {})], "tool_use"),
    _msg([text("Looks feasible.")], "end_turn"),  # forgets to submit -> runner nudges
    _msg([use("u2", "submit_intake", {"decision": "accept", "summary": "ok", "customer_questions": []})], "tool_use"),
]


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("CLAUDE_MODEL", "claude-opus-5-5")
    monkeypatch.setenv("AGENT_EFFORT", "low")
    monkeypatch.setattr(core, "_fallbacks_disabled", False)


def test_live_loop_tool_use_nudge_and_submit():
    events = []
    client = FakeClient(SCRIPT)
    out = asyncio.run(LiveRunner(client).run(INTAKE, _ctx(events)))
    assert out["decision"] == "accept"
    kinds = [e[0] for e in events]
    assert "agent_thinking" in kinds and "agent_message" in kinds and "tool_result" in kinds
    # request shape: adaptive thinking, explicit effort, fallbacks via beta, no sampling params
    mode, kw = client.calls[0]
    assert mode == "beta" and kw["fallbacks"] == "default" and core.FALLBACK_BETA in kw["betas"]
    assert kw["thinking"]["type"] == "adaptive" and kw["output_config"] == {"effort": "low"}
    assert "temperature" not in kw and "tool_choice" not in kw
    assert all(t.get("eager_input_streaming") for t in kw["tools"])
    # second request carries the tool result back in a single user message
    msgs = client.calls[1][1]["messages"]
    assert msgs[-1]["role"] == "user" and msgs[-1]["content"][0]["type"] == "tool_result"
    # third request includes the nudge
    assert "submit_intake" in client.calls[2][1]["messages"][-1]["content"]


def test_fallback_rejection_retries_without(monkeypatch):
    events = []
    client = FakeClient(SCRIPT, reject_fallbacks=True)
    out = asyncio.run(LiveRunner(client).run(INTAKE, _ctx(events)))
    assert out["decision"] == "accept"
    assert client.calls[0][0] == "beta" and client.calls[1][0] == "std"
    assert all(c[0] == "std" for c in client.calls[1:])


def test_bad_tool_input_returns_error_to_model():
    events = []
    script = [
        _msg([use("u1", "submit_intake", {"decision": "accept", "summary": "x", "customer_questions": []})], "tool_use"),
        _msg([use("u2", "check_spec", {})], "tool_use"),
        _msg([use("u3", "submit_intake", {"decision": "accept", "summary": "x", "customer_questions": []})], "tool_use"),
    ]
    client = FakeClient(script)
    asyncio.run(LiveRunner(client).run(INTAKE, _ctx(events)))
    errs = [e for e in events if e[0] == "tool_result" and e[2]["is_error"]]
    assert errs and "check_spec" in errs[0][2]["output"]["error"]


def test_refusal_raises():
    client = FakeClient([_msg([], "refusal")])
    with pytest.raises(RuntimeError, match="declined"):
        asyncio.run(LiveRunner(client).run(INTAKE, _ctx([])))


def test_unknown_model_sends_no_model_specific_params(monkeypatch):
    monkeypatch.setenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
    client = FakeClient(SCRIPT)
    asyncio.run(LiveRunner(client).run(INTAKE, _ctx([])))
    mode, kw = client.calls[0]
    assert mode == "std" and "thinking" not in kw and "output_config" not in kw
