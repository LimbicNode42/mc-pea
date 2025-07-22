"""
Pydantic models for API Link Discovery output structures.

This module defines the data models used to structure output from the
ApiLinkDiscoveryTask so it can be properly consumed by the ApiLinkContentExtractorTask.
"""

from pydantic import BaseModel, Field
from typing import List, Optional

class ApiLinkDiscoveryPoint(BaseModel):
    title: str = Field(description="Title of page link that was discovered")
    link: str = Field(description="Link to a page discovered in the format of a URL")
    
    # Dynamic categorization support
    category_path: List[str] = Field(
        default_factory=list,
        description="Hierarchical category path, e.g. ['Actions', 'Artifacts'] or ['Users'] for single level"
    )
    depth_level: int = Field(
        default=1,
        description="Depth level where this link was discovered during crawling"
    )

class ApiLinkDiscoveryCategory(BaseModel):
    category_name: str = Field(description="Name of the category this link belongs to")
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
    links: List[ApiLinkDiscoveryPoint] = Field(
        default_factory=list, 
        description="List of discovered API links in this category"
    )
    
class ApiLinkDiscoveryOutput(BaseModel):
    categories: List[ApiLinkDiscoveryCategory] = Field(description="List of discovered API link categories")
    
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
                        "links": [],
                        "category_info": None
                    }
                current_level = current_level[path_segment]["subcategories"]
            
            # Set the category info and links at the final level
            final_category_name = category.category_path[-1] if category.category_path else category.category_name
            if final_category_name not in tree:
                current_level = tree
                for path_segment in category.category_path[:-1]:
                    current_level = current_level[path_segment]["subcategories"]
                current_level[final_category_name] = {
                    "subcategories": {},
                    "links": category.links,
                    "category_info": category
                }
        
        return tree
    
    def get_links_by_category_path(self, category_path: List[str]) -> List[ApiLinkDiscoveryPoint]:
        """
        Get all links for a specific category path.
        
        Args:
            category_path: List representing the hierarchical path, e.g. ['Actions', 'Artifacts']
            
        Returns:
            List of links in that category path
        """
        for category in self.categories:
            if category.category_path == category_path:
                return category.links
        return []