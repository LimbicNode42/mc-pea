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
                max_output_tokens=config.get("max_output_tokens"),
                temperature=config.get("temperature"),
                max_retries=config.get("max_retry_limit"),
            )
            print("Using Claude LLM for MCP API integration")
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
        
        # Initialize parent class with proper agent configuration
        super().__init__(
            role=config.get("role"),
            goal=config.get("goal"),
            backstory=config.get("backstory"),
            llm=llm,
            tools=[],
            respect_context_window=config.get('respect_context_window', True),
            cache=config.get('cache', False),
            reasoning=config.get('reasoning', True),
            max_iter=config.get('max_iterations', 20),
            max_retry_limit=config.get('max_retry_limit', 2),
            verbose=config.get('verbose', True),
            allow_delegation=config.get('allow_delegation', False),
            # Pass our custom fields to the parent constructor
            website_url=website_url,
            server_name=server_name,
            mcp_server_path=server_path,
            **kwargs
        )
        
        # Store workflow state - these will be populated during execution
        self._extraction_results = None
        self._analysis_result = None
        self._tools_result = None
        self._resources_result = None
        
        # Create tools that have access to instance variables
        @tool("analyze_extraction_results")
        def analyze_extraction_results_tool(context: str = "{}") -> str:
            """Analyze the API extraction results to understand what tools and resources to create."""
            return str(self.analyze_extraction_results_wrapper(context))
        
        @tool("update_mcp_server_structure")
        def update_mcp_server_structure_tool(context: str = "{}") -> str:
            """Update the MCP server structure to accommodate the API tools and resources."""
            return str(self.update_mcp_server_structure_wrapper(context))
        
        @tool("generate_api_tools")
        def generate_api_tools_tool(context: str = "{}") -> str:
            """Generate MCP tools from API endpoints."""
            return str(self.generate_api_tools_wrapper(context))
        
        @tool("generate_api_resources")
        def generate_api_resources_tool(context: str = "{}") -> str:
            """Generate MCP resources from API endpoints."""
            return str(self.generate_api_resources_wrapper(context))
        
        @tool("validate_integration")
        def validate_integration_tool(context: str = "{}") -> str:
            """Validate the integration of tools and resources."""
            return str(self.validate_integration_wrapper(context))
        
        # Add tools to the agent
        self.tools.extend([
            analyze_extraction_results_tool,
            update_mcp_server_structure_tool,
            generate_api_tools_tool,
            generate_api_resources_tool,
            validate_integration_tool
        ])
    
    def analyze_extraction_results_wrapper(self, context: str) -> Dict[str, Any]:
        """Wrapper method for analyze_extraction_results tool."""
        try:
            # If no extraction results stored yet, try to get from context
            if self._extraction_results is None:
                try:
                    context_data = json.loads(context) if context != "{}" else {}
                    extraction_results = context_data.get('extraction_results', [])
                except:
                    extraction_results = []
            else:
                extraction_results = self._extraction_results
            
            result = self.analyze_extraction_results(extraction_results)
            # Store result for next steps
            self._analysis_result = result
            return result
        except Exception as e:
            return {'error': str(e)}
    
    def update_mcp_server_structure_wrapper(self, context: str) -> Dict[str, Any]:
        """Wrapper method for update_mcp_server_structure tool."""
        try:
            # Use stored analysis result if available, otherwise try context
            if self._analysis_result is not None:
                analysis_dict = self._analysis_result
            else:
                try:
                    context_data = json.loads(context) if context != "{}" else {}
                    analysis_dict = context_data.get('analysis_result', {})
                except:
                    analysis_dict = {}
            
            return self.update_mcp_server_structure(analysis_dict)
        except Exception as e:
            return {'error': str(e)}
    
    def generate_api_tools_wrapper(self, context: str) -> Dict[str, Any]:
        """Wrapper method for generate_api_tools tool."""
        try:
            # Use stored analysis result if available, otherwise try context
            if self._analysis_result is not None:
                analysis_dict = self._analysis_result
            else:
                try:
                    context_data = json.loads(context) if context != "{}" else {}
                    analysis_dict = context_data.get('analysis_result', {})
                except:
                    analysis_dict = {}
            
            result = self.generate_api_tools(analysis_dict)
            # Store result for validation step
            self._tools_result = result
            return result
        except Exception as e:
            return {'error': str(e)}
    
    def generate_api_resources_wrapper(self, context: str) -> Dict[str, Any]:
        """Wrapper method for generate_api_resources tool."""
        try:
            # Use stored analysis result if available, otherwise try context
            if self._analysis_result is not None:
                analysis_dict = self._analysis_result
            else:
                try:
                    context_data = json.loads(context) if context != "{}" else {}
                    analysis_dict = context_data.get('analysis_result', {})
                except:
                    analysis_dict = {}
            
            result = self.generate_api_resources(analysis_dict)
            # Store result for validation step
            self._resources_result = result
            return result
        except Exception as e:
            return {'error': str(e)}
    
    def validate_integration_wrapper(self, context: str) -> Dict[str, Any]:
        """Wrapper method for validate_integration tool."""
        try:
            # Use stored results if available, otherwise try context
            if self._tools_result is not None and self._resources_result is not None:
                tools_dict = self._tools_result
                resources_dict = self._resources_result
            else:
                try:
                    context_data = json.loads(context) if context != "{}" else {}
                    tools_dict = context_data.get('tools_result', {})
                    resources_dict = context_data.get('resources_result', {})
                except:
                    tools_dict = {}
                    resources_dict = {}
            
            return self.validate_integration(tools_dict, resources_dict)
        except Exception as e:
            return {'error': str(e)}
    
    def set_extraction_results(self, extraction_results: List[Dict[str, Any]]) -> None:
        """Set the extraction results for processing."""
        self._extraction_results = extraction_results
    
    def analyze_extraction_results(self, extraction_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the API extraction results to understand what tools and resources to create.
        
        Args:
            extraction_results: List of extraction results from API content extractor
            
        Returns:
            Dict containing analysis of endpoints, categorization, and integration plan
        """
        try:
            # Defensive coding - ensure extraction_results is valid
            if not extraction_results or not isinstance(extraction_results, list):
                print("❌ Invalid or empty extraction_results provided")
                return {
                    'error': 'Invalid or empty extraction_results provided',
                    'total_endpoints': 0,
                    'analysis_failed': True
                }
            
            print(f"🔍 Analyzing {len(extraction_results)} extraction result chunks...")
            
            # Aggregate all endpoints from successful extractions
            all_endpoints = []
            successful_chunks = 0
            failed_chunks = 0
            
            for result in extraction_results:
                if not isinstance(result, dict):
                    failed_chunks += 1
                    continue
                    
                if 'error' not in result and 'data' in result:
                    successful_chunks += 1
                    chunk_data = result['data']
                    
                    # Extract endpoints from the chunk data - with defensive coding
                    if isinstance(chunk_data, dict) and chunk_data.get('ocs'):
                        ocs_data = chunk_data['ocs']
                        if isinstance(ocs_data, list):
                            for category in ocs_data:
                                if not isinstance(category, dict):
                                    continue
                                    
                                category_name = category.get('cn', 'Unknown')
                                category_endpoints = category.get('ces', [])
                                
                                if isinstance(category_endpoints, list):
                                    for endpoint in category_endpoints:
                                        if not isinstance(endpoint, dict):
                                            continue
                                            
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
                if not isinstance(endpoint, dict):
                    continue
                    
                endpoint_method = endpoint.get('method', 'GET')
                if endpoint_method in ['GET']:
                    # GET endpoints can be both tools (for actions) and resources (for data)
                    tool_candidates.append(endpoint)
                    resource_candidates.append(endpoint)
                elif endpoint_method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                    # Write operations are primarily tools
                    tool_candidates.append(endpoint)
            
            # Build analysis with safe category extraction
            categories = []
            for ep in all_endpoints:
                if isinstance(ep, dict) and ep.get('category'):
                    categories.append(ep['category'])
            
            analysis = {
                'total_endpoints': len(all_endpoints),
                'successful_chunks': successful_chunks,
                'failed_chunks': failed_chunks,
                'categories': list(set(categories)),
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
                if not isinstance(endpoint, dict):
                    continue
                method = endpoint.get('method', 'UNKNOWN')
                if method in analysis['methods_distribution']:
                    analysis['methods_distribution'][method] += 1
                else:
                    analysis['methods_distribution'][method] = 1
            
            # Group endpoints by category
            for endpoint in all_endpoints:
                if not isinstance(endpoint, dict):
                    continue
                category = endpoint.get('category', 'Unknown')
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
    
    def generate_api_tools(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate MCP tools based on the extracted API endpoints.
        
        Args:
            analysis_result: Analysis of the API endpoints
            
        Returns:
            Dict containing generated tools information
        """
        try:
            print(f"🛠️ Generating MCP tools for API endpoints...")
            
            # Defensive coding - ensure analysis_result is valid
            if not analysis_result or not isinstance(analysis_result, dict):
                return {
                    'error': 'Invalid analysis_result provided',
                    'success': False,
                    'tools_generated': 0
                }
            
            tools_generated = []
            integration_plan = analysis_result.get('integration_plan') or {}
            priority_categories = integration_plan.get('priority_categories') or []
            max_tools = integration_plan.get('tools_to_create') or 20
            
            tools_created = 0
            
            # Generate tools for priority categories first
            for category in priority_categories:
                if tools_created >= max_tools:
                    break
                    
                endpoints_by_category = analysis_result.get('endpoints_by_category') or {}
                category_endpoints = endpoints_by_category.get(category) or []
                
                for endpoint in category_endpoints[:5]:  # Limit per category
                    if tools_created >= max_tools:
                        break
                    
                    # Ensure endpoint is valid
                    if not endpoint or not isinstance(endpoint, dict):
                        continue
                    
                    tool_info = {
                        'name': self._generate_tool_name(endpoint.get('name', ''), endpoint.get('method', 'GET')),
                        'description': endpoint.get('description', '') or f"{endpoint.get('method', 'GET')} request to {endpoint.get('path', '')}",
                        'category': category,
                        'method': endpoint.get('method', 'GET'),
                        'path': endpoint.get('path', ''),
                        'parameters': {
                            'path': endpoint.get('path_params') or [],
                            'query': endpoint.get('query_params') or [],
                            'body': endpoint.get('body_params') or [],
                            'headers': endpoint.get('headers') or []
                        },
                        'response_codes': endpoint.get('response_codes') or {},
                        'examples': endpoint.get('examples') or {}
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
    
    def generate_api_resources(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate MCP resources based on the extracted API endpoints.
        
        Args:
            analysis_result: Analysis of the API endpoints
            
        Returns:
            Dict containing generated resources information
        """
        try:
            print(f"📚 Generating MCP resources for API data...")
            
            # Defensive coding - ensure analysis_result is valid
            if not analysis_result or not isinstance(analysis_result, dict):
                return {
                    'error': 'Invalid analysis_result provided',
                    'success': False,
                    'resources_generated': 0
                }
            
            resources_generated = []
            integration_plan = analysis_result.get('integration_plan') or {}
            priority_categories = integration_plan.get('priority_categories') or []
            max_resources = integration_plan.get('resources_to_create') or 10
            
            resources_created = 0
            
            # Generate resources primarily for GET endpoints that return data
            for category in priority_categories:
                if resources_created >= max_resources:
                    break
                    
                endpoints_by_category = analysis_result.get('endpoints_by_category') or {}
                category_endpoints = endpoints_by_category.get(category) or []
                
                for endpoint in category_endpoints:
                    if resources_created >= max_resources:
                        break
                    
                    # Ensure endpoint is valid
                    if not endpoint or not isinstance(endpoint, dict):
                        continue
                    
                    # Focus on GET endpoints for resources
                    if endpoint.get('method') == 'GET':
                        resource_info = {
                            'name': self._generate_resource_name(endpoint.get('name', '')),
                            'description': f"Data resource for {endpoint.get('description', '') or endpoint.get('path', '')}",
                            'category': category,
                            'uri_template': f"api://{self.website_url.replace('https://', '').replace('http://', '')}{endpoint.get('path', '')}",
                            'path': endpoint.get('path', ''),
                            'parameters': endpoint.get('query_params') or [],
                            'mime_type': 'application/json',
                            'examples': endpoint.get('examples') or {}
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
            
            # Defensive coding - ensure inputs are valid
            if not isinstance(tools_result, dict):
                tools_result = {}
            if not isinstance(resources_result, dict):
                resources_result = {}
            
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
            
            # Combine created files - safely handle None values
            tools_files = tools_result.get('files_created')
            if tools_files and isinstance(tools_files, list):
                validation_result['files_created'].extend(tools_files)
                
            resources_files = resources_result.get('files_created')
            if resources_files and isinstance(resources_files, list):
                validation_result['files_created'].extend(resources_files)
            
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
        # Defensive coding - ensure tool_info is valid
        if not tool_info or not isinstance(tool_info, dict):
            return "// Error: Invalid tool_info provided"
            
        tool_name = tool_info.get('name', 'unknown_tool')
        description = tool_info.get('description', 'Generated MCP tool')
        method = tool_info.get('method', 'GET')
        path = tool_info.get('path', '')
        
        # Build basic parameter schema
        params_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Add parameters from different sources - with defensive coding
        parameters = tool_info.get('parameters')
        if parameters and isinstance(parameters, dict):
            for param_type in ['path', 'query', 'body']:
                params = parameters.get(param_type)
                if params and isinstance(params, list):
                    for param in params:
                        if isinstance(param, dict) and param.get('name'):
                            param_name = param['name']
                            params_schema['properties'][param_name] = {
                                "type": param.get('type', 'string'),
                                "description": param.get('description', f"{param_type} parameter")
                            }
                            if param.get('required', False):
                                params_schema['required'].append(param_name)
        
        return f'''/**
 * MCP Tool: {tool_name}
 * {description}
 * Generated from API endpoint: {method} {path}
 */

import {{ tool }} from '@modelcontextprotocol/sdk';

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
    
    def _generate_resource_typescript(self, resource_info: Dict[str, Any]) -> str:
        """Generate TypeScript code for an MCP resource."""
        resource_name = resource_info['name']
        description = resource_info['description']
        uri_template = resource_info['uri_template']
        path = resource_info['path']
        
        return f'''/**
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
