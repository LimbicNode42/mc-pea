"""
MCP API Integrator Agent

Agent responsible for integrating extracted API usage details into the generated MCP server.
Takes the API extraction results and updates the MCP server with tools and resources based on the API endpoints.
"""

from crewai import Agent, LLM
from crewai.tools import tool
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import os
import json
import time
import shutil
import re
import logging
from datetime import datetime
from typing import Dict, Any, List
from urllib.parse import urlparse
from core.agent_workers_config_loader import get_agent_config

# Set up file logging for debugging
log_dir = "debug_logs"
os.makedirs(log_dir, exist_ok=True)
log_filename = f"{log_dir}/mcp_api_integrator_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Clear any existing logging configuration
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Configure both file and console logging with explicit configuration
file_handler = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
console_handler = logging.StreamHandler()

# Set the format for both handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Set levels
file_handler.setLevel(logging.DEBUG)
console_handler.setLevel(logging.INFO)

# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Ensure immediate writing to file
file_handler.flush()

logger.info(f"🚀 MCP API Integrator Agent debug logging started - log file: {log_filename}")
print(f"📄 Debug log file created: {log_filename}")


class MCPAPIIntegratorAgent(Agent):
    """
    Agent responsible for integrating extracted API details into the MCP server.
    Updates the generated MCP server with tools and resources based on API extraction results.
    """

    def __init__(self, website_url: str = None, server_name: str = None, mcp_server_path: str = None, **kwargs):
        logger.info(f"🚀 MCPAPIIntegratorAgent.__init__ called with website_url={website_url}, server_name={server_name}, mcp_server_path={mcp_server_path}")
        
        # Force log flush
        for handler in logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        
        load_dotenv()
        
        # Set default values if not provided
        logger.debug("Setting default values if not provided...")
        if website_url is None:
            website_url = "https://api.example.com"
            logger.debug(f"Set default website_url: {website_url}")
        
        # Generate server name from website URL if not provided
        logger.debug("Generating server name from URL...")
        if not server_name:
            parsed = urlparse(website_url)
            domain = parsed.netloc.replace('www.', '').replace('.', '-')
            server_name = f"{domain}-api-mcp-server"
            logger.debug(f"Generated server_name: {server_name}")
        
        # Use custom server path if provided, otherwise use default
        logger.debug("Setting up server path...")
        if mcp_server_path:
            if os.path.isabs(mcp_server_path):
                server_path = mcp_server_path
            else:
                # Relative to current working directory
                server_path = os.path.abspath(mcp_server_path)
            logger.debug(f"Using custom server_path: {server_path}")
        else:
            # Default server path
            server_path = os.path.join(os.getcwd(), '..', 'mcp-servers', f"{server_name}")
            logger.debug(f"Using default server_path: {server_path}")

        # Validate server directory exists or can be created
        logger.debug(f"Creating server directory: {server_path}")
        os.makedirs(server_path, exist_ok=True)

        # Load agent configuration
        logger.info("Loading agent configuration...")
        config = get_agent_config('mcp_api_integrator_agent')
        logger.debug(f"Loaded config type: {type(config)}")
        logger.debug(f"Config content: {config}")
        
        # Add error handling for None config with detailed debugging
        if config is None:
            logger.error("❌ Config is None!")
            raise ValueError("Could not load configuration for 'mcp_api_integrator_agent'. Check that the config file exists and is valid.")
        
        # Add defensive coding for missing config values
        logger.debug("Extracting LLM config...")
        llm_config = config.get("llm", "")
        logger.debug(f"LLM config: {llm_config}")
        if not llm_config:
            logger.error("❌ No LLM configuration found!")
            raise ValueError("No LLM configuration found in agent config")

        logger.debug("Setting up LLM based on config...")
        if "claude" in llm_config:
            logger.info("🧠 Setting up Claude LLM...")
            llm = ChatAnthropic(
                model=config.get("llm", "claude-sonnet-4"),
                max_tokens=config.get("max_output_tokens", 8000),
                temperature=config.get("temperature", 0.2),
                max_retries=1,  # Reduced from config to prevent rapid retries
                default_request_timeout=120,  # Increase timeout
                anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            )
            print("Using Claude LLM for MCP API integration (with rate limiting)")
            logger.info("✅ Claude LLM configured successfully")
        elif "gemini" in llm_config:
            logger.info("🧠 Setting up Gemini LLM...")
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if not google_api_key:
                logger.error("❌ GOOGLE_API_KEY not found!")
                raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini models")
            
            # Extract just the model name (remove the provider prefix)
            model_name = config.get("llm", "gemini-2.5-flash").replace("gemini/", "")
            logger.debug(f"Extracted model name: {model_name}")
            
            # Use CrewAI's LLM class for Gemini models
            llm = LLM(
                model=f"gemini/{model_name}",
                api_key=google_api_key,
                max_tokens=config.get("max_input_tokens", 3000000),
                max_completion_tokens=config.get("max_output_tokens", 1000000),
                temperature=config.get("temperature", 0.2),
                reasoning_effort=config.get("reasoning_effort", "medium"),
            )
            print(f"Using Gemini LLM for MCP API integration: {model_name}")
            logger.info("✅ Gemini LLM configured successfully")
        else:
            logger.error(f"❌ Unsupported LLM type: {llm_config}")
            raise ValueError(f"Unsupported LLM type in configuration: {llm_config}")
        
        # Initialize parent class with proper agent configuration (empty tools initially)
        logger.info("🏗️ Initializing parent Agent class...")
        super().__init__(
            role=config.get("role", "MCP API Integrator"),
            goal=config.get("goal", "Integrate API extraction results into MCP server"),
            backstory=config.get("backstory", "Expert TypeScript developer for MCP servers"),
            llm=llm,
            tools=[],  # Start with empty tools, add them after initialization
            respect_context_window=config.get('respect_context_window', True),
            cache=config.get('cache', False),
            reasoning=config.get('reasoning', False),
            max_iter=config.get('max_iterations', 10),
            max_retry_limit=config.get('max_retry_limit', 1),
            verbose=config.get('verbose', True),
            allow_delegation=config.get('allow_delegation', False),
            **kwargs
        )
        logger.info("✅ Parent Agent class initialized successfully")
        
        # Store instance variables after super().__init__() to avoid Pydantic issues
        logger.info("📝 Storing instance variables...")
        object.__setattr__(self, 'website_url', website_url)
        object.__setattr__(self, 'server_name', server_name)
        object.__setattr__(self, 'mcp_server_path', server_path)
        logger.debug(f"Stored: website_url={website_url}, server_name={server_name}, mcp_server_path={server_path}")
        
        # Store workflow state
        logger.debug("Setting up workflow state...")
        object.__setattr__(self, '_extraction_results', None)
        object.__setattr__(self, '_last_call_time', 0)  # For rate limiting
        object.__setattr__(self, '_min_call_interval', float(os.getenv('MCP_INTEGRATOR_RATE_LIMIT', '2.0')))
        
        # Create concrete tools that provide actual functionality (AFTER super().__init__)
        logger.info("🔧 Creating tool functions...")
        @tool("read_file")
        def read_file_tool(context: str = "{}") -> str:
            """Read the contents of a file."""
            logger.debug(f"🔧 read_file_tool called with context={context}")
            # Extract file_path from context or use default
            import json
            try:
                ctx = json.loads(context) if isinstance(context, str) else context
                file_path = ctx.get('file_path', 'package.json')  # Default to package.json
            except:
                file_path = 'package.json'  # Fallback
            logger.debug(f"🔧 read_file_tool using file_path={file_path}")
            result = str(self.read_file_method(file_path))
            logger.debug(f"🔧 read_file_tool result: {result[:100]}...")
            return result
        
        @tool("write_file")
        def write_file_tool(context: str = "{}") -> str:
            """Write content to a file."""
            logger.debug(f"🔧 write_file_tool called with context={context}")
            # Extract parameters from context
            import json
            try:
                ctx = json.loads(context) if isinstance(context, str) else context
                file_path = ctx.get('file_path', 'output.txt')
                content = ctx.get('content', '')
            except:
                file_path = 'output.txt'
                content = ''
            logger.debug(f"🔧 write_file_tool using file_path={file_path}, content_length={len(content)}")
            result = str(self.write_file_method(file_path, content))
            logger.debug(f"🔧 write_file_tool result: {result}")
            return result
        
        @tool("copy_template")
        def copy_template_tool(context: str = "{}") -> str:
            """Copy template files to destination."""
            logger.debug(f"🔧 copy_template_tool called with context={context}")
            # Extract parameters from context or use defaults
            import json
            try:
                ctx = json.loads(context) if isinstance(context, str) else context
                template_path = ctx.get('template_path', '../templates/mcp-server-template')
                destination_path = ctx.get('destination_path', './output')
            except:
                template_path = '../templates/mcp-server-template'
                destination_path = './output'
            logger.debug(f"🔧 copy_template_tool using template_path={template_path}, destination_path={destination_path}")
            result = str(self.copy_template_method(template_path, destination_path))
            logger.debug(f"🔧 copy_template_tool result: {result}")
            return result
        
        @tool("list_directory")
        def list_directory_tool(context: str = "{}") -> str:
            """List contents of a directory."""
            logger.debug(f"🔧 list_directory_tool called with context={context}")
            # Extract directory path from context
            import json
            try:
                ctx = json.loads(context) if isinstance(context, str) else context
                dir_path = ctx.get('dir_path', '.')
            except:
                dir_path = '.'
            logger.debug(f"🔧 list_directory_tool using dir_path={dir_path}")
            result = str(self.list_directory_method(dir_path))
            logger.debug(f"🔧 list_directory_tool result: {result}")
            return result
        
        @tool("generate_typescript_tool")
        def generate_typescript_tool_tool(context: str = "{}") -> str:
            """Generate TypeScript code for an MCP tool based on API endpoint data."""
            logger.debug(f"🔧 generate_typescript_tool_tool called with context={context}")
            # Extract parameters from context
            import json
            try:
                ctx = json.loads(context) if isinstance(context, str) else context
                tool_name = ctx.get('tool_name', 'default_tool')
                endpoint_data = ctx.get('endpoint_data', '{"method": "GET", "path": "/", "description": "Default endpoint"}')
            except:
                tool_name = 'default_tool'
                endpoint_data = '{"method": "GET", "path": "/", "description": "Default endpoint"}'
            logger.debug(f"🔧 generate_typescript_tool_tool using tool_name={tool_name}, endpoint_data_length={len(endpoint_data)}")
            result = str(self.generate_typescript_tool_method(tool_name, endpoint_data))
            logger.debug(f"🔧 generate_typescript_tool_tool result: {result[:200]}...")
            return result
        
        @tool("generate_typescript_resource")
        def generate_typescript_resource_tool(context: str = "{}") -> str:
            """Generate TypeScript code for an MCP resource based on API endpoint data."""
            logger.debug(f"🔧 generate_typescript_resource_tool called with context={context}")
            # Extract parameters from context
            import json
            try:
                ctx = json.loads(context) if isinstance(context, str) else context
                resource_name = ctx.get('resource_name', 'default_resource')
                endpoint_data = ctx.get('endpoint_data', '{"method": "GET", "path": "/", "description": "Default resource"}')
            except:
                resource_name = 'default_resource'
                endpoint_data = '{"method": "GET", "path": "/", "description": "Default resource"}'
            logger.debug(f"🔧 generate_typescript_resource_tool using resource_name={resource_name}, endpoint_data_length={len(endpoint_data)}")
            result = str(self.generate_typescript_resource_method(resource_name, endpoint_data))
            logger.debug(f"🔧 generate_typescript_resource_tool result: {result[:200]}...")
            return result
        
        @tool("validate_typescript")
        def validate_typescript_tool(context: str = "{}") -> str:
            """Validate TypeScript file syntax."""
            logger.debug(f"🔧 validate_typescript_tool called with context={context}")
            # Extract file path from context
            import json
            try:
                ctx = json.loads(context) if isinstance(context, str) else context
                file_path = ctx.get('file_path', './src/index.ts')
            except:
                file_path = './src/index.ts'
            logger.debug(f"🔧 validate_typescript_tool using file_path={file_path}")
            result = str(self.validate_typescript_method(file_path))
            logger.debug(f"🔧 validate_typescript_tool result: {result}")
            return result
        
        # Add tools to the agent (like in the working base generator)
        logger.info("🧰 Adding tools to agent...")
        self.tools.extend([
            read_file_tool,
            write_file_tool,
            copy_template_tool,
            list_directory_tool,
            generate_typescript_tool_tool,
            generate_typescript_resource_tool,
            validate_typescript_tool
        ])
        logger.info(f"✅ Agent initialization complete! Total tools: {len(self.tools)}")
        
        # Force final log flush
        for handler in logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
    
    def read_file_method(self, file_path: str) -> Dict[str, Any]:
        """Read the contents of a file."""
        logger.debug(f"📖 read_file_method called with file_path={file_path}")
        try:
            # Resolve path relative to server directory if it's a relative path
            if not os.path.isabs(file_path):
                actual_path = os.path.join(self.mcp_server_path, file_path)
            else:
                actual_path = file_path
            logger.debug(f"📖 Resolved path: {actual_path}")
            
            logger.debug(f"📖 Attempting to read file: {actual_path}")
            with open(actual_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"📖 Successfully read {len(content)} characters from {actual_path}")
            result = {
                "success": True,
                "content": content,
                "file_path": actual_path
            }
            logger.debug(f"📖 read_file_method returning success result")
            return result
        except Exception as e:
            logger.error(f"📖 Error reading file {file_path}: {str(e)}")
            result = {
                "success": False,
                "error": f"Error reading file {file_path}: {str(e)}"
            }
            logger.debug(f"📖 read_file_method returning error result: {result}")
            return result
    
    def write_file_method(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to a file."""
        logger.debug(f"✍️ write_file_method called with file_path={file_path}, content_length={len(content)}")
        try:
            # Resolve path relative to server directory if it's a relative path
            if not os.path.isabs(file_path):
                actual_path = os.path.join(self.mcp_server_path, file_path)
            else:
                actual_path = file_path
            logger.debug(f"✍️ Resolved path: {actual_path}")
            
            logger.debug(f"✍️ Creating directory for: {os.path.dirname(actual_path)}")
            os.makedirs(os.path.dirname(actual_path), exist_ok=True)
            logger.debug(f"✍️ Writing {len(content)} characters to {actual_path}")
            with open(actual_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.debug(f"✍️ Successfully wrote to {actual_path}")
            result = {
                "success": True,
                "message": f"Successfully wrote to {actual_path}",
                "file_path": actual_path
            }
            logger.debug(f"✍️ write_file_method returning success result")
            return result
        except Exception as e:
            logger.error(f"✍️ Error writing file {file_path}: {str(e)}")
            result = {
                "success": False,
                "error": f"Error writing file {file_path}: {str(e)}"
            }
            logger.debug(f"✍️ write_file_method returning error result: {result}")
            return result
    
    def copy_template_method(self, template_path: str, destination_path: str) -> Dict[str, Any]:
        """Copy template files to destination."""
        logger.debug(f"📁 copy_template_method called with template_path={template_path}, destination_path={destination_path}")
        try:
            logger.debug(f"📁 Checking if destination exists: {destination_path}")
            if os.path.exists(destination_path):
                logger.debug(f"📁 Removing existing destination: {destination_path}")
                shutil.rmtree(destination_path)
            logger.debug(f"📁 Copying tree from {template_path} to {destination_path}")
            shutil.copytree(template_path, destination_path)
            logger.debug(f"📁 Successfully copied template")
            result = {
                "success": True,
                "message": f"Successfully copied template from {template_path} to {destination_path}",
                "template_path": template_path,
                "destination_path": destination_path
            }
            logger.debug(f"📁 copy_template_method returning success result")
            return result
        except Exception as e:
            logger.error(f"📁 Error copying template: {str(e)}")
            result = {
                "success": False,
                "error": f"Error copying template: {str(e)}"
            }
            logger.debug(f"📁 copy_template_method returning error result: {result}")
            return result
    
    def list_directory_method(self, dir_path: str) -> Dict[str, Any]:
        """List contents of a directory."""
        logger.debug(f"📂 list_directory_method called with dir_path={dir_path}")
        try:
            # Resolve path relative to server directory if it's a relative path
            if not os.path.isabs(dir_path):
                actual_path = os.path.join(self.mcp_server_path, dir_path)
            else:
                actual_path = dir_path
            logger.debug(f"📂 Resolved path: {actual_path}")
            
            logger.debug(f"📂 Checking if directory exists: {actual_path}")
            if not os.path.exists(actual_path):
                logger.warning(f"📂 Directory does not exist: {actual_path}")
                result = {
                    "success": False,
                    "error": f"Directory {actual_path} does not exist"
                }
                logger.debug(f"📂 list_directory_method returning not found result: {result}")
                return result
            logger.debug(f"📂 Listing contents of: {actual_path}")
            items = os.listdir(actual_path)
            logger.debug(f"📂 Found {len(items)} items: {items}")
            result = {
                "success": True,
                "items": items,
                "directory": actual_path
            }
            logger.debug(f"📂 list_directory_method returning success result")
            return result
        except Exception as e:
            logger.error(f"📂 Error listing directory {dir_path}: {str(e)}")
            result = {
                "success": False,
                "error": f"Error listing directory {dir_path}: {str(e)}"
            }
            logger.debug(f"📂 list_directory_method returning error result: {result}")
            return result
    
    def generate_typescript_tool_method(self, tool_name: str, endpoint_data: str) -> Dict[str, Any]:
        """Generate TypeScript code for an MCP tool based on API endpoint data."""
        logger.debug(f"⚙️ generate_typescript_tool_method called with tool_name={tool_name}, endpoint_data_length={len(endpoint_data)}")
        try:
            logger.debug(f"⚙️ Parsing endpoint data as JSON...")
            endpoint = json.loads(endpoint_data)
            logger.debug(f"⚙️ Parsed endpoint: {endpoint}")
            logger.debug(f"⚙️ Calling _generate_tool_typescript_code...")
            # Use the advanced TypeScript generation method
            code = self._generate_tool_typescript_code(tool_name, endpoint)
            logger.debug(f"⚙️ Generated {len(code)} characters of TypeScript code")
            result = {
                "success": True,
                "typescript_code": code,
                "tool_name": tool_name
            }
            logger.debug(f"⚙️ generate_typescript_tool_method returning success result")
            return result
        except Exception as e:
            logger.error(f"⚙️ Error generating TypeScript tool: {str(e)}")
            result = {
                "success": False,
                "error": f"Error generating TypeScript tool: {str(e)}"
            }
            logger.debug(f"⚙️ generate_typescript_tool_method returning error result: {result}")
            return result
    
    def generate_typescript_resource_method(self, resource_name: str, endpoint_data: str) -> Dict[str, Any]:
        """Generate TypeScript code for an MCP resource based on API endpoint data."""
        logger.debug(f"🔗 generate_typescript_resource_method called with resource_name={resource_name}, endpoint_data_length={len(endpoint_data)}")
        try:
            logger.debug(f"🔗 Parsing endpoint data as JSON...")
            endpoint = json.loads(endpoint_data)
            logger.debug(f"🔗 Parsed endpoint: {endpoint}")
            logger.debug(f"🔗 Calling _generate_resource_typescript_code...")
            # Use the advanced TypeScript generation method
            code = self._generate_resource_typescript_code(resource_name, endpoint)
            logger.debug(f"🔗 Generated {len(code)} characters of TypeScript code")
            result = {
                "success": True,
                "typescript_code": code,
                "resource_name": resource_name
            }
            logger.debug(f"🔗 generate_typescript_resource_method returning success result")
            return result
        except Exception as e:
            logger.error(f"🔗 Error generating TypeScript resource: {str(e)}")
            result = {
                "success": False,
                "error": f"Error generating TypeScript resource: {str(e)}"
            }
            logger.debug(f"🔗 generate_typescript_resource_method returning error result: {result}")
            return result
    
    def validate_typescript_method(self, file_path: str) -> Dict[str, Any]:
        """Validate TypeScript file syntax."""
        logger.debug(f"✅ validate_typescript_method called with file_path={file_path}")
        try:
            logger.debug(f"✅ Reading file for validation: {file_path}")
            # Simple validation - check if file can be read and has basic TS structure
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"✅ Read {len(content)} characters for validation")
            
            # Basic syntax checks
            logger.debug(f"✅ Checking for MCP registrations...")
            has_tool_registration = 'server.registerTool' in content
            has_resource_registration = 'server.registerResource' in content
            logger.debug(f"✅ Tool registration found: {has_tool_registration}")
            logger.debug(f"✅ Resource registration found: {has_resource_registration}")
            
            if has_tool_registration or has_resource_registration:
                result = {
                    "success": True,
                    "message": f"TypeScript file {file_path} appears valid",
                    "has_tools": has_tool_registration,
                    "has_resources": has_resource_registration
                }
                logger.debug(f"✅ validate_typescript_method returning success result")
                return result
            else:
                result = {
                    "success": False,
                    "warning": f"Warning: {file_path} may not contain proper MCP registrations"
                }
                logger.warning(f"✅ No MCP registrations found in {file_path}")
                logger.debug(f"✅ validate_typescript_method returning warning result: {result}")
                return result
        except Exception as e:
            logger.error(f"✅ Error validating TypeScript file {file_path}: {str(e)}")
            result = {
                "success": False,
                "error": f"Error validating TypeScript file {file_path}: {str(e)}"
            }
            logger.debug(f"✅ validate_typescript_method returning error result: {result}")
            return result
    
    def _apply_rate_limiting(self):
        """Apply rate limiting delay between LLM calls to prevent rate limit errors."""
        current_time = time.time()
        time_since_last_call = current_time - self._last_call_time
        
        if time_since_last_call < self._min_call_interval:
            delay = self._min_call_interval - time_since_last_call
            print(f"⏱️ Rate limiting: waiting {delay:.1f}s before next API call")
            time.sleep(delay)
        
        self._last_call_time = time.time()
    
    def set_extraction_results(self, extraction_results: List[Dict[str, Any]]) -> None:
        """Set the extraction results for processing."""
        logger.info(f"📋 set_extraction_results called with {len(extraction_results)} results")
        logger.debug(f"📋 Extraction results: {extraction_results}")
        self._extraction_results = extraction_results
        logger.debug(f"📋 Extraction results stored successfully")
    
    def _generate_tool_name(self, path: str, method: str) -> str:
        """Generate a clean tool name from endpoint information."""
        # Clean the path to create a valid identifier
        if path:
            # Remove leading slash and replace special characters
            clean_path = re.sub(r'[^a-zA-Z0-9_]', '_', path.lstrip('/'))
            # Remove multiple underscores
            clean_path = re.sub(r'_+', '_', clean_path)
            # Remove trailing underscores
            clean_path = clean_path.strip('_')
            return f"{method.lower()}_{clean_path}" if clean_path else f"{method.lower()}_endpoint"
        else:
            return f"{method.lower()}_endpoint"
    
    def _generate_resource_name(self, path: str) -> str:
        """Generate a clean resource name from endpoint information."""
        if path:
            # Remove leading slash and replace special characters
            clean_path = re.sub(r'[^a-zA-Z0-9_]', '_', path.lstrip('/'))
            # Remove multiple underscores
            clean_path = re.sub(r'_+', '_', clean_path)
            # Remove trailing underscores
            clean_path = clean_path.strip('_')
            return f"{clean_path}_resource" if clean_path else "api_resource"
        else:
            return "api_resource"
    
    def _generate_tool_typescript_code(self, tool_name: str, endpoint_data: Dict[str, Any]) -> str:
        """Generate TypeScript code for an MCP tool."""
        logger.debug(f"🛠️ _generate_tool_typescript_code called with tool_name={tool_name}")
        logger.debug(f"🛠️ Endpoint data: {endpoint_data}")
        
        method = endpoint_data.get('method', 'GET').upper()
        path = endpoint_data.get('path', '')
        description = endpoint_data.get('description', f'{method} {path}')
        parameters = endpoint_data.get('parameters', [])
        
        logger.debug(f"🛠️ Extracted: method={method}, path={path}, description={description}, parameters={len(parameters)}")
        
        # Generate parameter schema
        schema_properties = {}
        required_params = []
        
        logger.debug(f"🛠️ Processing {len(parameters)} parameters...")
        for param in parameters:
            param_name = param.get('name', 'unknown')
            param_type = param.get('type', 'string')
            param_required = param.get('required', False)
            param_description = param.get('description', '')
            
            logger.debug(f"🛠️ Processing parameter: {param_name} ({param_type}, required={param_required})")
            
            # Map API parameter types to JSON schema types
            if param_type in ['integer', 'int']:
                schema_type = 'number'
            elif param_type in ['boolean', 'bool']:
                schema_type = 'boolean'
            else:
                schema_type = 'string'
            
            schema_properties[param_name] = {
                'type': schema_type,
                'description': param_description
            }
            
            if param_required:
                required_params.append(param_name)
        
        logger.debug(f"🛠️ Generated schema properties: {schema_properties}")
        logger.debug(f"🛠️ Required parameters: {required_params}")
        
        # Generate the tool code
        properties_str = json.dumps(schema_properties, indent=6)
        required_str = json.dumps(required_params)
        
        body_code = ""
        if method in ['POST', 'PUT', 'PATCH']:
            body_code = f'''if (["{method}"].includes("{method}")) {{
        requestOptions.body = JSON.stringify(params);
      }}'''
            logger.debug(f"🛠️ Added body code for {method} method")
        
        logger.debug(f"🛠️ Generating final TypeScript code...")
        code = f'''server.registerTool(
  {{
    name: "{tool_name}",
    description: "{description}",
    inputSchema: {{
      type: "object",
      properties: {properties_str},
      required: {required_str}
    }}
  }},
  async (params) => {{
    try {{
      // Extract parameters
      const {{ {', '.join(schema_properties.keys())} }} = params;
      
      // Build URL with path parameters
      let url = `${{BASE_URL}}{path}`;
      
      // Build request options
      const requestOptions: RequestInit = {{
        method: "{method}",
        headers: {{
          "Content-Type": "application/json",
          ...getAuthHeaders()
        }}
      }};
      
      // Add body for POST/PUT/PATCH requests
      {body_code}
      
      // Make the API request
      const response = await fetch(url, requestOptions);
      
      if (!response.ok) {{
        throw new Error(`API request failed: ${{response.status}} ${{response.statusText}}`);
      }}
      
      const data = await response.json();
      
      return {{
        content: [
          {{
            type: "text",
            text: JSON.stringify(data, null, 2)
          }}
        ]
      }};
    }} catch (error) {{
      return {{
        content: [
          {{
            type: "text",
            text: `Error calling {tool_name}: ${{error instanceof Error ? error.message : String(error)}}`
          }}
        ]
      }};
    }}
  }}
);'''
        
        logger.debug(f"🛠️ Generated {len(code)} characters of TypeScript code")
        return code
    
    def _generate_resource_typescript_code(self, resource_name: str, endpoint_data: Dict[str, Any]) -> str:
        """Generate TypeScript code for an MCP resource."""
        logger.debug(f"🔧 _generate_resource_typescript_code called with resource_name={resource_name}")
        logger.debug(f"🔧 Endpoint data: {endpoint_data}")
        
        path = endpoint_data.get('path', '')
        description = endpoint_data.get('description', f'Access to {resource_name}')
        
        logger.debug(f"🔧 Extracted: path={path}, description={description}")
        logger.debug(f"🔧 Generating TypeScript resource code...")
        
        code = f'''server.registerResource(
  {{
    uri: "api://{resource_name}",
    name: "{resource_name}",
    description: "{description}",
    mimeType: "application/json"
  }},
  async () => {{
    try {{
      // Build URL
      const url = `${{BASE_URL}}{path}`;
      
      // Make the API request
      const response = await fetch(url, {{
        method: "GET",
        headers: {{
          "Content-Type": "application/json",
          ...getAuthHeaders()
        }}
      }});
      
      if (!response.ok) {{
        throw new Error(`API request failed: ${{response.status}} ${{response.statusText}}`);
      }}
      
      const data = await response.json();
      
      return {{
        contents: [
          {{
            uri: "api://{resource_name}",
            mimeType: "application/json",
            text: JSON.stringify(data, null, 2)
          }}
        ]
      }};
    }} catch (error) {{
      return {{
        contents: [
          {{
            uri: "api://{resource_name}",
            mimeType: "text/plain",
            text: `Error accessing {resource_name}: ${{error instanceof Error ? error.message : String(error)}}`
          }}
        ]
      }};
    }}
  }}
);'''
        
        logger.debug(f"🔧 Generated {len(code)} characters of TypeScript resource code")
        return code
