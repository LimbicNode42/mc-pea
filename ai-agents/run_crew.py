#!/usr/bin/env python3
"""
MC-PEA Crew Runner - Command Line Interface

Main entry point for running CrewAI crews with command line arguments.
This script loads crew configurations and executes them with provided parameters.

Usage:
    python run_crew.py --crew data_entry --url https://example.com --depth 2
    python run_crew.py -c data_entry -u https://api.docs.com -d 3
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from core.crew_config_loader import CrewConfigLoader
from agents.link_discovery_agent import ApiLinkDiscoveryAgent
from tasks.information_gathering import ApiLinkDiscoveryTask
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


def setup_argument_parser() -> argparse.ArgumentParser:
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Run MC-PEA CrewAI crews with configurable parameters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --crew data_entry --url https://docs.example.com --depth 2
  %(prog)s -c data_entry -u https://api.stripe.com/docs -d 3 --verbose
  %(prog)s --list-crews  # List available crews
        """
    )
    
    parser.add_argument(
        '-c', '--crew',
        type=str,
        default='data_entry',
        help='Name of the crew to run (default: data_entry)'
    )
    
    parser.add_argument(
        '-u', '--url',
        type=str,
        help='Target website URL to crawl (required unless using --list-crews)'
    )
    
    parser.add_argument(
        '-d', '--depth',
        type=int,
        default=2,
        help='Crawling depth limit (default: 2)'
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
        '--list-crews',
        action='store_true',
        help='List available crews and exit'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show configuration and crew setup without executing'
    )
    
    return parser


def list_available_crews() -> None:
    """List all available crews from configuration."""
    try:
        crew_loader = CrewConfigLoader()
        crew_names = crew_loader.get_all_crew_names()
        
        print("\n🤖 Available Crews:")
        print("=" * 50)
        
        if not crew_names:
            print("No crews found in configuration.")
            return
        
        for crew_name in crew_names:
            crew_config = crew_loader.get_crew_config(crew_name)
            print(f"\n📋 {crew_name}")
            print(f"   Tasks: {crew_loader.get_crew_tasks(crew_name)}")
            print(f"   Agents: {crew_loader.get_crew_agents(crew_name)}")
            print(f"   Process: {crew_loader.get_crew_process(crew_name)}")
            print(f"   Verbose: {crew_loader.is_crew_verbose(crew_name)}")
            print(f"   Memory: {crew_loader.is_crew_memory_enabled(crew_name)}")
            
    except Exception as e:
        logger.error(f"Error listing crews: {e}")
        sys.exit(1)


def create_data_entry_crew(url: str, depth: int) -> Crew:
    """Create and configure the data_entry crew with provided parameters."""
    try:
        # Load configurations
        crew_loader = CrewConfigLoader()
        
        # Get crew configuration
        crew_config = crew_loader.get_crew_config("data_entry")
        if not crew_config:
            raise ValueError("data_entry crew configuration not found")
        
        # Create agent instance
        logger.info(f"Creating ApiLinkDiscoveryAgent for URL: {url}")
        agent = ApiLinkDiscoveryAgent(website_url=url)
        
        # Create task instance with dynamic parameters
        logger.info(f"Creating ApiLinkDiscoveryTask with depth: {depth}")
        task = ApiLinkDiscoveryTask(website_url=url, depth=depth)
        task.agent = agent  # Assign the agent to the task
        
        # Override configuration with command line arguments if provided
        crew_process = crew_loader.get_crew_process("data_entry")
        
        # Create the crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=crew_process
        )
        
        logger.info(f"Created data_entry crew with {len(crew.agents)} agents and {len(crew.tasks)} tasks")
        return crew
        
    except Exception as e:
        logger.error(f"Error creating data_entry crew: {e}")
        raise


def run_crew(crew_name: str, url: str, depth: int, dry_run: bool = False) -> Optional[str]:
    """Run the specified crew with given parameters."""
    try:
        logger.info(f"Starting crew execution: {crew_name}")
        logger.info(f"Parameters - URL: {url}, Depth: {depth}")
        
        # Currently only supporting data_entry crew
        if crew_name != "data_entry":
            raise ValueError(f"Crew '{crew_name}' is not yet implemented. Only 'data_entry' is available.")
        
        # Create the crew
        crew = create_data_entry_crew(url, depth)
        
        if dry_run:
            print("\n🔍 Dry Run - Crew Configuration:")
            print("=" * 50)
            print(f"Crew: {crew_name}")
            print(f"URL: {url}")
            print(f"Depth: {depth}")
            print(f"Agents: {len(crew.agents)}")
            print(f"Tasks: {len(crew.tasks)}")
            print(f"Process: {crew.process}")
            print(f"Verbose: {crew.verbose}")
            print(f"Memory: {crew.memory}")
            print("\n✅ Configuration valid - ready to run")
            return None
        
        # Execute the crew
        logger.info("🚀 Starting crew execution...")
        try:
            result = crew.kickoff()
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
        # Handle list crews request
        if args.list_crews:
            list_available_crews()
            return
        
        # Validate required arguments
        if not args.url:
            parser.error("--url is required unless using --list-crews")
        
        # Validate URL format (basic check)
        if not (args.url.startswith('http://') or args.url.startswith('https://')):
            logger.warning(f"URL '{args.url}' should start with http:// or https://")
        
        # Run the crew
        result = run_crew(
            crew_name=args.crew,
            url=args.url,
            depth=args.depth,
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
