"""
Streamlit interface for MCP server generation - Simplified Main Module
"""
import os
import sys
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modular components
from interfaces.agent_discovery import render_agents_dashboard
from interfaces.server_discovery import render_servers_dashboard
from interfaces.server_generation import render_server_generation

# Import AI agents and workflows
try:
    from core.config import get_config_manager, get_config
    from interfaces.config_panel import render_config_panel
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    IMPORTS_AVAILABLE = False
    
    def get_config_manager():
        return None
    
    def get_config():
        return {}
    
    def render_config_panel():
        st.sidebar.write("Config panel not available")
        st.sidebar.error(f"Import failed: {e}")
        return None


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
    background: var(--background-color, #ffffff);
    border: 1px solid var(--border-color, #e0e0e0);
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
}

.status-card h4 {
    margin-top: 0;
    color: var(--text-color, #262730);
}

.status-card p {
    margin-bottom: 0.5rem;
    color: var(--text-color, #262730);
}

.success-card {
    background: var(--background-color, #d4edda);
    border: 1px solid #c3e6cb;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #28a745;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.error-card {
    background: var(--background-color, #f8d7da);
    border: 1px solid #f5c6cb;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #dc3545;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

@media (prefers-color-scheme: dark) {
    .status-card {
        background: var(--background-color, #2d3748);
        border-color: var(--border-color, #4a5568);
    }
    
    .status-card h4, .status-card p {
        color: var(--text-color, #e2e8f0);
    }
}
</style>
""", unsafe_allow_html=True)


def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<h1 class="main-header">🤖 MC-PEA AI Agent Interface</h1>', unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Render config panel if available
        if IMPORTS_AVAILABLE:
            render_config_panel()
        else:
            st.error("Configuration panel unavailable")
        
        st.divider()
        
        # System status
        st.subheader("📊 System Status")
        st.metric("Imports Available", "✅" if IMPORTS_AVAILABLE else "❌")
        
        # Quick actions
        st.subheader("🚀 Quick Actions")
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🤖 Agents", "🛠️ Servers", "➕ Generate", "📈 Monitor"])
    
    with tab1:
        render_agents_dashboard()
    
    with tab2:
        render_servers_dashboard()
    
    with tab3:
        render_server_generation()
    
    with tab4:
        st.header("📈 System Monitoring")
        st.info("🔧 Monitoring dashboard coming soon!")
        
        # Basic system info for now
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}")
        
        with col2:
            st.metric("Working Directory", "ai-agents")
        
        with col3:
            st.metric("Import Status", "✅" if IMPORTS_AVAILABLE else "❌")


if __name__ == "__main__":
    main()
