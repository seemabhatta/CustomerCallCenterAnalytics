"""Tests for the second-generation LLM client."""
import os
import dataclasses

import pytest
from pydantic import BaseModel

from src.infrastructure.llm.llm_client_v2 import (
    LLMClientV2,
    LLMProvider,
    RequestOptions,
    RequestSpec,
    ResponseEnvelope,
    ResponseUsage,
    RetryPolicy,
    ToolCall,
)


class DummyModel(BaseModel):
    value: int


class FakeProvider(LLMProvider):
    def __init__(self) -> None:
        self.last_spec: RequestSpec | None = None

    def run(self, spec: RequestSpec) -> ResponseEnvelope:
        self.last_spec = spec
        return ResponseEnvelope(
            text="ok",
            parsed=None,
            messages=list(spec.messages),
            usage=ResponseUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            response_id="resp-1",
            latency_ms=12.5,
            raw={"mock": True},
        )

    async def arun(self, spec: RequestSpec) -> ResponseEnvelope:
        self.last_spec = spec
        return ResponseEnvelope(
            text="async",
            parsed=None,
            messages=list(spec.messages),
            usage=None,
            response_id="resp-async",
            latency_ms=20.0,
            raw={"mock": True},
        )

    async def astream(self, spec: RequestSpec):
        self.last_spec = spec
        yield ResponseEnvelope(
            text="chunk",
            parsed=None,
            messages=list(spec.messages),
            usage=None,
            response_id="resp-stream",
            latency_ms=1.0,
            raw={"event": 1},
        )


@pytest.fixture
def fake_provider():
    return FakeProvider()


def test_client_applies_hooks(fake_provider):
    def hook(spec: RequestSpec) -> RequestSpec:
        new_messages = list(spec.messages) + [{"role": "system", "content": "hooked"}]
        return dataclasses.replace(spec, messages=new_messages)

    client = LLMClientV2(provider=fake_provider, hooks=[hook])

    response = client.run([{ "role": "user", "content": "hello" }])

    assert response.text == "ok"
    assert fake_provider.last_spec is not None
    assert fake_provider.last_spec.messages[-1]["content"] == "hooked"


@pytest.mark.asyncio
async def test_astream(fake_provider):
    client = LLMClientV2(provider=fake_provider)

    chunks = []
    async for chunk in client.astream([{ "role": "user", "content": "stream" }]):
        chunks.append(chunk)

    assert len(chunks) == 1
    assert chunks[0].text == "chunk"
    assert fake_provider.last_spec.messages[0]["content"] == "stream"


def test_response_envelope_require_methods():
    env = ResponseEnvelope(
        text="hello",
        parsed=DummyModel(value=1),
        messages=[],
        usage=None,
        response_id="resp",
        latency_ms=5.0,
        raw={},
    )

    assert env.require_text() == "hello"
    assert env.require_parsed().value == 1

    env_missing = ResponseEnvelope(
        text=None,
        parsed=None,
        messages=[],
        usage=None,
        response_id=None,
        latency_ms=0.0,
        raw={},
    )

    with pytest.raises(ValueError):
        env_missing.require_text()
    with pytest.raises(ValueError):
        env_missing.require_parsed()


def test_retry_policy_backoff_range():
    policy = RetryPolicy(base_delay=0.5, jitter=(0.9, 1.1))
    sleep = policy.compute_sleep(2)
    assert 0.5 * (2**2) * 0.9 <= sleep <= 0.5 * (2**2) * 1.1


def test_tool_call_dataclass_repr():
    tool = ToolCall(name="fetch", arguments={"id": 1})
    assert tool.name == "fetch"
    assert tool.arguments == {"id": 1}


def test_request_options_defaults():
    options = RequestOptions()
    assert options.temperature == 0.2
    assert options.max_output_tokens is None


def test_openai_provider_requires_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from src.infrastructure.llm.llm_client_v2 import OpenAIProvider

    with pytest.raises(RuntimeError):
        OpenAIProvider(api_key=None)


@pytest.mark.asyncio
async def test_client_async_run(fake_provider):
    client = LLMClientV2(provider=fake_provider)
    resp = await client.arun([{ "role": "user", "content": "ping" }])
    assert resp.text == "async"
    assert fake_provider.last_spec.messages[0]["content"] == "ping"
