#!/usr/bin/env python3
"""
BeeAI Platform A2A Integration - Complete Implementation
Based on: https://github.com/i-am-bee/beeai-platform/blob/main/docs/community-and-support/acp-a2a-migration-guide.mdx

This script implements complete A2A functionality with BeeAI platform integration:
1. Agent registration and discovery
2. Platform-managed context and memory
3. LLM service extensions
4. Trajectory and citations
5. File handling and processing
6. Multi-agent orchestration
"""

import os
import asyncio
import json
import httpx
from typing import Dict, Any, List, Optional, AsyncGenerator
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BeeAIPlatformIntegration:
    """
    Complete A2A platform integration following BeeAI migration guide
    """
    
    def __init__(self):
        self.platform_url = os.getenv("BEEAI_PLATFORM_URL", "http://localhost:8000")
        self.agents = {}
        self.contexts = {}
        
    async def register_agent(self, agent_name: str, agent_config: Dict[str, Any]) -> bool:
        """
        Register agent with BeeAI platform
        
        A2A MIGRATION: Agent registration is now platform-managed
        OLD (ACP): Manual agent discovery and registration
        NEW (A2A): Automatic registration via BeeAI platform
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.platform_url}/v1/agents/register",
                    json={
                        "name": agent_name,
                        "config": agent_config,
                        "capabilities": agent_config.get("capabilities", []),
                        "endpoints": agent_config.get("endpoints", {})
                    }
                )
                
                if response.status_code == 200:
                    self.agents[agent_name] = response.json()
                    print(f"✅ Agent '{agent_name}' registered successfully")
                    return True
                else:
                    print(f"❌ Failed to register agent '{agent_name}': {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error registering agent '{agent_name}': {e}")
            return False
    
    async def discover_agents(self) -> List[Dict[str, Any]]:
        """
        Discover available agents via BeeAI platform
        
        A2A MIGRATION: Agent discovery is now centralized
        OLD (ACP): Manual agent discovery via custom endpoints
        NEW (A2A): Platform-managed agent discovery
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.platform_url}/v1/agents")
                
                if response.status_code == 200:
                    agents = response.json()
                    print(f"🔍 Discovered {len(agents)} agents")
                    return agents
                else:
                    print(f"❌ Failed to discover agents: {response.text}")
                    return []
                    
        except Exception as e:
            print(f"❌ Error discovering agents: {e}")
            return []
    
    async def get_agent_endpoint(self, agent_name: str) -> Optional[str]:
        """
        Get agent endpoint for communication
        
        A2A MIGRATION: Endpoints are now platform-managed
        OLD (ACP): Manual endpoint configuration
        NEW (A2A): Platform-provided endpoints
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.platform_url}/v1/agents/{agent_name}")
                
                if response.status_code == 200:
                    agent_info = response.json()
                    return agent_info.get("endpoint")
                else:
                    print(f"❌ Failed to get endpoint for agent '{agent_name}': {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error getting endpoint for agent '{agent_name}': {e}")
            return None
    
    async def send_message(self, agent_name: str, message: Dict[str, Any], 
                          context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """
        Send message to agent via A2A protocol
        
        A2A MIGRATION: Message format follows BeeAI Server standards
        OLD (ACP): Custom JSON-RPC format
        NEW (A2A): BeeAI Server message format with streaming
        """
        endpoint = await self.get_agent_endpoint(agent_name)
        if not endpoint:
            yield f"❌ No endpoint available for agent '{agent_name}'"
            return
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "message": {
                        "content": [{"text": message.get("text", "")}],
                        "metadata": message.get("metadata", {})
                    }
                }
                
                if context:
                    payload["context"] = context
                
                async with client.stream(
                    "POST",
                    f"{endpoint}/v1/message:stream",
                    json=payload
                ) as response:
                    if response.status_code == 200:
                        async for chunk in response.aiter_text():
                            if chunk.strip():
                                try:
                                    # Parse streaming JSON response
                                    data = json.loads(chunk)
                                    if "content" in data:
                                        yield data["content"]
                                    elif "status" in data:
                                        yield f"Status: {data['status']}"
                                except json.JSONDecodeError:
                                    # Handle non-JSON streaming content
                                    yield chunk
                    else:
                        yield f"❌ Error: {response.status_code} - {await response.aread()}"
                        
        except Exception as e:
            yield f"❌ Error sending message to agent '{agent_name}': {e}"
    
    async def orchestrate_workflow(self, workflow_config: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Orchestrate multi-agent workflow
        
        A2A MIGRATION: Workflow orchestration is now platform-managed
        OLD (ACP): Manual workflow coordination
        NEW (A2A): Platform-managed workflow with context sharing
        """
        yield "🚀 Starting A2A Multi-Agent Workflow"
        yield "=" * 50
        
        # Step 1: Discover available agents
        agents = await self.discover_agents()
        if not agents:
            yield "❌ No agents available"
            return
        
        yield f"📋 Found {len(agents)} agents: {[a['name'] for a in agents]}"
        
        # Step 2: Execute workflow steps
        workflow_steps = workflow_config.get("steps", [])
        context = {}
        
        for i, step in enumerate(workflow_steps, 1):
            yield f"\n🔄 Step {i}: {step['name']}"
            yield f"📝 Description: {step.get('description', '')}"
            
            agent_name = step.get("agent")
            if not agent_name:
                yield f"❌ No agent specified for step {i}"
                continue
            
            # Prepare message with context
            message = {
                "text": step.get("input", ""),
                "metadata": {
                    "step": i,
                    "workflow_id": workflow_config.get("id", "default"),
                    "context": context
                }
            }
            
            # Send message to agent
            step_output = []
            async for response in self.send_message(agent_name, message, context):
                step_output.append(response)
                yield f"📤 {agent_name}: {response}"
            
            # Update context with step output
            context[f"step_{i}_output"] = "\n".join(step_output)
            context[f"step_{i}_agent"] = agent_name
        
        yield "\n✅ Workflow completed successfully!"
        yield f"📊 Final context: {json.dumps(context, indent=2)}"

class A2AAgentManager:
    """
    A2A Agent Manager for BeeAI Platform Integration
    """
    
    def __init__(self):
        self.integration = BeeAIPlatformIntegration()
        self.agent_configs = {
            "deepsearch_agent": {
                "name": "DeepSearch Research Agent",
                "description": "Research agent using CrewAI framework with MCP tools",
                "capabilities": ["research", "web_search", "content_analysis"],
                "endpoints": {
                    "message": "/v1/message:stream",
                    "health": "/health"
                },
                "model": "groq/llama-3.3-70b-versatile",
                "tools": ["mcp_linkup_search"]
            },
            "blogpost_agent": {
                "name": "BlogPost Generator Agent", 
                "description": "Content generation agent using LangGraph workflow",
                "capabilities": ["content_generation", "blog_writing", "markdown_formatting"],
                "endpoints": {
                    "message": "/v1/message:stream",
                    "health": "/health"
                },
                "model": "groq/llama-3.3-70b-versatile",
                "workflow": "langgraph_blog_generation"
            }
        }
    
    async def setup_agents(self) -> bool:
        """
        Setup and register all A2A agents with BeeAI platform
        """
        print("🔧 Setting up A2A agents with BeeAI platform...")
        
        success_count = 0
        for agent_name, config in self.agent_configs.items():
            if await self.integration.register_agent(agent_name, config):
                success_count += 1
        
        print(f"✅ Successfully registered {success_count}/{len(self.agent_configs)} agents")
        return success_count == len(self.agent_configs)
    
    async def run_demo_workflow(self) -> None:
        """
        Run a complete A2A workflow demonstration
        """
        print("\n🎯 Running A2A Workflow Demo")
        print("=" * 50)
        
        # Define workflow
        workflow_config = {
            "id": "a2a_demo_workflow",
            "name": "A2A Multi-Agent Blog Generation",
            "steps": [
                {
                    "name": "Research Phase",
                    "description": "Research topic using DeepSearch agent",
                    "agent": "deepsearch_agent",
                    "input": "Research the topic: 'ACP: Automated Commerce Protocol' - provide comprehensive information about its history, components, benefits, and real-world applications."
                },
                {
                    "name": "Content Generation Phase", 
                    "description": "Generate blog post using BlogPost agent",
                    "agent": "blogpost_agent",
                    "input": "Generate a comprehensive blog post about ACP (Automated Commerce Protocol) based on the research data provided. Include introduction, key components, benefits, challenges, and real-world applications."
                }
            ]
        }
        
        # Execute workflow
        async for output in self.integration.orchestrate_workflow(workflow_config):
            print(output)

async def main():
    """
    Main function for A2A platform integration
    """
    print("🚀 BeeAI Platform A2A Integration")
    print("Based on: https://github.com/i-am-bee/beeai-platform/blob/main/docs/community-and-support/acp-a2a-migration-guide.mdx")
    print("=" * 80)
    
    # Initialize agent manager
    agent_manager = A2AAgentManager()
    
    # Setup agents
    if await agent_manager.setup_agents():
        print("✅ All agents registered successfully")
        
        # Run demo workflow
        await agent_manager.run_demo_workflow()
    else:
        print("❌ Failed to setup agents")
        print("💡 Make sure BeeAI platform is running and accessible")

if __name__ == "__main__":
    asyncio.run(main())
