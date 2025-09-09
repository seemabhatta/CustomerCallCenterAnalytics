
# OpenAI Responses API — Python Advanced Cheatsheet (Safe & Updated for v1.107.0+)

The **Responses API** is the primary interface for generating text, code, structured outputs, and connecting to **tools** (functions, APIs, workflows, or agents).  
It replaces most legacy APIs (like Chat Completions and Assistants), while staying backward compatible.  
It is **stateless by default**, but you can manage **sessions** and simulate **memory**.

Endpoint:
```
POST https://api.openai.com/v1/responses
```
📖 Official docs:  
- [Responses API](https://platform.openai.com/docs/api-reference/responses)  
- [Structured outputs](https://platform.openai.com/docs/guides/structured-outputs?api-mode=responses)  
- [Streaming](https://platform.openai.com/docs/guides/streaming-responses?api-mode=responses)  
- [Python SDK](https://github.com/openai/openai-python)  

---

## 🔎 Compatibility Note

- **Tested with openai-python v1.107.0**.  
- Run this check to ensure your SDK is current:
```python
import openai
print(openai.__version__)  # should be >= 1.107.0
```

---

## 🛠 Helpers (Safe Accessors)

Always use these helpers instead of raw attributes to avoid shape mismatches:

```python
def rx_text(resp) -> str:
    """Return best-effort concatenated text from a Responses API result."""
    if getattr(resp, "output_text", None):
        return resp.output_text
    try:
        parts = []
        for b in getattr(resp, "output", []) or []:
            for c in getattr(b, "content", []) or []:
                t = getattr(c, "text", None)
                if isinstance(t, str):
                    parts.append(t)
        return "".join(parts).strip()
    except Exception:
        return str(resp)

def rx_parsed(resp):
    """Return parsed JSON when using text.format json_schema (or None)."""
    try:
        for b in getattr(resp, "output", []) or []:
            for c in getattr(b, "content", []) or []:
                p = getattr(c, "parsed", None)
                if p is not None:
                    return p
    except Exception:
        pass
    return None
```

---

## 1) Quickstart: Basic Text Generation
```python
from openai import OpenAI

client = OpenAI()
resp = client.responses.create(
    model="gpt-4o",
    input="Tell me a three sentence bedtime story about a unicorn."
)
print(rx_text(resp))
```

---

## 2) Structured Output (JSON Schema)
```python
resp = client.responses.create(
    model="gpt-4o",
    input="Extract name and email from: 'Contact Jane Doe <jane@example.com>'",
    text={
        "format": {
            "type": "json_schema",
            "name": "ContactExtraction",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string", "format": "email"}
                },
                "required": ["name","email"],
                "additionalProperties": False
            }
        }
    }
)

data = rx_parsed(resp)
print(data)  # {'name': 'Jane Doe', 'email': 'jane@example.com'}
```

---

## 3) Tools = Function Calling
```python
tools = [
  {
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "Get weather for a city",
      "parameters": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"]
      }
    }
  }
]

def get_weather(city: str):
    return {"city": city, "temp_f": 72}

resp = client.responses.create(
    model="gpt-4o",
    input="Check Boston weather",
    tools=tools,
    tool_choice="auto"
)
```

---

## 4) Tools + Structured Output Together
```python
resp = client.responses.create(
    model="gpt-4o",
    input="Check status of order ORD-123",
    tools=[...],
    text={
        "format": {
            "type": "json_schema",
            "name": "OrderStatus",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "status": {"type": "string"}
                },
                "required": ["order_id","status"]
            }
        }
    }
)
print(rx_parsed(resp))
```

---

## 5) Vision (Text + Image)
**Image URL:**
```python
resp = client.responses.create(
  model="gpt-4o-mini",
  input=[{
    "role": "user",
    "content": [
      {"type": "input_text", "text": "What do you see in this image?"},
      {"type": "input_image", "image_url": "https://example.com/cat.png"}
    ]
  }]
)
print(rx_text(resp))
```

**Base64 Image:**
```python
import base64
with open("img.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")

resp = client.responses.create(
  model="gpt-4o-mini",
  input=[{
    "role": "user",
    "content": [
      {"type": "input_text", "text": "Describe this image."},
      {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"}
    ]
  }]
)
print(rx_text(resp))
```

---

## 6) Streaming Responses
```python
buf = []
with client.responses.stream(
    model="gpt-4o",
    input="Draft a friendly email about tomorrow's meetup.",
) as stream:
    for ev in stream:
        if ev.type == "response.output_text.delta":
            buf.append(ev.delta or "")
final_text = "".join(buf)
print(final_text)
```

---

## 7) Sessions & Memory

### Conversation Context
```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hi, who won the World Cup in 2018?"},
    {"role": "assistant", "content": "France won the 2018 FIFA World Cup."},
    {"role": "user", "content": "Cool, who was the top scorer?"}
]

resp = client.responses.create(model="gpt-4o", input=messages)
print(rx_text(resp))
```

### Sessions
```python
session = client.sessions.create(
    model="gpt-4o",
    instructions="You are a financial advisor bot."
)

resp = client.responses.create(
    session=session.id,
    input="What’s a good ETF strategy for 30 years?"
)
print(rx_text(resp))
```

---

## 8) Async Support
```python
from openai import AsyncOpenAI
import asyncio

async def main():
    client = AsyncOpenAI()
    resp = await client.responses.create(
        model="gpt-4o",
        input="Explain quantum entanglement simply."
    )
    print(rx_text(resp))

asyncio.run(main())
```

---

## 9) Useful Knobs
```python
resp = client.responses.create(
    model="gpt-4o-mini",
    input="Summarize yesterday's standup",
    temperature=0.3,
    max_output_tokens=200,
    seed=1234
)
print(rx_text(resp))
```

---

## ⚠️ Common Pitfalls

- ❌ Don’t use `resp.output_parsed` → removed in SDK ≥ v1.107.0.  
- ✅ Use `rx_parsed(resp)` for JSON schema outputs.  
- ✅ Use `resp.output_text` or `rx_text(resp)` for plain generations.  
- Always inspect with `resp.model_dump_json(indent=2)` if unsure.  

---

## ✅ Summary (2025)
- **Responses API** = future-proof API for text, images, tools, JSON, and streaming.  
- **Tools** = APIs, workflows, or agents callable by the model.  
- **Sessions** = reusable defaults, not true memory.  
- **Memory** = managed by your app.  
- **Vision** = natively supported.  
- **Streaming** = token-by-token output.  
- **Async** = supported via `AsyncOpenAI`.  
- **Assistants API** = being phased out by 2026.  

---

## 🔬 Mini-Test Example (for CI)
```python
def test_responses_schema_contract(client):
    resp = client.responses.create(
        model="gpt-4o",
        input="Return a person",
        text={"format":{"type":"json_schema","name":"P","strict":True,"schema":{
            "type":"object",
            "properties":{"name":{"type":"string"}},
            "required":["name"],
            "additionalProperties":False
        }}}
    )
    assert rx_parsed(resp) and "name" in rx_parsed(resp)
```

---

### References
- [Responses API](https://platform.openai.com/docs/api-reference/responses)  
- [Structured outputs](https://platform.openai.com/docs/guides/structured-outputs?api-mode=responses)  
- [Streaming](https://platform.openai.com/docs/guides/streaming-responses?api-mode=responses)  
- [Python SDK](https://github.com/openai/openai-python)  
- [Agents SDK](https://developers.openai.com/tracks/building-agents)  
