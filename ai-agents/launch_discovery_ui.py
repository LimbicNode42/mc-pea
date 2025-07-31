"""
Launcher for the Endpoint Discovery UI

Simple script to launch the Streamlit interface for API endpoint discovery.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the endpoint discovery Streamlit interface."""
    
    # Get the path to the interface file
    current_dir = Path(__file__).parent
    interface_file = current_dir / "interfaces" / "endpoint_discovery_ui.py"
    
    if not interface_file.exists():
        print(f"❌ Interface file not found: {interface_file}")
        sys.exit(1)
    
    print("🚀 Launching Endpoint Discovery Interface...")
    print(f"📁 Interface file: {interface_file}")
    
    # Set up environment
    env = os.environ.copy()
    
    # Launch Streamlit
    try:
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            str(interface_file),
            "--server.headless", "false",
            "--server.port", "8501",
            "--theme.base", "light"
        ]
        
        print(f"🔧 Running command: {' '.join(cmd)}")
        subprocess.run(cmd, env=env, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to launch Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Interface shutdown requested")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
