"""
Web Crawler Module for discovering and collecting links up to configured depth.

This module handles the crawling aspect of web scraping, discovering all reachable links
within the specified depth using the MCP fetch_webpage server.
"""

from typing import Dict, Any, List, Set, Optional
import logging
import time
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque
import re


class WebCrawler:
    """Handles web crawling and link discovery using MCP fetch server."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger, mcp_client=None):
        """Initialize the web crawler.
        
        Args:
            config: Crawling configuration
            logger: Logger instance
            mcp_client: MCP client for fetch operations
        """
        self.config = config
        self.logger = logger
        self.mcp_client = mcp_client
        
        # Crawling parameters from config
        self.crawl_depth = config.get("crawl_depth", 2)
        self.max_depth = config.get("max_depth", 5)
        self.min_depth = config.get("min_depth", 1)
        self.follow_external_links = config.get("follow_external_links", False)
        self.respect_robots_txt = config.get("respect_robots_txt", True)
        self.max_pages_per_domain = config.get("max_pages_per_domain", 100)
        self.request_delay_seconds = config.get("request_delay_seconds", 1.0)
        
        # State tracking
        self.visited_urls: Set[str] = set()
        self.domain_page_counts: Dict[str, int] = {}
        self.crawl_results: List[Dict[str, Any]] = []
        
    def normalize_url(self, url: str) -> str:
        """Normalize URL for consistent comparison.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        """
        parsed = urlparse(url)
        # Remove fragment and normalize
        normalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip('/') if parsed.path != '/' else '/',
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))
        return normalized
    
    def is_valid_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is valid for crawling.
        
        Args:
            url: URL to validate
            base_domain: Base domain for the crawl
            
        Returns:
            True if URL is valid for crawling
        """
        try:
            parsed = urlparse(url)
            
            # Must have valid scheme
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check domain restrictions
            url_domain = parsed.netloc.lower()
            if not self.follow_external_links and url_domain != base_domain:
                return False
            
            # Check domain page limits
            if url_domain in self.domain_page_counts:
                if self.domain_page_counts[url_domain] >= self.max_pages_per_domain:
                    return False
            
            # Skip common non-content file types
            path_lower = parsed.path.lower()
            skip_extensions = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.zip', '.tar', '.gz', '.rar', '.7z',
                '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp',
                '.mp3', '.mp4', '.avi', '.mov', '.wmv',
                '.css', '.js', '.ico', '.xml', '.rss'
            ]
            
            if any(path_lower.endswith(ext) for ext in skip_extensions):
                return False
            
            # Skip URLs with certain query parameters that indicate dynamic content
            skip_query_patterns = [
                'download=', 'action=download', 'format=pdf',
                'print=1', 'export=', 'logout', 'login'
            ]
            
            if parsed.query:
                query_lower = parsed.query.lower()
                if any(pattern in query_lower for pattern in skip_query_patterns):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Error validating URL {url}: {e}")
            return False
    
    def extract_links_from_page(self, page_content: Dict[str, Any], base_url: str) -> List[str]:
        """Extract links from a page's content.
        
        Args:
            page_content: Page content from MCP fetch server
            base_url: Base URL for resolving relative links
            
        Returns:
            List of absolute URLs found on the page
        """
        links = []
        
        # Get links from MCP fetch server result if available
        if 'links' in page_content and isinstance(page_content['links'], list):
            for link in page_content['links']:
                if isinstance(link, dict):
                    # Handle both 'href' and 'url' formats
                    href = link.get('href') or link.get('url')
                    if href:
                        # Convert relative to absolute URL
                        absolute_url = urljoin(base_url, href)
                        normalized_url = self.normalize_url(absolute_url)
                        links.append(normalized_url)
                elif isinstance(link, str):
                    # Convert relative to absolute URL
                    absolute_url = urljoin(base_url, link)
                    normalized_url = self.normalize_url(absolute_url)
                    links.append(normalized_url)
        
        # Also extract links from content using regex as fallback
        content = page_content.get('content', '')
        if content:
            # Find href attributes in HTML
            href_pattern = r'href\s*=\s*["\']([^"\']+)["\']'
            href_matches = re.findall(href_pattern, content, re.IGNORECASE)
            
            for href in href_matches:
                absolute_url = urljoin(base_url, href)
                normalized_url = self.normalize_url(absolute_url)
                links.append(normalized_url)
            
            # Find markdown links
            markdown_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            markdown_matches = re.findall(markdown_pattern, content)
            
            for _, href in markdown_matches:
                absolute_url = urljoin(base_url, href)
                normalized_url = self.normalize_url(absolute_url)
                links.append(normalized_url)
        
        return list(set(links))  # Remove duplicates
    
    def fetch_page_via_mcp(self, url: str, query: str = None) -> Dict[str, Any]:
        """Fetch a page using MCP fetch_webpage tool.
        
        Args:
            url: URL to fetch
            query: Optional query for focused content extraction
            
        Returns:
            Page content and metadata
        """
        try:
            self.logger.info(f"Fetching page via MCP: {url}")
            
            # Use the actual MCP client to fetch the webpage
            if self.mcp_client:
                params = {"url": url}
                if query:
                    params["query"] = query
                
                result = self.mcp_client.call_tool("fetch_webpage", params)
                
                if result.get("status") == "success":
                    # Track domain page count
                    domain = urlparse(url).netloc.lower()
                    self.domain_page_counts[domain] = self.domain_page_counts.get(domain, 0) + 1
                    
                    # Add metadata
                    result["timestamp"] = time.time()
                    result["domain"] = domain
                    result["query_used"] = query
                    
                    return result
                else:
                    self.logger.error(f"MCP fetch failed for {url}: {result.get('error', 'Unknown error')}")
                    return {
                        "url": url,
                        "status": "error",
                        "error": result.get("error", "MCP fetch failed"),
                        "timestamp": time.time()
                    }
            else:
                # Fallback if no MCP client available
                self.logger.warning("No MCP client available, using fallback")
                return {
                    "url": url,
                    "title": f"Content from {url}",
                    "text": f"No MCP client available to fetch content from {url}",
                    "links": [],
                    "headings": [],
                    "status": "error",
                    "error": "No MCP client available",
                    "timestamp": time.time()
                }
                
        except Exception as e:
            self.logger.error(f"Error fetching page {url}: {e}")
            return {
                "url": url,
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
            self.domain_page_counts[domain] = self.domain_page_counts.get(domain, 0) + 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching page {url}: {e}")
            return {
                "url": url,
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def crawl_website(self, start_url: str, query: str = None) -> Dict[str, Any]:
        """Crawl a website starting from the given URL.
        
        Args:
            start_url: Starting URL for the crawl
            query: Optional query to guide content extraction
            
        Returns:
            Crawling results with discovered pages and links
        """
        self.logger.info(f"Starting website crawl from: {start_url}")
        self.logger.info(f"Crawl depth: {self.crawl_depth}, Max pages per domain: {self.max_pages_per_domain}")
        
        # Initialize crawl state
        start_url_normalized = self.normalize_url(start_url)
        base_domain = urlparse(start_url_normalized).netloc.lower()
        
        # Queue for BFS crawling: (url, depth)
        crawl_queue = deque([(start_url_normalized, 0)])
        crawl_results = []
        discovered_links = set()
        
        # Reset state
        self.visited_urls.clear()
        self.domain_page_counts.clear()
        
        while crawl_queue and len(crawl_results) < self.max_pages_per_domain:
            current_url, current_depth = crawl_queue.popleft()
            
            # Skip if already visited
            if current_url in self.visited_urls:
                continue
            
            # Skip if depth exceeded
            if current_depth > self.crawl_depth:
                continue
            
            # Skip if URL is not valid for crawling
            if not self.is_valid_url(current_url, base_domain):
                continue
            
            # Mark as visited
            self.visited_urls.add(current_url)
            
            # Fetch the page
            page_content = self.fetch_page_via_mcp(current_url, query)
            
            # Add to results
            crawl_result = {
                "url": current_url,
                "depth": current_depth,
                "page_content": page_content,
                "crawl_timestamp": time.time()
            }
            crawl_results.append(crawl_result)
            
            # Extract links for next level crawling
            if current_depth < self.crawl_depth and page_content.get("status") != "error":
                page_links = self.extract_links_from_page(page_content, current_url)
                
                for link in page_links:
                    if link not in self.visited_urls and link not in discovered_links:
                        if self.is_valid_url(link, base_domain):
                            crawl_queue.append((link, current_depth + 1))
                            discovered_links.add(link)
            
            # Respect request delay
            if self.request_delay_seconds > 0:
                time.sleep(self.request_delay_seconds)
        
        return {
            "start_url": start_url,
            "base_domain": base_domain,
            "crawl_depth": self.crawl_depth,
            "pages_crawled": len(crawl_results),
            "links_discovered": len(discovered_links),
            "crawl_results": crawl_results,
            "discovered_links": list(discovered_links),
            "domain_page_counts": dict(self.domain_page_counts),
            "status": "completed",
            "timestamp": time.time()
        }
    
    def get_crawl_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current crawl session.
        
        Returns:
            Crawl statistics
        """
        return {
            "total_pages_visited": len(self.visited_urls),
            "pages_per_domain": dict(self.domain_page_counts),
            "crawl_depth": self.crawl_depth,
            "max_pages_per_domain": self.max_pages_per_domain,
            "follow_external_links": self.follow_external_links,
            "request_delay_seconds": self.request_delay_seconds
        }
