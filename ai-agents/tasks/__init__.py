"""
Tasks package for MC-PEA AI Agents

This package contains task definitions that use centralized configuration
from configs/tasks.yaml, following the same pattern as agent configuration.
"""

from .link_discovery_task import ApiLinkDiscoveryTask
from .link_content_extractor_task import ApiLinkContentExtractorTask
from .orchestrated_link_content_extractor_task import OrchestratedApiLinkContentExtractorTask

__all__ = [
    "ApiLinkDiscoveryTask",
    "ApiLinkContentExtractorTask",
    "OrchestratedApiLinkContentExtractorTask"
]
