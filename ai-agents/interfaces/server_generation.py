"""Server generation interface for MCP server creation."""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from agents.orchestrator.orchestrator import OrchestratorAgent
    from agents.github_agent import GitHubAgent, RepositoryManager
    from core.config import get_config
    AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Agent import error: {e}")
    OrchestratorAgent = None
    GitHubAgent = None
    RepositoryManager = None
    AGENTS_AVAILABLE = False
    
    def get_config():
        return None


def create_workflow_diagram(steps: List[Dict[str, Any]]) -> go.Figure:
    """Create a workflow visualization using Plotly.
    
    Args:
        steps: List of workflow steps with name and status
        
    Returns:
        Plotly figure
    """
    if not steps:
        return go.Figure()
    
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
    
    # Calculate positions in a horizontal line
    for i, step in enumerate(steps):
        x = i / max(len(steps) - 1, 1)  # Normalize to 0-1
        y = 0.5  # Middle vertical position
        
        node_x.append(x)
        node_y.append(y)
        node_text.append(step["name"])
        node_colors.append(status_colors.get(step.get("status", "pending"), "#6c757d"))
    
    # Create the figure
    fig = go.Figure()
    
    # Add edges (connections between steps)
    for i in range(len(steps) - 1):
        fig.add_trace(go.Scatter(
            x=[node_x[i], node_x[i + 1]],
            y=[node_y[i], node_y[i + 1]],
            mode="lines",
            line=dict(width=2, color="#dee2e6"),
            showlegend=False,
            hoverinfo="skip"
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
        textposition="top center",
        textfont=dict(color="black", size=10),
        showlegend=False,
        hovertemplate="<b>%{text}</b><extra></extra>",
    ))
    
    fig.update_layout(
        title="MCP Server Generation Workflow",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        height=200
    )
    
    return fig


def create_progress_chart(progress_data: Dict[str, int]) -> go.Figure:
    """Create a progress chart showing step completion.
    
    Args:
        progress_data: Dictionary mapping step names to completion percentages
        
    Returns:
        Plotly figure
    """
    if not progress_data:
        return go.Figure()
    
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


def render_server_generation():
    """Render the MCP server generation interface."""
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
            st.info("💡 Please provide your Anthropic API key to continue with server generation.")
            return
    
    # Check agent availability
    if not AGENTS_AVAILABLE:
        st.error(
            "❌ **Agent system unavailable**\n\n"
            "The AI agents required for server generation are not available. "
            "This could be due to missing dependencies or configuration issues."
        )
        
        with st.expander("🔧 Troubleshooting", expanded=False):
            st.markdown("""
            **Common solutions:**
            1. Ensure all Python dependencies are installed
            2. Check that the agents directory exists and contains the required agents
            3. Verify your configuration files are properly set up
            4. Check the console for detailed error messages
            """)
        return
    
    # Get configuration
    config = get_config()
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Server Specification")
        
        # Information about the form
        st.info(
            "💡 **Intelligent Form Design:** "
            "API type will be automatically detected by the API analyzer agent. "
            "Specify GitHub organization/profile for repository creation and API documentation URL for automated analysis."
        )
        
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
            
            # GitHub configuration
            st.subheader("🐙 GitHub Configuration")
            github_org = st.text_input(
                "GitHub Organization/Profile *",
                placeholder="your-username or your-org",
                help="GitHub organization or profile where the repository will be created"
            )
            
            # API configuration
            st.subheader("🔌 API Configuration")
            api_url = st.text_input(
                "API Base URL",
                placeholder="https://api.example.com",
                help="Base URL for the target API (optional)"
            )
            
            api_docs_url = st.text_input(
                "API Documentation URL",
                placeholder="https://docs.api.example.com",
                help="Link to API documentation for the API analyzer agent to explore and scrape"
            )
            
            auth_type = st.selectbox(
                "Authentication Type",
                options=["api_key"],
                help="Authentication method for the API (API Key is currently the only supported method)",
                disabled=True  # Disabled since only one option
            )
            
            # Advanced options
            with st.expander("🔧 Advanced Options", expanded=False):
                # Language configuration
                st.subheader("⚙️ Development Configuration")
                language = st.selectbox(
                    "Programming Language",
                    options=["TypeScript"],
                    help="Programming language for the MCP server (TypeScript only for now)",
                    disabled=True  # Disabled since only TypeScript is supported
                )
                
                st.subheader("🛠️ Tools and Resources")
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
                "🚀 Generate MCP Server & Create GitHub Repo",
                type="primary",
                use_container_width=True,
                help="Generate TypeScript MCP server and create repository in specified GitHub org/profile"
            )
    
    with col2:
        st.subheader("⚡ Generation Progress")
        
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
                if st.session_state.generated_server:
                    result = st.session_state.generated_server
                    st.markdown("**Generated Server Details:**")
                    if result.get('repository_url'):
                        st.markdown(f"🐙 **Repository:** [{result['repository_url']}]({result['repository_url']})")
                    if result.get('pull_request_url'):
                        st.markdown(f"🔄 **Pull Request:** [{result['pull_request_url']}]({result['pull_request_url']})")
            elif st.session_state.workflow_status == "error":
                st.error("❌ Generation failed. Check the logs for details.")
        
        # Process form submission
        if submitted and server_name and server_description and github_org:
            try:
                # Validate inputs
                if not server_name.replace('-', '').replace('_', '').isalnum():
                    st.error("Server name must contain only letters, numbers, hyphens, and underscores")
                    st.stop()
                
                if not github_org.strip():
                    st.error("GitHub organization/profile is required")
                    st.stop()
                
                # Validate GitHub org format (basic check)
                if not github_org.replace('-', '').replace('_', '').isalnum():
                    st.error("GitHub organization/profile must contain only letters, numbers, hyphens, and underscores")
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
                    "github_org": github_org,
                    "language": language,
                    "api_url": api_url if api_url else None,
                    "api_docs_url": api_docs_url if api_docs_url else None,
                    "auth_type": auth_type,
                    "tools": [tool.strip() for tool in tools_list.split('\n') if tool.strip()],
                    "resources": [res.strip() for res in resources_list.split('\n') if res.strip()],
                    "custom_config": custom_config_dict
                }
                
                # Update workflow status
                st.session_state.workflow_status = "running"
                st.session_state.current_step = "Initializing workflow..."
                
                # Create workflow steps
                steps = []
                
                # Add API documentation analysis step if URL is provided
                if api_docs_url:
                    steps.append({"name": "Analyze API Docs", "status": "pending"})
                
                steps.extend([
                    {"name": "Detect API Type", "status": "pending"},
                    {"name": "Analyze API", "status": "pending"},
                    {"name": "Generate Code", "status": "pending"},
                    {"name": "Create GitHub Repo", "status": "pending"},
                ])
                
                # Add optional steps based on configuration
                if config and hasattr(config, 'generation'):
                    if getattr(config.generation, 'create_tests', True):
                        steps.append({"name": "Create Tests", "status": "pending"})
                    
                    if getattr(config.generation, 'create_dockerfile', False):
                        steps.append({"name": "Create Docker", "status": "pending"})
                
                if config and hasattr(config, 'validation'):
                    if getattr(config.validation, 'auto_validate', True):
                        steps.append({"name": "Validate MCP", "status": "pending"})
                
                steps.append({"name": "Package Server", "status": "pending"})
                
                # Display specification summary
                with st.expander("📋 Generated Specification", expanded=True):
                    st.json(specification)
                    st.info(
                        "💡 **Intelligent workflow features:**\n"
                        f"- **GitHub Repository:** Will be created in `{github_org}/{server_name}`\n"
                        f"- **Language:** {language} (following MCP best practices)\n"
                        f"- **Authentication:** {auth_type.replace('_', ' ').title()} (template-supported method)\n" +
                        (f"- **API Documentation:** Will be analyzed from {api_docs_url}\n" if api_docs_url else "") +
                        "- **API Type Detection:** Automatically determined by API analyzer agent\n"
                        "- **Automated Workflow:** API analysis → Code generation → GitHub repo creation"
                    )
                
                # Display workflow diagram
                with workflow_placeholder.container():
                    fig = create_workflow_diagram(steps)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Execute the workflow
                with st.spinner("Generating MCP server..."):
                    # Initialize agents
                    try:
                        orchestrator = OrchestratorAgent()
                        github_agent = None
                        
                        # Initialize GitHub agent if specified
                        if specification.get('github_org') and GitHubAgent:
                            github_agent = GitHubAgent()
                            github_validation = github_agent.validate_github_access()
                            
                            if not github_validation.get('success'):
                                st.error(f"GitHub authentication failed: {github_validation.get('error')}")
                                st.session_state.workflow_status = "error"
                                st.stop()
                            else:
                                st.success(f"✅ GitHub authenticated as: {github_validation.get('user_info', {}).get('username', 'Unknown')}")
                    except Exception as e:
                        st.error(f"Failed to initialize agents: {str(e)}")
                        st.session_state.workflow_status = "error"
                        st.stop()
                    
                    # Create progress tracking
                    progress_data = {step["name"]: 0 for step in steps}
                    
                    # Simulate step-by-step execution (replace with real implementation)
                    for i, step in enumerate(steps):
                        st.session_state.current_step = step["name"]
                        step["status"] = "running"
                        
                        # Update progress
                        progress_data[step["name"]] = 50
                        
                        # Update displays
                        with workflow_placeholder.container():
                            fig = create_workflow_diagram(steps)
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with progress_placeholder.container():
                            fig = create_progress_chart(progress_data)
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Simulate work (replace with actual agent calls)
                        time.sleep(1)
                        
                        # Complete step
                        step["status"] = "completed"
                        progress_data[step["name"]] = 100
                    
                    # Final update
                    with workflow_placeholder.container():
                        fig = create_workflow_diagram(steps)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with progress_placeholder.container():
                        fig = create_progress_chart(progress_data)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Mock successful result (replace with actual orchestrator execution)
                    result = {
                        "success": True,
                        "server_name": server_name,
                        "repository_url": f"https://github.com/{github_org}/{server_name}",
                        "pull_request_url": f"https://github.com/{github_org}/{server_name}/pull/1"
                    }
                    
                    st.session_state.workflow_status = "completed"
                    st.session_state.generated_server = result
                    st.session_state.current_step = None
                    
                    # Show balloons on success
                    st.balloons()
                    
            except Exception as e:
                st.error(f"❌ Generation failed: {str(e)}")
                st.session_state.workflow_status = "error"
                st.session_state.current_step = None
        
        elif submitted:
            st.error("❌ Please fill in all required fields (marked with *)")


def render_generation_history():
    """Render generation history if available."""
    if hasattr(st.session_state, 'generation_history') and st.session_state.generation_history:
        with st.expander("📚 Generation History", expanded=False):
            for i, entry in enumerate(st.session_state.generation_history[-5:]):  # Show last 5
                st.text(f"{i+1}. {entry['name']} - {entry['timestamp']}")
    else:
        st.info("No generation history available yet.")
