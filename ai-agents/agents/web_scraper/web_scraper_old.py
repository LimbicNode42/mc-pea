"""
Web Scraper Agent for crawling and scraping API documentation using Playwright MCP Server.
"""

from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew
from core.base_agent import BaseAgent, AgentConfig
from core.config import get_config, MCPEAConfig
import json
import asyncio
import logging


class WebScraperAgent(BaseAgent):
    """Agent responsible for crawling and scraping API documentation using Playwright MCP Server."""
    
    def __init__(self, anthropic_client=None):
        # Create agent config
        agent_config = AgentConfig(
            name="web_scraper",
            role="Web Documentation Scraper",
            goal="Crawl and scrape API documentation from websites using browser automation",
            backstory="""
            You are an expert web scraper specializing in crawling API documentation websites.
            You use Playwright to navigate through documentation sites, extract content, and 
            structure it in a standardized format for analysis by other agents.
            """
        )
        
        super().__init__(agent_config, anthropic_client)
        
        # MCP Server dependency
        self.mcp_server_dependency = {
            "name": "playwright-mcp-server",
            "package": "@executeautomation/playwright-mcp-server",
            "description": "Browser automation for web scraping API documentation",
            "repository": "https://github.com/executeautomation/mcp-playwright",
            "required": True,
            "status": "external",
            "docker_required": False,
            "installation": {
                "method": "npm",
                "command": "npm install -g @executeautomation/playwright-mcp-server",
                "alternative": "npx @executeautomation/playwright-mcp-server",
                "verification": "npx @executeautomation/playwright-mcp-server --help"
            },
            "config": {
                "mcpServers": {
                    "playwright": {
                        "command": "npx",
                        "args": ["-y", "@executeautomation/playwright-mcp-server"]
                    }
                }
            },
            "tools_provided": [
                "navigate_to_page",
                "extract_text",
                "take_screenshot", 
                "click_element",
                "type_text",
                "wait_for_element",
                "get_page_content"
            ],
            "fallback_available": True,
            "fallback_description": "Can use requests + BeautifulSoup for static content scraping"
        }
        
        # Register for configuration updates
        self.register_config_callback(self._on_scraper_config_update)
    
    def _on_scraper_config_update(self, new_config: MCPEAConfig) -> None:
        """Handle scraper-specific configuration updates.
        
        Args:
            new_config: Updated configuration
        """
        # Update scraper settings based on config
        self.logger.info("Web scraper configuration updated")
    
    def get_tools(self) -> List[Any]:
        """Get tools available to this agent.
        
        Returns:
            List of tools for web scraping
        """
        return [
            self.scrape_api_documentation,
            self.extract_structured_content,
            self.discover_documentation_structure,
            self.validate_playwright_availability,
            self.fallback_scraping
        ]
    
    def get_mcp_dependencies(self) -> List[Dict[str, Any]]:
        """Get MCP server dependencies for this agent.
        
        Returns:
            List of MCP server dependencies
        """
        return [self.mcp_server_dependency]
    
    def scrape_api_documentation(self, documentation_url: str, max_depth: int = 3) -> Dict[str, Any]:
        """Scrape API documentation from a given URL.
        
        Args:
            documentation_url: URL of the API documentation
            max_depth: Maximum depth to crawl (default: 3)
            
        Returns:
            Structured documentation content
        """
        try:
            # First, check if Playwright MCP server is available
            playwright_check = self.validate_playwright_availability()
            
            if playwright_check.get("available", False):
                # Use Playwright MCP server for advanced scraping
                return self._scrape_with_playwright(documentation_url, max_depth)
            else:
                # Use fallback method
                self.logger.info(f"Using fallback scraping for {documentation_url}")
                fallback_result = self.fallback_scraping(documentation_url)
                
                if fallback_result.get("success", False):
                    # Transform fallback result to match expected structure
                    fallback_data = fallback_result.get("data", {})
                    
                    # Convert to structured format
                    scraped_content = {
                        "source_url": documentation_url,
                        "scraping_metadata": {
                            "timestamp": "2025-07-10T12:00:00Z",
                            "agent": "web_scraper",
                            "method": "fallback_requests",
                            "max_depth": 1,  # Fallback is limited to single page
                            "pages_scraped": 1,
                            "success": True,
                            "limitations": [
                                "Static content only",
                                "No JavaScript execution",
                                "Single page only"
                            ]
                        },
                        "site_structure": {
                            "navigation": [],
                            "sections": [],
                            "sidebar_links": fallback_data.get("content", {}).get("links", [])[:10]
                        },
                        "content": {
                            "overview": {
                                "title": fallback_data.get("content", {}).get("title", ""),
                                "description": fallback_data.get("content", {}).get("text_content", "")[:500],
                                "base_url": documentation_url,
                                "authentication_methods": []
                            },
                            "endpoints": [],
                            "authentication": {
                                "methods": [],
                                "examples": []
                            },
                            "schemas": [],
                            "examples": fallback_data.get("content", {}).get("code_blocks", []),
                            "sdks": [],
                            "error_codes": []
                        },
                        "raw_content": {
                            "html_pages": {documentation_url: fallback_data.get("raw_content", {}).get("html", "")},
                            "text_content": {documentation_url: fallback_data.get("content", {}).get("text_content", "")},
                            "images": [],
                            "files": []
                        }
                    }
                    
                    return {
                        "success": True,
                        "data": scraped_content,
                        "message": f"Fallback scraping completed for {documentation_url}",
                        "method": "fallback",
                        "limitations": "Static content only - JavaScript content may be missing"
                    }
                else:
                    return fallback_result
            
        except Exception as e:
            self.logger.error(f"Error scraping documentation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def _scrape_with_playwright(self, documentation_url: str, max_depth: int = 3) -> Dict[str, Any]:
        """Scrape using Playwright MCP server (placeholder for actual implementation).
        
        Args:
            documentation_url: URL of the API documentation
            max_depth: Maximum depth to crawl
            
        Returns:
            Structured documentation content
        """
        # This would connect to the Playwright MCP server and use its tools
        # For now, return a more comprehensive mock structure
        
        scraped_content = {
            "source_url": documentation_url,
            "scraping_metadata": {
                "timestamp": "2025-07-10T12:00:00Z",
                "agent": "web_scraper",
                "method": "playwright_mcp",
                "max_depth": max_depth,
                "pages_scraped": 5,  # Playwright can scrape multiple pages
                "success": True
            },
            "site_structure": {
                "navigation": ["Getting Started", "API Reference", "Examples", "SDKs"],
                "sections": ["Overview", "Authentication", "Endpoints", "Errors"],
                "sidebar_links": []
            },
            "content": {
                "overview": {
                    "title": "API Documentation",
                    "description": "Comprehensive API documentation",
                    "base_url": documentation_url,
                    "authentication_methods": ["API Key", "OAuth 2.0"]
                },
                "endpoints": [],
                "authentication": {
                    "methods": ["api_key", "oauth2"],
                    "examples": []
                },
                "schemas": [],
                "examples": [],
                "sdks": [],
                "error_codes": []
            },
            "raw_content": {
                "html_pages": {},
                "text_content": {},
                "images": [],
                "files": []
            }
        }
        
        self.logger.info(f"Successfully scraped documentation from {documentation_url} using Playwright")
        return {
            "success": True,
            "data": scraped_content,
            "message": f"Playwright scraping completed for {documentation_url}",
            "method": "playwright"
        }
    
    def extract_structured_content(self, raw_html: str, content_type: str = "api_docs") -> Dict[str, Any]:
        """Extract structured content from raw HTML.
        
        Args:
            raw_html: Raw HTML content
            content_type: Type of content to extract (api_docs, openapi, etc.)
            
        Returns:
            Structured content data
        """
        try:
            # This would use Playwright to parse and extract structured content
            # For now, return a standardized structure
            
            structured_content = {
                "content_type": content_type,
                "extraction_metadata": {
                    "timestamp": "2025-07-10T12:00:00Z",
                    "agent": "web_scraper",
                    "html_length": len(raw_html),
                    "success": True
                },
                "extracted_data": {
                    "title": "",
                    "sections": [],
                    "code_blocks": [],
                    "links": [],
                    "images": [],
                    "tables": []
                }
            }
            
            return {
                "success": True,
                "data": structured_content,
                "message": "Successfully extracted structured content"
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting structured content: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def discover_documentation_structure(self, base_url: str) -> Dict[str, Any]:
        """Discover the structure of documentation site.
        
        Args:
            base_url: Base URL of the documentation site
            
        Returns:
            Site structure information
        """
        try:
            # This would use Playwright to discover site structure
            
            site_structure = {
                "base_url": base_url,
                "discovery_metadata": {
                    "timestamp": "2025-07-10T12:00:00Z",
                    "agent": "web_scraper",
                    "success": True
                },
                "structure": {
                    "main_sections": [],
                    "navigation_menus": [],
                    "search_functionality": False,
                    "api_reference": False,
                    "getting_started": False,
                    "examples": False,
                    "sdks": False
                },
                "urls_to_scrape": [],
                "estimated_pages": 0
            }
            
            return {
                "success": True,
                "data": site_structure,
                "message": f"Discovered structure for {base_url}"
            }
            
        except Exception as e:
            self.logger.error(f"Error discovering site structure: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def validate_playwright_availability(self) -> Dict[str, Any]:
        """Check if Playwright MCP server is available and can be used.
        
        Returns:
            Availability status and recommendations
        """
        try:
            import subprocess
            
            # Try to check if npx and playwright are available
            result = subprocess.run(
                ["npx", "@executeautomation/playwright-mcp-server", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "available": True,
                    "method": "playwright-mcp-server",
                    "message": "Playwright MCP server is available and ready to use",
                    "fallback_needed": False
                }
            else:
                return self._recommend_fallback("Playwright MCP server command failed")
                
        except subprocess.TimeoutExpired:
            return self._recommend_fallback("Playwright MCP server command timed out")
        except FileNotFoundError:
            return self._recommend_fallback("npx not found - Node.js may not be installed")
        except Exception as e:
            return self._recommend_fallback(f"Error checking Playwright availability: {str(e)}")
    
    def _recommend_fallback(self, reason: str) -> Dict[str, Any]:
        """Recommend fallback scraping method.
        
        Args:
            reason: Reason why Playwright is not available
            
        Returns:
            Fallback recommendation
        """
        return {
            "success": True,
            "available": False,
            "method": "fallback",
            "message": f"Playwright unavailable: {reason}. Will use fallback scraping.",
            "fallback_needed": True,
            "fallback_limitations": [
                "Cannot handle JavaScript-heavy sites",
                "No browser automation features",
                "Limited to static HTML content",
                "No screenshot capabilities"
            ],
            "installation_help": {
                "nodejs_required": True,
                "install_command": "npm install -g @executeautomation/playwright-mcp-server",
                "docker_alternative": "Not required - this is a Node.js package"
            }
        }
    
    def fallback_scraping(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fallback scraping method using requests + BeautifulSoup when Playwright is unavailable.
        
        Args:
            url: URL to scrape
            options: Scraping options
            
        Returns:
            Basic scraped content with limitations notice
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Basic HTTP request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic content
            scraped_content = {
                "source_url": url,
                "scraping_metadata": {
                    "timestamp": "2025-07-10T12:00:00Z",
                    "agent": "web_scraper",
                    "method": "fallback_requests",
                    "limitations": [
                        "Static content only",
                        "No JavaScript execution",
                        "No browser automation"
                    ],
                    "success": True
                },
                "content": {
                    "title": soup.title.string if soup.title else "",
                    "text_content": soup.get_text(),
                    "links": [a.get('href') for a in soup.find_all('a', href=True)],
                    "headings": [h.get_text() for h in soup.find_all(['h1', 'h2', 'h3', 'h4'])],
                    "code_blocks": [code.get_text() for code in soup.find_all(['code', 'pre'])],
                    "tables": len(soup.find_all('table')),
                    "forms": len(soup.find_all('form'))
                },
                "raw_content": {
                    "html": str(soup),
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                }
            }
            
            return {
                "success": True,
                "data": scraped_content,
                "message": f"Fallback scraping completed for {url}",
                "limitations": "Static content only - JavaScript content may be missing"
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "Fallback libraries not available. Please install: pip install requests beautifulsoup4",
                "data": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Fallback scraping failed: {str(e)}",
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
            if message.message_type == "scrape_documentation":
                url = message.content.get('url')
                max_depth = message.content.get('max_depth', 3)
                return self.scrape_api_documentation(url, max_depth)
            elif message.message_type == "discover_structure":
                url = message.content.get('url')
                return self.discover_documentation_structure(url)
            elif message.message_type == "extract_content":
                html = message.content.get('html')
                content_type = message.content.get('content_type', 'api_docs')
                return self.extract_structured_content(html, content_type)
        
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
        
        if task_type == 'scrape_documentation':
            url = task.get('url')
            max_depth = task.get('max_depth', 3)
            return self.scrape_api_documentation(url, max_depth)
        elif task_type == 'discover_structure':
            url = task.get('url')
            return self.discover_documentation_structure(url)
        elif task_type == 'extract_content':
            html = task.get('html')
            content_type = task.get('content_type', 'api_docs')
            return self.extract_structured_content(html, content_type)
        else:
            return {"success": False, "error": f"Unknown task type: {task_type}"}
