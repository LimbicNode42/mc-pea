"""
Hierarchical API Documentation Extraction Crew

This crew uses CrewAI's hierarchical process to automatically coordinate:
- 1 Discovery Agent (finds all API endpoints)
- Multiple Content Extractor Agents (process endpoint chunks in parallel)
- 1 Manager Agent (orchestrates, delegates, and reviews)

The manager handles all coordination, so agents don't need custom coordination logic.
"""

from crewai import Crew, Process
from agents_workers.api_discovery_agent import ApiLinkDiscoveryAgent
from agents_workers.api_content_extractor_agent import ApiLinkContentExtractorAgent
from agents_managers.api_orchestrator_agent import ApiContentOrchestratorAgent
from tasks.api_link_discovery_task import ApiLinkDiscoveryTask
from tasks.api_content_extractor_task import ApiLinkContentExtractorTask

class HierarchicalApiExtractionCrew:
    """
    Hierarchical crew for large-scale API documentation extraction.
    Uses CrewAI's built-in manager capabilities for coordination.
    """
    
    def __init__(self, website_url: str, num_extractors: int = 3):
        self.website_url = website_url
        self.num_extractors = num_extractors
        
        # Initialize agents
        self.discovery_agent = ApiLinkDiscoveryAgent(website_url=website_url)
        
        # Create multiple content extractor agents for parallel processing
        self.extractor_agents = [
            ApiLinkContentExtractorAgent() 
            for _ in range(num_extractors)
        ]
        
        # Manager agent (converted from orchestrator)
        self.manager_agent = ApiContentOrchestratorAgent()
        
        # Combine all agents
        self.agents = [self.discovery_agent] + self.extractor_agents
        
        # Initialize tasks
        self.discovery_task = ApiLinkDiscoveryTask(website_url=self.website_url)

        # Note: In hierarchical process, we define the types of tasks available
        # but the manager will create and assign specific instances as needed
        self.tasks = [self.discovery_task]
        
        # Create the crew with hierarchical process
        self.crew = Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=self.manager_agent,  # Use custom manager agent
            verbose=True
        )
    
    def execute(self):
        """Execute the hierarchical extraction workflow."""
        try:
            print(f"🚀 Starting hierarchical API extraction for {self.hostname}")
            print(f"👥 Manager: {self.manager_agent.role}")
            print(f"🔍 Discovery Agent: {self.discovery_agent.role}")
            print(f"⚙️ Content Extractors: {len(self.extractor_agents)} agents")
            
            # Execute the crew - manager handles all coordination
            result = self.crew.kickoff()
            
            print(f"✅ Hierarchical extraction completed")
            return result
            
        except Exception as e:
            print(f"❌ Error in hierarchical extraction: {e}")
            raise

    def get_crew_info(self):
        """Get information about the crew composition."""
        return {
            "process_type": "hierarchical",
            "manager": self.manager_agent.role,
            "agents": [agent.role for agent in self.agents],
            "num_extractors": self.num_extractors,
            "hostname": self.hostname
        }

# Factory function for easy crew creation
def create_hierarchical_extraction_crew(hostname: str, num_extractors: int = 3) -> HierarchicalApiExtractionCrew:
    """
    Create a hierarchical API extraction crew.
    
    Args:
        hostname: The API hostname to extract documentation from
        num_extractors: Number of parallel content extractor agents
        
    Returns:
        Configured hierarchical crew ready for execution
    """
    return HierarchicalApiExtractionCrew(hostname, num_extractors)
