"""
MCP Base Generator Task

Task for generating the base MCP server structure from templates.
"""

from crewai import Task
from typing import Dict, Any
from core.task_config_loader import TaskConfigLoader

class MCPBaseGeneratorTask(Task):
    """
    Task for generating base MCP server structure.
    """
    
    def __init__(self, website_url: str, server_name: str = None, template_path: str = None, **kwargs):
        # Load configuration from centralized config file
        task_loader = TaskConfigLoader()
        config_data = task_loader.get_task_config("mcp_base_generation")
          
        # Initialize the CrewAI Task with the loaded configuration
        # Format description and expected_output with provided parameters
        description_template = config_data.get("description", "")
        if not description_template:
            raise ValueError("No description found in task configuration")
        
        description = description_template.format(
            website_url=website_url, 
            server_name=server_name or "auto-generated from URL",
            template_path=template_path or "default MC-PEA template"
        )
        
        super().__init__(
            description=description,
            expected_output=config_data.get("expected_output", {}),
            # guardrail=validate_blog_content,
            async_execution=config_data.get("async_execution"),
            # output_json=ApiLinkDiscoveryOutput,
            markdown=config_data.get("markdown"),
            output_file=config_data.get("output_file"),
            **kwargs
        )
