"""Second-generation OpenAI client with rich ergonomics.

This module introduces a Provider-agnostic interface tailored for
agentic workflows. It abandons backwards compatibility with
`OpenAIWrapper` v1 in favour of:

- explicit request/response dataclasses
- structured prompt/context handling
- built-in retry, audit, and telemetry hooks
- streaming-first primitives
- provider abstraction (OpenAI is the default implementation)
"""
from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import os
import random
import time
from contextlib import AbstractAsyncContextManager, AsyncExitStack, nullcontext
from typing import Any, AsyncGenerator, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Type, Union

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel

from src.infrastructure.telemetry import get_tracer

load_dotenv()

logger = logging.getLogger(__name__)

Message = Dict[str, Union[str, Dict[str, Any]]]


@dataclasses.dataclass(frozen=True)
class ToolCall:
    """Tool invocation planned for a completion."""

    name: str
    arguments: Dict[str, Any]


@dataclasses.dataclass(frozen=True)
class RequestOptions:
    """Tunable request knobs."""

    temperature: float = 0.2
    max_output_tokens: Optional[int] = None
    top_p: Optional[float] = None
    seed: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclasses.dataclass(frozen=True)
class RequestSpec:
    """Full description of an LLM call."""

    messages: Sequence[Message]
    response_schema: Optional[Type[BaseModel]] = None
    system_prompt: Optional[str] = None
    tools: Optional[List[ToolCall]] = None
    options: RequestOptions = RequestOptions()
    provider_overrides: Optional[Dict[str, Any]] = None


@dataclasses.dataclass(frozen=True)
class ResponseUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cached_tokens: Optional[int] = None


@dataclasses.dataclass(frozen=True)
class ResponseEnvelope:
    """Standardised response wrapper for all providers."""

    text: Optional[str]
    parsed: Optional[BaseModel]
    messages: List[Message]
    usage: Optional[ResponseUsage]
    response_id: Optional[str]
    latency_ms: float
    raw: Any

    def require_text(self) -> str:
        if self.text is None:
            raise ValueError("response.text is not available")
        return self.text

    def require_parsed(self) -> BaseModel:
        if self.parsed is None:
            raise ValueError("response.parsed is not available")
        return self.parsed


class LLMProvider:
    """Interface that any LLM backend must implement."""

    async def arun(self, spec: RequestSpec) -> ResponseEnvelope:  # pragma: no cover - interface
        raise NotImplementedError

    def run(self, spec: RequestSpec) -> ResponseEnvelope:  # pragma: no cover - interface
        raise NotImplementedError

    async def astream(self, spec: RequestSpec) -> AsyncGenerator[ResponseEnvelope, None]:  # pragma: no cover - interface
        raise NotImplementedError


@dataclasses.dataclass
class RetryPolicy:
    max_attempts: int = 3
    base_delay: float = 0.5
    max_delay: float = 8.0
    backoff_multiplier: float = 2.0
    jitter: Tuple[float, float] = (0.8, 1.2)

    def compute_sleep(self, attempt: int) -> float:
        delay = min(self.base_delay * (self.backoff_multiplier ** attempt), self.max_delay)
        jitter = random.uniform(*self.jitter)
        return delay * jitter


class OpenAIProvider(LLMProvider):
    """OpenAI-backed implementation."""

    def __init__(
        self,
        *,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        organization: Optional[str] = None,
        timeout: Optional[float] = None,
        retry_policy: RetryPolicy = RetryPolicy(),
    ) -> None:
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set for OpenAIProvider")

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.timeout = timeout or float(os.getenv("OPENAI_TIMEOUT", "45.0"))
        self.retry_policy = retry_policy

        self._client = OpenAI(api_key=api_key, organization=organization, timeout=self.timeout)
        self._aclient = AsyncOpenAI(api_key=api_key, organization=organization, timeout=self.timeout)

    # --- public API -----------------------------------------------------
    def run(self, spec: RequestSpec) -> ResponseEnvelope:
        return asyncio.run(self.arun(spec))

    async def arun(self, spec: RequestSpec) -> ResponseEnvelope:
        messages = self._build_messages(spec)
        schema_payload = self._schema_payload(spec)

        attempt = 0
        last_exc: Optional[Exception] = None

        while attempt < self.retry_policy.max_attempts:
            tracer = get_tracer()
            context = tracer.start_as_current_span("openai.llm.arun") if tracer else nullcontext()
            start = time.perf_counter()

            with context as span:
                if span:
                    span.set_attribute("llm.provider", "openai")
                    span.set_attribute("llm.model", self.model)
                    span.set_attribute("llm.attempt", attempt + 1)

                try:
                    response = await self._dispatch_async(messages, schema_payload, spec)
                    latency_ms = (time.perf_counter() - start) * 1000
                    env = self._build_envelope(response, latency_ms, spec.response_schema)
                    if span:
                        span.set_attribute("llm.latency_ms", env.latency_ms)
                        span.set_attribute("llm.response_id", env.response_id or "")
                    return env
                except Exception as exc:  # pragma: no cover - error path
                    last_exc = exc
                    retryable = self._is_retryable(exc) and attempt < self.retry_policy.max_attempts - 1
                    if span:
                        span.record_exception(exc)
                        span.set_attribute("llm.retryable", retryable)
                    logger.warning("OpenAIProvider request failed", exc_info=exc, extra={"retryable": retryable, "attempt": attempt + 1})
                    if not retryable:
                        raise
                    await asyncio.sleep(self.retry_policy.compute_sleep(attempt))
                    attempt += 1

        assert last_exc is not None  # pragma: no cover
        raise last_exc

    async def astream(self, spec: RequestSpec) -> AsyncGenerator[ResponseEnvelope, None]:
        messages = self._build_messages(spec)
        schema_payload = self._schema_payload(spec)

        tracer = get_tracer()
        context = tracer.start_as_current_span("openai.llm.astream") if tracer else nullcontext()
        start = time.perf_counter()

        with context as span:
            if span:
                span.set_attribute("llm.provider", "openai")
                span.set_attribute("llm.model", self.model)

            params = {
                "model": self.model,
                "input": messages,
                "response_format": schema_payload,
                "temperature": spec.options.temperature,
                "max_output_tokens": spec.options.max_output_tokens,
                "top_p": spec.options.top_p,
                **(spec.provider_overrides or {}),
            }

            # Seed parameter not supported by current OpenAI client version
            # if spec.options.seed is not None:
            #     params["seed"] = spec.options.seed

            response = await self._aclient.responses.stream(**params)

            async with response as stream:
                async for event in stream:
                    if event.type != "response.output_text.delta":
                        continue
                    latency_ms = (time.perf_counter() - start) * 1000
                    yield ResponseEnvelope(
                        text=event.delta,
                        parsed=None,
                        messages=list(messages),
                        usage=None,
                        response_id=event.response_id,
                        latency_ms=latency_ms,
                        raw=event,
                    )

    # --- helpers --------------------------------------------------------
    async def _dispatch_async(self, messages: List[Message], schema_payload: Optional[Dict[str, Any]], spec: RequestSpec) -> Any:
        kwargs = {
            "model": self.model,
            "input": messages,
            "temperature": spec.options.temperature,
            "max_output_tokens": spec.options.max_output_tokens,
            "top_p": spec.options.top_p,
            "seed": spec.options.seed,
        }
        if schema_payload:
            kwargs["response_format"] = schema_payload
        if spec.provider_overrides:
            kwargs.update(spec.provider_overrides)

        return await self._aclient.responses.create(**kwargs)

    def _build_envelope(self, response: Any, latency_ms: float, schema: Optional[Type[BaseModel]]) -> ResponseEnvelope:
        text_output = getattr(response, "output_text", None)
        parsed_model: Optional[BaseModel] = None
        if schema and text_output:
            parsed_model = schema.model_validate_json(text_output)

        usage_raw = getattr(response, "usage", None)
        usage = None
        if usage_raw is not None:
            if hasattr(usage_raw, "model_dump"):
                usage_raw = usage_raw.model_dump()
            usage = ResponseUsage(
                prompt_tokens=usage_raw.get("prompt_tokens", 0),
                completion_tokens=usage_raw.get("completion_tokens", 0),
                total_tokens=usage_raw.get("total_tokens", 0),
                cached_tokens=usage_raw.get("cached_tokens"),
            )

        return ResponseEnvelope(
            text=text_output,
            parsed=parsed_model,
            messages=list(response.input) if hasattr(response, "input") else [],
            usage=usage,
            response_id=getattr(response, "id", None),
            latency_ms=latency_ms,
            raw=response,
        )

    def _build_messages(self, spec: RequestSpec) -> List[Message]:
        messages: List[Message] = []
        if spec.system_prompt:
            messages.append({"role": "system", "content": spec.system_prompt})
        messages.extend(spec.messages)
        return messages

    def _schema_payload(self, spec: RequestSpec) -> Optional[Dict[str, Any]]:
        if spec.response_schema is None:
            return None
        schema = spec.response_schema.model_json_schema()
        self._enforce_schema_strictness(schema)
        return {
            "type": "json_schema",
            "json_schema": {
                "name": spec.response_schema.__name__,
                "schema": schema,
                "strict": True,
            },
        }

    def _enforce_schema_strictness(self, schema: Dict[str, Any]) -> None:
        def recurse(obj: Any) -> None:
            if isinstance(obj, dict):
                if obj.get("type") == "object" and "additionalProperties" not in obj:
                    obj["additionalProperties"] = False
                if "anyOf" in obj:
                    for node in obj["anyOf"]:
                        if isinstance(node, dict) and node.get("type") == "object":
                            node["additionalProperties"] = False
                if "$ref" in obj and "description" in obj:
                    obj.pop("description", None)
                for value in obj.values():
                    recurse(value)
            elif isinstance(obj, list):
                for item in obj:
                    recurse(item)

        recurse(schema)
        if schema.get("type") == "object" and "additionalProperties" not in schema:
            schema["additionalProperties"] = False

    def _is_retryable(self, exc: Exception) -> bool:
        status = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
        if status in {408, 409, 425, 429, 500, 502, 503, 504}:
            return True
        code = getattr(exc, "type", "") or getattr(exc, "code", "")
        if isinstance(code, str) and any(token in code.lower() for token in ("timeout", "overloaded", "retry")):
            return True
        return False


class LLMClientV2:
    """High-level façade exposing sync/async operations."""

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        hooks: Optional[List[Callable[[RequestSpec], RequestSpec]]] = None,
    ) -> None:
        self.provider = provider or OpenAIProvider()
        self.hooks = hooks or []

    def register_hook(self, hook: Callable[[RequestSpec], RequestSpec]) -> None:
        self.hooks.append(hook)

    def run(
        self,
        messages: Sequence[Message],
        *,
        response_schema: Optional[Type[BaseModel]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[ToolCall]] = None,
        options: Optional[RequestOptions] = None,
        provider_overrides: Optional[Dict[str, Any]] = None,
    ) -> ResponseEnvelope:
        spec = RequestSpec(
            messages=messages,
            response_schema=response_schema,
            system_prompt=system_prompt,
            tools=tools,
            options=options or RequestOptions(),
            provider_overrides=provider_overrides,
        )
        spec = self._apply_hooks(spec)
        return self.provider.run(spec)

    async def arun(
        self,
        messages: Sequence[Message],
        *,
        response_schema: Optional[Type[BaseModel]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[ToolCall]] = None,
        options: Optional[RequestOptions] = None,
        provider_overrides: Optional[Dict[str, Any]] = None,
    ) -> ResponseEnvelope:
        spec = RequestSpec(
            messages=messages,
            response_schema=response_schema,
            system_prompt=system_prompt,
            tools=tools,
            options=options or RequestOptions(),
            provider_overrides=provider_overrides,
        )
        spec = self._apply_hooks(spec)
        return await self.provider.arun(spec)

    async def astream(
        self,
        messages: Sequence[Message],
        *,
        response_schema: Optional[Type[BaseModel]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[ToolCall]] = None,
        options: Optional[RequestOptions] = None,
        provider_overrides: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[ResponseEnvelope, None]:
        spec = RequestSpec(
            messages=messages,
            response_schema=response_schema,
            system_prompt=system_prompt,
            tools=tools,
            options=options or RequestOptions(),
            provider_overrides=provider_overrides,
        )
        spec = self._apply_hooks(spec)
        async for chunk in self.provider.astream(spec):
            yield chunk

    def _apply_hooks(self, spec: RequestSpec) -> RequestSpec:
        for hook in self.hooks:
            spec = hook(spec)
        return spec


__all__ = [
    "LLMClientV2",
    "OpenAIProvider",
    "RequestSpec",
    "RequestOptions",
    "ResponseEnvelope",
    "ResponseUsage",
    "ToolCall",
    "RetryPolicy",
]
