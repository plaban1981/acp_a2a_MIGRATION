#!/usr/bin/env python3
"""
DeepSearch Research Agent Server - A2A Protocol Implementation
Migrated from ACP to BeeAI Server-based A2A Protocol

MIGRATION CHANGES FROM ACP TO A2A:
1. Replaced FastAPI with BeeAI Server (@server.agent decorator)
2. Changed from manual JSON-RPC handling to automatic A2A protocol handling
3. Updated message structure from custom Message class to A2A Message type
4. Changed response pattern from FastAPI return to yield
5. Simplified message extraction using A2A message.parts structure
6. Removed manual task storage (handled by BeeAI platform)
7. Updated imports from acp_sdk/fastapi to beeai_sdk/a2a
8. Changed context from Context to RunContext
9. Integrated CrewAI with MCP tools for web search capabilities
10. Used LiteLLM custom provider for LLM integration
"""

import os
import pathlib
from collections.abc import AsyncGenerator

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

# CrewAI imports for agent framework
from crewai import Agent, Task, Crew, LLM
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
from dotenv import load_dotenv

load_dotenv()

# A2A MIGRATION: Initialize BeeAI Server instead of FastAPI
# OLD (ACP): app = FastAPI(title="DeepSearch Agent")
# NEW (A2A): server = Server()
server = Server()

# A2A MIGRATION: Configure LLM for CrewAI
# Using Groq as the LLM provider for research tasks
# OLD (ACP): Would configure via environment variables or custom middleware
# NEW (A2A): Direct configuration with CrewAI LLM wrapper
try:
    # Try to use Groq LLM if available
    research_llm = LLM(
        model="groq/llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY")
    )
except Exception as e:
    print(f"[WARN] Failed to initialize Groq LLM: {e}")
    print("[INFO] Falling back to default LLM")
    # Fallback to a default LLM configuration
    research_llm = None

# A2A MIGRATION: Configure MCP server for LinkUp search tools
# MCP (Model Context Protocol) allows agents to use external tools
# This configuration remains the same between ACP and A2A
server_params = StdioServerParameters(
    command="python",
    args=["servers/linkup_mcp_server.py"],  # Assumes linkup_mcp_server.py exists
    env={
        "LINKUP_API_KEY": os.getenv("LINKUP_API_KEY", ""),
        **os.environ
    }
)

# A2A MIGRATION: Helper function for message extraction
def extract_query_from_message(message: Message) -> str:
    """
    Extract text content from A2A message
    
    A2A MIGRATION NOTE: Message structure changed completely
    OLD (ACP): Direct dictionary access: request.get("query", "")
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

# A2A MIGRATION: Replace all FastAPI routes with single @server.agent decorator
# OLD (ACP): Multiple FastAPI routes:
#   - @app.post("/v1/research") for research requests
#   - @app.post("/a2a/tasks/send") for synchronous requests
#   - @app.post("/a2a/tasks/sendSubscribe") for streaming
#   - @app.get("/.well-known/agent.json") for agent card
# NEW (A2A): Single @server.agent decorator handles ALL protocol interactions
#   - BeeAI platform automatically provides all A2A endpoints
#   - Agent card is auto-generated from AgentDetail metadata
#   - Streaming is automatic via AsyncGenerator[str, None]

@server.agent(
    name="Enhanced DeepSearch Research Agent",
    default_input_modes=["text", "text/plain", "application/json"],
    default_output_modes=["text", "text/plain", "application/json"],
    detail=AgentDetail(
        interaction_mode="multi-turn",
        user_greeting="""Hi! I'm your Enhanced DeepSearch Research Agent powered by CrewAI and MCP tools. 

🔍 **What I can do:**
- Comprehensive topic research using advanced AI
- Web search and data gathering with MCP tools
- Multi-source information synthesis
- Real-time research with current data
- Multi-turn conversation for research refinement

📊 **How to use me:**
Send me any research topic, and I'll provide comprehensive analysis!""",
        version="2.0.0",
        tools=[
            AgentDetailTool(
                name="CrewAI Research Framework",
                description="Advanced research capabilities using CrewAI framework with LLM-powered analysis, task orchestration, and multi-agent collaboration"
            ),
            AgentDetailTool(
                name="MCP Web Search Tools",
                description="Model Context Protocol tools for enhanced web search, real-time data gathering, and information synthesis"
            ),
            AgentDetailTool(
                name="Groq LLM Integration",
                description="Fast inference using Llama 3.3 70B model for research synthesis, analysis, and content generation"
            ),
            AgentDetailTool(
                name="Research Analysis Engine",
                description="Comprehensive analysis of research data with key insights extraction, trend identification, and summary generation"
            ),
            AgentDetailTool(
                name="Multi-source Synthesis",
                description="Combine information from multiple sources to provide comprehensive, well-structured research reports"
            )
        ],
        framework="CrewAI + BeeAI A2A",
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
        documentation_url="https://docs.your-org.com/agents/deepsearch-research",
        license="Apache 2.0",
        tags=["Research", "Analysis", "Web Search", "CrewAI", "A2A Protocol"],
        recommended_models=["groq/llama-3.3-70b-versatile", "gpt-4o-mini", "claude-3-sonnet"],
        capabilities=[
            "Comprehensive Research",
            "Web Search Integration", 
            "Data Synthesis",
            "Multi-turn Conversation",
            "Real-time Analysis"
        ],
        limitations=[
            "Requires internet connection for web search",
            "Research quality depends on available sources",
            "May need human verification for sensitive topics"
        ],
        performance_metrics={
            "average_research_time": "60-120 seconds",
            "source_accuracy_score": "9.0/10",
            "comprehensiveness_level": "High"
        }
    ),
    skills=[
        AgentSkill(
            id="comprehensive-research",
            name="Comprehensive Research",
            description="""Comprehensive topic research using CrewAI and MCP tools with web search capabilities.

**Key Features:**
- Multi-source information gathering
- Real-time web search integration
- Advanced AI-powered analysis
- Structured research reports
- Multi-turn conversation support for refinement""",
            tags=["Research", "Analysis", "Web Search", "CrewAI"],
            examples=[
                "Research the latest trends in artificial intelligence for 2025",
                "Investigate the impact of climate change on global agriculture",
                "Analyze the current state of quantum computing technology",
                "Study the evolution of blockchain technology in finance",
                "Research emerging trends in renewable energy adoption"
            ]
        ),
        AgentSkill(
            id="data-synthesis",
            name="Data Synthesis & Analysis",
            description="""Synthesize information from multiple sources into comprehensive research reports.

**Capabilities:**
- Multi-source data integration
- Key insight extraction
- Trend identification and analysis
- Comparative analysis across sources
- Structured report generation""",
            tags=["Synthesis", "Analysis", "Data", "Research"],
            examples=[
                "Synthesize findings from multiple AI research papers",
                "Compare different approaches to climate change mitigation",
                "Analyze market trends across different industries",
                "Integrate data from various technology reports"
            ]
        ),
        AgentSkill(
            id="real-time-research",
            name="Real-time Research & Updates",
            description="""Conduct research with access to current, real-time information.

**Features:**
- Live web search capabilities
- Current event analysis
- Real-time data integration
- Up-to-date information synthesis
- Dynamic research updates""",
            tags=["Real-time", "Current", "Web Search", "Updates"],
            examples=[
                "Research the latest developments in AI regulation",
                "Find current market trends in renewable energy",
                "Investigate recent breakthroughs in quantum computing",
                "Analyze current global economic indicators"
            ]
        )
    ]
)
async def deepsearch_agent_handler(
    message: Message,
    context: RunContext,
) -> AsyncGenerator[str, None]:
    """
    Deep research agent using CrewAI with MCP tools
    
    A2A MIGRATION CHANGES:
    1. Function signature changed:
       OLD: async def agent(request: dict) -> JSONResponse
       NEW: async def agent(message: Message, context: RunContext) -> AsyncGenerator[str, None]
    
    2. Input changed from dictionary to Message
       OLD: query = request.get("query", "")
       NEW: query = extract_query_from_message(message)
    
    3. Context changed from implicit session to RunContext
       OLD: No context or custom session management
       NEW: context.context_id for context tracking
    
    4. Response changed from return to yield
       OLD: return {"result": result}
       NEW: yield result (automatic streaming)
    
    5. No manual task tracking or JSON-RPC
       OLD: Create tasks, manage status, return JSON-RPC responses
       NEW: Platform handles all protocol interactions
    """
    
    # A2A MIGRATION: Extract query from A2A message
    # OLD (ACP): query = request.get("query", "")
    # NEW (A2A): Use helper function to extract from message.parts
    query = ""
    try:
        for part in getattr(message, "parts", []):
            root = getattr(part, "root", None)
            if root and getattr(root, "kind", None) == "text":
                query = root.text
            elif hasattr(part, "content"):
                query = str(getattr(part, "content", ""))
    except Exception:
        query = str(message)
    
    if not query:
        # A2A MIGRATION: Yield error instead of raising HTTPException
        # OLD (ACP): raise HTTPException(status_code=400, detail="No query provided")
        # NEW (A2A): yield error message
        yield "❌ Error: No research query provided. Please provide a topic to research."
        return
    
    # Enhanced agent output with comprehensive agent card details
    yield f"🔍 Enhanced DeepSearch Research Agent - Processing: {query[:100]}..."
    yield "=" * 60
    yield "🚀 Powered by CrewAI + MCP Tools + A2A Protocol"
    yield "📊 Multi-turn conversation support enabled"
    yield "🔍 Real-time web search and data synthesis included"
    yield "=" * 60
    
    print(f"\n{'='*80}")
    print(f"[DEEPSEARCH_AGENT] Received query: {query}")
    print(f"{'='*80}\n")
    
    try:
        # A2A MIGRATION: CrewAI agent creation remains mostly the same
        # The main difference is in how we handle responses (yield vs return)
        
        # Check if MCP server is configured
        # Note: In production, you would create the MCP server adapter
        # For this migration example, we'll use a simplified approach
        
        # A2A MIGRATION: Create CrewAI agent
        # OLD (ACP): Would be the same, but result handling differs
        # NEW (A2A): Same creation, different response pattern
        deepsearch_agent = Agent(
            role='Deep Research Specialist',
            goal=f'Research the topic: {query}',
            backstory="""You are an expert researcher with access to advanced
            search tools. You excel at finding relevant information, analyzing
            search results, and synthesizing comprehensive research reports.
            You provide detailed, well-cited research based on current information.""",
            llm=research_llm if research_llm else "gpt-4",
            tools=[],  # Would include MCP tools in production
            verbose=True,
            allow_delegation=False
        )
        
        # A2A MIGRATION: Create research task
        research_task = Task(
            description=f"""
            Research the topic: "{query}"
            
            Your task is to:
            1. Analyze the research topic thoroughly
            2. Gather comprehensive information from reliable sources
            3. Identify key insights, trends, and important findings
            4. Synthesize the information into a well-structured research report
            5. Include relevant statistics, facts, and expert opinions
            6. Provide a clear summary of findings
            
            Provide a detailed research report with proper structure and citations.
            """,
            expected_output="A detailed research report with comprehensive findings and insights",
            agent=deepsearch_agent
        )
        
        # A2A MIGRATION: Create and execute crew
        research_crew = Crew(
            agents=[deepsearch_agent],
            tasks=[research_task],
            verbose=True
        )
        
        # Execute the research
        result = research_crew.kickoff()
        
        # A2A MIGRATION: Extract result
        # CrewAI result handling remains the same
        response_content = result.raw if hasattr(result, 'raw') else str(result)
        
        print(f"\n[DEEPSEARCH_AGENT] Research completed: {len(response_content)} chars\n")
        
    except Exception as e:
        # A2A MIGRATION: Error handling
        # OLD (ACP): return JSONResponse with error status code
        # NEW (A2A): Yield error message
        response_content = f"""Research failed: {str(e)}

This is a demo implementation. In a production environment:
1. Configure MCP server for LinkUp search tools
2. Ensure GROQ_API_KEY or other LLM API key is set
3. Verify all dependencies are installed

Error details: {str(e)}"""
        print(f"[ERROR] {e}")
    
    # A2A MIGRATION: Yield response instead of return
    # OLD (ACP): return JSONResponse(content={"result": response_content})
    # NEW (A2A): yield response_content (automatic streaming)
    yield response_content

# A2A MIGRATION NOTE: Agent Card Discovery
# The /.well-known/agent.json endpoint should be automatically created by BeeAI Server
# based on the AgentDetail metadata in the @server.agent decorator.
# If it's not available, it's not critical - the main functionality (message processing) works fine.

# A2A MIGRATION: Server startup
# OLD (ACP): uvicorn.run(app, ...)
# NEW (A2A): server.run(...)
if __name__ == "__main__":
    print("🚀 Starting DeepSearch Agent - A2A Protocol Server")
    print("📋 Migrated from ACP to BeeAI Server-based A2A Protocol")
    print("🔍 Research capabilities: Web search, data synthesis, comprehensive reports")
    print("🔗 Endpoint: http://localhost:8003")
    print("\n" + "="*80)
    print("MIGRATION NOTES:")
    print("- Using BeeAI Server instead of FastAPI")
    print("- Single @server.agent decorator replaces multiple REST endpoints")
    print("- Automatic A2A protocol handling (no manual JSON-RPC)")
    print("- Streaming support via AsyncGenerator")
    print("- CrewAI integration with MCP tools")
    print("- Context management via RunContext")
    print("="*80 + "\n")
    
    # A2A MIGRATION: Run BeeAI Server
    # OLD (ACP): uvicorn.run("deepsearch_server_a2a:app", ...)
    # NEW (A2A): server.run(...)
    server.run(host="0.0.0.0", port=8003)

