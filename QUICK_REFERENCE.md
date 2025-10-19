# ACP to A2A Migration - Quick Reference

## 🚀 One-Page Cheat Sheet

### Import Changes

```python
# ❌ OLD (ACP)
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from acp_sdk import Message, Context

# ✅ NEW (A2A)
from beeai_sdk.server import Server
from beeai_sdk.server.context import RunContext
from a2a.types import Message
from collections.abc import AsyncGenerator
```

### Server Initialization

```python
# ❌ OLD (ACP)
app = FastAPI(title="My Agent")
app.add_middleware(CORSMiddleware, ...)

# ✅ NEW (A2A)
server = Server()  # That's it!
```

### Agent Registration

```python
# ❌ OLD (ACP)
@app.post("/v1/agent/process")
async def process_agent(request: dict):
    query = request.get("message", "")
    result = await process(query)
    return JSONResponse({"result": result})

# ✅ NEW (A2A)
@server.agent(name="process_agent")
async def process_agent(
    message: Message,
    context: RunContext,
) -> AsyncGenerator[str, None]:
    query = extract_query_from_message(message)
    result = await process(query)
    yield result
```

### Message Extraction

```python
# ❌ OLD (ACP)
query = request.get("message", "")

# ✅ NEW (A2A)
def extract_query_from_message(message: Message) -> str:
    query = ""
    try:
        for part in getattr(message, "parts", []):
            root = getattr(part, "root", None)
            if root and getattr(root, "kind", None) == "text":
                query += (root.text or "")
            elif hasattr(part, "content"):
                query += str(getattr(part, "content", ""))
    except Exception as e:
        query = str(message)
    return query.strip()

# Usage
query = extract_query_from_message(message)
```

### Response Handling

```python
# ❌ OLD (ACP)
return JSONResponse(content={"result": result})

# ✅ NEW (A2A)
yield result  # Automatic streaming!
```

### Error Handling

```python
# ❌ OLD (ACP)
if not query:
    raise HTTPException(status_code=400, detail="No query")

# ✅ NEW (A2A)
if not query:
    yield "No query provided"
    return
```

### Client Invocation

```python
# ❌ OLD (ACP)
payload = {
    "jsonrpc": "2.0",
    "method": "tasks/sendSubscribe",
    "params": {
        "id": str(uuid.uuid4()),
        "message": {"role": "user", "parts": [{"type": "text", "text": query}]},
        "sessionId": str(uuid.uuid4())
    }
}
response = await client.post(f"{url}/a2a/tasks/sendSubscribe", json=payload)

# ✅ NEW (A2A)
payload = {
    "message": {
        "content": [{"text": query}]
    }
}
response = await client.post(f"{url}/v1/message:stream", json=payload)
```

### Server Startup

```python
# ❌ OLD (ACP)
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

# ✅ NEW (A2A)
if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8000)
```

## 🔧 Common Patterns

### Pattern 1: Simple Text Agent

```python
from beeai_sdk.server import Server
from a2a.types import Message
from beeai_sdk.server.context import RunContext
from collections.abc import AsyncGenerator

server = Server()

@server.agent(name="echo_agent")
async def echo_agent(
    message: Message,
    context: RunContext,
) -> AsyncGenerator[str, None]:
    # Extract text
    text = ""
    for part in getattr(message, "parts", []):
        root = getattr(part, "root", None)
        if root and getattr(root, "kind", None) == "text":
            text += (root.text or "")
    
    # Process and respond
    result = f"Echo: {text}"
    yield result

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8000)
```

### Pattern 2: CrewAI Agent

```python
from beeai_sdk.server import Server
from a2a.types import Message
from beeai_sdk.server.context import RunContext
from crewai import Agent, Task, Crew, LLM
from collections.abc import AsyncGenerator

server = Server()
llm = LLM(model="groq/llama-3.3-70b-versatile", api_key="...")

@server.agent(name="research_agent")
async def research_agent(
    message: Message,
    context: RunContext,
) -> AsyncGenerator[str, None]:
    # Extract query
    query = extract_query_from_message(message)
    
    # Create CrewAI agent
    agent = Agent(
        role='Researcher',
        goal=f'Research: {query}',
        backstory='Expert researcher',
        llm=llm,
        tools=[],
        verbose=True
    )
    
    task = Task(
        description=f"Research: {query}",
        expected_output="Research report",
        agent=agent
    )
    
    crew = Crew(agents=[agent], tasks=[task])
    result = crew.kickoff()
    
    # Yield result
    response = result.raw if hasattr(result, 'raw') else str(result)
    yield response

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8003)
```

### Pattern 3: LangGraph Agent

```python
from beeai_sdk.server import Server
from a2a.types import Message
from beeai_sdk.server.context import RunContext
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from collections.abc import AsyncGenerator

server = Server()

class MyState(TypedDict):
    input: str
    output: str

def process_node(state: MyState) -> MyState:
    state["output"] = f"Processed: {state['input']}"
    return state

workflow = StateGraph(MyState)
workflow.add_node("process", process_node)
workflow.set_entry_point("process")
workflow.add_edge("process", END)
graph = workflow.compile()

@server.agent(name="workflow_agent")
async def workflow_agent(
    message: Message,
    context: RunContext,
) -> AsyncGenerator[str, None]:
    # Extract input
    input_text = extract_query_from_message(message)
    
    # Execute workflow
    result = graph.invoke(MyState(input=input_text, output=""))
    
    # Yield result
    yield result["output"]

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8004)
```

### Pattern 4: Simple Client

```python
import asyncio
import httpx
import json

async def call_agent(url: str, text: str) -> str:
    async with httpx.AsyncClient(timeout=300.0) as client:
        payload = {
            "message": {
                "content": [{"text": text}]
            }
        }
        
        chunks = []
        async with client.stream(
            "POST",
            f"{url}/v1/message:stream",
            json=payload,
            headers={"Accept": "text/event-stream"}
        ) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() not in ["[DONE]", ""]:
                        try:
                            data = json.loads(data_str)
                            if "statusUpdate" in data:
                                status = data["statusUpdate"].get("status", {})
                                msg = status.get("message", {})
                                for part in msg.get("content", []):
                                    if isinstance(part, dict) and "text" in part:
                                        chunks.append(str(part["text"]))
                        except json.JSONDecodeError:
                            if data_str:
                                chunks.append(data_str)
        
        return "".join(chunks).strip()

# Usage
async def main():
    result = await call_agent("http://localhost:8000", "Hello!")
    print(result)

asyncio.run(main())
```

## 🐛 Common Issues & Solutions

### Issue 1: "No content received"

**Problem**: Agent returns empty response

**Solution**: Check if you're properly yielding the result:
```python
# ❌ Wrong
return result

# ✅ Correct
yield result
```

### Issue 2: "Message extraction failed"

**Problem**: Can't extract text from message

**Solution**: Use the helper function with fallbacks:
```python
def extract_query_from_message(message: Message) -> str:
    query = ""
    try:
        for part in getattr(message, "parts", []):
            root = getattr(part, "root", None)
            if root and getattr(root, "kind", None) == "text":
                query += (root.text or "")
            elif hasattr(part, "content"):
                query += str(getattr(part, "content", ""))
    except Exception as e:
        query = str(message)  # Fallback
    return query.strip()
```

### Issue 3: "Wrong/generic content generated"

**Problem**: Agent-to-agent communication passes raw JSON

**Solution**: Add streaming JSON parser:
```python
def parse_streaming_json(content: str) -> str:
    if "statusUpdate" not in content:
        return content
    
    parsed_chunks = []
    json_objects = content.replace("}{", "}|||{").split("|||")
    
    for json_str in json_objects:
        try:
            data = json.loads(json_str)
            if "statusUpdate" in data:
                status = data["statusUpdate"].get("status", {})
                msg = status.get("message", {})
                for part in msg.get("content", []):
                    if isinstance(part, dict) and "text" in part:
                        parsed_chunks.append(str(part["text"]))
        except:
            continue
    
    return "".join(parsed_chunks).strip() if parsed_chunks else content

# Usage
if "statusUpdate" in research_content:
    research_content = parse_streaming_json(research_content)
```

### Issue 4: "Port already in use"

**Problem**: Port 8003 or 8004 already taken

**Solution**: Change port in server.run():
```python
server.run(host="0.0.0.0", port=8005)  # Use different port
```

### Issue 5: "Import errors"

**Problem**: Cannot import beeai_sdk or a2a

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

## 📝 Checklist

### Pre-Migration
- [ ] Read migration guide
- [ ] Understand current ACP implementation
- [ ] Backup existing code
- [ ] Set up test environment

### During Migration
- [ ] Update dependencies (requirements.txt)
- [ ] Change imports (fastapi → beeai_sdk)
- [ ] Replace server initialization
- [ ] Update agent registration (@app.post → @server.agent)
- [ ] Change function signatures
- [ ] Update message extraction
- [ ] Change response pattern (return → yield)
- [ ] Add helper functions
- [ ] Update client code
- [ ] Test individual agents
- [ ] Test agent-to-agent communication

### Post-Migration
- [ ] Add migration comments
- [ ] Update documentation
- [ ] Test full workflow
- [ ] Check for linting errors
- [ ] Performance testing
- [ ] Deploy to production

## 🎯 Key Takeaways

1. **Simpler API**: One decorator instead of multiple routes
2. **Automatic Protocol**: No manual JSON-RPC needed
3. **Built-in Streaming**: Just yield, no SSE implementation
4. **Better DX**: Clearer code, easier debugging
5. **Less Boilerplate**: ~50% less code on average

## 📚 Resources

- Full README: `README.md`
- Migration Summary: `MIGRATION_SUMMARY.md`
- Complete Guide: `C:\Users\PLNAYAK\Documents\ACP_A2A\ACP-to-A2A-Complete-Migration-Guide-With-Code.md`
- Local Guide: `acp-a2a-migration-guide.mdx`

---

**Print this page and keep it on your desk during migration!** 📋

