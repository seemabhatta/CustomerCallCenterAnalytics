"""OpenAI Responses API wrapper with opinionated defaults.

Centralizes configuration, observability and schema handling for
synchronous and asynchronous calls. Keeps call-sites minimal while
following current platform best practices (JSON schema strictness,
retryable failures, token accounting).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import time
from contextlib import nullcontext
from typing import Any, Dict, List, Optional, Type, Union

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel

from src.infrastructure.telemetry import get_tracer

# Load environment variables
load_dotenv()

# Logger for minimal logging (auto-correlated with traces)
logger = logging.getLogger(__name__)


MessageInput = Union[str, List[Dict[str, str]]]


class OpenAIWrapper:
    """Wrapper for OpenAI Responses API with structured outputs."""

    def __init__(
        self,
        *,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: int = 2,
        backoff_base: float = 0.5,
    ) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set in environment")

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.timeout = timeout or float(os.getenv("OPENAI_TIMEOUT", "30.0"))
        self.max_retries = max(0, max_retries)
        self.backoff_base = max(0.1, backoff_base)

        # openai client instances share configuration
        self.client = OpenAI(api_key=api_key, timeout=self.timeout)
        self.async_client = AsyncOpenAI(api_key=api_key, timeout=self.timeout)

        # metadata from last request for callers who need accounting
        self.last_usage: Optional[Dict[str, Any]] = None
        self.last_response_id: Optional[str] = None
        self.last_latency_ms: Optional[float] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_text(
        self,
        prompt: MessageInput,
        *,
        temperature: float = 0.3,
        model: Optional[str] = None,
    ) -> str:
        """Generate plain text response."""

        messages = self._normalize_input(prompt)
        model_name = model or self.model

        def call() -> Any:
            return self.client.responses.create(
                model=model_name,
                input=messages,
                temperature=temperature,
            )

        response = self._invoke_with_retry(
            operation="openai.generate_text",
            model=model_name,
            temperature=temperature,
            call_fn=call,
        )
        return response.output_text

    def generate_structured(
        self,
        prompt: MessageInput,
        schema_model: Type[BaseModel],
        *,
        temperature: float = 0.3,
        model: Optional[str] = None,
    ) -> BaseModel:
        """Generate structured output using Pydantic model schema."""

        messages = self._normalize_input(prompt)
        model_name = model or self.model
        schema_payload = self._create_json_schema(schema_model)

        def call() -> Any:
            return self.client.responses.create(
                model=model_name,
                input=messages,
                temperature=temperature,
                text={
                    "format": schema_payload,
                },
            )

        response = self._invoke_with_retry(
            operation="openai.generate_structured",
            model=model_name,
            temperature=temperature,
            call_fn=call,
        )

        try:
            return schema_model.model_validate_json(response.output_text)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            logger.error("Structured response was not valid JSON", exc_info=exc)
            raise

    async def generate_text_async(
        self,
        prompt: MessageInput,
        *,
        temperature: float = 0.3,
        model: Optional[str] = None,
    ) -> str:
        """Generate plain text response asynchronously."""

        messages = self._normalize_input(prompt)
        model_name = model or self.model

        async def call() -> Any:
            return await self.async_client.responses.create(
                model=model_name,
                input=messages,
                temperature=temperature,
            )

        response = await self._invoke_with_retry_async(
            operation="openai.generate_text_async",
            model=model_name,
            temperature=temperature,
            call_fn=call,
        )
        return response.output_text

    async def generate_structured_async(
        self,
        prompt: MessageInput,
        schema_model: Type[BaseModel],
        *,
        temperature: float = 0.3,
        model: Optional[str] = None,
    ) -> BaseModel:
        """Generate structured output using Pydantic model schema asynchronously."""

        messages = self._normalize_input(prompt)
        model_name = model or self.model
        schema_payload = self._create_json_schema(schema_model)

        async def call() -> Any:
            return await self.async_client.responses.create(
                model=model_name,
                input=messages,
                temperature=temperature,
                text={
                    "format": schema_payload,
                },
            )

        response = await self._invoke_with_retry_async(
            operation="openai.generate_structured_async",
            model=model_name,
            temperature=temperature,
            call_fn=call,
        )

        try:
            return schema_model.model_validate_json(response.output_text)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            logger.error("Structured response was not valid JSON", exc_info=exc)
            raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _normalize_input(self, prompt: MessageInput) -> List[Dict[str, str]]:
        if isinstance(prompt, str):
            return [{"role": "user", "content": prompt}]
        if isinstance(prompt, list):
            return prompt
        raise TypeError("prompt must be a string or list of message dicts")

    def _invoke_with_retry(
        self,
        *,
        operation: str,
        model: str,
        temperature: float,
        call_fn: Any,
    ) -> Any:
        attempt = 0
        last_error: Optional[Exception] = None

        while True:
            tracer = get_tracer()
            context = tracer.start_as_current_span(operation) if tracer else nullcontext()
            start = time.perf_counter()

            with context as span:
                if span:
                    span.set_attribute("openai.model", model)
                    span.set_attribute("openai.temperature", temperature)
                    span.set_attribute("openai.attempt", attempt + 1)

                try:
                    response = call_fn()
                    latency_ms = (time.perf_counter() - start) * 1000
                    self._record_metadata(response, latency_ms)

                    if span:
                        span.set_attribute("openai.latency_ms", latency_ms)
                        span.set_attribute("openai.response_id", self.last_response_id or "")

                    return response
                except Exception as exc:  # pragma: no cover - error path
                    last_error = exc
                    retryable = self._is_retryable(exc) and attempt < self.max_retries

                    if span:
                        span.record_exception(exc)
                        span.set_attribute("openai.retryable", retryable)

                    logger.warning(
                        "OpenAI request failed",
                        extra={
                            "operation": operation,
                            "attempt": attempt + 1,
                            "model": model,
                            "retryable": retryable,
                        },
                        exc_info=exc,
                    )

                    if not retryable:
                        raise

                    sleep_for = self._compute_backoff(attempt)
                    time.sleep(sleep_for)
                    attempt += 1

        raise last_error  # pragma: no cover - loop exits via return/raise

    async def _invoke_with_retry_async(
        self,
        *,
        operation: str,
        model: str,
        temperature: float,
        call_fn: Any,
    ) -> Any:
        attempt = 0
        last_error: Optional[Exception] = None

        while True:
            tracer = get_tracer()
            context = tracer.start_as_current_span(operation) if tracer else nullcontext()
            start = time.perf_counter()

            with context as span:
                if span:
                    span.set_attribute("openai.model", model)
                    span.set_attribute("openai.temperature", temperature)
                    span.set_attribute("openai.attempt", attempt + 1)

                try:
                    response = await call_fn()
                    latency_ms = (time.perf_counter() - start) * 1000
                    self._record_metadata(response, latency_ms)

                    if span:
                        span.set_attribute("openai.latency_ms", latency_ms)
                        span.set_attribute("openai.response_id", self.last_response_id or "")

                    return response
                except Exception as exc:  # pragma: no cover - error path
                    last_error = exc
                    retryable = self._is_retryable(exc) and attempt < self.max_retries

                    if span:
                        span.record_exception(exc)
                        span.set_attribute("openai.retryable", retryable)

                    logger.warning(
                        "OpenAI async request failed",
                        extra={
                            "operation": operation,
                            "attempt": attempt + 1,
                            "model": model,
                            "retryable": retryable,
                        },
                        exc_info=exc,
                    )

                    if not retryable:
                        raise

                    sleep_for = self._compute_backoff(attempt)
                    await asyncio.sleep(sleep_for)
                    attempt += 1

        raise last_error  # pragma: no cover - loop exits via return/raise

    def _compute_backoff(self, attempt: int) -> float:
        jitter = random.uniform(0.8, 1.2)
        return self.backoff_base * (2**attempt) * jitter

    def _is_retryable(self, error: Exception) -> bool:
        status = getattr(error, "status_code", None) or getattr(error, "http_status", None)
        if status in {429, 500, 502, 503, 504}:
            return True

        # Some SDK exceptions surface a string "type" field
        error_type = getattr(error, "type", "") or getattr(error, "code", "")
        if isinstance(error_type, str) and any(token in error_type.lower() for token in ("timeout", "rate", "overloaded")):
            return True

        return False

    def _record_metadata(self, response: Any, latency_ms: float) -> None:
        usage = getattr(response, "usage", None)
        if usage is not None and hasattr(usage, "model_dump"):
            usage = usage.model_dump()
        self.last_usage = usage
        self.last_response_id = getattr(response, "id", None)
        self.last_latency_ms = latency_ms

    def _create_json_schema(self, schema_model: Type[BaseModel]) -> Dict[str, Any]:
        """Convert Pydantic model to JSON schema for structured outputs."""

        schema = schema_model.model_json_schema()

        def fix_schema(obj: Any) -> None:
            if isinstance(obj, dict):
                if obj.get("type") == "object" and "additionalProperties" not in obj:
                    obj["additionalProperties"] = False

                if "anyOf" in obj:
                    for any_item in obj["anyOf"]:
                        if isinstance(any_item, dict) and any_item.get("type") == "object":
                            any_item["additionalProperties"] = False

                if "$ref" in obj and "description" in obj:
                    obj.pop("description", None)

                for value in obj.values():
                    fix_schema(value)
            elif isinstance(obj, list):
                for item in obj:
                    fix_schema(item)

        fix_schema(schema)

        if schema.get("type") == "object" and "additionalProperties" not in schema:
            schema["additionalProperties"] = False

        return {
            "type": "json_schema",
            "name": schema_model.__name__,
            "schema": schema,
            "strict": True,
        }
