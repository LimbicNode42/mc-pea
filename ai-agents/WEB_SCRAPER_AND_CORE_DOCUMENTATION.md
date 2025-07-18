# 📁 Web Scraper & Core Module Documentation

## Overview

This document provides a comprehensive explanation of the purpose and functionality of each file and function in the MC-PEA AI agents system, specifically focusing on the `core/` and `agents/web_scraper/` modules.

## 🏗️ **Core Module (`core/`)**

The core module provides the foundation infrastructure for all MC-PEA AI agents, implementing the base framework, configuration management, and external service integrations.

### **1. `base_agent.py`** - Foundation for all AI agents

**Purpose**: Provides the abstract base class that all MC-PEA agents inherit from, implementing common functionality like message handling, task execution, and CrewAI integration.

#### **Key Classes**

##### `AgentConfig`
- **Purpose**: Pydantic model defining standardized agent configuration
- **Fields**: 
  - `name`: Agent identifier
  - `role`: Agent's role in the system
  - `goal`: Agent's primary objective
  - `backstory`: Context for the agent's behavior
  - `max_iterations`: Maximum execution iterations
  - `verbose`: Logging verbosity control
  - `temperature`: LLM temperature setting

##### `AgentMessage`
- **Purpose**: Standardized message structure for inter-agent communication
- **Fields**:
  - `sender`/`recipient`: Message routing
  - `message_type`: Categorizes message purpose
  - `content`: Message payload
  - `timestamp`: Message creation time
  - `correlation_id`: For tracking message chains

##### `AgentResult`
- **Purpose**: Standardized result format for all agent operations
- **Fields**:
  - `success`: Boolean operation status
  - `result`: Operation output data
  - `error`: Error message if failed
  - `metadata`: Additional context information

##### `BaseAgent` (Abstract Base Class)
- **Purpose**: Core agent functionality that all agents inherit

#### **Key Functions**

##### `__init__(config, logger)`
- **Purpose**: Initialize agent with configuration and setup infrastructure
- **Functionality**:
  - Sets up CrewAI integration
  - Initializes message queue for async communication
  - Registers for configuration hot-reload
  - Creates logger instance

##### `get_tools()` *(Abstract)*
- **Purpose**: Define agent-specific tools
- **Must be implemented**: By each concrete agent class
- **Returns**: List of tools available to the agent

##### `get_mcp_dependencies()`
- **Purpose**: Declare required MCP server dependencies
- **Returns**: List of MCP servers needed (fetch, memory, etc.)
- **Default**: Empty list (no dependencies)

##### `process_message(message)` *(Abstract)*
- **Purpose**: Handle incoming inter-agent messages
- **Must be implemented**: By each concrete agent class
- **Returns**: `AgentResult` with processing outcome

##### `execute_task(task)` *(Abstract)*
- **Purpose**: Execute specific tasks assigned to the agent
- **Must be implemented**: By each concrete agent class
- **Returns**: `AgentResult` with execution outcome

##### `start()` / `stop()`
- **Purpose**: Agent lifecycle management
- **Functionality**:
  - Controls agent running state
  - Starts/stops background message processing loop
  - Manages async task execution

##### `_message_loop()`
- **Purpose**: Background message processing with timeout handling
- **Functionality**:
  - Continuous message queue monitoring
  - Automatic message routing and processing
  - Error handling and logging

##### `_on_config_update(new_config)`
- **Purpose**: Handle configuration hot-reload events
- **Functionality**:
  - Updates agent settings dynamically
  - Recreates CrewAI agent with new parameters
  - Notifies registered callbacks

---

### **2. `config.py`** - Configuration management system

**Purpose**: Centralized configuration with hot-reload support, agent-specific profiles, and comprehensive LLM parameter management.

#### **Key Classes**

##### `AnthropicConfig`
- **Purpose**: Complete Claude API configuration matching CrewAI LLM parameters
- **Key Parameters**:
  - **Core**: `model`, `max_tokens`, `temperature`, `top_p`
  - **Advanced**: `presence_penalty`, `frequency_penalty`, `seed`
  - **Function calling**: `response_format`, `reasoning_effort`
  - **API**: `base_url`, `api_key`, `timeout`, `max_retries`

##### `AgentSpecificConfig`
- **Purpose**: Agent-type specific configuration overrides
- **Fields**:
  - `agent_type`: Identifies the agent category
  - `anthropic_overrides`: Custom Claude settings
  - `max_iterations`: Agent-specific iteration limits
  - `custom_settings`: Flexible additional configuration

##### `AgentProfilesConfig`
- **Purpose**: Predefined optimized profiles for different agent types

#### **Key Functions**

##### `_discover_agent_types()`
- **Purpose**: Dynamically discover agent types from directory structure
- **Functionality**:
  - Scans `agents/` directory for subdirectories
  - Returns list of available agent types
  - Fallback to known types if scan fails

##### `_get_default_config_for_agent(agent_type)`
- **Purpose**: Returns optimized configuration for specific agent types
- **Predefined Profiles**:
  - **`mcp_generator`**: High creativity, large output (Claude Opus 4)
  - **`validator`**: Fast, consistent validation (Claude Haiku)
  - **`api_analyzer`**: Balanced analysis capabilities (Claude Sonnet)
  - **`orchestrator`**: Advanced coordination (Claude Sonnet 4)

---

### **3. `agent_config_loader.py`** - Configuration file loader

**Purpose**: Loads and manages configurations from `agent_configs.json` with hot-reload support.

#### **Key Classes**

##### `AgentConfigLoader`
- **Purpose**: Main configuration file management

#### **Key Functions**

##### `__init__(config_file_path)`
- **Purpose**: Initialize loader with config file path
- **Default Path**: `ai-agents/agent_configs.json`
- **Functionality**: Automatically loads configuration on initialization

##### `_load_config()`
- **Purpose**: Load configuration from JSON file
- **Error Handling**: Creates default empty config if file missing
- **Logging**: Reports successful loads and errors

##### `get_agent_config(agent_name)`
- **Purpose**: Retrieve configuration for specific agent
- **Functionality**:
  - Merges agent-specific settings with global settings
  - Returns empty dict if agent not found
  - Prefixes global settings to avoid conflicts

##### `get_all_agent_names()`
- **Purpose**: List all configured agent names
- **Returns**: List of strings representing agent identifiers

##### `reload_config()`
- **Purpose**: Hot-reload configuration from file
- **Use Case**: Runtime configuration updates without restart

---

### **4. `anthropic_client.py`** - Claude AI integration ⭐ **AI-FIRST CORE**

**Purpose**: Wrapper for Anthropic Claude API with intelligent content analysis capabilities. This is the heart of the AI-first approach.

#### **Key Classes**

##### `AnthropicClient`
- **Purpose**: Claude API client for intelligent content analysis

#### **Key Functions**

##### `__init__(logger)`
- **Purpose**: Initialize Claude API client
- **Requirements**: `ANTHROPIC_API_KEY` environment variable
- **Model**: Uses Claude 3.5 Sonnet (latest)
- **Error Handling**: Raises ValueError if API key missing

##### `analyze_content_for_endpoints(content, source_url)` 🤖 **AI-POWERED**
- **Purpose**: **Core AI-first endpoint extraction**
- **Functionality**:
  - Creates detailed prompts for Claude analysis
  - Calls Claude API with optimized parameters
  - Parses JSON responses with fallback text parsing
  - Returns structured endpoint data with confidence scores
- **Input**: Web page content and source URL
- **Output**: Dictionary with endpoints, parameters, and metadata

##### `analyze_content_for_parameters(content, endpoint_path)` 🤖 **AI-POWERED**
- **Purpose**: **Core AI-first parameter extraction**
- **Functionality**:
  - Focuses on specific endpoint or general parameter discovery
  - Uses Claude for intelligent parameter type detection
  - Extracts constraints, defaults, and validation rules
- **Input**: Content and optional endpoint focus
- **Output**: Structured parameter data with types and descriptions

##### `_create_endpoint_analysis_prompt(content, source_url)`
- **Purpose**: Craft detailed prompts for Claude endpoint analysis
- **Features**:
  - Content truncation for token limits
  - Structured JSON response format specification
  - Comprehensive analysis instructions
  - Pattern recognition guidance

##### `_create_parameter_analysis_prompt(content, endpoint_path)`
- **Purpose**: Create focused prompts for parameter extraction
- **Features**:
  - Parameter type detection (string, integer, boolean, etc.)
  - Location identification (path, query, body, header)
  - Constraint and validation extraction

##### `_extract_json_from_response(response_text)`
- **Purpose**: Parse structured JSON from Claude's text responses
- **Functionality**:
  - Regex-based JSON block detection
  - Multiple parsing strategies
  - Fallback handling for malformed JSON

##### `_parse_text_response(response_text, source_url)`
- **Purpose**: Fallback text parsing when JSON extraction fails
- **Functionality**:
  - Basic regex-based endpoint detection
  - Creates structured response format
  - Lower confidence scores for fallback results

---

### **5. `mcp_client.py`** - MCP server communication

**Purpose**: Simple client for communicating with MCP servers, providing abstraction layer with fallback capabilities.

#### **Key Classes**

##### `SimpleMCPClient`
- **Purpose**: Basic MCP server client implementation

##### `MCPClientManager`
- **Purpose**: Manages multiple MCP client instances

#### **Key Functions**

##### `SimpleMCPClient.__init__(server_command, logger)`
- **Purpose**: Initialize MCP client for specific server
- **Parameters**:
  - `server_command`: Command to start MCP server
  - `logger`: Optional logging instance

##### `start_server()`
- **Purpose**: Start the MCP server process
- **Current Implementation**: Mock server start (placeholder)
- **Future**: Will spawn actual MCP server processes

##### `call_tool(tool_name, params)`
- **Purpose**: Call tools on MCP servers
- **Supported Tools**:
  - `fetch_webpage`: Web content retrieval
- **Fallback**: Uses requests/BeautifulSoup if MCP unavailable

##### `_fetch_webpage_fallback(params)`
- **Purpose**: Fallback web fetching when MCP server unavailable
- **Features**:
  - HTTP request with proper user agent
  - BeautifulSoup HTML parsing
  - Link extraction with absolute URL conversion
  - Heading extraction and text cleaning
  - Content length and link count limits

##### `MCPClientManager.get_client(server_name)`
- **Purpose**: Get or create MCP client for specific server
- **Supported Servers**:
  - `fetch` / `mcp-server-fetch`: Web content retrieval
  - `memory`: State tracking and caching
- **Fallback**: Creates fallback clients if servers unavailable

##### `shutdown_all()`
- **Purpose**: Cleanup all MCP client connections
- **Functionality**: Terminates server processes and clears client registry

---

## 🕷️ **Web Scraper Module (`agents/web_scraper/`)**

The web scraper module implements a modular, AI-first web scraping solution specifically designed for API documentation extraction.

### **1. `web_scraper.py`** - Main orchestrator agent

**Purpose**: Coordinates web crawling and content scraping using modular components and MCP servers.

#### **Key Classes**

##### `WebScraperAgent`
- **Purpose**: Main agent inheriting from BaseAgent
- **Architecture**: Orchestrates WebCrawler and ContentScraper modules

#### **Key Functions**

##### `__init__(anthropic_client, crawl_depth)`
- **Purpose**: Initialize web scraper agent with modular components
- **Configuration Loading**:
  - Loads settings from `agent_configs.json`
  - Creates AgentConfig with role, goal, backstory
  - Initializes crawling parameters with validation
- **Component Initialization**:
  - Creates WebCrawler and ContentScraper instances
  - Sets up MCP client manager
  - Configures depth limits and crawling rules

##### `get_mcp_dependencies()`
- **Purpose**: Declare required MCP server dependencies
- **Dependencies**:
  - **fetch server**: `mcp-server-fetch` for web content retrieval
  - **memory server**: `mcp-server-memory` for state tracking
- **Installation Info**: Includes multiple installation methods (uv, pip, docker)

##### `crawl_and_scrape(base_url, query)` 🎯 **MAIN METHOD**
- **Purpose**: Complete crawling and scraping workflow
- **Process**:
  1. Initialize crawling from base URL
  2. Use WebCrawler for link discovery up to configured depth
  3. Use ContentScraper for AI-powered content analysis
  4. Track state with MCP memory server
  5. Return comprehensive results with statistics

##### `scrape_api_documentation(base_url, query)`
- **Purpose**: Legacy backward-compatible method
- **Functionality**: Delegates to `crawl_and_scrape` for consistency

##### `get_crawling_config()`
- **Purpose**: Return current crawling configuration
- **Returns**: Dictionary with depth, domain restrictions, delays, etc.

##### `update_crawl_depth(new_depth)`
- **Purpose**: Dynamically update crawling depth with validation
- **Validation**: Ensures depth within min/max bounds
- **Updates**: Reconfigures both WebCrawler and ContentScraper

##### `get_modular_components()`
- **Purpose**: Return information about modular components
- **Returns**: Details about WebCrawler and ContentScraper instances

##### `cleanup()` / `__del__()`
- **Purpose**: Resource cleanup and MCP client shutdown
- **Functionality**: Ensures proper cleanup of MCP connections

---

### **2. `web_crawler.py`** - Link discovery and crawling

**Purpose**: Discovers and collects links up to configured depth using breadth-first search and MCP fetch server.

#### **Key Classes**

##### `WebCrawler`
- **Purpose**: Handles breadth-first web crawling with depth limits

#### **Key Functions**

##### `__init__(config, logger, mcp_client)`
- **Purpose**: Initialize crawler with configuration and MCP client
- **Configuration**:
  - Crawl depth limits (min, max, default)
  - External link following policy
  - Domain page limits and request delays
  - Robots.txt respect setting

##### `normalize_url(url)`
- **Purpose**: Normalize URLs for consistent comparison
- **Functionality**:
  - Convert scheme and domain to lowercase
  - Remove trailing slashes (except root)
  - Remove URL fragments
  - Preserve query parameters

##### `is_valid_url(url, base_domain)`
- **Purpose**: Validate URLs against crawling restrictions
- **Validation Rules**:
  - Must use HTTP/HTTPS schemes
  - Domain restrictions (internal vs external)
  - Page count limits per domain
  - File type filtering (skip PDFs, images, etc.)

##### `extract_links_from_page(page_content, base_url)` 🔧 **FIXED**
- **Purpose**: Extract links from MCP fetch server response
- **Bug Fix**: Handles both 'href' and 'url' formats from MCP server
- **Functionality**:
  - Parses MCP server response format
  - Converts relative to absolute URLs
  - Includes regex fallback for additional link discovery
  - Returns normalized absolute URLs

##### `fetch_page_via_mcp(url, query)`
- **Purpose**: Fetch web pages using MCP fetch server
- **Features**:
  - Calls MCP fetch_webpage tool
  - Tracks domain page counts
  - Adds metadata (timestamp, domain, query)
  - Error handling with structured responses

##### `crawl_website(start_url, query)` 🎯 **MAIN CRAWLING METHOD**
- **Purpose**: Perform breadth-first crawling up to depth limit
- **Algorithm**:
  1. Initialize queue with start URL at depth 0
  2. Process URLs level by level (BFS)
  3. Extract links from each page
  4. Add new links to queue at next depth level
  5. Respect depth limits and domain restrictions
  6. Track visited URLs to prevent cycles

##### `get_crawl_statistics()`
- **Purpose**: Return crawling metrics and statistics
- **Metrics**:
  - Total pages visited
  - Pages per domain breakdown
  - Maximum depth reached
  - Crawling duration and performance

---

### **3. `content_scraper.py`** - AI-powered content analysis ⭐ **AI-FIRST CORE**

**Purpose**: Extracts API endpoints and parameters using Claude AI with strict no-fallback policy.

#### **Key Classes**

##### `ContentScraper`
- **Purpose**: Intelligent content extraction using AI-first approach

#### **Key Functions**

##### `__init__(config, logger, mcp_client)`
- **Purpose**: Initialize content scraper with strict AI-first enforcement
- **🚨 CRITICAL**: **ENFORCES Claude dependency** - No fallback methods allowed
- **Functionality**:
  - Initializes AnthropicClient for Claude API
  - Raises RuntimeError if Claude unavailable
  - Sets up tracking for scraped pages and extracted endpoints
  - **NO FALLBACK PATTERNS** - Pure AI approach only

##### `extract_endpoints_from_content(content, source_url)` 🤖 **PURE AI**
- **Purpose**: **Core AI-first endpoint extraction** using Claude
- **Process**:
  1. Validates Claude client availability (fails if unavailable)
  2. Calls `AnthropicClient.analyze_content_for_endpoints()`
  3. Adds extraction metadata (source, timestamp, method)
  4. Returns structured endpoint data with confidence scores
- **NO FALLBACKS**: Raises RuntimeError if Claude unavailable

##### `extract_api_parameters(content, endpoint_path)` 🤖 **PURE AI**
- **Purpose**: **Core AI-first parameter extraction** using Claude
- **Process**:
  1. Validates Claude client availability (fails if unavailable)
  2. Calls `AnthropicClient.analyze_content_for_parameters()`
  3. Adds parameter metadata and endpoint association
  4. Returns structured parameter data with types and constraints
- **NO FALLBACKS**: Raises RuntimeError if Claude unavailable

##### `scrape_page_content(page_data)`
- **Purpose**: Main content scraping orchestration
- **Process**:
  1. Check if page already scraped (avoid duplicates)
  2. Extract endpoints using Claude AI
  3. Extract parameters using Claude AI
  4. Store results in MCP memory server
  5. Update internal tracking and statistics

##### `store_scraped_page_in_memory(url, content_summary)`
- **Purpose**: Store scraping results in MCP memory server
- **Functionality**:
  - Creates structured memory entry
  - Includes timestamp, endpoint count, status
  - Uses MCP memory server for persistence
  - Enables deduplication across sessions

##### `check_if_page_scraped(url)`
- **Purpose**: Prevent duplicate processing of pages
- **Functionality**:
  - Queries MCP memory server for existing entries
  - Returns scraping status and metadata
  - Enables efficient resource utilization

##### `get_scraping_statistics()`
- **Purpose**: Return content extraction metrics
- **Metrics**:
  - Total pages scraped
  - Total endpoints extracted
  - Endpoints by HTTP method breakdown
  - Parameter extraction counts

##### `cleanup()`
- **Purpose**: Clean up resources including Anthropic client
- **Functionality**: Ensures proper cleanup of Claude API connections
