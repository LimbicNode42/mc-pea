from crewai import Crew
from core.crew_config_loader import get_crew_config

class DataEntry(Crew):
  def __init__(self):
    # Load configuration from centralized config file
    config_data = get_crew_config("data_entry")
      
    # Initialize the CrewAI Agent with the loaded configuration
    super().__init__(
        tasks=config_data.get("tasks"),
        agents=config_data.get("agents"),
        process=config_data.get("process"),
        verbose=config_data.get("verbose", False),
        memory=config_data.get("memory", True),
    )
    
    # Store config data for later use
    self._config_data = config_data