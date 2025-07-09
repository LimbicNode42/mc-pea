"""
Configuration management for MC-PEA AI Agents.
Supports dynamic configuration updates and hot reloading.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class AnthropicConfig:
    """Configuration for Anthropic API settings based on CrewAI LLM parameters."""
    # Core parameters
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4000
    temperature: float = 0.7
    top_p: float = 0.9
    timeout: int = 60
    max_retries: int = 3
    
    # Advanced parameters (matching CrewAI LLM class)
    n: int = 1  # Number of completions to generate
    stop: Optional[list[str]] = None  # Stop sequences
    presence_penalty: float = 0.0  # Penalty for presence of tokens (-2.0 to 2.0)
    frequency_penalty: float = 0.0  # Penalty for frequency of tokens (-2.0 to 2.0) 
    seed: Optional[int] = None  # Random seed for reproducible outputs
    logprobs: Optional[int] = None  # Number of log probabilities to return
    top_logprobs: Optional[int] = None  # Number of top log probabilities per token
    logit_bias: Optional[Dict[int, float]] = None  # Bias for specific tokens
    
    # API configuration
    base_url: Optional[str] = None  # Custom API base URL
    api_base: Optional[str] = None  # Alternative to base_url
    api_version: Optional[str] = None  # API version
    api_key: Optional[str] = None  # Override API key
    
    # Response configuration
    stream: bool = False  # Enable streaming responses
    reasoning_effort: Optional[str] = None  # Reasoning effort level for Claude models (none, low, medium, high)
    
    # Function calling configuration
    max_completion_tokens: Optional[int] = None  # Alternative to max_tokens
    response_format: Optional[dict] = None  # Format for the response


@dataclass
class AgentConfig:
    """Base configuration for AI agents."""
    max_iterations: int = 5
    verbose: bool = True
    allow_delegation: bool = False
    memory: bool = True
    step_callback: Optional[str] = None


@dataclass
class WorkflowConfig:
    """Configuration for workflow execution."""
    parallel_execution: bool = False
    max_concurrent_tasks: int = 3
    timeout_minutes: int = 30
    auto_retry: bool = True
    retry_attempts: int = 2
    checkpoint_enabled: bool = True


@dataclass
class ValidationConfig:
    """Configuration for MCP validation settings."""
    auto_validate: bool = True
    strict_mode: bool = False
    check_typescript: bool = True
    check_mcp_compliance: bool = True
    run_tests: bool = True
    performance_check: bool = False


@dataclass
class GenerationConfig:
    """Configuration for code generation settings."""
    create_tests: bool = True
    create_docs: bool = True
    create_dockerfile: bool = True
    use_templates: bool = True
    template_path: str = "../templates/mcp-server-template"
    output_directory: str = "./output"
    overwrite_existing: bool = False


@dataclass
class UIConfig:
    """Configuration for Streamlit UI settings."""
    theme: str = "auto"  # auto, light, dark
    layout: str = "wide"  # centered, wide
    sidebar_state: str = "expanded"  # auto, expanded, collapsed
    show_advanced_options: bool = False
    auto_refresh_interval: int = 5  # seconds
    enable_hot_reload: bool = True


@dataclass
class MCPEAConfig:
    """Main configuration class containing all settings."""
    anthropic: AnthropicConfig
    agent: AgentConfig
    workflow: WorkflowConfig
    validation: ValidationConfig
    generation: GenerationConfig
    ui: UIConfig
    
    # Metadata
    version: str = "1.0.0"
    last_updated: str = ""
    config_file_path: str = ""

    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


class ConfigManager:
    """Manages configuration loading, saving, and hot reloading."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config: MCPEAConfig = self.load_config()
        self._callbacks = []
    
    def load_config(self) -> MCPEAConfig:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                # Create config objects from loaded data
                config = MCPEAConfig(
                    anthropic=AnthropicConfig(**data.get('anthropic', {})),
                    agent=AgentConfig(**data.get('agent', {})),
                    workflow=WorkflowConfig(**data.get('workflow', {})),
                    validation=ValidationConfig(**data.get('validation', {})),
                    generation=GenerationConfig(**data.get('generation', {})),
                    ui=UIConfig(**data.get('ui', {})),
                    version=data.get('version', '1.0.0'),
                    last_updated=data.get('last_updated', ''),
                    config_file_path=str(self.config_path)
                )
                
                return config
                
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                print(f"Error loading config: {e}. Using defaults.")
                return self.create_default_config()
        else:
            return self.create_default_config()
    
    def create_default_config(self) -> MCPEAConfig:
        """Create default configuration."""
        config = MCPEAConfig(
            anthropic=AnthropicConfig(),
            agent=AgentConfig(),
            workflow=WorkflowConfig(),
            validation=ValidationConfig(),
            generation=GenerationConfig(),
            ui=UIConfig(),
            config_file_path=str(self.config_path)
        )
        self.save_config(config)
        return config
    
    def save_config(self, config: Optional[MCPEAConfig] = None) -> bool:
        """Save configuration to file."""
        if config is None:
            config = self.config
        
        config.last_updated = datetime.now().isoformat()
        
        try:
            # Convert to dict for JSON serialization
            config_dict = {
                'anthropic': asdict(config.anthropic),
                'agent': asdict(config.agent),
                'workflow': asdict(config.workflow),
                'validation': asdict(config.validation),
                'generation': asdict(config.generation),
                'ui': asdict(config.ui),
                'version': config.version,
                'last_updated': config.last_updated,
                'config_file_path': config.config_file_path
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values."""
        try:
            # Apply updates to the appropriate sections
            for section, values in updates.items():
                if hasattr(self.config, section):
                    section_obj = getattr(self.config, section)
                    for key, value in values.items():
                        if hasattr(section_obj, key):
                            setattr(section_obj, key, value)
            
            # Save updated config
            if self.save_config():
                # Notify callbacks of config change
                self._notify_callbacks()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error updating config: {e}")
            return False
    
    def get_config(self) -> MCPEAConfig:
        """Get current configuration."""
        return self.config
    
    def reload_config(self) -> bool:
        """Reload configuration from file."""
        try:
            self.config = self.load_config()
            self._notify_callbacks()
            return True
        except Exception as e:
            print(f"Error reloading config: {e}")
            return False
    
    def register_callback(self, callback):
        """Register a callback for config changes."""
        self._callbacks.append(callback)
    
    def _notify_callbacks(self):
        """Notify all registered callbacks of config changes."""
        for callback in self._callbacks:
            try:
                callback(self.config)
            except Exception as e:
                print(f"Error in config callback: {e}")
    
    def export_config(self, export_path: str) -> bool:
        """Export current configuration to a different file."""
        try:
            config_dict = {
                'anthropic': asdict(self.config.anthropic),
                'agent': asdict(self.config.agent),
                'workflow': asdict(self.config.workflow),
                'validation': asdict(self.config.validation),
                'generation': asdict(self.config.generation),
                'ui': asdict(self.config.ui),
                'version': self.config.version,
                'last_updated': datetime.now().isoformat(),
                'config_file_path': export_path
            }
            
            with open(export_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """Import configuration from another file."""
        try:
            temp_manager = ConfigManager(import_path)
            self.config = temp_manager.config
            self.config.config_file_path = str(self.config_path)
            
            if self.save_config():
                self._notify_callbacks()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error importing config: {e}")
            return False


# Global config manager instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get the global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config() -> MCPEAConfig:
    """Get the current configuration."""
    return get_config_manager().get_config()

def update_config(updates: Dict[str, Any]) -> bool:
    """Update the global configuration."""
    return get_config_manager().update_config(updates)
