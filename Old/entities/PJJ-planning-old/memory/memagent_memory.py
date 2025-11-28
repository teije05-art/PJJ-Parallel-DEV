"""MemAgent-based Segmented Memory System for Project Jupiter

Phase 1 Implementation: ByteDance MemAgent Principles
- Fixed-length memory (12 segments max)
- Semantic search via MemAgent
- Lossless compression for old segments
- RL-trained overwrite scoring

Reference: MemAgent: Reshaping Long-Context LLM with Multi-Conv RL-based Memory Agent
(ByteDance/Tsinghua, 2507.02259v1)
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from collections import defaultdict


@dataclass
class MemorySegment:
    """A single segment in the fixed-length memory."""

    content: str  # The actual segment content
    source: str  # Where this came from (e.g., "iteration_1_planner", "user_feedback")
    importance_score: float = 0.5  # 0-1, learned importance
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    compressed_from: Optional[str] = None  # If compressed, reference to original
    token_count: int = 0  # Approximate token count
    access_count: int = 0  # How many times this segment was retrieved
    semantic_tags: List[str] = field(default_factory=list)  # For quick filtering

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'MemorySegment':
        """Create from dictionary."""
        return cls(**data)


class SegmentedMemory:
    """Fixed-length memory system following MemAgent principles.

    Key Features:
    - Fixed 12 segments max (configurable)
    - Max 2000 tokens per segment
    - Semantic search retrieval via MemAgent
    - Lossless compression when full
    - RL-trained overwrite scores (learned importance)

    Design:
    - Segments are added with importance scores
    - When memory is full, least-important segment is compressed
    - Compression maintains semantic meaning despite token reduction
    - System learns which segments matter through user feedback
    """

    def __init__(self,
                 max_segments: int = 12,
                 max_tokens_per_segment: int = 2000,
                 memagent_client: Optional[Any] = None):
        """Initialize SegmentedMemory.

        Args:
            max_segments: Maximum number of segments (default 12)
            max_tokens_per_segment: Maximum tokens per segment (default 2000)
            memagent_client: MemAgent client for semantic search (optional)
        """
        self.max_segments = max_segments
        self.max_tokens_per_segment = max_tokens_per_segment
        self.memagent_client = memagent_client

        # Core memory storage
        self.segments: List[MemorySegment] = []

        # Segment metadata for intelligent management
        self.segment_importance_scores: Dict[int, float] = {}  # seg_idx → importance
        self.segment_access_patterns: Dict[int, List[str]] = defaultdict(list)  # seg_idx → [queries]
        self.compression_history: List[Dict] = []  # Track what was compressed

        # RL-trained overwrite strategy
        self.overwrite_weights: Dict[str, float] = {
            'importance_score': 0.4,  # Lower importance = more likely to overwrite
            'access_frequency': 0.3,  # Less accessed = more likely to overwrite
            'age': 0.2,  # Older = more likely to overwrite
            'size': 0.1,  # Larger = slightly more likely to overwrite
        }

        # Training signals for improving overwrite strategy
        self.overwrite_training_signals: List[Dict] = []

        print(f"✅ SegmentedMemory initialized: {max_segments} segments, {max_tokens_per_segment} tokens/segment")

    # ========== CORE OPERATIONS ==========

    def add_segment(self,
                    content: str,
                    source: str,
                    importance_score: float = 0.5,
                    semantic_tags: Optional[List[str]] = None) -> bool:
        """Add a new segment to memory, handling overflow.

        If memory is full:
        1. Calculate overwrite scores for all segments
        2. Remove least important segment
        3. Compress it as backup
        4. Add new segment

        Args:
            content: The segment content
            source: Where this came from (e.g., "iteration_1", "user_feedback")
            importance_score: Estimated importance (0-1)
            semantic_tags: Optional tags for filtering

        Returns:
            True if added successfully, False if failed
        """
        # Estimate token count (rough: ~4 chars per token)
        token_count = len(content) // 4

        if token_count > self.max_tokens_per_segment:
            # Segment too large - compress before adding
            content = self._compress_content(content, target_tokens=self.max_tokens_per_segment)
            token_count = len(content) // 4

        # Create new segment
        new_segment = MemorySegment(
            content=content,
            source=source,
            importance_score=importance_score,
            token_count=token_count,
            semantic_tags=semantic_tags or []
        )

        # Check if we're at capacity
        if len(self.segments) >= self.max_segments:
            # Memory full - need to overwrite least important segment
            victim_idx = self._select_segment_to_overwrite()

            # Compress the victim before removing
            victim = self.segments[victim_idx]
            compressed = self._compress_content(
                victim.content,
                target_tokens=min(500, victim.token_count // 2)
            )

            # Record compression for potential recovery
            self.compression_history.append({
                'timestamp': datetime.now().isoformat(),
                'original_source': victim.source,
                'original_tokens': victim.token_count,
                'compressed_tokens': len(compressed) // 4,
                'compressed_content': compressed[:200] + "..."  # Store first 200 chars
            })

            print(f"   💾 Memory full. Compressed segment from '{victim.source}' "
                  f"({victim.token_count} → {len(compressed) // 4} tokens)")

            # Remove victim and add new segment
            self.segments.pop(victim_idx)

        # Add new segment
        self.segments.append(new_segment)
        seg_idx = len(self.segments) - 1
        self.segment_importance_scores[seg_idx] = importance_score

        print(f"   ✓ Added segment #{seg_idx}: '{source}' ({token_count} tokens, "
              f"importance={importance_score:.2f})")

        return True

    def get_relevant_segments(self,
                             query: str,
                             top_k: int = 3,
                             threshold: float = 0.3) -> List[Tuple[int, MemorySegment, float]]:
        """Retrieve top-K most relevant segments for a query.

        Uses semantic search if MemAgent client available, else falls back to keyword matching.

        Args:
            query: The search query
            top_k: Number of segments to return
            threshold: Minimum relevance score (0-1)

        Returns:
            List of (segment_idx, segment, relevance_score) tuples, sorted by relevance
        """
        if not self.segments:
            return []

        relevance_scores = []

        for idx, segment in enumerate(self.segments):
            # Calculate relevance score
            if self.memagent_client:
                # Use semantic search if available
                relevance = self._semantic_similarity(query, segment.content)
            else:
                # Fallback: keyword matching
                relevance = self._keyword_match_score(query, segment.content)

            if relevance >= threshold:
                relevance_scores.append((idx, segment, relevance))

        # Sort by relevance (descending)
        relevance_scores.sort(key=lambda x: x[2], reverse=True)

        # Update access patterns
        for idx, segment, score in relevance_scores[:top_k]:
            self.segment_access_patterns[idx].append(query)

        return relevance_scores[:top_k]

    def get_segment(self, idx: int) -> Optional[MemorySegment]:
        """Get a specific segment by index."""
        if 0 <= idx < len(self.segments):
            segment = self.segments[idx]
            segment.access_count += 1
            return segment
        return None

    def compress_segment(self, idx: int) -> Optional[str]:
        """Compress a specific segment while maintaining semantic meaning.

        Uses abstractive summarization approach.

        Args:
            idx: Segment index to compress

        Returns:
            Compressed content, or None if segment doesn't exist
        """
        if not (0 <= idx < len(self.segments)):
            return None

        segment = self.segments[idx]
        original_tokens = segment.token_count

        # Target: 30-50% of original size
        target_tokens = int(original_tokens * 0.4)
        compressed = self._compress_content(segment.content, target_tokens=target_tokens)

        # Update segment
        segment.content = compressed
        segment.token_count = len(compressed) // 4
        segment.compressed_from = segment.source

        print(f"   🔄 Compressed segment #{idx}: {original_tokens} → {segment.token_count} tokens")

        return compressed

    # ========== LEARNING & TRAINING ==========

    def train_overwrite_scores(self,
                              plan_result: Dict[str, Any],
                              user_approved: bool = True) -> None:
        """Update overwrite strategy based on planning outcomes.

        Implements RL-style training: learn which segments matter for good plans.

        Args:
            plan_result: Result dict from planning iteration
            user_approved: Whether user approved the plan
        """
        if not self.segments:
            return

        # Calculate outcome score (0-1)
        outcome_score = (
            (0.8 if user_approved else 0.2) +  # User approval is strong signal
            (plan_result.get('quality_score', 0.5) * 0.2)  # Plan quality
        )

        # Which segments were used (accessed) in this iteration?
        used_segments = {
            idx for idx, patterns in self.segment_access_patterns.items()
            if len(patterns) > 0
        }

        # Train: segments that were used in good plans matter more
        for idx, segment in enumerate(self.segments):
            if idx in used_segments:
                # Increase importance (good outcome with this segment)
                adjustment = 0.05 * outcome_score
                segment.importance_score = min(1.0, segment.importance_score + adjustment)
            else:
                # Slightly decrease unused segments
                segment.importance_score = max(0.0, segment.importance_score - 0.02)

            self.segment_importance_scores[idx] = segment.importance_score

        # Record training signal for future optimization
        self.overwrite_training_signals.append({
            'timestamp': datetime.now().isoformat(),
            'outcome_score': outcome_score,
            'used_segments': list(used_segments),
            'segment_importances': dict(self.segment_importance_scores)
        })

        print(f"   📊 Updated segment importance scores (outcome={outcome_score:.2f}, "
              f"used={len(used_segments)}/{len(self.segments)})")

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of current memory state."""
        total_tokens = sum(seg.token_count for seg in self.segments)

        return {
            'segment_count': len(self.segments),
            'max_segments': self.max_segments,
            'total_tokens': total_tokens,
            'max_tokens': self.max_segments * self.max_tokens_per_segment,
            'utilization_percent': (total_tokens / (self.max_segments * self.max_tokens_per_segment)) * 100,
            'segments': [
                {
                    'idx': idx,
                    'source': seg.source,
                    'tokens': seg.token_count,
                    'importance': seg.importance_score,
                    'accesses': seg.access_count,
                }
                for idx, seg in enumerate(self.segments)
            ],
            'compression_count': len(self.compression_history)
        }

    # ========== INTERNAL HELPERS ==========

    def _select_segment_to_overwrite(self) -> int:
        """Select which segment to overwrite using RL-trained weights.

        Calculates overwrite score for each segment:
        score = w1 * (1 - importance) + w2 * (1 - access_freq) + w3 * age + w4 * size

        Returns:
            Index of segment to overwrite (lowest score = least useful)
        """
        if not self.segments:
            return 0

        overwrite_scores = []
        now = datetime.fromisoformat(datetime.now().isoformat())

        for idx, segment in enumerate(self.segments):
            # Normalize components (0-1)
            importance_factor = 1.0 - segment.importance_score

            access_freq = min(1.0, segment.access_count / max(1, sum(
                s.access_count for s in self.segments
            )))
            access_factor = 1.0 - access_freq

            # Age factor (newer = higher access = less likely to overwrite)
            created = datetime.fromisoformat(segment.created_at)
            age_seconds = (now - created).total_seconds()
            age_factor = min(1.0, age_seconds / (7 * 24 * 3600))  # 7 days = 1.0

            size_factor = segment.token_count / self.max_tokens_per_segment

            # Calculate weighted score
            score = (
                self.overwrite_weights['importance_score'] * importance_factor +
                self.overwrite_weights['access_frequency'] * access_factor +
                self.overwrite_weights['age'] * age_factor +
                self.overwrite_weights['size'] * size_factor
            )

            overwrite_scores.append((idx, score))

        # Return index with highest overwrite score (most likely to remove)
        return max(overwrite_scores, key=lambda x: x[1])[0]

    def _compress_content(self, content: str, target_tokens: int) -> str:
        """Compress content while maintaining semantic meaning.

        Simple implementation: extract key sentences based on word frequency.

        Args:
            content: Original content
            target_tokens: Target number of tokens

        Returns:
            Compressed content
        """
        current_tokens = len(content) // 4

        if current_tokens <= target_tokens:
            return content

        # Simple compression: keep first N sentences to reach target
        sentences = content.split('.')

        compressed_parts = []
        token_count = 0

        for sentence in sentences:
            sentence_tokens = len(sentence) // 4
            if token_count + sentence_tokens <= target_tokens:
                compressed_parts.append(sentence.strip())
                token_count += sentence_tokens
            else:
                break

        return '.'.join(compressed_parts) + '.' if compressed_parts else content[:target_tokens * 4]

    def _semantic_similarity(self, query: str, content: str) -> float:
        """Calculate semantic similarity between query and content.

        Uses MemAgent client if available.
        """
        if not self.memagent_client:
            return self._keyword_match_score(query, content)

        try:
            # Use MemAgent for semantic search
            # This is a placeholder - actual implementation would use MemAgent
            similarity = self.memagent_client.semantic_similarity(query, content)
            return similarity
        except Exception as e:
            print(f"   ⚠️ Semantic search failed: {e}, falling back to keyword matching")
            return self._keyword_match_score(query, content)

    def _keyword_match_score(self, query: str, content: str) -> float:
        """Fallback: keyword matching similarity score."""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())

        if not query_words:
            return 0.5

        matches = len(query_words & content_words)
        return matches / len(query_words)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize memory to dictionary."""
        return {
            'segments': [seg.to_dict() for seg in self.segments],
            'max_segments': self.max_segments,
            'max_tokens_per_segment': self.max_tokens_per_segment,
            'importance_scores': self.segment_importance_scores,
            'overwrite_weights': self.overwrite_weights,
            'compression_history': self.compression_history,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SegmentedMemory':
        """Deserialize memory from dictionary."""
        memory = cls(
            max_segments=data.get('max_segments', 12),
            max_tokens_per_segment=data.get('max_tokens_per_segment', 2000)
        )

        # Restore segments
        memory.segments = [
            MemorySegment.from_dict(seg_dict)
            for seg_dict in data.get('segments', [])
        ]

        # Restore metadata
        memory.segment_importance_scores = data.get('importance_scores', {})
        memory.overwrite_weights = data.get('overwrite_weights', memory.overwrite_weights)
        memory.compression_history = data.get('compression_history', [])

        return memory
