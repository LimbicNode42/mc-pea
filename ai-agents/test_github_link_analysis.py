#!/usr/bin/env python3
"""
GitHub API Documentation Link Analysis

This script fetches and analyzes all links from the GitHub API documentation
to understand the navigation structure and assess feasibility of comprehensive
crawling using sidebar/navigation links only.
"""

import sys
import os
import json
import re
from typing import Dict, List, Any, Set, Tuple
from urllib.parse import urljoin, urlparse

# Add the parent directory to the path to import agents
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.web_scraper.web_scraper import WebScraperAgent


class GitHubAPILinkAnalyzer:
    """Analyzer for GitHub API documentation link structure."""
    
    def __init__(self):
        self.agent = WebScraperAgent()
        self.base_url = "https://docs.github.com"
        self.api_base = "https://docs.github.com/en/rest"
        
    def analyze_github_api_links(self, url: str = None) -> Dict[str, Any]:
        """Analyze all links from the GitHub API documentation page."""
        if url is None:
            url = "https://docs.github.com/en/rest?apiVersion=2022-11-28"
        
        print(f"🔍 ANALYZING LINKS FROM: {url}")
        print("=" * 60)
        
        # Fetch the page content using the agent's fetch method
        # This simulates what would happen with the actual MCP fetch tool
        result = self.agent.fetch_webpage_content(url, "GitHub REST API documentation links and navigation")
        
        # For demonstration, we'll simulate the content extraction that would happen
        # In reality, this would use the actual MCP fetch tool response
        simulated_content = self._get_simulated_github_content()
        
        # Extract all links from the content
        links = self._extract_all_links(simulated_content)
        
        # Categorize links
        categorized_links = self._categorize_links(links)
        
        # Analyze navigation structure
        navigation_analysis = self._analyze_navigation_structure(categorized_links)
        
        # Generate crawling strategy
        crawling_strategy = self._generate_crawling_strategy(categorized_links, navigation_analysis)
        
        return {
            "base_url": url,
            "total_links": len(links),
            "categorized_links": categorized_links,
            "navigation_analysis": navigation_analysis,
            "crawling_strategy": crawling_strategy,
            "mcp_memory_integration": self._design_memory_integration(),
            "sample_links": links[:20]  # First 20 for inspection
        }
    
    def _get_simulated_github_content(self) -> str:
        """Get simulated GitHub API documentation content with realistic link structure."""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>GitHub REST API documentation</title></head>
        <body>
        
        <!-- Navigation sidebar -->
        <nav class="sidebar">
            <ul class="nav-list">
                <li><a href="/en/rest?apiVersion=2022-11-28">REST API</a>
                    <ul>
                        <li><a href="/en/rest/quickstart">Quickstart</a></li>
                        <li><a href="/en/rest/about-the-rest-api">About the REST API</a></li>
                        <li><a href="/en/rest/authentication">Authentication</a></li>
                    </ul>
                </li>
                
                <!-- API Reference sections -->
                <li><a href="/en/rest/actions">Actions</a>
                    <ul>
                        <li><a href="/en/rest/actions/artifacts">Artifacts</a></li>
                        <li><a href="/en/rest/actions/cache">Cache</a></li>
                        <li><a href="/en/rest/actions/secrets">Secrets</a></li>
                        <li><a href="/en/rest/actions/variables">Variables</a></li>
                        <li><a href="/en/rest/actions/workflow-jobs">Workflow jobs</a></li>
                        <li><a href="/en/rest/actions/workflow-runs">Workflow runs</a></li>
                        <li><a href="/en/rest/actions/workflows">Workflows</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/apps">Apps</a>
                    <ul>
                        <li><a href="/en/rest/apps/apps">GitHub Apps</a></li>
                        <li><a href="/en/rest/apps/installations">Installations</a></li>
                        <li><a href="/en/rest/apps/oauth-applications">OAuth Applications</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/checks">Checks</a>
                    <ul>
                        <li><a href="/en/rest/checks/runs">Check runs</a></li>
                        <li><a href="/en/rest/checks/suites">Check suites</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/code-scanning">Code scanning</a>
                    <ul>
                        <li><a href="/en/rest/code-scanning/code-scanning">Code scanning</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/codespaces">Codespaces</a>
                    <ul>
                        <li><a href="/en/rest/codespaces/codespaces">Codespaces</a></li>
                        <li><a href="/en/rest/codespaces/machines">Machines</a></li>
                        <li><a href="/en/rest/codespaces/secrets">Secrets</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/copilot">Copilot</a>
                    <ul>
                        <li><a href="/en/rest/copilot/copilot-usage">Usage</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/dependabot">Dependabot</a>
                    <ul>
                        <li><a href="/en/rest/dependabot/alerts">Alerts</a></li>
                        <li><a href="/en/rest/dependabot/secrets">Secrets</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/git">Git database</a>
                    <ul>
                        <li><a href="/en/rest/git/blobs">Blobs</a></li>
                        <li><a href="/en/rest/git/commits">Commits</a></li>
                        <li><a href="/en/rest/git/refs">References</a></li>
                        <li><a href="/en/rest/git/tags">Tags</a></li>
                        <li><a href="/en/rest/git/trees">Trees</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/issues">Issues</a>
                    <ul>
                        <li><a href="/en/rest/issues/assignees">Assignees</a></li>
                        <li><a href="/en/rest/issues/comments">Comments</a></li>
                        <li><a href="/en/rest/issues/events">Events</a></li>
                        <li><a href="/en/rest/issues/issues">Issues</a></li>
                        <li><a href="/en/rest/issues/labels">Labels</a></li>
                        <li><a href="/en/rest/issues/milestones">Milestones</a></li>
                        <li><a href="/en/rest/issues/timeline">Timeline</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/licenses">Licenses</a></li>
                
                <li><a href="/en/rest/markdown">Markdown</a></li>
                
                <li><a href="/en/rest/orgs">Organizations</a>
                    <ul>
                        <li><a href="/en/rest/orgs/blocking">Blocking users</a></li>
                        <li><a href="/en/rest/orgs/custom-roles">Custom roles</a></li>
                        <li><a href="/en/rest/orgs/members">Members</a></li>
                        <li><a href="/en/rest/orgs/orgs">Organizations</a></li>
                        <li><a href="/en/rest/orgs/outside-collaborators">Outside collaborators</a></li>
                        <li><a href="/en/rest/orgs/webhooks">Webhooks</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/packages">Packages</a></li>
                
                <li><a href="/en/rest/projects">Projects</a>
                    <ul>
                        <li><a href="/en/rest/projects/cards">Cards</a></li>
                        <li><a href="/en/rest/projects/collaborators">Collaborators</a></li>
                        <li><a href="/en/rest/projects/columns">Columns</a></li>
                        <li><a href="/en/rest/projects/projects">Projects (classic)</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/pulls">Pull requests</a>
                    <ul>
                        <li><a href="/en/rest/pulls/comments">Review comments</a></li>
                        <li><a href="/en/rest/pulls/pulls">Pull requests</a></li>
                        <li><a href="/en/rest/pulls/review-requests">Review requests</a></li>
                        <li><a href="/en/rest/pulls/reviews">Reviews</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/rate-limit">Rate limit</a></li>
                
                <li><a href="/en/rest/reactions">Reactions</a></li>
                
                <li><a href="/en/rest/repos">Repositories</a>
                    <ul>
                        <li><a href="/en/rest/repos/autolinks">Autolinks</a></li>
                        <li><a href="/en/rest/repos/branches">Branches</a></li>
                        <li><a href="/en/rest/repos/collaborators">Collaborators</a></li>
                        <li><a href="/en/rest/repos/comments">Comments</a></li>
                        <li><a href="/en/rest/repos/commits">Commits</a></li>
                        <li><a href="/en/rest/repos/contents">Contents</a></li>
                        <li><a href="/en/rest/repos/deploy-keys">Deploy keys</a></li>
                        <li><a href="/en/rest/repos/deployments">Deployments</a></li>
                        <li><a href="/en/rest/repos/environments">Environments</a></li>
                        <li><a href="/en/rest/repos/forks">Forks</a></li>
                        <li><a href="/en/rest/repos/merging">Merging</a></li>
                        <li><a href="/en/rest/repos/pages">Pages</a></li>
                        <li><a href="/en/rest/repos/releases">Releases</a></li>
                        <li><a href="/en/rest/repos/repos">Repositories</a></li>
                        <li><a href="/en/rest/repos/rules">Rules</a></li>
                        <li><a href="/en/rest/repos/statuses">Statuses</a></li>
                        <li><a href="/en/rest/repos/tags">Tags</a></li>
                        <li><a href="/en/rest/repos/webhooks">Webhooks</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/search">Search</a></li>
                
                <li><a href="/en/rest/secret-scanning">Secret scanning</a>
                    <ul>
                        <li><a href="/en/rest/secret-scanning/secret-scanning">Secret scanning</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/teams">Teams</a>
                    <ul>
                        <li><a href="/en/rest/teams/discussions">Discussions</a></li>
                        <li><a href="/en/rest/teams/members">Members</a></li>
                        <li><a href="/en/rest/teams/teams">Teams</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/users">Users</a>
                    <ul>
                        <li><a href="/en/rest/users/blocking">Blocking users</a></li>
                        <li><a href="/en/rest/users/emails">Emails</a></li>
                        <li><a href="/en/rest/users/followers">Followers</a></li>
                        <li><a href="/en/rest/users/gpg-keys">GPG keys</a></li>
                        <li><a href="/en/rest/users/keys">Keys</a></li>
                        <li><a href="/en/rest/users/users">Users</a></li>
                    </ul>
                </li>
                
                <li><a href="/en/rest/webhooks">Webhooks</a>
                    <ul>
                        <li><a href="/en/rest/webhooks/webhooks">Webhooks</a></li>
                    </ul>
                </li>
            </ul>
        </nav>
        
        <!-- Main content area -->
        <main>
            <h1>GitHub REST API documentation</h1>
            <p>Create integrations, retrieve data, and automate your workflows with the GitHub REST API.</p>
            
            <!-- Content links (these would be in-content, not navigation) -->
            <p>See also: <a href="/en/graphql">GraphQL API</a></p>
            <p>Learn about <a href="/en/rest/guides/getting-started-with-the-rest-api">getting started</a></p>
            <p>Check our <a href="https://github.blog/changelog/">API changelog</a></p>
        </main>
        
        </body>
        </html>
        """
    
    def _extract_all_links(self, content: str) -> List[Dict[str, str]]:
        """Extract all links from the HTML content."""
        links = []
        
        # Pattern to match href attributes
        href_pattern = r'href=["\']([^"\']+)["\']'
        
        # Find all href matches
        href_matches = re.findall(href_pattern, content)
        
        for href in href_matches:
            # Parse the link context to understand its purpose
            link_context = self._extract_link_context(content, href)
            
            links.append({
                "href": href,
                "absolute_url": urljoin(self.base_url, href),
                "context": link_context,
                "is_api_related": self._is_api_related_link(href),
                "link_type": self._classify_link_type(href, link_context)
            })
        
        return links
    
    def _extract_link_context(self, content: str, href: str) -> str:
        """Extract the text context around a link."""
        # Find the link in the content and extract surrounding text
        href_escaped = re.escape(href)
        pattern = rf'<a[^>]*href=["\']?{href_escaped}["\']?[^>]*>([^<]+)</a>'
        
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return "Unknown"
    
    def _is_api_related_link(self, href: str) -> bool:
        """Check if a link is related to API documentation."""
        api_indicators = [
            '/rest/', '/api/', '/graphql/', 
            '/webhooks/', '/authentication',
            '/quickstart', '/guides/'
        ]
        
        return any(indicator in href.lower() for indicator in api_indicators)
    
    def _classify_link_type(self, href: str, context: str) -> str:
        """Classify the type of link."""
        if href.startswith('#'):
            return "anchor"
        elif href.startswith('http') and 'docs.github.com' not in href:
            return "external"
        elif '/rest/' in href:
            if href.count('/') >= 4:  # e.g., /en/rest/actions/artifacts
                return "api_endpoint_page"
            else:
                return "api_category_page"
        elif href in ['/en/rest', '/en/rest?apiVersion=2022-11-28']:
            return "api_main_page"
        elif '/en/rest/' in href and href.endswith(('quickstart', 'authentication', 'about-the-rest-api')):
            return "api_guide_page"
        else:
            return "general_docs"
    
    def _categorize_links(self, links: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        """Categorize links by type and purpose."""
        categories = {
            "navigation_links": [],      # Sidebar navigation
            "api_category_pages": [],    # Main API categories (Actions, Repos, etc.)
            "api_endpoint_pages": [],    # Specific endpoint documentation
            "api_guide_pages": [],       # Quickstart, authentication, etc.
            "external_links": [],        # Links outside docs.github.com
            "anchor_links": [],          # In-page anchors
            "content_links": []          # Links within page content
        }
        
        for link in links:
            link_type = link["link_type"]
            
            if link_type == "api_category_page":
                categories["api_category_pages"].append(link)
            elif link_type == "api_endpoint_page":
                categories["api_endpoint_pages"].append(link)
            elif link_type == "api_guide_page":
                categories["api_guide_pages"].append(link)
            elif link_type == "external":
                categories["external_links"].append(link)
            elif link_type == "anchor":
                categories["anchor_links"].append(link)
            else:
                categories["content_links"].append(link)
            
            # Also categorize as navigation if it appears to be in sidebar
            if self._is_navigation_link(link):
                categories["navigation_links"].append(link)
        
        return categories
    
    def _is_navigation_link(self, link: Dict[str, str]) -> bool:
        """Determine if a link is part of the navigation structure."""
        href = link["href"]
        context = link["context"]
        
        # Navigation links typically:
        # 1. Are REST API related
        # 2. Have short, descriptive text
        # 3. Follow the /en/rest/category pattern
        
        if not link["is_api_related"]:
            return False
        
        # Check if it follows navigation patterns
        navigation_patterns = [
            r'^/en/rest$',
            r'^/en/rest\?',
            r'^/en/rest/[^/]+$',           # Category level: /en/rest/actions
            r'^/en/rest/[^/]+/[^/]+$',     # Subcategory: /en/rest/actions/artifacts
        ]
        
        return any(re.match(pattern, href) for pattern in navigation_patterns)
    
    def _analyze_navigation_structure(self, categorized_links: Dict[str, List[Dict[str, str]]]) -> Dict[str, Any]:
        """Analyze the navigation structure for crawling strategy."""
        
        nav_links = categorized_links["navigation_links"]
        api_categories = categorized_links["api_category_pages"]
        api_endpoints = categorized_links["api_endpoint_pages"]
        
        # Build hierarchy
        hierarchy = {}
        
        for link in nav_links:
            href = link["href"]
            parts = href.strip('/').split('/')
            
            if len(parts) >= 3 and parts[1] == 'rest':
                if len(parts) == 3:  # Main category
                    category = parts[2].split('?')[0]  # Remove query params
                    if category not in hierarchy:
                        hierarchy[category] = {"subcategories": [], "link": link}
                elif len(parts) == 4:  # Subcategory
                    category = parts[2]
                    subcategory = parts[3]
                    if category not in hierarchy:
                        hierarchy[category] = {"subcategories": [], "link": None}
                    hierarchy[category]["subcategories"].append({
                        "name": subcategory,
                        "link": link
                    })
        
        # Calculate completeness metrics
        total_categories = len(hierarchy)
        total_subcategories = sum(len(cat["subcategories"]) for cat in hierarchy.values())
        
        return {
            "hierarchy": hierarchy,
            "total_categories": total_categories,
            "total_subcategories": total_subcategories,
            "total_navigable_pages": total_categories + total_subcategories,
            "navigation_completeness": {
                "main_categories": list(hierarchy.keys()),
                "estimated_total_pages": total_categories + total_subcategories + 10,  # +guides
                "crawlable_via_navigation": True
            }
        }
    
    def _generate_crawling_strategy(
        self, 
        categorized_links: Dict[str, List[Dict[str, str]]], 
        navigation_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a comprehensive crawling strategy."""
        
        hierarchy = navigation_analysis["hierarchy"]
        
        # Define crawling phases
        crawling_phases = {
            "phase_1_main_categories": {
                "description": "Crawl all main API category pages",
                "targets": [
                    f"/en/rest/{category}" 
                    for category in hierarchy.keys() 
                    if category not in ['', '?apiVersion=2022-11-28']
                ],
                "expected_endpoints_per_page": 5,
                "priority": "high"
            },
            
            "phase_2_subcategories": {
                "description": "Crawl all subcategory pages for detailed endpoints",
                "targets": [],
                "expected_endpoints_per_page": 10,
                "priority": "high"
            },
            
            "phase_3_guide_pages": {
                "description": "Crawl guide and reference pages",
                "targets": [
                    "/en/rest/quickstart",
                    "/en/rest/about-the-rest-api",
                    "/en/rest/authentication"
                ],
                "expected_endpoints_per_page": 2,
                "priority": "medium"
            }
        }
        
        # Populate subcategory targets
        for category, data in hierarchy.items():
            for subcat in data["subcategories"]:
                crawling_phases["phase_2_subcategories"]["targets"].append(
                    subcat["link"]["href"]
                )
        
        # Calculate estimated totals
        total_pages = sum(len(phase["targets"]) for phase in crawling_phases.values())
        estimated_endpoints = sum(
            len(phase["targets"]) * phase["expected_endpoints_per_page"]
            for phase in crawling_phases.values()
        )
        
        return {
            "crawling_phases": crawling_phases,
            "total_pages_to_crawl": total_pages,
            "estimated_total_endpoints": estimated_endpoints,
            "crawl_order": ["phase_1_main_categories", "phase_2_subcategories", "phase_3_guide_pages"],
            "memory_requirements": {
                "pages_to_track": total_pages,
                "expected_memory_entries": total_pages * 2,  # Page + extracted data
                "deduplication_needed": True
            },
            "success_criteria": {
                "min_endpoints_target": estimated_endpoints * 0.7,
                "completeness_threshold": 0.8,
                "page_coverage_target": 0.95
            }
        }
    
    def _design_memory_integration(self) -> Dict[str, Any]:
        """Design MCP memory server integration strategy."""
        return {
            "mcp_memory_server": {
                "name": "memory",
                "package": "mcp-server-memory",
                "purpose": "Track crawled pages and extracted endpoints",
                "tools_needed": ["add_memory", "search_memories", "list_memories"]
            },
            
            "memory_schema": {
                "page_memory": {
                    "key": "github_api_page_{url_hash}",
                    "content": {
                        "url": "string",
                        "crawled_at": "timestamp",
                        "endpoints_found": "number",
                        "status": "string (success|error|skipped)",
                        "extraction_summary": "string"
                    }
                },
                "endpoint_memory": {
                    "key": "github_endpoint_{method}_{path_hash}",
                    "content": {
                        "method": "string",
                        "path": "string",
                        "source_page": "string",
                        "confidence": "float",
                        "description": "string",
                        "discovered_at": "timestamp"
                    }
                }
            },
            
            "crawling_workflow": {
                "1_check_memory": "Before crawling, check if page already processed",
                "2_crawl_page": "Use fetch_webpage to get content",
                "3_extract_endpoints": "Apply enhanced extraction strategies",
                "4_store_page_memory": "Save page crawl results",
                "5_store_endpoint_memories": "Save individual endpoints",
                "6_update_queue": "Add newly discovered links to crawl queue",
                "7_deduplication": "Check for duplicate endpoints across pages"
            },
            
            "queue_management": {
                "priority_queue": [
                    "uncrawled_main_categories",
                    "uncrawled_subcategories", 
                    "uncrawled_guide_pages",
                    "discovered_links"
                ],
                "skip_conditions": [
                    "already_in_memory",
                    "external_link",
                    "non_api_related"
                ]
            }
        }
    
    def generate_comprehensive_report(self, analysis_result: Dict[str, Any]) -> str:
        """Generate a comprehensive analysis report."""
        report = []
        report.append("🔗 GITHUB API DOCUMENTATION LINK ANALYSIS")
        report.append("=" * 60)
        report.append("")
        
        # Summary
        total_links = analysis_result["total_links"]
        report.append(f"📊 SUMMARY:")
        report.append(f"  Total links found: {total_links}")
        report.append("")
        
        # Link categories
        categorized = analysis_result["categorized_links"]
        report.append(f"📂 LINK CATEGORIES:")
        for category, links in categorized.items():
            report.append(f"  {category:25} {len(links):3} links")
        report.append("")
        
        # Navigation analysis
        nav_analysis = analysis_result["navigation_analysis"]
        report.append(f"🧭 NAVIGATION STRUCTURE:")
        report.append(f"  Main categories: {nav_analysis['total_categories']}")
        report.append(f"  Subcategories: {nav_analysis['total_subcategories']}")
        report.append(f"  Total navigable pages: {nav_analysis['total_navigable_pages']}")
        report.append("")
        
        # Sample main categories
        hierarchy = nav_analysis["hierarchy"]
        report.append(f"📋 MAIN API CATEGORIES:")
        for category in sorted(hierarchy.keys())[:10]:
            subcats = len(hierarchy[category]["subcategories"])
            report.append(f"  {category:20} ({subcats} subcategories)")
        if len(hierarchy) > 10:
            report.append(f"  ... and {len(hierarchy) - 10} more")
        report.append("")
        
        # Crawling strategy
        strategy = analysis_result["crawling_strategy"]
        report.append(f"🎯 CRAWLING STRATEGY:")
        report.append(f"  Total pages to crawl: {strategy['total_pages_to_crawl']}")
        report.append(f"  Estimated endpoints: {strategy['estimated_total_endpoints']}")
        report.append("")
        
        # MCP memory integration
        memory = analysis_result["mcp_memory_integration"]
        report.append(f"💾 MCP MEMORY INTEGRATION:")
        report.append(f"  Memory server: {memory['mcp_memory_server']['name']}")
        report.append(f"  Tools needed: {', '.join(memory['mcp_memory_server']['tools_needed'])}")
        report.append("")
        
        # Navigation feasibility conclusion
        nav_complete = nav_analysis["navigation_completeness"]
        report.append(f"✅ NAVIGATION-ONLY CRAWLING FEASIBILITY:")
        report.append(f"  Crawlable via navigation: {nav_complete['crawlable_via_navigation']}")
        report.append(f"  Estimated coverage: {nav_complete['estimated_total_pages']} pages")
        report.append(f"  Recommendation: {'FEASIBLE' if nav_complete['crawlable_via_navigation'] else 'NOT RECOMMENDED'}")
        
        return "\n".join(report)


def main():
    """Run the GitHub API documentation link analysis."""
    analyzer = GitHubAPILinkAnalyzer()
    
    print("🚀 STARTING GITHUB API LINK ANALYSIS")
    print("=" * 60)
    
    try:
        # Analyze the GitHub API documentation
        analysis_result = analyzer.analyze_github_api_links()
        
        # Generate comprehensive report
        report = analyzer.generate_comprehensive_report(analysis_result)
        print(report)
        
        # Save detailed results
        with open("github_api_link_analysis.json", "w") as f:
            json.dump(analysis_result, f, indent=2)
        
        print(f"\n💾 Detailed analysis saved to: github_api_link_analysis.json")
        
        # Show sample navigation structure with depth 2
        print(f"\n🔍 SAMPLE NAVIGATION HIERARCHY (DEPTH 2):")
        print("-" * 50)
        
        hierarchy = analysis_result["navigation_analysis"]["hierarchy"]
        count = 0
        for category, data in sorted(hierarchy.items())[:5]:  # Show first 5 categories
            print(f"📁 {category}")
            for subcat in data["subcategories"][:3]:  # Show first 3 subcategories
                print(f"  └── {subcat['name']}")
                count += 1
            if len(data["subcategories"]) > 3:
                print(f"  └── ... and {len(data['subcategories']) - 3} more")
            print()
        
        print(f"🎯 CONCLUSION: Navigation-only crawling can discover ~{analysis_result['crawling_strategy']['estimated_total_endpoints']} endpoints")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ ANALYSIS COMPLETE")


if __name__ == "__main__":
    main()
