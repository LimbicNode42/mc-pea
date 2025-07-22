"""
Information Gathering Tasks

This module contains task definitions that use the centralized task configuration
from configs/tasks.yaml, similar to how agents load their configuration.
"""

from crewai import Task
from core.task_config_loader import TaskConfigLoader
from models.link_discovery_output import ApiLinkDiscoveryOutput
from models.link_content_extractor_output import ApiLinkContentExtractorOutput

class ApiLinkDiscoveryTask(Task):
  def __init__(self, website_url: str, depth: int = 3):
    # Load configuration from centralized config file
    task_loader = TaskConfigLoader()
    config_data = task_loader.get_task_config("api_link_discovery")
      
    # Initialize the CrewAI Task with the loaded configuration
    # Format description and expected_output with provided parameters
    description_template = config_data.get("description", "")
    if not description_template:
        raise ValueError("No description found in task configuration")
    
    description = description_template.format(
        website_url=website_url, 
        depth=depth
    )
    
    super().__init__(
        description=description, 
        expected_output=config_data.get("expected_output"),
        # Don't pass agent from config - it should be assigned later
        # agent=config_data.get("agent"),
        ooutput_json=ApiLinkDiscoveryOutput,
        markdown=config_data.get("markdown", False),
        output_file=config_data.get("output_file", None),
    )
    
    # Store config data for later use
    self._config_data = config_data

class ApiLinkContentExtractorTask(Task):
  def __init__(self):
    # Load configuration from centralized config file
    task_loader = TaskConfigLoader()
    config_data = task_loader.get_task_config("api_link_content_extractor")

    # Initialize the CrewAI Task with the loaded configuration
    description_template = config_data.get("description")
    if not description_template:
        raise ValueError("No description found in task configuration")
    
    # For the content extractor, the description doesn't need formatting
    # since it will receive context from the previous task
    description = description_template.replace("{website_urls}", "the discovered links from the previous task")
    
    super().__init__(
        description=description,
        expected_output=config_data.get("expected_output"),
        # Don't pass agent from config - it should be assigned later
        # agent=config_data.get("agent"),
        output_json=ApiLinkContentExtractorOutput,
        markdown=config_data.get("markdown", False),
        output_file=config_data.get("output_file", None),
    )
    
    # Store config data for later use
    self._config_data = config_data
