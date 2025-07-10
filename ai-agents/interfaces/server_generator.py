"""Streamlit interface for MCP server generation."""

import asyncio
import json
import os
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
                    "type": "mcp-server"
                }
                
                # Read package.json for metadata
                package_json = server_dir / "package.json"
                if package_json.exists():
                    try:
                        package_data = json.loads(package_json.read_text())
                        server_info["description"] = package_data.get("description", server_info["description"])
                        server_info["version"] = package_data.get("version", server_info["version"])
                        server_info["status"] = "configured"
                    except Exception:
                        pass
                
                # Check for TypeScript source
                src_dir = server_dir / "src"
                if src_dir.exists() and (src_dir / "index.ts").exists():
                    server_info["status"] = "implemented"
                
                # Check for tests
                tests_dir = server_dir / "tests"
                if tests_dir.exists():
                    server_info["has_tests"] = True
                else:
                    server_info["has_tests"] = False
                
                # Check README
                readme_file = server_dir / "README.md"
                if readme_file.exists():
                    server_info["has_docs"] = True
                else:
                    server_info["has_docs"] = False
                
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
                            "type": "ai-generated"
                        }
                        servers.append(server_info)
    except Exception:
        pass
    
    return servers


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
        with st.expander(f"📦 {server['name']} - {server['status'].title()}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Description:** {server['description']}")
                st.write(f"**Version:** {server['version']}")
                st.write(f"**Type:** {server['type']}")
                st.write(f"**Path:** `{server['path']}`")
            
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
            
            # Action buttons
            button_col1, button_col2, button_col3 = st.columns(3)
            
            with button_col1:
                if st.button(f"View Details", key=f"view_{server['name']}"):
                    st.info(f"Would open details for {server['name']}")
            
            with button_col2:
                if st.button(f"Test Server", key=f"test_{server['name']}"):
                    st.info(f"Would run tests for {server['name']}")
            
            with button_col3:
                if st.button(f"Deploy", key=f"deploy_{server['name']}"):
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
