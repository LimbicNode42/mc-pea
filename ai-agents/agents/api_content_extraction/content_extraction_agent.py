"""
API Content Extraction Agent for extracting API endpoints and documentation content.

This agent specializes in content analysis and API endpoint discovery using AI:
- Extracts API endpoints from documentation using Claude AI
- Analyzes content structure and parameters
- Tracks extraction state using MCP memory server
- AI-first approach with no fallback patterns
"""

from typing import Dict, Any, List, Optional
from core.base_agent import BaseAgent, AgentConfig
from core.agent_config_loader import get_agent_config
from .content_extractor import ContentExtractor
import logging
import time
import json


class ContentExtractionAgent(BaseAgent):
    """Agent responsible for extracting and analyzing API content from web pages."""
    
    def __init__(self, anthropic_client=None):
        # Load configuration from centralized config file
        config_data = get_agent_config("api_content_extraction")
        
        # Create agent config using loaded data
        agent_config = AgentConfig(
            name=config_data.get("name", "api_content_extraction"),
            role=config_data.get("role", "API Content Extraction Specialist"),
            goal=config_data.get("goal", "Extract and analyze API endpoints and documentation content"),
            backstory=config_data.get("backstory", """
            You are a specialized content analysis expert focused on extracting API endpoints and documentation.
            You use advanced AI analysis to understand complex documentation structures and identify API patterns.
            You rely exclusively on Claude AI for intelligent content analysis - no static patterns or fallbacks.
            You use MCP servers for efficient operations:
            - MCP memory server for tracking extracted content and analysis state
            You're optimized for AI-first analysis with no hardcoded extraction rules.
            """)
        )
        
        # Store config data for later use
        self._config_data = config_data
        
        super().__init__(agent_config, anthropic_client)
        
        # Initialize MCP client (will be set when available)
        self.mcp_client = None
        
        # Initialize content extractor
        extraction_config = config_data.get("extraction", {})
        self.extractor = ContentExtractor(extraction_config, self.logger, self.mcp_client)
        
        # Track extraction sessions
        self.extraction_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Register for configuration updates
        self.register_config_callback(self._on_content_extraction_config_update)
    
    @property
    def name(self) -> str:
        """Get agent name."""
        return self.config.name
    
    @property
    def role(self) -> str:
        """Get agent role."""
        return self.config.role
    
    @property
    def goal(self) -> str:
        """Get agent goal."""
        return self.config.goal
    
    def get_mcp_dependencies(self) -> List[Dict[str, Any]]:
        """Get MCP server dependencies for this agent.
        
        Returns:
            List of required MCP servers from configuration
        """
        return self._config_data.get("mcp_dependencies", [])
    
    def _on_content_extraction_config_update(self, new_config) -> None:
        """Handle content extraction-specific configuration updates.
        
        Args:
            new_config: Updated configuration
        """
        # Update extractor configuration
        if hasattr(self, 'extractor'):
            extraction_config = new_config.get("extraction", {})
            self.extractor.config.update(extraction_config)
        
        self.logger.info("Content extraction configuration updated")
    
    def get_tools(self) -> List[Any]:
        """Get tools available to this agent.
        
        Returns:
            List of tools for content extraction
        """
        # Return empty list for now - tools will be implemented as MCP server integrations
        return []
    
    def extract_content(self, pages_data: List[Dict[str, Any]], 
                       focus_query: Optional[str] = None) -> Dict[str, Any]:
        """Extract content from multiple pages.
        
        Args:
            pages_data: List of page data from link discovery
            focus_query: Optional query to focus extraction
            
        Returns:
            Extraction results with endpoints and content analysis
        """
        session_id = f"extraction_{int(time.time())}"
        
        self.logger.info(f"🔍 Starting content extraction from {len(pages_data)} pages")
        self.logger.info(f"📋 Session ID: {session_id}")
        
        if focus_query:
            self.logger.info(f"🎯 Focus query: {focus_query}")
        
        # Initialize extraction session
        session_data = {
            "session_id": session_id,
            "start_time": time.time(),
            "status": "in_progress",
            "focus_query": focus_query,
            "pages_to_extract": len(pages_data),
            "pages_completed": 0,
            "total_endpoints": 0,
            "total_parameters": 0,
            "extraction_results": []
        }
        
        self.extraction_sessions[session_id] = session_data
        
        # Process each page
        all_endpoints = []
        all_parameters = []
        
        for i, page_data in enumerate(pages_data):
            try:
                self.logger.info(f"📄 Processing page {i+1}/{len(pages_data)}: {page_data.get('url', 'unknown')}")
                
                # Extract content from this page
                page_result = self.extractor.scrape_page_content(page_data)
                
                if page_result.get("status") == "scraped":
                    content_summary = page_result.get("content_summary", {})
                    endpoints = content_summary.get("endpoints", [])
                    parameters = content_summary.get("parameters", [])
                    
                    all_endpoints.extend(endpoints)
                    all_parameters.extend(parameters)
                    
                    # Update session
                    session_data["pages_completed"] += 1
                    session_data["extraction_results"].append(page_result)
                    
                    self.logger.info(f"✅ Extracted {len(endpoints)} endpoints, {len(parameters)} parameters from page")
                else:
                    self.logger.warning(f"⚠️ Failed to extract from page: {page_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                self.logger.error(f"❌ Error processing page {i+1}: {e}")
                continue
        
        # Finalize session
        session_data["status"] = "completed"
        session_data["completion_time"] = time.time()
        session_data["total_endpoints"] = len(all_endpoints)
        session_data["total_parameters"] = len(all_parameters)
        session_data["duration"] = session_data["completion_time"] - session_data["start_time"]
        
        # Analyze extracted content
        analysis = self._analyze_extracted_content(all_endpoints, all_parameters)
        
        self.logger.info(f"✅ Content extraction completed: {len(all_endpoints)} endpoints, {len(all_parameters)} parameters")
        
        return {
            "session_id": session_id,
            "extraction_summary": {
                "pages_processed": len(pages_data),
                "pages_successful": session_data["pages_completed"],
                "total_endpoints": len(all_endpoints),
                "total_parameters": len(all_parameters),
                "duration": session_data["duration"]
            },
            "endpoints": all_endpoints,
            "parameters": all_parameters,
            "analysis": analysis,
            "session_data": session_data,
            "status": "completed"
        }
    
    def extract_endpoints_from_text(self, content: str, source_url: Optional[str] = None) -> Dict[str, Any]:
        """Extract endpoints from raw text content.
        
        Args:
            content: Text content to analyze
            source_url: Optional source URL for context
            
        Returns:
            Extracted endpoints with metadata
        """
        self.logger.info(f"🔍 Extracting endpoints from text content ({len(content)} chars)")
        
        try:
            endpoints = self.extractor.extract_endpoints_from_content(content, source_url)
            
            return {
                "endpoints": endpoints,
                "source_url": source_url,
                "content_length": len(content),
                "endpoints_found": len(endpoints),
                "extraction_method": "claude_ai_analysis",
                "timestamp": time.time(),
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to extract endpoints from text: {e}")
            return {
                "endpoints": [],
                "source_url": source_url,
                "content_length": len(content),
                "endpoints_found": 0,
                "error": str(e),
                "status": "error"
            }
    
    def extract_api_parameters(self, content: str, endpoint_path: Optional[str] = None) -> Dict[str, Any]:
        """Extract API parameters from content.
        
        Args:
            content: Content to analyze
            endpoint_path: Optional specific endpoint to focus on
            
        Returns:
            Extracted parameters with metadata
        """
        self.logger.info(f"🔍 Extracting API parameters from content")
        
        try:
            parameters = self.extractor.extract_api_parameters(content, endpoint_path)
            
            return {
                "parameters": parameters,
                "endpoint_path": endpoint_path,
                "content_length": len(content),
                "parameters_found": len(parameters),
                "extraction_method": "claude_ai_analysis",
                "timestamp": time.time(),
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to extract parameters: {e}")
            return {
                "parameters": [],
                "endpoint_path": endpoint_path,
                "content_length": len(content),
                "parameters_found": 0,
                "error": str(e),
                "status": "error"
            }
    
    def get_extraction_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of an extraction session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session status information
        """
        if session_id not in self.extraction_sessions:
            return {
                "session_id": session_id,
                "status": "not_found",
                "error": "Session not found"
            }
        
        session = self.extraction_sessions[session_id]
        
        # Calculate progress
        progress = 0
        if session["pages_to_extract"] > 0:
            progress = (session["pages_completed"] / session["pages_to_extract"]) * 100
        
        return {
            "session_id": session_id,
            "status": session["status"],
            "progress": progress,
            "pages_to_extract": session["pages_to_extract"],
            "pages_completed": session["pages_completed"],
            "total_endpoints": session["total_endpoints"],
            "total_parameters": session["total_parameters"],
            "duration": time.time() - session["start_time"] if session["status"] == "in_progress" else session.get("duration", 0)
        }
    
    def get_extracted_endpoints(self, session_id: str, endpoint_type: Optional[str] = None) -> Dict[str, Any]:
        """Get extracted endpoints from a session.
        
        Args:
            session_id: Session identifier
            endpoint_type: Optional filter by endpoint type
            
        Returns:
            Extracted endpoints
        """
        if session_id not in self.extraction_sessions:
            return {
                "session_id": session_id,
                "status": "not_found",
                "error": "Session not found"
            }
        
        session = self.extraction_sessions[session_id]
        
        # Collect all endpoints from extraction results
        all_endpoints = []
        for result in session.get("extraction_results", []):
            content_summary = result.get("content_summary", {})
            endpoints = content_summary.get("endpoints", [])
            all_endpoints.extend(endpoints)
        
        # Filter by endpoint type if specified
        if endpoint_type:
            all_endpoints = [
                endpoint for endpoint in all_endpoints 
                if endpoint.get("method", "").upper() == endpoint_type.upper()
            ]
        
        return {
            "session_id": session_id,
            "endpoints": all_endpoints,
            "total_count": len(all_endpoints),
            "endpoint_methods": list(set(ep.get("method", "UNKNOWN") for ep in all_endpoints))
        }
    
    def _analyze_extracted_content(self, endpoints: List[Dict[str, Any]], 
                                 parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze extracted content for patterns and insights.
        
        Args:
            endpoints: List of extracted endpoints
            parameters: List of extracted parameters
            
        Returns:
            Content analysis results
        """
        analysis = {
            "endpoint_analysis": {
                "total_endpoints": len(endpoints),
                "methods": {},
                "paths": [],
                "domains": set()
            },
            "parameter_analysis": {
                "total_parameters": len(parameters),
                "types": {},
                "required_count": 0,
                "optional_count": 0
            },
            "patterns": {
                "rest_api_detected": False,
                "graphql_detected": False,
                "authentication_required": False,
                "versioning_detected": False
            }
        }
        
        # Analyze endpoints
        for endpoint in endpoints:
            method = endpoint.get("method", "UNKNOWN")
            analysis["endpoint_analysis"]["methods"][method] = analysis["endpoint_analysis"]["methods"].get(method, 0) + 1
            
            path = endpoint.get("path", "")
            analysis["endpoint_analysis"]["paths"].append(path)
            
            # Check for patterns
            if "/graphql" in path.lower():
                analysis["patterns"]["graphql_detected"] = True
            if any(version in path for version in ["/v1/", "/v2/", "/api/v"]):
                analysis["patterns"]["versioning_detected"] = True
            if any(auth in path.lower() for auth in ["auth", "login", "token"]):
                analysis["patterns"]["authentication_required"] = True
        
        # Analyze parameters
        for parameter in parameters:
            param_type = parameter.get("type", "unknown")
            analysis["parameter_analysis"]["types"][param_type] = analysis["parameter_analysis"]["types"].get(param_type, 0) + 1
            
            if parameter.get("required", False):
                analysis["parameter_analysis"]["required_count"] += 1
            else:
                analysis["parameter_analysis"]["optional_count"] += 1
        
        # Detect REST API pattern
        if analysis["endpoint_analysis"]["methods"]:
            rest_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
            found_methods = set(analysis["endpoint_analysis"]["methods"].keys())
            if found_methods.intersection(rest_methods):
                analysis["patterns"]["rest_api_detected"] = True
        
        return analysis
    
    async def process_message(self, message) -> Dict[str, Any]:
        """Process an incoming message.
        
        Args:
            message: Incoming message
            
        Returns:
            Processing result
        """
        if hasattr(message, 'message_type'):
            if message.message_type == "extract_content":
                content = message.content
                return self.extract_content(
                    content.get("pages_data", []),
                    content.get("focus_query")
                )
            elif message.message_type == "extract_endpoints":
                content = message.content
                return self.extract_endpoints_from_text(
                    content.get("content", ""),
                    content.get("source_url")
                )
            elif message.message_type == "get_extraction_status":
                return self.get_extraction_status(message.content.get("session_id"))
        
        return {"success": False, "error": "Unknown message type"}
    
    async def execute_task(self, task) -> Dict[str, Any]:
        """Execute a specific task.
        
        Args:
            task: Task to execute
            
        Returns:
            Execution result
        """
        task_type = task.get('type', 'unknown')
        
        if task_type == 'extract_content':
            spec = task.get('specification', {})
            return self.extract_content(
                spec.get('pages_data', []),
                spec.get('focus_query')
            )
        elif task_type == 'extract_endpoints':
            spec = task.get('specification', {})
            return self.extract_endpoints_from_text(
                spec.get('content', ''),
                spec.get('source_url')
            )
        else:
            return {"success": False, "error": f"Unknown task type: {task_type}"}
    
    def get_extraction_statistics(self) -> Dict[str, Any]:
        """Get extraction statistics.
        
        Returns:
            Extraction statistics
        """
        return self.extractor.get_scraping_statistics()
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if hasattr(self, 'extractor') and self.extractor:
                self.extractor.cleanup()
            
            self.logger.info("🧹 ContentExtractionAgent cleanup completed")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error during ContentExtractionAgent cleanup: {e}")
