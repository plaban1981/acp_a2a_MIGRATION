#!/usr/bin/env python3
"""
ACP to A2A Migration - Main Launcher
Demonstrates the migrated agent system

MIGRATION SUMMARY:
- Migrated from ACP (Agent Communication Protocol) to A2A (Agent-to-Agent Protocol)
- Replaced FastAPI with BeeAI Server
- Updated from custom JSON-RPC to BeeAI Server endpoints
- Simplified message handling and response patterns
- Added comprehensive migration comments in all scripts
"""

import sys
import subprocess
import os

def print_banner():
    """Print migration banner"""
    print("="*80)
    print("   ACP to A2A Migration Demo")
    print("   BeeAI Server-based Agent Implementation")
    print("="*80)
    print()
    print("MIGRATION HIGHLIGHTS:")
    print("✅ Replaced FastAPI with BeeAI Server")
    print("✅ Changed from @app.post() to @server.agent() decorator")
    print("✅ Updated message extraction from dict to message.parts")
    print("✅ Changed response from return to yield (streaming)")
    print("✅ Simplified endpoints: /v1/message:stream instead of /a2a/tasks/send")
    print("✅ Added streaming JSON parser for agent-to-agent communication")
    print("✅ Removed manual task tracking (platform-managed)")
    print("="*80)
    print()

def print_usage():
    """Print usage information"""
    print("Usage: python main.py [command]")
    print()
    print("Commands:")
    print("  server-blog      - Start BlogPost Generator Agent (port 8004)")
    print("  server-research  - Start DeepSearch Research Agent (port 8003)")
    print("  client          - Run the agentic client workflow")
    print("  platform        - Start BeeAI Platform A2A integration")
    print("  enhanced        - Start enhanced A2A agents with platform integration")
    print("  demo            - Run complete A2A workflow demonstration")
    print("  help            - Show this help message")
    print()
    print("Examples:")
    print("  python main.py server-blog")
    print("  python main.py server-research")
    print("  python main.py client")
    print("  python main.py platform")
    print("  python main.py enhanced")
    print("  python main.py demo")
    print()
    print("To run full workflow:")
    print("  Terminal 1: python main.py server-research")
    print("  Terminal 2: python main.py server-blog")
    print("  Terminal 3: python main.py client")
    print()
    print("For complete A2A platform integration:")
    print("  python main.py platform")
    print("  python main.py enhanced")
    print("  python main.py demo")

def main():
    """
    Main launcher for ACP to A2A migration demo
    
    A2A MIGRATION NOTE:
    This launcher simplifies running the migrated agents
    Each agent runs as a BeeAI Server instance
    """
    print_banner()
    
    if len(sys.argv) < 2:
        print("❌ No command specified")
        print()
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "server-blog":
        print("🚀 Starting BlogPost Generator Agent Server...")
        print("📋 Migrated from ACP FastAPI to BeeAI Server")
        print("🔗 Endpoint: http://localhost:8004")
        print("-" * 80)
        subprocess.run([sys.executable, "blogpost_server_a2a.py"])
    
    elif command == "server-research":
        print("🚀 Starting DeepSearch Research Agent Server...")
        print("📋 Migrated from ACP FastAPI to BeeAI Server")
        print("🔗 Endpoint: http://localhost:8003")
        print("-" * 80)
        subprocess.run([sys.executable, "deepserach_server_a2a.py"])
    
    elif command == "client":
        print("🤖 Starting Agentic Client...")
        print("📋 Migrated from custom JSON-RPC to BeeAI Server endpoints")
        print("-" * 80)
        # Pass through any additional arguments to the client
        client_args = sys.argv[2:] if len(sys.argv) > 2 else []
        subprocess.run([sys.executable, "agentic_client_a2a.py"] + client_args)
    
    elif command == "platform":
        print("🚀 Starting BeeAI Platform A2A Integration...")
        print("📋 Complete platform integration with enhanced features")
        print("-" * 80)
        subprocess.run([sys.executable, "platform_launcher.py"])
    
    elif command == "enhanced":
        print("🔧 Starting Enhanced A2A Agents...")
        print("📋 Platform-managed context, LLM extensions, memory management")
        print("-" * 80)
        print("Available enhanced agents:")
        print("  1. Enhanced DeepSearch Agent")
        print("  2. Enhanced BlogPost Agent")
        print()
        choice = input("Select agent (1-2) or 'both' for both: ").strip().lower()
        
        if choice == "1" or choice == "deepsearch":
            subprocess.run([sys.executable, "enhanced_deepsearch_agent.py"])
        elif choice == "2" or choice == "blogpost":
            subprocess.run([sys.executable, "enhanced_blogpost_agent.py"])
        elif choice == "both":
            print("Starting both enhanced agents...")
            print("Terminal 1: Enhanced DeepSearch Agent")
            print("Terminal 2: Enhanced BlogPost Agent")
            print("Run in separate terminals:")
            print("  python enhanced_deepsearch_agent.py")
            print("  python enhanced_blogpost_agent.py")
        else:
            print("❌ Invalid choice. Please select 1, 2, or 'both'")
    
    elif command == "demo":
        print("🎯 Running Complete A2A Workflow Demo...")
        print("📋 Demonstrates all A2A capabilities with platform integration")
        print("-" * 80)
        print("Choose demo type:")
        print("  1. Simple Demo (works with existing agents)")
        print("  2. Platform Demo (requires BeeAI platform)")
        print()
        choice = input("Select demo type (1-2): ").strip()
        
        if choice == "1":
            subprocess.run([sys.executable, "simple_a2a_demo.py"])
        elif choice == "2":
            subprocess.run([sys.executable, "beeai_platform_integration.py"])
        else:
            print("❌ Invalid choice. Please select 1 or 2")
    
    elif command == "help" or command == "-h" or command == "--help":
        print_usage()
    
    else:
        print(f"❌ Unknown command: {command}")
        print()
        print_usage()

if __name__ == "__main__":
    main()

