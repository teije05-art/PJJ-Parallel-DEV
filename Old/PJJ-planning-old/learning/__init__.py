"""Learning system for Project Jupiter.

Phase 3: Flow-GRPO Training Integration
Implements reinforcement learning for agent coordination and pattern effectiveness.
"""

from .flow_grpo_trainer import FlowGRPOTrainer, IterationSignal
from .agent_coordination import AgentCoordination

__all__ = ['FlowGRPOTrainer', 'IterationSignal', 'AgentCoordination']
