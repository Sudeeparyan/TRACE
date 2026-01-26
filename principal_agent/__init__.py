"""
TRACE Principal Agent Package

This package contains the Principal (Self-Healing) Agent - the global orchestrator
for the TRACE system that monitors all Parent and Child agents.

IMPORTANT: JSON File Upload Handling
-------------------------------------
The adk_json_patch module is imported to fix JSON file upload errors.
This must be imported BEFORE the agent to patch ADK's Content handling.
"""

# Import patch FIRST to fix JSON file uploads
import sys
from pathlib import Path

# Add parent directory to path to import adk_json_patch
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    import adk_json_patch  # This patches ADK to handle JSON files
except ImportError:
    print("⚠️ Warning: adk_json_patch not found - JSON file uploads may fail")

# Now import the agent
from .agent import root_agent

__all__ = ["root_agent"]
