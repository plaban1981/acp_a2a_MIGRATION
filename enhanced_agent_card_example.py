#!/usr/bin/env python3
"""
Enhanced Agent Card Example - Following BeeAI Migration Guide Best Practices
Based on: https://github.com/i-am-bee/beeai-platform/blob/main/docs/community-and-support/acp-a2a-migration-guide.mdx
"""

from a2a.types import Message, AgentSkill
from beeai_sdk.server import Server
from beeai_sdk.server.context import RunContext
from beeai_sdk.a2a.extensions import AgentDetail, AgentDetailTool
from textwrap import dedent

server = Server()

@server.agent(
    name="Enhanced BlogPost Generator",
    default_input_modes=["text", "text/plain", "application/json"],
    default_output_modes=["text", "text/plain", "text/markdown"],
    detail=AgentDetail(
        interaction_mode="multi-turn",  # Enhanced: Allow follow-up questions
        user_greeting=dedent("""
            Hi! I'm your Enhanced BlogPost Generator powered by LangGraph and Groq LLM. 
            
            🚀 **What I can do:**
            - Transform research content into engaging blog posts
            - Generate SEO-optimized content with proper structure
            - Create markdown files with metadata
            - Handle multi-turn conversations for content refinement
            
            📝 **How to use me:**
            Send me research content, and I'll create a comprehensive blog post for you!
        """),
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
            description=dedent("""
                Transform research content into engaging, SEO-optimized blog posts with proper markdown formatting.
                
                **Key Features:**
                - Multi-step LangGraph workflow for quality content
                - SEO optimization with meta tags and structure
                - Automatic markdown file generation
                - Context-aware content adaptation
                - Multi-turn conversation support for refinements
            """),
            tags=["Content", "Blog", "SEO", "Writing", "LangGraph"],
            examples=[
                "Generate a blog post from this research about AI trends in 2025",
                "Create an SEO-optimized article based on market analysis data",
                "Write a comprehensive blog post about quantum computing applications",
                "Transform this technical research into a business-friendly blog post",
                "Create a series of blog posts from this comprehensive research report"
            ],
            input_requirements=[
                "Research content or topic description",
                "Optional: Target audience specification",
                "Optional: SEO keywords or focus areas"
            ],
            output_format="Markdown file with metadata and SEO optimization"
        ),
        AgentSkill(
            id="content-analysis",
            name="Content Analysis & Optimization",
            description=dedent("""
                Analyze research content quality and provide optimization suggestions.
                
                **Capabilities:**
                - Content structure analysis
                - Key insight extraction
                - SEO opportunity identification
                - Readability assessment
                - Content gap analysis
            """),
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
            description=dedent("""
                Support iterative content improvement through conversation.
                
                **Features:**
                - Follow-up question handling
                - Content refinement requests
                - Style and tone adjustments
                - Length and format modifications
                - Additional research integration
            """),
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
async def enhanced_blogpost_agent(
    message: Message,
    context: RunContext,
) -> AsyncGenerator[str, None]:
    """
    Enhanced BlogPost agent with comprehensive agent card details
    
    This agent demonstrates best practices for A2A agent card implementation
    following the BeeAI migration guide recommendations.
    """
    
    # Extract query from A2A message
    query = extract_query_from_message(message)
    
    yield f"✍️ Enhanced BlogPost Generator - Processing: {query}"
    yield "=" * 60
    yield "🚀 Powered by LangGraph + Groq LLM + A2A Protocol"
    yield "📊 Multi-turn conversation support enabled"
    yield "🔍 SEO optimization and content analysis included"
    yield "=" * 60
    
    # Your existing blog generation logic here...
    yield "📝 Blog generation workflow initiated..."
    yield "✅ Enhanced agent card details provide better user experience!"

def extract_query_from_message(message: Message) -> str:
    """Extract query from A2A message format"""
    if message.parts:
        for part in message.parts:
            if hasattr(part, 'text') and part.text:
                return part.text
            elif hasattr(part, 'content') and part.content:
                return part.content
    return "No query found in message"

if __name__ == "__main__":
    print("🚀 Enhanced Agent Card Example")
    print("Following BeeAI Migration Guide Best Practices")
    print("=" * 60)
