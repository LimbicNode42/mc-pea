#!/usr/bin/env python3
"""
Entry point for the MC-PEA AI Agent Streamlit interface.
This script sets up the proper Python path and launches the server generator.
"""

import os
import sys
from pathlib import Path

# Add the ai-agents directory to Python path
ai_agents_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(ai_agents_dir))

# Now we can import and run the server generator
if __name__ == "__main__":
    from interfaces.server_generator import main
    main()
