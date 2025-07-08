"""Streamlit interface for MCP server generation with AI agent integration."""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from streamlit.runtime.caching import cache_data

# Import AI agents and workflows
try:
    from ..workflows.mcp_development import MCPDevelopmentWorkflows
    from ..agents.orchestrator import OrchestratorAgent
except ImportError:
    # Fallback for when running directly
    MCPDevelopmentWorkflows = None
    OrchestratorAgent = None

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

.success-box {
    background-color: #d4edda;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #28a745;
}

.error-box {
    background-color: #f8d7da;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #dc3545;
}

.info-box {
    background-color: #d1ecf1;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #17a2b8;
}

.workflow-step {
    padding: 0.5rem;
    margin: 0.5rem 0;
    border-radius: 0.5rem;
    border: 1px solid #ddd;
}

.workflow-step.active {
    background-color: #e3f2fd;
    border-color: #2196f3;
}

.workflow-step.completed {
    background-color: #e8f5e8;
    border-color: #4caf50;
}

.workflow-step.failed {
    background-color: #ffebee;
    border-color: #f44336;
}

.metric-card {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #dee2e6;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)


class MCPServerGeneratorUI:
    """Main UI class for MCP server generation with AI agent integration."""
    
    def __init__(self):
        self.initialize_session_state()
        self.setup_agents()
    
    def initialize_session_state(self):
        """Initialize Streamlit session state."""
        defaults = {
            'generation_state': 'idle',
            'current_step': 0,
            'total_steps': 5,
            'progress_data': {},
            'server_config': {},
            'api_spec': {},
            'generation_results': {},
            'validation_results': {},
            'workflow_history': [],
            'active_workflow': None,
            'agents_initialized': False
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def setup_agents(self):
        """Setup AI agents and workflows."""
        if st.session_state.get('agents_initialized', False):
            return
        
        try:
            # Initialize configuration
            config = {
                'anthropic_api_key': st.secrets.get('ANTHROPIC_API_KEY', ''),
                'output_dir': './generated-servers',
                'log_level': 'INFO'
            }
            
            # Initialize workflows (if available)
            if MCPDevelopmentWorkflows:
                st.session_state['workflows'] = MCPDevelopmentWorkflows(config)
            else:
                st.session_state['workflows'] = None
            
            # Initialize orchestrator (if available)
            if OrchestratorAgent:
                st.session_state['orchestrator'] = OrchestratorAgent(config)
            else:
                st.session_state['orchestrator'] = None
            
            st.session_state['agents_initialized'] = True
                
        except Exception as e:
            st.error(f"Failed to initialize agents: {str(e)}")
            st.session_state['workflows'] = None
            st.session_state['orchestrator'] = None
    
    def create_workflow_diagram(self, steps: List[Dict[str, Any]]) -> go.Figure:
        """Create a workflow visualization using Plotly."""
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
    
    def create_progress_chart(self, progress_data: Dict[str, float]) -> go.Figure:
        """Create a progress chart using Plotly."""
        if not progress_data:
            progress_data = {"Overall": 0}
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(progress_data.keys()),
                y=list(progress_data.values()),
                marker_color=px.colors.qualitative.Set3,
                text=[f"{v:.1f}%" for v in progress_data.values()],
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title="Generation Progress",
            yaxis_title="Progress (%)",
            yaxis=dict(range=[0, 100]),
            height=300,
            showlegend=False
        )
        
        return fig
    
    def render_sidebar(self):
        """Render the sidebar configuration."""
        with st.sidebar:
            st.header("⚙️ Configuration")
            
            # API Configuration
            st.subheader("API Keys")
            anthropic_api_key = st.text_input(
                "Anthropic API Key",
                type="password",
                help="Enter your Anthropic API key for Claude access",
                value=st.secrets.get('ANTHROPIC_API_KEY', '') if 'ANTHROPIC_API_KEY' in st.secrets else ''
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
            include_docker = st.checkbox("Include Docker configuration", value=True)
            
            # Output Configuration
            st.subheader("Output Settings")
            output_dir = st.text_input("Output Directory", value="./generated-servers")
            
            return {
                'anthropic_api_key': anthropic_api_key,
                'max_iterations': max_iterations,
                'temperature': temperature,
                'verbose_mode': verbose_mode,
                'auto_validate': auto_validate,
                'create_tests': create_tests,
                'create_docs': create_docs,
                'include_docker': include_docker,
                'output_dir': output_dir
            }
    
    def render_server_specification(self):
        """Render the server specification form."""
        st.header("📝 Server Specification")
        
        # Server details
        server_name = st.text_input(
            "Server Name",
            placeholder="my-api-server",
            help="Name for the MCP server (lowercase, hyphens allowed)",
        )
        
        server_description = st.text_area(
            "Server Description",
            placeholder="Brief description of what this server does",
            height=100,
        )
        
        # API Configuration
        st.subheader("API Configuration")
        api_url = st.text_input(
            "API Base URL",
            placeholder="https://api.example.com",
            help="Base URL of the API to integrate",
        )
        
        col1, col2 = st.columns(2)
        with col1:
            api_type = st.selectbox(
                "API Type",
                ["REST", "GraphQL", "gRPC", "WebSocket"],
                index=0,
            )
        
        with col2:
            auth_type = st.selectbox(
                "Authentication Type",
                ["None", "API Key", "Bearer Token", "OAuth2", "Basic Auth"],
                index=0,
            )
        
        # Documentation
        st.subheader("Documentation")
        col1, col2 = st.columns(2)
        with col1:
            docs_url = st.text_input(
                "API Documentation URL",
                placeholder="https://docs.example.com",
                help="URL to API documentation",
            )
        
        with col2:
            openapi_url = st.text_input(
                "OpenAPI Specification URL",
                placeholder="https://api.example.com/openapi.json",
                help="URL to OpenAPI/Swagger specification",
            )
        
        # Advanced Configuration
        with st.expander("Advanced Configuration"):
            rate_limit = st.number_input("Rate Limit (requests/second)", value=10, min_value=1)
            timeout = st.number_input("Request Timeout (seconds)", value=30, min_value=1)
            retry_attempts = st.number_input("Retry Attempts", value=3, min_value=0)
            
            custom_headers = st.text_area(
                "Custom Headers (JSON)",
                placeholder='{"X-Custom-Header": "value"}',
                help="Custom headers to include in API requests"
            )
        
        return {
            'name': server_name,
            'description': server_description,
            'url': api_url,
            'type': api_type,
            'auth_type': auth_type,
            'docs_url': docs_url,
            'openapi_url': openapi_url,
            'rate_limit': rate_limit,
            'timeout': timeout,
            'retry_attempts': retry_attempts,
            'custom_headers': custom_headers
        }
    
    def render_workflow_status(self):
        """Render workflow status and progress."""
        st.header("📊 Workflow Status")
        
        if st.session_state.active_workflow:
            workflow = st.session_state.active_workflow
            
            # Status indicator
            status = workflow.get('status', 'unknown')
            if status == 'running':
                st.info("🔄 Workflow is running...")
            elif status == 'completed':
                st.success("✅ Workflow completed successfully!")
            elif status == 'failed':
                st.error("❌ Workflow failed. Check logs for details.")
            else:
                st.info("⏳ Workflow is pending...")
            
            # Progress indicator
            progress = workflow.get('progress', 0)
            st.progress(progress / 100)
            
            # Current step
            current_step = workflow.get('current_step', 'Initializing')
            st.write(f"**Current Step:** {current_step}")
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Progress", f"{progress:.1f}%")
            with col2:
                if 'start_time' in workflow:
                    start_time = datetime.fromisoformat(workflow['start_time'])
                    elapsed = datetime.now() - start_time
                    st.metric("Elapsed", f"{elapsed.seconds}s")
            with col3:
                step_index = workflow.get('current_step_index', 0)
                total_steps = workflow.get('total_steps', 5)
                st.metric("Step", f"{step_index + 1}/{total_steps}")
            
            # Results
            if workflow.get('results'):
                with st.expander("Workflow Results"):
                    st.json(workflow['results'])
            
            # Logs
            if workflow.get('logs'):
                with st.expander("Workflow Logs"):
                    for log in workflow['logs']:
                        st.text(log)
        
        else:
            st.info("No active workflow. Configure and start a workflow to see progress.")
    
    def render_workflow_visualization(self):
        """Render workflow visualization."""
        st.header("🔄 Workflow Visualization")
        
        # Default workflow steps
        steps = [
            {"name": "Analyze API", "status": "pending"},
            {"name": "Generate Server", "status": "pending"},
            {"name": "Validate Code", "status": "pending"},
            {"name": "Run Tests", "status": "pending"},
            {"name": "Package", "status": "pending"},
        ]
        
        # Update step status based on current state
        if st.session_state.active_workflow:
            current_step = st.session_state.active_workflow.get('current_step_index', 0)
            status = st.session_state.active_workflow.get('status', 'pending')
            
            for i, step in enumerate(steps):
                if i < current_step:
                    step['status'] = 'completed'
                elif i == current_step:
                    step['status'] = 'running' if status == 'running' else 'completed'
                else:
                    step['status'] = 'pending'
            
            # If workflow failed, mark current step as failed
            if status == 'failed' and current_step < len(steps):
                steps[current_step]['status'] = 'failed'
        
        # Create and display workflow diagram
        fig = self.create_workflow_diagram(steps)
        st.plotly_chart(fig, use_container_width=True)
        
        # Progress chart
        if st.session_state.progress_data:
            progress_fig = self.create_progress_chart(st.session_state.progress_data)
            st.plotly_chart(progress_fig, use_container_width=True)
    
    def start_generation_workflow(self, api_spec: Dict[str, Any], config: Dict[str, Any]):
        """Start the complete generation workflow."""
        if not api_spec.get('url'):
            st.error("API URL is required to start workflow.")
            return
        
        # Initialize workflow
        st.session_state.active_workflow = {
            'type': 'full_development',
            'status': 'running',
            'current_step': 'Initializing Workflow',
            'current_step_index': 0,
            'progress': 0,
            'total_steps': 5,
            'start_time': datetime.now().isoformat(),
            'results': {},
            'logs': []
        }
        
        # Update progress data
        st.session_state.progress_data = {
            "API Analysis": 0,
            "Code Generation": 0,
            "Validation": 0,
            "Testing": 0,
            "Packaging": 0
        }
        
        # Simulate workflow execution
        try:
            # Simulate workflow steps
            steps = [
                ("Analyzing API", "API Analysis", 20),
                ("Generating Server Code", "Code Generation", 40),
                ("Validating Implementation", "Validation", 60),
                ("Running Tests", "Testing", 80),
                ("Finalizing Package", "Packaging", 100)
            ]
            
            for i, (step_name, progress_key, progress) in enumerate(steps):
                # Update workflow state
                st.session_state.active_workflow.update({
                    'current_step': step_name,
                    'current_step_index': i,
                    'progress': progress
                })
                
                # Update progress data
                st.session_state.progress_data[progress_key] = progress
                
                # Add log entry
                st.session_state.active_workflow['logs'].append(
                    f"[{datetime.now().isoformat()}] {step_name}..."
                )
                
                # Simulate processing time
                time.sleep(1)
                
                # Rerun to update UI
                st.rerun()
            
            # Generate mock results
            results = {
                'server_path': f'{config["output_dir"]}/{api_spec["name"]}-mcp-server',
                'files_created': [
                    'src/index.ts',
                    'src/tools/api_request.ts',
                    'src/resources/data.ts',
                    'package.json',
                    'tsconfig.json',
                    'README.md'
                ],
                'validation_score': 87,
                'tests_passed': 15,
                'tests_total': 18,
                'deployment_ready': True,
                'mcp_specification': {
                    'name': f"{api_spec['name']}-mcp-server",
                    'description': api_spec['description'],
                    'version': '1.0.0',
                    'tools': ['api_request', 'get_data', 'post_data'],
                    'resources': ['api://data', 'api://config'],
                    'authentication': api_spec.get('auth_type', 'None')
                }
            }
            
            # Complete workflow
            st.session_state.active_workflow.update({
                'status': 'completed',
                'progress': 100,
                'results': results,
                'end_time': datetime.now().isoformat()
            })
            
            # Add completion log
            st.session_state.active_workflow['logs'].append(
                f"[{datetime.now().isoformat()}] Workflow completed successfully!"
            )
            
        except Exception as e:
            st.session_state.active_workflow.update({
                'status': 'failed',
                'error': str(e),
                'end_time': datetime.now().isoformat()
            })
            
            # Add error log
            st.session_state.active_workflow['logs'].append(
                f"[{datetime.now().isoformat()}] ERROR: {str(e)}"
            )
    
    def render_workflow_controls(self, api_spec: Dict[str, Any], config: Dict[str, Any]):
        """Render workflow control buttons."""
        st.header("🚀 Workflow Control")
        
        # Main generation button
        if st.button("🎯 Generate MCP Server", 
                    disabled=not api_spec.get('url') or st.session_state.active_workflow,
                    help="Start complete MCP server generation workflow"):
            self.start_generation_workflow(api_spec, config)
        
        # Control buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⏹️ Stop Workflow", 
                        disabled=not st.session_state.active_workflow or 
                                st.session_state.active_workflow.get('status') != 'running'):
                if st.session_state.active_workflow:
                    st.session_state.active_workflow['status'] = 'cancelled'
                    st.success("Workflow cancelled.")
        
        with col2:
            if st.button("🔄 Reset", 
                        disabled=st.session_state.active_workflow and 
                                st.session_state.active_workflow.get('status') == 'running'):
                st.session_state.active_workflow = None
                st.session_state.progress_data = {}
                st.success("Workflow reset.")
        
        with col3:
            if st.button("📋 View History"):
                if st.session_state.workflow_history:
                    st.sidebar.subheader("Workflow History")
                    for i, workflow in enumerate(st.session_state.workflow_history):
                        st.sidebar.write(f"{i+1}. {workflow.get('type', 'Unknown')} - {workflow.get('status', 'Unknown')}")
                else:
                    st.sidebar.info("No workflow history available.")
    
    def render_results_section(self):
        """Render results section."""
        if st.session_state.active_workflow and st.session_state.active_workflow.get('results'):
            st.header("📁 Generated Files")
            
            results = st.session_state.active_workflow['results']
            
            # File list
            if 'files_created' in results:
                st.subheader("Created Files")
                for file in results['files_created']:
                    st.write(f"✅ {file}")
            
            # Metrics
            if 'validation_score' in results:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Validation Score", f"{results['validation_score']}/100")
                with col2:
                    if 'tests_passed' in results and 'tests_total' in results:
                        st.metric("Tests Passed", f"{results['tests_passed']}/{results['tests_total']}")
                with col3:
                    st.metric("Deployment Ready", "Yes" if results.get('deployment_ready') else "No")
                with col4:
                    st.metric("Server Path", results.get('server_path', 'N/A'))
            
            # MCP Specification
            if 'mcp_specification' in results:
                with st.expander("MCP Specification"):
                    st.json(results['mcp_specification'])
            
            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Download Server Package"):
                    st.info("Package download would be implemented here.")
            with col2:
                if st.button("📄 Download Documentation"):
                    st.info("Documentation download would be implemented here.")
    
    def run(self):
        """Run the main Streamlit application."""
        # Header
        st.markdown('<h1 class="main-header">🤖 MC-PEA AI Agent Interface</h1>', unsafe_allow_html=True)
        st.markdown("""
        Generate production-ready MCP servers using AI agents. This interface provides a complete 
        workflow for analyzing APIs, generating TypeScript MCP servers, and validating implementations.
        """)
        
        # Render sidebar
        config = self.render_sidebar()
        
        # Main interface
        col1, col2 = st.columns([1, 1])
        
        with col1:
            api_spec = self.render_server_specification()
            self.render_workflow_controls(api_spec, config)
        
        with col2:
            self.render_workflow_status()
            self.render_workflow_visualization()
        
        # Results section (full width)
        self.render_results_section()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        **MC-PEA AI Agent Interface** - Powered by Claude, CrewAI, and Plotly  
        Generate MCP servers with AI-driven analysis, code generation, and validation.
        """)


def main():
    """Main application entry point."""
    ui = MCPServerGeneratorUI()
    ui.run()


if __name__ == "__main__":
    main()
