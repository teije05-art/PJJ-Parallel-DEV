"""
Enhanced Project Jupiter Learning Orchestrator

PDDL-INSTRUCT-inspired system with AgentFlow integration.
Uses 4 specialized agents with Flow-GRPO optimization for real learning.
"""

__version__ = "0.2.0"

# Import the orchestrator classes
from .orchestrator import EnhancedLearningOrchestrator
from .agentflow_agents import (
    PlannerAgent, 
    ExecutorAgent, 
    VerifierAgent, 
    GeneratorAgent, 
    AgentCoordinator
)

__all__ = [
    "EnhancedLearningOrchestrator",
    "PlannerAgent", 
    "ExecutorAgent", 
    "VerifierAgent", 
    "GeneratorAgent", 
    "AgentCoordinator"
]

