"""
Agents Module - Specialized agent implementations

This module provides specialized agents:

Core 4-Agent Workflow:
- PlannerAgent: Strategic planning
- VerifierAgent: Quality validation
- ExecutorAgent: Implementation
- GeneratorAgent: Content synthesis

Human-In-The-Loop Approval Agents:
- ProposalAgent: Pre-planning analysis with user selection constraints
- CheckpointAgent: Iteration synthesis with user selection constraints

All agents are coordinated through AgentCoordinator.
"""

from .base_agent import BaseAgent, AgentResult
from .planner_agent import PlannerAgent
from .verifier_agent import VerifierAgent
from .executor_agent import ExecutorAgent
from .generator_agent import GeneratorAgent
from .proposal_agent import ProposalAgent
from .checkpoint_agent import CheckpointAgent
from .agent_factory import AgentCoordinator

__all__ = [
    'BaseAgent',
    'AgentResult',
    'PlannerAgent',
    'VerifierAgent',
    'ExecutorAgent',
    'GeneratorAgent',
    'ProposalAgent',
    'CheckpointAgent',
    'AgentCoordinator',
]
