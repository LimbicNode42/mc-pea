"""
Agent Discovery Module for Streamlit Interface
"""
import sys
from pathlib import Path
from typing import Dict, Any, List
import streamlit as st

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


@st.cache_data(ttl=60)  # Cache for 60 seconds to allow updates
def discover_available_agents() -> List[Dict[str, Any]]:
    """Discover all available AI agents in the system.
    
    Returns:
        List of agent information dictionaries
    """
    agents = []
    agents_dir = Path(__file__).parent.parent / "agents"
    
    if not agents_dir.exists():
        return agents
    
    # Try to import and instantiate agents to get comprehensive info
    sys.path.append(str(agents_dir.parent))
    
    for agent_dir in agents_dir.iterdir():
        if agent_dir.is_dir() and not agent_dir.name.startswith('__'):
            agent_info = {
                "name": agent_dir.name,
                "path": str(agent_dir),
                "status": "available",
                "description": "No description available",
                "implemented": False,
                "mcp_dependencies": [],
                "dependency_count": 0,
                "has_dependencies": False
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
                    
                    # Try to import the agent and get comprehensive info
                    try:
                        if agent_dir.name == "orchestrator":
                            from agents.orchestrator.orchestrator import OrchestratorAgent
                            try:
                                agent_instance = OrchestratorAgent()
                                agent_info.update(agent_instance.get_agent_info())
                            except Exception:
                                # If full initialization fails, get dependencies without initialization
                                agent_info["mcp_dependencies"] = []
                                agent_info["implemented"] = True
                                agent_info["role"] = "Workflow Orchestrator"
                                agent_info["has_dependencies"] = False
                                agent_info["dependency_count"] = 0
                        elif agent_dir.name == "web_scraper":
                            from agents.web_scraper.web_scraper import WebScraperAgent
                            try:
                                agent_instance = WebScraperAgent()
                                agent_info.update(agent_instance.get_agent_info())
                            except Exception:
                                # Get dependencies without full initialization
                                # Use official MCP fetch server dependency
                                fetch_dependency = {
                                    "name": "fetch",
                                    "package": "mcp-server-fetch",
                                    "description": "Official MCP fetch server for web content retrieval",
                                    "repository": "https://github.com/modelcontextprotocol/servers/tree/main/src/fetch",
                                    "required": True,
                                    "status": "official",
                                    "docker_required": False,
                                    "fallback_available": False
                                }
                                agent_info["mcp_dependencies"] = [fetch_dependency]
                                agent_info["implemented"] = True
                                agent_info["role"] = "Web Documentation Scraper"
                                agent_info["has_dependencies"] = True
                                agent_info["dependency_count"] = 1
                        elif agent_dir.name == "api_analyzer":
                            from agents.api_analyzer.api_analysis import APIAnalysisAgent
                            try:
                                agent_instance = APIAnalysisAgent()
                                agent_info.update(agent_instance.get_agent_info())
                            except Exception:
                                # Get dependencies without full initialization
                                agent_info["mcp_dependencies"] = []
                                agent_info["implemented"] = True
                                agent_info["role"] = "API Documentation Analyzer"
                                agent_info["has_dependencies"] = False
                                agent_info["dependency_count"] = 0
                        elif agent_dir.name == "github_agent":
                            from agents.github_agent.github_agent import GitHubAgent
                            try:
                                # GitHub agent requires token, so we'll get dependencies without full initialization
                                github_dependency = {
                                    "name": "github",
                                    "package": "github-mcp-server",
                                    "description": "Official GitHub MCP server for repository operations",
                                    "repository": "https://github.com/github/github-mcp-server",
                                    "required": True,
                                    "status": "official",
                                    "docker_required": False,
                                    "installation": {
                                        "method": "npm",
                                        "command": "npm install -g github-mcp-server"
                                    },
                                    "tools_provided": [
                                        "create_repository", "create_branch", "push_files", 
                                        "create_pull_request", "create_issue", "get_me"
                                    ],
                                    "fallback_available": False
                                }
                                dependencies = [github_dependency]
                                agent_info["mcp_dependencies"] = dependencies
                                agent_info["implemented"] = True
                                agent_info["role"] = "GitHub Operations Agent"
                                agent_info["has_dependencies"] = True
                                agent_info["dependency_count"] = len(dependencies)
                            except Exception:
                                # Fallback info
                                agent_info["mcp_dependencies"] = []
                                agent_info["implemented"] = True
                                agent_info["role"] = "GitHub Operations Agent"
                                agent_info["has_dependencies"] = False
                                agent_info["dependency_count"] = 0
                        # Add other agents as they're implemented
                    except Exception as e:
                        # If import fails, keep basic info
                        agent_info["implemented"] = True if init_file.exists() else False
                        pass
                        
                except Exception:
                    pass
            
            # Check if agent has proper implementation
            if not agent_info["implemented"]:
                agent_info["implemented"] = (agent_dir / "__init__.py").exists()
                if not agent_info["implemented"]:
                    agent_info["status"] = "skeleton"
            
            agents.append(agent_info)
    
    return agents


def render_agents_dashboard():
    """Render the agents status dashboard."""
    st.header("🤖 Available AI Agents")
    
    agents = discover_available_agents()
    
    if not agents:
        st.warning("No AI agents found in the system.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Agents", len(agents))
    
    with col2:
        implemented_count = len([a for a in agents if a["implemented"]])
        st.metric("Implemented", implemented_count)
    
    with col3:
        agents_with_deps = len([a for a in agents if a.get("has_dependencies", False)])
        st.metric("Using MCP Servers", agents_with_deps)
    
    with col4:
        total_deps = sum(a.get("dependency_count", 0) for a in agents)
        st.metric("Total Dependencies", total_deps)
    
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
            
            # MCP dependencies info
            dep_info = ""
            if agent.get("has_dependencies", False):
                deps = agent.get("mcp_dependencies", [])
                dep_info = f"<p><strong>MCP Dependencies:</strong> {len(deps)}</p>"
                for dep in deps[:2]:  # Show first 2 dependencies
                    dep_name = dep.get("name", "Unknown")
                    dep_status = "✅" if dep.get("docker_required", True) == False else "🐳"
                    dep_info += f"<p><small>{dep_status} {dep_name}</small></p>"
                if len(deps) > 2:
                    dep_info += f"<p><small>... and {len(deps) - 2} more</small></p>"
            else:
                dep_info = "<p><strong>MCP Dependencies:</strong> None</p>"
            
            st.markdown(f"""
            <div class="status-card">
                <h4>{status_color} {agent['name'].replace('_', ' ').title()}</h4>
                <p><strong>Status:</strong> {status_text}</p>
                <p>{agent['description'][:80]}{'...' if len(agent['description']) > 80 else ''}</p>
                {dep_info}
                <p><small><strong>Path:</strong> {agent['path']}</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Add configuration button for implemented agents
            if agent["implemented"]:
                if st.button(f"⚙️ Configure", key=f"config_{agent['name']}", type="secondary"):
                    st.session_state[f"show_config_{agent['name']}"] = True
                
                # Show configuration panel if requested
                if st.session_state.get(f"show_config_{agent['name']}", False):
                    from interfaces.agent_config import render_agent_configuration_panel
                    render_agent_configuration_panel(agent)
                    if st.button(f"✅ Done", key=f"done_config_{agent['name']}", type="primary"):
                        st.session_state[f"show_config_{agent['name']}"] = False
                        st.rerun()
    
    # Agent capabilities matrix with MCP dependencies
    st.subheader("Agent Capabilities & Dependencies Matrix")
    
    capabilities_data = []
    for agent in agents:
        deps = agent.get("mcp_dependencies", [])
        dep_names = [dep.get("name", "Unknown") for dep in deps[:3]]  # Show first 3
        dep_display = ", ".join(dep_names)
        if len(deps) > 3:
            dep_display += f" (+{len(deps) - 3} more)"
        
        capabilities_data.append({
            "Agent": agent["name"].replace('_', ' ').title(),
            "Status": "✅" if agent["implemented"] else "⚠️",
            "Implementation": "Complete" if agent["implemented"] else "Skeleton",
            "Role": agent.get("role", "Unknown"),
            "MCP Dependencies": dep_display if dep_display else "None",
            "Docker Required": "Yes" if any(dep.get("docker_required", True) for dep in deps) else "No"
        })
    
    st.dataframe(capabilities_data, use_container_width=True)
    
    # Detailed MCP dependency information
    if any(agent.get("has_dependencies", False) for agent in agents):
        st.subheader("🔌 MCP Server Dependencies Details")
        
        for agent in agents:
            if agent.get("has_dependencies", False):
                with st.expander(f"📋 {agent['name'].replace('_', ' ').title()} Dependencies"):
                    deps = agent.get("mcp_dependencies", [])
                    
                    for dep in deps:
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**{dep.get('name', 'Unknown')}**")
                            st.write(dep.get('description', 'No description'))
                            if dep.get('repository'):
                                st.markdown(f"[Repository]({dep['repository']})")
                        
                        with col2:
                            docker_req = dep.get('docker_required', True)
                            st.write(f"**Docker Required:** {'🐳 Yes' if docker_req else '✅ No'}")
                            st.write(f"**Status:** {dep.get('status', 'Unknown')}")
                        
                        with col3:
                            if 'installation' in dep:
                                install_info = dep['installation']
                                st.write(f"**Install:** `{install_info.get('command', 'N/A')}`")
                            
                            if dep.get('fallback_available'):
                                st.write("🔄 **Fallback Available**")
                        
                        st.divider()
