"""
OpenTelemetry tracing configuration for orchestration observability.
Provides distributed tracing for the entire call center analytics pipeline.
"""

import os
from datetime import datetime
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor

# Global tracer instance
tracer = None
_initialized = False


def simple_span_formatter(span: ReadableSpan) -> str:
    """Format span as a simple, readable one-line output.
    
    Format: [HH:MM:SS] STATUS operation_name | duration | key=value key=value
    
    Args:
        span: ReadableSpan object to format
        
    Returns:
        Formatted string for console output (empty string if span should be filtered)
    """
    # Check if we should show database traces
    show_db_traces = os.getenv("OTEL_SHOW_DB_TRACES", "false").lower() == "true"
    
    # Filter out database operations unless explicitly enabled
    if not show_db_traces and span.attributes:
        db_system = span.attributes.get("db.system")
        if db_system == "sqlite":
            return ""  # Skip database spans entirely
    # Get timestamp from span start time (nanoseconds since epoch)
    start_time = datetime.fromtimestamp(span.start_time / 1_000_000_000)
    timestamp = start_time.strftime("%H:%M:%S")
    
    # Calculate duration in seconds if span is ended
    if span.end_time:
        duration_ns = span.end_time - span.start_time
        duration_s = duration_ns / 1_000_000_000
        duration_str = f"{duration_s:.1f}s"
        status_icon = "✓" if span.status.status_code.name != "ERROR" else "✗"
    else:
        duration_str = "..."
        status_icon = "→"
    
    # Extract key attributes for display
    key_attrs = []
    if span.attributes:
        # Priority attributes to show first
        priority_keys = ["workflow_type", "risk_level", "transcript_id", "analysis_id", 
                        "plan_id", "workflow_count", "action_item_id", "model", "pipeline_status"]
        
        # Show priority attributes first
        for key in priority_keys:
            if key in span.attributes:
                value = str(span.attributes[key])
                # Truncate long values
                if len(value) > 20:
                    value = value[:17] + "..."
                key_attrs.append(f"{key.replace('_', '')}={value}")
        
        # Add other important attributes (limit total display)
        for key, value in span.attributes.items():
            if key not in priority_keys and len(key_attrs) < 5:
                if key not in ["service", "operation", "class", "function", "success"]:
                    value_str = str(value)
                    if len(value_str) > 15:
                        value_str = value_str[:12] + "..."
                    key_attrs.append(f"{key.replace('_', '')}={value_str}")
    
    # Build the main line
    attrs_str = " | " + " ".join(key_attrs) if key_attrs else ""
    main_line = f"[{timestamp}] {status_icon} {span.name} | {duration_str}{attrs_str}"
    
    # Add events as additional lines if they exist
    lines = [main_line]
    if span.events:
        for event in span.events:
            event_time = datetime.fromtimestamp(event.timestamp / 1_000_000_000)
            event_timestamp = event_time.strftime("%H:%M:%S")
            event_attrs = ""
            if event.attributes:
                event_attr_list = [f"{k}={v}" for k, v in event.attributes.items()]
                if event_attr_list:
                    event_attrs = " | " + " ".join(event_attr_list[:3])  # Limit to 3 attributes
            lines.append(f"[{event_timestamp}]   📝 {event.name}{event_attrs}")
    
    return "\n".join(lines) + "\n"


def initialize_tracing(
    service_name: str = "call-center-analytics", 
    enable_console: bool = None, 
    enable_jaeger: bool = None,
    enable_otlp: bool = None
):
    """Initialize OpenTelemetry tracing with configured exporters.
    
    Args:
        service_name: Name of the service for tracing
        enable_console: Enable console span exporter for development (defaults to env var)
        enable_jaeger: Enable Jaeger exporter for production (defaults to env var)
        enable_otlp: Enable OTLP exporter for cloud platforms (defaults to env var)
    """
    global tracer, _initialized
    
    if _initialized:
        return tracer
    
    # Determine exporters from environment variables if not explicitly provided
    if enable_console is None:
        enable_console = os.getenv("OTEL_CONSOLE_ENABLED", "true").lower() == "true"
    if enable_jaeger is None:
        enable_jaeger = os.getenv("OTEL_JAEGER_ENABLED", "false").lower() == "true"
    if enable_otlp is None:
        enable_otlp = os.getenv("OTEL_OTLP_ENABLED", "false").lower() == "true"
    
    # Create tracer provider
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__, service_name)
    
    # Configure exporters
    if enable_console:
        # Check console output format preference
        console_format = os.getenv("OTEL_CONSOLE_FORMAT", "simple").lower()
        
        if console_format == "simple":
            console_exporter = ConsoleSpanExporter(formatter=simple_span_formatter)
        else:
            # Use default JSON format
            console_exporter = ConsoleSpanExporter()
        
        console_processor = BatchSpanProcessor(console_exporter)
        trace.get_tracer_provider().add_span_processor(console_processor)
    
    if enable_jaeger:
        try:
            from opentelemetry.exporter.jaeger.thrift import JaegerExporter
            jaeger_exporter = JaegerExporter(
                agent_host_name=os.getenv("JAEGER_HOST", "localhost"),
                agent_port=int(os.getenv("JAEGER_PORT", "6831")),
            )
            jaeger_processor = BatchSpanProcessor(jaeger_exporter)
            trace.get_tracer_provider().add_span_processor(jaeger_processor)
        except ImportError:
            pass  # Jaeger exporter not available
    
    if enable_otlp:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            otlp_exporter = OTLPSpanExporter(
                endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
                headers={"Authorization": f"Bearer {os.getenv('OTEL_EXPORTER_OTLP_TOKEN', '')}"} if os.getenv('OTEL_EXPORTER_OTLP_TOKEN') else None
            )
            otlp_processor = BatchSpanProcessor(otlp_exporter)
            trace.get_tracer_provider().add_span_processor(otlp_processor)
        except ImportError:
            pass  # OTLP exporter not available
    
    # Auto-instrument HTTP, database, and OpenAI calls
    HTTPXClientInstrumentor().instrument()
    SQLite3Instrumentor().instrument()
    
    # Auto-instrument OpenAI API calls for LLM observability
    try:
        from opentelemetry.instrumentation.openai import OpenAIInstrumentor
        OpenAIInstrumentor().instrument()
    except ImportError:
        pass  # OpenAI instrumentation not available
    
    _initialized = True
    
    # Report configured exporters
    exporters = []
    if enable_console:
        exporters.append("console")
    if enable_jaeger:
        exporters.append("jaeger")
    if enable_otlp:
        exporters.append("otlp")
    
    exporters_str = ", ".join(exporters) if exporters else "none"
    
    return tracer


def get_tracer():
    """Get the configured tracer instance.
    
    Returns:
        Tracer instance for creating spans
    """
    global tracer
    if not _initialized:
        tracer = initialize_tracing()
    return tracer


def trace_async_function(operation_name: str):
    """Decorator to trace async functions with automatic span creation.
    
    Args:
        operation_name: Name for the traced operation
        
    Usage:
        @trace_async_function("workflow.extract")
        async def extract_workflows(self, plan_id):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(operation_name) as span:
                # Add function arguments as attributes
                if args and hasattr(args[0], '__class__'):
                    span.set_attribute("class", args[0].__class__.__name__)
                span.set_attribute("function", func.__name__)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("success", False)
                    span.set_attribute("error", str(e))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


def trace_function(operation_name: str):
    """Decorator to trace synchronous functions with automatic span creation.
    
    Args:
        operation_name: Name for the traced operation
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(operation_name) as span:
                # Add function arguments as attributes
                if args and hasattr(args[0], '__class__'):
                    span.set_attribute("class", args[0].__class__.__name__)
                span.set_attribute("function", func.__name__)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("success", False)
                    span.set_attribute("error", str(e))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


def set_span_attributes(**attributes):
    """Set attributes on the current active span.
    
    Args:
        **attributes: Key-value pairs to add as span attributes
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        for key, value in attributes.items():
            current_span.set_attribute(key, str(value))


def add_span_event(name: str, **attributes):
    """Add an event to the current active span.
    
    Args:
        name: Event name
        **attributes: Event attributes
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.add_event(name, attributes)