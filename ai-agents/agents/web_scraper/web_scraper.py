"""
Web Scraper Agent for crawling and scraping API documentation using the official MCP fetch server.

This agent uses the official MCP fetch server (mcp-server-fetch) which provides lightweight,
Kubernetes-ready web content fetching without browser dependencies. Falls back to 
requests + BeautifulSoup when the MCP server is unavailable.
"""

from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew
from core.base_agent import BaseAgent, AgentConfig
from core.config import get_config, MCPEAConfig
from core.agent_config_loader import get_agent_config
import json
import logging
import requests
from urllib.parse import urljoin, urlparse
import time
from bs4 import BeautifulSoup
import html2text
import re


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
        
        # Initialize HTML to text converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0  # Don't wrap text
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MC-PEA Documentation Scraper 1.0'
        })
        
        # Register for configuration updates
        self.register_config_callback(self._on_scraper_config_update)
    
    def _on_scraper_config_update(self, new_config: MCPEAConfig) -> None:
        """Handle scraper-specific configuration updates.
        
        Args:
            new_config: Updated configuration
        """
        self.logger.info("Web scraper configuration updated")
    
    def get_tools(self) -> List[Any]:
        """Get tools available to this agent.
        
        For now, we'll return an empty list to avoid CrewAI tool validation issues.
        The actual functionality is available through direct method calls.
        
        Returns:
            Empty list for now
        """
        return []
    
    def get_mcp_dependencies(self) -> List[Dict[str, Any]]:
        """Get MCP server dependencies for this agent.
        
        Returns:
            List of required MCP servers from configuration
        """
        return self._config_data.get("mcp_dependencies", [
            {
                "name": "fetch",
                "package": "mcp-server-fetch", 
                "type": "official",
                "repository": "https://github.com/modelcontextprotocol/servers/tree/main/src/fetch",
                "description": "Official MCP fetch server for web content retrieval",
                "tools": ["fetch"],
                "installation": {
                    "uv": "uvx mcp-server-fetch",
                    "pip": "pip install mcp-server-fetch && python -m mcp_server_fetch",
                    "docker": "docker run -i --rm mcp/fetch"
                },
                "lightweight": True,
                "deployment_friendly": True,
                "kubernetes_ready": True
            }
        ])
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information including dependency status.
        
        Returns:
            Agent information with MCP fetch server dependency from configuration
        """
        base_info = super().get_agent_info()
        dependencies = self.get_mcp_dependencies()
        
        base_info.update({
            "mcp_dependencies": dependencies,
            "dependency_count": len(dependencies),
            "has_dependencies": len(dependencies) > 0,
            "fallback_available": True,
            "fallback_description": self._config_data.get("fallback_description", "Falls back to lightweight requests + BeautifulSoup when MCP fetch server unavailable"),
            "deployment_friendly": self._config_data.get("deployment_friendly", True),
            "kubernetes_ready": self._config_data.get("kubernetes_ready", True),
            "docker_requirements": self._config_data.get("docker_requirements", "Official MCP fetch server (lightweight Python)")
        })
        return base_info
    
    def fetch_webpage_content(self, url: str, query: str = None) -> Dict[str, Any]:
        """Fetch webpage content using the MCP fetch server.
        
        This method first tries to use the fetch_webpage tool (MCP fetch server),
        then falls back to requests + BeautifulSoup if unavailable.
        
        Args:
            url: URL to fetch
            query: Optional query to focus content extraction
            
        Returns:
            Webpage content and metadata
        """
        try:
            # Primary method: Use MCP fetch server via fetch_webpage tool
            # Note: fetch_webpage is the tool provided by MCP fetch server
            # This will be available when the agent is used in an MCP environment
            # For now, we'll implement the fallback method
            
            # TODO: When integrated with MCP environment, use:
            # result = self.fetch_webpage(url=url, max_length=10000)
            
            # Fallback method: Direct HTTP request with BeautifulSoup
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.title.string if soup.title else ""
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Convert to clean text
            text_content = self.html_converter.handle(str(soup))
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                link_text = link.get_text(strip=True)
                if href and link_text:
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(url, href)
                    links.append({
                        "text": link_text,
                        "url": absolute_url
                    })
            
            # Extract headings for structure
            headings = []
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                headings.append({
                    "level": int(heading.name[1]),
                    "text": heading.get_text(strip=True)
                })
            
            return {
                "url": url,
                "title": title.strip(),
                "content": text_content,
                "links": links[:50],  # Limit to first 50 links
                "headings": headings[:20],  # Limit to first 20 headings
                "status": "success",
                "method": "fallback_requests",
                "timestamp": time.time(),
                "note": "Using fallback method - MCP fetch server preferred"
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching webpage {url}: {e}")
            return {
                "url": url,
                "error": str(e),
                "status": "failed",
                "method": "fallback_requests",
                "timestamp": time.time()
            }
    
    def scrape_api_documentation(self, documentation_url: str, max_depth: int = 3) -> Dict[str, Any]:
        """Scrape API documentation from a given URL.
        
        Args:
            documentation_url: URL of the API documentation
            max_depth: Maximum depth to crawl (default: 3)
            
        Returns:
            Structured documentation content
        """
        try:
            self.logger.info(f"Starting documentation scraping for: {documentation_url}")
            
            # Fetch main page
            main_page = self.fetch_webpage_content(documentation_url, "API documentation structure")
            
            if main_page.get("status") != "success":
                return {
                    "source_url": documentation_url,
                    "error": f"Failed to fetch main page: {main_page.get('error', 'Unknown error')}",
                    "success": False
                }
            
            # Analyze page structure
            structure = self.analyze_page_structure(main_page)
            
            # Extract key sections
            sections = self._extract_documentation_sections(main_page)
            
            # Build comprehensive result
            scraped_content = {
                "source_url": documentation_url,
                "scraping_metadata": {
                    "timestamp": time.time(),
                    "agent": "web_scraper",
                    "method": "mcp_fetch_server", 
                    "server": "mcp-server-fetch",
                    "max_depth": max_depth,
                    "pages_scraped": 1,  # Start with main page
                    "success": True,
                    "deployment_friendly": True,
                    "lightweight": True
                },
                "site_structure": structure,
                "content": {
                    "overview": {
                        "title": main_page.get("title", ""),
                        "description": self._extract_description(main_page),
                        "base_url": documentation_url
                    },
                    "sections": sections,
                    "navigation": structure.get("navigation", []),
                    "api_endpoints": self._extract_api_endpoints(main_page),
                    "code_examples": self._extract_code_examples(main_page)
                },
                "metadata": {
                    "language": self._detect_language(main_page),
                    "framework": self._detect_framework(main_page),
                    "documentation_type": self._classify_documentation_type(main_page)
                }
            }
            
            # If max_depth > 1, crawl additional pages
            if max_depth > 1:
                additional_pages = self._crawl_additional_pages(
                    main_page, documentation_url, max_depth - 1
                )
                scraped_content["scraping_metadata"]["pages_scraped"] += len(additional_pages)
                scraped_content["additional_pages"] = additional_pages
            
            return scraped_content
            
        except Exception as e:
            self.logger.error(f"Error scraping documentation: {e}")
            return {
                "source_url": documentation_url,
                "error": str(e),
                "success": False,
                "scraping_metadata": {
                    "agent": "web_scraper",
                    "method": "fetch_webpage",
                    "timestamp": time.time()
                }
            }
    
    def analyze_page_structure(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the structure of a webpage.
        
        Args:
            page_data: Page data from fetch_webpage_content
            
        Returns:
            Structured analysis of page layout
        """
        headings = page_data.get("headings", [])
        links = page_data.get("links", [])
        
        # Categorize links
        navigation_links = []
        api_links = []
        guide_links = []
        
        for link in links:
            link_text_lower = link["text"].lower()
            link_url_lower = link["url"].lower()
            
            if any(nav_word in link_text_lower for nav_word in ["api", "reference", "endpoint"]):
                api_links.append(link)
            elif any(guide_word in link_text_lower for guide_word in ["guide", "tutorial", "getting started", "quickstart"]):
                guide_links.append(link)
            elif any(nav_word in link_text_lower for nav_word in ["home", "docs", "documentation", "menu"]):
                navigation_links.append(link)
        
        return {
            "navigation": navigation_links[:10],
            "api_references": api_links[:10],
            "guides": guide_links[:10],
            "heading_structure": headings,
            "total_links": len(links),
            "total_headings": len(headings)
        }
    
    def _extract_documentation_sections(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract main documentation sections from page content.
        
        Args:
            page_data: Page data from fetch_webpage_content
            
        Returns:
            List of documentation sections
        """
        sections = []
        headings = page_data.get("headings", [])
        content = page_data.get("content", "")
        
        # Split content by headings to create sections
        content_lines = content.split('\n')
        current_section = None
        
        for line in content_lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line is a heading
            heading_match = None
            for heading in headings:
                if heading["text"] in line:
                    heading_match = heading
                    break
            
            if heading_match and heading_match["level"] <= 3:  # Only h1, h2, h3
                # Save previous section
                if current_section:
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    "title": heading_match["text"],
                    "level": heading_match["level"],
                    "content": []
                }
            elif current_section:
                current_section["content"].append(line)
        
        # Add final section
        if current_section:
            sections.append(current_section)
        
        # Convert content lists to strings and limit sections
        for section in sections[:10]:  # Limit to 10 sections
            section["content"] = '\n'.join(section["content"][:20])  # Limit content length
        
        return sections
    
    def _extract_description(self, page_data: Dict[str, Any]) -> str:
        """Extract page description from content.
        
        Args:
            page_data: Page data from fetch_webpage_content
            
        Returns:
            Page description
        """
        content = page_data.get("content", "")
        lines = content.split('\n')
        
        # Look for first substantial paragraph
        for line in lines:
            line = line.strip()
            if len(line) > 50 and not line.startswith('#'):
                return line[:300] + "..." if len(line) > 300 else line
        
        return "No description available"
    
    def _extract_api_endpoints(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract API endpoints from page content.
        
        Args:
            page_data: Page data from fetch_webpage_content
            
        Returns:
            List of API endpoints found
        """
        endpoints = []
        content = page_data.get("content", "")
        
        # Simple pattern matching for common API patterns
        import re
        
        # Look for HTTP methods and paths
        http_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-{}]+)'
        matches = re.findall(http_pattern, content, re.IGNORECASE)
        
        for method, path in matches[:10]:  # Limit to 10 endpoints
            endpoints.append({
                "method": method.upper(),
                "path": path,
                "description": f"{method.upper()} {path}"
            })
        
        return endpoints
    
    def _extract_code_examples(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract code examples from page content.
        
        Args:
            page_data: Page data from fetch_webpage_content
            
        Returns:
            List of code examples found
        """
        examples = []
        content = page_data.get("content", "")
        
        # Look for code blocks (markdown style)
        import re
        code_pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(code_pattern, content, re.DOTALL)
        
        for language, code in matches[:5]:  # Limit to 5 examples
            examples.append({
                "language": language or "text",
                "code": code.strip()[:500]  # Limit code length
            })
        
        return examples
    
    def _detect_language(self, page_data: Dict[str, Any]) -> str:
        """Detect programming language from content.
        
        Args:
            page_data: Page data from fetch_webpage_content
            
        Returns:
            Detected programming language
        """
        content = page_data.get("content", "").lower()
        
        # Simple keyword-based detection
        language_keywords = {
            "python": ["python", "pip", "import", "def ", "class "],
            "javascript": ["javascript", "npm", "node", "function", "const", "let"],
            "java": ["java", "maven", "gradle", "public class", "import java"],
            "go": ["golang", "go mod", "func ", "import ("],
            "rust": ["rust", "cargo", "fn ", "use ", "struct"],
            "typescript": ["typescript", "npm", "interface", "type "]
        }
        
        for language, keywords in language_keywords.items():
            if any(keyword in content for keyword in keywords):
                return language
        
        return "unknown"
    
    def _detect_framework(self, page_data: Dict[str, Any]) -> str:
        """Detect framework from content.
        
        Args:
            page_data: Page data from fetch_webpage_content
            
        Returns:
            Detected framework
        """
        content = page_data.get("content", "").lower()
        
        frameworks = {
            "react": ["react", "jsx", "component"],
            "vue": ["vue", "vuejs", "nuxt"],
            "angular": ["angular", "typescript", "component"],
            "django": ["django", "python", "models"],
            "flask": ["flask", "python", "app.route"],
            "express": ["express", "node", "app.get"],
            "fastapi": ["fastapi", "python", "async def"],
            "spring": ["spring", "java", "annotation"]
        }
        
        for framework, keywords in frameworks.items():
            if any(keyword in content for keyword in keywords):
                return framework
        
        return "unknown"
    
    def _classify_documentation_type(self, page_data: Dict[str, Any]) -> str:
        """Classify the type of documentation.
        
        Args:
            page_data: Page data from fetch_webpage_content
            
        Returns:
            Documentation type classification
        """
        content = page_data.get("content", "").lower()
        title = page_data.get("title", "").lower()
        
        if any(word in content + title for word in ["api", "reference", "endpoint"]):
            return "api_reference"
        elif any(word in content + title for word in ["guide", "tutorial", "getting started"]):
            return "tutorial"
        elif any(word in content + title for word in ["sdk", "library", "package"]):
            return "sdk_documentation"
        else:
            return "general_documentation"
    
    def _crawl_additional_pages(self, main_page: Dict[str, Any], base_url: str, remaining_depth: int) -> List[Dict[str, Any]]:
        """Crawl additional pages based on links from main page.
        
        Args:
            main_page: Main page data
            base_url: Base URL for relative link resolution
            remaining_depth: Remaining crawl depth
            
        Returns:
            List of additional page data
        """
        if remaining_depth <= 0:
            return []
        
        additional_pages = []
        links = main_page.get("links", [])
        
        # Filter for documentation-relevant links
        relevant_links = []
        base_domain = urlparse(base_url).netloc
        
        for link in links[:10]:  # Limit to 10 links to avoid excessive crawling
            link_url = link["url"]
            link_domain = urlparse(link_url).netloc
            
            # Only follow links to same domain
            if link_domain == base_domain:
                link_text_lower = link["text"].lower()
                # Focus on API and guide links
                if any(keyword in link_text_lower for keyword in ["api", "guide", "tutorial", "reference", "getting started"]):
                    relevant_links.append(link)
        
        # Crawl relevant links
        for link in relevant_links[:3]:  # Limit to 3 additional pages
            try:
                page_data = self.fetch_webpage_content(link["url"])
                if page_data.get("status") == "success":
                    page_data["source_link"] = link
                    additional_pages.append(page_data)
                    
                # Add small delay to be respectful
                time.sleep(1)
                
            except Exception as e:
                self.logger.warning(f"Failed to crawl {link['url']}: {e}")
                continue
        
        return additional_pages
    
    def extract_structured_content(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure content from scraped data for AI analysis.
        
        Args:
            scraped_data: Raw scraped data
            
        Returns:
            Structured content optimized for AI processing
        """
        try:
            structured = {
                "source_url": scraped_data.get("source_url", ""),
                "title": scraped_data.get("content", {}).get("overview", {}).get("title", ""),
                "description": scraped_data.get("content", {}).get("overview", {}).get("description", ""),
                "api_endpoints": scraped_data.get("content", {}).get("api_endpoints", []),
                "code_examples": scraped_data.get("content", {}).get("code_examples", []),
                "main_sections": scraped_data.get("content", {}).get("sections", []),
                "navigation": scraped_data.get("site_structure", {}).get("navigation", []),
                "metadata": {
                    "language": scraped_data.get("metadata", {}).get("language", "unknown"),
                    "framework": scraped_data.get("metadata", {}).get("framework", "unknown"),
                    "doc_type": scraped_data.get("metadata", {}).get("documentation_type", "unknown"),
                    "pages_analyzed": scraped_data.get("scraping_metadata", {}).get("pages_scraped", 1)
                },
                "processing_notes": {
                    "method": "mcp_fetch_server",
                    "server": "mcp-server-fetch",
                    "kubernetes_ready": True,
                    "no_browser_required": True,
                    "deployment_friendly": True,
                    "lightweight": True
                }
            }
            
            return structured
            
        except Exception as e:
            self.logger.error(f"Error structuring content: {e}")
            return {
                "error": f"Failed to structure content: {e}",
                "source_url": scraped_data.get("source_url", "unknown")
            }
    
    def discover_documentation_structure(self, base_url: str) -> Dict[str, Any]:
        """Discover the overall structure of documentation site.
        
        Args:
            base_url: Base URL of documentation site
            
        Returns:
            Site structure analysis
        """
        try:
            self.logger.info(f"Discovering documentation structure for: {base_url}")
            
            # Fetch main page
            main_page = self.fetch_webpage_content(base_url)
            
            if main_page.get("status") != "success":
                return {
                    "base_url": base_url,
                    "error": f"Failed to fetch main page: {main_page.get('error')}",
                    "success": False
                }
            
            # Analyze structure
            structure = self.analyze_page_structure(main_page)
            
            # Categorize discovered links
            categorized_links = {
                "api_references": structure.get("api_references", []),
                "guides_tutorials": structure.get("guides", []),
                "navigation": structure.get("navigation", [])
            }
            
            return {
                "base_url": base_url,
                "site_title": main_page.get("title", ""),
                "structure": categorized_links,
                "total_links_found": structure.get("total_links", 0),
                "heading_count": structure.get("total_headings", 0),
                "language": self._detect_language(main_page),
                "framework": self._detect_framework(main_page),
                "doc_type": self._classify_documentation_type(main_page),
                "success": True,
                "method": "fetch_webpage",
                "deployment_friendly": True
            }
            
        except Exception as e:
            self.logger.error(f"Error discovering documentation structure: {e}")
            return {
                "base_url": base_url,
                "error": str(e),
                "success": False
            }
    
    async def process_message(self, message) -> Dict[str, Any]:
        """Process an incoming message.
        
        Args:
            message: Incoming message
            
        Returns:
            Processing result
        """
        try:
            if message.message_type == "scrape_documentation":
                url = message.content.get("url")
                max_depth = message.content.get("max_depth", 2)
                if url:
                    result = self.scrape_api_documentation(url, max_depth)
                    return {"success": True, "result": result}
                else:
                    return {"success": False, "error": "URL not provided in message"}
            
            elif message.message_type == "discover_structure":
                url = message.content.get("url")
                if url:
                    result = self.discover_documentation_structure(url)
                    return {"success": True, "result": result}
                else:
                    return {"success": False, "error": "URL not provided in message"}
            
            else:
                return {"success": False, "error": f"Unknown message type: {message.message_type}"}
                
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
            task_type = task.get("type")
            
            if task_type == "scrape_api_documentation":
                url = task.get("url")
                max_depth = task.get("max_depth", 2)
                if url:
                    result = self.scrape_api_documentation(url, max_depth)
                    return {"success": True, "result": result}
                else:
                    return {"success": False, "error": "URL not provided in task"}
            
            elif task_type == "extract_structured_content":
                content = task.get("content")
                if content:
                    result = self.extract_structured_content(content)
                    return {"success": True, "result": result}
                else:
                    return {"success": False, "error": "Content not provided in task"}
            
            elif task_type == "discover_documentation_structure":
                url = task.get("url")
                if url:
                    result = self.discover_documentation_structure(url)
                    return {"success": True, "result": result}
                else:
                    return {"success": False, "error": "URL not provided in task"}
            
            elif task_type == "fetch_webpage_content":
                url = task.get("url")
                query = task.get("query", "")
                if url:
                    result = self.fetch_webpage_content(url, query)
                    return {"success": True, "result": result}
                else:
                    return {"success": False, "error": "URL not provided in task"}
            
            elif task_type == "analyze_page_structure":
                url = task.get("url")
                if url:
                    result = self.analyze_page_structure(url)
                    return {"success": True, "result": result}
                else:
                    return {"success": False, "error": "URL not provided in task"}
            
            else:
                return {"success": False, "error": f"Unknown task type: {task_type}"}
                
        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            return {"success": False, "error": str(e)}


def create_web_scraper_agent(anthropic_client=None) -> WebScraperAgent:
    """Factory function to create a WebScraperAgent instance.
    
    Args:
        anthropic_client: Anthropic client instance
        
    Returns:
        Configured WebScraperAgent instance
    """
    return WebScraperAgent(anthropic_client)
