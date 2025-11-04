"""Tests for MemAgent Integration (Phase 1)

Tests for SegmentedMemory implementation:
- Fixed-length memory constraints
- Semantic search retrieval
- Compression of old segments
- Importance scoring and overwrite strategy
"""

import pytest
from orchestrator.memory import SegmentedMemory
from orchestrator.memory.memagent_memory import MemorySegment


class TestSegmentedMemory:
    """Test SegmentedMemory class."""

    @pytest.fixture
    def memory(self):
        """Create a test memory instance."""
        return SegmentedMemory(max_segments=5, max_tokens_per_segment=1000)

    def test_initialization(self, memory):
        """Test SegmentedMemory initialization."""
        assert memory.max_segments == 5
        assert memory.max_tokens_per_segment == 1000
        assert len(memory.segments) == 0

    def test_add_segment(self, memory):
        """Test adding a segment to memory."""
        success = memory.add_segment(
            content="Market research shows growth trends",
            source="research_phase",
            importance_score=0.8
        )
        assert success
        assert len(memory.segments) == 1
        assert memory.segments[0].content == "Market research shows growth trends"

    def test_memory_bounded(self, memory):
        """Test that memory stays bounded at max_segments."""
        # Add more segments than max
        for i in range(10):
            memory.add_segment(
                content=f"Segment {i}: " + ("x" * 100),
                source=f"iteration_{i}",
                importance_score=0.5
            )

        # Should only have max_segments
        assert len(memory.segments) <= memory.max_segments
        assert len(memory.segments) == memory.max_segments

    def test_importance_scoring(self, memory):
        """Test that importance scores affect segment retention."""
        # Add low-importance segment
        memory.add_segment(
            content="Low importance content",
            source="low_priority",
            importance_score=0.1
        )

        # Add high-importance segment
        memory.add_segment(
            content="High importance strategic decision",
            source="high_priority",
            importance_score=0.9
        )

        # When memory fills up, low-importance should be compressed first
        for i in range(10):
            memory.add_segment(
                content=f"New content {i}",
                source=f"new_{i}",
                importance_score=0.5
            )

        # High-priority should still be there (not compressed)
        sources = [s.source for s in memory.segments]
        assert "high_priority" in sources or "low_priority" not in sources

    def test_semantic_search(self, memory):
        """Test retrieving segments by semantic similarity."""
        memory.add_segment(
            content="Market research shows ecommerce trends",
            source="market_analysis",
            importance_score=0.7
        )

        memory.add_segment(
            content="Customer demographic analysis reveals target audience",
            source="customer_analysis",
            importance_score=0.8
        )

        # Search for market-related content
        results = memory.get_relevant_segments("market trends", top_k=2)

        assert len(results) >= 1
        # First result should be market-related
        assert "market" in results[0][1].content.lower()

    def test_compression(self, memory):
        """Test segment compression."""
        large_content = "This is a large segment. " * 100
        memory.add_segment(
            content=large_content,
            source="large_segment",
            importance_score=0.5
        )

        original_tokens = len(large_content) // 4

        # Compress the segment
        compressed = memory.compress_segment(0)

        assert compressed is not None
        assert len(compressed) < len(large_content)
        assert len(compressed) // 4 < original_tokens

    def test_overwrite_training(self, memory):
        """Test that overwrite scores update based on outcomes."""
        memory.add_segment(
            content="Market research complete",
            source="iteration_1",
            importance_score=0.5
        )

        memory.add_segment(
            content="Customer analysis complete",
            source="iteration_2",
            importance_score=0.5
        )

        # Train: mark iteration_1 as having good outcome
        memory.train_overwrite_scores(
            plan_result={'quality_score': 0.9},
            user_approved=True
        )

        # Check that importance scores changed
        assert memory.segments[0].importance_score > 0.5  # Should increase

    def test_memory_summary(self, memory):
        """Test memory summary generation."""
        memory.add_segment(
            content="First segment with data",
            source="seg1",
            importance_score=0.6
        )

        memory.add_segment(
            content="Second segment",
            source="seg2",
            importance_score=0.4
        )

        summary = memory.get_memory_summary()

        assert summary['segment_count'] == 2
        assert summary['max_segments'] == 5
        assert 'utilization_percent' in summary
        assert len(summary['segments']) == 2

    def test_serialization(self, memory):
        """Test memory serialization/deserialization."""
        memory.add_segment(
            content="Test content",
            source="test",
            importance_score=0.7
        )

        # Serialize
        data = memory.to_dict()
        assert 'segments' in data
        assert len(data['segments']) == 1

        # Deserialize
        memory2 = SegmentedMemory.from_dict(data)
        assert len(memory2.segments) == 1
        assert memory2.segments[0].content == "Test content"
        assert memory2.segments[0].importance_score == 0.7


class TestMemorySegment:
    """Test MemorySegment dataclass."""

    def test_segment_creation(self):
        """Test creating a memory segment."""
        seg = MemorySegment(
            content="Test content",
            source="test_source",
            importance_score=0.75,
            token_count=50
        )

        assert seg.content == "Test content"
        assert seg.source == "test_source"
        assert seg.importance_score == 0.75
        assert seg.token_count == 50

    def test_segment_serialization(self):
        """Test segment to/from dict."""
        seg = MemorySegment(
            content="Content",
            source="source",
            importance_score=0.8
        )

        data = seg.to_dict()
        seg2 = MemorySegment.from_dict(data)

        assert seg.content == seg2.content
        assert seg.source == seg2.source
        assert seg.importance_score == seg2.importance_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
