"""
Crews package for MC-PEA AI Agents

This package contains crew definitions that use centralized configuration
and coordinate multiple agents and tasks.
"""

from .orchestrated_data_entry import OrchestratedDataEntryCrew

__all__ = [
    "OrchestratedDataEntryCrew"
]