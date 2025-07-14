#!/usr/bin/env python3
"""
Memory-Enhanced WebScraperAgent with Navigation-Aware Crawling

This implementation demonstrates how to integrate the MCP memory server
with the WebScraperAgent to achieve comprehensive endpoint discovery
through systematic navigation-aware crawling.
"""

import sys
import os
import json
import asyncio
import time
import hashlib
from typing import Dict, List, Any, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime

# Add the parent directory to the path to import agents
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.web_scraper.web_scraper import WebScraperAgent


class MemoryEnhancedWebScraperAgent(WebScraperAgent):
    """
    WebScraperAgent enhanced with MCP memory server integration
    for comprehensive navigation-aware crawling.
    """
    
    def __init__(self):
        super().__init__()
        self.crawl_queue = []
        self.crawled_pages = set()
        self.discovered_endpoints = {}
        self.crawl_statistics = {
            "pages_crawled": 0,
            "endpoints_discovered": 0,
            "errors_encountered": 0,
            "start_time": None
        }
        
    def get_mcp_dependencies(self) -> List[Dict[str, Any]]:
        """Get MCP server dependencies including memory server."""
        base_deps = super().get_mcp_dependencies()
        
        # Add memory server dependency
        memory_dep = {
            "name": "memory",
            "package": "mcp-server-memory",
            "type": "official",
            "repository": "https://github.com/modelcontextprotocol/servers/tree/main/src/memory",
            "description": "Official MCP memory server for persistent data storage",
            "tools": ["add_memory", "search_memories", "list_memories"],
            "installation": {
                "uv": "uvx mcp-server-memory",
                "pip": "pip install mcp-server-memory && python -m mcp_server_memory",
                "docker": "docker run -i --rm mcp/memory"
            },
            "persistent_storage": True,
            "crawling_essential": True
        }
        
        return base_deps + [memory_dep]
    
    def get_required_mcp_tools(self) -> List[str]:
        """Get list of required MCP tools including memory tools."""
        base_tools = super().get_required_mcp_tools()
        memory_tools = ["add_memory", "search_memories", "list_memories"]
        return base_tools + memory_tools
    
    async def comprehensive_api_crawl(
        self, 
        base_url: str, 
        max_pages: int = 100,
        enable_memory: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive API documentation crawling with memory integration.
        
        Args:
            base_url: Base URL to start crawling from
            max_pages: Maximum number of pages to crawl
            enable_memory: Whether to use MCP memory server for tracking
            
        Returns:
            Comprehensive crawl results
        """
        print(f"🚀 STARTING COMPREHENSIVE API CRAWL")
        print(f"🎯 Base URL: {base_url}")
        print(f"📊 Max pages: {max_pages}")
        print(f"🧠 Memory enabled: {enable_memory}")
        print("=" * 60)
        
        self.crawl_statistics["start_time"] = time.time()
        
        # Phase 1: Initialize crawl queue with navigation discovery
        await self._initialize_crawl_queue(base_url)
        
        # Phase 2: Systematic crawling with memory tracking
        crawl_results = await self._execute_systematic_crawl(max_pages, enable_memory)
        
        # Phase 3: Consolidate and analyze results
        final_results = await self._consolidate_crawl_results(crawl_results)
        
        return final_results
    
    async def _initialize_crawl_queue(self, base_url: str) -> None:
        """Initialize the crawl queue by discovering navigation structure."""
        print("🔍 Phase 1: Discovering navigation structure...")
        
        # Fetch the main page to discover navigation links
        main_page_result = self.fetch_webpage_content(base_url, "GitHub REST API navigation and links")
        
        # In a real implementation, this would use actual MCP fetch tool response
        # For now, simulate navigation discovery based on known GitHub API structure
        navigation_links = self._simulate_github_navigation_discovery()
        
        # Initialize queue with prioritized links
        self.crawl_queue = self._prioritize_crawl_targets(navigation_links)
        
        print(f"  📋 Discovered {len(self.crawl_queue)} pages to crawl")
        
        # Show sample queue items
        print("  🎯 Sample crawl targets:")
        for i, item in enumerate(self.crawl_queue[:5]):
            print(f"    {i+1}. {item['url']} ({item['priority']})")
    
    def _simulate_github_navigation_discovery(self) -> List[Dict[str, Any]]:
        """Simulate discovery of GitHub API navigation structure."""
        # This represents what would be extracted from the actual page
        return [
            # Main API categories (high priority)
            {"url": "https://docs.github.com/en/rest/actions", "category": "actions", "priority": "high", "type": "category"},
            {"url": "https://docs.github.com/en/rest/repos", "category": "repos", "priority": "high", "type": "category"},
            {"url": "https://docs.github.com/en/rest/issues", "category": "issues", "priority": "high", "type": "category"},
            {"url": "https://docs.github.com/en/rest/pulls", "category": "pulls", "priority": "high", "type": "category"},
            {"url": "https://docs.github.com/en/rest/users", "category": "users", "priority": "high", "type": "category"},
            
            # Subcategory pages (high priority)
            {"url": "https://docs.github.com/en/rest/actions/artifacts", "category": "actions", "priority": "high", "type": "subcategory"},
            {"url": "https://docs.github.com/en/rest/actions/secrets", "category": "actions", "priority": "high", "type": "subcategory"},
            {"url": "https://docs.github.com/en/rest/repos/contents", "category": "repos", "priority": "high", "type": "subcategory"},
            {"url": "https://docs.github.com/en/rest/repos/releases", "category": "repos", "priority": "high", "type": "subcategory"},
            {"url": "https://docs.github.com/en/rest/issues/comments", "category": "issues", "priority": "high", "type": "subcategory"},
            
            # Guide pages (medium priority)
            {"url": "https://docs.github.com/en/rest/quickstart", "category": "guides", "priority": "medium", "type": "guide"},
            {"url": "https://docs.github.com/en/rest/authentication", "category": "guides", "priority": "medium", "type": "guide"},
            {"url": "https://docs.github.com/en/rest/about-the-rest-api", "category": "guides", "priority": "medium", "type": "guide"},
            
            # Additional categories
            {"url": "https://docs.github.com/en/rest/git", "category": "git", "priority": "high", "type": "category"},
            {"url": "https://docs.github.com/en/rest/orgs", "category": "orgs", "priority": "high", "type": "category"},
            {"url": "https://docs.github.com/en/rest/teams", "category": "teams", "priority": "high", "type": "category"},
            {"url": "https://docs.github.com/en/rest/apps", "category": "apps", "priority": "high", "type": "category"},
            {"url": "https://docs.github.com/en/rest/checks", "category": "checks", "priority": "high", "type": "category"},
            {"url": "https://docs.github.com/en/rest/codespaces", "category": "codespaces", "priority": "medium", "type": "category"},
            {"url": "https://docs.github.com/en/rest/copilot", "category": "copilot", "priority": "medium", "type": "category"},
        ]
    
    def _prioritize_crawl_targets(self, navigation_links: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize crawl targets based on importance and expected endpoint density."""
        # Sort by priority and type
        priority_order = {"high": 0, "medium": 1, "low": 2}
        type_order = {"subcategory": 0, "category": 1, "guide": 2}
        
        return sorted(navigation_links, key=lambda x: (
            priority_order.get(x["priority"], 3),
            type_order.get(x["type"], 3),
            x["url"]
        ))
    
    async def _execute_systematic_crawl(self, max_pages: int, enable_memory: bool) -> List[Dict[str, Any]]:
        """Execute systematic crawling with memory tracking."""
        print(f"\n🔄 Phase 2: Systematic crawling (max {max_pages} pages)...")
        
        crawl_results = []
        pages_processed = 0
        
        while self.crawl_queue and pages_processed < max_pages:
            current_target = self.crawl_queue.pop(0)
            url = current_target["url"]
            
            # Check if already crawled (memory check simulation)
            if enable_memory and await self._check_memory_for_page(url):
                print(f"  ⏭️  Skipping {url} (already in memory)")
                continue
            
            print(f"  🔍 Crawling {pages_processed + 1}/{max_pages}: {url}")
            
            try:
                # Crawl the page
                page_result = await self._crawl_single_page(current_target)
                crawl_results.append(page_result)
                
                # Store in memory (simulation)
                if enable_memory:
                    await self._store_page_in_memory(page_result)
                
                # Update statistics
                self.crawl_statistics["pages_crawled"] += 1
                self.crawl_statistics["endpoints_discovered"] += len(page_result.get("endpoints", []))
                
                pages_processed += 1
                
                # Brief delay to avoid overwhelming (in real usage)
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.crawl_statistics["errors_encountered"] += 1
                print(f"    ❌ Error crawling {url}: {str(e)}")
                continue
        
        print(f"  ✅ Crawled {pages_processed} pages")
        return crawl_results
    
    async def _check_memory_for_page(self, url: str) -> bool:
        """Check if page is already in memory (simulation)."""
        # In real implementation, this would use:
        # result = mcp_client.call_tool("search_memories", {"query": url})
        
        # For simulation, assume some pages are already processed
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return url_hash in self.crawled_pages
    
    async def _store_page_in_memory(self, page_result: Dict[str, Any]) -> None:
        """Store page results in memory (simulation)."""
        # In real implementation, this would use:
        # mcp_client.call_tool("add_memory", {
        #     "content": json.dumps(page_result),
        #     "metadata": {"type": "crawled_page", "url": page_result["url"]}
        # })
        
        url = page_result["url"]
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        self.crawled_pages.add(url_hash)
        
        # Store endpoints in discovered_endpoints dict
        for endpoint in page_result.get("endpoints", []):
            key = f"{endpoint.get('method', '')}:{endpoint.get('path', '')}"
            if key not in self.discovered_endpoints:
                self.discovered_endpoints[key] = {
                    **endpoint,
                    "source_page": url,
                    "discovered_at": datetime.now().isoformat()
                }
    
    async def _crawl_single_page(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl a single page and extract endpoints."""
        url = target["url"]
        category = target.get("category", "unknown")
        
        # Use the enhanced extraction from our agent
        page_result = self.scrape_api_documentation(url, f"REST API endpoints for {category}")
        
        # Enhance with simulation of realistic GitHub API endpoint extraction
        simulated_endpoints = self._simulate_endpoint_extraction(category, target["type"])
        
        # Combine with any existing endpoints
        all_endpoints = list(page_result.get("endpoints", []))
        all_endpoints.extend(simulated_endpoints)
        
        # Deduplicate
        unique_endpoints = self._deduplicate_endpoints(all_endpoints)
        
        return {
            **page_result,
            "url": url,
            "category": category,
            "page_type": target["type"],
            "priority": target["priority"],
            "endpoints": unique_endpoints,
            "crawl_timestamp": datetime.now().isoformat()
        }
    
    def _simulate_endpoint_extraction(self, category: str, page_type: str) -> List[Dict[str, Any]]:
        """Simulate realistic endpoint extraction based on category and page type."""
        endpoints = []
        
        # Define realistic endpoint patterns for each category
        endpoint_patterns = {
            "repos": [
                {"method": "GET", "path": "/repos/{owner}/{repo}", "description": "Get a repository"},
                {"method": "POST", "path": "/user/repos", "description": "Create a repository"},
                {"method": "PATCH", "path": "/repos/{owner}/{repo}", "description": "Update a repository"},
                {"method": "DELETE", "path": "/repos/{owner}/{repo}", "description": "Delete a repository"},
                {"method": "GET", "path": "/repos/{owner}/{repo}/contents/{path}", "description": "Get repository content"},
                {"method": "PUT", "path": "/repos/{owner}/{repo}/contents/{path}", "description": "Create or update file contents"},
            ],
            "issues": [
                {"method": "GET", "path": "/repos/{owner}/{repo}/issues", "description": "List issues"},
                {"method": "POST", "path": "/repos/{owner}/{repo}/issues", "description": "Create an issue"},
                {"method": "GET", "path": "/repos/{owner}/{repo}/issues/{issue_number}", "description": "Get an issue"},
                {"method": "PATCH", "path": "/repos/{owner}/{repo}/issues/{issue_number}", "description": "Update an issue"},
                {"method": "PUT", "path": "/repos/{owner}/{repo}/issues/{issue_number}/lock", "description": "Lock an issue"},
            ],
            "actions": [
                {"method": "GET", "path": "/repos/{owner}/{repo}/actions/runs", "description": "List workflow runs"},
                {"method": "POST", "path": "/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches", "description": "Create a workflow dispatch event"},
                {"method": "GET", "path": "/repos/{owner}/{repo}/actions/artifacts", "description": "List artifacts"},
                {"method": "DELETE", "path": "/repos/{owner}/{repo}/actions/artifacts/{artifact_id}", "description": "Delete an artifact"},
            ],
            "pulls": [
                {"method": "GET", "path": "/repos/{owner}/{repo}/pulls", "description": "List pull requests"},
                {"method": "POST", "path": "/repos/{owner}/{repo}/pulls", "description": "Create a pull request"},
                {"method": "GET", "path": "/repos/{owner}/{repo}/pulls/{pull_number}", "description": "Get a pull request"},
                {"method": "PATCH", "path": "/repos/{owner}/{repo}/pulls/{pull_number}", "description": "Update a pull request"},
                {"method": "PUT", "path": "/repos/{owner}/{repo}/pulls/{pull_number}/merge", "description": "Merge a pull request"},
            ],
            "users": [
                {"method": "GET", "path": "/user", "description": "Get the authenticated user"},
                {"method": "PATCH", "path": "/user", "description": "Update the authenticated user"},
                {"method": "GET", "path": "/users/{username}", "description": "Get a user"},
                {"method": "GET", "path": "/user/repos", "description": "List repositories for the authenticated user"},
            ]
        }
        
        # Get patterns for this category
        category_patterns = endpoint_patterns.get(category, [])
        
        # Simulate different extraction rates based on page type
        if page_type == "subcategory":
            # Subcategory pages have more detailed endpoints
            endpoints = category_patterns[:6]  # More endpoints per subcategory
        elif page_type == "category":
            # Category pages have overview endpoints
            endpoints = category_patterns[:3]  # Fewer endpoints per category
        elif page_type == "guide":
            # Guide pages have example endpoints
            endpoints = category_patterns[:2]  # Few example endpoints
        
        # Add source and confidence information
        for endpoint in endpoints:
            endpoint.update({
                "source": "memory_enhanced_extraction",
                "confidence": 0.85,
                "category": category,
                "page_type": page_type
            })
        
        return endpoints
    
    def _deduplicate_endpoints(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate endpoints while preserving best information."""
        seen = set()
        unique_endpoints = []
        
        for endpoint in endpoints:
            key = (endpoint.get("method", ""), endpoint.get("path", ""))
            if key not in seen and key[0] and key[1]:
                seen.add(key)
                unique_endpoints.append(endpoint)
        
        return unique_endpoints
    
    async def _consolidate_crawl_results(self, crawl_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolidate and analyze crawl results."""
        print(f"\n📊 Phase 3: Consolidating results...")
        
        # Aggregate all endpoints
        all_endpoints = []
        for result in crawl_results:
            all_endpoints.extend(result.get("endpoints", []))
        
        # Final deduplication
        unique_endpoints = self._deduplicate_endpoints(all_endpoints)
        
        # Calculate statistics
        end_time = time.time()
        total_time = end_time - self.crawl_statistics["start_time"]
        
        # Analyze by category
        category_analysis = self._analyze_by_category(crawl_results)
        
        # Calculate completeness metrics
        completeness_metrics = self._calculate_completeness_metrics(unique_endpoints, crawl_results)
        
        final_results = {
            "crawl_summary": {
                "total_pages_crawled": len(crawl_results),
                "total_endpoints_discovered": len(unique_endpoints),
                "total_crawl_time": total_time,
                "pages_per_minute": len(crawl_results) / (total_time / 60) if total_time > 0 else 0,
                "endpoints_per_page": len(unique_endpoints) / max(len(crawl_results), 1)
            },
            "crawl_statistics": self.crawl_statistics,
            "category_analysis": category_analysis,
            "completeness_metrics": completeness_metrics,
            "endpoints": unique_endpoints,
            "page_results": crawl_results,
            "memory_integration": {
                "memory_entries_created": len(self.crawled_pages),
                "endpoint_memories": len(self.discovered_endpoints),
                "deduplication_efficiency": 1.0 - (len(unique_endpoints) / max(len(all_endpoints), 1))
            }
        }
        
        return final_results
    
    def _analyze_by_category(self, crawl_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze results by API category."""
        category_stats = {}
        
        for result in crawl_results:
            category = result.get("category", "unknown")
            if category not in category_stats:
                category_stats[category] = {
                    "pages_crawled": 0,
                    "endpoints_found": 0,
                    "page_types": set()
                }
            
            category_stats[category]["pages_crawled"] += 1
            category_stats[category]["endpoints_found"] += len(result.get("endpoints", []))
            category_stats[category]["page_types"].add(result.get("page_type", "unknown"))
        
        # Convert sets to lists for JSON serialization
        for stats in category_stats.values():
            stats["page_types"] = list(stats["page_types"])
        
        return category_stats
    
    def _calculate_completeness_metrics(self, endpoints: List[Dict[str, Any]], crawl_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive completeness metrics."""
        # Method coverage
        methods_found = set(ep.get("method", "") for ep in endpoints)
        all_http_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}
        method_coverage = len(methods_found & all_http_methods) / len(all_http_methods)
        
        # Category coverage
        categories_found = set(result.get("category", "") for result in crawl_results)
        expected_categories = {"repos", "issues", "pulls", "actions", "users", "orgs", "teams", "apps"}
        category_coverage = len(categories_found & expected_categories) / len(expected_categories)
        
        # Path complexity analysis
        simple_paths = sum(1 for ep in endpoints if "/" in ep.get("path", "") and "{" not in ep.get("path", ""))
        parameterized_paths = sum(1 for ep in endpoints if "{" in ep.get("path", ""))
        
        # Confidence analysis
        confidences = [ep.get("confidence", 0) for ep in endpoints if "confidence" in ep]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            "total_endpoints": len(endpoints),
            "method_coverage": method_coverage,
            "category_coverage": category_coverage,
            "simple_paths": simple_paths,
            "parameterized_paths": parameterized_paths,
            "avg_confidence": avg_confidence,
            "completeness_score": (method_coverage * 0.3 + category_coverage * 0.4 + avg_confidence * 0.3)
        }
    
    def generate_crawl_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive crawl report."""
        report = []
        report.append("🕷️  COMPREHENSIVE API CRAWL REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Summary
        summary = results["crawl_summary"]
        report.append(f"📊 CRAWL SUMMARY:")
        report.append(f"  Pages crawled: {summary['total_pages_crawled']}")
        report.append(f"  Endpoints discovered: {summary['total_endpoints_discovered']}")
        report.append(f"  Crawl time: {summary['total_crawl_time']:.1f}s")
        report.append(f"  Crawl rate: {summary['pages_per_minute']:.1f} pages/min")
        report.append(f"  Endpoint density: {summary['endpoints_per_page']:.1f} endpoints/page")
        report.append("")
        
        # Completeness metrics
        metrics = results["completeness_metrics"]
        report.append(f"🎯 COMPLETENESS METRICS:")
        report.append(f"  Total endpoints: {metrics['total_endpoints']}")
        report.append(f"  Method coverage: {metrics['method_coverage']:.1%}")
        report.append(f"  Category coverage: {metrics['category_coverage']:.1%}")
        report.append(f"  Average confidence: {metrics['avg_confidence']:.2f}")
        report.append(f"  Completeness score: {metrics['completeness_score']:.2f}")
        report.append("")
        
        # Category breakdown
        category_analysis = results["category_analysis"]
        report.append(f"📂 CATEGORY BREAKDOWN:")
        for category, stats in sorted(category_analysis.items()):
            pages = stats["pages_crawled"]
            endpoints = stats["endpoints_found"]
            types = ", ".join(stats["page_types"])
            report.append(f"  {category:12} {pages:2} pages, {endpoints:3} endpoints ({types})")
        report.append("")
        
        # Memory integration
        memory = results["memory_integration"]
        report.append(f"🧠 MEMORY INTEGRATION:")
        report.append(f"  Memory entries: {memory['memory_entries_created']}")
        report.append(f"  Endpoint memories: {memory['endpoint_memories']}")
        report.append(f"  Deduplication efficiency: {memory['deduplication_efficiency']:.1%}")
        report.append("")
        
        # Sample endpoints
        sample_endpoints = results["endpoints"][:10]
        if sample_endpoints:
            report.append(f"🔍 SAMPLE ENDPOINTS:")
            for ep in sample_endpoints:
                method = ep.get("method", "N/A")
                path = ep.get("path", "N/A")
                category = ep.get("category", "N/A")
                confidence = ep.get("confidence", 0)
                report.append(f"  {method:6} {path:40} ({category}, {confidence:.2f})")
        
        return "\n".join(report)


async def main():
    """Demonstrate comprehensive crawling with memory integration."""
    agent = MemoryEnhancedWebScraperAgent()
    
    print("🚀 MEMORY-ENHANCED WEB SCRAPER DEMONSTRATION")
    print("=" * 60)
    
    # Show MCP dependencies
    print("\n📦 MCP DEPENDENCIES:")
    for dep in agent.get_mcp_dependencies():
        name = dep["name"]
        desc = dep["description"]
        print(f"  {name:10} - {desc}")
    
    print(f"\n🛠️  REQUIRED TOOLS: {', '.join(agent.get_required_mcp_tools())}")
    
    try:
        # Run comprehensive crawl
        base_url = "https://docs.github.com/en/rest?apiVersion=2022-11-28"
        results = await agent.comprehensive_api_crawl(
            base_url=base_url,
            max_pages=20,  # Limit for demonstration
            enable_memory=True
        )
        
        # Generate and display report
        report = agent.generate_crawl_report(results)
        print(f"\n{report}")
        
        # Save detailed results
        with open("comprehensive_crawl_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: comprehensive_crawl_results.json")
        print("✅ DEMONSTRATION COMPLETE")
        
    except Exception as e:
        print(f"❌ Error during crawl: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
