"""
Pydantic models for API Link Content Extractor output structures.

This module defines the data models used to structure output from the
ApiLinkContentExtractorTask, containing detailed API endpoint information
extracted from documentation pages with support for dynamic hierarchical categorization.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ApiParameter(BaseModel):
    name: str = Field(description="Name of the API parameter")
    description: str = Field(description="Description of the API parameter usage")
    required: bool = Field(default=False, description="Whether the parameter is required or optional")
    type: str = Field(description="Type of the parameter, e.g. string, integer, etc.")
    default_value: str = Field(
        default=None, 
        description="Default value of the parameter if applicable"
    )

class ApiLinkContentExtractorPoint(BaseModel):
    name: str = Field(description="Name of the API endpoint that briefly describes its usage")
    description: str = Field(description="Description of the API endpoint usage")

    method: str = Field(description="HTTP method used for the API endpoint, e.g. GET, POST")
    path: str = Field(description="Path of the API endpoint, e.g. /api/v1/resource")

    # Dynamic categorization support
    category_path: List[str] = Field(
        default_factory=list,
        description="Hierarchical category path, e.g. ['Actions', 'Artifacts'] or ['Users'] for single level"
    )
    source_url: Optional[str] = Field(
        default=None,
        description="URL from which this endpoint information was extracted"
    )

    headers: List[ApiParameter] = Field(default_factory=list, description="List of headers used in the API request")
    path_parameters: List[ApiParameter] = Field(default_factory=list, description="List of path parameters used in the API endpoint URL")
    query_parameters: List[ApiParameter] = Field(default_factory=list, description="List of query parameters used in the API request")
    body_parameters: List[ApiParameter] = Field(default_factory=list, description="List of body parameters used in the API request")

    response_codes: Dict[str, str] = Field(
        default_factory=dict, 
        description="Dictionary mapping response codes to their descriptions"
    )
    
    # response_schema: Dict[str, Any] = Field(
    #     default_factory=dict,
    #     description="JSON schema or example of the API response structure"
    # )

class ApiLinkContentExtractorCategory(BaseModel):
    name: str = Field(description="Name of the API category, e.g. User Management, Payments")
    description: str = Field(description="Description of the API category")
    endpoints: List[ApiLinkContentExtractorPoint] = Field(
        default_factory=list, 
        description="List of API endpoints within this category"
    )
    
class ApiLinkContentExtractorOutput(BaseModel):
    categories: List[ApiLinkContentExtractorCategory] = Field(description="List of API categories with their endpoints")