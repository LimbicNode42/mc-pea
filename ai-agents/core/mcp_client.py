"""
Simple MCP Client for Python agents to call MCP servers.
"""

import subprocess
import json
import logging
from typing import Dict, Any, Optional
import tempfile
import os


class SimpleMCPClient:
    """Simple MCP client for calling MCP servers from Python."""
    
    def __init__(self, server_command: str, logger: Optional[logging.Logger] = None):
        """Initialize MCP client.
        
        Args:
            server_command: Command to start the MCP server
            logger: Optional logger
        """
        self.server_command = server_command
        self.logger = logger or logging.getLogger(__name__)
        self.server_process = None
        
    def start_server(self) -> bool:
        """Start the MCP server process.
        
        Returns:
            True if server started successfully
        """
        try:
            # For now, we'll mock the server start
            self.logger.info(f"Starting MCP server: {self.server_command}")
            # In a real implementation, this would start the server process
            return True
        except Exception as e:
            self.logger.error(f"Failed to start MCP server: {e}")
            return False
    
    def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            params: Tool parameters
            
        Returns:
            Tool result
        """
        try:
            self.logger.info(f"Calling MCP tool: {tool_name} with params: {params}")
            
            # For testing purposes, we'll implement basic fetch functionality
            if tool_name == "fetch_webpage":
                return self._fetch_webpage_fallback(params)
            else:
                return {
                    "status": "error",
                    "error": f"Tool {tool_name} not implemented in fallback mode"
                }
                
        except Exception as e:
            self.logger.error(f"MCP tool call failed: {e}")
            return {
                "status": "error", 
                "error": str(e)
            }
    
    def _fetch_webpage_fallback(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback webpage fetching using requests.
        
        Args:
            params: Parameters including 'url' and optional 'query'
            
        Returns:
            Webpage content
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            import re
            from urllib.parse import urljoin, urlparse
            
            url = params.get("url")
            query = params.get("query", "")
            
            if not url:
                return {"status": "error", "error": "URL parameter required"}
            
            # Fetch the webpage
            headers = {
                'User-Agent': 'MC-PEA WebScraperAgent/1.0 (Educational/Research)'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic information
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title"
            
            # Extract text content
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            text_content = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                link_text = link.get_text().strip()
                if absolute_url and link_text:
                    links.append({
                        "url": absolute_url,
                        "text": link_text[:100]  # Limit text length
                    })
            
            # Extract headings
            headings = []
            for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                heading_text = tag.get_text().strip()
                if heading_text:
                    headings.append({
                        "level": int(tag.name[1]),
                        "text": heading_text
                    })
            
            return {
                "status": "success",
                "url": url,
                "title": title_text,
                "text": text[:50000],  # Limit content size
                "links": links[:100],  # Limit number of links
                "headings": headings[:50],  # Limit number of headings
                "content_length": len(text),
                "link_count": len(links),
                "heading_count": len(headings)
            }
            
        except ImportError:
            return {
                "status": "error",
                "error": "Required packages (requests, beautifulsoup4) not available"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to fetch webpage: {str(e)}"
            }
    
    def stop_server(self):
        """Stop the MCP server process."""
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
            self.logger.info("MCP server stopped")


class MCPClientManager:
    """Manager for MCP clients."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the MCP client manager.
        
        Args:
            logger: Optional logger
        """
        self.logger = logger or logging.getLogger(__name__)
        self.clients: Dict[str, SimpleMCPClient] = {}
    
    def get_client(self, server_name: str) -> Optional[SimpleMCPClient]:
        """Get or create an MCP client for a server.
        
        Args:
            server_name: Name of the MCP server
            
        Returns:
            MCP client instance or None if not available
        """
        if server_name not in self.clients:
            # Map server names to commands
            server_commands = {
                "mcp-server-fetch": "npx @modelcontextprotocol/server-fetch",
                "fetch": "npx @modelcontextprotocol/server-fetch",
                "memory": "npx @modelcontextprotocol/server-memory"
            }
            
            command = server_commands.get(server_name)
            if command:
                client = SimpleMCPClient(command, self.logger)
                if client.start_server():
                    self.clients[server_name] = client
                    return client
            
            self.logger.warning(f"MCP server {server_name} not available, using fallback")
            # Create a fallback client
            fallback_client = SimpleMCPClient(f"fallback-{server_name}", self.logger)
            fallback_client.start_server()
            self.clients[server_name] = fallback_client
            return fallback_client
        
        return self.clients[server_name]
    
    def shutdown_all(self):
        """Shutdown all MCP clients."""
        for client in self.clients.values():
            client.stop_server()
        self.clients.clear()
        self.logger.info("All MCP clients shut down")
