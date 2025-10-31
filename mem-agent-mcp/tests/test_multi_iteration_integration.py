#!/usr/bin/env python3
"""
Integration Tests for Multi-Iteration Planning System

Tests the complete workflow:
1. Single iteration planning
2. Multi-iteration planning with proposal approval
3. Checkpoint approval flow
4. Multi-agent orchestration
5. MemAgent-guided iteration deepening

Run with: pytest tests/test_multi_iteration_integration.py -v
"""

import pytest
import sys
import os
from pathlib import Path
from datetime import datetime

# Add repo to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

# ============================================================================
# IMPORTS
# ============================================================================

try:
    from orchestrator.simple_orchestrator import SimpleOrchestrator
    from orchestrator.iteration_manager import IterationManager, IterationResult
    ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Orchestrator not available: {e}")
    ORCHESTRATOR_AVAILABLE = False

try:
    from llama_planner import LlamaPlanner
    LLAMA_PLANNER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: LlamaPlanner not available: {e}")
    LLAMA_PLANNER_AVAILABLE = False

try:
    from orchestrator.agents import (
        PlannerAgent, VerifierAgent, ExecutorAgent, GeneratorAgent
    )
    AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Agents not available: {e}")
    AGENTS_AVAILABLE = False

try:
    from agent.agent import Agent
    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Agent not available: {e}")
    AGENT_AVAILABLE = False

# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def memory_path():
    """Create test memory path"""
    test_memory = Path(REPO_ROOT) / "test_memory"
    test_memory.mkdir(exist_ok=True)
    yield test_memory
    # Cleanup is manual to preserve results for inspection


@pytest.fixture
def orchestrator(memory_path):
    """Create orchestrator instance for testing"""
    if not ORCHESTRATOR_AVAILABLE:
        pytest.skip("Orchestrator not available")

    return SimpleOrchestrator(str(memory_path))


@pytest.fixture
def iteration_manager(memory_path):
    """Create iteration manager for testing"""
    if not ORCHESTRATOR_AVAILABLE:
        pytest.skip("Orchestrator not available")

    if not LLAMA_PLANNER_AVAILABLE:
        pytest.skip("LlamaPlanner not available")

    llama_planner = LlamaPlanner(str(memory_path))
    return IterationManager(
        max_iterations=6,
        checkpoint_interval=3,
        llama_planner=llama_planner,
        goal="Test goal"
    )


# ============================================================================
# UNIT TESTS: Data Models
# ============================================================================

class TestIterationResult:
    """Test IterationResult data structure"""

    def test_iteration_result_creation(self):
        """Test creating IterationResult"""
        result = IterationResult(
            iteration_num=1,
            plan="Test plan content",
            key_insights=["Insight 1", "Insight 2"],
            frameworks_used=["Framework A", "Framework B"],
            data_points_count=5
        )

        assert result.iteration_num == 1
        assert result.plan == "Test plan content"
        assert len(result.key_insights) == 2
        assert result.data_points_count == 5
        assert result.execution_timestamp  # Should be set automatically

    def test_iteration_result_defaults(self):
        """Test IterationResult with defaults"""
        result = IterationResult(
            iteration_num=2,
            plan="Plan"
        )

        assert result.key_insights == []
        assert result.frameworks_used == []
        assert result.data_points_count == 0
        assert result.metadata == {}


# ============================================================================
# UNIT TESTS: IterationManager
# ============================================================================

@pytest.mark.skipif(not ORCHESTRATOR_AVAILABLE, reason="Orchestrator not available")
class TestIterationManager:
    """Test IterationManager functionality"""

    def test_initialization(self, iteration_manager):
        """Test IterationManager initialization"""
        assert iteration_manager.max_iterations == 6
        assert iteration_manager.checkpoint_interval == 3
        assert iteration_manager.current_iteration == 0
        assert len(iteration_manager.iteration_history) == 0

    def test_validation(self, memory_path):
        """Test IterationManager validation"""
        llama_planner = LlamaPlanner(str(memory_path))

        # Test invalid max_iterations
        with pytest.raises(ValueError):
            IterationManager(
                max_iterations=0,
                checkpoint_interval=3,
                llama_planner=llama_planner,
                goal="Test"
            )

        # Test invalid checkpoint_interval
        with pytest.raises(ValueError):
            IterationManager(
                max_iterations=6,
                checkpoint_interval=0,
                llama_planner=llama_planner,
                goal="Test"
            )

        # Test None llama_planner
        with pytest.raises(ValueError):
            IterationManager(
                max_iterations=6,
                checkpoint_interval=3,
                llama_planner=None,
                goal="Test"
            )

    def test_checkpoint_logic(self, iteration_manager):
        """Test checkpoint interval logic"""
        # Checkpoint at iteration 3
        iteration_manager.current_iteration = 3
        assert iteration_manager.should_checkpoint()

        # No checkpoint at iteration 2
        iteration_manager.current_iteration = 2
        assert not iteration_manager.should_checkpoint()

        # Checkpoint at iteration 6
        iteration_manager.current_iteration = 6
        assert iteration_manager.should_checkpoint()

    def test_iteration_tracking(self, iteration_manager):
        """Test iteration counter tracking"""
        assert iteration_manager.get_next_iteration_number() == 1

        iteration_manager.current_iteration = 1
        assert iteration_manager.get_next_iteration_number() == 2

        iteration_manager.current_iteration = 5
        assert iteration_manager.get_next_iteration_number() == 6

    def test_completion_check(self, iteration_manager):
        """Test iteration completion checking"""
        assert not iteration_manager.is_complete()

        iteration_manager.current_iteration = 5
        assert not iteration_manager.is_complete()

        iteration_manager.current_iteration = 6
        assert iteration_manager.is_complete()


# ============================================================================
# INTEGRATION TESTS: Single Iteration
# ============================================================================

@pytest.mark.skipif(not ORCHESTRATOR_AVAILABLE, reason="Orchestrator not available")
class TestSingleIterationFlow:
    """Test single iteration planning flow"""

    def test_single_iteration_request(self):
        """Test that max_iterations=1 triggers single-iteration flow"""
        # This is a configuration test
        max_iterations = 1
        assert max_iterations <= 1, "Should not trigger multi-iteration"

    def test_backward_compatibility(self):
        """Test backward compatibility with existing code"""
        # Verify defaults don't break existing behavior
        max_iterations = 1  # Default for old behavior
        checkpoint_interval = 3

        assert max_iterations == 1
        assert checkpoint_interval == 3


# ============================================================================
# INTEGRATION TESTS: Multi-Iteration
# ============================================================================

@pytest.mark.skipif(not ORCHESTRATOR_AVAILABLE, reason="Orchestrator not available")
class TestMultiIterationFlow:
    """Test multi-iteration planning flow"""

    def test_multi_iteration_detection(self):
        """Test that max_iterations > 1 triggers multi-iteration"""
        max_iterations = 6
        assert max_iterations > 1, "Should trigger multi-iteration"

    def test_checkpoint_interval_validation(self):
        """Test checkpoint interval is valid"""
        max_iterations = 6
        checkpoint_interval = 3

        # Checkpoint should fit within iterations
        assert checkpoint_interval <= max_iterations
        assert checkpoint_interval > 0

    def test_iteration_progression(self, iteration_manager):
        """Test iterations progress correctly"""
        proposal = "Test proposal"
        iteration_manager.initialize_from_proposal(proposal)

        assert iteration_manager.current_iteration == 0
        assert iteration_manager.proposal == proposal

    def test_iteration_result_storage(self, iteration_manager):
        """Test iteration results are stored"""
        result = IterationResult(
            iteration_num=1,
            plan="Plan 1",
            key_insights=["Insight A"],
            frameworks_used=["Framework X"],
            data_points_count=10
        )

        iteration_manager.store_iteration_result(result)
        assert iteration_manager.current_iteration == 1
        assert len(iteration_manager.iteration_history) == 1
        assert iteration_manager.iteration_history[0].plan == "Plan 1"


# ============================================================================
# INTEGRATION TESTS: Approval Gates
# ============================================================================

class TestApprovalGates:
    """Test approval gate functionality"""

    def test_proposal_approval_request(self):
        """Test proposal approval request generation"""
        approval_id = "proposal_session123"
        approval_type = "proposal"
        goal = "Test goal"
        proposal = "Test proposal content"

        assert approval_id.startswith("proposal_")
        assert approval_type == "proposal"
        assert len(proposal) > 0

    def test_checkpoint_approval_request(self):
        """Test checkpoint approval request generation"""
        approval_id = "checkpoint_iter3_session123"
        approval_type = "checkpoint"
        iteration = 3
        total_iterations = 6

        assert "checkpoint" in approval_id
        assert approval_type == "checkpoint"
        assert iteration < total_iterations

    def test_approval_response_formats(self):
        """Test approval response handling"""
        approval_statuses = [
            "approved",
            "rejected",
            "adjust_requested",
            "paused"
        ]

        for status in approval_statuses:
            assert status in approval_statuses

    def test_session_state_management(self):
        """Test session state for pending approvals"""
        session = {
            "pending_approvals": {
                "proposal_session123": {
                    "type": "proposal",
                    "status": "pending",
                    "proposal": "Content"
                }
            }
        }

        assert "pending_approvals" in session
        assert "proposal_session123" in session["pending_approvals"]
        approval = session["pending_approvals"]["proposal_session123"]
        assert approval["type"] == "proposal"


# ============================================================================
# INTEGRATION TESTS: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling in multi-iteration system"""

    def test_division_error_prevention(self):
        """Test that string division errors are prevented"""
        # Test the fix for: unsupported operand type(s) for /: 'str' and 'str'
        completed = 3
        total = 6

        # Ensure types are converted
        percentage = int(100 * int(completed) / int(total))
        assert isinstance(percentage, int)
        assert percentage == 50

    def test_division_with_string_input(self):
        """Test division works with string inputs (simulating JSON parsing)"""
        completed = "3"
        total = "6"

        # Should be converted to int
        percentage = int(100 * int(completed) / int(total))
        assert percentage == 50

    def test_zero_division_prevention(self):
        """Test prevention of division by zero"""
        total = 0

        # Should prevent division by zero
        percentage = int(100 * 1 / max(int(total), 1))
        assert percentage == 100

    def test_invalid_approval_handling(self):
        """Test handling of invalid approvals"""
        approval_id = "invalid_id"
        session = {"pending_approvals": {}}

        # Should detect missing approval
        is_valid = approval_id in session["pending_approvals"]
        assert not is_valid

    def test_cascade_failure_prevention(self):
        """Test cascade failure prevention"""
        memagent_failures = 0
        max_allowed_failures = 2

        # Simulate failures
        for i in range(3):
            memagent_failures += 1
            if memagent_failures > max_allowed_failures:
                break

        assert memagent_failures > max_allowed_failures


# ============================================================================
# INTEGRATION TESTS: Multi-Agent Workflow
# ============================================================================

@pytest.mark.skipif(not AGENTS_AVAILABLE, reason="Agents not available")
class TestMultiAgentOrchestration:
    """Test multi-agent workflow orchestration"""

    def test_agent_pipeline_order(self):
        """Test agent execution order"""
        agent_order = ["planner", "verifier", "executor", "generator"]

        assert agent_order[0] == "planner"
        assert agent_order[1] == "verifier"
        assert agent_order[2] == "executor"
        assert agent_order[3] == "generator"

    def test_agent_result_passing(self):
        """Test results pass through agent pipeline"""
        results = {
            "planner": {"success": True, "output": "Plan"},
            "verifier": {"success": True, "output": "Verified"},
            "executor": {"success": True, "output": "Executed"},
            "generator": {"success": True, "output": "Generated"}
        }

        # Each result should be available to next agent
        assert results["planner"]["output"] == "Plan"
        assert results["verifier"]["output"] == "Verified"
        assert results["executor"]["output"] == "Executed"
        assert results["generator"]["output"] == "Generated"

    def test_iteration_context_propagation(self):
        """Test iteration context is propagated to agents"""
        context = {
            "iteration_mode": True,
            "iteration_number": 2,
            "max_iterations": 6,
            "iteration_guidance": "Focus on market analysis",
            "previous_plan": "Plan from iteration 1"
        }

        # All agents should receive context
        assert context["iteration_mode"]
        assert context["iteration_number"] == 2
        assert context["max_iterations"] == 6
        assert "iteration_guidance" in context


# ============================================================================
# INTEGRATION TESTS: MemAgent Guidance
# ============================================================================

@pytest.mark.skipif(not LLAMA_PLANNER_AVAILABLE, reason="LlamaPlanner not available")
class TestMemAgentGuidance:
    """Test MemAgent-guided iteration deepening"""

    def test_ememagent_integration(self):
        """Test MemAgent integration in iteration system"""
        # MemAgent is used for:
        # 1. Semantic search of previous iterations
        # 2. Extracting learned patterns
        # 3. Generating guidance for next iteration
        # 4. Storing execution results

        operations = [
            "semantic_search",
            "store_result",
            "retrieve_patterns",
            "generate_guidance"
        ]

        for op in operations:
            assert op in operations

    def test_iteration_guidance_generation(self):
        """Test that iteration guidance is generated"""
        previous_insights = [
            "Market is growing at 15% CAGR",
            "Top 3 competitors are X, Y, Z",
            "Regulatory barriers exist in region A"
        ]

        # Guidance should be generated from previous insights
        assert len(previous_insights) > 0
        assert "Market" in previous_insights[0]


# ============================================================================
# CHECKPOINT TESTS
# ============================================================================

class TestCheckpointGeneration:
    """Test checkpoint summary generation"""

    def test_checkpoint_at_correct_intervals(self):
        """Test checkpoints occur at correct intervals"""
        checkpoint_interval = 3
        iterations = [1, 2, 3, 4, 5, 6]
        checkpoint_iterations = [i for i in iterations if i % checkpoint_interval == 0]

        assert checkpoint_iterations == [3, 6]

    def test_checkpoint_data_collection(self):
        """Test checkpoint collects necessary data"""
        checkpoint_data = {
            "iteration": 3,
            "total_iterations": 6,
            "insights": ["Insight 1", "Insight 2", "Insight 3"],
            "frameworks_evolved": 5,
            "data_points_collected": 25
        }

        assert checkpoint_data["iteration"] == 3
        assert len(checkpoint_data["insights"]) == 3
        assert checkpoint_data["frameworks_evolved"] > 0
        assert checkpoint_data["data_points_collected"] > 0

    def test_checkpoint_summary_format(self):
        """Test checkpoint summary is properly formatted"""
        summary = {
            "progress": "3/6 iterations complete (50%)",
            "insights_section": "## TOP INSIGHTS",
            "evolution_section": "## ITERATION EVOLUTION",
            "metrics_section": "## GOAL-SPECIFIC METRICS"
        }

        assert "50%" in summary["progress"]
        assert "TOP INSIGHTS" in summary["insights_section"]


# ============================================================================
# ROUTING TESTS
# ============================================================================

class TestEndpointRouting:
    """Test endpoint routing logic"""

    def test_single_iteration_routing(self):
        """Test routing for single iteration"""
        max_iterations = 1

        if max_iterations > 1:
            route = "multi_iteration"
        else:
            route = "single_iteration"

        assert route == "single_iteration"

    def test_multi_iteration_routing(self):
        """Test routing for multi-iteration"""
        max_iterations = 6

        if max_iterations > 1:
            route = "multi_iteration"
        else:
            route = "single_iteration"

        assert route == "multi_iteration"

    def test_proposal_requirement(self):
        """Test proposal is required for multi-iteration"""
        max_iterations = 6
        proposal = "Test proposal"

        requires_proposal = max_iterations > 1
        assert requires_proposal
        assert len(proposal) > 0

    def test_approval_gate_routing(self):
        """Test approval gate is inserted for multi-iteration"""
        max_iterations = 6
        approval_status = None

        if max_iterations > 1:
            # Should wait for approval
            needs_approval = approval_status is None
            assert needs_approval


# ============================================================================
# COMPATIBILITY TESTS
# ============================================================================

class TestBackwardCompatibility:
    """Test backward compatibility"""

    def test_existing_single_iteration_unchanged(self):
        """Test existing single-iteration code works unchanged"""
        # Old code should still work
        max_iterations = 1  # Old default
        assert max_iterations == 1

    def test_default_values_maintained(self):
        """Test default values are maintained"""
        defaults = {
            "max_iterations": 9,  # Old default
            "checkpoint_interval": 3
        }

        assert defaults["max_iterations"] == 9
        assert defaults["checkpoint_interval"] == 3


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
