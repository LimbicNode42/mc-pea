"""
Content Scraper Module for extracting API endpoints and parameters from web pages.

This module handles the content extraction and analysis aspect of web scraping,
focusing on extracting API endpoints, parameters, and documentation structure
from the pages discovered by the web crawler.

Uses Claude AI for intelligent endpoint extraction instead of static regex patterns.
"""

from typing import Dict, Any, List, Optional, Set
import logging
import re
import json
import time
from urllib.parse import urlparse, urljoin
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ContentScraper:
    """Handles content extraction and API endpoint discovery."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger, mcp_client=None):
        """Initialize the content scraper.
        
        Args:
            config: Scraping configuration
            logger: Logger instance
            mcp_client: MCP client for fetch operations (optional, may not need it)
        """
        self.config = config
        self.logger = logger
        self.mcp_client = mcp_client
        
        # Track scraped pages using MCP memory server
        self.scraped_pages: Set[str] = set()
        self.extracted_endpoints: List[Dict[str, Any]] = []
        
        # Initialize Anthropic client for intelligent endpoint extraction
        try:
            from core.anthropic_client import AnthropicClient
            self.anthropic_client = AnthropicClient(logger)
            self.use_claude_extraction = True
            self.logger.info("✅ Anthropic Claude client initialized for intelligent endpoint extraction")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Anthropic client: {e}")
            self.logger.error("� No fallback methods allowed - AI-first approach required")
            raise RuntimeError(f"Anthropic client is mandatory for AI-first approach: {e}")
        
        # NO FALLBACK PATTERNS - AI-first approach only
        
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
        """Extract API endpoints from content using Claude AI for intelligent analysis.
        
        Args:
            content: Content to extract endpoints from
            source_url: URL where content was found (for context)
            
        Returns:
            List of extracted endpoints with metadata
        """
        self.logger.info(f"🔍 Extracting endpoints from content using Claude AI analysis")
        
        # ONLY use Claude for endpoint extraction - no fallbacks
        if not self.anthropic_client:
            self.logger.error("❌ Anthropic client not available - cannot extract endpoints")
            raise RuntimeError("Anthropic client is required for endpoint extraction - no fallback methods allowed")
        
        if not self.use_claude_extraction:
            self.logger.error("❌ Claude extraction is disabled - cannot extract endpoints")
            raise RuntimeError("Claude extraction must be enabled - no fallback methods allowed")
        
        # Use Claude for intelligent endpoint extraction
        try:
            self.logger.info("🤖 Analyzing content with Claude for API endpoints...")
            claude_result = self.anthropic_client.analyze_content_for_endpoints(content, source_url)
            
            endpoints = claude_result.get("endpoints", [])
            
            # Add additional metadata to each endpoint
            for endpoint in endpoints:
                endpoint.update({
                    "source": "claude_ai_analysis",
                    "source_url": source_url,
                    "extraction_timestamp": time.time(),
                    "extraction_method": "claude_intelligent_analysis"
                })
            
            self.logger.info(f"✅ Claude extracted {len(endpoints)} endpoints")
            
            # Log analysis metadata
            metadata = claude_result.get("analysis_metadata", {})
            confidence = metadata.get("confidence_score", 0.0)
            content_type = metadata.get("content_type", "unknown")
            
            self.logger.info(f"📊 Analysis confidence: {confidence:.2f}, Content type: {content_type}")
            
            return endpoints
            
        except Exception as e:
            self.logger.error(f"❌ Claude endpoint extraction failed: {e}")
            # NO FALLBACK - raise the error to ensure only Claude is used
            raise RuntimeError(f"Claude endpoint extraction failed and no fallback allowed: {e}")
    
    def extract_api_parameters(self, content: str, endpoint_path: str = None) -> List[Dict[str, Any]]:
        """Extract API parameters from content using Claude AI for intelligent analysis.
        
        Args:
            content: Content to extract parameters from
            endpoint_path: Specific endpoint path to focus on
            
        Returns:
            List of extracted parameters
        """
        self.logger.info(f"🔍 Extracting API parameters using Claude AI analysis")
        
        # ONLY use Claude for parameter extraction - no fallbacks
        if not self.anthropic_client:
            self.logger.error("❌ Anthropic client not available - cannot extract parameters")
            raise RuntimeError("Anthropic client is required for parameter extraction - no fallback methods allowed")
        
        # Use Claude for intelligent parameter extraction
        try:
            self.logger.info("🤖 Analyzing content with Claude for API parameters...")
            claude_result = self.anthropic_client.analyze_content_for_parameters(content, endpoint_path)
            
            parameters = claude_result.get("parameters", [])
            
            # Add additional metadata to each parameter
            for parameter in parameters:
                parameter.update({
                    "source": "claude_ai_analysis",
                    "endpoint_path": endpoint_path,
                    "extraction_timestamp": time.time(),
                    "extraction_method": "claude_intelligent_analysis"
                })
            
            self.logger.info(f"✅ Claude extracted {len(parameters)} parameters")
            
            return parameters
            
        except Exception as e:
            self.logger.error(f"❌ Claude parameter extraction failed: {e}")
            # NO FALLBACK - raise the error to ensure only Claude is used
            raise RuntimeError(f"Claude parameter extraction failed and no fallback allowed: {e}")
    
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
    
    def cleanup(self):
        """Clean up resources, including Anthropic client if needed."""
        try:
            if hasattr(self, 'anthropic_client') and self.anthropic_client:
                # Close Anthropic client if it has cleanup methods
                if hasattr(self.anthropic_client, 'close'):
                    self.anthropic_client.close()
                self.anthropic_client = None
            
            self.logger.info("🧹 ContentScraper cleanup completed")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error during ContentScraper cleanup: {e}")
