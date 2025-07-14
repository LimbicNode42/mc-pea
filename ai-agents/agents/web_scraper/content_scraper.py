"""
Content Scraper Module for extracting API endpoints and parameters from web pages.

This module handles the content extraction and analysis aspect of web scraping,
focusing on extracting API endpoints, parameters, and documentation structure
from the pages discovered by the web crawler.
"""

from typing import Dict, Any, List, Optional, Set
import logging
import re
import json
import time
from urllib.parse import urlparse, urljoin


class ContentScraper:
    """Handles content extraction and API endpoint discovery."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """Initialize the content scraper.
        
        Args:
            config: Scraping configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Track scraped pages using MCP memory server
        self.scraped_pages: Set[str] = set()
        self.extracted_endpoints: List[Dict[str, Any]] = []
        
        # Patterns for API endpoint detection
        self.endpoint_patterns = self._compile_endpoint_patterns()
        
    def _compile_endpoint_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for API endpoint detection.
        
        Returns:
            List of compiled regex patterns
        """
        http_methods = r'(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|CONNECT|TRACE)'
        
        patterns = [
            # Standard format: METHOD /path
            re.compile(rf'{http_methods}\s+(/[^\s]+)', re.IGNORECASE | re.MULTILINE),
            # Markdown code blocks: `METHOD /path`
            re.compile(rf'`{http_methods}\s+([^`]+)`', re.IGNORECASE),
            # HTML code tags: <code>METHOD /path</code>
            re.compile(rf'<code>{http_methods}\s+([^<]+)</code>', re.IGNORECASE),
            # Bold markdown: **METHOD** /path
            re.compile(rf'\*\*{http_methods}\*\*\s+([^\s]+)', re.IGNORECASE),
            # Documentation format: METHOD: /path
            re.compile(rf'{http_methods}:\s*(/[^\s]+)', re.IGNORECASE),
            # API docs format: • METHOD /path or - METHOD /path
            re.compile(rf'[•\-]\s*{http_methods}\s+(/[^\s]+)', re.IGNORECASE),
            # Table format: | METHOD | /path |
            re.compile(rf'\|\s*{http_methods}\s*\|\s*([^|]+)\s*\|', re.IGNORECASE),
            # JSON/YAML format: "method": "GET", "path": "/api/..."
            re.compile(rf'"method":\s*"{http_methods}",\s*"path":\s*"([^"]+)"', re.IGNORECASE),
            # OpenAPI format: get: /path or post: /path
            re.compile(rf'({http_methods.lower()}|{http_methods}):\s*(/[^\s]+)', re.IGNORECASE),
            # Full URL patterns: METHOD https://domain/path
            re.compile(rf'{http_methods}\s+(https?://[^\s]+)', re.IGNORECASE),
            # Endpoint documentation: endpoint: METHOD /path
            re.compile(rf'endpoint:\s*{http_methods}\s+(/[^\s]+)', re.IGNORECASE),
        ]
        
        return patterns
    
    def store_scraped_page_in_memory(self, url: str, content_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Store scraped page information in MCP memory server.
        
        Args:
            url: URL of the scraped page
            content_summary: Summary of extracted content
            
        Returns:
            Result of memory storage operation
        """
        try:
            # This would be the actual MCP memory server call
            memory_entry = {
                "url": url,
                "scraped_timestamp": time.time(),
                "content_summary": content_summary,
                "endpoints_found": len(content_summary.get('endpoints', [])),
                "headings_found": len(content_summary.get('headings', [])),
                "status": "scraped"
            }
            
            self.logger.info(f"Storing scraped page in memory: {url}")
            
            # In a real MCP environment, this would use the memory server
            # memory_result = mcp_client.call_tool("store_memory", {
            #     "key": f"scraped_page_{hash(url)}",
            #     "value": json.dumps(memory_entry),
            #     "category": "scraped_pages"
            # })
            
            # For now, return a structure indicating the tool would be called
            return {
                "status": "mcp_tool_required",
                "tool_name": "store_memory",
                "tool_params": {
                    "key": f"scraped_page_{abs(hash(url))}",
                    "value": json.dumps(memory_entry),
                    "category": "scraped_pages"
                },
                "mcp_server": "mcp-server-memory",
                "local_storage": memory_entry
            }
            
        except Exception as e:
            self.logger.error(f"Error storing scraped page in memory: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_if_page_scraped(self, url: str) -> Dict[str, Any]:
        """Check if a page has already been scraped using MCP memory server.
        
        Args:
            url: URL to check
            
        Returns:
            Information about whether page was previously scraped
        """
        try:
            page_key = f"scraped_page_{abs(hash(url))}"
            
            self.logger.debug(f"Checking if page already scraped: {url}")
            
            # In a real MCP environment, this would use the memory server
            # memory_result = mcp_client.call_tool("retrieve_memory", {
            #     "key": page_key,
            #     "category": "scraped_pages"
            # })
            
            # For now, return a structure indicating the tool would be called
            return {
                "status": "mcp_tool_required",
                "tool_name": "retrieve_memory",
                "tool_params": {
                    "key": page_key,
                    "category": "scraped_pages"
                },
                "mcp_server": "mcp-server-memory",
                "is_scraped": url in self.scraped_pages  # Local fallback
            }
            
        except Exception as e:
            self.logger.error(f"Error checking scraped page status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "is_scraped": False
            }
    
    def extract_endpoints_from_content(self, content: str, source_url: str = None) -> List[Dict[str, Any]]:
        """Extract API endpoints from content using comprehensive patterns.
        
        Args:
            content: Content to extract endpoints from
            source_url: URL where content was found (for context)
            
        Returns:
            List of extracted endpoints with metadata
        """
        endpoints = []
        
        # Use compiled patterns for better performance
        for pattern in self.endpoint_patterns:
            matches = pattern.findall(content)
            
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    # Handle tuple matches (method, path)
                    method, path = match[0], match[1]
                    # Clean up the path - remove common artifacts
                    path = re.sub(r'[`<>]', '', path)  # Remove markdown/HTML artifacts
                    path = path.strip().rstrip('.,;:|')  # Remove trailing punctuation
                    path = path.split()[0] if path else ''  # Take first word if multiple
                    
                    # Skip if path doesn't look like an API path
                    if path and (path.startswith('/') or path.startswith('http')) and len(path) > 1:
                        endpoint = {
                            "method": method.upper(),
                            "path": path,
                            "source": "pattern_extraction",
                            "source_url": source_url,
                            "extraction_timestamp": time.time()
                        }
                        
                        # Try to extract additional context around the endpoint
                        context = self._extract_endpoint_context(content, method, path)
                        if context:
                            endpoint.update(context)
                        
                        endpoints.append(endpoint)
                        
                elif isinstance(match, str):
                    # Handle single string matches (for simpler patterns)
                    parts = match.split(' ', 1)
                    if len(parts) == 2:
                        method, path = parts
                        path = re.sub(r'[`<>]', '', path)
                        path = path.strip().rstrip('.,;:|')
                        path = path.split()[0] if path else ''
                        
                        if path and (path.startswith('/') or path.startswith('http')) and len(path) > 1:
                            endpoint = {
                                "method": method.upper(),
                                "path": path,
                                "source": "pattern_extraction",
                                "source_url": source_url,
                                "extraction_timestamp": time.time()
                            }
                            
                            context = self._extract_endpoint_context(content, method, path)
                            if context:
                                endpoint.update(context)
                            
                            endpoints.append(endpoint)
        
        # Extract endpoints from structured sections
        section_endpoints = self._extract_endpoints_from_sections(content, source_url)
        endpoints.extend(section_endpoints)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_endpoints = []
        for endpoint in endpoints:
            key = (endpoint['method'], endpoint['path'])
            if key not in seen:
                seen.add(key)
                unique_endpoints.append(endpoint)
        
        return unique_endpoints[:50]  # Limit to first 50 unique endpoints found
    
    def _extract_endpoint_context(self, content: str, method: str, path: str) -> Dict[str, Any]:
        """Extract additional context around an endpoint.
        
        Args:
            content: Full content
            method: HTTP method
            path: Endpoint path
            
        Returns:
            Additional context information
        """
        context = {}
        
        # Look for the endpoint in context
        endpoint_pattern = re.escape(f"{method} {path}")
        match = re.search(rf'(.{{0,200}}){endpoint_pattern}(.{{0,200}})', content, re.IGNORECASE | re.DOTALL)
        
        if match:
            before_context = match.group(1)
            after_context = match.group(2)
            
            # Extract description from surrounding text
            description_patterns = [
                r'description[:\s]+([^.\n]+)',
                r'summary[:\s]+([^.\n]+)',
                r'title[:\s]+([^.\n]+)',
            ]
            
            for desc_pattern in description_patterns:
                desc_match = re.search(desc_pattern, before_context + after_context, re.IGNORECASE)
                if desc_match:
                    context['description'] = desc_match.group(1).strip()
                    break
            
            # Extract parameters
            param_patterns = [
                r'parameters?[:\s]*\n((?:\s*[-*]\s*[^\n]+\n?)+)',
                r'params?[:\s]*\n((?:\s*[-*]\s*[^\n]+\n?)+)',
                r'\{([^}]+)\}',  # Path parameters
                r'\?([^&\s]+)',  # Query parameters
            ]
            
            for param_pattern in param_patterns:
                param_matches = re.findall(param_pattern, after_context, re.IGNORECASE)
                if param_matches:
                    if 'parameters' not in context:
                        context['parameters'] = []
                    for param_match in param_matches:
                        if isinstance(param_match, str):
                            context['parameters'].append(param_match.strip())
        
        return context
    
    def _extract_endpoints_from_sections(self, content: str, source_url: str = None) -> List[Dict[str, Any]]:
        """Extract endpoints from structured documentation sections.
        
        Args:
            content: Content to search
            source_url: Source URL for context
            
        Returns:
            List of endpoints found in sections
        """
        endpoints = []
        
        # Additional patterns for REST API documentation sections
        section_patterns = [
            # GitHub-style endpoint lists
            r'REST API endpoints for ([^:]+):\s*\n((?:\s*-[^\n]+\n?)+)',
            # Swagger/OpenAPI style paths
            r'paths:\s*\n((?:\s+/[^:]+:\s*\n(?:\s+[^:]+:[^\n]*\n?)+)+)',
            # Documentation endpoint listings
            r'## ([^#\n]+)\s*\n((?:\s*[-*]\s*[A-Z]+\s+/[^\n]+\n?)+)',
        ]
        
        for section_pattern in section_patterns:
            section_matches = re.findall(section_pattern, content, re.MULTILINE | re.IGNORECASE)
            for section_match in section_matches:
                if len(section_match) >= 2:
                    section_name, section_content = section_match[0], section_match[1]
                    # Extract individual endpoints from the section
                    endpoint_lines = re.findall(r'[-*]\s*([A-Z]+)\s+(/[^\s\n]+)', section_content)
                    for endpoint_match in endpoint_lines:
                        if len(endpoint_match) == 2:
                            method, path = endpoint_match
                            endpoints.append({
                                "method": method.upper(),
                                "path": path.strip(),
                                "source": "section_extraction",
                                "category": section_name.strip(),
                                "source_url": source_url,
                                "extraction_timestamp": time.time()
                            })
        
        return endpoints
    
    def extract_api_parameters(self, content: str, endpoint_path: str = None) -> List[Dict[str, Any]]:
        """Extract API parameters from content.
        
        Args:
            content: Content to extract parameters from
            endpoint_path: Specific endpoint path to focus on
            
        Returns:
            List of extracted parameters
        """
        parameters = []
        
        # Parameter patterns
        param_patterns = [
            # JSON schema style
            r'"([^"]+)":\s*\{\s*"type":\s*"([^"]+)"(?:,\s*"description":\s*"([^"]+)")?',
            # OpenAPI parameter definitions
            r'- name:\s*([^\n]+)\s*\n\s*in:\s*([^\n]+)\s*\n\s*description:\s*([^\n]+)',
            # Table format parameters
            r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|',
            # Path parameters in braces
            r'\{([^}]+)\}',
            # Query parameters
            r'\?([^&\s=]+)=',
        ]
        
        for pattern in param_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 1:
                    param_name = match[0].strip()
                    param_type = match[1].strip() if len(match) > 1 else "string"
                    param_desc = match[2].strip() if len(match) > 2 else ""
                    
                    parameters.append({
                        "name": param_name,
                        "type": param_type,
                        "description": param_desc,
                        "endpoint_path": endpoint_path,
                        "extraction_timestamp": time.time()
                    })
                elif isinstance(match, str):
                    parameters.append({
                        "name": match.strip(),
                        "type": "string",
                        "description": "",
                        "endpoint_path": endpoint_path,
                        "extraction_timestamp": time.time()
                    })
        
        return parameters[:20]  # Limit to first 20 parameters
    
    def scrape_page_content(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape and analyze content from a single page.
        
        Args:
            page_data: Page data from crawler (includes URL and content)
            
        Returns:
            Scraped content analysis
        """
        url = page_data.get("url")
        page_content = page_data.get("page_content", {})
        content = page_content.get("content", "")
        
        self.logger.info(f"Scraping content from: {url}")
        
        # Check if already scraped
        scrape_check = self.check_if_page_scraped(url)
        if scrape_check.get("is_scraped", False):
            self.logger.info(f"Page already scraped: {url}")
            return {
                "url": url,
                "status": "already_scraped",
                "scrape_check": scrape_check
            }
        
        # Extract endpoints
        endpoints = self.extract_endpoints_from_content(content, url)
        
        # Extract parameters for each endpoint
        all_parameters = []
        for endpoint in endpoints:
            endpoint_params = self.extract_api_parameters(content, endpoint.get("path"))
            all_parameters.extend(endpoint_params)
        
        # Extract headings and structure
        headings = self._extract_headings(content)
        
        # Create content summary
        content_summary = {
            "url": url,
            "title": page_content.get("title", ""),
            "endpoints": endpoints,
            "parameters": all_parameters,
            "headings": headings,
            "content_length": len(content),
            "extraction_timestamp": time.time()
        }
        
        # Store in memory server
        memory_result = self.store_scraped_page_in_memory(url, content_summary)
        
        # Track locally
        self.scraped_pages.add(url)
        self.extracted_endpoints.extend(endpoints)
        
        return {
            "url": url,
            "status": "scraped",
            "content_summary": content_summary,
            "memory_storage": memory_result,
            "endpoints_found": len(endpoints),
            "parameters_found": len(all_parameters)
        }
    
    def _extract_headings(self, content: str) -> List[Dict[str, Any]]:
        """Extract headings from content.
        
        Args:
            content: Content to extract headings from
            
        Returns:
            List of headings with levels
        """
        headings = []
        
        # Markdown headings
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        matches = re.findall(heading_pattern, content, re.MULTILINE)
        
        for match in matches:
            level = len(match[0])
            text = match[1].strip()
            headings.append({
                "level": level,
                "text": text,
                "type": "markdown"
            })
        
        # HTML headings
        html_heading_pattern = r'<h([1-6])[^>]*>([^<]+)</h[1-6]>'
        html_matches = re.findall(html_heading_pattern, content, re.IGNORECASE)
        
        for match in html_matches:
            level = int(match[0])
            text = match[1].strip()
            headings.append({
                "level": level,
                "text": text,
                "type": "html"
            })
        
        return headings
    
    def get_scraping_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current scraping session.
        
        Returns:
            Scraping statistics
        """
        return {
            "pages_scraped": len(self.scraped_pages),
            "total_endpoints_extracted": len(self.extracted_endpoints),
            "endpoints_by_method": self._group_endpoints_by_method(),
            "unique_paths": len(set(ep.get("path") for ep in self.extracted_endpoints))
        }
    
    def _group_endpoints_by_method(self) -> Dict[str, int]:
        """Group extracted endpoints by HTTP method.
        
        Returns:
            Count of endpoints by method
        """
        method_counts = {}
        for endpoint in self.extracted_endpoints:
            method = endpoint.get("method", "UNKNOWN")
            method_counts[method] = method_counts.get(method, 0) + 1
        return method_counts
