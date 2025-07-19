"""
Information Gathering Tasks

This module contains task definitions that use the centralized task configuration
from configs/tasks.yaml, similar to how agents load their configuration.
"""

from crewai import Task
from core.task_config_loader import TaskConfigLoader

class ApiLinkDiscoveryTask(Task):
  def __init__(self, website_url: str, depth: int = 2):
    # Load configuration from centralized config file
    task_loader = TaskConfigLoader()
    config_data = task_loader.get_task_config("api_link_discovery")
      
    # Initialize the CrewAI Task with the loaded configuration
    # Format description and expected_output with provided parameters
    description = config_data.get("description").format(
        website_url=website_url, 
        depth=depth
    )
    
    super().__init__(
        description=description, 
        expected_output=config_data.get("expected_output"),
        agent=config_data.get("agent"),
        markdown=config_data.get("markdown", False),
    )
    
    # Store config data for later use
    self._config_data = config_data
