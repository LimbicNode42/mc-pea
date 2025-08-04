"""
MCP API Integration Task

Task for integrating extracted API usage details into the generated MCP server.
"""

from crewai import Task
from typing import Dict, Any, List
from core.task_config_loader import TaskConfigLoader

class MCPAPIIntegrationTask(Task):
    """
    Task for integrating API extraction results into the MCP server.
    """
    
    def __init__(self, website_url: str, server_name: str, mcp_server_path: str, extraction_results: List[Dict[str, Any]], **kwargs):
        # Load configuration from centralized config file
        task_loader = TaskConfigLoader()
        config_data = task_loader.get_task_config("mcp_api_integration")
          
        # Initialize the CrewAI Task with the loaded configuration
        # Format description and expected_output with provided parameters
        description_template = config_data.get("description", "")
        if not description_template:
            raise ValueError("No description found in task configuration")
        
        description = description_template.format(
            website_url=website_url,
            server_name=server_name,
            mcp_server_path=mcp_server_path,
            total_extraction_chunks=len(extraction_results),
            successful_chunks=len([r for r in extraction_results if 'error' not in r])
        )
        
        # Format expected output
        expected_output_template = config_data.get("expected_output", "")
        expected_output = expected_output_template.format(
            server_name=server_name,
            mcp_server_path=mcp_server_path
        )
        
        super().__init__(
            description=description,
            expected_output=expected_output,
            # guardrail=validate_blog_content,
            async_execution=config_data.get("async_execution"),
            # output_json=MCPAPIIntegrationOutput,
            markdown=config_data.get("markdown"),
            output_file=config_data.get("output_file"),
            **kwargs
        )
        
        # Store task-specific data for agent access using object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, 'website_url', website_url)
        object.__setattr__(self, 'server_name', server_name)
        object.__setattr__(self, 'mcp_server_path', mcp_server_path)
        object.__setattr__(self, 'extraction_results', extraction_results)
