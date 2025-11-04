"""Tests for Flow-GRPO Integration (Phase 3)

Tests for training signals and agent coordination:
- Flow score calculation
- Agent weight updates
- Pattern effectiveness tracking
- Agent pair performance learning
"""

import pytest
from orchestrator.learning import FlowGRPOTrainer, IterationSignal
from orchestrator.learning.agent_coordination import AgentCoordination


class TestIterationSignal:
    """Test IterationSignal dataclass."""

    def test_signal_creation(self):
        """Test creating an iteration signal."""
        signal = IterationSignal(
            iteration=1,
            agent_name="planner",
            verification_quality=0.85,
            user_approved=True,
            reasoning_quality=0.80
        )

        assert signal.iteration == 1
        assert signal.agent_name == "planner"
        assert signal.verification_quality == 0.85

    def test_flow_score_calculation(self):
        """Test flow score calculation."""
        signal = IterationSignal(
            iteration=1,
            agent_name="planner",
            verification_quality=0.8,
            user_approved=True,
            reasoning_quality=0.9
        )

        flow_score = signal.calculate_flow_score()

        assert 0 <= flow_score <= 1
        assert flow_score > 0.5  # Should be decent since approved

    def test_flow_score_without_approval(self):
        """Test flow score when not approved."""
        signal = IterationSignal(
            iteration=1,
            agent_name="planner",
            verification_quality=0.8,
            user_approved=False,
            reasoning_quality=0.9
        )

        flow_score = signal.calculate_flow_score()

        # Should be lower than approved version
        approved_signal = IterationSignal(
            iteration=2,
            agent_name="planner",
            verification_quality=0.8,
            user_approved=True,
            reasoning_quality=0.9
        )

        assert flow_score < approved_signal.calculate_flow_score()


class TestFlowGRPOTrainer:
    """Test FlowGRPOTrainer class."""

    @pytest.fixture
    def trainer(self):
        """Create a test trainer."""
        return FlowGRPOTrainer(learning_rate=0.05, baseline_score=0.5)

    def test_initialization(self, trainer):
        """Test trainer initialization."""
        assert trainer.learning_rate == 0.05
        assert trainer.baseline_score == 0.5
        assert 'planner' in trainer.agent_selection_weights
        assert 'verifier' in trainer.agent_selection_weights

    def test_record_iteration_signal(self, trainer):
        """Test recording iteration signal."""
        flow_score = trainer.record_iteration_signal(
            iteration=1,
            agent_name="planner",
            verification_quality=0.8,
            user_approved=True,
            reasoning_quality=0.85
        )

        assert 0 <= flow_score <= 1
        assert len(trainer.iteration_signals) == 1
        assert trainer.iteration_signals[0].iteration == 1

    def test_agent_weight_update(self, trainer):
        """Test agent weights update based on performance."""
        initial_weight = trainer.agent_selection_weights['planner']

        # Good performance - weight should increase
        trainer.record_iteration_signal(
            iteration=1,
            agent_name="planner",
            verification_quality=0.9,
            user_approved=True,
            reasoning_quality=0.9
        )

        new_weight = trainer.agent_selection_weights['planner']
        assert new_weight > initial_weight

    def test_pattern_performance(self, trainer):
        """Test recording pattern performance."""
        trainer.record_pattern_performance(
            pattern_name="pattern_1",
            flow_score=0.85,
            verification_passed=True,
            user_approved=True
        )

        assert "pattern_1" in trainer.pattern_scores
        assert trainer.pattern_scores["pattern_1"] > 0.5

    def test_get_recommended_agent_sequence(self, trainer):
        """Test getting recommended agent sequence."""
        # Update weights
        trainer.record_iteration_signal(1, "planner", 0.9, True, 0.9)
        trainer.record_iteration_signal(1, "verifier", 0.7, True, 0.7)
        trainer.update_agent_weights()

        sequence = trainer.get_recommended_agent_sequence()

        assert len(sequence) > 0
        assert isinstance(sequence[0], tuple)  # (name, weight)
        assert sequence[0][0]  # Has agent name

    def test_get_top_patterns(self, trainer):
        """Test getting top patterns."""
        trainer.record_pattern_performance("pattern_a", 0.9, True, True)
        trainer.record_pattern_performance("pattern_b", 0.6, False, False)

        top = trainer.get_top_patterns(2)

        assert len(top) <= 2
        # pattern_a should be first (higher score)
        if len(top) > 1:
            assert top[0][0] == "pattern_a"

    def test_should_skip_agent(self, trainer):
        """Test checking if agent should be skipped."""
        # Default weights should be used
        should_skip = trainer.should_skip_agent("planner", threshold=0.2)

        assert isinstance(should_skip, bool)

    def test_training_summary(self, trainer):
        """Test getting training summary."""
        trainer.record_iteration_signal(1, "planner", 0.8, True, 0.85)
        trainer.record_iteration_signal(2, "verifier", 0.75, False, 0.80)

        summary = trainer.get_training_summary()

        assert summary['total_iterations'] == 2
        assert 'approval_rate' in summary
        assert summary['approval_rate'] > 0  # At least one approved

    def test_reset_weights(self, trainer):
        """Test resetting agent weights."""
        # Update weights
        trainer.record_iteration_signal(1, "planner", 0.9, True, 0.9)

        # Reset
        trainer.reset_weights()

        for agent, weight in trainer.agent_selection_weights.items():
            assert weight == 1.0

    def test_serialization(self, trainer):
        """Test trainer serialization."""
        trainer.record_iteration_signal(1, "planner", 0.85, True, 0.90)

        data = trainer.to_dict()

        assert 'agent_selection_weights' in data
        assert 'pattern_scores' in data
        assert data['iteration_count'] == 1

    def test_deserialization(self, trainer):
        """Test trainer deserialization."""
        trainer.record_iteration_signal(1, "planner", 0.85, True, 0.90)
        data = trainer.to_dict()

        trainer2 = FlowGRPOTrainer.from_dict(data)

        assert trainer2.learning_rate == trainer.learning_rate
        assert trainer2.baseline_score == trainer.baseline_score


class TestAgentCoordination:
    """Test AgentCoordination class."""

    @pytest.fixture
    def coordinator(self):
        """Create a test coordinator."""
        return AgentCoordination()

    def test_initialization(self, coordinator):
        """Test coordinator initialization."""
        assert coordinator.default_sequence == ['planner', 'verifier', 'executor', 'generator']
        assert len(coordinator.pair_performances) == 0

    def test_record_pair_performance(self, coordinator):
        """Test recording agent pair performance."""
        coordinator.record_pair_performance("planner", "verifier", flow_score=0.85, success=True)

        pair_key = ("planner", "verifier")
        assert pair_key in coordinator.pair_performances
        assert coordinator.pair_performances[pair_key].get_average_score() == 0.85

    def test_pair_score_untested(self, coordinator):
        """Test pair score for untested pairs."""
        score = coordinator.get_pair_score("planner", "executor")

        assert score == 0.5  # Default for untested pairs

    def test_pair_score_tested(self, coordinator):
        """Test pair score for tested pairs."""
        coordinator.record_pair_performance("planner", "verifier", 0.8, True)
        coordinator.record_pair_performance("planner", "verifier", 0.9, True)

        score = coordinator.get_pair_score("planner", "verifier")

        assert score == 0.85  # Average of 0.8 and 0.9

    def test_recommend_agent_sequence(self, coordinator):
        """Test recommending agent sequence."""
        # Record some pair performances
        coordinator.record_pair_performance("planner", "verifier", 0.9, True)
        coordinator.record_pair_performance("verifier", "executor", 0.8, True)
        coordinator.record_pair_performance("executor", "generator", 0.85, True)

        sequence = coordinator.recommend_agent_sequence()

        assert len(sequence) > 0
        assert sequence[0] in ["planner", "verifier", "executor", "generator"]

    def test_should_skip_agent_pair(self, coordinator):
        """Test checking if pair should be skipped."""
        # Untested pair
        should_skip = coordinator.should_skip_agent_pair("planner", "verifier")
        assert should_skip is False

        # Low-performing pair
        coordinator.record_pair_performance("planner", "verifier", 0.1, False)
        should_skip = coordinator.should_skip_agent_pair("planner", "verifier", threshold=0.3)
        assert should_skip is True

    def test_mark_agent_unavailable(self, coordinator):
        """Test marking agent unavailable."""
        coordinator.mark_agent_unavailable("planner")
        assert coordinator.agent_available["planner"] is False

    def test_mark_agent_available(self, coordinator):
        """Test marking agent available."""
        coordinator.mark_agent_unavailable("planner")
        coordinator.mark_agent_available("planner")
        assert coordinator.agent_available["planner"] is True

    def test_coordination_summary(self, coordinator):
        """Test coordination summary."""
        coordinator.record_pair_performance("planner", "verifier", 0.85, True)
        coordinator.record_pair_performance("verifier", "executor", 0.75, True)

        summary = coordinator.get_coordination_summary()

        assert 'total_pairs_learned' in summary
        assert summary['total_pairs_learned'] == 2
        assert 'recommended_sequence' in summary

    def test_reset_learning(self, coordinator):
        """Test resetting coordination learning."""
        coordinator.record_pair_performance("planner", "verifier", 0.85, True)

        coordinator.reset_learning()

        assert len(coordinator.pair_performances) == 0

    def test_serialization(self, coordinator):
        """Test coordinator serialization."""
        coordinator.record_pair_performance("planner", "verifier", 0.85, True)

        data = coordinator.to_dict()

        assert 'pair_performances' in data
        assert 'agent_availability' in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
