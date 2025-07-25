"""
Orchestrated API Link Content Extractor Task

This task coordinates multiple agents to process large-scale API documentation
by partitioning work and enabling parallel processing while maintaining consistency.
"""

from crewai import Task
from typing import List
from core.task_config_loader import TaskConfigLoader
from agents.content_orchestrator_agent import ApiContentOrchestratorAgent
from models.link_content_extractor_output import ApiLinkContentExtractorOutput

class OrchestratedApiLinkContentExtractorTask(Task):
    def __init__(self, hostname: str, context: List[Task]):
        # Load configuration from centralized config file
        task_loader = TaskConfigLoader()
        # Use the existing config but modify the description for orchestration
        config_data = task_loader.get_task_config("api_link_content_extractor")

        # Extract context output from the first task (LinkDiscoveryTask)
        first_context_task = context[0]
        context_output = ""
        if hasattr(first_context_task, 'output') and hasattr(first_context_task.output, 'raw'):
            context_output = first_context_task.output.raw

        # Create orchestrated description
        orchestrated_description = f"""
ORCHESTRATED API CONTENT EXTRACTION TASK

You are the master orchestrator coordinating multiple specialized content extraction agents to process the complete API documentation from {hostname}.

CONTEXT FROM PREVIOUS TASK:
{context_output}

YOUR COORDINATION RESPONSIBILITIES:

1. PARTITION WORK:
   - Parse the link discovery output from the context
   - Partition endpoints into chunks of 5 endpoints each
   - Maintain category organization and ordering information
   - Create metadata for chunk tracking and result assembly

2. COORDINATE AGENTS:
   - Delegate each chunk to a specialized ApiEndpointContentExtractorAgent
   - Ensure each agent receives:
     * Clear chunk boundaries (5 endpoints max)
     * Category context and metadata
     * Strict schema requirements and golden examples
     * Hostname and URL construction instructions

3. MANAGE OUTPUT ASSEMBLY:
   - Collect results from all specialized agents
   - Merge chunk results back into category structure
   - Maintain original discovery task ordering
   - Ensure final output follows ApiLinkContentExtractorOutput schema exactly

4. ENSURE CONSISTENCY:
   - Provide identical templates and examples to all agents
   - Validate that all agents follow the same output schema
   - Handle any agent failures gracefully with empty but valid structures

CRITICAL REQUIREMENTS:
- Process ALL endpoints from the link discovery context
- Maintain exact category and endpoint ordering from discovery task
- Output must conform exactly to ApiLinkContentExtractorOutput schema
- Each endpoint must include: en, ed, em, ep, ecp, esu, eh, epp, eqp, ebp, erc, ere
- Never lose or skip endpoints due to chunking
- Coordinate efficiently to maximize parallel processing benefits

Begin orchestration now by partitioning the discovery output and coordinating your specialized agents.
"""

        # Initialize the CrewAI Task with orchestration-specific configuration
        super().__init__(
            description=orchestrated_description,
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

    def execute(self):
        """Execute the orchestrated content extraction."""
        try:
            # Step 1: Partition the work
            chunks = self.orchestrator_agent.partition_endpoints(
                self._context_output, 
                chunk_size=5
            )
            
            print(f"Created {len(chunks)} chunks for processing")
            
            # Step 2: Coordinate extraction across agents
            chunk_results = self.orchestrator_agent.coordinate_extraction(
                chunks, 
                self._hostname
            )
            
            print(f"Processed {len(chunk_results)} chunk results")
            
            # Step 3: Merge results into final output
            final_output = self.orchestrator_agent.merge_chunk_outputs(chunk_results)
            
            print(f"Final output contains {len(final_output.get('ocs', []))} categories")
            
            return final_output
            
        except Exception as e:
            print(f"Error in orchestrated execution: {e}")
            # Return empty but valid structure
            return {
                'ocs': []
            }
