"""
Orchestrated API Link Content Extractor Task

This task coordinates multiple agents to process large-scale API documentation
by partitioning work and enabling parallel processing while maintaining consistency.
"""

from crewai import Task
from typing import List
from core.task_config_loader import TaskConfigLoader
from models.link_content_extractor_output import ApiLinkContentExtractorOutput

class OrchestratedApiLinkContentExtractorTask(Task):
    def __init__(self, hostname: str, context: List[Task]):
        # Load configuration from centralized config file
        task_loader = TaskConfigLoader()
        # Use the existing config but modify the description for orchestration
        config_data = task_loader.get_task_config("api_orchestrator")

        # Extract context output from the first task (LinkDiscoveryTask)
        first_context_task = context[0]
        context_output = ""
        if hasattr(first_context_task, 'output') and hasattr(first_context_task.output, 'raw'):
            context_output = first_context_task.output.raw

        description_template = config_data.get("description", "")
        if not description_template:
            raise ValueError("No description found in task configuration")

        description = description_template.format(
            hostname=hostname, 
            context_output=context_output
        )

        # Initialize the CrewAI Task with orchestration-specific configuration
        super().__init__(
            description=description,
            expected_output=config_data.get("expected_output"),
            async_execution=config_data.get("async_execution"),
            context=context,
            output_json=ApiLinkContentExtractorOutput,
            markdown=config_data.get("markdown"),
            output_file=config_data.get("output_file")
            # Note: agent will be assigned by the crew
        )
        
        # Store config data and parameters for later use
        self._config_data = config_data
        self._hostname = hostname
        self._context_output = context_output

    # def execute(self):
    #     """Execute the orchestrated content extraction."""
    #     try:
    #         # Step 1: Partition the work
    #         chunks = self.orchestrator_agent.partition_endpoints(
    #             self._context_output, 
    #             chunk_size=5
    #         )
            
    #         print(f"Created {len(chunks)} chunks for processing")
            
    #         # Step 2: Coordinate extraction across agents
    #         chunk_results = self.orchestrator_agent.coordinate_extraction(
    #             chunks, 
    #             self._hostname
    #         )
            
    #         print(f"Processed {len(chunk_results)} chunk results")
            
    #         # Step 3: Merge results into final output
    #         final_output = self.orchestrator_agent.merge_chunk_outputs(chunk_results)
            
    #         print(f"Final output contains {len(final_output.get('ocs', []))} categories")
            
    #         return final_output
            
    #     except Exception as e:
    #         print(f"Error in orchestrated execution: {e}")
    #         # Return empty but valid structure
    #         return {
    #             'ocs': []
    #         }
