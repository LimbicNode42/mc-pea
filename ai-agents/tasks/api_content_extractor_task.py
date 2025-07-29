from crewai import Task
from core.task_config_loader import TaskConfigLoader
from models.api_content_extractor_output import ApiLinkContentExtractorOutput
from models.api_flow_models import ChunkData

class ApiLinkContentExtractorTask(Task):
  def __init__(self, context: ChunkData):
    # Load configuration from centralized config file
    task_loader = TaskConfigLoader()
    config_data = task_loader.get_task_config("api_content_extraction")

    # Initialize the CrewAI Task with the loaded configuration
    description_template = config_data.get("description")
    if not description_template:
        raise ValueError("No description found in task configuration")

    # Format the description template with context output
    formatted_description = description_template.format(
        chunk=context.endpoints
    )
    
    super().__init__(
        description=formatted_description,
        expected_output=config_data.get("expected_output"),
        async_execution=config_data.get("async_execution"),
        output_json=ApiLinkContentExtractorOutput,
        markdown=config_data.get("markdown"),
    )

    # Store config data for later use
    self._config_data = config_data