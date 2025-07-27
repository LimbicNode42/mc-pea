#!/usr/bin/env python3
"""
MC-PEA Crew Runner - Command Line Interface

Main entry point for running CrewAI crews with command line arguments.
This script loads crew configurations and executes them with provided parameters.

Usage:
    python run_crew.py --crew data_entry --url https://example.com
    python run_crew.py -c data_entry -u https://api.docs.com
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import os
import agentops

from crewai import Crew
from crews.api_extraction import HierarchicalApiExtractionCrew

# Load environment variables from .env file
load_dotenv()

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from crewai import Crew

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verify API key is loaded
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
if not anthropic_key:
    logger.error("❌ ANTHROPIC_API_KEY not found in environment variables")
    logger.error("   Please ensure you have a .env file with ANTHROPIC_API_KEY set")
    sys.exit(1)
else:
    logger.info(f"✅ Anthropic API key loaded (ending with: ...{anthropic_key[-4:]})")

google_key = os.getenv('GOOGLE_API_KEY')
if not google_key:
    logger.error("❌ GOOGLE_API_KEY not found in environment variables")
    logger.error("   Please ensure you have a .env file with GOOGLE_API_KEY set")
    sys.exit(1)
else:
    logger.info(f"✅ Google API key loaded (ending with: ...{google_key[-4:]})")


def setup_argument_parser() -> argparse.ArgumentParser:
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Run MC-PEA CrewAI crews with configurable parameters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --crew api_extraction --url https://docs.example.com
  %(prog)s -c api_extraction -u https://api.stripe.com/docs --verbose
  %(prog)s --list-crews  # List available crews
        """
    )
    
    parser.add_argument(
        '-c', '--crew',
        type=str,
        default='api_extraction',
        help='Name of the crew to run (default: api_extraction)'
    )
    
    parser.add_argument(
        '-u', '--url',
        type=str,
        help='Target website URL to crawl (required unless using --list-crews)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output (overrides config setting)'
    )
    
    parser.add_argument(
        '--no-memory',
        action='store_true',
        help='Disable crew memory (overrides config setting)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show configuration and crew setup without executing'
    )
    
    return parser

def init_observability() -> None:
    """Initialize observability tools like logging and monitoring."""
    # This is a placeholder for any observability setup you might want to do
    logger.info("Initializing observability tools...")

    agentops_key = os.getenv('AGENTOPS_API_KEY')
    if not agentops_key:
        logger.error("❌ AGENTOPS_API_KEY not found in environment variables")
        logger.error("   Please ensure you have a .env file with AGENTOPS_API_KEY set")
        logger.error("Observability failed to initialize.")
        sys.exit(1)
    else:
        logger.info(f"✅ AgentOps API key loaded (ending with: ...{agentops_key[-4:]})")
        # You can add more observability setup here if needed
        # For example, integrating with a monitoring service or setting up metrics
        agentops.init()  # Initialize AgentOps if needed
        logger.info("Observability initialized successfully.")

def create_api_extraction_crew(url: str) -> HierarchicalApiExtractionCrew:
    """Create and configure the api_extraction crew with provided parameters."""
    try:
        logger.info(f"Creating ApiExtraction crew for URL: {url}")

        # Use the HierarchicalApiExtractionCrew class
        crew_wrapper = HierarchicalApiExtractionCrew(website_url=url)
        
        # Get the actual CrewAI Crew object for logging
        crew = crew_wrapper.crew

        logger.info(f"Created api_extraction crew with {len(crew.agents)} agents and {len(crew.tasks)} tasks")
        return crew_wrapper  # Return the wrapper so we can access execute() method
        
    except Exception as e:
        logger.error(f"Error creating api_extraction crew: {e}")
        raise

def run_crew(crew_name: str, url: str, dry_run: bool = False) -> Optional[str]:
    """Run the specified crew with given parameters."""
    try:
        logger.info(f"Starting crew execution: {crew_name}")
        logger.info(f"Parameters - URL: {url}")

        # Support multiple crew types
        if crew_name == "api_extraction":
            crew_wrapper = create_api_extraction_crew(url)
        else:
            raise ValueError(f"Crew '{crew_name}' is not implemented. Available crews: 'api_extraction'")

        if dry_run:
            print("\n🔍 Dry Run - Crew Configuration:")
            print("=" * 50)
            print(f"Crew: {crew_name}")
            print(f"URL: {url}")
            print(f"Agents: {len(crew_wrapper.crew.agents)}")
            print(f"Tasks: {len(crew_wrapper.crew.tasks)}")
            print(f"Process: {crew_wrapper.crew.process}")
            print(f"Verbose: {crew_wrapper.crew.verbose}")
            print(f"Memory: {crew_wrapper.crew.memory}")
            print("\n✅ Configuration valid - ready to run")
            return None
        
        # Execute the crew
        logger.info("🚀 Starting crew execution...")
        try:
            result = crew_wrapper.execute()
            logger.info("✅ Crew execution completed successfully")
            return result
        except Exception as execution_error:
            logger.error(f"❌ Error during crew execution: {execution_error}")
            logger.error(f"❌ Error type: {type(execution_error)}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
        
    except Exception as e:
        logger.error(f"❌ Error running crew {crew_name}: {e}")
        raise


def main():
    """Main entry point for the crew runner."""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    try:
        # Validate required arguments
        if not args.url:
            parser.error("--url is required unless using --list-crews")
        
        # Validate URL format (basic check)
        if not (args.url.startswith('http://') or args.url.startswith('https://')):
            logger.warning(f"URL '{args.url}' should start with http:// or https://")
        
        init_observability()

        # Run the crew
        result = run_crew(
            crew_name=args.crew,
            url=args.url,
            dry_run=args.dry_run
        )
        
        # Display results
        if result and not args.dry_run:
            print("\n" + "=" * 80)
            print("🎉 CREW EXECUTION RESULTS")
            print("=" * 80)
            print(result)
            print("=" * 80)
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
