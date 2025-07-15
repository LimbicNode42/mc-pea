"""
Web Scraper Agent for crawling and scraping API documentation using MCP servers.

This agent orchestrates web crawling and content scraping using:
- MCP fetch server (mcp-server-fetch) for web content retrieval
- MCP memory server for tracking scraped pages and maintaining state
- Modular architecture with separate crawler and scraper components
"""

from typing import Dict, Any, List, Optional
from core.base_agent import BaseAgent, AgentConfig
from core.agent_config_loader import get_agent_config
import json
import logging
import re
from urllib.parse import urljoin, urlparse

# Import the separated modules
from .web_crawler import WebCrawler
from .content_scraper import ContentScraper


class WebScraperAgent(BaseAgent):
    """Agent responsible for orchestrating web crawling and content scraping using MCP servers."""
    
    def __init__(self, anthropic_client=None, crawl_depth: Optional[int] = None):
        # Load configuration from centralized config file
        config_data = get_agent_config("web_scraper")
        
        # Create agent config using loaded data
        agent_config = AgentConfig(
            name=config_data.get("name", "web_scraper"),
            role=config_data.get("role", "Web Documentation Scraper"),
            goal=config_data.get("goal", "Crawl and scrape API documentation from websites using lightweight web fetching"),
            backstory=config_data.get("backstory", """
            You are an expert web scraper specializing in crawling API documentation websites.
            You orchestrate web crawling and content scraping using modular components and MCP servers:
            - WebCrawler for discovering links up to configured depth
            - ContentScraper for extracting API endpoints and parameters
            - MCP fetch server for lightweight web content retrieval
            - MCP memory server for tracking scraped pages and maintaining state
            You're optimized for Kubernetes deployments with lightweight dependencies.
            """)
        )
        
        # Store config data for later use
        self._config_data = config_data
        
        # Configure crawling parameters
        crawling_config = config_data.get("crawling", {})
        self.crawl_depth = crawl_depth if crawl_depth is not None else crawling_config.get("default_depth", 2)
        self.max_depth = crawling_config.get("max_depth", 5)
        self.min_depth = crawling_config.get("min_depth", 1)
        
        # Create crawling configuration for modules
        module_config = {
            "crawl_depth": self.crawl_depth,
            "max_depth": self.max_depth,
            "min_depth": self.min_depth,
            "follow_external_links": crawling_config.get("follow_external_links", False),
            "respect_robots_txt": crawling_config.get("respect_robots_txt", True),
            "max_pages_per_domain": crawling_config.get("max_pages_per_domain", 100),
            "request_delay_seconds": crawling_config.get("request_delay_seconds", 1.0)
        }
        
        # Validate depth parameter
        if self.crawl_depth < self.min_depth:
            self.crawl_depth = self.min_depth
        elif self.crawl_depth > self.max_depth:
            self.crawl_depth = self.max_depth
        
        # Initialize base agent (without anthropic_client parameter)
        super().__init__(agent_config)
        
        # Initialize MCP client manager for accessing MCP tools
        from core.mcp_client import MCPClientManager
        self.mcp_manager = MCPClientManager(self.logger)
        self.fetch_client = self.mcp_manager.get_client("fetch")
        
        # Initialize the modular components after logger is available, passing MCP client
        self.web_crawler = WebCrawler(module_config, self.logger, self.fetch_client)
        self.content_scraper = ContentScraper(module_config, self.logger, self.fetch_client)
    
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
            },
            {
                "name": "memory",
                "package": "mcp-server-memory",
                "type": "official", 
                "repository": "https://github.com/modelcontextprotocol/servers/tree/main/src/memory",
                "description": "Official MCP memory server for state management and tracking",
                "tools": ["store_memory", "retrieve_memory", "list_memories"],
                "installation": {
                    "uv": "uvx mcp-server-memory",
                    "pip": "pip install mcp-server-memory && python -m mcp_server_memory",
                    "docker": "docker run -i --rm mcp/memory"
                },
                "lightweight": True,
                "deployment_friendly": True,
                "kubernetes_ready": True
            }
        ]
    
    def get_required_mcp_tools(self) -> List[str]:
        """Get list of required MCP tools for this agent."""
        return ["fetch_webpage", "store_memory", "retrieve_memory", "list_memories"]
    
    def crawl_and_scrape(self, base_url: str, query: str = None) -> Dict[str, Any]:
        """Main method to crawl and scrape API documentation from a base URL.
        
        This method orchestrates the entire process:
        1. Use WebCrawler to discover all links up to configured depth
        2. Use ContentScraper to extract content and API endpoints from discovered pages
        3. Use MCP memory server to track progress and avoid re-scraping
        
        Args:
            base_url: Base URL of the API documentation
            query: Optional query to guide extraction
            
        Returns:
            Complete crawling and scraping results
        """
        self.logger.info(f"Starting crawl and scrape operation for: {base_url}")
        
        # Step 1: Crawl the website to discover all links
        self.logger.info("Phase 1: Crawling website to discover links")
        crawl_results = self.web_crawler.crawl_website(base_url, query)
        
        if crawl_results.get("status") == "error":
            return {
                "base_url": base_url,
                "status": "error",
                "error": crawl_results.get("error"),
                "phase": "crawling"
            }
        
        # Step 2: Scrape content from discovered pages
        self.logger.info("Phase 2: Scraping content from discovered pages")
        scraping_results = []
        
        for page_data in crawl_results.get("crawl_results", []):
            scrape_result = self.content_scraper.scrape_page_content(page_data)
            scraping_results.append(scrape_result)
            
            # Log progress
            if scrape_result.get("status") == "scraped":
                endpoints_count = scrape_result.get("endpoints_found", 0)
                self.logger.info(f"Scraped {page_data.get('url')}: {endpoints_count} endpoints found")
        
        # Step 3: Aggregate results
        all_endpoints = []
        all_parameters = []
        successful_scrapes = 0
        
        for scrape_result in scraping_results:
            if scrape_result.get("status") in ["scraped", "already_scraped"]:
                successful_scrapes += 1
                content_summary = scrape_result.get("content_summary", {})
                all_endpoints.extend(content_summary.get("endpoints", []))
                all_parameters.extend(content_summary.get("parameters", []))
        
        return {
            "base_url": base_url,
            "status": "completed",
            "crawl_results": crawl_results,
            "scraping_results": scraping_results,
            "summary": {
                "pages_crawled": crawl_results.get("pages_crawled", 0),
                "pages_scraped": successful_scrapes,
                "total_endpoints": len(all_endpoints),
                "total_parameters": len(all_parameters),
                "unique_endpoints": len(set((ep.get("method"), ep.get("path")) for ep in all_endpoints)),
                "crawl_depth_used": crawl_results.get("crawl_depth", self.crawl_depth)
            },
            "endpoints": all_endpoints,
            "parameters": all_parameters,
            "crawl_statistics": self.web_crawler.get_crawl_statistics(),
            "scraping_statistics": self.content_scraper.get_scraping_statistics()
        }
    
    def fetch_webpage_content(self, url: str, query: str = None) -> Dict[str, Any]:
        """Fetch webpage content using the MCP fetch server (delegated to crawler).
        
        Args:
            url: URL to fetch
            query: Optional query to focus content extraction
            
        Returns:
            Webpage content and metadata
        """
        return self.web_crawler.fetch_page_via_mcp(url, query)
    
    def scrape_api_documentation(self, base_url: str, query: str = None) -> Dict[str, Any]:
        """Legacy method - now delegates to crawl_and_scrape for backward compatibility.
        
        Args:
            base_url: Base URL of the API documentation
            query: Optional query to guide extraction
            
        Returns:
            Scraped documentation structure (backward compatible format)
        """
        self.logger.info(f"Using legacy scrape_api_documentation method, delegating to crawl_and_scrape")
        
        # Use the new orchestrated method
        results = self.crawl_and_scrape(base_url, query)
        
        # Convert to legacy format for backward compatibility
        if results.get("status") == "error":
            return {
                "base_url": base_url,
                "pages": [],
                "endpoints": [],
                "status": "error",
                "error": results.get("error")
            }
        
        # Get the first page content for legacy compatibility
        crawl_results = results.get("crawl_results", {})
        first_page = None
        if crawl_results.get("crawl_results"):
            first_page_data = crawl_results["crawl_results"][0]
            first_page = first_page_data.get("page_content", {})
        
        return {
            "base_url": base_url,
            "title": first_page.get("title", "API Documentation") if first_page else "API Documentation",
            "pages": [page_data.get("page_content", {}) for page_data in crawl_results.get("crawl_results", [])],
            "endpoints": results.get("endpoints", []),
            "parameters": results.get("parameters", []),
            "links": crawl_results.get("discovered_links", []),
            "headings": [],  # Could aggregate from all pages if needed
            "status": "success",
            "mcp_tool_used": "fetch_webpage",
            "summary": results.get("summary", {}),
            "new_format_available": True  # Indicate that new format is available via crawl_and_scrape
        }
    
    async def handle_async_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle async scraping task.
        
        Args:
            task_data: Task data containing URL and parameters
            
        Returns:
            Task result
        """
        url = task_data.get("url")
        query = task_data.get("query")
        use_new_format = task_data.get("use_crawl_and_scrape", False)
        
        if not url:
            return {"error": "URL is required", "status": "error"}
        
        try:
            if use_new_format:
                result = self.crawl_and_scrape(url, query)
            else:
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
            use_new_format = message.get("use_crawl_and_scrape", False)
            
            if not url:
                return {
                    "type": "error",
                    "error": "URL is required for scrape request"
                }
            
            if use_new_format:
                result = self.crawl_and_scrape(url, query)
            else:
                result = self.scrape_api_documentation(url, query)
                
            return {
                "type": "scrape_response",
                "result": result,
                "original_message": message
            }
        
        elif message_type == "crawl_and_scrape_request":
            url = message.get("url")
            query = message.get("query")
            
            if not url:
                return {
                    "type": "error",
                    "error": "URL is required for crawl and scrape request"
                }
            
            result = self.crawl_and_scrape(url, query)
            return {
                "type": "crawl_and_scrape_response",
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
            
            if message_type in ["scrape_documentation", "scrape_request"]:
                url = content.get("url")
                query = content.get("query")
                use_new_format = content.get("use_crawl_and_scrape", False)
                
                if url:
                    if use_new_format:
                        result = self.crawl_and_scrape(url, query)
                    else:
                        result = self.scrape_api_documentation(url, query)
                    return {"success": True, "result": result}
                else:
                    return {"success": False, "error": "URL not provided in message"}
            
            elif message_type == "crawl_and_scrape":
                url = content.get("url")
                query = content.get("query")
                if url:
                    result = self.crawl_and_scrape(url, query)
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
                use_new_format = task.get("use_crawl_and_scrape", False)
                
                if url:
                    if use_new_format:
                        result = self.crawl_and_scrape(url, query)
                    else:
                        result = self.scrape_api_documentation(url, query)
                    return {"success": True, "result": result}
                else:
                    return {"success": False, "error": "URL not provided in task"}
            
            elif task_type == "crawl_and_scrape":
                url = task.get("url")
                query = task.get("query")
                if url:
                    result = self.crawl_and_scrape(url, query)
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

    def get_crawling_config(self) -> Dict[str, Any]:
        """Get current crawling configuration."""
        return {
            "crawl_depth": self.crawl_depth,
            "max_depth": self.max_depth,
            "min_depth": self.min_depth,
            "follow_external_links": self.web_crawler.follow_external_links,
            "respect_robots_txt": self.web_crawler.respect_robots_txt,
            "max_pages_per_domain": self.web_crawler.max_pages_per_domain,
            "request_delay_seconds": self.web_crawler.request_delay_seconds
        }
    
    def update_crawl_depth(self, new_depth: int) -> bool:
        """Update the crawl depth with validation.
        
        Args:
            new_depth: New depth value to set
            
        Returns:
            True if update was successful, False if depth was out of bounds
        """
        if new_depth < self.min_depth or new_depth > self.max_depth:
            self.logger.warning(f"Depth {new_depth} out of bounds [{self.min_depth}, {self.max_depth}]")
            return False
            
        self.crawl_depth = new_depth
        self.web_crawler.crawl_depth = new_depth
        self.logger.info(f"Updated crawl depth to {new_depth}")
        return True
    
    def get_modular_components(self) -> Dict[str, Any]:
        """Get information about the modular components.
        
        Returns:
            Information about crawler and scraper modules
        """
        return {
            "web_crawler": {
                "class": "WebCrawler",
                "description": "Handles website crawling and link discovery",
                "statistics": self.web_crawler.get_crawl_statistics()
            },
            "content_scraper": {
                "class": "ContentScraper", 
                "description": "Handles content extraction and API endpoint discovery",
                "statistics": self.content_scraper.get_scraping_statistics()
            },
            "architecture": "modular",
            "mcp_integration": {
                "fetch_server": "mcp-server-fetch",
                "memory_server": "mcp-server-memory"
            }
        }
    
    def cleanup(self):
        """Cleanup method to shutdown MCP clients."""
        if hasattr(self, 'mcp_manager'):
            self.logger.info("Shutting down MCP clients")
            self.mcp_manager.shutdown_all()
    
    def __del__(self):
        """Destructor to ensure cleanup happens."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during cleanup
