#!/usr/bin/env python3
"""Test script to verify server parsing functions."""

import sys
from pathlib import Path
import json

# Add the interfaces directory to the path
sys.path.append(str(Path(__file__).parent / "interfaces"))

from server_generator import (
    discover_mcp_servers,
    _extract_server_capabilities,
    _parse_typescript_tools,
    _parse_typescript_resources,
    _extract_env_vars_from_readme
)

def test_server_discovery():
    """Test server discovery function."""
    print("=== Testing Server Discovery ===")
    
    servers = discover_mcp_servers()
    print(f"Found {len(servers)} servers:")
    
    for server in servers:
        print(f"\n📦 {server['name']}")
        print(f"  Status: {server['status']}")
        print(f"  Description: {server['description'][:100]}...")
        print(f"  Tools: {len(server.get('tools', []))}")
        print(f"  Resources: {len(server.get('resources', []))}")
        print(f"  Environment Variables: {len(server.get('environment_variables', []))}")
        print(f"  Has Tests: {server.get('has_tests', False)}")
        print(f"  Has Docs: {server.get('has_docs', False)}")

def test_auth_server_parsing():
    """Test parsing of auth-mcp-server specifically."""
    print("\n=== Testing Auth Server Parsing ===")
    
    auth_server_path = Path(__file__).parent.parent / "mcp-servers" / "auth-mcp-server"
    
    if not auth_server_path.exists():
        print(f"❌ Auth server not found at: {auth_server_path}")
        return
    
    print(f"✅ Found auth server at: {auth_server_path}")
    
    # Test capabilities extraction
    capabilities = _extract_server_capabilities(auth_server_path)
    print(f"\nCapabilities extracted:")
    print(f"  Tools: {len(capabilities['tools'])}")
    print(f"  Resources: {len(capabilities['resources'])}")
    print(f"  Integrations: {len(capabilities['integrations'])}")
    
    # Show sample tools
    if capabilities['tools']:
        print(f"\nSample tools:")
        for tool in capabilities['tools'][:3]:
            print(f"  - {tool['name']}: {tool['description'][:50]}...")
    
    # Show sample resources
    if capabilities['resources']:
        print(f"\nSample resources:")
        for resource in capabilities['resources'][:3]:
            print(f"  - {resource['uri']}: {resource['description'][:50]}...")
    
    # Test README parsing
    readme_path = auth_server_path / "README.md"
    if readme_path.exists():
        print(f"\n📖 Testing README parsing...")
        readme_content = readme_path.read_text(encoding='utf-8', errors='ignore')
        env_vars = _extract_env_vars_from_readme(readme_content)
        print(f"  Environment variables found: {len(env_vars)}")
        
        for env_var in env_vars[:5]:
            print(f"  - {env_var['name']}: {env_var['description'][:50]}...")

def test_tools_parsing():
    """Test parsing of tools.ts file specifically."""
    print("\n=== Testing Tools File Parsing ===")
    
    tools_file = Path(__file__).parent.parent / "mcp-servers" / "auth-mcp-server" / "src" / "keycloak" / "tools.ts"
    
    if not tools_file.exists():
        print(f"❌ Tools file not found at: {tools_file}")
        return
    
    print(f"✅ Found tools file at: {tools_file}")
    
    content = tools_file.read_text(encoding='utf-8', errors='ignore')
    print(f"File size: {len(content)} characters")
    
    # Test parsing
    tools = _parse_typescript_tools(content)
    print(f"Parsed {len(tools)} tools:")
    
    for tool in tools[:5]:
        print(f"  - {tool['name']} ({tool['category']}): {tool['description'][:60]}...")

if __name__ == "__main__":
    test_server_discovery()
    test_auth_server_parsing()
    test_tools_parsing()
    print("\n=== Test Complete ===")
