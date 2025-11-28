"""Memory management system for Project Jupiter.

Phase 1: MemAgent Integration
Implements ByteDance MemAgent's segment-based memory with fixed-length constraints.
"""

from .memagent_memory import SegmentedMemory

__all__ = ['SegmentedMemory']
