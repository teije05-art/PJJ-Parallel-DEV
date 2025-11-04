"""Integration layer for Project Jupiter.

Phase 4: Complete System Integration
Wires together MemAgent (Phase 1), PDDL-INSTRUCT (Phase 2), and Flow-GRPO (Phase 3)
into a unified planning loop with closed-loop learning.
"""

from .planning_loop import IntegratedPlanningLoop

__all__ = ['IntegratedPlanningLoop']
