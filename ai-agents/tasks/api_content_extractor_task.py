"""
Information Gathering Tasks

This module contains task definitions that use the centralized task configuration
from configs/tasks.yaml, similar to how agents load their configuration.
"""

from crewai import Task
from typing import List
from core.task_config_loader import TaskConfigLoader
from models.api_content_extractor_output import ApiLinkContentExtractorOutput

class ApiLinkContentExtractorTask(Task):
  def __init__(self):
    # Load configuration from centralized config file
    task_loader = TaskConfigLoader()
    config_data = task_loader.get_task_config("api_content_extraction")

    # Initialize the CrewAI Task with the loaded configuration
    description_template = config_data.get("description")
    if not description_template:
        raise ValueError("No description found in task configuration")
    
    super().__init__(
        description=config_data.get("description"),
        expected_output=config_data.get("expected_output"),
        async_execution=config_data.get("async_execution"),
        output_json=ApiLinkContentExtractorOutput,
        markdown=config_data.get("markdown"),
        output_file=config_data.get("output_file"),
    )
    
    # Store config data for later use
    self._config_data = config_data
