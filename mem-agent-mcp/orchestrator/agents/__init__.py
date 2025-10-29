"""
Agents Module - Specialized agent implementations

This module provides 4 specialized agents:
- PlannerAgent: Strategic planning
- VerifierAgent: Quality validation
- ExecutorAgent: Implementation
- GeneratorAgent: Content synthesis

All agents are coordinated through AgentCoordinator.
"""

from .base_agent import BaseAgent, AgentResult
from .planner_agent import PlannerAgent
from .verifier_agent import VerifierAgent
from .executor_agent import ExecutorAgent
from .generator_agent import GeneratorAgent
from .agent_factory import AgentCoordinator

__all__ = [
    'BaseAgent',
    'AgentResult',
    'PlannerAgent',
    'VerifierAgent',
    'ExecutorAgent',
    'GeneratorAgent',
    'AgentCoordinator',
]
