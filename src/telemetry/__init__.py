"""OpenTelemetry telemetry package for distributed tracing."""

from .tracer import (
    initialize_tracing,
    get_tracer,
    trace_async_function,
    trace_function,
    set_span_attributes,
    add_span_event
)

__all__ = [
    'initialize_tracing',
    'get_tracer',
    'trace_async_function',
    'trace_function',
    'set_span_attributes',
    'add_span_event'
]