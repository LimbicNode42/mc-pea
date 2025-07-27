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
  def __init__(self, hostname: str, context: List[Task]):
    # Load configuration from centralized config file
    task_loader = TaskConfigLoader()
    config_data = task_loader.get_task_config("api_content_extraction")

    # Initialize the CrewAI Task with the loaded configuration
    description_template = config_data.get("description")
    if not description_template:
        raise ValueError("No description found in task configuration")
    
    # Extract context output from the orchestrator task (should be the last context task)
    context_output = ""
    if context and len(context) > 0:
        # Get the most recent context task (orchestrator)
        orchestrator_task = context[-1]
        if hasattr(orchestrator_task, 'output') and hasattr(orchestrator_task.output, 'raw'):
            context_output = orchestrator_task.output.raw
    
    # Format the description template with hostname and context output
    formatted_description = description_template.format(
        hostname=hostname,
        context_output=context_output
    )
    
    super().__init__(
        description=formatted_description,
        expected_output=config_data.get("expected_output"),
        async_execution=config_data.get("async_execution"),
        context=context,
        output_json=ApiLinkContentExtractorOutput,
        markdown=config_data.get("markdown"),
        output_file=config_data.get("output_file"),
    )
    
    # Store config data for later use
    self._config_data = config_data
    self._hostname = hostname
