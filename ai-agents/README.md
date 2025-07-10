# MC-PEA AI Agent Dashboard

A comprehensive Streamlit-based dashboard for managing AI agents and MCP (Model Context Protocol) server generation.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. **Navigate to the ai-agents directory:**
   ```bash
   cd ai-agents
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and add your API keys
   # Required: ANTHROPIC_API_KEY
   ```

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```

The dashboard will open in your browser at `http://localhost:8501`

### 🧪 Docker-Free Testing

For quick testing without Docker or MCP servers:

```bash
# Test all agents with fallback methods
python docker_free_test.py

# Test specific components
python docker_free_test.py --test web_scraper
python docker_free_test.py --test api_analyzer

# Test with custom URL
python docker_free_test.py --url https://docs.example.com/api
```

See [DOCKER_FREE_TESTING.md](DOCKER_FREE_TESTING.md) for detailed documentation.

## 🎯 Features

### 🏠 Dashboard Tab
- **System Overview:** Quick metrics showing available agents, MCP servers, and their status
- **Configuration Status:** Current system configuration and hot reload status
- **Quick Actions:** One-click access to common tasks
- **Recent Activity:** Track recent server generations and validations

### 🤖 Agents Tab
- **Available Agents:** View all AI agents in the system
- **Agent Status:** See which agents are fully implemented vs. skeleton
- **Capabilities Matrix:** Understand what each agent can do
- **Agent Details:** Descriptions and current implementation status

### 🛠️ Servers Tab
- **Generated Servers:** Browse all MCP servers in the system
- **Server Metrics:** Implementation status, testing coverage, documentation
- **Server Actions:** View details, run tests, deploy servers
- **New Server Generation:** Create new MCP servers from API specifications

## 📊 Agent Overview

### Current Agents

1. **API Analyzer Agent** (`api_analyzer/`)
   - Analyzes external APIs and creates MCP server specifications
   - Supports OpenAPI/Swagger parsing
   - Generates confidence scores and complexity analysis

2. **MCP Generator Agent** (`mcp_generator/`)
   - Generates production-ready TypeScript MCP server code
   - Creates complete project structure with tests and documentation
   - Follows MCP protocol standards

3. **Orchestrator Agent** (`orchestrator/`)
   - Coordinates multi-agent workflows
   - Manages dependencies and parallel execution
   - Tracks workflow progress and handles errors

4. **Validator Agent** (`validator/`)
   - Validates MCP servers for protocol compliance
   - Performs security and performance analysis
   - Generates quality reports and recommendations

## 🛠️ MCP Server Discovery

The dashboard automatically discovers:

- **Production Servers:** In `../mcp-servers/` directory
- **Generated Servers:** In configured output directories
- **Template Servers:** In `../templates/` directory

Each server shows:
- Implementation status (configured, implemented, tested)
- Documentation availability
- Test coverage
- Version and description

## ⚙️ Configuration

The system uses dynamic configuration that can be updated through the UI:

- **Agent Settings:** Model configuration, temperature, iterations
- **Workflow Settings:** Parallel execution, task limits
- **Generation Settings:** Auto-testing, documentation creation
- **UI Settings:** Hot reload, advanced options display

## 🔧 Development

### Adding New Agents

1. Create a new directory in `agents/`
2. Implement the agent class extending `BaseAgent`
3. Add proper docstrings and type hints
4. The dashboard will automatically discover it

### Extending the Interface

The interface is built with Streamlit and uses:
- **Plotly** for interactive visualizations
- **Pandas** for data handling
- **Pydantic** for data validation

## 🐛 Troubleshooting

### Import Errors
- Ensure you're running from the `ai-agents/` directory
- Check that all dependencies are installed
- Verify Python path includes the current directory

### Missing Agents/Servers
- Check directory structure matches expected layout
- Ensure `__init__.py` files exist in agent directories
- Verify file permissions and paths

### Configuration Issues
- Check environment variables are set correctly
- Ensure configuration files have valid syntax
- Check logs for detailed error messages

## 📚 API Reference

### Environment Variables

- `ANTHROPIC_API_KEY`: Required for AI agent functionality
- `MCPEA_CONFIG_PATH`: Optional custom configuration file path
- `MCPEA_OUTPUT_DIR`: Optional custom output directory for generated servers

### Configuration Files

- `.env`: Environment variables
- `config.json`: System configuration (auto-generated)
- Individual agent configs in agent directories

## 🤝 Contributing

1. Follow the coding standards in the project instructions
2. Add comprehensive type hints and docstrings
3. Include tests for new functionality
4. Update documentation for any interface changes

## 📄 License

This project is part of the MC-PEA (Model Context Protocol Enterprise Architecture) framework.
