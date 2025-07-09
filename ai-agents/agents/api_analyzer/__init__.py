"""
API Analyzer Agent - Analyzes external APIs to generate MCP server specifications.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import requests
from core.base_agent import BaseAgent, AgentConfig
from core.config import get_config, MCPEAConfig


class APIAnalyzerAgent(BaseAgent):
    """Agent that analyzes external APIs and generates MCP server specifications."""
    
    def __init__(self, anthropic_client=None):
        # Create agent config
        agent_config = AgentConfig(
            name="api_analyzer",
            role="API Analysis Specialist",
            goal="Analyze external APIs and generate comprehensive MCP server specifications",
            backstory="""
            You are an expert API analyst with deep knowledge of RESTful services, authentication methods,
            and data structures. You excel at understanding API documentation and translating complex
            API capabilities into clear MCP server specifications.
            """
        )
        
        super().__init__(agent_config, anthropic_client)
        self.analysis_cache = {}
        
        # Register for configuration updates
        self.register_config_callback(self._on_analyzer_config_update)
    
    def _on_analyzer_config_update(self, new_config: MCPEAConfig) -> None:
        """Handle analyzer-specific configuration updates.
        
        Args:
            new_config: Updated configuration
        """
        # Update Anthropic client settings for API analysis
        if hasattr(new_config, 'anthropic'):
            self.anthropic_config = new_config.anthropic
        
        self.logger.info("API Analyzer configuration updated")
    
    def get_tools(self) -> List[Any]:
        """Get tools available to this agent.
        
        Returns:
            List of tools for API analysis
        """
        return []  # API analyzer uses external tools and HTTP requests
    
    async def analyze_api(self, api_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an API specification and generate MCP server recommendations.
        
        Args:
            api_spec: API specification containing URL, documentation, etc.
            
        Returns:
            Analysis results with MCP server specifications
        """
        try:
            api_url = api_spec.get('url', '')
            cache_key = f"api_{hash(api_url)}"
            
            if cache_key in self.analysis_cache:
                return self.analysis_cache[cache_key]
            
            # Gather API information
            api_info = await self._gather_api_info(api_spec)
            
            # Generate MCP server specification using AI
            mcp_spec = await self._generate_mcp_spec(api_info)
            
            # Cache results
            result = {
                'api_info': api_info,
                'mcp_specification': mcp_spec,
                'analysis_timestamp': self._get_timestamp(),
                'confidence_score': self._calculate_confidence(api_info, mcp_spec)
            }
            
            self.analysis_cache[cache_key] = result
            
            await self._emit_message('api_analyzed', {
                'api_url': api_url,
                'mcp_spec': mcp_spec,
                'confidence': result['confidence_score']
            })
            
            return result
            
        except Exception as e:
            await self._emit_message('api_analysis_error', {
                'error': str(e),
                'api_spec': api_spec
            })
            raise
    
    async def _gather_api_info(self, api_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Gather comprehensive information about the API."""
        info = {
            'url': api_spec.get('url', ''),
            'name': api_spec.get('name', ''),
            'description': api_spec.get('description', ''),
            'documentation_url': api_spec.get('docs_url', ''),
            'endpoints': [],
            'authentication': {},
            'rate_limits': {},
            'data_formats': [],
            'complexity_score': 0
        }
        
        # Try to fetch OpenAPI/Swagger spec if available
        openapi_url = api_spec.get('openapi_url')
        if openapi_url:
            try:
                response = requests.get(openapi_url, timeout=10)
                if response.status_code == 200:
                    openapi_spec = response.json()
                    info.update(self._parse_openapi_spec(openapi_spec))
            except Exception as e:
                self.logger.warning(f"Failed to fetch OpenAPI spec: {e}")
        
        # Analyze URL structure
        parsed_url = urlparse(info['url'])
        info['base_domain'] = parsed_url.netloc
        info['protocol'] = parsed_url.scheme
        
        # Calculate complexity score
        info['complexity_score'] = self._calculate_api_complexity(info)
        
        return info
    
    def _parse_openapi_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Parse OpenAPI specification to extract relevant information."""
        parsed = {
            'endpoints': [],
            'authentication': {},
            'data_formats': []
        }
        
        # Extract paths and operations
        paths = spec.get('paths', {})
        for path, methods in paths.items():
            for method, operation in methods.items():
                if isinstance(operation, dict):
                    endpoint = {
                        'path': path,
                        'method': method.upper(),
                        'summary': operation.get('summary', ''),
                        'description': operation.get('description', ''),
                        'parameters': operation.get('parameters', []),
                        'responses': operation.get('responses', {}),
                        'tags': operation.get('tags', [])
                    }
                    parsed['endpoints'].append(endpoint)
        
        # Extract security schemes
        security_schemes = spec.get('components', {}).get('securitySchemes', {})
        for name, scheme in security_schemes.items():
            parsed['authentication'][name] = {
                'type': scheme.get('type', ''),
                'scheme': scheme.get('scheme', ''),
                'in': scheme.get('in', ''),
                'name': scheme.get('name', '')
            }
        
        return parsed
    
    def _calculate_api_complexity(self, api_info: Dict[str, Any]) -> int:
        """Calculate a complexity score for the API (0-100)."""
        score = 0
        
        # Base score for having endpoints
        endpoint_count = len(api_info.get('endpoints', []))
        score += min(endpoint_count * 2, 40)  # Max 40 points for endpoints
        
        # Authentication complexity
        auth_methods = len(api_info.get('authentication', {}))
        score += min(auth_methods * 10, 20)  # Max 20 points for auth
        
        # Data format variety
        format_count = len(api_info.get('data_formats', []))
        score += min(format_count * 5, 15)  # Max 15 points for formats
        
        # Documentation quality
        if api_info.get('documentation_url'):
            score += 10
        if api_info.get('description'):
            score += 5
        
        # Rate limiting presence
        if api_info.get('rate_limits'):
            score += 10
        
        return min(score, 100)
    
    async def _generate_mcp_spec(self, api_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate MCP server specification using AI analysis."""
        prompt = f"""
        Analyze this API and generate a comprehensive MCP server specification:
        
        API Information:
        - Name: {api_info.get('name', 'Unknown')}
        - URL: {api_info.get('url', '')}
        - Description: {api_info.get('description', '')}
        - Endpoints: {len(api_info.get('endpoints', []))} endpoints
        - Authentication: {list(api_info.get('authentication', {}).keys())}
        - Complexity Score: {api_info.get('complexity_score', 0)}/100
        
        Endpoints Sample:
        {json.dumps(api_info.get('endpoints', [])[:5], indent=2)}
        
        Generate a detailed MCP server specification including:
        1. Server metadata (name, description, version)
        2. Required tools and their configurations
        3. Resource endpoints and data structures
        4. Authentication integration requirements
        5. Error handling strategies
        6. Rate limiting considerations
        7. Testing recommendations
        8. Security considerations
        
        Format as a structured JSON specification that can be used to generate a TypeScript MCP server.
        """
        
        try:
            response = await self.anthropic_client.generate_completion(prompt, max_tokens=2000)
            
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                mcp_spec = json.loads(json_str)
                
                # Add metadata
                mcp_spec['generated_by'] = 'APIAnalyzerAgent'
                mcp_spec['source_api'] = api_info.get('url', '')
                mcp_spec['analysis_timestamp'] = self._get_timestamp()
                
                return mcp_spec
            else:
                raise ValueError("Failed to extract valid JSON from AI response")
                
        except Exception as e:
            self.logger.error(f"Failed to generate MCP spec: {e}")
            # Return a basic fallback specification
            return self._generate_fallback_spec(api_info)
    
    def _generate_fallback_spec(self, api_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a basic fallback MCP specification."""
        return {
            'name': f"{api_info.get('name', 'api')}-mcp-server",
            'description': f"MCP server for {api_info.get('name', 'API')}",
            'version': '1.0.0',
            'tools': [
                {
                    'name': 'api_request',
                    'description': 'Make requests to the API',
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'endpoint': {'type': 'string'},
                            'method': {'type': 'string'},
                            'parameters': {'type': 'object'}
                        }
                    }
                }
            ],
            'resources': [
                {
                    'uri': 'api://data',
                    'name': 'API Data',
                    'description': 'Access to API data'
                }
            ],
            'generated_by': 'APIAnalyzerAgent_Fallback',
            'source_api': api_info.get('url', ''),
            'analysis_timestamp': self._get_timestamp()
        }
    
    def _calculate_confidence(self, api_info: Dict[str, Any], mcp_spec: Dict[str, Any]) -> float:
        """Calculate confidence score for the analysis (0.0-1.0)."""
        score = 0.0
        
        # API information completeness
        if api_info.get('name'): score += 0.1
        if api_info.get('description'): score += 0.1
        if api_info.get('endpoints'): score += 0.2
        if api_info.get('authentication'): score += 0.1
        if api_info.get('documentation_url'): score += 0.1
        
        # MCP specification completeness
        if mcp_spec.get('tools'): score += 0.2
        if mcp_spec.get('resources'): score += 0.1
        if mcp_spec.get('description'): score += 0.1
        
        return min(score, 1.0)
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute API analysis task."""
        task_type = task.get('type', 'analyze_api')
        
        if task_type == 'analyze_api':
            api_spec = task.get('api_spec', {})
            return await self.analyze_api(api_spec)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
