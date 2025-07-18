"""
Task Configuration Loader

Utility for loading task configurations from the centralized configs/tasks.yaml file.
This allows for easy management and updates of task settings without modifying code.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class TaskConfigLoader:
    """Loads and manages task configurations from centralized config file."""
    
    def __init__(self, config_file_path: Optional[str] = None):
        """Initialize the config loader.
        
        Args:
            config_file_path: Optional path to config file. Defaults to tasks.yaml in configs directory.
        """
        if config_file_path is None:
            # Default to tasks.yaml in the configs directory
            current_dir = Path(__file__).parent  # core directory
            ai_agents_root = current_dir.parent  # ai-agents directory
            config_file_path = ai_agents_root / "configs" / "tasks.yaml"
        
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
                
            logger.info(f"Loaded task configurations from {self.config_file_path}")
            
        except Exception as e:
            logger.error(f"Error loading config file {self.config_file_path}: {e}")
            self._config = {}
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self._load_config()
    
    def get_task_config(self, task_name: str) -> Dict[str, Any]:
        """Get configuration for a specific task.
        
        Args:
            task_name: Name of the task
            
        Returns:
            Task configuration dictionary
        """
        if not self._config:
            logger.warning("No configuration loaded")
            return {}
        
        # Tasks are stored directly at the root level
        task_config = self._config.get(task_name, {})
        
        if not task_config:
            logger.warning(f"No configuration found for task: {task_name}")
            return {}
        
        # Add the task name to the config if not present
        merged_config = task_config.copy()
        if 'name' not in merged_config:
            merged_config['name'] = task_name
        
        return merged_config
    
    def get_all_task_names(self) -> List[str]:
        """Get list of all configured task names.
        
        Returns:
            List of task names
        """
        if not self._config:
            return []
        
        # Filter out non-task entries (like global_settings, etc.)
        task_names = []
        for key, value in self._config.items():
            if isinstance(value, dict) and ('description' in value or 'expected_output' in value):
                task_names.append(key)
        
        return task_names
    
    def get_global_settings(self) -> Dict[str, Any]:
        """Get global settings.
        
        Returns:
            Global settings dictionary
        """
        if not self._config:
            return {}
        
        return self._config.get("global_settings", {})
    
    def update_task_config(self, task_name: str, config_updates: Dict[str, Any]) -> bool:
        """Update configuration for a specific task and save to file.
        
        Args:
            task_name: Name of the task
            config_updates: Dictionary of configuration updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._config:
                self._config = {}
            
            if task_name not in self._config:
                self._config[task_name] = {}
            
            # Update the configuration
            self._config[task_name].update(config_updates)
            
            # Save to file
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            logger.info(f"Updated configuration for task: {task_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating config for task {task_name}: {e}")
            return False
    
    def validate_task_config(self, task_name: str) -> Dict[str, Any]:
        """Validate task configuration and return validation results.
        
        Args:
            task_name: Name of the task to validate
            
        Returns:
            Validation results dictionary
        """
        config = self.get_task_config(task_name)
        
        if not config:
            return {
                "valid": False,
                "errors": [f"No configuration found for task: {task_name}"],
                "warnings": []
            }
        
        errors = []
        warnings = []
        
        # Required fields for tasks
        required_fields = ["description", "expected_output", "agent"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
            elif not config[field] or not isinstance(config[field], str):
                errors.append(f"Invalid value for required field: {field}")
        
        # Validate optional fields
        optional_fields = ["markdown", "config"]
        for field in optional_fields:
            if field in config:
                if field == "markdown" and not isinstance(config[field], (bool, str)):
                    warnings.append(f"Field '{field}' should be boolean or string")
                elif field == "config" and not isinstance(config[field], dict):
                    warnings.append(f"Field '{field}' should be a dictionary")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def format_task_description(self, task_name: str, **kwargs) -> str:
        """Format task description with provided parameters.
        
        Args:
            task_name: Name of the task
            **kwargs: Parameters to format the description
            
        Returns:
            Formatted task description
        """
        config = self.get_task_config(task_name)
        description = config.get("description", "")
        
        try:
            return description.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing parameter for task {task_name}: {e}")
            return description
        except Exception as e:
            logger.error(f"Error formatting task description for {task_name}: {e}")
            return description


# Global instance for easy access
_task_config_loader = None

def get_task_config_loader() -> TaskConfigLoader:
    """Get the global task configuration loader instance.
    
    Returns:
        TaskConfigLoader instance
    """
    global _task_config_loader
    if _task_config_loader is None:
        _task_config_loader = TaskConfigLoader()
    return _task_config_loader

def get_task_config(task_name: str) -> Dict[str, Any]:
    """Convenience function to get task configuration.
    
    Args:
        task_name: Name of the task
        
    Returns:
        Task configuration dictionary
    """
    return get_task_config_loader().get_task_config(task_name)

def reload_task_configs() -> None:
    """Convenience function to reload all task configurations."""
    global _task_config_loader
    if _task_config_loader:
        _task_config_loader.reload_config()

def format_task_description(task_name: str, **kwargs) -> str:
    """Convenience function to format task description with parameters.
    
    Args:
        task_name: Name of the task
        **kwargs: Parameters to format the description
        
    Returns:
        Formatted task description
    """
    return get_task_config_loader().format_task_description(task_name, **kwargs)
