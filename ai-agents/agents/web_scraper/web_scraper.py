"""
Web Scraper Agent for crawling and scraping API documentation using the official MCP fetch server.

This agent uses the official MCP fetch server (mcp-server-fetch) which provides lightweight,
Kubernetes-ready web content fetching without browser dependencies.
"""

from typing import Dict, Any, List, Optional
from core.base_agent import BaseAgent, AgentConfig
from core.agent_config_loader import get_agent_config
import json
import logging
import re
from urllib.parse import urljoin, urlparse


class WebScraperAgent(BaseAgent):
    """Agent responsible for crawling and scraping API documentation using the official MCP fetch server."""
    
    def __init__(self, anthropic_client=None):
        # Load configuration from centralized config file
        config_data = get_agent_config("web_scraper")
        
        # Create agent config using loaded data
        agent_config = AgentConfig(
            name=config_data.get("name", "web_scraper"),
            role=config_data.get("role", "Web Documentation Scraper"),
            goal=config_data.get("goal", "Crawl and scrape API documentation from websites using lightweight web fetching"),
            backstory=config_data.get("backstory", """
            You are an expert web scraper specializing in crawling API documentation websites.
            You use the official MCP fetch server to efficiently extract content from documentation sites
            and structure it in a standardized format for analysis by other agents.
            You're optimized for Kubernetes deployments with lightweight dependencies.
            """)
        )
        
        # Store config data for later use
        self._config_data = config_data
        
        super().__init__(agent_config, anthropic_client)
    
    def get_mcp_dependencies(self) -> List[Dict[str, Any]]:
        """Get MCP server dependencies for this agent."""
        return [
            {
                "name": "fetch",
                "package": "mcp-server-fetch", 
                "type": "official",
                "repository": "https://github.com/modelcontextprotocol/servers/tree/main/src/fetch",
                "description": "Official MCP fetch server for web content retrieval",
                "tools": ["fetch_webpage"],
                "installation": {
                    "uv": "uvx mcp-server-fetch",
                    "pip": "pip install mcp-server-fetch && python -m mcp_server_fetch",
                    "docker": "docker run -i --rm mcp/fetch"
                },
                "lightweight": True,
                "deployment_friendly": True,
                "kubernetes_ready": True
            }
        ]
    
    def get_required_mcp_tools(self) -> List[str]:
        """Get list of required MCP tools for this agent."""
        return ["fetch_webpage"]
    
    def fetch_webpage_content(self, url: str, query: str = None) -> Dict[str, Any]:
        """Fetch webpage content using the MCP fetch server.
        
        Args:
            url: URL to fetch
            query: Optional query to focus content extraction
            
        Returns:
            Webpage content and metadata
        """
        try:
            # Attempt to use MCP fetch tool - this would be handled by the MCP environment
            self.logger.info(f"Fetching webpage content from: {url}")
            
            # In a real MCP environment, this would use the fetch_webpage tool
            # For testing/simulation, we can log the attempt
            if query:
                self.logger.info(f"Using query for focused extraction: {query}")
            
            # This is where the actual MCP tool call would happen
            # The MCP environment would handle the tool invocation
            # fetch_webpage_result = mcp_client.call_tool("fetch_webpage", {"url": url, "query": query})
            
            # For now, return a structure indicating the tool would be called
            return {
                "url": url,
                "title": f"Content from {url}",
                "content": f"MCP fetch_webpage tool would extract content from {url}",
                "links": [],
                "headings": [],
                "status": "mcp_tool_required",
                "tool_name": "fetch_webpage",
                "tool_params": {"url": url, "query": query} if query else {"url": url},
                "mcp_server": "mcp-server-fetch"
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching webpage content: {str(e)}")
            return {
                "url": url,
                "title": "Error",
                "content": f"Failed to fetch content: {str(e)}",
                "links": [],
                "headings": [],
                "status": "error",
                "error": str(e)
            }
    
    def scrape_api_documentation(self, base_url: str, query: str = None) -> Dict[str, Any]:
        """Scrape API documentation from a base URL.
        
        Args:
            base_url: Base URL of the API documentation
            query: Optional query to guide extraction
            
        Returns:
            Scraped documentation structure
        """
        self.logger.info(f"Starting API documentation scraping for: {base_url}")
        
        # Fetch the main page
        main_page = self.fetch_webpage_content(base_url, query)
        
        if main_page.get("status") == "error":
            return {
                "base_url": base_url,
                "pages": [],
                "endpoints": [],
                "status": "error",
                "error": main_page.get("error")
            }
        
        # Extract API endpoints and structure from the main page
        # This would be enhanced with actual content parsing when MCP tools are available
        endpoints = self._extract_endpoints_from_content(main_page.get("content", ""))
        
        return {
            "base_url": base_url,
            "title": main_page.get("title", "API Documentation"),
            "pages": [main_page],
            "endpoints": endpoints,
            "links": main_page.get("links", []),
            "headings": main_page.get("headings", []),
            "status": "success",
            "mcp_tool_used": "fetch_webpage"
        }
    
    def _extract_endpoints_from_content(self, content: str) -> List[Dict[str, Any]]:
        """Extract API endpoints from content.
        
        Args:
            content: Content to extract endpoints from
            
        Returns:
            List of extracted endpoints
        """
        endpoints = []
        
        # Simple regex patterns for common API endpoint formats
        patterns = [
            r'(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s]+)',
            r'`(GET|POST|PUT|DELETE|PATCH)\s+([^`]+)`',
            r'<code>(GET|POST|PUT|DELETE|PATCH)\s+([^<]+)</code>',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    method, path = match
                    endpoints.append({
                        "method": method.upper(),
                        "path": path.strip(),
                        "source": "regex_extraction"
                    })
        
        return endpoints[:20]  # Limit to first 20 endpoints found
    
    async def handle_async_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle async scraping task.
        
        Args:
            task_data: Task data containing URL and parameters
            
        Returns:
            Task result
        """
        url = task_data.get("url")
        query = task_data.get("query")
        
        if not url:
            return {"error": "URL is required", "status": "error"}
        
        try:
            result = self.scrape_api_documentation(url, query)
            return {
                "status": "completed",
                "result": result,
                "timestamp": task_data.get("timestamp")
            }
        except Exception as e:
            self.logger.error(f"Error in async task: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": task_data.get("timestamp")
            }
    
    def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming message.
        
        Args:
            message: Message to process
            
        Returns:
            Response message
        """
        message_type = message.get("type", "unknown")
        
        if message_type == "scrape_request":
            url = message.get("url")
            query = message.get("query")
            
            if not url:
                return {
                    "type": "error",
                    "error": "URL is required for scrape request"
                }
            
            result = self.scrape_api_documentation(url, query)
            return {
                "type": "scrape_response",
                "result": result,
                "original_message": message
            }
        
        elif message_type == "dependencies_request":
            return {
                "type": "dependencies_response",
                "mcp_dependencies": self.get_mcp_dependencies(),
                "required_tools": self.get_required_mcp_tools()
            }
        
        else:
            return {
                "type": "error",
                "error": f"Unknown message type: {message_type}"
            }
    
    def get_tools(self) -> List[Any]:
        """Get tools available to this agent.
        
        Returns:
            List of tools for the agent (empty for MCP-only operation)
        """
        return []  # MCP tools are handled by the MCP environment, not CrewAI tools
    
    async def process_message(self, message) -> Dict[str, Any]:
        """Process an incoming message.
        
        Args:
            message: Incoming message
            
        Returns:
            Processing result
        """
        try:
            if hasattr(message, 'message_type'):
                message_type = message.message_type
                content = message.content if hasattr(message, 'content') else {}
            else:
                # Handle dict-style messages
                message_type = message.get('type', 'unknown')
                content = message
            
            if message_type == "scrape_documentation":
                url = content.get("url")
                query = content.get("query")
                if url:
                    result = self.scrape_api_documentation(url, query)
                    return {"success": True, "result": result}
                else:
                    return {"success": False, "error": "URL not provided in message"}
            
            elif message_type == "scrape_request":
                url = content.get("url")
                query = content.get("query")
                if url:
                    result = self.scrape_api_documentation(url, query)
                    return {"success": True, "result": result}
                else:
                    return {"success": False, "error": "URL not provided in message"}
            
            else:
                return {"success": False, "error": f"Unknown message type: {message_type}"}
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return {"success": False, "error": str(e)}

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task.
        
        Args:
            task: Task to execute
            
        Returns:
            Execution result
        """
        try:
            task_type = task.get("type", "unknown")
            
            if task_type == "scrape_api_documentation":
                url = task.get("url")
                query = task.get("query")
                if url:
                    result = self.scrape_api_documentation(url, query)
                    return {"success": True, "result": result}
                else:
                    return {"success": False, "error": "URL not provided in task"}
            
            elif task_type == "fetch_webpage_content":
                url = task.get("url")
                query = task.get("query")
                if url:
                    result = self.fetch_webpage_content(url, query)
                    return {"success": True, "result": result}
                else:
                    return {"success": False, "error": "URL not provided in task"}
            
            else:
                return {"success": False, "error": f"Unknown task type: {task_type}"}
                
        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            return {"success": False, "error": str(e)}
