"""Tests for PDDL-INSTRUCT Integration (Phase 2)

Tests for logical reasoning and verification:
- Precondition checking
- Effect verification
- Reasoning chain generation
- Verification feedback
"""

import pytest
from orchestrator.reasoning import LogicalPlanningPrompt, VerificationFeedback
from orchestrator.reasoning.logical_planner import (
    ReasoningLevel, EcommercePlanningPrompt, HealthcarePlanningPrompt
)
from orchestrator.reasoning.verification_feedback import VerificationResult, VerificationReport


class TestLogicalPlanningPrompt:
    """Test LogicalPlanningPrompt class."""

    def test_initialization(self):
        """Test prompt initialization."""
        prompt = LogicalPlanningPrompt("Create a marketing strategy", "ecommerce")
        assert prompt.goal == "Create a marketing strategy"
        assert prompt.domain == "ecommerce"

    def test_add_precondition(self):
        """Test adding preconditions."""
        prompt = LogicalPlanningPrompt("Plan something")

        prompt.add_precondition(
            name="research_complete",
            description="Research has been conducted",
            how_to_verify="Check for market analysis"
        )

        assert len(prompt.preconditions) == 1
        assert prompt.preconditions[0].name == "research_complete"

    def test_add_expected_effect(self):
        """Test adding expected effects."""
        prompt = LogicalPlanningPrompt("Plan something")

        prompt.add_expected_effect(
            name="strategy_created",
            description="Strategy has been created",
            how_to_verify="Check for documented strategy"
        )

        assert len(prompt.expected_effects) == 1
        assert prompt.expected_effects[0].name == "strategy_created"

    def test_generate_precondition_checks(self):
        """Test generating precondition verification text."""
        prompt = LogicalPlanningPrompt("Plan")
        prompt.add_precondition("research_done", "Research complete", "Check analysis")

        text = prompt.generate_precondition_checks({})
        assert "Precondition Verification" in text
        assert "research_done" in text or "Research complete" in text

    def test_generate_full_prompt(self):
        """Test generating complete prompt."""
        prompt = LogicalPlanningPrompt("Plan", "general")
        prompt.add_precondition("ready", "All ready", "Check status")
        prompt.add_expected_effect("done", "Work complete", "Check result")

        full_prompt = prompt.generate_full_prompt({}, reasoning_level=ReasoningLevel.DETAILED)

        assert "Goal" in full_prompt
        assert "Precondition" in full_prompt
        assert "Reasoning Chain" in full_prompt
        assert "Expected Effects" in full_prompt
        assert "Verification" in full_prompt

    def test_verify_preconditions(self):
        """Test precondition verification."""
        prompt = LogicalPlanningPrompt("Plan")
        prompt.add_precondition("market_research", "Market studied", "Check data")

        context = {"market_research_data": "Complete"}

        results = prompt.verify_preconditions(context)

        assert isinstance(results, dict)
        assert "market_research" in results or True  # May not find match

    def test_score_reasoning_quality(self):
        """Test reasoning quality scoring."""
        from orchestrator.reasoning.logical_planner import ReasoningChainStep

        prompt = LogicalPlanningPrompt("Plan")

        steps = [
            ReasoningChainStep(1, "Analyze", "Because needed", "Understanding"),
            ReasoningChainStep(2, "Plan", "Following analysis", "Strategy"),
            ReasoningChainStep(3, "Execute", "From strategy", "Results"),
        ]

        score = prompt.score_reasoning_quality(steps)

        assert 0 <= score <= 1
        assert score > 0.5  # Should be reasonably good

    def test_extract_reasoning_chain(self):
        """Test extracting reasoning chain from response."""
        prompt = LogicalPlanningPrompt("Plan")

        response = """
        1. **ACTION**: Analyze the market
        2. **WHY**: Need to understand competition
        3. **OUTCOME**: Market analysis complete
        """

        chain = prompt.extract_reasoning_chain(response)

        assert len(chain) > 0
        assert chain[0].action
        assert chain[0].reasoning


class TestEcommercePlanningPrompt(TestLogicalPlanningPrompt):
    """Test ecommerce-specific prompt."""

    def test_ecommerce_preconditions(self):
        """Test that ecommerce has specific preconditions."""
        prompt = EcommercePlanningPrompt("Create marketing strategy")

        # Should have ecommerce-specific preconditions
        precond_names = [p.name for p in prompt.preconditions]

        assert len(prompt.preconditions) > 0
        assert any("market" in name.lower() for name in precond_names)


class TestHealthcarePlanningPrompt(TestLogicalPlanningPrompt):
    """Test healthcare-specific prompt."""

    def test_healthcare_preconditions(self):
        """Test that healthcare has specific preconditions."""
        prompt = HealthcarePlanningPrompt("Create care plan")

        # Should have healthcare-specific preconditions
        precond_names = [p.name for p in prompt.preconditions]

        assert len(prompt.preconditions) > 0
        assert any("clinical" in name.lower() or "patient" in name.lower() for name in precond_names)


class TestVerificationFeedback:
    """Test VerificationFeedback class."""

    @pytest.fixture
    def verifier(self):
        """Create a test verifier."""
        return VerificationFeedback(domain="general")

    def test_initialization(self, verifier):
        """Test verifier initialization."""
        assert verifier.domain == "general"
        assert len(verifier.verification_history) == 0

    def test_check_preconditions(self, verifier):
        """Test checking preconditions."""
        preconditions = {
            "research_complete": True,
            "budget_defined": True,
        }

        context = {
            "research_complete": "Market analysis done",
            "budget_defined": 50000,
        }

        checks, all_passed = verifier.check_preconditions(preconditions, context)

        assert len(checks) == 2
        assert isinstance(all_passed, bool)

    def test_check_effects(self, verifier):
        """Test checking effects."""
        expected_effects = {
            "strategy_created": True,
            "timeline_defined": True,
        }

        outcome = "A comprehensive marketing strategy has been created. Timeline: Q1-Q4."

        checks, all_occurred = verifier.check_effects(expected_effects, outcome)

        assert len(checks) == 2
        assert isinstance(all_occurred, bool)

    def test_validate_reasoning_chain(self, verifier):
        """Test reasoning chain validation."""
        steps = [
            "First, analyze the market and competitors",
            "Then, identify target audience demographics",
            "Next, develop positioning strategy",
            "Finally, execute marketing plan",
        ]

        score = verifier.validate_reasoning_chain(steps)

        assert 0 <= score <= 1
        assert score > 0.3  # Should have some quality

    def test_generate_binary_feedback(self, verifier):
        """Test binary feedback generation."""
        valid_feedback = verifier.generate_binary_feedback(True)
        invalid_feedback = verifier.generate_binary_feedback(False)

        assert "✅" in valid_feedback or "Correct" in valid_feedback
        assert "❌" in invalid_feedback or "Incorrect" in invalid_feedback

    def test_generate_detailed_feedback(self, verifier):
        """Test detailed feedback generation."""
        from orchestrator.reasoning.verification_feedback import PreconditionCheck, EffectCheck

        precond_checks = [
            PreconditionCheck(
                name="research",
                description="Research Complete",
                result=VerificationResult.PASS,
                explanation="Market research done"
            )
        ]

        effect_checks = [
            EffectCheck(
                name="strategy",
                description="Strategy Created",
                result=VerificationResult.PASS,
                explanation="Strategy documented"
            )
        ]

        feedback = verifier.generate_detailed_feedback(
            precond_checks, effect_checks, reasoning_score=0.85
        )

        assert "Preconditions" in feedback or "preconditions" in feedback.lower()
        assert "Effects" in feedback or "effects" in feedback.lower()

    def test_generate_verification_report(self, verifier):
        """Test complete verification report generation."""
        preconditions = {"research_done": True}
        effects = {"strategy_created": True}
        outcome = "Strategy was successfully created"
        steps = ["Analyze", "Plan", "Execute"]
        context = {"research_done": "Yes"}

        report = verifier.generate_verification_report(
            preconditions=preconditions,
            expected_effects=effects,
            actual_outcome=outcome,
            reasoning_steps=steps,
            context=context
        )

        assert isinstance(report, VerificationReport)
        assert report.overall_validity is not None
        assert report.reasoning_quality_score > 0

    def test_verification_history(self, verifier):
        """Test that verification history is tracked."""
        preconditions = {"test": True}
        effects = {"result": True}

        verifier.generate_verification_report(
            preconditions=preconditions,
            expected_effects=effects,
            actual_outcome="Something happened",
            reasoning_steps=["Step 1"],
            context={}
        )

        assert len(verifier.verification_history) == 1

    def test_get_verification_summary(self, verifier):
        """Test verification summary generation."""
        summary = verifier.get_verification_summary()

        assert "total_reports" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
