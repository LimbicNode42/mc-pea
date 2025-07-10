# Docker-Free Local Testing Guide

This guide helps you test the MC-PEA AI agent system locally without requiring Docker or MCP servers.

## Quick Start

1. **Run the Docker-free test suite:**
   ```bash
   cd ai-agents
   python docker_free_test.py
   ```

2. **Test specific components:**
   ```bash
   # Test web scraper only
   python docker_free_test.py --test web_scraper
   
   # Test API analyzer only
   python docker_free_test.py --test api_analyzer
   
   # Test orchestrator only
   python docker_free_test.py --test orchestrator
   ```

3. **Test with custom URL:**
   ```bash
   python docker_free_test.py --url https://docs.example.com/api
   ```

## What Gets Tested

### Web Scraper Agent
- ✅ **Fallback Scraping**: Uses `requests` + `BeautifulSoup` when Playwright MCP server is unavailable
- ✅ **Availability Check**: Verifies if Playwright MCP server is installed
- ✅ **Error Handling**: Graceful fallback when Docker/MCP servers are unavailable
- ❌ **Limitations**: JavaScript-heavy sites may not work properly

### API Analyzer Agent
- ✅ **Content Analysis**: Analyzes scraped documentation data
- ✅ **Specification Generation**: Creates MCP server specifications
- ✅ **Pattern Detection**: Identifies API patterns and conventions
- ✅ **No Dependencies**: Works without external MCP servers

### Orchestrator Agent
- ✅ **Agent Coordination**: Manages workflow between agents
- ✅ **Configuration Management**: Handles agent configuration
- ✅ **Dependency Tracking**: Reports MCP server dependencies
- ✅ **Status Monitoring**: Tracks agent states and capabilities

## Installation Requirements

### Minimal Requirements (Docker-free)
```bash
# Python dependencies
pip install requests beautifulsoup4 streamlit plotly

# Or install from requirements.txt
pip install -r requirements.txt
```

### Optional for Full Functionality
```bash
# Node.js and Playwright MCP server
npm install -g @executeautomation/playwright-mcp-server

# Docker (for other MCP servers)
# Install Docker Desktop from https://docker.com
```

## Understanding Test Results

### Success Indicators
- ✅ **PASS**: Component is working correctly
- ❌ **FAIL**: Component has issues that need attention

### Common Issues and Solutions

#### Web Scraper Issues
```
❌ FAIL Web Scraper Fallback
Error: No module named 'requests'
```
**Solution**: Install required packages
```bash
pip install requests beautifulsoup4
```

#### Network Issues
```
❌ FAIL Web Scraper Fallback
Error: HTTPSConnectionPool... timed out
```
**Solution**: Check internet connectivity or try a different URL
```bash
python docker_free_test.py --url https://httpbin.org/html
```

#### Import Issues
```
❌ FAIL API Analyzer
Error: No module named 'crewai'
```
**Solution**: Install missing dependencies
```bash
pip install -r requirements.txt
```

## Fallback Limitations

When running without Docker or MCP servers:

### Web Scraper Limitations
- **No JavaScript Execution**: Can't handle SPAs or dynamic content
- **Single Page Only**: Can't crawl multiple pages automatically
- **No Screenshots**: Can't capture visual content
- **No Browser Automation**: Can't interact with forms or buttons

### Workarounds
1. **Use Static Documentation**: Works well with static API docs
2. **Manual URL Lists**: Provide specific URLs to scrape
3. **Preprocessed Content**: Use pre-downloaded HTML files
4. **Alternative Sources**: Use OpenAPI specs or Postman collections

## Development Workflow

### Local Development (Docker-free)
```bash
# 1. Test agents locally
python docker_free_test.py

# 2. Run Streamlit interface
streamlit run interfaces/server_generator.py

# 3. Test specific functionality
python docker_free_test.py --test web_scraper --url https://api.example.com/docs
```

### Production Setup
```bash
# 1. Install Node.js and MCP servers
npm install -g @executeautomation/playwright-mcp-server

# 2. Install Docker for other MCP servers
# See MCP_MASTER_REFERENCE.md for details

# 3. Configure MCP servers
# Edit config/mcp-servers.yml
```

## Troubleshooting

### Python Path Issues
```bash
# If imports fail, set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Permission Issues
```bash
# On Windows, run as administrator if needed
# On Linux/Mac, check file permissions
chmod +x docker_free_test.py
```

### Environment Issues
```bash
# Check Python version (3.8+ required)
python --version

# Check installed packages
pip list | grep -E "(requests|beautifulsoup4|streamlit)"
```

## Next Steps

### After Successful Testing
1. **Install Full Stack**: Add Node.js and MCP servers for complete functionality
2. **Configure Authentication**: Set up Keycloak and Infisical (see ENV_VARIABLE_GUIDE.md)
3. **Deploy to Production**: Follow DEPLOYMENT_GUIDE.md

### For Development
1. **Add New Agents**: Follow the template in `templates/mcp-server-template/`
2. **Extend Functionality**: Add new tools and capabilities
3. **Improve Fallbacks**: Enhance fallback implementations

## Support

- **Documentation**: See `docs/` directory for detailed guides
- **Examples**: Check `examples/` for sample implementations
- **Testing**: Use `tests/` directory for validation scripts
- **Issues**: Report problems in the project repository

## Configuration

### Environment Variables
Create `.env` file in the ai-agents directory:
```env
# Optional: Configure logging level
LOG_LEVEL=INFO

# Optional: Configure API timeouts
HTTP_TIMEOUT=30
```

### Agent Configuration
Edit `config.json` to customize agent behavior:
```json
{
  "agents": {
    "web_scraper": {
      "max_retries": 3,
      "timeout": 30,
      "fallback_enabled": true
    },
    "api_analyzer": {
      "confidence_threshold": 0.8,
      "max_endpoints": 100
    }
  }
}
```

This Docker-free approach ensures that developers can start working with MC-PEA AI agents immediately, without complex setup requirements, while still providing a path to full functionality when needed.
