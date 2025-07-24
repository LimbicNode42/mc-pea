"""
Pydantic models for API Link Discovery output structures.

This module defines the data models used to structure output from the
ApiLinkDiscoveryTask so it can be properly consumed by the ApiLinkContentExtractorTask.
"""

from pydantic import BaseModel, Field
from typing import List

class ApiLinkDiscoveryPoint(BaseModel):
    t: str = Field(description="Short title")
    l: str = Field(description="Path or relative URL (e.g. /rest/actions/artifacts)")

class ApiLinkDiscoveryCategory(BaseModel):
    n: str = Field(description="Category name (max 15 chars)")
    ls: List[ApiLinkDiscoveryPoint] = Field(
        default_factory=list, 
        description="Links in this category"
    )
    
class ApiLinkDiscoveryOutput(BaseModel):
    cs: List[ApiLinkDiscoveryCategory] = Field(description="Categories")