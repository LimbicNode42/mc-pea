"""
Pydantic models for API Link Discovery output structures.

This module defines the data models used to structure output from the
ApiLinkDiscoveryTask so it can be properly consumed by the ApiLinkContentExtractorTask.
"""

from pydantic import BaseModel, Field
from typing import List

class ApiLinkDiscoveryPoint(BaseModel):
    title: str = Field(description="Title of page link that was discovered")
    link: str = Field(description="Link to a page discovered in the format of a HTTP URL")

class ApiLinkDiscoveryCategory(BaseModel):
    category_name: str = Field(description="Name of the category this link belongs to")
    links: List[ApiLinkDiscoveryPoint] = Field(
        default_factory=list, 
        description="List of discovered links in this category"
    )
    
class ApiLinkDiscoveryOutput(BaseModel):
    categories: List[ApiLinkDiscoveryCategory] = Field(description="List of discovered link categories")