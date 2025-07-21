"""
Pydantic models for API Link Discovery output structures.

This module defines the data models used to structure output from the
ApiLinkDiscoveryTask so it can be properly consumed by the ApiLinkContentExtractorTask.
"""

from pydantic import BaseModel, HttpUrl, Field

class ApiLinkDiscoveryOutput(BaseModel):
    """
    Complete output structure from the API Link Discovery task.
    
    This model structures the results from web crawling API documentation
    sites, organizing discovered links by category and providing metadata
    about the crawling process.
    """
    title: str = Field(
        default="About artifacts in GitHub Actions",
        description="Title of page link that was discovered"
    )
    
    link: HttpUrl = Field(
        default="https://docs.github.com/en/rest/actions/artifacts?apiVersion=2022-11-28#about-artifacts-in-github-actions",
        description="Link to a page discovered in the format of a URL"
    )