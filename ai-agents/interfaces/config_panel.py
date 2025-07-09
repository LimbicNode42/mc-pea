"""
Configuration panel for the MC-PEA AI Agent Streamlit interface.
Provides real-time configuration editing and hot reload functionality.
"""

import streamlit as st
import json
from typing import Dict, Any
from core.config import get_config_manager, MCPEAConfig


def render_config_panel():
    """Render the configuration panel in the Streamlit sidebar."""
    
    config_manager = get_config_manager()
    config = config_manager.get_config()
    
    st.sidebar.markdown("---")
    st.sidebar.header("🔧 Configuration")
    
    # Configuration management buttons
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🔄 Reload", help="Reload config from file"):
            if config_manager.reload_config():
                st.success("Config reloaded!")
                st.rerun()
            else:
                st.error("Failed to reload config")
    
    with col2:
        if st.button("💾 Save", help="Save current config"):
            if config_manager.save_config():
                st.success("Config saved!")
            else:
                st.error("Failed to save config")
    
    # Show/hide advanced options
    show_advanced = st.sidebar.checkbox(
        "Show Advanced Options", 
        value=config.ui.show_advanced_options,
        help="Show all configuration options"
    )
    
    if show_advanced != config.ui.show_advanced_options:
        config_manager.update_config({
            "ui": {"show_advanced_options": show_advanced}
        })
        st.rerun()
    
    # Configuration sections
    config_sections = {
        "🤖 Anthropic API": render_anthropic_config,
        "👥 Agent Settings": render_agent_config,
        "🔄 Workflow": render_workflow_config,
        "✅ Validation": render_validation_config,
        "🏗️ Generation": render_generation_config,
        "🎨 UI Settings": render_ui_config
    }
    
    # Render each configuration section
    for section_name, render_func in config_sections.items():
        with st.sidebar.expander(section_name, expanded=False):
            render_func(config, show_advanced)
    
    # Export/Import configuration
    if show_advanced:
        with st.sidebar.expander("📁 Import/Export", expanded=False):
            render_import_export(config_manager)


def render_anthropic_config(config: MCPEAConfig, show_advanced: bool):
    """Render Anthropic API configuration options."""
    
    updates = {}
    
    # Model selection
    model_options = [
        "claude-opus-4-20250514",
        "claude-sonnet-4-20250514",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022", 
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307"
    ]
    
    new_model = st.selectbox(
        "Model",
        options=model_options,
        index=model_options.index(config.anthropic.model) if config.anthropic.model in model_options else 0,
        help="Choose the Anthropic model to use"
    )
    
    if new_model != config.anthropic.model:
        updates["model"] = new_model
    
    # Temperature
    new_temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=config.anthropic.temperature,
        step=0.1,
        help="Controls randomness in responses (0.0 = deterministic, 1.0 = very random)"
    )
    
    if new_temperature != config.anthropic.temperature:
        updates["temperature"] = new_temperature
    
    # Max tokens
    new_max_tokens = st.number_input(
        "Max Tokens",
        min_value=100,
        max_value=8192,
        value=config.anthropic.max_tokens,
        step=100,
        help="Maximum number of tokens in the response"
    )
    
    if new_max_tokens != config.anthropic.max_tokens:
        updates["max_tokens"] = int(new_max_tokens)
    
    # Basic options section
    with st.expander("Basic Options", expanded=True):
        # Top P
        new_top_p = st.slider(
            "Top P",
            min_value=0.0,
            max_value=1.0,
            value=config.anthropic.top_p,
            step=0.05,
            help="Controls diversity via nucleus sampling"
        )
        
        if new_top_p != config.anthropic.top_p:
            updates["top_p"] = new_top_p
            
        # Seed
        new_seed = st.number_input(
            "Seed",
            min_value=0,
            max_value=2147483647,
            value=getattr(config.anthropic, "seed", 0),
            step=1,
            help="Random seed for deterministic outputs"
        )
        
        if new_seed != getattr(config.anthropic, "seed", 0):
            updates["seed"] = int(new_seed)
            
        # Streaming
        new_stream = st.checkbox(
            "Stream Response",
            value=getattr(config.anthropic, "stream", False),
            help="Stream tokens as they're generated rather than waiting for the complete response"
        )
        
        if new_stream != getattr(config.anthropic, "stream", False):
            updates["stream"] = new_stream
    
    if show_advanced:
        # Advanced options section
        with st.expander("Advanced Options", expanded=False):
            # Presence Penalty
            new_presence_penalty = st.slider(
                "Presence Penalty",
                min_value=-2.0,
                max_value=2.0,
                value=getattr(config.anthropic, "presence_penalty", 0.0),
                step=0.1,
                help="Reduces repetition by penalizing tokens that already appear in the text"
            )
            
            if new_presence_penalty != getattr(config.anthropic, "presence_penalty", 0.0):
                updates["presence_penalty"] = new_presence_penalty
            
            # Frequency Penalty
            new_frequency_penalty = st.slider(
                "Frequency Penalty",
                min_value=-2.0,
                max_value=2.0,
                value=getattr(config.anthropic, "frequency_penalty", 0.0),
                step=0.1,
                help="Reduces repetition by penalizing tokens based on their frequency in the text"
            )
            
            if new_frequency_penalty != getattr(config.anthropic, "frequency_penalty", 0.0):
                updates["frequency_penalty"] = new_frequency_penalty
            
            # Logprobs
            new_logprobs = st.number_input(
                "Log Probabilities",
                min_value=0,
                max_value=5,
                value=getattr(config.anthropic, "logprobs", 0),
                step=1,
                help="Number of most likely tokens to return with probabilities"
            )
            
            if new_logprobs != getattr(config.anthropic, "logprobs", 0):
                updates["logprobs"] = int(new_logprobs)
            
            # Top Logprobs
            new_top_logprobs = st.number_input(
                "Top Log Probabilities",
                min_value=0,
                max_value=5,
                value=getattr(config.anthropic, "top_logprobs", 0),
                step=1,
                help="Number of top token log probabilities to return"
            )
            
            if new_top_logprobs != getattr(config.anthropic, "top_logprobs", 0):
                updates["top_logprobs"] = int(new_top_logprobs)
            
            # Reasoning Effort
            reasoning_effort_options = ["none", "low", "medium", "high"]
            new_reasoning_effort = st.selectbox(
                "Reasoning Effort",
                options=reasoning_effort_options,
                index=reasoning_effort_options.index(getattr(config.anthropic, "reasoning_effort", "none")) if getattr(config.anthropic, "reasoning_effort", "none") in reasoning_effort_options else 0,
                help="Level of effort the model should put into reasoning (primarily for Claude models)"
            )
            
            if new_reasoning_effort != getattr(config.anthropic, "reasoning_effort", "none"):
                updates["reasoning_effort"] = new_reasoning_effort
        
        # Connection options section
        with st.expander("Connection Options", expanded=False):
            # Timeout
            new_timeout = st.number_input(
                "Timeout (seconds)",
                min_value=10,
                max_value=300,
                value=config.anthropic.timeout,
                step=10,
                help="API request timeout in seconds"
            )
            
            if new_timeout != config.anthropic.timeout:
                updates["timeout"] = int(new_timeout)
            
            # Max retries
            new_max_retries = st.number_input(
                "Max Retries",
                min_value=0,
                max_value=10,
                value=config.anthropic.max_retries,
                step=1,
                help="Maximum number of API retry attempts"
            )
            
            if new_max_retries != config.anthropic.max_retries:
                updates["max_retries"] = int(new_max_retries)
            
            # API Base
            new_api_base = st.text_input(
                "API Base URL",
                value=getattr(config.anthropic, "api_base", ""),
                help="Override the default API base URL (leave empty for default)"
            )
            
            if new_api_base != getattr(config.anthropic, "api_base", ""):
                updates["api_base"] = new_api_base if new_api_base else None
            
            # API Version
            new_api_version = st.text_input(
                "API Version",
                value=getattr(config.anthropic, "api_version", ""),
                help="Specify API version to use (leave empty for default)"
            )
            
            if new_api_version != getattr(config.anthropic, "api_version", ""):
                updates["api_version"] = new_api_version if new_api_version else None
    
    # Apply updates
    if updates:
        get_config_manager().update_config({"anthropic": updates})


def render_agent_config(config: MCPEAConfig, show_advanced: bool):
    """Render agent configuration options."""
    
    updates = {}
    
    # Max iterations
    new_max_iterations = st.slider(
        "Max Iterations",
        min_value=1,
        max_value=20,
        value=config.agent.max_iterations,
        step=1,
        help="Maximum number of iterations for agent tasks"
    )
    
    if new_max_iterations != config.agent.max_iterations:
        updates["max_iterations"] = new_max_iterations
    
    # Verbose mode
    new_verbose = st.checkbox(
        "Verbose Mode",
        value=config.agent.verbose,
        help="Enable detailed logging and output"
    )
    
    if new_verbose != config.agent.verbose:
        updates["verbose"] = new_verbose
    
    if show_advanced:
        # Allow delegation
        new_allow_delegation = st.checkbox(
            "Allow Delegation",
            value=config.agent.allow_delegation,
            help="Allow agents to delegate tasks to other agents"
        )
        
        if new_allow_delegation != config.agent.allow_delegation:
            updates["allow_delegation"] = new_allow_delegation
        
        # Memory
        new_memory = st.checkbox(
            "Enable Memory",
            value=config.agent.memory,
            help="Enable agent memory for context retention"
        )
        
        if new_memory != config.agent.memory:
            updates["memory"] = new_memory
    
    # Apply updates
    if updates:
        get_config_manager().update_config({"agent": updates})


def render_workflow_config(config: MCPEAConfig, show_advanced: bool):
    """Render workflow configuration options."""
    
    updates = {}
    
    # Parallel execution
    new_parallel = st.checkbox(
        "Parallel Execution",
        value=config.workflow.parallel_execution,
        help="Enable parallel execution of workflow steps"
    )
    
    if new_parallel != config.workflow.parallel_execution:
        updates["parallel_execution"] = new_parallel
    
    # Max concurrent tasks
    new_max_concurrent = st.slider(
        "Max Concurrent Tasks",
        min_value=1,
        max_value=10,
        value=config.workflow.max_concurrent_tasks,
        step=1,
        help="Maximum number of tasks to run concurrently"
    )
    
    if new_max_concurrent != config.workflow.max_concurrent_tasks:
        updates["max_concurrent_tasks"] = new_max_concurrent
    
    if show_advanced:
        # Timeout
        new_timeout = st.number_input(
            "Timeout (minutes)",
            min_value=5,
            max_value=120,
            value=config.workflow.timeout_minutes,
            step=5,
            help="Workflow timeout in minutes"
        )
        
        if new_timeout != config.workflow.timeout_minutes:
            updates["timeout_minutes"] = int(new_timeout)
        
        # Auto retry
        new_auto_retry = st.checkbox(
            "Auto Retry",
            value=config.workflow.auto_retry,
            help="Automatically retry failed workflow steps"
        )
        
        if new_auto_retry != config.workflow.auto_retry:
            updates["auto_retry"] = new_auto_retry
        
        # Retry attempts
        new_retry_attempts = st.number_input(
            "Retry Attempts",
            min_value=0,
            max_value=10,
            value=config.workflow.retry_attempts,
            step=1,
            help="Number of retry attempts for failed steps"
        )
        
        if new_retry_attempts != config.workflow.retry_attempts:
            updates["retry_attempts"] = int(new_retry_attempts)
        
        # Checkpoint enabled
        new_checkpoint = st.checkbox(
            "Enable Checkpoints",
            value=config.workflow.checkpoint_enabled,
            help="Save workflow state at checkpoints"
        )
        
        if new_checkpoint != config.workflow.checkpoint_enabled:
            updates["checkpoint_enabled"] = new_checkpoint
    
    # Apply updates
    if updates:
        get_config_manager().update_config({"workflow": updates})


def render_validation_config(config: MCPEAConfig, show_advanced: bool):
    """Render validation configuration options."""
    
    updates = {}
    
    # Auto validate
    new_auto_validate = st.checkbox(
        "Auto Validate",
        value=config.validation.auto_validate,
        help="Automatically validate generated code"
    )
    
    if new_auto_validate != config.validation.auto_validate:
        updates["auto_validate"] = new_auto_validate
    
    # Check MCP compliance
    new_check_mcp = st.checkbox(
        "Check MCP Compliance",
        value=config.validation.check_mcp_compliance,
        help="Validate MCP protocol compliance"
    )
    
    if new_check_mcp != config.validation.check_mcp_compliance:
        updates["check_mcp_compliance"] = new_check_mcp
    
    # Run tests
    new_run_tests = st.checkbox(
        "Run Tests",
        value=config.validation.run_tests,
        help="Execute generated test suites"
    )
    
    if new_run_tests != config.validation.run_tests:
        updates["run_tests"] = new_run_tests
    
    if show_advanced:
        # Strict mode
        new_strict = st.checkbox(
            "Strict Mode",
            value=config.validation.strict_mode,
            help="Enable strict validation rules"
        )
        
        if new_strict != config.validation.strict_mode:
            updates["strict_mode"] = new_strict
        
        # Check TypeScript
        new_check_ts = st.checkbox(
            "Check TypeScript",
            value=config.validation.check_typescript,
            help="Validate TypeScript compilation"
        )
        
        if new_check_ts != config.validation.check_typescript:
            updates["check_typescript"] = new_check_ts
        
        # Performance check
        new_perf_check = st.checkbox(
            "Performance Check",
            value=config.validation.performance_check,
            help="Run performance validation tests"
        )
        
        if new_perf_check != config.validation.performance_check:
            updates["performance_check"] = new_perf_check
    
    # Apply updates
    if updates:
        get_config_manager().update_config({"validation": updates})


def render_generation_config(config: MCPEAConfig, show_advanced: bool):
    """Render generation configuration options."""
    
    updates = {}
    
    # Create tests
    new_create_tests = st.checkbox(
        "Generate Tests",
        value=config.generation.create_tests,
        help="Generate test files for the MCP server"
    )
    
    if new_create_tests != config.generation.create_tests:
        updates["create_tests"] = new_create_tests
    
    # Create docs
    new_create_docs = st.checkbox(
        "Generate Documentation",
        value=config.generation.create_docs,
        help="Generate README and documentation files"
    )
    
    if new_create_docs != config.generation.create_docs:
        updates["create_docs"] = new_create_docs
    
    # Create Dockerfile
    new_create_dockerfile = st.checkbox(
        "Generate Dockerfile",
        value=config.generation.create_dockerfile,
        help="Generate Docker configuration files"
    )
    
    if new_create_dockerfile != config.generation.create_dockerfile:
        updates["create_dockerfile"] = new_create_dockerfile
    
    if show_advanced:
        # Use templates
        new_use_templates = st.checkbox(
            "Use Templates",
            value=config.generation.use_templates,
            help="Use predefined templates for code generation"
        )
        
        if new_use_templates != config.generation.use_templates:
            updates["use_templates"] = new_use_templates
        
        # Template path
        new_template_path = st.text_input(
            "Template Path",
            value=config.generation.template_path,
            help="Path to the MCP server template directory"
        )
        
        if new_template_path != config.generation.template_path:
            updates["template_path"] = new_template_path
        
        # Output directory
        new_output_dir = st.text_input(
            "Output Directory",
            value=config.generation.output_directory,
            help="Directory to save generated files"
        )
        
        if new_output_dir != config.generation.output_directory:
            updates["output_directory"] = new_output_dir
        
        # Overwrite existing
        new_overwrite = st.checkbox(
            "Overwrite Existing",
            value=config.generation.overwrite_existing,
            help="Overwrite existing files without confirmation"
        )
        
        if new_overwrite != config.generation.overwrite_existing:
            updates["overwrite_existing"] = new_overwrite
    
    # Apply updates
    if updates:
        get_config_manager().update_config({"generation": updates})


def render_ui_config(config: MCPEAConfig, show_advanced: bool):
    """Render UI configuration options."""
    
    updates = {}
    
    # Theme
    theme_options = ["auto", "light", "dark"]
    new_theme = st.selectbox(
        "Theme",
        options=theme_options,
        index=theme_options.index(config.ui.theme) if config.ui.theme in theme_options else 0,
        help="Choose the UI theme"
    )
    
    if new_theme != config.ui.theme:
        updates["theme"] = new_theme
    
    # Layout
    layout_options = ["centered", "wide"]
    new_layout = st.selectbox(
        "Layout",
        options=layout_options,
        index=layout_options.index(config.ui.layout) if config.ui.layout in layout_options else 1,
        help="Choose the page layout"
    )
    
    if new_layout != config.ui.layout:
        updates["layout"] = new_layout
    
    if show_advanced:
        # Sidebar state
        sidebar_options = ["auto", "expanded", "collapsed"]
        new_sidebar_state = st.selectbox(
            "Sidebar State",
            options=sidebar_options,
            index=sidebar_options.index(config.ui.sidebar_state) if config.ui.sidebar_state in sidebar_options else 1,
            help="Default sidebar state"
        )
        
        if new_sidebar_state != config.ui.sidebar_state:
            updates["sidebar_state"] = new_sidebar_state
        
        # Auto refresh interval
        new_refresh_interval = st.number_input(
            "Auto Refresh (seconds)",
            min_value=1,
            max_value=60,
            value=config.ui.auto_refresh_interval,
            step=1,
            help="Auto refresh interval for real-time updates"
        )
        
        if new_refresh_interval != config.ui.auto_refresh_interval:
            updates["auto_refresh_interval"] = int(new_refresh_interval)
        
        # Enable hot reload
        new_hot_reload = st.checkbox(
            "Enable Hot Reload",
            value=config.ui.enable_hot_reload,
            help="Enable hot reloading of configuration changes"
        )
        
        if new_hot_reload != config.ui.enable_hot_reload:
            updates["enable_hot_reload"] = new_hot_reload
    
    # Apply updates
    if updates:
        get_config_manager().update_config({"ui": updates})


def render_import_export(config_manager):
    """Render import/export configuration options."""
    
    st.markdown("**Export Configuration**")
    
    export_name = st.text_input(
        "Export Filename",
        value="mc-pea-config-export.json",
        help="Filename for exported configuration"
    )
    
    if st.button("📥 Export Config"):
        try:
            if config_manager.export_config(export_name):
                st.success(f"Configuration exported to {export_name}")
            else:
                st.error("Failed to export configuration")
        except Exception as e:
            st.error(f"Export error: {str(e)}")
    
    st.markdown("**Import Configuration**")
    
    uploaded_file = st.file_uploader(
        "Choose config file",
        type=['json'],
        help="Upload a JSON configuration file"
    )
    
    if uploaded_file is not None:
        if st.button("📤 Import Config"):
            try:
                # Save uploaded file temporarily
                temp_path = f"temp_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Import configuration
                if config_manager.import_config(temp_path):
                    st.success("Configuration imported successfully!")
                    st.rerun()
                else:
                    st.error("Failed to import configuration")
                
                # Clean up temp file
                import os
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
            except Exception as e:
                st.error(f"Import error: {str(e)}")
    
    # Show current config as JSON
    st.markdown("**Current Configuration**")
    with st.expander("View JSON", expanded=False):
        config_dict = {
            'anthropic': config_manager.config.anthropic.__dict__,
            'agent': config_manager.config.agent.__dict__,
            'workflow': config_manager.config.workflow.__dict__,
            'validation': config_manager.config.validation.__dict__,
            'generation': config_manager.config.generation.__dict__,
            'ui': config_manager.config.ui.__dict__,
            'version': config_manager.config.version,
            'last_updated': config_manager.config.last_updated
        }
        st.json(config_dict)
