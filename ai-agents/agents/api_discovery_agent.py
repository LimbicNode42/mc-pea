"""
API Link Discovery Agent for discovering and cataloging API-related web links.

This agent specializes in web crawling and link discovery using MCP servers:
- Discovers API documentation links up to configured depth
- Respects robots.txt and domain limits
- Tracks crawl state using MCP memory server
- Optimized for API documentation discovery
"""


from dotenv import load_dotenv
import os
from crewai import Agent, LLM
from crewai_tools import ScrapeWebsiteTool
from langchain_anthropic import ChatAnthropic
from core.agent_config_loader import AgentConfigLoader

class ApiLinkDiscoveryAgent(Agent):
    """Agent responsible for discovering and cataloging API-related web links."""

    def __init__(self, website_url: str):
        load_dotenv()

        # Load configuration from centralized config file
        agent_loader = AgentConfigLoader()
        config_data = agent_loader.get_agent_config("api_link_discovery")

        if "claude" in config_data.get("llm"):
            llm = ChatAnthropic(
                model=config_data.get("llm"),
                max_tokens=config_data.get("max_tokens"),
                temperature=config_data.get("temperature"),
                max_retries=config_data.get("max_retry_limit"),
            )
            print("Using Claude LLM for link discovery")
        elif "gemini" in config_data.get("llm"):
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini models")
            
            # Extract just the model name (remove the provider prefix)
            model_name = config_data.get("llm").replace("gemini/", "")
            
            # Use CrewAI's LLM class for Gemini models
            llm = LLM(
                model=f"gemini/{model_name}",
                api_key=google_api_key,
                max_tokens=config_data.get("max_input_tokens"),
                max_completion_tokens=config_data.get("max_output_tokens"),
                temperature=config_data.get("temperature"),
                reasoning_effort=config_data.get("reasoning_effort"),
            )
            print(f"Using Gemini LLM for link discovery: {model_name}")
        else:
            raise ValueError("Unsupported LLM type in configuration")
        
        goal_template = config_data.get("goal", "")
        if not goal_template:
            raise ValueError("No goal found in task configuration")

        goal = goal_template.format(
            website_url=website_url
        )

        text_scraper_tool = ScrapeWebsiteTool(website_url=website_url)
        
        # Initialize the CrewAI Agent with the loaded configuration
        super().__init__(
            role=config_data.get("role"),
            goal=goal,
            backstory=config_data.get("backstory"),
            llm=llm,
            tools=[text_scraper_tool],
            respect_context_window=config_data.get("respect_context_window"),
            cache=config_data.get("cache"),
            reasoning=config_data.get("reasoning"),
            max_iter=config_data.get("max_iterations"),
            max_retry_limit=config_data.get("max_retry_limit"),
            verbose=config_data.get("verbose"),
        )
        
        # Store config data for later use
        self._config_data = config_data
