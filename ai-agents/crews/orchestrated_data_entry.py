"""
Orchestrated Data Entry Crew

This crew uses the multi-agent orchestration approach for processing large-scale
API documentation through coordinated parallel extraction.
"""

from crewai import Crew
from typing import Dict, Any

from core.crew_config_loader import CrewConfigLoader
from agents.api_discovery_agent import ApiLinkDiscoveryAgent
from agents.api_orchestrator_agent import ApiContentOrchestratorAgent
from agents.api_content_extractor_agent import ApiLinkContentExtractorAgent
from tasks.link_discovery_task import ApiLinkDiscoveryTask
from tasks.orchestrated_link_content_extractor_task import OrchestratedApiLinkContentExtractorTask
from tasks.link_content_extractor_task import ApiLinkContentExtractorTask

class OrchestratedDataEntryCrew(Crew):
    def __init__(self, website_url: str, hostname: str, depth: int = 3):
        # Load crew configuration
        crew_loader = CrewConfigLoader()
        config_data = crew_loader.get_crew_config("orchestrated_data_entry")

        # Create agents
        link_discovery_agent = ApiLinkDiscoveryAgent(website_url=website_url)
        orchestrator_agent = ApiContentOrchestratorAgent()
        # content_extractor_agent = ApiLinkContentExtractorAgent()

        # Create tasks with proper agent assignments
        link_discovery_task = ApiLinkDiscoveryTask(website_url, depth)
        link_discovery_task.agent = link_discovery_agent
        
        orchestrated_content_extractor_task = OrchestratedApiLinkContentExtractorTask(
            hostname, 
            context=[link_discovery_task]
        )
        orchestrated_content_extractor_task.agent = orchestrator_agent

        # api_content_extractor_task = ApiLinkContentExtractorTask(
        #     hostname=hostname, 
        #     context=[orchestrated_content_extractor_task]
        # )
        # api_content_extractor_task.agent = content_extractor_agent

        # Initialize the crew
        super().__init__(
            tasks=[
                link_discovery_task,
                orchestrated_content_extractor_task,
                # api_content_extractor_task
            ],
            agents=[
                link_discovery_agent,
                orchestrator_agent,
                # content_extractor_agent
            ],
            process=config_data.get("process", "sequential"),
            memory=config_data.get("memory", False),
            cache=config_data.get("cache", False),
            verbose=config_data.get("verbose", True),
            output_log_file=config_data.get("output_log_file", "orchestrated_data_entry.json")
        )

        # Store parameters
        self._website_url = website_url
        self._hostname = hostname
        self._depth = depth
        self._config_data = config_data

    def kickoff(self) -> Dict[str, Any]:
        """Execute the orchestrated data entry workflow."""
        try:
            print(f"🚀 Starting orchestrated data entry for {self._website_url}")
            print(f"📊 Processing with depth={self._depth}, hostname={self._hostname}")
            
            # Execute the crew workflow
            result = super().kickoff()
            
            print(f"✅ Orchestrated data entry completed successfully")
            return result
            
        except Exception as e:
            print(f"❌ Error in orchestrated data entry: {e}")
            return {
                "error": str(e),
                "website_url": self._website_url,
                "hostname": self._hostname
            }
