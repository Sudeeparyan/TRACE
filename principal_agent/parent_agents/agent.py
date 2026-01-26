"""
TRACE Parent Agents entrypoint for ADK Web.

This module exposes the parent-level root agent so the ADK runtime can
locate it via `parent_agents.agent.root_agent`.
"""

from .regional_coordinator.agent import regional_coordinator

# ADK expects a `root_agent` symbol at parent_agents.agent.
root_agent = regional_coordinator
