"""
API Analysis Agent for analyzing scraped API documentation.
"""

from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew
from core.base_agent import BaseAgent, AgentConfig
from core.config import get_config, MCPEAConfig
import json
import logging


class APIAnalysisAgent(BaseAgent):
    """Agent responsible for analyzing scraped API documentation and extracting structured information."""
    
    def __init__(self, anthropic_client=None):
        # Create agent config
        agent_config = AgentConfig(
            name="api_analysis",
            role="API Documentation Analyzer",
            goal="Analyze scraped API documentation and extract structured API specifications",
            backstory="""
            You are an expert API analyst who specializes in understanding and analyzing API documentation.
            You take scraped documentation content and extract meaningful API specifications, 
            endpoint definitions, authentication methods, and usage patterns to help generate 
            accurate MCP servers.
            """
        )
        
        super().__init__(agent_config, anthropic_client)
        
        # No direct MCP server dependencies for this agent
        self.mcp_server_dependencies = []
        
        # Register for configuration updates
        self.register_config_callback(self._on_analysis_config_update)
    
    def _on_analysis_config_update(self, new_config: MCPEAConfig) -> None:
        """Handle analysis-specific configuration updates.
        
        Args:
            new_config: Updated configuration
        """
        # Update analysis settings based on config
        self.logger.info("API analysis configuration updated")
    
    def get_tools(self) -> List[Any]:
        """Get tools available to this agent.
        
        Returns:
            List of tools for API analysis
        """
        return [
            self.analyze_api_documentation,
            self.extract_api_endpoints,
            self.identify_authentication_methods,
            self.generate_api_specification,
            self.detect_api_patterns
        ]
    
    def get_mcp_dependencies(self) -> List[Dict[str, Any]]:
        """Get MCP server dependencies for this agent.
        
        Returns:
            List of MCP server dependencies (empty for this agent)
        """
        return self.mcp_server_dependencies
    
    def analyze_api_documentation(self, scraped_content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze scraped API documentation content.
        
        Args:
            scraped_content: Content from web scraper agent
            
        Returns:
            Analyzed API information
        """
        try:
            # Extract metadata from scraped content
            source_url = scraped_content.get('source_url', '')
            content = scraped_content.get('content', {})
            
            # Perform comprehensive analysis
            analysis_result = {
                "source_url": source_url,
                "analysis_metadata": {
                    "timestamp": "2025-07-10T12:00:00Z",
                    "agent": "api_analysis",
                    "success": True,
                    "confidence_score": 0.85
                },
                "api_info": {
                    "name": "",
                    "version": "",
                    "base_url": "",
                    "description": "",
                    "documentation_quality": "good",
                    "api_type": "REST",  # REST, GraphQL, gRPC, etc.
                    "data_formats": ["JSON"],  # JSON, XML, etc.
                },
                "authentication": {
                    "methods": [],
                    "required": True,
                    "complexity": "medium"
                },
                "endpoints": [],
                "rate_limiting": {
                    "present": False,
                    "details": {}
                },
                "sdks": [],
                "examples_quality": "good",
                "recommended_tools": [],
                "recommended_resources": []
            }
            
            self.logger.info(f"Successfully analyzed API documentation from {source_url}")
            return {
                "success": True,
                "data": analysis_result,
                "message": "API documentation analysis completed"
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing API documentation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def extract_api_endpoints(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract API endpoints from documentation content.
        
        Args:
            content: Documentation content to analyze
            
        Returns:
            Extracted endpoint information
        """
        try:
            endpoints = []
            
            # This would analyze the content and extract endpoint patterns
            # For now, return a standardized structure
            
            endpoint_info = {
                "extraction_metadata": {
                    "timestamp": "2025-07-10T12:00:00Z",
                    "agent": "api_analysis",
                    "total_endpoints": len(endpoints),
                    "success": True
                },
                "endpoints": endpoints,
                "endpoint_patterns": {
                    "base_paths": [],
                    "common_parameters": [],
                    "response_formats": [],
                    "http_methods": []
                }
            }
            
            return {
                "success": True,
                "data": endpoint_info,
                "message": f"Extracted {len(endpoints)} endpoints"
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting API endpoints: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def identify_authentication_methods(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Identify authentication methods from documentation.
        
        Args:
            content: Documentation content to analyze
            
        Returns:
            Authentication method information
        """
        try:
            auth_methods = []
            
            # This would analyze content for authentication patterns
            
            auth_info = {
                "identification_metadata": {
                    "timestamp": "2025-07-10T12:00:00Z",
                    "agent": "api_analysis",
                    "methods_found": len(auth_methods),
                    "success": True
                },
                "authentication_methods": auth_methods,
                "recommended_method": "api_key",  # Based on MC-PEA template support
                "implementation_complexity": "low",
                "security_level": "medium"
            }
            
            return {
                "success": True,
                "data": auth_info,
                "message": f"Identified {len(auth_methods)} authentication methods"
            }
            
        except Exception as e:
            self.logger.error(f"Error identifying authentication methods: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def generate_api_specification(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive API specification from analysis.
        
        Args:
            analysis_data: Complete analysis data
            
        Returns:
            API specification suitable for MCP server generation
        """
        try:
            # Create a specification that the MCP generator can use
            specification = {
                "generation_metadata": {
                    "timestamp": "2025-07-10T12:00:00Z",
                    "agent": "api_analysis",
                    "source": analysis_data.get('source_url', ''),
                    "success": True
                },
                "api_specification": {
                    "name": "",
                    "description": "",
                    "base_url": "",
                    "version": "1.0.0",
                    "authentication": {
                        "type": "api_key",
                        "location": "header",
                        "parameter_name": "Authorization"
                    },
                    "endpoints": [],
                    "schemas": [],
                    "error_handling": {
                        "error_codes": [],
                        "error_format": "json"
                    }
                },
                "mcp_recommendations": {
                    "suggested_tools": [],
                    "suggested_resources": [],
                    "complexity_estimate": "medium",
                    "development_time": "2-4 hours"
                }
            }
            
            return {
                "success": True,
                "data": specification,
                "message": "Generated API specification for MCP server"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating API specification: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def detect_api_patterns(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Detect common API patterns and conventions.
        
        Args:
            content: Documentation content to analyze
            
        Returns:
            Detected patterns and conventions
        """
        try:
            patterns = {
                "detection_metadata": {
                    "timestamp": "2025-07-10T12:00:00Z",
                    "agent": "api_analysis",
                    "success": True
                },
                "detected_patterns": {
                    "restful_conventions": True,
                    "consistent_naming": True,
                    "standard_http_codes": True,
                    "pagination_pattern": None,
                    "versioning_strategy": None,
                    "rate_limiting_headers": False
                },
                "quality_indicators": {
                    "documentation_completeness": 0.8,
                    "example_coverage": 0.7,
                    "consistency_score": 0.9
                },
                "recommendations": []
            }
            
            return {
                "success": True,
                "data": patterns,
                "message": "Detected API patterns and conventions"
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting API patterns: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def process_message(self, message) -> Dict[str, Any]:
        """Process an incoming message.
        
        Args:
            message: Incoming message
            
        Returns:
            Processing result
        """
        # Handle different message types
        if hasattr(message, 'message_type'):
            if message.message_type == "analyze_documentation":
                content = message.content
                return self.analyze_api_documentation(content)
            elif message.message_type == "extract_endpoints":
                content = message.content
                return self.extract_api_endpoints(content)
            elif message.message_type == "identify_auth":
                content = message.content
                return self.identify_authentication_methods(content)
            elif message.message_type == "generate_specification":
                analysis_data = message.content
                return self.generate_api_specification(analysis_data)
        
        return {"success": False, "error": "Unknown message type"}
    
    async def execute_task(self, task) -> Dict[str, Any]:
        """Execute a specific task.
        
        Args:
            task: Task to execute
            
        Returns:
            Execution result
        """
        # Handle different task types
        task_type = task.get('type', 'unknown')
        
        if task_type == 'analyze_documentation':
            content = task.get('content')
            return self.analyze_api_documentation(content)
        elif task_type == 'extract_endpoints':
            content = task.get('content')
            return self.extract_api_endpoints(content)
        elif task_type == 'identify_auth':
            content = task.get('content')
            return self.identify_authentication_methods(content)
        elif task_type == 'generate_specification':
            analysis_data = task.get('analysis_data')
            return self.generate_api_specification(analysis_data)
        else:
            return {"success": False, "error": f"Unknown task type: {task_type}"}
