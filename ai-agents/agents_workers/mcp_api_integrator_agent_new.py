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
from typing import Dict, Any, List
from urllib.parse import urlparse
from core.agent_workers_config_loader import get_agent_config
from pydantic import Field


class MCPAPIIntegratorAgent(Agent):
    """
    Agent responsible for integrating extracted API details into the MCP server.
    Updates the generated MCP server with tools and resources based on API extraction results.
    """
    
    # Declare custom fields as Pydantic model fields
    website_url: str = Field(description="The website URL for API integration")
    server_name: str = Field(description="The generated server name")
    mcp_server_path: str = Field(description="Path to the MCP server directory")

    def __init__(self, website_url: str, server_name: str, mcp_server_path: str, **kwargs):
        load_dotenv()
        
        # Generate server name from website URL if not provided
        if not server_name:
            parsed = urlparse(website_url)
            domain = parsed.netloc.replace('www.', '').replace('.', '-')
            server_name = f"{domain}-api-mcp-server"
        
        # Use custom server path if provided, otherwise use default
        if mcp_server_path:
            if os.path.isabs(mcp_server_path):
                server_path = mcp_server_path
            else:
                # Relative to current working directory
                server_path = os.path.abspath(mcp_server_path)
        else:
            # Default server path
            server_path = os.path.join(os.getcwd(), '..', 'mcp-servers', f"{server_name}")

        # Validate server directory exists or can be created
        os.makedirs(server_path, exist_ok=True)

        # Load agent configuration
        config = get_agent_config('mcp_api_integrator_agent')
        
        # Add error handling for None config
        if config is None:
            raise ValueError("Could not load configuration for 'mcp_api_integrator_agent'. Check that the config file exists and is valid.")

        if "claude" in config.get("llm", ""):
            llm = ChatAnthropic(
                model=config.get("llm"),
                max_tokens=config.get("max_output_tokens"),
                temperature=config.get("temperature"),
                max_retries=1,  # Reduced from config to prevent rapid retries
                default_request_timeout=120,  # Increase timeout
                # Add rate limiting delay
                anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            )
            print("Using Claude LLM for MCP API integration (with rate limiting)")
        elif "gemini" in config.get("llm", ""):
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini models")
            
            # Extract just the model name (remove the provider prefix)
            model_name = config.get("llm").replace("gemini/", "")
            
            # Use CrewAI's LLM class for Gemini models
            llm = LLM(
                model=f"gemini/{model_name}",
                api_key=google_api_key,
                max_tokens=config.get("max_input_tokens"),
                max_completion_tokens=config.get("max_output_tokens"),
                temperature=config.get("temperature"),
                reasoning_effort=config.get("reasoning_effort"),
            )
            print(f"Using Gemini LLM for MCP API integration: {model_name}")
        else:
            raise ValueError(f"Unsupported LLM type in configuration: {config.get('llm', 'None')}")
        
        # Store instance variables
        self.website_url = website_url
        self.server_name = server_name
        self.mcp_server_path = server_path
        
        # Create concrete tools that provide actual functionality
        @tool("read_file")
        def read_file_tool(file_path: str) -> str:
            """Read the contents of a file."""
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file {file_path}: {str(e)}"
        
        @tool("write_file")
        def write_file_tool(file_path: str, content: str) -> str:
            """Write content to a file."""
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Successfully wrote to {file_path}"
            except Exception as e:
                return f"Error writing file {file_path}: {str(e)}"
        
        @tool("copy_template")
        def copy_template_tool(template_path: str, destination_path: str) -> str:
            """Copy template files to destination."""
            try:
                if os.path.exists(destination_path):
                    shutil.rmtree(destination_path)
                shutil.copytree(template_path, destination_path)
                return f"Successfully copied template from {template_path} to {destination_path}"
            except Exception as e:
                return f"Error copying template: {str(e)}"
        
        @tool("list_directory")
        def list_directory_tool(dir_path: str) -> str:
            """List contents of a directory."""
            try:
                if not os.path.exists(dir_path):
                    return f"Directory {dir_path} does not exist"
                items = os.listdir(dir_path)
                return json.dumps(items)
            except Exception as e:
                return f"Error listing directory {dir_path}: {str(e)}"
        
        @tool("generate_typescript_tool")
        def generate_typescript_tool_tool(tool_name: str, endpoint_data: str) -> str:
            """Generate TypeScript code for an MCP tool based on API endpoint data."""
            try:
                endpoint = json.loads(endpoint_data)
                return self._generate_tool_typescript_code(tool_name, endpoint)
            except Exception as e:
                return f"Error generating TypeScript tool: {str(e)}"
        
        @tool("generate_typescript_resource")
        def generate_typescript_resource_tool(resource_name: str, endpoint_data: str) -> str:
            """Generate TypeScript code for an MCP resource based on API endpoint data."""
            try:
                endpoint = json.loads(endpoint_data)
                return self._generate_resource_typescript_code(resource_name, endpoint)
            except Exception as e:
                return f"Error generating TypeScript resource: {str(e)}"
        
        @tool("validate_typescript")
        def validate_typescript_tool(file_path: str) -> str:
            """Validate TypeScript file syntax."""
            try:
                # Simple validation - check if file can be read and has basic TS structure
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic syntax checks
                if 'server.registerTool' in content or 'server.registerResource' in content:
                    return f"TypeScript file {file_path} appears valid"
                else:
                    return f"Warning: {file_path} may not contain proper MCP registrations"
            except Exception as e:
                return f"Error validating TypeScript file {file_path}: {str(e)}"
        
        # Initialize parent class with proper agent configuration
        super().__init__(
            role=config.get("role"),
            goal=config.get("goal"),
            backstory=config.get("backstory"),
            llm=llm,
            tools=[
                read_file_tool,
                write_file_tool,
                copy_template_tool,
                list_directory_tool,
                generate_typescript_tool_tool,
                generate_typescript_resource_tool,
                validate_typescript_tool
            ],
            respect_context_window=config.get('respect_context_window', True),
            cache=config.get('cache', False),
            reasoning=config.get('reasoning', True),
            max_iter=config.get('max_iterations', 20),
            max_retry_limit=config.get('max_retry_limit', 2),
            verbose=config.get('verbose', True),
            allow_delegation=config.get('allow_delegation', False),
            **kwargs
        )
        
        # Store workflow state
        self._extraction_results = None
        self._last_call_time = 0  # For rate limiting
        self._min_call_interval = float(os.getenv('MCP_INTEGRATOR_RATE_LIMIT', '2.0'))
    
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
        self._extraction_results = extraction_results
    
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
        method = endpoint_data.get('method', 'GET').upper()
        path = endpoint_data.get('path', '')
        description = endpoint_data.get('description', f'{method} {path}')
        parameters = endpoint_data.get('parameters', [])
        
        # Generate parameter schema
        schema_properties = {}
        required_params = []
        
        for param in parameters:
            param_name = param.get('name', 'unknown')
            param_type = param.get('type', 'string')
            param_required = param.get('required', False)
            param_description = param.get('description', '')
            
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
        
        # Generate the tool code
        properties_str = json.dumps(schema_properties, indent=6)
        required_str = json.dumps(required_params)
        
        body_code = ""
        if method in ['POST', 'PUT', 'PATCH']:
            body_code = f'''if (["{method}"].includes("{method}")) {{
        requestOptions.body = JSON.stringify(params);
      }}'''
        
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
        
        return code
    
    def _generate_resource_typescript_code(self, resource_name: str, endpoint_data: Dict[str, Any]) -> str:
        """Generate TypeScript code for an MCP resource."""
        path = endpoint_data.get('path', '')
        description = endpoint_data.get('description', f'Access to {resource_name}')
        
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
        
        return code
