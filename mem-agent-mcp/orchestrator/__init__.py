"""
Enhanced Project Jupiter Learning Orchestrator

PDDL-INSTRUCT-inspired system with AgentFlow integration.
Uses 4 specialized agents with Flow-GRPO optimization for real learning.

Now with modular architecture for easier maintenance and web search integration!
"""

__version__ = "0.3.0"

# Import the orchestrator classes
from .simple_orchestrator import SimpleOrchestrator  # NEW: Modular version
from .agentflow_agents import (
    PlannerAgent,
    ExecutorAgent,
    VerifierAgent,
    GeneratorAgent,
    AgentCoordinator
)

__all__ = [
    "SimpleOrchestrator",  # NEW: Use this one!
    "PlannerAgent",
    "ExecutorAgent",
    "VerifierAgent",
    "GeneratorAgent",
    "AgentCoordinator"
]

