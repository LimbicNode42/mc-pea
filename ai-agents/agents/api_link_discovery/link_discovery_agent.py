"""
API Link Discovery Agent for discovering and cataloging API-related web links.

This agent specializes in web crawling and link discovery using MCP servers:
- Discovers API documentation links up to configured depth
- Respects robots.txt and domain limits
- Tracks crawl state using MCP memory server
- Optimized for API documentation discovery
"""

from typing import Dict, Any, List, Optional, Set
from core.base_agent import BaseAgent, AgentConfig
from core.agent_config_loader import get_agent_config
from .web_crawler import WebCrawler
import logging
import time


class LinkDiscoveryAgent(BaseAgent):
    """Agent responsible for discovering and cataloging API-related web links."""
    
    def __init__(self, anthropic_client=None, crawl_depth: Optional[int] = None):
        # Load configuration from centralized config file
        config_data = get_agent_config("api_link_discovery")
        
        # Create agent config using loaded data
        agent_config = AgentConfig(
            name=config_data.get("name", "api_link_discovery"),
            role=config_data.get("role", "API Link Discovery Specialist"),
            goal=config_data.get("goal", "Discover and catalog API-related web links for documentation analysis"),
            backstory=config_data.get("backstory", """
            You are a specialized web crawling expert focused on discovering and mapping API-related web links.
            You systematically explore websites to build comprehensive maps of available API documentation,
            endpoint references, and related content. You use MCP servers for lightweight operations:
            - MCP fetch server for efficient web content retrieval
            - MCP memory server for tracking discovered links and crawl state
            You're optimized for Kubernetes deployments with minimal resource usage.
            """)
        )
        
        # Store config data for later use
        self._config_data = config_data
        
        super().__init__(agent_config, anthropic_client)
        
        # Initialize MCP client (will be set when available)
        self.mcp_client = None
        
        # Initialize web crawler
        crawling_config = config_data.get("crawling", {})
        if crawl_depth is not None:
            crawling_config["crawl_depth"] = crawl_depth
            
        self.crawler = WebCrawler(crawling_config, self.logger, self.mcp_client)
        
        # Track discovery state
        self.discovery_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Register for configuration updates
        self.register_config_callback(self._on_link_discovery_config_update)
    
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
    
    def _on_link_discovery_config_update(self, new_config) -> None:
        """Handle link discovery-specific configuration updates.
        
        Args:
            new_config: Updated configuration
        """
        # Update crawler configuration
        if hasattr(self, 'crawler'):
            crawling_config = new_config.get("crawling", {})
            self.crawler.update_config(crawling_config)
        
        self.logger.info("API link discovery configuration updated")
    
    def get_tools(self) -> List[Any]:
        """Get tools available to this agent.
        
        Returns:
            List of tools for link discovery
        """
        # Return empty list for now - tools will be implemented as MCP server integrations
        return []
    
    def discover_links(self, start_url: str, max_depth: Optional[int] = None, 
                      target_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Discover API-related links starting from a URL.
        
        Args:
            start_url: Starting URL for discovery
            max_depth: Maximum crawl depth (overrides config)
            target_patterns: URL patterns to prioritize
            
        Returns:
            Discovery results with found links
        """
        session_id = f"api_discovery_{int(time.time())}"
        
        self.logger.info(f"🔍 Starting API link discovery from: {start_url}")
        self.logger.info(f"📋 Session ID: {session_id}")
        
        # Configure crawler for this session
        crawl_config = self.crawler.config.copy()
        if max_depth is not None:
            crawl_config["max_depth"] = max_depth
        
        # Start discovery
        discovery_result = self.crawler.crawl_website(start_url)
        
        # Store session information
        self.discovery_sessions[session_id] = {
            "start_url": start_url,
            "start_time": time.time(),
            "status": "completed",
            "result": discovery_result,
            "target_patterns": target_patterns,
            "config": crawl_config
        }
        
        # Filter results based on target patterns if provided
        if target_patterns:
            discovery_result = self._filter_by_patterns(discovery_result, target_patterns)
        
        self.logger.info(f"✅ API link discovery completed: {len(discovery_result.get('discovered_links', []))} links found")
        
        return {
            "session_id": session_id,
            "start_url": start_url,
            "discovery_result": discovery_result,
            "links_found": len(discovery_result.get("discovered_links", [])),
            "pages_crawled": len(discovery_result.get("crawled_pages", [])),
            "status": "completed"
        }
    
    def _filter_by_patterns(self, discovery_result: Dict[str, Any], patterns: List[str]) -> Dict[str, Any]:
        """Filter discovery results by URL patterns.
        
        Args:
            discovery_result: Original discovery results
            patterns: URL patterns to match
            
        Returns:
            Filtered discovery results
        """
        import re
        
        filtered_links = []
        discovered_links = discovery_result.get("discovered_links", [])
        
        for link in discovered_links:
            url = link.get("url", "")
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    filtered_links.append(link)
                    break
        
        filtered_result = discovery_result.copy()
        filtered_result["discovered_links"] = filtered_links
        filtered_result["original_count"] = len(discovered_links)
        filtered_result["filtered_count"] = len(filtered_links)
        
        return filtered_result
    
    def get_discovery_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of a discovery session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session status information
        """
        if session_id not in self.discovery_sessions:
            return {
                "session_id": session_id,
                "status": "not_found",
                "error": "Session not found"
            }
        
        session = self.discovery_sessions[session_id]
        return {
            "session_id": session_id,
            "status": session["status"],
            "start_url": session["start_url"],
            "start_time": session["start_time"],
            "duration": time.time() - session["start_time"],
            "links_discovered": len(session["result"].get("discovered_links", [])),
            "pages_crawled": len(session["result"].get("crawled_pages", []))
        }
    
    def get_discovered_links(self, session_id: str, link_type: Optional[str] = None) -> Dict[str, Any]:
        """Get discovered links from a session.
        
        Args:
            session_id: Session identifier
            link_type: Optional filter by link type
            
        Returns:
            Discovered links
        """
        if session_id not in self.discovery_sessions:
            return {
                "session_id": session_id,
                "status": "not_found",
                "error": "Session not found"
            }
        
        session = self.discovery_sessions[session_id]
        discovered_links = session["result"].get("discovered_links", [])
        
        # Filter by link type if specified
        if link_type:
            discovered_links = [
                link for link in discovered_links 
                if link.get("type") == link_type
            ]
        
        return {
            "session_id": session_id,
            "links": discovered_links,
            "total_count": len(discovered_links),
            "link_types": list(set(link.get("type") for link in discovered_links))
        }
    
    def analyze_link_patterns(self, session_id: str) -> Dict[str, Any]:
        """Analyze patterns in discovered API-related links.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Link pattern analysis
        """
        if session_id not in self.discovery_sessions:
            return {
                "session_id": session_id,
                "status": "not_found",
                "error": "Session not found"
            }
        
        session = self.discovery_sessions[session_id]
        discovered_links = session["result"].get("discovered_links", [])
        
        # Analyze patterns
        patterns = {
            "api_patterns": [],
            "doc_patterns": [],
            "reference_patterns": [],
            "guide_patterns": []
        }
        
        api_keywords = ["api", "endpoint", "reference", "rest", "graphql"]
        doc_keywords = ["docs", "documentation", "guide", "tutorial", "examples"]
        
        for link in discovered_links:
            url = link.get("url", "").lower()
            title = link.get("title", "").lower()
            
            # Check for API patterns
            if any(keyword in url or keyword in title for keyword in api_keywords):
                patterns["api_patterns"].append(link)
            
            # Check for documentation patterns
            if any(keyword in url or keyword in title for keyword in doc_keywords):
                patterns["doc_patterns"].append(link)
        
        return {
            "session_id": session_id,
            "patterns": patterns,
            "analysis": {
                "api_links_found": len(patterns["api_patterns"]),
                "doc_links_found": len(patterns["doc_patterns"]),
                "total_analyzed": len(discovered_links)
            }
        }
    
    async def process_message(self, message) -> Dict[str, Any]:
        """Process an incoming message.
        
        Args:
            message: Incoming message
            
        Returns:
            Processing result
        """
        if hasattr(message, 'message_type'):
            if message.message_type == "discover_links":
                content = message.content
                return self.discover_links(
                    content.get("start_url"),
                    content.get("max_depth"),
                    content.get("target_patterns")
                )
            elif message.message_type == "get_discovery_status":
                return self.get_discovery_status(message.content.get("session_id"))
            elif message.message_type == "analyze_patterns":
                return self.analyze_link_patterns(message.content.get("session_id"))
        
        return {"success": False, "error": "Unknown message type"}
    
    async def execute_task(self, task) -> Dict[str, Any]:
        """Execute a specific task.
        
        Args:
            task: Task to execute
            
        Returns:
            Execution result
        """
        task_type = task.get('type', 'unknown')
        
        if task_type == 'discover_links':
            spec = task.get('specification', {})
            return self.discover_links(
                spec.get('start_url'),
                spec.get('max_depth'),
                spec.get('target_patterns')
            )
        elif task_type == 'analyze_patterns':
            return self.analyze_link_patterns(task.get('session_id'))
        else:
            return {"success": False, "error": f"Unknown task type: {task_type}"}
    
    def get_crawler_statistics(self) -> Dict[str, Any]:
        """Get crawler statistics.
        
        Returns:
            Crawler statistics
        """
        return self.crawler.get_crawling_statistics()
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if hasattr(self, 'crawler') and self.crawler:
                self.crawler.cleanup()
            
            self.logger.info("🧹 LinkDiscoveryAgent cleanup completed")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error during LinkDiscoveryAgent cleanup: {e}")
