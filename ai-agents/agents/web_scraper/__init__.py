"""
Web Scraper Agent Module

This module provides a modular web scraping solution for API documentation:
- WebScraperAgent: Main orchestrator agent
- WebCrawler: Handles link discovery and crawling
- ContentScraper: Handles content extraction and API endpoint discovery

Uses MCP servers for lightweight, Kubernetes-ready operation:
- mcp-server-fetch for web content retrieval
- mcp-server-memory for tracking scraped pages
"""

from .web_scraper import WebScraperAgent
from .web_crawler import WebCrawler
from .content_scraper import ContentScraper

__all__ = ['WebScraperAgent', 'WebCrawler', 'ContentScraper']
