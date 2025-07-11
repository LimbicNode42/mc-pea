#!/usr/bin/env python3
"""
Agent Configuration Management Utility

This script provides command-line tools for managing agent configurations:
- View current configurations
- Update agent settings
- Validate configurations
- Add new agents
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.agent_config_loader import AgentConfigLoader, get_config_loader

def view_agent_config(agent_name: str = None) -> None:
    """View agent configuration(s)."""
    loader = get_config_loader()
    
    if agent_name:
        print(f"🤖 Configuration for agent: {agent_name}")
        print("=" * 50)
        config = loader.get_agent_config(agent_name)
        if config:
            print(json.dumps(config, indent=2))
        else:
            print(f"❌ No configuration found for agent: {agent_name}")
    else:
        print("🤖 All Agent Configurations")
        print("=" * 30)
        agent_names = loader.get_all_agent_names()
        for name in agent_names:
            print(f"\n📋 Agent: {name}")
            config = loader.get_agent_config(name)
            print(f"   Role: {config.get('role', 'N/A')}")
            print(f"   Dependencies: {len(config.get('mcp_dependencies', []))}")
            print(f"   Kubernetes Ready: {config.get('kubernetes_ready', False)}")
            print(f"   Deployment Friendly: {config.get('deployment_friendly', False)}")

def validate_configurations() -> None:
    """Validate all agent configurations."""
    loader = get_config_loader()
    
    print("🔍 Validating Agent Configurations")
    print("=" * 35)
    
    agent_names = loader.get_all_agent_names()
    total_agents = len(agent_names)
    valid_agents = 0
    
    for agent_name in agent_names:
        validation = loader.validate_agent_config(agent_name)
        
        print(f"\n📋 Agent: {agent_name}")
        if validation["valid"]:
            print("   ✅ Valid configuration")
            valid_agents += 1
        else:
            print("   ❌ Invalid configuration")
            for error in validation["errors"]:
                print(f"      - {error}")
        
        if validation["warnings"]:
            print("   ⚠️  Warnings:")
            for warning in validation["warnings"]:
                print(f"      - {warning}")
    
    print(f"\n📊 Summary: {valid_agents}/{total_agents} agents have valid configurations")

def update_agent_config(agent_name: str, updates: Dict[str, Any]) -> None:
    """Update agent configuration."""
    loader = get_config_loader()
    
    print(f"🔧 Updating configuration for agent: {agent_name}")
    
    success = loader.update_agent_config(agent_name, updates)
    
    if success:
        print("✅ Configuration updated successfully")
        # Show updated config
        updated_config = loader.get_agent_config(agent_name)
        print("\n📋 Updated configuration:")
        print(json.dumps(updated_config, indent=2))
    else:
        print("❌ Failed to update configuration")

def add_new_agent(agent_name: str, role: str, goal: str, backstory: str) -> None:
    """Add a new agent configuration."""
    loader = get_config_loader()
    
    new_config = {
        "name": agent_name,
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "mcp_dependencies": [],
        "fallback_description": "Self-contained agent with no external dependencies",
        "deployment_friendly": True,
        "kubernetes_ready": True,
        "docker_requirements": "Python runtime"
    }
    
    print(f"➕ Adding new agent: {agent_name}")
    
    success = loader.update_agent_config(agent_name, new_config)
    
    if success:
        print("✅ New agent configuration added successfully")
        print("\n📋 New agent configuration:")
        print(json.dumps(new_config, indent=2))
    else:
        print("❌ Failed to add new agent configuration")

def show_global_settings() -> None:
    """Show global settings and MCP standards."""
    loader = get_config_loader()
    
    print("🌐 Global Settings")
    print("=" * 20)
    global_settings = loader.get_global_settings()
    print(json.dumps(global_settings, indent=2))
    
    print("\n📋 MCP Standards")
    print("=" * 20)
    mcp_standards = loader.get_mcp_standards()
    print(json.dumps(mcp_standards, indent=2))
    
    print("\n🚀 Deployment Targets")
    print("=" * 20)
    targets = ["kubernetes", "docker", "serverless"]
    for target in targets:
        print(f"\n🎯 {target.title()}:")
        config = loader.get_deployment_config(target)
        print(json.dumps(config, indent=2))

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Agent Configuration Management Utility")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # View command
    view_parser = subparsers.add_parser("view", help="View agent configuration(s)")
    view_parser.add_argument("--agent", type=str, help="Specific agent name to view")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate all configurations")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update agent configuration")
    update_parser.add_argument("agent", type=str, help="Agent name to update")
    update_parser.add_argument("--role", type=str, help="Update agent role")
    update_parser.add_argument("--goal", type=str, help="Update agent goal")
    update_parser.add_argument("--backstory", type=str, help="Update agent backstory")
    update_parser.add_argument("--kubernetes-ready", type=bool, help="Update Kubernetes readiness")
    update_parser.add_argument("--deployment-friendly", type=bool, help="Update deployment friendliness")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add new agent configuration")
    add_parser.add_argument("agent", type=str, help="New agent name")
    add_parser.add_argument("--role", type=str, required=True, help="Agent role")
    add_parser.add_argument("--goal", type=str, required=True, help="Agent goal")
    add_parser.add_argument("--backstory", type=str, required=True, help="Agent backstory")
    
    # Global command
    global_parser = subparsers.add_parser("global", help="View global settings and standards")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "view":
            view_agent_config(args.agent)
        
        elif args.command == "validate":
            validate_configurations()
        
        elif args.command == "update":
            updates = {}
            if args.role:
                updates["role"] = args.role
            if args.goal:
                updates["goal"] = args.goal
            if args.backstory:
                updates["backstory"] = args.backstory
            if args.kubernetes_ready is not None:
                updates["kubernetes_ready"] = args.kubernetes_ready
            if args.deployment_friendly is not None:
                updates["deployment_friendly"] = args.deployment_friendly
            
            if not updates:
                print("❌ No updates specified. Use --role, --goal, --backstory, etc.")
                return
            
            update_agent_config(args.agent, updates)
        
        elif args.command == "add":
            add_new_agent(args.agent, args.role, args.goal, args.backstory)
        
        elif args.command == "global":
            show_global_settings()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
