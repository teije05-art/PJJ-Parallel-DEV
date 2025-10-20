"""
Enhanced Project Jupiter Learning Orchestrator

PDDL-INSTRUCT-inspired system with AgentFlow integration.
Uses 4 specialized agents with Flow-GRPO optimization for real learning.
"""

__version__ = "0.2.0"

# Import the enhanced orchestrator classes
try:
    from .enhanced_orchestrator import EnhancedLearningOrchestrator
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
    
except ImportError as e:
    # Fallback to original orchestrator if enhanced version fails
    try:
        from .orchestrator import LearningOrchestrator
        __all__ = ["LearningOrchestrator"]
        print(f"Warning: Enhanced orchestrator failed to import ({e}), falling back to original")
    except ImportError:
        __all__ = []
        print(f"Error: No orchestrator available - {e}")

