"""
TRACE Principal Agent Package

This package contains the Principal (Self-Healing) Agent - the global orchestrator
for the TRACE system that monitors all Parent and Child agents.
"""

from .agent import root_agent

__all__ = ["root_agent"]
