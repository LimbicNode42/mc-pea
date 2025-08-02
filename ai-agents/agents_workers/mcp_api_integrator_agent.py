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
from typing import Dict, Any, List, Optional
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
    server_name: str = Field(description="The MCP server name")
    mcp_server_path: str = Field(description="Path to the generated MCP server")
    
    def __init__(self, website_url: str, server_name: str, mcp_server_path: str, **kwargs):
        load_dotenv()
        
        # Load agent configuration
        config = get_agent_config('mcp_api_integrator_agent')

        if "claude" in config.get("llm"):
            llm = ChatAnthropic(
                model=config.get("llm"),
                max_output_tokens=config.get("max_output_tokens"),
                temperature=config.get("temperature"),
                max_retries=config.get("max_retry_limit"),
            )
            print("Using Claude LLM for MCP API integration")
        elif "gemini" in config.get("llm"):
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
            raise ValueError("Unsupported LLM type in configuration")
        
        super().__init__(
            role=config.get('role', 'MCP API Integrator'),
            goal=config.get('goal', f'Integrate extracted API usage details into MCP server {server_name} for {website_url}'),
            backstory=config.get('backstory', f"""You are an expert TypeScript developer specializing in Model Context Protocol (MCP) server development.
            Your job is to take extracted API usage details and seamlessly integrate them into an existing MCP server structure.
            You understand how to create MCP tools for API endpoints and resources for API data, following MC-PEA project standards.
            You work with both the server structure and the extracted API data to create a fully functional MCP server."""),
            llm=llm,
            tools=[self.analyze_extraction_results, self.update_mcp_server_structure, self.generate_api_tools, self.generate_api_resources, self.validate_integration],
            respect_context_window=config.get('respect_context_window', True),
            cache=config.get('cache', False),
            verbose=config.get('verbose', True),
            website_url=website_url,
            server_name=server_name,
            mcp_server_path=mcp_server_path
        )
    
    @tool
    def analyze_extraction_results(self, extraction_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the API extraction results to understand what tools and resources to create.
        
        Args:
            extraction_results: List of extraction results from API content extractor
            
        Returns:
            Dict containing analysis of endpoints, categorization, and integration plan
        """
        try:
            print(f"🔍 Analyzing {len(extraction_results)} extraction result chunks...")
            
            # Aggregate all endpoints from successful extractions
            all_endpoints = []
            successful_chunks = 0
            failed_chunks = 0
            
            for result in extraction_results:
                if 'error' not in result and 'data' in result:
                    successful_chunks += 1
                    chunk_data = result['data']
                    
                    # Extract endpoints from the chunk data
                    if isinstance(chunk_data, dict) and 'ocs' in chunk_data:
                        for category in chunk_data['ocs']:
                            category_name = category.get('cn', 'Unknown')
                            category_endpoints = category.get('ces', [])
                            
                            for endpoint in category_endpoints:
                                endpoint_info = {
                                    'category': category_name,
                                    'name': endpoint.get('en', ''),
                                    'description': endpoint.get('ed', ''),
                                    'method': endpoint.get('em', 'GET'),
                                    'path': endpoint.get('ep', ''),
                                    'headers': endpoint.get('eh', []),
                                    'path_params': endpoint.get('epp', []),
                                    'query_params': endpoint.get('eqp', []),
                                    'body_params': endpoint.get('ebp', []),
                                    'response_codes': endpoint.get('erc', {}),
                                    'examples': endpoint.get('ere', {})
                                }
                                all_endpoints.append(endpoint_info)
                else:
                    failed_chunks += 1
            
            # Categorize endpoints for MCP tools and resources
            tool_candidates = []
            resource_candidates = []
            
            for endpoint in all_endpoints:
                if endpoint['method'] in ['GET']:
                    # GET endpoints can be both tools (for actions) and resources (for data)
                    tool_candidates.append(endpoint)
                    resource_candidates.append(endpoint)
                elif endpoint['method'] in ['POST', 'PUT', 'PATCH', 'DELETE']:
                    # Write operations are primarily tools
                    tool_candidates.append(endpoint)
            
            analysis = {
                'total_endpoints': len(all_endpoints),
                'successful_chunks': successful_chunks,
                'failed_chunks': failed_chunks,
                'categories': list(set(ep['category'] for ep in all_endpoints)),
                'methods_distribution': {},
                'tool_candidates': len(tool_candidates),
                'resource_candidates': len(resource_candidates),
                'endpoints_by_category': {},
                'integration_plan': {
                    'tools_to_create': min(len(tool_candidates), 20),  # Limit for initial implementation
                    'resources_to_create': min(len(resource_candidates), 10),  # Limit for initial implementation
                    'priority_categories': []
                }
            }
            
            # Calculate method distribution
            for endpoint in all_endpoints:
                method = endpoint['method']
                if method in analysis['methods_distribution']:
                    analysis['methods_distribution'][method] += 1
                else:
                    analysis['methods_distribution'][method] = 1
            
            # Group endpoints by category
            for endpoint in all_endpoints:
                category = endpoint['category']
                if category not in analysis['endpoints_by_category']:
                    analysis['endpoints_by_category'][category] = []
                analysis['endpoints_by_category'][category].append(endpoint)
            
            # Determine priority categories (those with most endpoints)
            category_sizes = [(cat, len(eps)) for cat, eps in analysis['endpoints_by_category'].items()]
            category_sizes.sort(key=lambda x: x[1], reverse=True)
            analysis['integration_plan']['priority_categories'] = [cat for cat, _ in category_sizes[:5]]
            
            print(f"✅ Analysis complete: {analysis['total_endpoints']} endpoints across {len(analysis['categories'])} categories")
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing extraction results: {e}")
            return {
                'error': str(e),
                'total_endpoints': 0,
                'analysis_failed': True
            }
    
    @tool
    def update_mcp_server_structure(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the MCP server structure to accommodate the API tools and resources.
        
        Args:
            analysis_result: Result from analyze_extraction_results
            
        Returns:
            Dict containing the updated server structure information
        """
        try:
            print(f"🔧 Updating MCP server structure at {self.mcp_server_path}...")
            
            if not os.path.exists(self.mcp_server_path):
                return {
                    'error': f'MCP server path does not exist: {self.mcp_server_path}',
                    'success': False
                }
            
            # Read the current server structure
            server_files = []
            for root, dirs, files in os.walk(self.mcp_server_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.mcp_server_path)
                    server_files.append(relative_path)
            
            # Plan the structure updates
            updates_needed = {
                'new_directories': [],
                'new_files': [],
                'files_to_modify': [],
                'structure_valid': True
            }
            
            # Check if we need API-specific directories
            api_dir = os.path.join(self.mcp_server_path, 'src', 'api')
            tools_dir = os.path.join(self.mcp_server_path, 'src', 'tools')
            resources_dir = os.path.join(self.mcp_server_path, 'src', 'resources')
            
            if not os.path.exists(api_dir):
                updates_needed['new_directories'].append('src/api')
            if not os.path.exists(tools_dir):
                updates_needed['new_directories'].append('src/tools')
            if not os.path.exists(resources_dir):
                updates_needed['new_directories'].append('src/resources')
            
            # Identify files that need modification
            main_file = os.path.join(self.mcp_server_path, 'src', 'index.ts')
            if os.path.exists(main_file):
                updates_needed['files_to_modify'].append('src/index.ts')
            
            package_json = os.path.join(self.mcp_server_path, 'package.json')
            if os.path.exists(package_json):
                updates_needed['files_to_modify'].append('package.json')
            
            # Create the new directories
            for new_dir in updates_needed['new_directories']:
                full_path = os.path.join(self.mcp_server_path, new_dir)
                os.makedirs(full_path, exist_ok=True)
                print(f"📁 Created directory: {new_dir}")
            
            result = {
                'success': True,
                'server_path': self.mcp_server_path,
                'updates_applied': updates_needed,
                'files_structure': server_files,
                'ready_for_integration': True
            }
            
            print(f"✅ Server structure updated successfully")
            return result
            
        except Exception as e:
            print(f"❌ Error updating server structure: {e}")
            return {
                'error': str(e),
                'success': False,
                'ready_for_integration': False
            }
    
    @tool
    def generate_api_tools(self, analysis_result: Dict[str, Any], endpoints_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate MCP tools based on the extracted API endpoints.
        
        Args:
            analysis_result: Analysis of the API endpoints
            endpoints_data: Detailed endpoint information
            
        Returns:
            Dict containing generated tools information
        """
        try:
            print(f"🛠️ Generating MCP tools for API endpoints...")
            
            tools_generated = []
            priority_categories = analysis_result.get('integration_plan', {}).get('priority_categories', [])
            max_tools = analysis_result.get('integration_plan', {}).get('tools_to_create', 20)
            
            tools_created = 0
            
            # Generate tools for priority categories first
            for category in priority_categories:
                if tools_created >= max_tools:
                    break
                    
                category_endpoints = analysis_result.get('endpoints_by_category', {}).get(category, [])
                
                for endpoint in category_endpoints[:5]:  # Limit per category
                    if tools_created >= max_tools:
                        break
                    
                    tool_info = {
                        'name': self._generate_tool_name(endpoint['name'], endpoint['method']),
                        'description': endpoint['description'] or f"{endpoint['method']} request to {endpoint['path']}",
                        'category': category,
                        'method': endpoint['method'],
                        'path': endpoint['path'],
                        'parameters': {
                            'path': endpoint.get('path_params', []),
                            'query': endpoint.get('query_params', []),
                            'body': endpoint.get('body_params', []),
                            'headers': endpoint.get('headers', [])
                        },
                        'response_codes': endpoint.get('response_codes', {}),
                        'examples': endpoint.get('examples', {})
                    }
                    
                    tools_generated.append(tool_info)
                    tools_created += 1
            
            # Generate TypeScript tool files
            tools_files_created = []
            
            for tool in tools_generated:
                tool_file_content = self._generate_tool_typescript(tool)
                tool_filename = f"{tool['name'].lower().replace(' ', '_')}.ts"
                tool_filepath = os.path.join(self.mcp_server_path, 'src', 'tools', tool_filename)
                
                with open(tool_filepath, 'w', encoding='utf-8') as f:
                    f.write(tool_file_content)
                
                tools_files_created.append(tool_filename)
                print(f"🔧 Created tool file: {tool_filename}")
            
            result = {
                'success': True,
                'tools_generated': len(tools_generated),
                'tools_details': tools_generated,
                'files_created': tools_files_created,
                'categories_covered': list(set(tool['category'] for tool in tools_generated))
            }
            
            print(f"✅ Generated {len(tools_generated)} MCP tools")
            return result
            
        except Exception as e:
            print(f"❌ Error generating API tools: {e}")
            return {
                'error': str(e),
                'success': False,
                'tools_generated': 0
            }
    
    @tool
    def generate_api_resources(self, analysis_result: Dict[str, Any], endpoints_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate MCP resources based on the extracted API endpoints.
        
        Args:
            analysis_result: Analysis of the API endpoints
            endpoints_data: Detailed endpoint information
            
        Returns:
            Dict containing generated resources information
        """
        try:
            print(f"📚 Generating MCP resources for API data...")
            
            resources_generated = []
            priority_categories = analysis_result.get('integration_plan', {}).get('priority_categories', [])
            max_resources = analysis_result.get('integration_plan', {}).get('resources_to_create', 10)
            
            resources_created = 0
            
            # Generate resources primarily for GET endpoints that return data
            for category in priority_categories:
                if resources_created >= max_resources:
                    break
                    
                category_endpoints = analysis_result.get('endpoints_by_category', {}).get(category, [])
                
                for endpoint in category_endpoints:
                    if resources_created >= max_resources:
                        break
                    
                    # Focus on GET endpoints for resources
                    if endpoint['method'] == 'GET':
                        resource_info = {
                            'name': self._generate_resource_name(endpoint['name']),
                            'description': f"Data resource for {endpoint['description'] or endpoint['path']}",
                            'category': category,
                            'uri_template': f"api://{self.website_url.replace('https://', '').replace('http://', '')}{endpoint['path']}",
                            'path': endpoint['path'],
                            'parameters': endpoint.get('query_params', []),
                            'mime_type': 'application/json',
                            'examples': endpoint.get('examples', {})
                        }
                        
                        resources_generated.append(resource_info)
                        resources_created += 1
            
            # Generate TypeScript resource files
            resources_files_created = []
            
            for resource in resources_generated:
                resource_file_content = self._generate_resource_typescript(resource)
                resource_filename = f"{resource['name'].lower().replace(' ', '_')}.ts"
                resource_filepath = os.path.join(self.mcp_server_path, 'src', 'resources', resource_filename)
                
                with open(resource_filepath, 'w', encoding='utf-8') as f:
                    f.write(resource_file_content)
                
                resources_files_created.append(resource_filename)
                print(f"📄 Created resource file: {resource_filename}")
            
            result = {
                'success': True,
                'resources_generated': len(resources_generated),
                'resources_details': resources_generated,
                'files_created': resources_files_created,
                'categories_covered': list(set(resource['category'] for resource in resources_generated))
            }
            
            print(f"✅ Generated {len(resources_generated)} MCP resources")
            return result
            
        except Exception as e:
            print(f"❌ Error generating API resources: {e}")
            return {
                'error': str(e),
                'success': False,
                'resources_generated': 0
            }
    
    @tool
    def validate_integration(self, tools_result: Dict[str, Any], resources_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the complete API integration into the MCP server.
        
        Args:
            tools_result: Result from generate_api_tools
            resources_result: Result from generate_api_resources
            
        Returns:
            Dict containing validation results and final integration status
        """
        try:
            print(f"✅ Validating complete API integration...")
            
            validation_result = {
                'integration_successful': True,
                'tools_integration': tools_result.get('success', False),
                'resources_integration': resources_result.get('success', False),
                'total_tools_created': tools_result.get('tools_generated', 0),
                'total_resources_created': resources_result.get('resources_generated', 0),
                'files_created': [],
                'validation_errors': [],
                'next_steps': []
            }
            
            # Combine created files
            validation_result['files_created'].extend(tools_result.get('files_created', []))
            validation_result['files_created'].extend(resources_result.get('files_created', []))
            
            # Check if main index.ts needs updating
            index_file = os.path.join(self.mcp_server_path, 'src', 'index.ts')
            if os.path.exists(index_file):
                validation_result['next_steps'].append('Update src/index.ts to register new tools and resources')
            else:
                validation_result['validation_errors'].append('Main index.ts file not found')
                validation_result['integration_successful'] = False
            
            # Check if package.json needs updating
            package_file = os.path.join(self.mcp_server_path, 'package.json')
            if os.path.exists(package_file):
                validation_result['next_steps'].append('Update package.json with API-specific dependencies if needed')
            
            # Validate directory structure
            required_dirs = ['src/tools', 'src/resources', 'src/api']
            for req_dir in required_dirs:
                full_path = os.path.join(self.mcp_server_path, req_dir)
                if not os.path.exists(full_path):
                    validation_result['validation_errors'].append(f'Required directory missing: {req_dir}')
                    validation_result['integration_successful'] = False
            
            # Add final next steps
            if validation_result['integration_successful']:
                validation_result['next_steps'].extend([
                    'Build the TypeScript project: npm run build',
                    'Test the MCP server: npm test',
                    'Validate MCP protocol compliance'
                ])
            
            # Generate integration summary
            validation_result['integration_summary'] = {
                'server_path': self.mcp_server_path,
                'api_source': self.website_url,
                'tools_created': validation_result['total_tools_created'],
                'resources_created': validation_result['total_resources_created'],
                'files_modified': len(validation_result['files_created']),
                'ready_for_use': validation_result['integration_successful'] and len(validation_result['validation_errors']) == 0
            }
            
            if validation_result['integration_successful']:
                print(f"🎉 API integration completed successfully!")
                print(f"   - Tools created: {validation_result['total_tools_created']}")
                print(f"   - Resources created: {validation_result['total_resources_created']}")
                print(f"   - Files created: {len(validation_result['files_created'])}")
            else:
                print(f"⚠️ Integration completed with {len(validation_result['validation_errors'])} errors")
            
            return validation_result
            
        except Exception as e:
            print(f"❌ Error validating integration: {e}")
            return {
                'error': str(e),
                'integration_successful': False,
                'validation_failed': True
            }
    
    def _generate_tool_name(self, endpoint_name: str, method: str) -> str:
        """Generate a clean tool name from endpoint information."""
        if endpoint_name:
            # Clean and format the endpoint name
            clean_name = endpoint_name.lower().replace(' ', '_').replace('-', '_')
            return f"{method.lower()}_{clean_name}"
        else:
            return f"{method.lower()}_endpoint"
    
    def _generate_resource_name(self, endpoint_name: str) -> str:
        """Generate a clean resource name from endpoint information."""
        if endpoint_name:
            clean_name = endpoint_name.lower().replace(' ', '_').replace('-', '_')
            return f"{clean_name}_data"
        else:
            return "api_data"
    
    def _generate_tool_typescript(self, tool_info: Dict[str, Any]) -> str:
        """Generate TypeScript code for an MCP tool."""
        tool_name = tool_info['name']
        description = tool_info['description']
        method = tool_info['method']
        path = tool_info['path']
        
        # Build parameter schema
        params_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Add parameters from different sources
        for param_type in ['path', 'query', 'body']:
            params = tool_info['parameters'].get(param_type, [])
            for param in params:
                if isinstance(param, dict) and 'name' in param:
                    param_name = param['name']
                    params_schema['properties'][param_name] = {
                        "type": param.get('type', 'string'),
                        "description": param.get('description', f"{param_type} parameter")
                    }
                    if param.get('required', False):
                        params_schema['required'].append(param_name)
        
        typescript_content = f'''/**
 * MCP Tool: {tool_name}
 * {description}
 * Generated from API endpoint: {method} {path}
 */

import {{ tool }} from '@modelcontextprotocol/sdk';
import {{ z }} from 'zod';

const {tool_name}Schema = z.object({json.dumps(params_schema, indent=2).replace('"', "'")});

export const {tool_name} = tool(
  {{
    name: '{tool_name}',
    description: '{description}',
    inputSchema: {{
      type: 'object',
      properties: {json.dumps(params_schema['properties'], indent=6)},
      required: {json.dumps(params_schema['required'])}
    }}
  }},
  async (params) => {{
    try {{
      // TODO: Implement {method} request to {path}
      // Use the provided parameters to make the API call
      
      const result = {{
        method: '{method}',
        path: '{path}',
        parameters: params,
        // Add actual API call implementation here
      }};

      return {{
        content: [
          {{
            type: 'text',
            text: JSON.stringify(result, null, 2)
          }}
        ]
      }};
    }} catch (error) {{
      return {{
        content: [
          {{
            type: 'text',
            text: `Error executing {tool_name}: ${{error.message}}`
          }}
        ],
        isError: true
      }};
    }}
  }}
);
'''
        return typescript_content
    
    def _generate_resource_typescript(self, resource_info: Dict[str, Any]) -> str:
        """Generate TypeScript code for an MCP resource."""
        resource_name = resource_info['name']
        description = resource_info['description']
        uri_template = resource_info['uri_template']
        path = resource_info['path']
        
        typescript_content = f'''/**
 * MCP Resource: {resource_name}
 * {description}
 * Generated from API endpoint: {path}
 */

import {{ resource }} from '@modelcontextprotocol/sdk';

export const {resource_name} = resource(
  {{
    uri: '{uri_template}',
    name: '{resource_name}',
    description: '{description}',
    mimeType: 'application/json'
  }},
  async (uri) => {{
    try {{
      // TODO: Implement data fetching for {path}
      // Parse URI parameters and make appropriate API call
      
      const data = {{
        uri: uri,
        path: '{path}',
        description: '{description}',
        // Add actual data fetching implementation here
      }};

      return {{
        contents: [
          {{
            uri: uri,
            mimeType: 'application/json',
            text: JSON.stringify(data, null, 2)
          }}
        ]
      }};
    }} catch (error) {{
      throw new Error(`Error fetching {resource_name}: ${{error.message}}`);
    }}
  }}
);
'''
        return typescript_content
    
    def get_integration_info(self) -> Dict[str, str]:
        """Get basic information about this integration agent."""
        return {
            'agent_type': 'MCP API Integrator',
            'website_url': self.website_url,
            'server_name': self.server_name,
            'mcp_server_path': self.mcp_server_path,
            'capabilities': 'API tools and resources generation, MCP server integration'
        }
