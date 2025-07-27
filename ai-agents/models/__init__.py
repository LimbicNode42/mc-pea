"""
Models package for MC-PEA AI Agents.

This package contains Pydantic models for structuring data flow between
different AI agent tasks and ensuring consistent data formats.
"""

from .api_discovery_output import ApiLinkDiscoveryOutput
from .api_content_extractor_output import ApiLinkContentExtractorOutput

__all__ = [
    "ApiLinkDiscoveryOutput",
    "ApiLinkContentExtractorOutput",
]
