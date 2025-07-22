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
    
    # Dynamic categorization support
    category_path: List[str] = Field(
        default_factory=list,
        description="Full hierarchical path to this category, e.g. ['Actions', 'Artifacts']"
    )
    parent_category: Optional[str] = Field(
        default=None,
        description="Parent category name if this is a subcategory"
    )
    level: int = Field(
        default=1,
        description="Nesting level of this category (1 = top level, 2 = subcategory, etc.)"
    )
    
    endpoints: List[ApiLinkContentExtractorPoint] = Field(
        default_factory=list, 
        description="List of API endpoints within this category"
    )
    
class ApiLinkContentExtractorOutput(BaseModel):
    categories: List[ApiLinkContentExtractorCategory] = Field(description="List of API categories with their endpoints")
    
    def get_category_tree(self) -> dict:
        """
        Get categories organized as a nested tree structure.
        
        Returns:
            Nested dictionary representing the category hierarchy
        """
        tree = {}
        
        for category in self.categories:
            current_level = tree
            
            # Navigate through the category path
            for path_segment in category.category_path:
                if path_segment not in current_level:
                    current_level[path_segment] = {
                        "subcategories": {},
                        "endpoints": [],
                        "category_info": None
                    }
                current_level = current_level[path_segment]["subcategories"]
            
            # Set the category info and endpoints at the final level
            final_category_name = category.category_path[-1] if category.category_path else category.name
            if final_category_name not in tree:
                current_level = tree
                for path_segment in category.category_path[:-1]:
                    current_level = current_level[path_segment]["subcategories"]
                current_level[final_category_name] = {
                    "subcategories": {},
                    "endpoints": category.endpoints,
                    "category_info": category
                }
        
        return tree
    
    def get_endpoints_by_category_path(self, category_path: List[str]) -> List[ApiLinkContentExtractorPoint]:
        """
        Get all endpoints for a specific category path.
        
        Args:
            category_path: List representing the hierarchical path, e.g. ['Actions', 'Artifacts']
            
        Returns:
            List of endpoints in that category path
        """
        for category in self.categories:
            if category.category_path == category_path:
                return category.endpoints
        return []
    
    def get_all_endpoints_flat(self) -> List[ApiLinkContentExtractorPoint]:
        """
        Get all endpoints in a flat list regardless of categorization.
        
        Returns:
            Flat list of all endpoints
        """
        all_endpoints = []
        for category in self.categories:
            all_endpoints.extend(category.endpoints)
        return all_endpoints
    
    def get_categories_by_level(self, level: int) -> List[ApiLinkContentExtractorCategory]:
        """
        Get all categories at a specific nesting level.
        
        Args:
            level: The nesting level (1 = top level, 2 = subcategory, etc.)
            
        Returns:
            List of categories at that level
        """
        return [category for category in self.categories if category.level == level]