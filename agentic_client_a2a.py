#!/usr/bin/env python3
"""
Agentic Client - A2A Protocol Implementation
Migrated from custom A2A JSON-RPC to BeeAI Server-based A2A Protocol

MIGRATION CHANGES FROM ACP TO A2A:
1. Changed from custom JSON-RPC endpoints (/a2a/tasks/send) to BeeAI Server endpoints (/v1/message:stream)
2. Updated message format from manual JSON-RPC to BeeAI streaming format
3. Updated response parsing from custom statusUpdate to BeeAI statusUpdate structure
4. Simplified message structure - no manual task IDs or session management
5. Changed from manual task tracking to platform-managed context
6. Removed custom Message/TextPart/DataPart classes - use simple dictionaries
7. Updated streaming response format to match BeeAI Server output
"""

import asyncio
import json
import httpx
import sys
from typing import Dict, Any

class A2AClient:
    """
    A2A Protocol Client for communicating with BeeAI Server agents
    
    A2A MIGRATION NOTE: Simplified from custom JSON-RPC implementation
    OLD (ACP): Used /a2a/tasks/send with full JSON-RPC structure
    NEW (A2A): Uses /v1/message:stream with simplified message format
    """
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=300.0, verify=False)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def discover_agent(self) -> Dict[str, Any]:
        """
        Discover agent capabilities via Agent Card
        
        A2A MIGRATION NOTE: Agent card discovery remains the same
        Endpoint: /.well-known/agent.json
        """
        try:
            response = await self.client.get(f"{self.base_url}/.well-known/agent.json")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to discover agent at {self.base_url}: {e}")
            return {}
    
    async def invoke_agent(self, text_input: str) -> str:
        """
        Call an A2A agent using BeeAI Server streaming API
        
        A2A MIGRATION CHANGES:
        1. Endpoint changed:
           OLD: POST /a2a/tasks/sendSubscribe with JSON-RPC
           NEW: POST /v1/message:stream with simplified message format
        
        2. Message format changed:
           OLD: {
               "jsonrpc": "2.0",
               "id": uuid,
               "method": "tasks/sendSubscribe",
               "params": {
                   "id": task_id,
                   "message": {"role": "user", "parts": [...]},
                   "sessionId": session_id
               }
           }
           NEW: {
               "message": {
                   "content": [{"text": text_input}]
               }
           }
        
        3. Response format changed:
           OLD: SSE with "data: " prefix, custom statusUpdate structure
           NEW: SSE with "data: " prefix, BeeAI statusUpdate structure
        """
        # A2A MIGRATION: Simplified message format
        # No need for manual task IDs, session IDs, or JSON-RPC structure
        payload = {
            "message": {
                "content": [{"text": text_input}]
            }
        }
        
        print(f"[invoke_agent] Streaming from {self.base_url}/v1/message:stream")
        
        chunks = []
        event_count = 0
        try:
            # A2A MIGRATION: Changed endpoint from /a2a/tasks/sendSubscribe to /v1/message:stream
            async with self.client.stream(
                "POST",
                f"{self.base_url}/v1/message:stream",
                json=payload,
                headers={"Accept": "text/event-stream"}
            ) as resp:
                if resp.status_code >= 400:
                    body = await resp.aread()
                    raise Exception(f"Agent error: HTTP {resp.status_code}: {body.decode()[:500]}")
                
                # A2A MIGRATION: Parse Server-Sent Events (SSE)
                # Response format is the same, but statusUpdate structure may differ
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        if data_str.strip() in ["[DONE]", ""]:
                            continue
                        
                        event_count += 1
                        
                        # DEBUG: Show raw SSE data
                        if event_count <= 2:
                            print(f"[DEBUG] Event {event_count} RAW data_str: {data_str[:150]}")
                        
                        try:
                            data = json.loads(data_str)
                            
                            # DEBUG: Show what we received
                            if event_count <= 3:
                                print(f"[DEBUG] Event {event_count} keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                                if isinstance(data, dict) and "statusUpdate" in data:
                                    print(f"[DEBUG] Event {event_count} full JSON structure:")
                                    print(f"  statusUpdate keys: {list(data['statusUpdate'].keys())}")
                                    if 'status' in data['statusUpdate']:
                                        print(f"  status keys: {list(data['statusUpdate']['status'].keys())}")
                            
                            # A2A MIGRATION: Extract text from BeeAI statusUpdate envelope
                            # Structure: statusUpdate.status.message.content[].text
                            if isinstance(data, dict) and "statusUpdate" in data:
                                status = data["statusUpdate"].get("status", {})
                                message = status.get("message", {})
                                content_list = message.get("content", [])
                                
                                if event_count <= 3:
                                    print(f"[DEBUG] Event {event_count}: status={bool(status)}, message={bool(message)}, content_list={len(content_list)}")
                                    if content_list:
                                        print(f"[DEBUG] Event {event_count}: content_list[0] = {content_list[0] if len(content_list) > 0 else 'empty'}")
                                
                                for part in content_list:
                                    if isinstance(part, dict) and "text" in part:
                                        text_chunk = str(part["text"])
                                        # Only append non-empty text chunks
                                        if text_chunk.strip():
                                            if event_count <= 3:
                                                print(f"[DEBUG] Event {event_count}: ✅ Extracted text: {len(text_chunk)} chars, first 100: {text_chunk[:100]}")
                                            chunks.append(text_chunk)
                                            # Print progress indicator (optional)
                                            if len(text_chunk) > 100:
                                                print(f"[invoke_agent] ✅ Extracted text chunk: {len(text_chunk)} chars")
                            # If no statusUpdate, might be direct message
                            elif isinstance(data, dict) and "content" in data:
                                for part in data.get("content", []):
                                    if isinstance(part, dict) and "text" in part:
                                        text_chunk = str(part["text"])
                                        if text_chunk.strip():
                                            chunks.append(text_chunk)
                                        
                        except json.JSONDecodeError as e:
                            # If JSON parsing fails, skip this line (don't append raw JSON)
                            if event_count <= 3:
                                print(f"[DEBUG] Event {event_count}: JSON parse failed - {e}")
                                print(f"[DEBUG] Event {event_count}: data_str[:100] = {data_str[:100]}")
                            # Only append if it looks like plain text (not starting with '{')
                            if data_str and not data_str.strip().startswith('{'):
                                if event_count <= 3:
                                    print(f"[DEBUG] Event {event_count}: Appending as plain text")
                                chunks.append(data_str)
                            else:
                                if event_count <= 3:
                                    print(f"[DEBUG] Event {event_count}: Skipping (looks like JSON)")
                
                result = "".join(chunks).strip()
                print(f"[invoke_agent] Total events: {event_count}, Extracted chunks: {len(chunks)}, Total chars: {len(result)}")
                
                if not result:
                    raise Exception("No content received from agent")
                
                # DEBUG: Show what we're returning
                if len(result) > 100:
                    print(f"[DEBUG] Result preview: {result[:200]}...")
                
                return result
                
        except httpx.ReadError as e:
            # Stream closed early - check if we got content
            if chunks:
                result = "".join(chunks).strip()
                print(f"[invoke_agent] Stream closed early, got {len(result)} chars")
                return result
            raise Exception(f"Stream error: {e}")

# Workflow Functions

async def sequential_workflow_a2a():
    """
    Main A2A workflow: User -> DeepSearch -> BlogPost Generator
    
    A2A MIGRATION NOTE: Workflow logic remains similar, but uses new client API
    OLD (ACP): Called send_task with full JSON-RPC structure
    NEW (A2A): Calls invoke_agent with simplified message format
    """
    print("🚀 Starting A2A Sequential Workflow")
    print("=" * 80)
    
    # Get topic from user
    topic = input("📝 Enter a topic for research and blog generation: ").strip()
    if not topic:
        topic = "The future of sustainable energy technologies"
        print(f"No topic entered. Using default: {topic}")
    
    print(f"\n🔍 Step 1: Discovering and researching topic: '{topic}'")
    print("-" * 60)
    
    # A2A MIGRATION: Step 1 - Communicate with DeepSearch Agent
    # OLD (ACP): Used send_task with complex JSON-RPC structure
    # NEW (A2A): Use invoke_agent with simple text input
    async with A2AClient("http://localhost:8003") as deepsearch_client:
        # Discover agent capabilities (optional)
        agent_card = await deepsearch_client.discover_agent()
        if agent_card:
            print(f"✅ Discovered DeepSearch Agent: {agent_card.get('name', 'Unknown')}")
        
        # A2A MIGRATION: Simplified agent invocation
        # Just pass the topic as text - no need for complex message structure
        try:
            research_content = await deepsearch_client.invoke_agent(topic)
            print(f"✅ Research completed: {len(research_content)} chars")
            
            # Show a clean preview of the research
            if research_content:
                # Try to extract meaningful preview (first few sentences)
                preview = research_content[:500].strip()
                if len(research_content) > 500:
                    # Find a good breaking point (end of sentence)
                    last_period = preview.rfind('.')
                    if last_period > 200:
                        preview = preview[:last_period + 1]
                    preview += "..."
                
                print(f"\n📋 Research Preview:")
                print("-" * 60)
                print(preview)
                print("-" * 60)
        except Exception as e:
            print(f"❌ Research failed: {e}")
            return
    
    print(f"\n📝 Step 2: Generating blog post from research data")
    print("-" * 60)
    
    # A2A MIGRATION: Step 2 - Communicate with BlogPost Generator Agent
    # OLD (ACP): Used send_task with artifacts and metadata
    # NEW (A2A): Use invoke_agent with research content
    async with A2AClient("http://localhost:8004") as blogpost_client:
        # Discover agent capabilities (optional)
        agent_card = await blogpost_client.discover_agent()
        if agent_card:
            print(f"✅ Discovered BlogPost Agent: {agent_card.get('name', 'Unknown')}")
        
        # A2A MIGRATION: Pass research content to blog generator
        try:
            blog_post = await blogpost_client.invoke_agent(research_content)
            print(f"✅ Blog post generated: {len(blog_post)} chars")
            
            # Display the blog post in a clean format
            print("\n" + "="*80)
            print("📝 GENERATED BLOG POST SUMMARY")
            print("="*80)
            
            # Extract key information if available
            if "**Title:**" in blog_post:
                # Clean display of the blog post info
                print(blog_post)
            else:
                # Fallback: just show the content
                print(blog_post)
            
            print("="*80)
            print("\n💡 TIP: Check your directory for the generated .md file")
        except Exception as e:
            print(f"❌ Blog generation failed: {e}")
            return
    
    print("\n" + "=" * 80)
    print("🎉 A2A Sequential workflow completed successfully!")

async def streaming_workflow_a2a():
    """
    Streaming A2A workflow with real-time updates
    
    A2A MIGRATION NOTE: Streaming is built into invoke_agent
    The client automatically handles streaming responses
    """
    print("🚀 Starting A2A Streaming Workflow")
    print("=" * 80)
    
    topic = input("📝 Enter a topic for research and blog generation: ").strip()
    if not topic:
        topic = "Latest developments in quantum computing"
        print(f"No topic entered. Using default: {topic}")
    
    print(f"\n🔍 Step 1: Streaming research for: '{topic}'")
    print("-" * 60)
    
    # A2A MIGRATION: Streaming is automatic with invoke_agent
    # The method handles SSE parsing internally
    research_content = ""
    async with A2AClient("http://localhost:8003") as deepsearch_client:
        try:
            research_content = await deepsearch_client.invoke_agent(topic)
            print(f"✅ Research completed: {len(research_content)} chars")
        except Exception as e:
            print(f"❌ Research failed: {e}")
            return
    
    if not research_content:
        print("❌ No research content received")
        return
    
    print(f"\n📝 Step 2: Streaming blog generation")
    print("-" * 60)
    
    # Step 2: Stream blog generation
    async with A2AClient("http://localhost:8004") as blogpost_client:
        try:
            blog_post = await blogpost_client.invoke_agent(research_content)
            print(f"✅ Blog generated!")
            print("\n" + "="*80)
            print("GENERATED BLOG POST")
            print("="*80)
            print(blog_post)
            print("="*80)
        except Exception as e:
            print(f"❌ Blog generation failed: {e}")
            return
    
    print("\n" + "=" * 80)
    print("🎉 A2A Streaming workflow completed!")

async def test_deepsearch_a2a():
    """
    Test DeepSearch agent independently using A2A protocol
    
    A2A MIGRATION NOTE: Simplified test function
    OLD (ACP): Used send_task with full structure
    NEW (A2A): Uses invoke_agent with simple text
    """
    print("🔍 Testing DeepSearch Agent (A2A Protocol)")
    print("-" * 60)
    
    topic = input("Enter a research topic: ").strip() or "Latest trends in artificial intelligence"
    
    async with A2AClient("http://localhost:8003") as client:
        # Discover agent
        agent_card = await client.discover_agent()
        if agent_card:
            print(f"✅ Agent: {agent_card.get('name', 'Unknown')}")
            print(f"📝 Description: {agent_card.get('description', 'N/A')}")
        
        # A2A MIGRATION: Simplified invocation
        try:
            result = await client.invoke_agent(topic)
            print(f"\n{'='*80}")
            print("RESEARCH RESULT")
            print('='*80)
            print(result)
            print('='*80)
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_blogpost_a2a():
    """
    Test BlogPost agent independently using A2A protocol
    
    A2A MIGRATION NOTE: Simplified test function
    """
    print("📝 Testing BlogPost Generator Agent (A2A Protocol)")
    print("-" * 60)
    
    # Mock research data
    mock_research = """
    Research Topic: Artificial Intelligence in Healthcare

    Executive Summary:
    AI in healthcare is revolutionizing patient care through diagnostic imaging, 
    drug discovery, and personalized treatment plans. The market is expected to 
    reach $102 billion by 2025.

    Key Insights:
    - AI diagnostic tools show 94% accuracy in cancer detection
    - Machine learning reduces drug discovery time by 30%
    - Telemedicine adoption increased 3800% during pandemic

    Recent Developments:
    - FDA approved 130+ AI medical devices in 2023
    - Google's Med-PaLM achieves expert-level medical reasoning

    Sources: McKinsey Global Institute, Nature Medicine, FDA Medical Device Database
    """
    
    async with A2AClient("http://localhost:8004") as client:
        # Discover agent
        agent_card = await client.discover_agent()
        if agent_card:
            print(f"✅ Agent: {agent_card.get('name', 'Unknown')}")
        
        # A2A MIGRATION: Simplified invocation
        try:
            result = await client.invoke_agent(mock_research)
            print(f"\n{'='*80}")
            print("BLOG POST RESULT")
            print('='*80)
            print(result)
            print('='*80)
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    """Main function with different A2A demo modes"""
    print("🤖 A2A Protocol Agentic Client")
    print("📋 Migrated from custom JSON-RPC to BeeAI Server-based A2A")
    print("=" * 80)
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "sequential":
            await sequential_workflow_a2a()
        elif mode == "streaming":
            await streaming_workflow_a2a()
        elif mode == "deepsearch":
            await test_deepsearch_a2a()
        elif mode == "blogpost":
            await test_blogpost_a2a()
        else:
            print("Usage: python agentic_client_a2a.py [sequential|streaming|deepsearch|blogpost]")
            print("  sequential - Main workflow: Topic -> DeepSearch -> BlogPost (RECOMMENDED)")
            print("  streaming  - Same workflow with real-time streaming updates")
            print("  deepsearch - Test DeepSearch agent only")
            print("  blogpost   - Test BlogPost generator only")
    else:
        # Default: run the main sequential workflow
        print("🧪 Running A2A sequential workflow...")
        print("\nMIGRATION NOTES:")
        print("- Using /v1/message:stream endpoint instead of /a2a/tasks/send")
        print("- Simplified message format (no JSON-RPC wrapper)")
        print("- Automatic streaming response handling")
        print("- Platform-managed context (no manual session/task IDs)")
        print("="*80 + "\n")
        await sequential_workflow_a2a()

if __name__ == "__main__":
    asyncio.run(main())
