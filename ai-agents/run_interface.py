#!/usr/bin/env python3
"""
MC-PEA AI Agent Dashboard - Main Streamlit Application

This is the main entry point for the MC-PEA AI agent system interface.
It provides a comprehensive dashboard for managing AI agents and MCP servers.

Usage:
    streamlit run app.py
"""

import os
import sys
from pathlib import Path

# Add the ai-agents directory to Python path
current_dir = Path(__file__).parent
ai_agents_dir = current_dir
sys.path.insert(0, str(ai_agents_dir))

# Set working directory to ai-agents for proper imports
os.chdir(ai_agents_dir)

# Import and run the main interface
try:
    from interfaces.server_generator import main
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    import streamlit as st
    
    st.set_page_config(
        page_title="MC-PEA AI Agent Interface - Import Error",
        page_icon="❌",
        layout="wide"
    )
    
    st.error("❌ Failed to import required modules")
    st.markdown(f"""
    **Import Error:** {e}
    
    **Troubleshooting Steps:**
    1. Make sure you're running this from the `ai-agents/` directory
    2. Install required dependencies: `pip install -r requirements.txt`
    3. Check that all agent modules are properly implemented
    4. Verify the directory structure matches the expected layout
    
    **Expected Directory Structure:**
    ```
    ai-agents/
    ├── app.py                    # This file
    ├── requirements.txt
    ├── core/                     # Core framework
    ├── agents/                   # Agent implementations
    ├── interfaces/               # UI interfaces
    ├── workflows/                # Workflow definitions
    └── tools/                    # Shared tools
    ```
    
    **Current Directory:** `{os.getcwd()}`
    
    **Python Path:** `{sys.path[:3]}...`
    """)
    
    # Show directory contents for debugging
    st.subheader("🔍 Directory Contents")
    try:
        current_contents = list(Path(".").iterdir())
        st.write("Current directory contents:")
        for item in current_contents:
            if item.is_dir():
                st.write(f"📁 {item.name}/")
            else:
                st.write(f"📄 {item.name}")
    except Exception as debug_e:
        st.error(f"Could not list directory contents: {debug_e}")
