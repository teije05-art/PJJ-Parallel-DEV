"""
Workflow Coordinator Module

Single Responsibility: Call agents in sequence and combine results

This module handles agent coordination:
- Calls Planner -> Verifier -> Executor -> Generator in sequence
- Combines results from all agents
- NO knowledge of memory storage, approval, or learning

No dependencies on: Memory storage, approval workflow, learning
"""

import os
import sys
from typing import Dict
from pathlib import Path

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from .agentflow_agents import AgentCoordinator, AgentResult


class WorkflowCoordinator:
    """Coordinates the 4-agent workflow"""

    def __init__(self, agent: Agent, memory_path: Path):
        """
        Initialize workflow coordinator

        Args:
            agent: The memagent instance (shared across all modules)
            memory_path: Path to memory directory
        """
        self.agent = agent
        self.memory_path = memory_path

        # Initialize the agent coordinator (manages the 4 agents)
        self.agent_coordinator = AgentCoordinator(agent, memory_path)

    def run_workflow(self, goal: str, context: Dict) -> Dict[str, AgentResult]:
        """
        Main entry point - runs the 4-agent workflow

        Args:
            goal: The planning goal
            context: Context from ContextManager

        Returns:
            Dictionary with results from all 4 agents:
            - planner: Strategic plan
            - verifier: Plan validation
            - executor: Implementation results
            - generator: Final synthesis
        """
        print("\n🎯 WORKFLOW COORDINATOR: Running 4-agent workflow...")

        # Call the agent coordinator (which handles the actual agent workflow)
        results = self.agent_coordinator.coordinate_agentic_workflow(goal, context)

        print("\n✅ WORKFLOW COORDINATOR: All agents completed")

        return results
