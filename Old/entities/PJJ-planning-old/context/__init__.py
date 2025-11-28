"""
Context Management Module

Provides modular context retrieval for planning operations:
- goal_context: Goal analysis and project status
- memory_context: Memory retrieval for patterns and history
- search_context: Web search for real-world data
- context_builder: Main orchestrator combining all context sources
- context_formatter: Formatting utilities

This refactoring splits the monolithic context_manager.py (350 lines) into
focused modules, each with a single responsibility.
"""

from .context_builder import ContextBuilder
from .goal_context import GoalContextProvider
from .memory_context import MemoryContextProvider
from .search_context import SearchContextProvider

__all__ = [
    'ContextBuilder',
    'GoalContextProvider',
    'MemoryContextProvider',
    'SearchContextProvider'
]
