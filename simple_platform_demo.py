#!/usr/bin/env python3
"""
Simple A2A Platform Demo - Windows Compatible
Demonstrates A2A capabilities without requiring full BeeAI platform
"""

import asyncio
import httpx
import json
from typing import Dict, Any

class SimpleA2ADemo:
    """
    Simple A2A demonstration that works on Windows
    Shows agent-to-agent communication without full platform
    """
    
    def __init__(self):
        self.agents = {
            "research": "http://localhost:8003",
            "blog": "http://localhost:8004"
        }
    
    def print_banner(self):
        """Print demo banner"""
        print("=" * 80)
        print("   Simple A2A Platform Demo")
        print("   Windows Compatible")
        print("=" * 80)
        print()
        print("FEATURES:")
        print("✅ Agent-to-agent communication")
        print("✅ Streaming responses")
        print("✅ Multi-agent workflows")
        print("✅ Enhanced agent capabilities")
        print("✅ No platform dependencies")
        print("=" * 80)
        print()
    
    async def check_agents(self) -> Dict[str, bool]:
        """Check if agents are running"""
        print("🔍 Checking agent availability...")
        results = {}
        
        for name, url in self.agents.items():
            try:
                async with httpx.AsyncClient() as client:
                    # Test streaming endpoint
                    payload = {
                        "message": {
                            "content": [{"text": "Health check"}]
                        }
                    }
                    
                    async with client.stream(
                        "POST",
                        f"{url}/v1/message:stream",
                        json=payload,
                        timeout=5.0
                    ) as response:
                        if response.status_code == 200:
                            print(f"✅ {name.capitalize()} agent is running at {url}")
                            results[name] = True
                        else:
                            print(f"❌ {name.capitalize()} agent failed: HTTP {response.status_code}")
                            results[name] = False
                            
            except Exception as e:
                print(f"❌ {name.capitalize()} agent not available: {e}")
                results[name] = False
        
        return results
    
    async def run_workflow_demo(self):
        """Run a complete A2A workflow demonstration"""
        print("🚀 Running A2A Workflow Demo...")
        print("-" * 50)
        
        # Step 1: Research Phase
        print("\n🔍 Step 1: Research Phase")
        print("=" * 30)
        
        research_query = "Research the topic: 'ACP to A2A Migration Benefits' - provide detailed analysis of migration patterns, benefits, and best practices."
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "message": {
                        "content": [{"text": research_query}]
                    }
                }
                
                print(f"📤 Sending research query to research agent...")
                print(f"📝 Query: {research_query[:100]}...")
                
                async with client.stream(
                    "POST",
                    f"{self.agents['research']}/v1/message:stream",
                    json=payload,
                    timeout=60.0
                ) as response:
                    if response.status_code == 200:
                        print("📡 Research response:")
                        print("-" * 30)
                        
                        research_result = ""
                        async for chunk in response.aiter_text():
                            if chunk.strip():
                                print(chunk, end="")
                                research_result += chunk
                        
                        print("\n" + "-" * 30)
                        print("✅ Research phase completed")
                        
                        # Step 2: Blog Generation Phase
                        print("\n✍️ Step 2: Blog Generation Phase")
                        print("=" * 30)
                        
                        blog_query = f"Generate a comprehensive blog post about ACP to A2A migration based on this research: {research_result[:1000]}..."
                        
                        print(f"📤 Sending blog generation request...")
                        print(f"📝 Request: {blog_query[:100]}...")
                        
                        blog_payload = {
                            "message": {
                                "content": [{"text": blog_query}]
                            }
                        }
                        
                        async with client.stream(
                            "POST",
                            f"{self.agents['blog']}/v1/message:stream",
                            json=blog_payload,
                            timeout=60.0
                        ) as response:
                            if response.status_code == 200:
                                print("📡 Blog generation response:")
                                print("-" * 30)
                                
                                blog_result = ""
                                async for chunk in response.aiter_text():
                                    if chunk.strip():
                                        print(chunk, end="")
                                        blog_result += chunk
                                
                                print("\n" + "-" * 30)
                                print("✅ Blog generation phase completed")
                                
                                # Summary
                                print("\n🎉 A2A Workflow Completed Successfully!")
                                print("=" * 50)
                                print("📊 Results Summary:")
                                print(f"  🔍 Research: ✅ Completed ({len(research_result)} chars)")
                                print(f"  ✍️ Blog Generation: ✅ Completed ({len(blog_result)} chars)")
                                print()
                                print("🎯 A2A Capabilities Demonstrated:")
                                print("  ✅ Agent-to-agent communication")
                                print("  ✅ Streaming responses")
                                print("  ✅ Multi-agent workflow orchestration")
                                print("  ✅ Enhanced content generation")
                                print("  ✅ Platform-independent operation")
                                print()
                                print("🚀 Your A2A system is working perfectly!")
                                
                            else:
                                print(f"❌ Blog generation failed: HTTP {response.status_code}")
                    else:
                        print(f"❌ Research failed: HTTP {response.status_code}")
                        
        except Exception as e:
            print(f"❌ Workflow failed: {e}")
    
    async def run_interactive_demo(self):
        """Run interactive A2A demonstration"""
        print("🎮 Interactive A2A Demo")
        print("=" * 30)
        print("Available agents:")
        print("  1. Research Agent (research)")
        print("  2. Blog Generation Agent (blog)")
        print("  3. Complete Workflow (workflow)")
        print("  4. Exit")
        print()
        
        while True:
            try:
                choice = input("Select option (1-4): ").strip()
                
                if choice == "1":
                    query = input("Enter research query: ").strip()
                    if query:
                        await self.send_message("research", query)
                
                elif choice == "2":
                    query = input("Enter blog generation request: ").strip()
                    if query:
                        await self.send_message("blog", query)
                
                elif choice == "3":
                    await self.run_workflow_demo()
                
                elif choice == "4":
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid choice. Please select 1-4.")
                
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Demo interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def send_message(self, agent_name: str, message: str):
        """Send message to specific agent"""
        if agent_name not in self.agents:
            print(f"❌ Unknown agent: {agent_name}")
            return
        
        url = self.agents[agent_name]
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "message": {
                        "content": [{"text": message}]
                    }
                }
                
                print(f"📤 Sending message to {agent_name} agent...")
                print(f"📝 Message: {message}")
                print("-" * 50)
                
                async with client.stream(
                    "POST",
                    f"{url}/v1/message:stream",
                    json=payload,
                    timeout=60.0
                ) as response:
                    if response.status_code == 200:
                        print("📡 Response:")
                        print("-" * 30)
                        
                        async for chunk in response.aiter_text():
                            if chunk.strip():
                                print(chunk, end="")
                        
                        print("\n" + "-" * 30)
                        print("✅ Message processed successfully")
                    else:
                        print(f"❌ Request failed: HTTP {response.status_code}")
                        
        except Exception as e:
            print(f"❌ Communication failed: {e}")

async def main():
    """Main function"""
    demo = SimpleA2ADemo()
    demo.print_banner()
    
    # Check if agents are running
    agent_status = await demo.check_agents()
    
    if not any(agent_status.values()):
        print("\n❌ No agents are running!")
        print("💡 Please start the agents first:")
        print("   Terminal 1: python main.py server-research")
        print("   Terminal 2: python main.py server-blog")
        return
    
    print(f"\n✅ {sum(agent_status.values())} agent(s) are running")
    
    # Run interactive demo
    await demo.run_interactive_demo()

if __name__ == "__main__":
    print("🚀 Simple A2A Platform Demo")
    print("Windows Compatible - No Platform Dependencies")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
