"""
Models package for MC-PEA AI Agents.

This package contains Pydantic models for structuring data flow between
different AI agent tasks and ensuring consistent data formats.
"""

from .link_discovery_output import ApiLinkDiscoveryOutput

__all__ = [
    "ApiLinkDiscoveryOutput"
]
