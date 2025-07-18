"""
Information Gathering Tasks

This module contains task definitions that use the centralized task configuration
from configs/tasks.yaml, similar to how agents load their configuration.
"""

from crewai import Task
from core.task_config_loader import get_task_config

class ApiLinkDiscoveryAgent(Task):
  def __init__(self, website_url: str, depth: int = 2):
    # Load configuration from centralized config file
    config_data = get_task_config("scrape")
      
    # Initialize the CrewAI Agent with the loaded configuration
    super().__init__(
        description=config_data.get("description"), expected_output=config_data.get("expected_output"),
        agent=config_data.get("agent"),
        markdown=config_data.get("markdown", False),
    )
    
    # Store config data for later use
    self._config_data = config_data
