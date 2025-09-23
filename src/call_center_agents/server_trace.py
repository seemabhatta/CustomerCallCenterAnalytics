# server_trace.py
import os, json, time, asyncio
from typing import Any, Callable, Dict, List, Optional
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
from openai import OpenAI

# ----------------------------
# Config
# ----------------------------
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

httpx_client = httpx.Client(
    http2=True,
    timeout=httpx.Timeout(5.0, connect=3.0),  # tune as needed
    limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
)
client = OpenAI(api_key=OPENAI_API_KEY, http_client=httpx_client)

# ----------------------------
# Generic Trace Bus & Tool Wrap
# ----------------------------
class TraceBus:
    def __init__(self, emit: Callable[[Dict[str, Any]], None]):
        self.emit = emit

    def log(self, event: Dict[str, Any]):
        # event is a JSON-serializable dict with keys like type, name, text, etc.
        self.emit(event)

def _summarize(out: Any) -> str:
    try:
        if isinstance(out, list): return f"{len(out)} items"
        if isinstance(out, dict): return f"keys: {', '.join(list(out)[:6])}"
        s = str(out)
        return s[:120] + ("…" if len(s) > 120 else "")
    except Exception:
        return "ok"

def wrap_tool(bus: TraceBus, name: str, fn: Callable[..., Any]):
    async def _wrapped_async(**kwargs):
        t0 = time.perf_counter()
        bus.log({"type": "tool_call", "name": name, "args": kwargs})
        try:
            out = await fn(**kwargs)  # if your fn is async
            dt = int((time.perf_counter() - t0) * 1000)
            bus.log({"type": "tool_result", "name": name, "ok": True, "latency_ms": dt, "summary": _summarize(out)})
            return out
        except Exception as e:
            dt = int((time.perf_counter() - t0) * 1000)
            bus.log({"type": "tool_result", "name": name, "ok": False, "latency_ms": dt, "error": str(e)[:300]})
            raise

    def _wrapped_sync(**kwargs):
        t0 = time.perf_counter()
        bus.log({"type": "tool_call", "name": name, "args": kwargs})
        try:
            out = fn(**kwargs)  # if your fn is sync
            dt = int((time.perf_counter() - t0) * 1000)
            bus.log({"type": "tool_result", "name": name, "ok": True, "latency_ms": dt, "summary": _summarize(out)})
            return out
        except Exception as e:
            dt = int((time.perf_counter() - t0) * 1000)
            bus.log({"type": "tool_result", "name": name, "ok": False, "latency_ms": dt, "error": str(e)[:300]})
            raise

    # Choose async vs sync based on provided fn
    return _wrapped_async if asyncio.iscoroutinefunction(fn) else _wrapped_sync

# ----------------------------
# Tool Registry (plug your real tools here)
# ----------------------------
# Replace these with your actual implementations (DB reads, APIs, etc.)
def tool_search_analyses(category: Optional[str] = None, start: Optional[str] = None, end: Optional[str] = None):
    # TODO: implement real query (SQLite/Postgres/etc.)
    return []  # no results example

def tool_search_transcripts(query: str):
    # TODO: implement full-text transcript search
    return []

def tool_list_workflows(filter: Optional[str] = None):
    # TODO: implement workflow lookup
    return [{"id": "wf_001"}, {"id": "wf_002"}, {"id": "wf_003"}]

TOOLS: Dict[str, Dict[str, Any]] = {
    "search_analyses": {
        "fn": tool_search_analyses,
        "schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "start": {"type": "string"},
                "end": {"type": "string"},
            },
            "required": [],
        },
        "description": "Search analyses store by filters."
    },
    "search_transcripts": {
        "fn": tool_search_transcripts,
        "schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        "description": "Search transcripts by keyword."
    },
    "list_workflows": {
        "fn": tool_list_workflows,
        "schema": {
            "type": "object",
            "properties": {"filter": {"type": "string"}},
            "required": [],
        },
        "description": "List workflows by optional filter."
    },
}

def openai_tool_specs():
    # Convert our registry into OpenAI "tools=function" schema
    specs = []
    for name, meta in TOOLS.items():
        specs.append({
            "type": "function",
            "function": {
                "name": name,
                "description": meta.get("description") or name,
                "parameters": meta["schema"],
            }
        })
    return specs

# ----------------------------
# Model Output Schema (showable events only)
# ----------------------------
REASONING_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "oneOf": [
                    {"type":"object","properties":{"type":{"const":"plan"},"text":{"type":"string"}},"required":["type","text"]},
                    {"type":"object","properties":{"type":{"const":"observation"},"text":{"type":"string"}},"required":["type","text"]},
                    {"type":"object","properties":{"type":{"const":"decision"},"text":{"type":"string"}},"required":["type","text"]},
                    {"type":"object","properties":{"type":{"const":"answer"},"text":{"type":"string"}},"required":["type","text"]}
                ]
            }
        }
    },
    "required": ["events"],
    "additionalProperties": False
}

SYSTEM = (
    "You are an executive assistant. "
    "Think silently, but emit SHORT, user-safe events for plan/observation/decision/answer. "
    "Do not reveal chain-of-thought. Keep each event concise."
)

# ----------------------------
# Agent Runner (SSE-driven)
# ----------------------------
async def run_agent(bus: TraceBus, user_query: str):
    """
    1) Ask the model for a short plan/observations/decision/answer (showable events).
    2) Allow function-calling. Dispatch tools via registry, logging tool_call/tool_result.
    3) Stream events to client via bus.log(...).
    """
    # Step 1: initial planning/thought events
    # We use structured output to ensure we get 'events' list safely.
    try:
        resp = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_query}
            ],
            tools=openai_tool_specs(),
            tool_choice="auto",
            text={
                "format": {
                    "type": "json_schema",
                    "name": "ReasoningTrace",
                    "strict": True,
                    "schema": REASONING_SCHEMA
                }
            },
            max_output_tokens=400,
            temperature=0
        )
    except Exception as e:
        bus.log({"type": "observation", "text": f"Model error: {str(e)[:200]}"})
        bus.log({"type": "answer", "text": "Sorry, I hit a model error."})
        return

    # Emit showable events (plan/observation/decision...) from the model
    try:
        parsed = resp.output_parsed or {}
        for ev in parsed.get("events", []):
            bus.log(ev)
    except Exception:
        pass

    # If the model made tool calls (via Responses tool outputs), dispatch them:
    # The Responses API returns 'resp' with possible tool calls; here we inspect
    # the low-level 'resp.output' parts for tool calls (functions). The SDK
    # abstracts some of this, so we also handle 'resp' top-level 'output' items.
    # NOTE: Keep this generic; you can enhance if you prefer streaming events.
    def _iter_tool_calls(r):
        # Try to find any tool call messages
        # The OpenAI Python SDK v1 returns a structured 'resp' with .output and .output_parsed.
        # We'll scan .output for function calls if present.
        for item in getattr(r, "output", []) or []:
            # each item may be text, tool_call, or tool_result-like
            t = getattr(item, "type", None)
            if t == "tool_call":
                yield item

    # Dispatch each tool call synchronously here; you can loop with while
    for tool_call in _iter_tool_calls(resp):
        name = getattr(tool_call, "name", None)
        arguments = getattr(tool_call, "arguments", {}) or {}
        tool_meta = TOOLS.get(name)
        if not tool_meta:
            bus.log({"type": "tool_result", "name": name or "unknown", "ok": False, "error": "Unknown tool"})
            continue

        wrapped = wrap_tool(bus, name, tool_meta["fn"])
        # Call tool (sync or async wrappers handled by wrap_tool)
        if asyncio.iscoroutinefunction(tool_meta["fn"]):
            out = await wrapped(**arguments)
        else:
            out = wrapped(**arguments)

        # Optional: feed tool results back to the model for a final answer
        # Keep this simple: ask model to produce a final concise 'answer' event.
        try:
            final = client.responses.create(
                model=OPENAI_MODEL,
                input=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": user_query},
                    {"role": "assistant", "content": f"Tool {name} returned: {_summarize(out)}. Provide final answer as a single 'answer' event."}
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "ReasoningTraceAnswerOnly",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "events": {
                                    "type": "array",
                                    "items": {"type":"object","properties":{"type":{"const":"answer"},"text":{"type":"string"}},"required":["type","text"]}
                                }
                            },
                            "required": ["events"]
                        }
                    }
                },
                max_output_tokens=200,
                temperature=0
            )
            parsed_final = final.output_parsed or {}
            for ev in parsed_final.get("events", []):
                bus.log(ev)
        except Exception as e:
            bus.log({"type":"observation","text":f"Finalization error: {str(e)[:200]}"})

    # If no tool calls happened and no 'answer' was produced yet, ask for a final answer
    # (idempotent safeguard)
    # You can skip this if your first response always includes an 'answer'.
    bus.log({"type": "decision", "text": "Wrapping up."})
    bus.log({"type": "answer", "text": "Done. (Integrate your own tools to make this actionable.)"})

# ----------------------------
# FastAPI App
# ----------------------------
app = FastAPI(title="Thinking Trace Service", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TraceRequest(BaseModel):
    query: str

@app.post("/trace/stream")
async def trace_stream(req: TraceRequest):
    """
    SSE endpoint. POST a JSON body: {"query":"..."}.
    The response is an event-stream of JSON events:
      { "type": "plan" | "tool_call" | "tool_result" | "observation" | "decision" | "answer", ... }
    """
    queue: asyncio.Queue = asyncio.Queue()

    def emit(ev: Dict[str, Any]):
        # Ensure JSON serializable
        try:
            queue.put_nowait(ev)
        except Exception:
            pass

    bus = TraceBus(emit)

    async def gen():
        # kick off agent in background
        asyncio.create_task(run_agent(bus, req.query))
        # stream events
        while True:
            ev = await queue.get()
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")

@app.get("/")
def root():
    return {"ok": True, "service": "Thinking Trace Service", "endpoints": ["/trace/stream"]}

