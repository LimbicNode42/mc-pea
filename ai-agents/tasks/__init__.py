"""
Tasks package for MC-PEA AI Agents

This package contains task definitions that use centralized configuration
from configs/tasks.yaml, following the same pattern as agent configuration.
"""

from .api_link_discovery_task import ApiLinkDiscoveryTask
from .api_content_extractor_task import ApiLinkContentExtractorTask

__all__ = [
    "ApiLinkDiscoveryTask",
    "ApiLinkContentExtractorTask",
]
