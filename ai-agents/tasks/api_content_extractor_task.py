import agentops
from crewai import Task, TaskOutput
from typing import Tuple, Any
from core.task_config_loader import TaskConfigLoader
from models.api_content_extractor_output_v2 import ApiContentExtractorOutput
from models.api_flow_models import ChunkData
from utils.schema_helpers import get_schema_prompt

# @agentops.task(name="api_content_extractor_task")
class ApiLinkContentExtractorTask(Task):
    def __init__(self, context: ChunkData):
        # Load configuration from centralized config file
        task_loader = TaskConfigLoader()
        config_data = task_loader.get_task_config("api_content_extraction")

        # Initialize the CrewAI Task with the loaded configuration
        description_template = config_data.get("description")
        if not description_template:
            raise ValueError("No description found in task configuration")

        # Add schema guidance to description
        schema_guidance = get_schema_prompt()
        
        # Convert endpoints to string safely for description
        import json
        endpoints_str = json.dumps(context.endpoints, indent=2)
        
        # Build description without using .format() to avoid brace conflicts
        formatted_description = f"{description_template}\n\nInput JSON: {endpoints_str}\n\n{schema_guidance}"
        
        super().__init__(
            description=formatted_description,
            expected_output=config_data.get("expected_output"),
            guardrail=validate_api_content_extraction,
            async_execution=config_data.get("async_execution"),
            output_json=ApiContentExtractorOutput,
            markdown=config_data.get("markdown"),
        )

        # Store config data for later use
        self._config_data = config_data

# @agentops.guardrail(name="api_content_extractor_task")
def validate_api_content_extraction(result: TaskOutput) -> Tuple[bool, Any]:
    """Fast validation focusing on essential structure only."""
    
    # Quick type checks
    if not hasattr(result, 'json_dict') or not result.json_dict:
        return False, "Missing json_dict output"
    
    data = result.json_dict
    if not isinstance(data, dict):
        return False, "Output is not a dictionary"
    
    if 'ocs' not in data:
        return False, "Missing 'ocs' field"
    
    categories = data['ocs']
    if not isinstance(categories, list) or len(categories) == 0:
        return False, "Empty or invalid categories"
    
    # Quick endpoint count check
    total_endpoints = 0
    for cat in categories:
        if isinstance(cat, dict) and 'ces' in cat:
            endpoints = cat['ces']
            if isinstance(endpoints, list):
                total_endpoints += len(endpoints)
    
    if total_endpoints == 0:
        return False, "No endpoints found"
    
    print(f"✅ Validation passed: {len(categories)} categories, {total_endpoints} endpoints")
    return True, data