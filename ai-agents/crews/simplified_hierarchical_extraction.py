"""
Simplified Hierarchical API Extraction

A simplified approach that works within CrewAI's hierarchical constraints
by having the manager handle chunking through delegation rather than
trying to pass data between pre-defined tasks.
"""

from crewai import Crew, Process, Task, Agent
from agents_workers.api_discovery_agent import ApiLinkDiscoveryAgent
from agents_workers.api_content_extractor_agent import ApiLinkContentExtractorAgent
from agents_managers.api_orchestrator_agent import ApiContentOrchestratorAgent
from tasks.api_link_discovery_task import ApiLinkDiscoveryTask
from typing import List, Dict, Any

class SimplifiedHierarchicalApiExtractionCrew:
    """
    Simplified hierarchical crew that uses the manager to coordinate
    discovery and then delegate extraction work dynamically.
    """
    
    def __init__(self, website_url: str, num_extractors: int = 3):
        self.website_url = website_url
        self.num_extractors = num_extractors
        
        # Initialize agents
        self.discovery_agent = ApiLinkDiscoveryAgent(website_url=website_url)
        self.extractor_agents = [
            ApiLinkContentExtractorAgent() 
            for _ in range(num_extractors)
        ]
        self.manager_agent = ApiContentOrchestratorAgent()
        
        # Create a single high-level task that the manager can break down
        self.main_task = Task(
            description=f"""
            Complete API documentation extraction for {website_url}:
            
            1. First, discover all API endpoints from the website
            2. Then, chunk the discovered endpoints into manageable groups
            3. Finally, extract detailed information from each chunk using parallel processing
            
            Use the discovery agent to find all endpoints, then coordinate the content
            extraction agents to process the endpoints in chunks for maximum efficiency.
            
            The final output should combine discovery results with detailed extraction
            data from all endpoint chunks.
            """,
            expected_output="""
            A comprehensive API documentation dataset containing:
            - Complete discovery results with all found endpoints
            - Detailed extraction data from all endpoint chunks
            - Processing metadata (chunks processed, total endpoints, etc.)
            """,
            async_execution=False
        )
        
        # All agents available to the manager
        self.all_agents = [self.discovery_agent] + self.extractor_agents
        
        # Create the crew with hierarchical process
        self.crew = Crew(
            agents=self.all_agents,
            tasks=[self.main_task],
            process=Process.hierarchical,
            manager_agent=self.manager_agent,
            verbose=True
        )
    
    def execute(self):
        """Execute the simplified hierarchical extraction workflow."""
        try:
            print(f"🚀 Starting simplified hierarchical API extraction for {self.website_url}")
            print(f"👥 Manager: {self.manager_agent.role}")
            print(f"🔍 Discovery Agent: {self.discovery_agent.role}")
            print(f"⚙️ Content Extractors: {len(self.extractor_agents)} agents")
            print(f"📋 Single high-level task for manager to coordinate")
            
            # Execute the crew - manager will break down the task and delegate
            result = self.crew.kickoff()
            
            print(f"✅ Simplified hierarchical extraction completed")
            return result
            
        except Exception as e:
            print(f"❌ Error in simplified hierarchical extraction: {e}")
            raise

    def get_crew_info(self):
        """Get information about the crew composition."""
        return {
            "process_type": "simplified_hierarchical",
            "manager": self.manager_agent.role,
            "total_agents": len(self.all_agents),
            "discovery_agents": 1,
            "extraction_agents": len(self.extractor_agents),
            "website_url": self.website_url,
            "approach": "manager_delegates_to_specialists"
        }
