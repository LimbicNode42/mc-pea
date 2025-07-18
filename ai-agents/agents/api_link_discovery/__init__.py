"""
API Link Discovery Agent Module

This module provides specialized API link discovery and web crawling functionality:
- LinkDiscoveryAgent: Main agent for discovering and cataloging API-related web links
- WebCrawler: Core crawling engine with MCP server integration

Uses MCP servers for lightweight, Kubernetes-ready operation:
- mcp-server-fetch for web content retrieval
- mcp-server-memory for tracking discovered links and crawl state
"""

from .link_discovery_agent import LinkDiscoveryAgent
from .web_crawler import WebCrawler

__all__ = ['LinkDiscoveryAgent', 'WebCrawler']
