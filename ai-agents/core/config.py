"""
Configuration management for MC-PEA AI Agents.
Supports dynamic configuration updates and hot reloading.
"""

import json
import os
from typing import Dict, Any, Optional, List
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
class AgentSpecificConfig:
    """Agent-specific configuration that can override global settings."""
    agent_type: str  # e.g., "mcp_generator", "validator", "analyzer", "orchestrator"
    anthropic_overrides: Optional[Dict[str, Any]] = None  # Override specific Anthropic settings
    max_iterations: Optional[int] = None  # Override global max iterations
    verbose: Optional[bool] = None  # Override global verbose setting
    allow_delegation: Optional[bool] = None  # Override global delegation setting
    memory: Optional[bool] = None  # Override global memory setting
    step_callback: Optional[str] = None  # Agent-specific callback
    custom_settings: Optional[Dict[str, Any]] = None  # Agent-specific custom settings


@dataclass
class AgentProfilesConfig:
    """Predefined agent profiles with optimized settings."""
    # Agent profiles with different LLM configurations
    profiles: Dict[str, AgentSpecificConfig] = None
    
    def __post_init__(self):
        if self.profiles is None:
            self.profiles = self._create_default_profiles()
    
    def _discover_agent_types(self) -> List[str]:
        """Dynamically discover agent types from the agents directory."""
        agents_dir = Path(__file__).parent.parent / "agents"
        agent_types = []
        
        if agents_dir.exists():
            for item in agents_dir.iterdir():
                if (item.is_dir() and 
                    not item.name.startswith('_') and 
                    item.name != '__pycache__'):
                    agent_types.append(item.name)
        
        # Fallback to known agent types if directory scan fails
        if not agent_types:
            agent_types = ["mcp_generator", "validator", "api_analyzer", "orchestrator"]
        
        return sorted(agent_types)
    
    def _get_default_config_for_agent(self, agent_type: str) -> AgentSpecificConfig:
        """Get default configuration for a specific agent type."""
        
        # Predefined optimized configurations for known agent types
        known_configs = {
            "mcp_generator": AgentSpecificConfig(
                agent_type="mcp_generator",
                anthropic_overrides={
                    "model": "claude-opus-4-20250514",  # Most capable for complex generation
                    "temperature": 0.8,  # Higher creativity for code generation
                    "max_tokens": 8000,  # Larger output for complete files
                    "presence_penalty": 0.1,  # Slight penalty to avoid repetition
                    "reasoning_effort": "high"  # Maximum reasoning for complex tasks
                },
                max_iterations=10,  # More iterations for complex generation
                verbose=True,
                allow_delegation=True,
                memory=True
            ),
            "validator": AgentSpecificConfig(
                agent_type="validator",
                anthropic_overrides={
                    "model": "claude-3-5-haiku-20241022",  # Fast and efficient for validation
                    "temperature": 0.2,  # Low temperature for consistent validation
                    "max_tokens": 2000,  # Smaller output for validation reports
                    "reasoning_effort": "medium"  # Balanced reasoning for checks
                },
                max_iterations=3,  # Quick validation cycles
                verbose=False,
                allow_delegation=False,
                memory=False
            ),
            "api_analyzer": AgentSpecificConfig(
                agent_type="api_analyzer",
                anthropic_overrides={
                    "model": "claude-3-5-sonnet-20241022",  # Balanced for analysis
                    "temperature": 0.5,  # Moderate creativity for analysis
                    "max_tokens": 4000,  # Medium output for analysis reports
                    "reasoning_effort": "medium"
                },
                max_iterations=5,
                verbose=True,
                allow_delegation=False,
                memory=True
            ),
            "orchestrator": AgentSpecificConfig(
                agent_type="orchestrator",
                anthropic_overrides={
                    "model": "claude-sonnet-4-20250514",  # Latest model for coordination
                    "temperature": 0.3,  # Lower temperature for consistent coordination
                    "max_tokens": 3000,  # Medium output for coordination tasks
                    "reasoning_effort": "high"  # High reasoning for orchestration decisions
                },
                max_iterations=8,
                verbose=True,
                allow_delegation=True,
                memory=True
            )
        }
        
        # Return predefined config if available, otherwise create a sensible default
        if agent_type in known_configs:
            return known_configs[agent_type]
        else:
            # Create default config for unknown agent types
            return self._create_default_agent_config(agent_type)
    
    def _create_default_agent_config(self, agent_type: str) -> AgentSpecificConfig:
        """Create a sensible default configuration for unknown agent types."""
        
        # Determine default settings based on agent type patterns
        if "generator" in agent_type.lower() or "creator" in agent_type.lower():
            # Generator-type agents need more creativity and output capacity
            default_config = {
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.7,
                "max_tokens": 6000,
                "reasoning_effort": "high"
            }
            max_iterations = 8
            verbose = True
            allow_delegation = True
            memory = True
        elif "validator" in agent_type.lower() or "checker" in agent_type.lower():
            # Validator-type agents need consistency and speed
            default_config = {
                "model": "claude-3-5-haiku-20241022",
                "temperature": 0.2,
                "max_tokens": 2000,
                "reasoning_effort": "medium"
            }
            max_iterations = 3
            verbose = False
            allow_delegation = False
            memory = False
        elif "analyzer" in agent_type.lower() or "parser" in agent_type.lower():
            # Analyzer-type agents need balanced capabilities
            default_config = {
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.4,
                "max_tokens": 4000,
                "reasoning_effort": "medium"
            }
            max_iterations = 5
            verbose = True
            allow_delegation = False
            memory = True
        elif "orchestrator" in agent_type.lower() or "coordinator" in agent_type.lower():
            # Orchestrator-type agents need high reasoning for coordination
            default_config = {
                "model": "claude-sonnet-4-20250514",
                "temperature": 0.3,
                "max_tokens": 3000,
                "reasoning_effort": "high"
            }
            max_iterations = 8
            verbose = True
            allow_delegation = True
            memory = True
        else:
            # Generic default for unknown agent types
            default_config = {
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.5,
                "max_tokens": 4000,
                "reasoning_effort": "medium"
            }
            max_iterations = 5
            verbose = True
            allow_delegation = False
            memory = True
        
        return AgentSpecificConfig(
            agent_type=agent_type,
            anthropic_overrides=default_config,
            max_iterations=max_iterations,
            verbose=verbose,
            allow_delegation=allow_delegation,
            memory=memory
        )
    
    def _create_default_profiles(self) -> Dict[str, AgentSpecificConfig]:
        """Create default profiles for all discovered agent types."""
        discovered_agents = self._discover_agent_types()
        profiles = {}
        
        for agent_type in discovered_agents:
            profiles[agent_type] = self._get_default_config_for_agent(agent_type)
        
        return profiles
    
    def add_agent_profile(self, agent_type: str) -> AgentSpecificConfig:
        """Add a new agent profile for a newly discovered agent type."""
        if agent_type not in self.profiles:
            self.profiles[agent_type] = self._get_default_config_for_agent(agent_type)
        return self.profiles[agent_type]
    
    def refresh_profiles(self) -> bool:
        """Refresh profiles to include any newly discovered agent types."""
        discovered_agents = self._discover_agent_types()
        updated = False
        
        for agent_type in discovered_agents:
            if agent_type not in self.profiles:
                self.profiles[agent_type] = self._get_default_config_for_agent(agent_type)
                updated = True
        
        return updated


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
    agent_profiles: AgentProfilesConfig
    
    # Metadata
    version: str = "1.0.0"
    last_updated: str = ""
    config_file_path: str = ""

    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
        if self.agent_profiles is None:
            self.agent_profiles = AgentProfilesConfig()
    
    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """Get effective configuration for a specific agent type."""
        # Ensure the agent profile exists (auto-create if new agent discovered)
        if agent_type not in self.agent_profiles.profiles:
            self.agent_profiles.add_agent_profile(agent_type)
        
        # Start with global settings
        base_config = {
            "anthropic": asdict(self.anthropic),
            "agent": asdict(self.agent)
        }
        
        # Apply agent-specific overrides if they exist
        if agent_type in self.agent_profiles.profiles:
            profile = self.agent_profiles.profiles[agent_type]
            
            # Override Anthropic settings
            if profile.anthropic_overrides:
                base_config["anthropic"].update(profile.anthropic_overrides)
            
            # Override agent settings
            agent_overrides = {}
            if profile.max_iterations is not None:
                agent_overrides["max_iterations"] = profile.max_iterations
            if profile.verbose is not None:
                agent_overrides["verbose"] = profile.verbose
            if profile.allow_delegation is not None:
                agent_overrides["allow_delegation"] = profile.allow_delegation
            if profile.memory is not None:
                agent_overrides["memory"] = profile.memory
            if profile.step_callback is not None:
                agent_overrides["step_callback"] = profile.step_callback
                
            base_config["agent"].update(agent_overrides)
            
            # Add custom settings
            if profile.custom_settings:
                base_config["custom"] = profile.custom_settings
        
        return base_config
    
    def refresh_agent_profiles(self) -> bool:
        """Refresh agent profiles to include any newly discovered agent types."""
        return self.agent_profiles.refresh_profiles()
    
    def get_available_agent_types(self) -> List[str]:
        """Get list of all available agent types (discovered + configured)."""
        return list(self.agent_profiles.profiles.keys())


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
                    agent_profiles=AgentProfilesConfig(),  # Always use defaults for profiles
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
            agent_profiles=AgentProfilesConfig(),
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
                'agent_profiles': asdict(config.agent_profiles),
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
