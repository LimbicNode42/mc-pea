"""
Pydantic models for API Link Discovery output structures.

This module defines the data models used to structure output from the
ApiLinkDiscoveryTask so it can be properly consumed by the ApiLinkContentExtractorTask.
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import List

class ApiLinkDiscoveryPoint(BaseModel):
    title: str = Field(description="Title of page link that was discovered")
    link: HttpUrl = Field(description="Link to a page discovered in the format of a URL")
    
class ApiLinkDiscoveryOutput(BaseModel):
    links: List[ApiLinkDiscoveryPoint] = Field(description="List of discovered API links")