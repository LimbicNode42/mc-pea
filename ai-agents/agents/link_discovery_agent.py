"""
API Link Discovery Agent for discovering and cataloging API-related web links.

This agent specializes in web crawling and link discovery using MCP servers:
- Discovers API documentation links up to configured depth
- Respects robots.txt and domain limits
- Tracks crawl state using MCP memory server
- Optimized for API documentation discovery
"""

from crewai import Agent
from core.agent_config_loader import get_agent_config


class ApiLinkDiscoveryAgent(Agent):
    """Agent responsible for discovering and cataloging API-related web links."""
    
    def __init__(self):
        # Load configuration from centralized config file
        config_data = get_agent_config("api_link_discovery")
        
        # Initialize the CrewAI Agent with the loaded configuration
        super().__init__(
            role=config_data.get("role"),
            goal=config_data.get("goal"),
            backstory=config_data.get("backstory"),
            llm=config_data.get("llm", "claude-sonnet-4-20250514"),
            verbose=config_data.get("verbose", False)
        )
        
        # Store config data for later use
        self._config_data = config_data
