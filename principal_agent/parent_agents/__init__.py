"""
Parent Agents package exposing the regional coordinator entrypoint.

Importing the local ``agent`` module here makes it available as
``parent_agents.agent`` which is what ADK expects when it loads the app.
"""

from . import agent as agent

root_agent = agent.root_agent

__all__ = ["agent", "root_agent"]
