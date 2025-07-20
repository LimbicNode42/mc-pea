"""
API Link Discovery Agent for discovering and cataloging API-related web links.

This agent specializes in web crawling and link discovery using MCP servers:
- Discovers API documentation links up to configured depth
- Respects robots.txt and domain limits
- Tracks crawl state using MCP memory server
- Optimized for API documentation discovery
"""

from crewai import Agent
from crewai_tools import ScrapeWebsiteTool
from langchain_anthropic import ChatAnthropic
from core.agent_config_loader import AgentConfigLoader

class ApiLinkDiscoveryAgent(Agent):
    """Agent responsible for discovering and cataloging API-related web links."""

    def __init__(self, website_url: str):
        # Load configuration from centralized config file
        agent_loader = AgentConfigLoader()
        config_data = agent_loader.get_agent_config("api_link_discovery")

        llm = ChatAnthropic(
            model=config_data.get("llm"),
            max_tokens=config_data.get("max_tokens", 8000),
            temperature=config_data.get("temperature", 0.3),
            max_retries=config_data.get("max_retry_limit", 2),
        )

        scraper_tool = ScrapeWebsiteTool(website_url=website_url)
        
        # Initialize the CrewAI Agent with the loaded configuration
        super().__init__(
            role=config_data.get("role"),
            goal=config_data.get("goal"),
            backstory=config_data.get("backstory"),
            llm=llm,
            tools=[scraper_tool],
            verbose=config_data.get("verbose", False),
            max_iterations=config_data.get("max_iterations", 20),
            max_retry_limit=config_data.get("max_retry_limit", 2)
        )
        
        # Store config data for later use
        self._config_data = config_data
