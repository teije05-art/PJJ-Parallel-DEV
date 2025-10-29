"""
Base Agent - Common functionality for all specialized agents

This module provides the foundation for all agent types in the system.
All agents inherit from BaseAgent to ensure consistent behavior and logging.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent


@dataclass
class AgentResult:
    """Standard result format for all agent operations"""
    success: bool
    output: str
    metadata: Dict[str, Any]
    timestamp: str


class BaseAgent:
    """Base class for all specialized agents

    Provides common functionality:
    - Logging and coordination tracking
    - Standard result wrapping
    - Memory access
    """

    def __init__(self, agent: Agent, memory_path: Path):
        """
        Initialize base agent

        Args:
            agent: The MemAgent instance
            memory_path: Path to memory directory
        """
        self.agent = agent
        self.memory_path = memory_path
        self.agent_type = self.__class__.__name__

    def _log_agent_action(self, action: str, result: AgentResult):
        """Log agent actions to MemAgent for coordination tracking

        Args:
            action: Description of the action performed
            result: AgentResult from the action
        """
        log_entry = f"""
## {self.agent_type} Action - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Action:** {action}
**Success:** {result.success}
**Output:** {result.output[:200]}...
**Metadata:** {result.metadata}

---
"""

        # Store in agent coordination log
        coordination_file = self.memory_path / "entities" / "agent_coordination.md"
        try:
            if coordination_file.exists():
                with open(coordination_file, 'a') as f:
                    f.write(log_entry)
            else:
                coordination_file.write_text(f"# Agent Coordination Log\n\n{log_entry}")
        except Exception as e:
            print(f"   ⚠️ Failed to log agent action: {e}")

    def _wrap_result(self, success: bool, output: str, metadata: Dict[str, Any]) -> AgentResult:
        """Wrap agent output in standard AgentResult format

        Args:
            success: Whether operation succeeded
            output: Agent output text
            metadata: Additional metadata about the operation

        Returns:
            AgentResult with standard format
        """
        return AgentResult(
            success=success,
            output=output,
            metadata=metadata,
            timestamp=datetime.now().isoformat()
        )

    def _handle_error(self, action: str, error: Exception) -> AgentResult:
        """Handle errors consistently across all agents

        Args:
            action: Name of the action that failed
            error: The exception that was raised

        Returns:
            AgentResult indicating failure with error details
        """
        import traceback
        error_details = traceback.format_exc()
        error_msg = f"{action} failed: {str(error)}\n\nDetails:\n{error_details}"

        error_result = AgentResult(
            success=False,
            output=error_msg,
            metadata={
                "error": str(error),
                "error_type": type(error).__name__,
                "full_traceback": error_details
            },
            timestamp=datetime.now().isoformat()
        )

        self._log_agent_action(action, error_result)
        return error_result
