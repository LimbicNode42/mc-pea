"""Streamlit interface for MCP server generation."""

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from streamlit.runtime.caching import cache_data
from dotenv import load_dotenv

# Import AI agents and workflows
from ..workflows.mcp_development import MCPDevelopmentWorkflows
from ..agents.orchestrator import OrchestratorAgent

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


def create_progress_chart(progress_data: Dict[str, float]) -> go.Figure:
    """Create a progress chart.
    
    Args:
        progress_data: Progress data for different components
        
    Returns:
        Plotly figure
    """
    fig = go.Figure(data=[
        go.Bar(
            x=list(progress_data.keys()),
            y=list(progress_data.values()),
            marker_color=px.colors.qualitative.Set3,
        )
    ])
    
    fig.update_layout(
        title="Generation Progress",
        yaxis_title="Progress (%)",
        yaxis=dict(range=[0, 100]),
        height=300,
    )
    
    return fig


def main():
    """Main Streamlit application."""
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Header
    st.markdown('<h1 class="main-header">🤖 MC-PEA AI Agent Interface</h1>', unsafe_allow_html=True)
    st.markdown("Generate production-ready MCP servers using AI agents")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Configuration
        st.subheader("API Keys")
        
        # Check for environment variable first
        env_anthropic_key = os.getenv('ANTHROPIC_API_KEY', '')
        
        if env_anthropic_key:
            st.success("✅ Anthropic API key loaded from environment")
            anthropic_api_key = env_anthropic_key
            # Show masked version for confirmation
            masked_key = f"{env_anthropic_key[:8]}...{env_anthropic_key[-4:]}" if len(env_anthropic_key) > 12 else "***"
            st.text(f"Key: {masked_key}")
        else:
            st.info("💡 Set ANTHROPIC_API_KEY environment variable for production")
            anthropic_api_key = st.text_input(
                "Anthropic API Key",
                type="password",
                help="Enter your Anthropic API key for Claude access (or set ANTHROPIC_API_KEY env var)",
            )
        
        # Agent Configuration
        st.subheader("Agent Settings")
        max_iterations = st.slider("Max Iterations", 1, 10, 5)
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        verbose_mode = st.checkbox("Verbose Mode", value=True)
        
        # Workflow Configuration
        st.subheader("Workflow Options")
        auto_validate = st.checkbox("Auto-validate generated code", value=True)
        create_tests = st.checkbox("Generate test files", value=True)
        create_docs = st.checkbox("Generate documentation", value=True)
    
    # Main interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📝 Server Specification")
        
        # Server details
        server_name = st.text_input(
            "Server Name",
            placeholder="my-api-server",
            help="Name for the MCP server (lowercase, hyphens allowed)",
        )
        
        server_description = st.text_area(
            "Description",
            placeholder="A brief description of what this MCP server does...",
            height=100,
        )
        
        # API Configuration
        st.subheader("API Configuration")
        
        api_type = st.selectbox(
            "API Type",
            ["REST API", "GraphQL", "Database", "File System", "Custom"],
        )
        
        if api_type == "REST API":
            api_base_url = st.text_input(
                "Base URL",
                placeholder="https://api.example.com/v1",
            )
            
            api_auth_type = st.selectbox(
                "Authentication",
                ["None", "API Key", "Bearer Token", "OAuth2", "Basic Auth"],
            )
            
            if api_auth_type != "None":
                api_auth_details = st.text_area(
                    "Auth Details",
                    placeholder="Additional authentication configuration...",
                    height=80,
                )
        
        elif api_type == "Database":
            db_type = st.selectbox(
                "Database Type",
                ["PostgreSQL", "MySQL", "MongoDB", "Redis", "InfluxDB"],
            )
            
            connection_string = st.text_input(
                "Connection String",
                placeholder="postgresql://user:pass@localhost:5432/db",
                type="password",
            )
        
        # Tools and Resources
        st.subheader("Tools & Resources")
        
        tools_input = st.text_area(
            "Tools (one per line)",
            placeholder="get_users\ncreate_user\nupdate_user\ndelete_user",
            height=100,
            help="List the tools/functions this server should provide",
        )
        
        resources_input = st.text_area(
            "Resources (one per line)",
            placeholder="users\nprofiles\nsettings",
            height=80,
            help="List the resources this server should expose",
        )
    
    with col2:
        st.header("🔄 Generation Progress")
        
        # Workflow steps
        workflow_steps = [
            {"name": "Analyze API", "status": "pending"},
            {"name": "Generate Code", "status": "pending"},
            {"name": "Create Tests", "status": "pending"},
            {"name": "Validate MCP", "status": "pending"},
            {"name": "Package", "status": "pending"},
        ]
        
        # Show workflow diagram
        workflow_fig = create_workflow_diagram(workflow_steps)
        st.plotly_chart(workflow_fig, use_container_width=True)
        
        # Progress metrics
        progress_data = {
            "Analysis": 0,
            "Code Gen": 0,
            "Testing": 0,
            "Validation": 0,
        }
        
        progress_fig = create_progress_chart(progress_data)
        st.plotly_chart(progress_fig, use_container_width=True)
        
        # Status area
        status_placeholder = st.empty()
        logs_placeholder = st.empty()
    
    # Generation controls
    st.header("🚀 Generation Controls")
    
    col_generate, col_validate, col_download = st.columns([2, 1, 1])
    
    with col_generate:
        if st.button("🎯 Generate MCP Server", type="primary", use_container_width=True):
            if not anthropic_api_key:
                st.error("Please provide an Anthropic API key")
                return
            
            if not server_name:
                st.error("Please provide a server name")
                return
            
            # Show generation in progress
            with status_placeholder.container():
                st.markdown('<div class="status-card">🔄 Generation in progress...</div>', unsafe_allow_html=True)
            
            # Simulate generation process
            progress_bar = st.progress(0)
            
            steps_completed = 0
            total_steps = len(workflow_steps)
            
            for i, step in enumerate(workflow_steps):
                step["status"] = "running"
                workflow_fig = create_workflow_diagram(workflow_steps)
                
                # Update progress
                time.sleep(2)  # Simulate work
                steps_completed += 1
                progress_bar.progress(steps_completed / total_steps)
                
                step["status"] = "completed"
                
                # Update progress data
                progress_data = {
                    "Analysis": min(100, (steps_completed / total_steps) * 120),
                    "Code Gen": max(0, min(100, ((steps_completed - 1) / total_steps) * 120)),
                    "Testing": max(0, min(100, ((steps_completed - 2) / total_steps) * 120)),
                    "Validation": max(0, min(100, ((steps_completed - 3) / total_steps) * 120)),
                }
                
                progress_fig = create_progress_chart(progress_data)
                
                with logs_placeholder.container():
                    st.text(f"✅ Completed: {step['name']}")
            
            # Show completion
            with status_placeholder.container():
                st.markdown('<div class="success-card">✅ MCP server generated successfully!</div>', unsafe_allow_html=True)
            
            # Show generated files
            st.subheader("📁 Generated Files")
            
            generated_files = [
                "src/index.ts",
                "src/tools/api_tools.ts", 
                "src/resources/api_resources.ts",
                "package.json",
                "tsconfig.json",
                "tests/basic.test.ts",
                "README.md",
                "Dockerfile",
            ]
            
            for file_path in generated_files:
                st.text(f"📄 {file_path}")
    
    with col_validate:
        if st.button("🔍 Validate", use_container_width=True):
            st.info("Validation will check MCP protocol compliance")
    
    with col_download:
        if st.button("📥 Download", use_container_width=True):
            st.info("Download generated server as ZIP file")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "🔧 **MC-PEA AI Agents** - Automated MCP server generation and management"
    )


if __name__ == "__main__":
    main()
