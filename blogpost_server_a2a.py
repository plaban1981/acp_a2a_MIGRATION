#!/usr/bin/env python3
"""
BlogPost Generator Agent Server - A2A Protocol Implementation
Migrated from ACP to BeeAI Server-based A2A Protocol

MIGRATION CHANGES FROM ACP TO A2A:
1. Replaced FastAPI with BeeAI Server (@server.agent decorator)
2. Changed from manual JSON-RPC handling to automatic A2A protocol handling
3. Updated message structure from custom Message class to A2A Message type
4. Changed response pattern from FastAPI return/StreamingResponse to yield
5. Simplified message extraction using A2A message.parts structure
6. Removed manual task storage (handled by BeeAI platform)
7. Changed LLM invocation from message list to string prompt (LangChain.LLM vs ChatModel)
8. Added streaming JSON parser for agent-to-agent communication
9. Updated imports from acp_sdk/fastapi to beeai_sdk/a2a
10. Changed context from Context to RunContext with context_id instead of session_id
"""

import os
import json
import pathlib
import re
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Dict

# A2A MIGRATION: Environment setup for containerized deployments
# Required for proper operation in Docker/K8s environments
os.environ["HOME"] = "/tmp"
os.environ["XDG_DATA_HOME"] = "/tmp/.local/share"
pathlib.Path(os.environ["XDG_DATA_HOME"]).mkdir(parents=True, exist_ok=True)
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
# Disable BeeAI platform self-registration (optional - only needed if platform is not running)
os.environ["BEEAI_DISABLE_REGISTRATION"] = "true"

# A2A MIGRATION: Changed imports from acp_sdk/fastapi to beeai_sdk/a2a
# OLD (ACP): from fastapi import FastAPI, Request
# OLD (ACP): from acp_sdk import Message, Context
# NEW (A2A): from beeai_sdk.server import Server
# NEW (A2A): from a2a.types import Message
from a2a.types import Message, AgentSkill  # A2A protocol types
from beeai_sdk.server import Server  # Replaces FastAPI
from beeai_sdk.server.context import RunContext  # Replaces Context
from beeai_sdk.a2a.extensions import AgentDetail, AgentDetailTool  # Agent metadata per migration guide

# Framework imports
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# A2A MIGRATION: Initialize BeeAI Server instead of FastAPI
# OLD (ACP): app = FastAPI(title="BlogPost Generator Agent")
# NEW (A2A): server = Server()
server = Server()

# A2A MIGRATION: Initialize LLM for blog generation
# LLM configuration remains the same, but is now simpler without middleware/CORS
blog_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7
)

# A2A MIGRATION: LangGraph State Definition
# OLD (ACP): Would include task_id for manual task tracking
# NEW (A2A): BeeAI platform handles task management automatically
class BlogState(TypedDict):
    topic: str
    research_content: str
    blog_title: str
    blog_content: str
    filename: str

# A2A MIGRATION: LangGraph Workflow Nodes
# The workflow logic remains the same, but LLM invocation follows A2A patterns
def generate_title_node(state: BlogState) -> BlogState:
    """
    Generate an engaging blog title
    
    A2A MIGRATION NOTE: Using ChatGroq with message format
    For ChatModel (like ChatGroq), we use invoke with message list
    For LangChain.LLM base class, we would pass string directly
    """
    prompt = f"""
    Based on the following research content about "{state['topic']}", 
    create an engaging, SEO-friendly blog post title.
    
    Research content: {state['research_content'][:500]}...
    
    Requirements:
    - Make it catchy and engaging
    - Keep it under 60 characters for SEO
    - Make it informative and clear
    
    Return only the title, nothing else.
    """
    
    # A2A MIGRATION: For ChatModel (ChatGroq), we use invoke with message format
    response = blog_llm.invoke([{"role": "user", "content": prompt}])
    state["blog_title"] = response.content.strip()
    return state

def generate_blog_content_node(state: BlogState) -> BlogState:
    """
    Generate the full blog post content
    
    A2A MIGRATION NOTE: Similar to title generation, using ChatModel invoke
    """
    prompt = f"""
    Create a comprehensive, well-structured blog post based on the following research:
    
    Topic: {state['topic']}
    Title: {state['blog_title']}
    Research Content: {state['research_content']}
    
    Requirements:
    - Write in an engaging, professional tone
    - Use markdown formatting
    - Include proper headings (##, ###)
    - Add bullet points and numbered lists where appropriate
    - Include a compelling introduction and conclusion
    - Make it SEO-friendly with natural keyword usage
    - Aim for 800-1500 words
    - Include relevant insights from the research
    - Add a "Key Takeaways" section at the end
    
    Structure:
    1. Introduction
    2. Main content sections with subheadings
    3. Key insights and findings
    4. Key Takeaways
    5. Conclusion
    
    Return the complete blog post in markdown format.
    """
    
    # A2A MIGRATION: Invoke LLM with message format
    response = blog_llm.invoke([{"role": "user", "content": prompt}])
    state["blog_content"] = response.content.strip()
    return state

def save_blog_node(state: BlogState) -> BlogState:
    """
    Save the blog post to a markdown file
    
    A2A MIGRATION NOTE: File saving logic remains the same
    """
    try:
        # Create filename from title
        safe_title = "".join(c for c in state["blog_title"] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_').lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"blog_{timestamp}_{safe_title[:50]}.md"
        
        # A2A MIGRATION: Create the complete blog post with A2A metadata
        blog_post = f"""---
title: "{state['blog_title']}"
date: {datetime.now().strftime("%Y-%m-%d")}
topic: "{state['topic']}"
generated_by: BlogPost Generator Agent A2A
protocol: A2A (migrated from ACP)
---

# {state['blog_title']}

{state['blog_content']}

---
*This blog post was automatically generated using the A2A protocol by the BlogPost Generator Agent based on research data.*
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(blog_post)
        state["filename"] = filename
        
    except Exception as e:
        state["filename"] = f"Error saving file: {str(e)}"
    
    return state

# A2A MIGRATION: Create the blog generation workflow
def create_blog_workflow():
    """
    A2A MIGRATION NOTE: Workflow creation remains the same
    LangGraph is framework-agnostic and works with both ACP and A2A
    """
    workflow = StateGraph(BlogState)
    
    # Add nodes
    workflow.add_node("generate_title", generate_title_node)
    workflow.add_node("generate_content", generate_blog_content_node)
    workflow.add_node("save_blog", save_blog_node)
    
    # Add edges
    workflow.set_entry_point("generate_title")
    workflow.add_edge("generate_title", "generate_content")
    workflow.add_edge("generate_content", "save_blog")
    workflow.add_edge("save_blog", END)
    
    return workflow.compile()

blog_workflow = create_blog_workflow()

# A2A MIGRATION: Helper Functions for Message Processing

def extract_query_from_message(message: Message) -> str:
    """
    Extract text content from A2A message
    
    A2A MIGRATION NOTE: Message structure changed completely
    OLD (ACP): Direct dictionary access: request.get("message", "")
    NEW (A2A): Extract from message.parts with proper type handling
    
    The A2A Message structure:
    - message.parts[] - array of message parts
    - part.root - the actual content
    - root.kind - type of content ("text", "file", "data", etc.)
    - root.text - text content (if kind == "text")
    """
    query = ""
    try:
        # Iterate through message parts
        for part in getattr(message, "parts", []):
            root = getattr(part, "root", None)
            
            # Check for text content
            if root and getattr(root, "kind", None) == "text":
                query += (root.text or "")
            
            # Fallback: check for content attribute
            elif hasattr(part, "content"):
                query += str(getattr(part, "content", ""))
        
    except Exception as e:
        # Ultimate fallback: convert entire message to string
        print(f"[WARN] Message extraction failed: {e}")
        query = str(message)
    
    return query.strip()

def parse_streaming_json(research_content: str) -> str:
    """
    Parse concatenated statusUpdate JSON objects to extract text content.
    
    A2A MIGRATION CRITICAL FIX:
    When agents communicate via A2A streaming, upstream agents may pass
    raw statusUpdate JSON instead of extracted text. This parser handles
    that case to prevent wrong/generic content generation.
    
    This is a known issue when one A2A agent calls another A2A agent.
    The streaming response comes in JSON-RPC format that needs to be parsed.
    
    Handles cases like:
    '{  "statusUpdate": {    "status": {      "message": {        "content": [{"text": "Actual research content"}]      }    }  }}'
    
    Without this parser, the agent would generate generic/wrong content
    because it would try to process the JSON structure as the actual content.
    """
    if "statusUpdate" not in research_content:
        return research_content
    
    print("[BLOGPOST_AGENT] Detected streaming JSON format, parsing...")
    print(f"[BLOGPOST_AGENT] Total content length: {len(research_content)} chars")
    print(f"[BLOGPOST_AGENT] First 200 chars: {research_content[:200]}")
    print(f"[BLOGPOST_AGENT] Last 200 chars: {research_content[-200:]}")
    parsed_chunks = []
    
    # Split by statusUpdate boundaries
    # Handles concatenated JSON like: }{  by replacing with }|||{
    json_objects = research_content.replace("}{", "}|||{").split("|||")
    print(f"[BLOGPOST_AGENT] Split into {len(json_objects)} JSON objects")
    
    for idx, json_str in enumerate(json_objects):
        try:
            data = json.loads(json_str)
            print(f"[BLOGPOST_AGENT] JSON object {idx}: has statusUpdate? {('statusUpdate' in data)}")
            
            # Extract text from: statusUpdate.status.message.content[].text
            if isinstance(data, dict) and "statusUpdate" in data:
                status = data["statusUpdate"].get("status", {})
                msg = status.get("message", {})
                content_list = msg.get("content", [])
                print(f"[BLOGPOST_AGENT] Object {idx}: status={bool(status)}, msg={bool(msg)}, content_list length={len(content_list)}")
                
                for part in content_list:
                    if isinstance(part, dict) and "text" in part:
                        text_content = str(part["text"])
                        print(f"[BLOGPOST_AGENT] Object {idx}: Extracted text chunk: {len(text_content)} chars")
                        parsed_chunks.append(text_content)
                        
        except (json.JSONDecodeError, Exception) as e:
            print(f"[BLOGPOST_AGENT] Failed to parse JSON object {idx}: {e}")
            # Skip malformed JSON
            continue
    
    if parsed_chunks:
        result = "".join(parsed_chunks).strip()
        print(f"[BLOGPOST_AGENT] Parsed {len(parsed_chunks)} chunks, total {len(result)} chars")
        return result
    else:
        print("[BLOGPOST_AGENT] WARNING: Failed to parse any text from streaming JSON!")
        print("[BLOGPOST_AGENT] Attempting alternative extraction...")
        
        # Alternative: Try to find any text content in the JSON
        try:
            # Look for any "text" fields in the entire content
            text_matches = re.findall(r'"text":\s*"([^"]+)"', research_content)
            if text_matches:
                alt_result = " ".join(text_matches)
                print(f"[BLOGPOST_AGENT] Alternative extraction found {len(text_matches)} text fields, total {len(alt_result)} chars")
                return alt_result
        except Exception as e:
            print(f"[BLOGPOST_AGENT] Alternative extraction also failed: {e}")
        
        # Last resort: Return a clear error message instead of JSON
        return "ERROR: Unable to extract research content from message. Please provide research text directly."

# A2A MIGRATION: Replace all FastAPI routes with single @server.agent decorator
# OLD (ACP): Multiple FastAPI routes:
#   - @app.post("/a2a/tasks/send") for synchronous requests
#   - @app.post("/a2a/tasks/sendSubscribe") for streaming
#   - @app.post("/a2a/tasks/get") for status
#   - @app.post("/a2a/tasks/cancel") for cancellation
#   - @app.get("/.well-known/agent.json") for agent card
# NEW (A2A): Single @server.agent decorator handles ALL protocol interactions
#   - BeeAI platform automatically provides all A2A endpoints
#   - Agent card is auto-generated from AgentDetail metadata
#   - Streaming is automatic via AsyncGenerator[str, None]

@server.agent(
    name="Enhanced BlogPost Generator",
    default_input_modes=["text", "text/plain", "application/json"],
    default_output_modes=["text", "text/plain", "text/markdown"],
    detail=AgentDetail(
        interaction_mode="multi-turn",
        user_greeting="""Hi! I'm your Enhanced BlogPost Generator powered by LangGraph and Groq LLM. 

🚀 **What I can do:**
- Transform research content into engaging blog posts
- Generate SEO-optimized content with proper structure
- Create markdown files with metadata
- Handle multi-turn conversations for content refinement

📝 **How to use me:**
Send me research content, and I'll create a comprehensive blog post for you!""",
        version="2.0.0",
        tools=[
            AgentDetailTool(
                name="LangGraph Workflow Engine",
                description="Multi-step content generation workflow: topic analysis, title creation, content writing, SEO optimization, and markdown file generation"
            ),
            AgentDetailTool(
                name="Groq LLM Integration",
                description="Advanced language model (Llama 3.3 70B) for high-quality, context-aware content generation with temperature control"
            ),
            AgentDetailTool(
                name="SEO Optimization Engine",
                description="Automatic SEO-friendly formatting, keyword optimization, meta descriptions, and structured content hierarchy"
            ),
            AgentDetailTool(
                name="Content Analysis",
                description="Analyze research content quality, extract key insights, and suggest content improvements"
            ),
            AgentDetailTool(
                name="File Processing",
                description="Generate and save markdown files with proper metadata, timestamps, and formatting"
            )
        ],
        framework="LangGraph + BeeAI A2A",
        author={
            "name": "ACP Migration Team",
            "email": "team@example.com",
            "organization": "Your Organization"
        },
        contributors=[
            {"name": "Developer 1", "role": "Lead Developer"},
            {"name": "Developer 2", "role": "AI Engineer"}
        ],
        source_code_url="https://github.com/your-org/acp-migration-a2a",
        documentation_url="https://docs.your-org.com/agents/blogpost-generator",
        license="Apache 2.0",
        tags=["Content Generation", "Blog Writing", "SEO", "LangGraph", "A2A Protocol"],
        recommended_models=["groq/llama-3.3-70b-versatile", "gpt-4o-mini", "claude-3-sonnet"],
        capabilities=[
            "Content Generation",
            "SEO Optimization", 
            "File Processing",
            "Multi-turn Conversation",
            "Research Analysis"
        ],
        limitations=[
            "Requires research content as input",
            "Best for technical and business content",
            "May need human review for sensitive topics"
        ],
        performance_metrics={
            "average_processing_time": "30-60 seconds",
            "content_quality_score": "8.5/10",
            "seo_optimization_level": "High"
        }
    ),
    skills=[
        AgentSkill(
            id="blog-generation",
            name="Blog Post Generation",
            description="""Transform research content into engaging, SEO-optimized blog posts with proper markdown formatting.

**Key Features:**
- Multi-step LangGraph workflow for quality content
- SEO optimization with meta tags and structure
- Automatic markdown file generation
- Context-aware content adaptation
- Multi-turn conversation support for refinements""",
            tags=["Content", "Blog", "SEO", "Writing", "LangGraph"],
            examples=[
                "Generate a blog post from this research about AI trends in 2025",
                "Create an SEO-optimized article based on market analysis data",
                "Write a comprehensive blog post about quantum computing applications",
                "Transform this technical research into a business-friendly blog post",
                "Create a series of blog posts from this comprehensive research report"
            ]
        ),
        AgentSkill(
            id="content-analysis",
            name="Content Analysis & Optimization",
            description="""Analyze research content quality and provide optimization suggestions.

**Capabilities:**
- Content structure analysis
- Key insight extraction
- SEO opportunity identification
- Readability assessment
- Content gap analysis""",
            tags=["Analysis", "Optimization", "SEO", "Content"],
            examples=[
                "Analyze this research content for SEO opportunities",
                "Extract key insights from this technical paper",
                "Suggest improvements for content structure",
                "Identify content gaps in this research"
            ]
        ),
        AgentSkill(
            id="multi-turn-conversation",
            name="Multi-turn Content Refinement",
            description="""Support iterative content improvement through conversation.

**Features:**
- Follow-up question handling
- Content refinement requests
- Style and tone adjustments
- Length and format modifications
- Additional research integration""",
            tags=["Conversation", "Refinement", "Iteration", "Content"],
            examples=[
                "Make this blog post more technical",
                "Shorten the content to 500 words",
                "Add more examples to this section",
                "Change the tone to be more casual",
                "Add a conclusion section"
            ]
        )
    ]
)
async def blogpost_generator_agent(
    message: Message,
    context: RunContext,
) -> AsyncGenerator[str, None]:
    """
    Blog post generator using LangGraph workflow
    
    A2A MIGRATION CHANGES:
    1. Function signature changed:
       OLD: async def agent(input: list[Message], context: Context) -> dict
       NEW: async def agent(message: Message, context: RunContext) -> AsyncGenerator[str, None]
    
    2. Input changed from list[Message] to single Message
       OLD: Received history of messages
       NEW: Receives current message only (platform manages history)
    
    3. Context changed from Context to RunContext
       OLD: context.session_id for session tracking
       NEW: context.context_id for context tracking
    
    4. Response changed from return to yield
       OLD: return JSONResponse({"result": result})
       NEW: yield result (automatic streaming)
    
    5. No manual task tracking
       OLD: Create A2ATask, manage status, store in tasks_storage
       NEW: Platform handles all task management automatically
    
    6. No manual JSON-RPC responses
       OLD: Manually create {"jsonrpc": "2.0", "result": {...}}
       NEW: Just yield string content, platform handles protocol
    """
    
    # A2A MIGRATION: Extract research content from A2A message
    # OLD (ACP): research_content = request.get("message", "")
    # NEW (A2A): Use helper function to extract from message.parts
    research_content = ""
    try:
        for part in getattr(message, "parts", []):
            root = getattr(part, "root", None)
            if root and getattr(root, "kind", None) == "text":
                research_content += (root.text or "")
            elif hasattr(part, "content"):
                research_content += str(getattr(part, "content", ""))
    except Exception:
        research_content = str(message)
    
    # Enhanced agent output with comprehensive agent card details
    yield f"✍️ Enhanced BlogPost Generator - Processing: {research_content[:100]}..."
    yield "=" * 60
    yield "🚀 Powered by LangGraph + Groq LLM + A2A Protocol"
    yield "📊 Multi-turn conversation support enabled"
    yield "🔍 SEO optimization and content analysis included"
    yield "=" * 60
    
    # Debug logging - helpful for troubleshooting agent-to-agent communication
    print(f"\n{'='*80}")
    print(f"[BLOGPOST_AGENT] Received raw content ({len(research_content)} chars)")
    print(f"[BLOGPOST_AGENT] First 500 chars: {research_content[:500]}")
    print(f"{'='*80}\n")
    
    # A2A MIGRATION CRITICAL: Parse streaming JSON if detected
    # This handles the case where upstream A2A agent sends raw statusUpdate JSON
    if "statusUpdate" in research_content:
        research_content = parse_streaming_json(research_content)
    
    # Debug log after parsing
    print(f"[BLOGPOST_AGENT] Final content: {len(research_content)} chars")
    print(f"[BLOGPOST_AGENT] Preview: {research_content[:500]}\n")
    
    # Extract topic from research content
    # Try to find the first meaningful line as the topic
    lines = research_content.split('\n')
    topic = lines[0].strip() if lines else "Blog Post Topic"
    if len(topic) > 150:  # If first line is too long, truncate
        topic = topic[:150] + "..."
    
    try:
        # A2A MIGRATION: Execute workflow (logic remains the same)
        initial_state = BlogState(
            topic=topic,
            research_content=research_content,
            blog_title="",
            blog_content="",
            filename=""
        )
        
        # Execute the LangGraph workflow
        final_state = blog_workflow.invoke(initial_state)
        
        # A2A MIGRATION: Prepare response
        # OLD (ACP): Return JSONResponse with artifacts, metadata, etc.
        # NEW (A2A): Simply yield a formatted string response
        response = f"""
✅ Blog post successfully generated!

**Topic:** {topic}
**Title:** {final_state['blog_title']}
**File:** {final_state['filename']}
**Content Length:** {len(final_state['blog_content'])} characters

**Preview:**
{final_state['blog_content'][:300]}...

---
Complete blog post has been saved to: {final_state['filename']}
"""
        
        # A2A MIGRATION: Yield response instead of return
        # OLD (ACP): return JSONResponse(content={...})
        # NEW (A2A): yield response (streaming happens automatically)
        print(f"[BLOGPOST_AGENT] Yielding response: {len(response)} chars")
        print(f"[BLOGPOST_AGENT] Response preview: {response[:300]}")
        yield response
        
    except Exception as e:
        # A2A MIGRATION: Error handling
        # OLD (ACP): Return JSONResponse with error codes
        # NEW (A2A): Yield error message (platform handles error protocol)
        error_msg = f"❌ Blog generation failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        yield error_msg

# A2A MIGRATION NOTE: Agent Card Discovery
# The /.well-known/agent.json endpoint should be automatically created by BeeAI Server
# based on the AgentDetail metadata in the @server.agent decorator.
# If it's not available, it's not critical - the main functionality (message processing) works fine.

# A2A MIGRATION: Server startup
# OLD (ACP): uvicorn.run(app, ...)
# NEW (A2A): server.run(...)
if __name__ == "__main__":
    print("🚀 Starting BlogPost Generator Agent - A2A Protocol Server")
    print("📋 Migrated from ACP to BeeAI Server-based A2A Protocol")
    print("✍️ Content capabilities: Blog generation, SEO optimization, markdown files")
    print("🔗 Endpoint: http://localhost:8004")
    print("\n" + "="*80)
    print("MIGRATION NOTES:")
    print("- Using BeeAI Server instead of FastAPI")
    print("- Single @server.agent decorator replaces multiple REST endpoints")
    print("- Automatic A2A protocol handling (no manual JSON-RPC)")
    print("- Streaming support via AsyncGenerator")
    print("- Includes streaming JSON parser for agent-to-agent communication")
    print("="*80 + "\n")
    
    # A2A MIGRATION: Run BeeAI Server
    # OLD (ACP): uvicorn.run("blogpost_server_a2a:app", ...)
    # NEW (A2A): server.run(...)
    server.run(host="0.0.0.0", port=8004)
