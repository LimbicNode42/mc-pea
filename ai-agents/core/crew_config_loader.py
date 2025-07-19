"""
Crew Configuration Loader

Utility for loading crew configurations from the centralized configs/crews.yaml file.
This allows for easy management and updates of crew settings without modifying code.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class CrewConfigLoader:
    """Loads and manages crew configurations from centralized config file."""
    
    def __init__(self, config_file_path: Optional[str] = None):
        """Initialize the config loader.
        
        Args:
            config_file_path: Optional path to config file. Defaults to crews.yaml in configs directory.
        """
        if config_file_path is None:
            # Default to crews.yaml in the configs directory
            current_dir = Path(__file__).parent  # core directory
            ai_agents_root = current_dir.parent  # ai-agents directory
            config_file_path = ai_agents_root / "configs" / "crews.yaml"
        
        self.config_file_path = Path(config_file_path)
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from the YAML file."""
        try:
            if not self.config_file_path.exists():
                logger.error(f"Config file not found: {self.config_file_path}")
                self._config = {}
                return
            
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
                
            logger.info(f"Loaded crew configurations from {self.config_file_path}")
            
        except Exception as e:
            logger.error(f"Error loading config file {self.config_file_path}: {e}")
            self._config = {}
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self._load_config()
    
    def get_crew_config(self, crew_name: str) -> Dict[str, Any]:
        """Get configuration for a specific crew.
        
        Args:
            crew_name: Name of the crew
            
        Returns:
            Crew configuration dictionary
        """
        if not self._config:
            logger.warning("No configuration loaded")
            return {}
        
        # Crews are stored directly at the root level
        crew_config = self._config.get(crew_name, {})
        
        if not crew_config:
            logger.warning(f"No configuration found for crew: {crew_name}")
            return {}
        
        # Add the crew name to the config if not present
        merged_config = crew_config.copy()
        if 'name' not in merged_config:
            merged_config['name'] = crew_name
        
        return merged_config
    
    def get_all_crew_names(self) -> List[str]:
        """Get list of all configured crew names.
        
        Returns:
            List of crew names
        """
        if not self._config:
            return []
        
        # Filter out non-crew entries (like global_settings, etc.)
        crew_names = []
        for key, value in self._config.items():
            if isinstance(value, dict) and ('tasks' in value or 'agents' in value or 'process' in value):
                crew_names.append(key)
        
        return crew_names
    
    def get_global_settings(self) -> Dict[str, Any]:
        """Get global settings.
        
        Returns:
            Global settings dictionary
        """
        if not self._config:
            return {}
        
        return self._config.get("global_settings", {})
    
    def update_crew_config(self, crew_name: str, config_updates: Dict[str, Any]) -> bool:
        """Update configuration for a specific crew and save to file.
        
        Args:
            crew_name: Name of the crew
            config_updates: Dictionary of configuration updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._config:
                self._config = {}
            
            # Update the crew configuration
            if crew_name not in self._config:
                self._config[crew_name] = {}
            
            self._config[crew_name].update(config_updates)
            
            # Save to file
            return self._save_config()
            
        except Exception as e:
            logger.error(f"Error updating crew config for {crew_name}: {e}")
            return False
    
    def add_crew_config(self, crew_name: str, crew_config: Dict[str, Any]) -> bool:
        """Add a new crew configuration.
        
        Args:
            crew_name: Name of the crew
            crew_config: Complete crew configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._config:
                self._config = {}
            
            self._config[crew_name] = crew_config
            
            # Save to file
            return self._save_config()
            
        except Exception as e:
            logger.error(f"Error adding crew config for {crew_name}: {e}")
            return False
    
    def remove_crew_config(self, crew_name: str) -> bool:
        """Remove a crew configuration.
        
        Args:
            crew_name: Name of the crew to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._config or crew_name not in self._config:
                logger.warning(f"Crew {crew_name} not found in configuration")
                return False
            
            del self._config[crew_name]
            
            # Save to file
            return self._save_config()
            
        except Exception as e:
            logger.error(f"Error removing crew config for {crew_name}: {e}")
            return False
    
    def _save_config(self) -> bool:
        """Save configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            self.config_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, sort_keys=True)
            
            logger.info(f"Saved crew configuration to {self.config_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config file {self.config_file_path}: {e}")
            return False
    
    def get_crew_tasks(self, crew_name: str) -> List[str]:
        """Get list of tasks for a specific crew.
        
        Args:
            crew_name: Name of the crew
            
        Returns:
            List of task names
        """
        crew_config = self.get_crew_config(crew_name)
        if not crew_config:
            return []
        
        tasks = crew_config.get('tasks', '')
        if isinstance(tasks, str):
            # Handle multi-line string format
            return [task.strip() for task in tasks.strip().split('\n') if task.strip()]
        elif isinstance(tasks, list):
            return tasks
        else:
            return []
    
    def get_crew_agents(self, crew_name: str) -> List[str]:
        """Get list of agents for a specific crew.
        
        Args:
            crew_name: Name of the crew
            
        Returns:
            List of agent names
        """
        crew_config = self.get_crew_config(crew_name)
        if not crew_config:
            return []
        
        agents = crew_config.get('agents', '')
        if isinstance(agents, str):
            # Handle multi-line string format
            return [agent.strip() for agent in agents.strip().split('\n') if agent.strip()]
        elif isinstance(agents, list):
            return agents
        else:
            return []
    
    def get_crew_process(self, crew_name: str) -> str:
        """Get process type for a specific crew.
        
        Args:
            crew_name: Name of the crew
            
        Returns:
            Process type (sequential, hierarchical, etc.)
        """
        crew_config = self.get_crew_config(crew_name)
        if not crew_config:
            return "sequential"  # Default process type
        
        process = crew_config.get('process', 'sequential')
        if isinstance(process, str):
            return process.strip()
        else:
            return str(process)
    
    def is_crew_verbose(self, crew_name: str) -> bool:
        """Check if crew should run in verbose mode.
        
        Args:
            crew_name: Name of the crew
            
        Returns:
            True if verbose mode enabled
        """
        crew_config = self.get_crew_config(crew_name)
        if not crew_config:
            return False
        
        verbose = crew_config.get('verbose', False)
        if isinstance(verbose, str):
            return verbose.lower().strip() in ('true', 'yes', '1')
        else:
            return bool(verbose)
    
    def is_crew_memory_enabled(self, crew_name: str) -> bool:
        """Check if crew has memory enabled.
        
        Args:
            crew_name: Name of the crew
            
        Returns:
            True if memory is enabled
        """
        crew_config = self.get_crew_config(crew_name)
        if not crew_config:
            return False
        
        memory = crew_config.get('memory', False)
        if isinstance(memory, str):
            return memory.lower().strip() in ('true', 'yes', '1')
        else:
            return bool(memory)
