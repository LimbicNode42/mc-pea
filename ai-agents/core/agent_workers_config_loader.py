"""
Agent Configuration Loader

Utility for loading agent configurations from the centralized configs/agent_workers.yaml file.
This allows for easy management and updates of agent settings without modifying code.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class AgentConfigLoader:
    """Loads and manages agent configurations from centralized config file."""
    
    def __init__(self, config_file_path: Optional[str] = None):
        """Initialize the config loader.
        
        Args:
            config_file_path: Optional path to config file. Defaults to agent_workers.yaml in configs directory.
        """
        if config_file_path is None:
            # Default to agent_workers.yaml in the configs directory
            current_dir = Path(__file__).parent  # core directory
            ai_agents_root = current_dir.parent  # ai-agents directory
            config_file_path = ai_agents_root / "configs" / "agent_workers.yaml"
        
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
                
            logger.info(f"Loaded agent configurations from {self.config_file_path}")
            
        except Exception as e:
            logger.error(f"Error loading config file {self.config_file_path}: {e}")
            self._config = {}
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self._load_config()
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent configuration dictionary
        """
        if not self._config:
            logger.warning("No configuration loaded")
            return {}
        
        # In the new YAML format, agents are stored directly at the root level
        agent_config = self._config.get(agent_name, {})
        
        if not agent_config:
            logger.warning(f"No configuration found for agent: {agent_name}")
            return {}
        
        # Add the agent name to the config if not present
        merged_config = agent_config.copy()
        if 'name' not in merged_config:
            merged_config['name'] = agent_name
        
        return merged_config
    
    def get_all_agent_names(self) -> List[str]:
        """Get list of all configured agent names.
        
        Returns:
            List of agent names
        """
        if not self._config:
            return []
        
        # In the new YAML format, filter out non-agent entries (like global_settings, etc.)
        agent_names = []
        for key, value in self._config.items():
            if isinstance(value, dict) and ('role' in value or 'goal' in value):
                agent_names.append(key)
        
        return agent_names
    
    def get_global_settings(self) -> Dict[str, Any]:
        """Get global settings.
        
        Returns:
            Global settings dictionary
        """
        if not self._config:
            return {}
        
        return self._config.get("global_settings", {})
    
    def get_mcp_standards(self) -> Dict[str, Any]:
        """Get MCP standards configuration.
        
        Returns:
            MCP standards dictionary
        """
        if not self._config:
            return {}
        
        return self._config.get("mcp_standards", {})
    
    def get_deployment_config(self, target: str = "kubernetes") -> Dict[str, Any]:
        """Get deployment configuration for specific target.
        
        Args:
            target: Deployment target (kubernetes, docker, serverless)
            
        Returns:
            Deployment configuration dictionary
        """
        if not self._config:
            return {}
        
        deployment_targets = self._config.get("deployment_targets", {})
        return deployment_targets.get(target, {})
    
    def update_agent_config(self, agent_name: str, config_updates: Dict[str, Any]) -> bool:
        """Update configuration for a specific agent and save to file.
        
        Args:
            agent_name: Name of the agent
            config_updates: Dictionary of configuration updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._config:
                self._config = {}
            
            if agent_name not in self._config:
                self._config[agent_name] = {}
            
            # Update the configuration
            self._config[agent_name].update(config_updates)
            
            # Save to file
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            logger.info(f"Updated configuration for agent: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating config for agent {agent_name}: {e}")
            return False
    
    def validate_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Validate agent configuration and return validation results.
        
        Args:
            agent_name: Name of the agent to validate
            
        Returns:
            Validation results dictionary
        """
        config = self.get_agent_config(agent_name)
        
        if not config:
            return {
                "valid": False,
                "errors": [f"No configuration found for agent: {agent_name}"],
                "warnings": []
            }
        
        errors = []
        warnings = []
        
        # Required fields
        required_fields = ["name", "role", "goal", "backstory"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
            elif not config[field] or not isinstance(config[field], str):
                errors.append(f"Invalid value for required field: {field}")
        
        # Validate MCP dependencies
        mcp_deps = config.get("mcp_dependencies", [])
        if not isinstance(mcp_deps, list):
            errors.append("mcp_dependencies must be a list")
        else:
            for i, dep in enumerate(mcp_deps):
                if not isinstance(dep, dict):
                    errors.append(f"MCP dependency {i} must be a dictionary")
                    continue
                
                dep_required = ["name", "package", "type"]
                for field in dep_required:
                    if field not in dep:
                        errors.append(f"MCP dependency {i} missing field: {field}")
        
        # Deployment settings
        if not config.get("deployment_friendly"):
            warnings.append("Agent not marked as deployment friendly")
        
        if not config.get("kubernetes_ready"):
            warnings.append("Agent not marked as Kubernetes ready")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


# Global instance for easy access
_config_loader = None

def get_config_loader() -> AgentConfigLoader:
    """Get the global configuration loader instance.
    
    Returns:
        AgentConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = AgentConfigLoader()
    return _config_loader

def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """Convenience function to get agent configuration.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        Agent configuration dictionary
    """
    return get_config_loader().get_agent_config(agent_name)

def reload_configs() -> None:
    """Convenience function to reload all configurations."""
    global _config_loader
    if _config_loader:
        _config_loader.reload_config()
