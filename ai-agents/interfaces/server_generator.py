"""Streamlit interface for MCP server generation."""

import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from streamlit.runtime.caching import cache_data
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import AI agents and workflows
try:
    # from workflows.mcp_development import MCPDevelopmentWorkflows
    from agents.orchestrator.orchestrator import OrchestratorAgent
    from core.config import get_config_manager, get_config
    from interfaces.config_panel import render_config_panel
    print("✅ Successfully imported all modules")
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    # If running directly, mock these for now
    # MCPDevelopmentWorkflows = None
    OrchestratorAgent = None
    IMPORTS_AVAILABLE = False
    
    def get_config_manager():
        return None
    
    def get_config():
        return {}
    
    def render_config_panel():
        st.sidebar.write("Config panel not available")
        st.sidebar.error(f"Import failed: {e}")
        st.sidebar.write("Debug info:")
        st.sidebar.code(f"Error: {e}")
        return None


@st.cache_data
def discover_available_agents() -> List[Dict[str, Any]]:
    """Discover all available AI agents in the system.
    
    Returns:
        List of agent information dictionaries
    """
    agents = []
    agents_dir = Path(__file__).parent.parent / "agents"
    
    if not agents_dir.exists():
        return agents
    
    for agent_dir in agents_dir.iterdir():
        if agent_dir.is_dir() and not agent_dir.name.startswith('__'):
            agent_info = {
                "name": agent_dir.name,
                "path": str(agent_dir),
                "status": "available",
                "description": "No description available"
            }
            
            # Try to read agent description from __init__.py
            init_file = agent_dir / "__init__.py"
            if init_file.exists():
                try:
                    content = init_file.read_text()
                    # Extract docstring if available
                    if '"""' in content:
                        start = content.find('"""') + 3
                        end = content.find('"""', start)
                        if end > start:
                            agent_info["description"] = content[start:end].strip()
                except Exception:
                    pass
            
            # Check if agent has proper implementation
            if (agent_dir / "__init__.py").exists():
                agent_info["implemented"] = True
            else:
                agent_info["implemented"] = False
                agent_info["status"] = "skeleton"
            
            agents.append(agent_info)
    
    return agents


@st.cache_data
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
                server_info = {
                    "name": server_dir.name,
                    "path": str(server_dir),
                    "status": "unknown",
                    "description": "No description available",
                    "version": "unknown",
                    "type": "mcp-server",
                    "tools": [],
                    "resources": [],
                    "environment_variables": [],
                    "dependencies": [],
                    "keywords": []
                }
                
                # Read package.json for metadata
                package_json = server_dir / "package.json"
                if package_json.exists():
                    try:
                        package_data = json.loads(package_json.read_text())
                        server_info["description"] = package_data.get("description", server_info["description"])
                        server_info["version"] = package_data.get("version", server_info["version"])
                        server_info["status"] = "configured"
                        server_info["keywords"] = package_data.get("keywords", [])
                        
                        # Extract dependencies
                        deps = package_data.get("dependencies", {})
                        dev_deps = package_data.get("devDependencies", {})
                        server_info["dependencies"] = {
                            "runtime": list(deps.keys()),
                            "development": list(dev_deps.keys()),
                            "total_count": len(deps) + len(dev_deps)
                        }
                    except Exception:
                        pass
                
                # Check for TypeScript source
                src_dir = server_dir / "src"
                if src_dir.exists() and (src_dir / "index.ts").exists():
                    server_info["status"] = "implemented"
                    
                    # Extract tools and resources from TypeScript files
                    try:
                        server_info.update(_extract_server_capabilities(server_dir))
                    except Exception as e:
                        print(f"Error extracting capabilities for {server_dir.name}: {e}")
                
                # Extract environment variables from README
                readme_file = server_dir / "README.md"
                if readme_file.exists():
                    server_info["has_docs"] = True
                    try:
                        readme_content = readme_file.read_text(encoding='utf-8', errors='ignore')
                        server_info["environment_variables"] = _extract_env_vars_from_readme(readme_content)
                    except Exception:
                        pass
                else:
                    server_info["has_docs"] = False
                
                # Check for tests
                tests_dir = server_dir / "tests"
                if tests_dir.exists():
                    server_info["has_tests"] = True
                else:
                    server_info["has_tests"] = False
                
                servers.append(server_info)
    
    # Also check AI agents output directory if configured
    try:
        config = get_config()
        if hasattr(config, 'generation') and hasattr(config.generation, 'output_directory'):
            output_dir = Path(config.generation.output_directory)
            if output_dir.exists():
                for server_dir in output_dir.iterdir():
                    if server_dir.is_dir() and server_dir.name not in [s["name"] for s in servers]:
                        server_info = {
                            "name": server_dir.name,
                            "path": str(server_dir),
                            "status": "generated",
                            "description": "AI-generated MCP server",
                            "version": "1.0.0",
                            "type": "ai-generated",
                            "tools": [],
                            "resources": [],
                            "environment_variables": [],
                            "dependencies": [],
                            "keywords": []
                        }
                        servers.append(server_info)
    except Exception:
        pass
    
    return servers


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
    
    # Look for tools definitions - handle both patterns
    # Pattern 1: Service-grouped (auth-mcp-server style) - look for *tools.ts files
    tools_files = list(src_dir.rglob("*tools.ts"))
    for tools_file in tools_files:
        try:
            content = tools_file.read_text(encoding='utf-8', errors='ignore')
            tools = _parse_typescript_tools(content)
            capabilities["tools"].extend(tools)
        except Exception:
            continue
    
    # Pattern 2: Function-grouped (db-mcp-server style) - look in tools/ directory
    tools_dir = src_dir / "tools"
    if tools_dir.exists():
        for tools_file in tools_dir.glob("*.ts"):
            if tools_file.name == "index.ts":
                continue  # Skip index files
            try:
                content = tools_file.read_text(encoding='utf-8', errors='ignore')
                tools = _parse_register_tool_calls(content)
                # Use filename as category for function-grouped structure
                category = tools_file.stem.title()
                for tool in tools:
                    tool["category"] = category
                capabilities["tools"].extend(tools)
            except Exception:
                continue
    
    # Look for resources definitions - handle both patterns  
    # Pattern 1: Service-grouped - look for *resources.ts files
    resources_files = list(src_dir.rglob("*resources.ts"))
    for resources_file in resources_files:
        try:
            content = resources_file.read_text(encoding='utf-8', errors='ignore')
            resources = _parse_typescript_resources(content)
            capabilities["resources"].extend(resources)
        except Exception:
            continue
    
    # Pattern 2: Function-grouped - look in resources/ directory
    resources_dir = src_dir / "resources"
    if resources_dir.exists():
        for resources_file in resources_dir.glob("*.ts"):
            if resources_file.name == "index.ts":
                continue  # Skip index files
            try:
                content = resources_file.read_text(encoding='utf-8', errors='ignore')
                resources = _parse_register_resource_calls(content)
                # Use filename as category for function-grouped structure
                category = resources_file.stem.title()
                for resource in resources:
                    resource["category"] = category
                capabilities["resources"].extend(resources)
            except Exception:
                continue
    
    # Detect integrations from directory structure and file names
    integrations = []
    for subdir in src_dir.iterdir():
        if subdir.is_dir() and subdir.name not in ['__pycache__', 'node_modules']:
            integration_name = subdir.name
            if integration_name not in ['types', 'utils', 'lib', 'common', 'tools', 'resources', 'prompts']:
                integrations.append({
                    "name": integration_name.title(),
                    "type": "service_integration",
                    "files": len(list(subdir.glob("*.ts")))
                })
    
    # For function-grouped structure, detect integrations from tool/resource file names
    if tools_dir and tools_dir.exists():
        for file in tools_dir.glob("*.ts"):
            if file.name != "index.ts":
                integrations.append({
                    "name": file.stem.title(),
                    "type": "database_integration",
                    "files": 1
                })
    
    capabilities["integrations"] = integrations
    
    return capabilities


def _parse_typescript_tools(content: str) -> List[Dict[str, Any]]:
    """Parse TypeScript tools definitions from file content.
    
    Args:
        content: TypeScript file content
        
    Returns:
        List of tool definitions
    """
    tools = []
    
    # Enhanced regex-based parsing for tool definitions
    
    # Look for exported tool arrays - handle multi-line array definitions
    # Match arrays that end with ]; (semicolon)
    tool_array_pattern = r'export\s+const\s+(\w*[Tt]ools?)\s*:\s*Tool\[\]\s*=\s*\[(.*?)\];'
    matches = re.findall(tool_array_pattern, content, re.DOTALL)
    
    for match in matches:
        array_name = match[0]
        array_content = match[1]
        
        # Extract individual tool objects by finding name and description pairs
        # More lenient pattern to handle various formatting
        tool_object_pattern = r'\{\s*name:\s*[\'"]([^\'",]+)[\'"],.*?description:\s*[\'"]([^\'",]*?)[\'"]\s*,?'
        tool_matches = re.findall(tool_object_pattern, array_content, re.DOTALL)
        
        for tool_match in tool_matches:
            tool_name = tool_match[0].strip()
            tool_desc = tool_match[1].strip()
            
            tools.append({
                "name": tool_name,
                "description": tool_desc[:100] + "..." if len(tool_desc) > 100 else tool_desc,
                "category": array_name.replace("Tools", "").replace("tools", "").title() or "General"
            })
    
    # Also look for individual tool definitions (fallback)
    if not tools:
        # Alternative pattern for single tool exports or different array formats
        single_tool_pattern = r'name:\s*[\'"]([^\'",]+)[\'"].*?description:\s*[\'"]([^\'",]*?)[\'"]\s*,?'
        single_matches = re.findall(single_tool_pattern, content, re.DOTALL)
        
        for tool_match in single_matches:
            tool_name = tool_match[0].strip()
            tool_desc = tool_match[1].strip()
            
            tools.append({
                "name": tool_name,
                "description": tool_desc[:100] + "..." if len(tool_desc) > 100 else tool_desc,
                "category": "General"
            })
    
    return tools


def _parse_typescript_resources(content: str) -> List[Dict[str, Any]]:
    """Parse TypeScript resources definitions from file content.
    
    Args:
        content: TypeScript file content
        
    Returns:
        List of resource definitions
    """
    resources = []
    
    # Enhanced regex-based parsing for resource definitions
    
    # Look for exported resource arrays - handle multi-line array definitions
    # Match arrays that end with ]; (semicolon)
    resource_array_pattern = r'export\s+const\s+(\w*[Rr]esources?)\s*:\s*Resource\[\]\s*=\s*\[(.*?)\];'
    matches = re.findall(resource_array_pattern, content, re.DOTALL)
    
    for match in matches:
        array_name = match[0]
        array_content = match[1]
        
        # Extract individual resource objects by finding uri, name, and description
        # More lenient pattern to handle various formatting
        resource_object_pattern = r'\{\s*uri:\s*[\'"]([^\'",]+)[\'"],.*?name:\s*[\'"]([^\'",]*?)[\'"],.*?description:\s*[\'"]([^\'",]*?)[\'"]\s*,?'
        resource_matches = re.findall(resource_object_pattern, array_content, re.DOTALL)
        
        for resource_match in resource_matches:
            uri = resource_match[0].strip()
            name = resource_match[1].strip()
            description = resource_match[2].strip()
            
            resources.append({
                "uri": uri,
                "name": name,
                "description": description[:100] + "..." if len(description) > 100 else description,
                "category": array_name.replace("Resources", "").replace("resources", "").title() or "General"
            })
    
    # Also look for individual resource definitions (fallback)
    if not resources:
        single_resource_pattern = r'uri:\s*[\'"]([^\'",]+)[\'"].*?name:\s*[\'"]([^\'",]*?)[\'"].*?description:\s*[\'"]([^\'",]*?)[\'"]\s*,?'
        single_matches = re.findall(single_resource_pattern, content, re.DOTALL)
        
        for resource_match in single_matches:
            uri = resource_match[0].strip()
            name = resource_match[1].strip()
            description = resource_match[2].strip()
            
            resources.append({
                "uri": uri,
                "name": name,
                "description": description[:100] + "..." if len(description) > 100 else description,
                "category": "General"
            })
    
    return resources


def _parse_register_tool_calls(content: str) -> List[Dict[str, Any]]:
    """Parse server.registerTool() calls from TypeScript content.
    
    Args:
        content: TypeScript file content
        
    Returns:
        List of tool definitions
    """
    tools = []
    
    # Look for server.registerTool calls
    # Pattern: server.registerTool('tool_name', { description: '...' }, async (...) => {...})
    register_tool_pattern = r'server\.registerTool\s*\(\s*[\'"]([^\'",]+)[\'"].*?description:\s*[\'"]([^\'",]*?)[\'"].*?\)'
    matches = re.findall(register_tool_pattern, content, re.DOTALL)
    
    for match in matches:
        tool_name = match[0].strip()
        tool_desc = match[1].strip()
        
        tools.append({
            "name": tool_name,
            "description": tool_desc[:100] + "..." if len(tool_desc) > 100 else tool_desc,
            "category": "General"  # Will be set by caller
        })
    
    return tools


def _parse_register_resource_calls(content: str) -> List[Dict[str, Any]]:
    """Parse server.registerResource() calls from TypeScript content.
    
    Args:
        content: TypeScript file content
        
    Returns:
        List of resource definitions
    """
    resources = []
    
    # Look for server.registerResource calls
    # Pattern: server.registerResource('resource_id', 'uri://...', { name: '...', description: '...' }, async (...) => {...})
    register_resource_pattern = r'server\.registerResource\s*\(\s*[\'"]([^\'",]+)[\'"],\s*[\'"]([^\'",]+)[\'"].*?name:\s*[\'"]([^\'",]*?)[\'"].*?description:\s*[\'"]([^\'",]*?)[\'"].*?\)'
    matches = re.findall(register_resource_pattern, content, re.DOTALL)
    
    for match in matches:
        resource_id = match[0].strip()
        resource_uri = match[1].strip()
        resource_name = match[2].strip()
        resource_desc = match[3].strip()
        
        resources.append({
            "uri": resource_uri,
            "name": resource_name or resource_id,
            "description": resource_desc[:100] + "..." if len(resource_desc) > 100 else resource_desc,
            "category": "General"  # Will be set by caller
        })
    
    return resources


def _extract_env_vars_from_readme(content: str) -> List[Dict[str, Any]]:
    """Extract environment variables documentation from README content.
    
    Args:
        content: README markdown content
        
    Returns:
        List of environment variable definitions
    """
    env_vars = []
    
    # Look for export statements in code blocks
    export_pattern = r'export\s+([A-Z_][A-Z0-9_]*)\s*=\s*[\'"]([^\'"]*)[\'"]'
    exports = re.findall(export_pattern, content)
    
    # Also look for environment variable documentation patterns
    # Pattern for variables mentioned in configuration sections
    config_var_pattern = r'`?([A-Z_][A-Z0-9_]*)`?\s*[:\-=]\s*([^\n\r]+)'
    config_vars = re.findall(config_var_pattern, content)
    
    # Combine both sources
    all_vars = {}
    
    # Add exports first
    for export_match in exports:
        var_name = export_match[0]
        example_value = export_match[1]
        all_vars[var_name] = {
            "name": var_name,
            "example": example_value if not any(secret in example_value.lower() 
                                              for secret in ['password', 'secret', 'token', 'key']) 
                      else "[REDACTED]",
            "description": "",
            "source": "export"
        }
    
    # Add config variables
    for config_match in config_vars:
        var_name = config_match[0]
        description = config_match[1].strip()
        
        # Skip if it doesn't look like an env var
        if not var_name.isupper() or len(var_name) < 3:
            continue
            
        if var_name not in all_vars:
            all_vars[var_name] = {
                "name": var_name,
                "example": "",
                "description": description,
                "source": "config"
            }
        else:
            # Enhance existing entry with description
            all_vars[var_name]["description"] = description
    
    # Convert to list and determine if required
    for var_name, var_info in all_vars.items():
        # Try to find description in surrounding text if not already found
        if not var_info["description"]:
            var_context_pattern = rf'#{1,4}[^#]*{re.escape(var_name)}[^#]*?([^\n\r]+)'
            context_match = re.search(var_context_pattern, content, re.DOTALL)
            if context_match:
                var_info["description"] = context_match.group(1).strip()[:100]
        
        # Default description if still empty
        if not var_info["description"]:
            var_info["description"] = f"Configuration for {var_name.lower().replace('_', ' ')}"
        
        # Determine if required based on common patterns and context
        var_context = content.lower()
        is_required = True  # Default to required
        
        # Check for optional indicators
        if any(opt in var_context for opt in [f"{var_name.lower()} is optional", "optional:", "# optional"]):
            is_required = False
        elif "defaults to" in var_info["description"].lower():
            is_required = False
            
        env_vars.append({
            "name": var_name,
            "description": var_info["description"],
            "example": var_info["example"],
            "required": is_required,
            "category": _categorize_env_var(var_name)
        })
    
    return env_vars


def _categorize_env_var(var_name: str) -> str:
    """Categorize environment variable by name.
    
    Args:
        var_name: Environment variable name
        
    Returns:
        Category string
    """
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


def render_agents_dashboard():
    """Render the agents status dashboard."""
    st.header("🤖 Available AI Agents")
    
    agents = discover_available_agents()
    
    if not agents:
        st.warning("No AI agents found in the system.")
        return
    
    # Create columns for agent cards
    cols = st.columns(min(len(agents), 3))
    
    for i, agent in enumerate(agents):
        with cols[i % 3]:
            # Status badge
            if agent["implemented"]:
                status_color = "🟢"
                status_text = "Ready"
            else:
                status_color = "🟡"
                status_text = "Skeleton"
            
            st.markdown(f"""
            <div class="status-card">
                <h4>{status_color} {agent['name'].replace('_', ' ').title()}</h4>
                <p><strong>Status:</strong> {status_text}</p>
                <p>{agent['description'][:100]}{'...' if len(agent['description']) > 100 else ''}</p>
                <p><small><strong>Path:</strong> {agent['path']}</small></p>
            </div>
            """, unsafe_allow_html=True)
    
    # Agent capabilities matrix
    st.subheader("Agent Capabilities Matrix")
    
    capabilities_data = []
    for agent in agents:
        capabilities_data.append({
            "Agent": agent["name"].replace('_', ' ').title(),
            "Status": "✅" if agent["implemented"] else "⚠️",
            "Implementation": "Complete" if agent["implemented"] else "Skeleton",
            "Role": agent.get("role", "Unknown")
        })
    
    st.dataframe(capabilities_data, use_container_width=True)


def render_servers_dashboard():
    """Render the MCP servers status dashboard."""
    st.header("🛠️ Generated MCP Servers")
    
    servers = discover_mcp_servers()
    
    if not servers:
        st.info("No MCP servers found. Generate your first server below!")
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
                st.write(f"**Description:** {server['description']}")
                st.write(f"**Version:** {server['version']}")
                st.write(f"**Type:** {server['type']}")
                st.write(f"**Path:** `{server['path']}`")
                
                # Keywords/Tags
                if server.get("keywords"):
                    keywords_str = ", ".join([f"`{kw}`" for kw in server["keywords"][:5]])
                    if len(server["keywords"]) > 5:
                        keywords_str += f" +{len(server['keywords']) - 5} more"
                    st.write(f"**Keywords:** {keywords_str}")
            
            with col2:
                # Status indicators
                status_indicators = []
                
                if server["status"] == "implemented":
                    status_indicators.append("✅ Implemented")
                elif server["status"] == "configured":
                    status_indicators.append("⚙️ Configured")
                elif server["status"] == "generated":
                    status_indicators.append("🤖 AI Generated")
                else:
                    status_indicators.append("❓ Unknown")
                
                if server.get("has_tests", False):
                    status_indicators.append("🧪 Has Tests")
                else:
                    status_indicators.append("⚠️ No Tests")
                
                if server.get("has_docs", False):
                    status_indicators.append("📚 Documented")
                else:
                    status_indicators.append("📝 Needs Docs")
                
                for indicator in status_indicators:
                    st.write(indicator)
            
            # Detailed capabilities section
            if server.get("tools") or server.get("resources") or server.get("integrations"):
                st.divider()
                
                # Create tabs for different aspects
                detail_tab1, detail_tab2, detail_tab3, detail_tab4 = st.tabs([
                    f"🔧 Tools ({len(server.get('tools', []))})",
                    f"📊 Resources ({len(server.get('resources', []))})", 
                    f"🔗 Integrations ({len(server.get('integrations', []))})",
                    f"⚙️ Environment ({len(server.get('environment_variables', []))})"
                ])
                
                with detail_tab1:
                    tools = server.get("tools", [])
                    if tools:
                        # Group tools by category
                        tools_by_category = {}
                        for tool in tools:
                            category = tool.get("category", "General")
                            if category not in tools_by_category:
                                tools_by_category[category] = []
                            tools_by_category[category].append(tool)
                        
                        for category, category_tools in tools_by_category.items():
                            st.write(f"**{category} Tools:**")
                            tools_data = []
                            for tool in category_tools:
                                tools_data.append({
                                    "Name": tool["name"],
                                    "Description": tool["description"]
                                })
                            st.dataframe(tools_data, use_container_width=True, hide_index=True)
                    else:
                        st.info("No tools detected in this server.")
                
                with detail_tab2:
                    resources = server.get("resources", [])
                    if resources:
                        # Group resources by category
                        resources_by_category = {}
                        for resource in resources:
                            category = resource.get("category", "General")
                            if category not in resources_by_category:
                                resources_by_category[category] = []
                            resources_by_category[category].append(resource)
                        
                        for category, category_resources in resources_by_category.items():
                            st.write(f"**{category} Resources:**")
                            resources_data = []
                            for resource in category_resources:
                                resources_data.append({
                                    "URI": resource["uri"],
                                    "Name": resource["name"],
                                    "Description": resource["description"]
                                })
                            st.dataframe(resources_data, use_container_width=True, hide_index=True)
                    else:
                        st.info("No resources detected in this server.")
                
                with detail_tab3:
                    integrations = server.get("integrations", [])
                    if integrations:
                        integrations_data = []
                        for integration in integrations:
                            integrations_data.append({
                                "Service": integration["name"],
                                "Type": integration["type"].replace("_", " ").title(),
                                "Files": integration["files"]
                            })
                        st.dataframe(integrations_data, use_container_width=True, hide_index=True)
                    else:
                        st.info("No service integrations detected.")
                
                with detail_tab4:
                    env_vars = server.get("environment_variables", [])
                    if env_vars:
                        # Group by category
                        env_by_category = {}
                        for env_var in env_vars:
                            category = env_var.get("category", "General")
                            if category not in env_by_category:
                                env_by_category[category] = []
                            env_by_category[category].append(env_var)
                        
                        for category, category_vars in env_by_category.items():
                            st.write(f"**{category} Variables:**")
                            env_data = []
                            for env_var in category_vars:
                                env_data.append({
                                    "Variable": env_var["name"],
                                    "Required": "✅" if env_var.get("required", True) else "⚠️",
                                    "Example": env_var.get("example", "N/A"),
                                    "Description": env_var.get("description", "No description")
                                })
                            st.dataframe(env_data, use_container_width=True, hide_index=True)
                    else:
                        st.info("No environment variables documented.")
            
            # Dependencies section
            if server.get("dependencies"):
                st.divider()
                deps = server["dependencies"]
                
                dep_col1, dep_col2, dep_col3 = st.columns(3)
                
                with dep_col1:
                    st.metric("Runtime Dependencies", len(deps.get("runtime", [])))
                    
                with dep_col2:
                    st.metric("Dev Dependencies", len(deps.get("development", [])))
                    
                with dep_col3:
                    st.metric("Total Dependencies", deps.get("total_count", 0))
                
                # Show key dependencies
                runtime_deps = deps.get("runtime", [])
                if runtime_deps:
                    mcp_deps = [dep for dep in runtime_deps if "mcp" in dep.lower()]
                    auth_deps = [dep for dep in runtime_deps if any(auth in dep.lower() for auth in ["auth", "oauth", "jwt", "passport"])]
                    
                    if mcp_deps:
                        st.write(f"**MCP Dependencies:** {', '.join([f'`{dep}`' for dep in mcp_deps])}")
                    if auth_deps:
                        st.write(f"**Auth Dependencies:** {', '.join([f'`{dep}`' for dep in auth_deps])}")
            
            # Action buttons
            st.divider()
            button_col1, button_col2, button_col3, button_col4 = st.columns(4)
            
            with button_col1:
                if st.button(f"📋 View Source", key=f"view_{server['name']}"):
                    st.info(f"Would open source code for {server['name']}")
            
            with button_col2:
                if st.button(f"🧪 Run Tests", key=f"test_{server['name']}"):
                    st.info(f"Would run tests for {server['name']}")
            
            with button_col3:
                if st.button(f"🔍 Validate", key=f"validate_{server['name']}"):
                    st.info(f"Would validate MCP compliance for {server['name']}")
            
            with button_col4:
                if st.button(f"🚀 Deploy", key=f"deploy_{server['name']}"):
                    st.info(f"Would deploy {server['name']}")


def create_progress_chart(progress_data: Dict[str, int]) -> go.Figure:
    """Create a progress chart showing step completion.
    
    Args:
        progress_data: Dictionary mapping step names to completion percentages
        
    Returns:
        Plotly figure
    """
    steps = list(progress_data.keys())
    progress = list(progress_data.values())
    
    fig = go.Figure(data=[
        go.Bar(
            x=steps,
            y=progress,
            marker_color=['#28a745' if p == 100 else '#ffc107' if p > 0 else '#6c757d' for p in progress],
            text=[f"{p}%" for p in progress],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Step Progress",
        xaxis_title="Workflow Steps",
        yaxis_title="Completion (%)",
        yaxis=dict(range=[0, 100]),
        height=300,
        showlegend=False
    )
    
    return fig


# Configure page
st.set_page_config(
    page_title="MC-PEA AI Agent Interface",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}

.status-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
}

.success-card {
    background-color: #d4edda;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #28a745;
}

.error-card {
    background-color: #f8d7da;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #dc3545;
}
</style>
""", unsafe_allow_html=True)


def create_workflow_diagram(steps: List[Dict[str, Any]]) -> go.Figure:
    """Create a workflow visualization using Plotly.
    
    Args:
        steps: List of workflow steps
        
    Returns:
        Plotly figure
    """
    # Create nodes and edges for the workflow
    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    
    # Status colors
    status_colors = {
        "pending": "#ffc107",
        "running": "#007bff", 
        "completed": "#28a745",
        "failed": "#dc3545",
    }
    
    for i, step in enumerate(steps):
        node_x.append(i)
        node_y.append(0)
        node_text.append(step["name"])
        node_colors.append(status_colors.get(step.get("status", "pending"), "#6c757d"))
    
    # Create the figure
    fig = go.Figure()
    
    # Add edges (connections between steps)
    for i in range(len(steps) - 1):
        fig.add_trace(go.Scatter(
            x=[i, i + 1],
            y=[0, 0],
            mode="lines",
            line=dict(color="#6c757d", width=2),
            showlegend=False,
            hoverinfo="skip",
        ))
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(
            size=40,
            color=node_colors,
            line=dict(width=2, color="white"),
        ),
        text=node_text,
        textposition="middle center",
        textfont=dict(color="white", size=10),
        showlegend=False,
        hovertemplate="<b>%{text}</b><extra></extra>",
    ))
    
    fig.update_layout(
        title="MCP Server Generation Workflow",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="rgba(0,0,0,0)",
        height=200,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    
    return fig


def main():
    """Main Streamlit application."""
    import os
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get configuration and apply UI settings
    config = get_config()
    if config and hasattr(config, 'ui'):
        # Note: set_page_config must be called before other Streamlit commands
        # So we can only apply some settings after initial page setup
        pass
    
    # Render configuration panel in sidebar first
    if IMPORTS_AVAILABLE:
        render_config_panel()
    else:
        with st.sidebar:
            st.error("Config panel unavailable")
            st.write("Import error occurred. Please check the console for details.")
            st.write("Current directory structure:")
            try:
                import os
                current_dir = os.getcwd()
                st.code(f"Current working directory: {current_dir}")
                if os.path.exists("core"):
                    st.success("✅ core/ directory found")
                else:
                    st.error("❌ core/ directory not found")
                if os.path.exists("interfaces"):
                    st.success("✅ interfaces/ directory found")  
                else:
                    st.error("❌ interfaces/ directory not found")
                if os.path.exists("workflows"):
                    st.success("✅ workflows/ directory found")
                else:
                    st.error("❌ workflows/ directory not found")
            except Exception as e:
                st.error(f"Error checking directories: {e}")
    
    # Main header
    st.markdown('<h1 class="main-header">🤖 MC-PEA AI Agent Interface</h1>', unsafe_allow_html=True)
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["🏠 Dashboard", "🤖 Agents", "🛠️ Servers"])
    
    with tab1:
        # Configuration status indicator
        if config:
            with st.expander("📊 Current Configuration Status", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Model", config.anthropic.model)
                    st.metric("Temperature", f"{config.anthropic.temperature:.1f}")
                
                with col2:
                    st.metric("Max Iterations", config.agent.max_iterations)
                    st.metric("Parallel Execution", "✅" if config.workflow.parallel_execution else "❌")
                
                with col3:
                    st.metric("Auto Validate", "✅" if config.validation.auto_validate else "❌")
                    st.metric("Create Tests", "✅" if config.generation.create_tests else "❌")
            
            # Hot reload status
            if config.ui.enable_hot_reload:
                st.info("🔥 Hot reload is enabled - configuration changes will be applied immediately!")
        
        # Quick stats overview
        st.subheader("📈 System Overview")
        
        agents = discover_available_agents()
        servers = discover_mcp_servers()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Available Agents", len(agents), 
                     delta=f"{len([a for a in agents if a['implemented']])} implemented")
        
        with col2:
            st.metric("MCP Servers", len(servers),
                     delta=f"{len([s for s in servers if s['status'] == 'implemented'])} ready")
        
        with col3:
            tested_servers = len([s for s in servers if s.get("has_tests", False)])
            st.metric("Tested Servers", tested_servers)
        
        with col4:
            documented_servers = len([s for s in servers if s.get("has_docs", False)])
            st.metric("Documented", documented_servers)
        
        # Recent activity placeholder
        st.subheader("📋 Recent Activity")
        st.info("Activity tracking will be implemented in a future version.")
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        quick_col1, quick_col2, quick_col3 = st.columns(3)
        
        with quick_col1:
            if st.button("🚀 Generate New Server", type="primary"):
                st.balloons()
                st.success("Switched to server generation tab!")
        
        with quick_col2:
            if st.button("🔍 Validate All Servers"):
                st.info("Server validation would run here")
        
        with quick_col3:
            if st.button("📚 Generate Documentation"):
                st.info("Documentation generation would run here")
    
    with tab2:
        render_agents_dashboard()
    
    with tab3:
        render_servers_dashboard()
        
        # Add server generation section below servers list
        st.divider()
        
        st.header("➕ Generate New MCP Server")
        
        # Check for required API key
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not anthropic_api_key:
            st.warning("⚠️ Anthropic API key not found in environment variables")
            anthropic_api_key = st.text_input(
                "Enter your Anthropic API Key:",
                type="password",
                help="Your API key is required to generate MCP servers. Get one from https://console.anthropic.com/"
            )
            
            if not anthropic_api_key:
                st.stop()
        
        # Server generation form (continue with existing form...)
        # Main content area
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📝 Server Specification")
        
        # Server configuration form
        with st.form("server_spec_form"):
            server_name = st.text_input(
                "Server Name *", 
                value="my-api-server",
                help="Name for your MCP server (lowercase, hyphens allowed)"
            )
            
            server_description = st.text_area(
                "Description *",
                value="A Model Context Protocol server for API integration",
                help="Brief description of what this server does"
            )
            
            api_type = st.selectbox(
                "API Type",
                options=["REST", "GraphQL", "gRPC", "Other"],
                help="Type of API to integrate with"
            )
            
            api_url = st.text_input(
                "API Base URL",
                placeholder="https://api.example.com",
                help="Base URL for the target API (optional)"
            )
            
            auth_type = st.selectbox(
                "Authentication Type",
                options=["none", "api_key", "bearer_token", "oauth2", "basic_auth"],
                help="Authentication method for the API"
            )
            
            # Advanced options (shown based on config)
            with st.expander("🔧 Advanced Options", expanded=config.ui.show_advanced_options if config else False):
                tools_list = st.text_area(
                    "Tools to Generate",
                    value="get_data\npost_data\nupdate_data\ndelete_data",
                    help="One tool per line. Tools will be generated based on API endpoints."
                )
                
                resources_list = st.text_area(
                    "Resources to Expose",
                    value="api_docs\napi_status",
                    help="One resource per line. Resources provide data without side effects."
                )
                
                custom_config = st.text_area(
                    "Custom Configuration (JSON)",
                    value="{}",
                    help="Additional configuration in JSON format"
                )
            
            # Submit button
            submitted = st.form_submit_button(
                "🚀 Generate MCP Server",
                type="primary",
                use_container_width=True
            )
        
        # Generation history (if available)
        if config and hasattr(st.session_state, 'generation_history'):
            with st.expander("📚 Generation History", expanded=False):
                for i, entry in enumerate(st.session_state.generation_history[-5:]):  # Show last 5
                    st.text(f"{i+1}. {entry['name']} - {entry['timestamp']}")
    
    with col2:
        st.header("⚡ Generation Progress")
        
        # Real-time status display
        status_placeholder = st.empty()
        progress_placeholder = st.empty()
        workflow_placeholder = st.empty()
        
        # Initialize session state for tracking
        if 'workflow_status' not in st.session_state:
            st.session_state.workflow_status = "idle"
            st.session_state.current_step = None
            st.session_state.generated_server = None
        
        # Display current status
        with status_placeholder.container():
            if st.session_state.workflow_status == "idle":
                st.info("🏃‍♂️ Ready to generate your MCP server!")
            elif st.session_state.workflow_status == "running":
                st.warning(f"⚙️ Generating... Current step: {st.session_state.current_step}")
            elif st.session_state.workflow_status == "completed":
                st.success("✅ Generation completed successfully!")
            elif st.session_state.workflow_status == "error":
                st.error("❌ Generation failed. Check the logs for details.")
        
        # Process form submission
        if submitted and server_name and server_description:
            try:
                # Validate inputs
                if not server_name.replace('-', '').replace('_', '').isalnum():
                    st.error("Server name must contain only letters, numbers, hyphens, and underscores")
                    st.stop()
                
                # Parse custom config
                try:
                    custom_config_dict = json.loads(custom_config) if custom_config.strip() else {}
                except json.JSONDecodeError:
                    st.error("Invalid JSON in custom configuration")
                    st.stop()
                
                # Create specification
                specification = {
                    "name": server_name,
                    "description": server_description,
                    "api_type": api_type,
                    "api_url": api_url if api_url else None,
                    "auth_type": auth_type,
                    "tools": [tool.strip() for tool in tools_list.split('\n') if tool.strip()],
                    "resources": [res.strip() for res in resources_list.split('\n') if res.strip()],
                    "custom_config": custom_config_dict
                }
                
                # Update workflow status
                st.session_state.workflow_status = "running"
                st.session_state.current_step = "Initializing workflow..."
                
                # Create workflow steps based on current configuration
                steps = [
                    {"name": "Analyze API", "status": "pending"},
                    {"name": "Generate Code", "status": "pending"},
                ]
                
                if config and config.generation.create_tests:
                    steps.append({"name": "Create Tests", "status": "pending"})
                
                if config and config.validation.auto_validate:
                    steps.append({"name": "Validate MCP", "status": "pending"})
                
                if config and config.generation.create_dockerfile:
                    steps.append({"name": "Create Docker", "status": "pending"})
                
                steps.append({"name": "Package Server", "status": "pending"})
                
                # Display workflow diagram
                with workflow_placeholder.container():
                    fig = create_workflow_diagram(steps)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Create progress tracking
                progress_data = {step["name"]: 0 for step in steps}
                
                # Initialize agents (mock for now)
                if OrchestratorAgent:
                    try:
                        orchestrator = OrchestratorAgent()
                        
                        # Execute workflow
                        with st.spinner("Generating MCP server..."):
                            # Simulate step-by-step execution
                            for i, step in enumerate(steps):
                                st.session_state.current_step = step["name"]
                                step["status"] = "running"
                                
                                # Update progress
                                progress_data[step["name"]] = 50
                                
                                # Simulate work
                                time.sleep(1)
                                
                                # Complete step
                                step["status"] = "completed"
                                progress_data[step["name"]] = 100
                                
                                # Update displays
                                with workflow_placeholder.container():
                                    fig = create_workflow_diagram(steps)
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                with progress_placeholder.container():
                                    fig = create_progress_chart(progress_data)
                                    st.plotly_chart(fig, use_container_width=True)
                            

                            # Execute the actual workflow
                            result = orchestrator.execute_workflow(specification)
                            
                            if result.get("success"):
                                st.session_state.workflow_status = "completed"
                                st.session_state.generated_server = result
                                
                                # Add to history
                                if 'generation_history' not in st.session_state:
                                    st.session_state.generation_history = []
                                
                                st.session_state.generation_history.append({
                                    "name": server_name,
                                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "result": result
                                })
                                
                                st.success("🎉 MCP Server generated successfully!")
                                
                                # Display results
                                with st.expander("📋 Generation Results", expanded=True):
                                    st.json(result)
                                
                                # Download button for generated files
                                if result.get("generated_files"):
                                    st.download_button(
                                        label="📥 Download Generated Server",
                                        data=json.dumps(result, indent=2),
                                        file_name=f"{server_name}-mcp-server.json",
                                        mime="application/json"
                                    )
                            
                            else:
                                st.session_state.workflow_status = "error"
                                st.error(f"Generation failed: {result.get('error', 'Unknown error')}")
                    
                    except Exception as e:
                        st.session_state.workflow_status = "error"
                        st.error(f"Error during generation: {str(e)}")
                        st.exception(e)
                
                else:
                    st.warning("🚧 Agent system not available. Running in demo mode.")
                    
                    # Demo mode - simulate successful generation
                    demo_result = {
                        "success": True,
                        "server_name": server_name,
                        "generated_files": [
                            "src/index.ts",
                            "src/tools/api_tools.ts",
                            "package.json",
                            "README.md"
                        ],
                        "execution_time": "Demo mode",
                        "mcp_compliance": True
                    }
                    
                    with progress_placeholder.container():
                        progress_data = {step["name"]: 100 for step in steps}
                        fig = create_progress_chart(progress_data)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    st.session_state.workflow_status = "completed"
                    st.session_state.generated_server = demo_result
                    
                    st.info("Demo generation completed!")
                    with st.expander("📋 Demo Results", expanded=True):
                        st.json(demo_result)
            
            except Exception as e:
                st.session_state.workflow_status = "error"
                st.error(f"Unexpected error: {str(e)}")
                st.exception(e)
    
    # Footer with configuration info
    if config:
        st.markdown("---")
        st.markdown(f"""
        **Configuration:** 
        Last updated: {config.last_updated} | 
        Version: {config.version} | 
        Hot reload: {'🔥 Enabled' if config.ui.enable_hot_reload else '❄️ Disabled'}
        """)
        
        # Auto-refresh for hot reload
        if config.ui.enable_hot_reload and config.ui.auto_refresh_interval > 0:
            time.sleep(config.ui.auto_refresh_interval)
            st.rerun()
if __name__ == "__main__":
    main()
