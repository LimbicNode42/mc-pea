# MC-PEA Hot-Reload Configuration System

## 🔥 Overview

The MC-PEA AI Agents system now includes a comprehensive hot-reload configuration system that allows you to modify any static values in real-time through the Streamlit interface. All agents automatically respond to configuration changes without requiring restarts.

## 🎯 Features

### ✅ Dynamic Configuration Management
- **Real-time updates**: Change any configuration value and see immediate effects
- **Persistent storage**: All changes are automatically saved to `config.json`
- **Hot-reload support**: Agents receive configuration updates instantly
- **Validation**: Invalid configurations are rejected with helpful error messages
- **Export/Import**: Save and load different configuration profiles

### 🎛️ Configurable Parameters

#### 🤖 Anthropic API Settings
- **Model**: Choose from available Claude models
- **Temperature**: Control randomness (0.0 = deterministic, 1.0 = creative)
- **Max Tokens**: Set response length limits
- **Top P**: Control diversity via nucleus sampling
- **Timeout**: API request timeout in seconds
- **Max Retries**: Number of retry attempts

#### 👥 Agent Behavior
- **Max Iterations**: Maximum task iterations per agent
- **Verbose Mode**: Enable detailed logging
- **Allow Delegation**: Let agents delegate to other agents
- **Memory**: Enable context retention across tasks

#### 🔄 Workflow Control
- **Parallel Execution**: Run workflow steps concurrently
- **Max Concurrent Tasks**: Limit simultaneous operations
- **Timeout**: Workflow timeout in minutes
- **Auto Retry**: Automatically retry failed steps
- **Retry Attempts**: Number of retry attempts
- **Checkpoints**: Save workflow state at key points

#### ✅ Validation Settings
- **Auto Validate**: Automatically validate generated code
- **Strict Mode**: Enable strict validation rules
- **TypeScript Check**: Validate TypeScript compilation
- **MCP Compliance**: Check MCP protocol compliance
- **Run Tests**: Execute generated test suites
- **Performance Check**: Run performance validation

#### 🏗️ Code Generation
- **Create Tests**: Generate test files
- **Create Documentation**: Generate README and docs
- **Create Dockerfile**: Generate Docker configuration
- **Use Templates**: Use predefined templates
- **Template Path**: Path to template directory
- **Output Directory**: Where to save generated files
- **Overwrite Existing**: Replace existing files

#### 🎨 UI Configuration
- **Theme**: Light, dark, or auto theme
- **Layout**: Wide or centered layout
- **Sidebar State**: Expanded, collapsed, or auto
- **Advanced Options**: Show/hide advanced settings
- **Auto Refresh**: Automatic UI refresh interval
- **Hot Reload**: Enable/disable hot reload

## 🚀 Quick Start

### 1. Launch the Streamlit Interface
```bash
cd ai-agents
python run_server_generator.py
```

### 2. Access Configuration Panel
The configuration panel is available in the sidebar of the Streamlit interface. Click the sections to expand and modify values.

### 3. Make Real-time Changes
- Adjust sliders for numeric values
- Toggle checkboxes for boolean settings
- Select from dropdowns for enumerated options
- Edit text fields for string values

### 4. See Immediate Effects
All changes are applied instantly:
- Agents receive configuration updates via callbacks
- UI reflects new settings immediately
- Workflow plans adapt to new parameters
- Generation behavior changes accordingly

## 🧪 Testing Hot-Reload

### Run the Test Suite
```bash
cd ai-agents
python test_hot_reload.py
```

This comprehensive test validates:
- Basic configuration operations
- File persistence
- Agent responsiveness
- Callback mechanisms
- Import/export functionality

### Run Interactive Demo
```bash
cd ai-agents
python demo_hot_reload.py
```

The demo provides:
- Real-time configuration monitoring
- Simulated configuration changes
- Manual configuration updates
- Live agent response testing

## 📁 Configuration File Structure

The configuration is stored in `config.json` with the following structure:

```json
{
  "anthropic": {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 4000,
    "temperature": 0.7,
    "top_p": 0.9,
    "timeout": 60,
    "max_retries": 3
  },
  "agent": {
    "max_iterations": 5,
    "verbose": true,
    "allow_delegation": false,
    "memory": true
  },
  "workflow": {
    "parallel_execution": false,
    "max_concurrent_tasks": 3,
    "timeout_minutes": 30,
    "auto_retry": true,
    "retry_attempts": 2,
    "checkpoint_enabled": true
  },
  "validation": {
    "auto_validate": true,
    "strict_mode": false,
    "check_typescript": true,
    "check_mcp_compliance": true,
    "run_tests": true,
    "performance_check": false
  },
  "generation": {
    "create_tests": true,
    "create_docs": true,
    "create_dockerfile": true,
    "use_templates": true,
    "template_path": "../templates/mcp-server-template",
    "output_directory": "./output",
    "overwrite_existing": false
  },
  "ui": {
    "theme": "auto",
    "layout": "wide",
    "sidebar_state": "expanded",
    "show_advanced_options": false,
    "auto_refresh_interval": 5,
    "enable_hot_reload": true
  },
  "version": "1.0.0",
  "last_updated": "2025-01-09T10:30:00",
  "config_file_path": "config.json"
}
```

## 🔧 API Usage

### Programmatic Configuration Updates

```python
from core.config import update_config, get_config

# Update multiple sections at once
success = update_config({
    "anthropic": {
        "temperature": 0.8,
        "max_tokens": 5000
    },
    "agent": {
        "max_iterations": 10,
        "verbose": False
    }
})

# Get current configuration
config = get_config()
print(f"Current temperature: {config.anthropic.temperature}")
```

### Register Configuration Callbacks

```python
from core.config import get_config_manager

def my_callback(new_config):
    print(f"Config updated! New temperature: {new_config.anthropic.temperature}")

config_manager = get_config_manager()
config_manager.register_callback(my_callback)
```

### Agent Hot-Reload Integration

```python
from core.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, config, anthropic_client):
        super().__init__(config, anthropic_client)
        
        # Register for config updates
        self.register_config_callback(self._on_config_update)
    
    def _on_config_update(self, new_config):
        # Respond to configuration changes
        self.temperature = new_config.anthropic.temperature
        self.max_iterations = new_config.agent.max_iterations
        print(f"Agent updated with new config!")
```

## 🎨 UI Integration

The Streamlit interface provides comprehensive configuration management:

### Configuration Status Display
- Real-time metrics showing current values
- Hot-reload status indicator
- Last updated timestamp
- Configuration version tracking

### Interactive Controls
- Sliders for numeric ranges
- Checkboxes for boolean values
- Select boxes for enumerated options
- Text inputs for strings and paths

### Advanced Features
- Configuration export/import
- JSON view of current settings
- Validation error display
- Change history tracking

## 🔄 Workflow Impact

Configuration changes immediately affect workflow generation:

- **Test Creation**: Controlled by `generation.create_tests`
- **Documentation**: Controlled by `generation.create_docs`
- **Docker Files**: Controlled by `generation.create_dockerfile`
- **Validation Steps**: Controlled by `validation.auto_validate`
- **Parallel Execution**: Controlled by `workflow.parallel_execution`

Example workflow adaptation:
```python
# With create_tests=False, create_dockerfile=True
steps = ["analyze_api", "generate_code", "create_docker", "package_server"]

# With create_tests=True, validation.auto_validate=True
steps = ["analyze_api", "generate_code", "create_tests", "validate_mcp", "package_server"]
```

## 🛡️ Best Practices

### 1. Use Environment Variables for Secrets
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### 2. Test Configuration Changes
Always validate changes with the test suite before production use.

### 3. Backup Configurations
Export important configurations for reuse:
```python
config_manager.export_config("production-config.json")
```

### 4. Monitor Agent Responses
Use verbose mode to see how agents respond to configuration changes.

### 5. Use Appropriate Timeouts
Set realistic timeouts based on your use case and API limits.

## 🐛 Troubleshooting

### Configuration Not Updating
1. Check if hot-reload is enabled in UI settings
2. Verify the config file is writable
3. Look for validation errors in the console

### Agents Not Responding
1. Ensure agents are properly initialized
2. Check callback registration
3. Verify agent inheritance from BaseAgent

### File Permission Issues
1. Check write permissions on config.json
2. Verify directory permissions for output folder
3. Run with appropriate user privileges

### Performance Issues
1. Reduce auto-refresh interval
2. Disable verbose mode for production
3. Use appropriate concurrent task limits

## 📈 Monitoring and Debugging

### Enable Verbose Logging
Set `agent.verbose = true` in configuration to see detailed agent activity.

### Monitor Configuration Changes
Use the demo script to track real-time configuration updates.

### Check Agent Callbacks
Each agent logs when it receives configuration updates.

### Validate Configuration
Use the test suite to verify configuration integrity.

## 🔮 Future Enhancements

- **Remote Configuration**: Load configs from external sources
- **Configuration Profiles**: Predefined settings for different use cases
- **Change History**: Track and rollback configuration changes
- **Conditional Configuration**: Rules-based configuration updates
- **Configuration Validation**: Advanced validation with custom rules

---

🎉 **The hot-reload configuration system makes MC-PEA highly flexible and responsive to your changing needs. Experiment with different settings and see immediate results!**
