"""
Tasks package for MC-PEA AI Agents

This package contains task definitions that use centralized configuration
from configs/tasks.yaml, following the same pattern as agent configuration.
"""

from .information_gathering import (
    create_scrape_task,
    create_api_analysis_task,
    create_information_extraction_task,
    create_content_analysis_task,
    create_website_discovery_workflow
)

__all__ = [
    "create_scrape_task",
    "create_api_analysis_task", 
    "create_information_extraction_task",
    "create_content_analysis_task",
    "create_website_discovery_workflow"
]
