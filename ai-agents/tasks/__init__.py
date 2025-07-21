"""
Tasks package for MC-PEA AI Agents

This package contains task definitions that use centralized configuration
from configs/tasks.yaml, following the same pattern as agent configuration.
"""

from .information_gathering import ApiLinkDiscoveryTask
from .information_gathering import ApiLinkContentExtractorTask

__all__ = [
    "ApiLinkDiscoveryTask",
    "ApiLinkContentExtractorTask"
]
