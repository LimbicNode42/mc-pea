from crewai import Crew
from core.crew_config_loader import CrewConfigLoader
from agents.link_discovery_agent import ApiLinkDiscoveryAgent
from agents.link_content_extractor_agent import ApiLinkContentExtractorAgent
from tasks.information_gathering import ApiLinkDiscoveryTask, ApiLinkContentExtractorTask

class DataEntry(Crew):
  def __init__(self, website_url: str, depth: int = 3):
    # Load configuration from centralized config file
    crew_loader = CrewConfigLoader()
    config_data = crew_loader.get_crew_config("data_entry")
    
    # Create agents based on configuration
    discovery_agent = ApiLinkDiscoveryAgent(website_url=website_url)
    extractor_agent = ApiLinkContentExtractorAgent(website_url=website_url)
    
    # Create tasks based on configuration
    discovery_task = ApiLinkDiscoveryTask(website_url=website_url, depth=depth)
    extractor_task = ApiLinkContentExtractorTask()
    
    # Assign agents to tasks
    discovery_task.agent = discovery_agent
    extractor_task.agent = extractor_agent
    
    # Set up task dependencies - extractor task uses discovery task output as context
    extractor_task.context = [discovery_task]
    
    # Initialize the CrewAI Crew with actual instances
    super().__init__(
        agents=[discovery_agent, extractor_agent],
        tasks=[discovery_task, extractor_task],
        process=config_data.get("process"),
        verbose=config_data.get("verbose", False),
        memory=config_data.get("memory", True),
        output_log_file="data_entry.json"
    )
    
    # Store config data for later use
    self._config_data = config_data