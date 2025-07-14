"""
Server Discovery Module for Streamlit Interface
"""
import re
import sys
from pathlib import Path
from typing import Dict, Any, List
import streamlit as st

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


@st.cache_data(ttl=60)  # Cache for 60 seconds to allow updates
def discover_mcp_servers() -> List[Dict[str, Any]]:
    """Discover all generated MCP servers in the system.
    
    Returns:
        List of MCP server information dictionaries
    """
    servers = []
    
    # Check main mcp-servers directory
    mcp_servers_dir = Path(__file__).parent.parent.parent / "mcp-servers"
    
    if mcp_servers_dir.exists():
        for server_dir in mcp_servers_dir.iterdir():
            if server_dir.is_dir() and not server_dir.name.startswith('.'):
                server_info = _extract_server_info(server_dir)
                if server_info:
                    servers.append(server_info)
    
    return servers


def _extract_server_info(server_dir: Path) -> Dict[str, Any]:
    """Extract information about an MCP server from its directory.
    
    Args:
        server_dir: Path to the server directory
        
    Returns:
        Dictionary with server information
    """
    server_info = {
        "name": server_dir.name,
        "path": str(server_dir),
        "status": "unknown",
        "description": "No description available",
        "tools": [],
        "resources": [],
        "integrations": [],
        "has_tests": False,
        "has_docs": False,
        "package_json": None,
        "env_vars": []
    }
    
    # Check for package.json
    package_json_file = server_dir / "package.json"
    if package_json_file.exists():
        try:
            with open(package_json_file, 'r') as f:
                package_data = f.read()
                server_info["package_json"] = package_data
                server_info["status"] = "implemented"
        except Exception:
            pass
    
    # Check for README
    readme_file = server_dir / "README.md"
    if readme_file.exists():
        try:
            content = readme_file.read_text(encoding='utf-8', errors='ignore')
            # Extract description from README
            lines = content.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    server_info["description"] = line.strip()[:200]
                    break
            
            # Extract environment variables
            server_info["env_vars"] = _extract_env_vars_from_readme(content)
            server_info["has_docs"] = True
        except Exception:
            pass
    
    # Check for tests
    tests_dir = server_dir / "tests"
    if tests_dir.exists() and any(tests_dir.iterdir()):
        server_info["has_tests"] = True
    
    # Extract capabilities
    capabilities = _extract_server_capabilities(server_dir)
    server_info.update(capabilities)
    
    return server_info


def _extract_server_capabilities(server_dir: Path) -> Dict[str, Any]:
    """Extract tools and resources from MCP server source code.
    
    Args:
        server_dir: Path to the server directory
        
    Returns:
        Dictionary with tools and resources information
    """
    capabilities = {
        "tools": [],
        "resources": [],
        "integrations": []
    }
    
    src_dir = server_dir / "src"
    if not src_dir.exists():
        return capabilities
    
    # Look for TypeScript files and extract tools/resources
    for ts_file in src_dir.rglob("*.ts"):
        if ts_file.name == "index.ts":
            continue
            
        try:
            content = ts_file.read_text(encoding='utf-8', errors='ignore')
            
            # Extract tools
            tools = _parse_register_tool_calls(content)
            capabilities["tools"].extend(tools)
            
            # Extract resources
            resources = _parse_register_resource_calls(content)
            capabilities["resources"].extend(resources)
            
        except Exception:
            continue
    
    # Detect integrations from directory structure
    for subdir in src_dir.iterdir():
        if subdir.is_dir() and subdir.name not in ['__pycache__', 'node_modules', 'types', 'utils']:
            capabilities["integrations"].append({
                "name": subdir.name.title(),
                "type": "service_integration",
                "files": len(list(subdir.glob("*.ts")))
            })
    
    return capabilities


def _parse_register_tool_calls(content: str) -> List[Dict[str, Any]]:
    """Parse server.registerTool() calls from TypeScript content."""
    tools = []
    
    # Pattern: server.registerTool('tool_name', { description: '...' }, ...)
    pattern = r'server\.registerTool\s*\(\s*[\'"]([^\'",]+)[\'"].*?description:\s*[\'"]([^\'",]*?)[\'"]'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        tool_name = match[0].strip()
        tool_desc = match[1].strip()
        
        tools.append({
            "name": tool_name,
            "description": tool_desc[:100] + "..." if len(tool_desc) > 100 else tool_desc,
            "category": "General"
        })
    
    return tools


def _parse_register_resource_calls(content: str) -> List[Dict[str, Any]]:
    """Parse server.registerResource() calls from TypeScript content."""
    resources = []
    
    # Pattern: server.registerResource('resource_id', 'uri://...', { name: '...', description: '...' }, ...)
    pattern = r'server\.registerResource\s*\(\s*[\'"]([^\'",]+)[\'"],\s*[\'"]([^\'",]+)[\'"].*?name:\s*[\'"]([^\'",]*?)[\'"].*?description:\s*[\'"]([^\'",]*?)[\'"]'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        resource_id = match[0].strip()
        resource_uri = match[1].strip()
        resource_name = match[2].strip()
        resource_desc = match[3].strip()
        
        resources.append({
            "uri": resource_uri,
            "name": resource_name or resource_id,
            "description": resource_desc[:100] + "..." if len(resource_desc) > 100 else resource_desc,
            "category": "General"
        })
    
    return resources


def _extract_env_vars_from_readme(content: str) -> List[Dict[str, Any]]:
    """Extract environment variables documentation from README content."""
    env_vars = []
    
    # Look for export statements
    export_pattern = r'export\s+([A-Z_][A-Z0-9_]*)\s*=\s*[\'"]([^\'"]*)[\'"]'
    exports = re.findall(export_pattern, content)
    
    for export_match in exports:
        var_name = export_match[0]
        example_value = export_match[1]
        
        env_vars.append({
            "name": var_name,
            "description": f"Configuration for {var_name.lower().replace('_', ' ')}",
            "example": example_value if not any(secret in example_value.lower() 
                                              for secret in ['password', 'secret', 'token', 'key']) 
                      else "[REDACTED]",
            "required": True,
            "category": _categorize_env_var(var_name)
        })
    
    return env_vars


def _categorize_env_var(var_name: str) -> str:
    """Categorize environment variable by name."""
    var_lower = var_name.lower()
    
    if any(auth in var_lower for auth in ['password', 'secret', 'token', 'key', 'client_id']):
        return "Authentication"
    elif any(db in var_lower for db in ['database', 'db_', 'postgres', 'mysql']):
        return "Database"
    elif any(url in var_lower for url in ['url', 'host', 'endpoint', 'server']):
        return "Connection"
    elif any(config in var_lower for config in ['realm', 'project', 'org', 'environment']):
        return "Configuration"
    else:
        return "General"


def render_servers_dashboard():
    """Render the MCP servers status dashboard."""
    st.header("🛠️ Generated MCP Servers")
    
    servers = discover_mcp_servers()
    
    if not servers:
        st.info("No MCP servers found. Generate your first server using the agents!")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Servers", len(servers))
    
    with col2:
        implemented_count = len([s for s in servers if s["status"] == "implemented"])
        st.metric("Implemented", implemented_count)
    
    with col3:
        tested_count = len([s for s in servers if s.get("has_tests", False)])
        st.metric("With Tests", tested_count)
    
    with col4:
        documented_count = len([s for s in servers if s.get("has_docs", False)])
        st.metric("Documented", documented_count)
    
    # Server details
    st.subheader("Server Details")
    
    for server in servers:
        with st.expander(f"📦 {server['name']} - {server['status'].title()}", expanded=False):
            
            # Basic info section
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Description:** {server['description']}")
                st.markdown(f"**Path:** `{server['path']}`")
                
                # Show tools if available
                if server.get("tools"):
                    st.markdown("**Tools:**")
                    for tool in server["tools"][:5]:  # Show first 5 tools
                        st.write(f"• `{tool['name']}` - {tool['description']}")
                    if len(server["tools"]) > 5:
                        st.write(f"... and {len(server['tools']) - 5} more tools")
                
                # Show resources if available
                if server.get("resources"):
                    st.markdown("**Resources:**")
                    for resource in server["resources"][:3]:  # Show first 3 resources
                        st.write(f"• `{resource['name']}` - {resource['description']}")
                    if len(server["resources"]) > 3:
                        st.write(f"... and {len(server['resources']) - 3} more resources")
            
            with col2:
                st.markdown("**Status**")
                status_icon = "✅" if server["status"] == "implemented" else "⚠️"
                st.write(f"{status_icon} {server['status'].title()}")
                
                st.write(f"**Tests:** {'✅' if server['has_tests'] else '❌'}")
                st.write(f"**Docs:** {'✅' if server['has_docs'] else '❌'}")
                
                if server.get("tools"):
                    st.write(f"**Tools:** {len(server['tools'])}")
                if server.get("resources"):
                    st.write(f"**Resources:** {len(server['resources'])}")
            
            # Environment variables section
            if server.get("env_vars"):
                st.markdown("**Environment Variables:**")
                env_data = []
                for env_var in server["env_vars"]:
                    env_data.append({
                        "Variable": env_var["name"],
                        "Category": env_var["category"],
                        "Required": "✅" if env_var["required"] else "❌",
                        "Example": env_var["example"]
                    })
                st.dataframe(env_data, use_container_width=True)
