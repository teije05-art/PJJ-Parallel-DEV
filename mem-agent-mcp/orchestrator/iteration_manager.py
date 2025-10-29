"""
Iteration Manager - Multi-Iteration Planning with MemAgent Guidance

This module manages multi-iteration planning loops where each iteration is shaped by
MemAgent's semantic understanding of previous iterations. Critical principle:
NOT repetition - EVOLUTION.

Each iteration builds on previous through intelligent memory retrieval and guidance,
creating progressively deeper and more tailored plans.

Author: Claude Code
Date: October 29, 2025
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class IterationResult:
    """Result from a single planning iteration."""
    iteration_num: int
    plan: str
    key_insights: List[str] = field(default_factory=list)
    frameworks_used: List[str] = field(default_factory=list)
    data_points_count: int = 0
    execution_timestamp: str = ""
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Ensure timestamp is set."""
        if not self.execution_timestamp:
            self.execution_timestamp = datetime.now().isoformat()


class IterationManager:
    """
    Manages multi-iteration planning loops with MemAgent-guided refinement.

    Core responsibility: Track iteration state and use MemAgent to actively guide
    each iteration based on learnings from previous iterations.

    Not just running the same workflow multiple times, but evolving the plan
    through intelligent semantic guidance from the memory system.

    Attributes:
        max_iterations: Total iterations to execute (e.g., 6)
        checkpoint_interval: Checkpoint every N iterations (e.g., 3)
        llama_planner: LlamaPlanner instance (MemAgent wrapper)
        goal: Original planning goal
        current_iteration: Current iteration number (0-based counter)
        iteration_history: List of all completed iteration results
    """

    def __init__(self, max_iterations: int, checkpoint_interval: int,
                 llama_planner, goal: str):
        """
        Initialize iteration manager.

        Args:
            max_iterations: Total iterations to run (e.g., 6, 20)
            checkpoint_interval: Checkpoint every N iterations (e.g., 3)
            llama_planner: LlamaPlanner instance for MemAgent access
            goal: Original user's planning goal

        Raises:
            ValueError: If parameters are invalid
        """
        if max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")
        if checkpoint_interval < 1:
            raise ValueError("checkpoint_interval must be >= 1")
        if llama_planner is None:
            raise ValueError("llama_planner cannot be None")
        if not goal:
            raise ValueError("goal cannot be empty")

        self.max_iterations = max_iterations
        self.checkpoint_interval = checkpoint_interval
        self.llama_planner = llama_planner
        self.goal = goal

        # State tracking
        self.current_iteration = 0  # Iterations completed
        self.iteration_history: List[IterationResult] = []
        self.checkpoint_count = 0
        self.proposal = None

        # Memory naming for this planning session
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.memory_entity_prefix = f"planning_session_{self.session_id}"

    # ==================== INITIALIZATION ====================

    def initialize_from_proposal(self, proposal: str) -> None:
        """
        Initialize iteration loop with the approved proposal.

        This is the starting point. The proposal serves as the foundation,
        and iteration 1 builds from it. MemAgent stores it for reference
        by subsequent iterations.

        Args:
            proposal: The user-approved proposal to build iterations from
        """
        if not proposal:
            raise ValueError("proposal cannot be empty")

        self.proposal = proposal

        # Store proposal in MemAgent for semantic retrieval
        try:
            self.llama_planner.store_entity(
                entity_name=f"{self.memory_entity_prefix}_proposal",
                content=proposal
            )
        except Exception as e:
            # Log but don't fail - proceed without MemAgent if needed
            print(f"Warning: Could not store proposal in MemAgent: {e}")

    # ==================== ITERATION GUIDANCE ====================

    def get_iteration_guidance(self) -> str:
        """
        Get MemAgent-guided context for current iteration.

        CRITICAL: This is where MemAgent actively guides iteration N based on N-1.
        Uses semantic search to understand what was learned, not just array indexing.

        Returns:
            Markdown-formatted guidance string for the iteration
        """
        if self.current_iteration == 0:
            raise RuntimeError("Call get_next_iteration_number() first")

        iteration_num = self.current_iteration + 1

        if iteration_num == 1:
            # Iteration 1: Build from proposal
            guidance = f"""## ITERATION 1 OF {self.max_iterations}

**Starting point:** The approved proposal above

**Your task:** Create the first strategic plan iteration based on the proposal.

**Focus areas:**
- Establish foundational strategy and key pillars
- Identify critical data gaps for research
- Apply primary domain-specific frameworks
- Extract initial market, competitive, and regulatory data points

**Remember:** This is the foundation. Set the stage for deeper analysis in subsequent iterations.
"""
            return guidance

        else:
            # Iteration N>1: MemAgent-GUIDED REFINEMENT
            # This is the key difference - semantic guidance, not repetition

            previous_iteration = self.iteration_history[-1]
            iteration_num = self.current_iteration + 1

            # STEP 1: Query MemAgent for semantic understanding of prior learnings
            previous_insights_retrieval = self._retrieve_previous_insights()

            # STEP 2: Format the guidance
            guidance = f"""## ITERATION {iteration_num} OF {self.max_iterations}

**Based on MemAgent semantic retrieval of iteration {iteration_num - 1}:**

{previous_insights_retrieval}

**Frameworks applied in prior iterations:**
{self._format_frameworks_used_so_far()}

**Data extraction progress:**
- Total data points extracted so far: {self._count_total_data_points()}
- Frameworks applied: {self._count_unique_frameworks()}

**YOUR TASK THIS ITERATION:**

Deepen and refine the strategy from iteration {iteration_num - 1}.

**Critical:** Do NOT repeat previous analysis. Use MemAgent's insights above to guide your focus.

**What to do differently:**
- Build on frameworks already established (referenced above)
- Go deeper into areas needing more specificity
- Add NEW frameworks that complement prior analysis
- Extract additional data that supports, challenges, or refines prior findings
- Increase specificity and tactical detail

**Output quality check:**
This iteration should be DISTINCTLY DIFFERENT from iteration {iteration_num - 1} -
not a repetition, but an evolution based on what was learned.

**Remember:** You are guided by MemAgent's understanding of previous iterations.
Use those insights to inform your strategy refinement.
"""
            return guidance

    def _retrieve_previous_insights(self) -> str:
        """
        Retrieve previous iteration insights using MemAgent semantic search.

        This is what makes iterations LEARN from each other.
        Uses semantic search to find relevant insights, not just key_insights field.

        Returns:
            Formatted string of previous insights, or fallback if search fails
        """
        try:
            iteration_num = self.current_iteration
            previous_iteration = self.iteration_history[-1]

            # Query MemAgent semantically
            # This query is designed to surface what was LEARNED, not just what was done
            query = f"""Key insights, findings, and learnings from planning iteration {iteration_num}
            for goal: {self.goal}. What did we discover? What changed our understanding?"""

            retrieved_insights = self.llama_planner.search_similar(
                query=query,
                max_results=5
            )

            if retrieved_insights:
                formatted = "**MemAgent-retrieved insights from previous iteration:**\n"
                for i, insight in enumerate(retrieved_insights, 1):
                    formatted += f"- {insight}\n"
                return formatted
            else:
                # Fallback: Use stored key_insights
                return self._fallback_previous_insights(previous_iteration)

        except Exception as e:
            # Fallback if semantic search fails
            print(f"Warning: MemAgent semantic search failed: {e}")
            previous_iteration = self.iteration_history[-1]
            return self._fallback_previous_insights(previous_iteration)

    def _fallback_previous_insights(self, previous_iteration: IterationResult) -> str:
        """Fallback formatting if MemAgent search fails."""
        if previous_iteration.key_insights:
            formatted = "**Insights from previous iteration (direct storage):**\n"
            for insight in previous_iteration.key_insights[:5]:  # Top 5 insights
                formatted += f"- {insight}\n"
            return formatted
        else:
            return "**Previous iteration insights:** Insights were stored in MemAgent memory.\n"

    def _format_frameworks_used_so_far(self) -> str:
        """Format frameworks used across all iterations so far."""
        all_frameworks = set()
        for result in self.iteration_history:
            all_frameworks.update(result.frameworks_used)

        if all_frameworks:
            return "\n".join([f"- {fw}" for fw in sorted(all_frameworks)])
        else:
            return "- No frameworks stored yet (will be extracted from agent output)"

    def _count_total_data_points(self) -> int:
        """Count total data points extracted across all iterations."""
        return sum(result.data_points_count for result in self.iteration_history)

    def _count_unique_frameworks(self) -> int:
        """Count unique frameworks applied across all iterations."""
        all_frameworks = set()
        for result in self.iteration_history:
            all_frameworks.update(result.frameworks_used)
        return len(all_frameworks)

    # ==================== CONTEXT ENHANCEMENT ====================

    def get_iteration_context(self, original_context: Dict) -> Dict:
        """
        Enhance context with iteration-specific guidance and previous iteration data.

        This is the injection point for MemAgent-guided context. The enhanced context
        is passed to workflow_coordinator and agents, giving them the full picture.

        Args:
            original_context: Base context (goal, memory search, web search, etc.)

        Returns:
            Enhanced context with iteration guidance and previous iteration data
        """
        context = original_context.copy()
        context['iteration_number'] = self.current_iteration + 1
        context['max_iterations'] = self.max_iterations
        context['iteration_guidance'] = self.get_iteration_guidance()

        # Include previous iteration context (for agents to reference)
        if self.current_iteration > 0:
            previous_result = self.iteration_history[-1]
            context['previous_plan'] = previous_result.plan
            context['previous_insights'] = previous_result.key_insights
            context['previous_frameworks'] = previous_result.frameworks_used
            context['previous_data_points'] = previous_result.data_points_count
        else:
            # Iteration 1: Include proposal as the baseline
            context['previous_plan'] = self.proposal
            context['previous_insights'] = []
            context['previous_frameworks'] = []
            context['previous_data_points'] = 0

        # Flag that we're in iteration mode (agents check this)
        context['iteration_mode'] = True

        return context

    # ==================== RESULT STORAGE ====================

    def store_iteration_result(self, iteration_result: IterationResult) -> None:
        """
        Store iteration result to both local history AND MemAgent.

        CRITICAL: MemAgent storage makes insights semantically searchable for
        next iteration. This is what enables learning between iterations.

        Args:
            iteration_result: IterationResult object from agent execution
        """
        if iteration_result.iteration_num != self.current_iteration + 1:
            raise ValueError(
                f"Iteration number mismatch. Expected {self.current_iteration + 1}, "
                f"got {iteration_result.iteration_num}"
            )

        # Store locally
        self.iteration_history.append(iteration_result)
        self.current_iteration += 1

        # Store to MemAgent for semantic retrieval in next iteration
        entity_name = f"{self.memory_entity_prefix}_iteration_{iteration_result.iteration_num}"

        iteration_storage = self._format_iteration_for_storage(iteration_result)

        try:
            self.llama_planner.store_entity(
                entity_name=entity_name,
                content=iteration_storage
            )
        except Exception as e:
            print(f"Warning: Could not store iteration to MemAgent: {e}")
            # Continue anyway - local storage is sufficient fallback

    def _format_iteration_for_storage(self, result: IterationResult) -> str:
        """Format iteration result for MemAgent storage."""
        return f"""# Planning Iteration {result.iteration_num}

**Goal:** {self.goal}
**Timestamp:** {result.execution_timestamp}

## Key Insights
{self._format_list(result.key_insights) if result.key_insights else "- No insights extracted"}

## Frameworks Applied
{self._format_list(result.frameworks_used) if result.frameworks_used else "- No frameworks recorded"}

## Data Points Extracted
Count: {result.data_points_count} key figures and metrics

## Full Plan Content
{result.plan}

## Metadata
{self._format_metadata(result.metadata)}

---

*This iteration was stored to MemAgent for semantic retrieval and guidance of subsequent iterations.*
"""

    # ==================== STATE QUERIES ====================

    def should_checkpoint(self) -> bool:
        """
        Check if current iteration is a checkpoint.

        Returns:
            True if we should present a checkpoint summary to user
        """
        if self.current_iteration == 0:
            return False
        return self.current_iteration % self.checkpoint_interval == 0

    def at_final_iteration(self) -> bool:
        """Check if we've reached the final iteration."""
        return self.current_iteration >= self.max_iterations

    def get_next_iteration_number(self) -> int:
        """Get the next iteration number to execute (1-indexed)."""
        return self.current_iteration + 1

    def get_remaining_iterations(self) -> int:
        """Get number of iterations remaining."""
        return self.max_iterations - self.current_iteration

    def get_iterations_until_checkpoint(self) -> int:
        """Get iterations until next checkpoint."""
        if self.current_iteration == 0:
            next_checkpoint = self.checkpoint_interval
        else:
            next_checkpoint = ((self.current_iteration // self.checkpoint_interval) + 1) * self.checkpoint_interval
        return next_checkpoint - self.current_iteration

    def get_next_checkpoint_number(self) -> int:
        """Get the iteration number of the next checkpoint."""
        if self.current_iteration == 0:
            return self.checkpoint_interval
        else:
            return ((self.current_iteration // self.checkpoint_interval) + 1) * self.checkpoint_interval

    # ==================== PROGRESS REPORTING ====================

    def get_iteration_summary(self) -> str:
        """
        Get human-readable summary of iteration progress.

        Returns:
            Formatted progress summary string
        """
        if self.current_iteration == 0:
            next_checkpoint = self.checkpoint_interval
            until_checkpoint = self.checkpoint_interval
        else:
            next_checkpoint = self.get_next_checkpoint_number()
            until_checkpoint = self.get_iterations_until_checkpoint()

        summary = f"""
ITERATION PROGRESS: {self.current_iteration}/{self.max_iterations}

**Completed:** {self.current_iteration} iteration{'s' if self.current_iteration != 1 else ''}
**Remaining:** {self.get_remaining_iterations()} iteration{'s' if self.get_remaining_iterations() != 1 else ''}

**Checkpoints passed:** {self.checkpoint_count}
**Next checkpoint:** Iteration {next_checkpoint} ({until_checkpoint} iteration{'s' if until_checkpoint != 1 else ''} away)

**Aggregate statistics:**
- Unique frameworks applied: {self._count_unique_frameworks()}
- Total data points extracted: {self._count_total_data_points()}
- Iterations with insights: {len([r for r in self.iteration_history if r.key_insights])}
"""
        return summary.strip()

    def get_iteration_history_summary(self) -> List[Dict]:
        """
        Get summary of all completed iterations.

        Returns:
            List of dicts with iteration number, key metrics
        """
        summary = []
        for result in self.iteration_history:
            summary.append({
                'iteration': result.iteration_num,
                'frameworks': result.frameworks_used,
                'data_points': result.data_points_count,
                'insights_count': len(result.key_insights),
                'timestamp': result.execution_timestamp
            })
        return summary

    def get_cumulative_metrics(self) -> Dict:
        """
        Get cumulative metrics across all iterations.

        Returns:
            Dict with aggregated metrics
        """
        all_frameworks = set()
        total_data_points = 0
        total_insights = 0

        for result in self.iteration_history:
            all_frameworks.update(result.frameworks_used)
            total_data_points += result.data_points_count
            total_insights += len(result.key_insights)

        return {
            'iterations_completed': self.current_iteration,
            'max_iterations': self.max_iterations,
            'unique_frameworks': len(all_frameworks),
            'total_data_points': total_data_points,
            'total_insights': total_insights,
            'average_data_points_per_iteration': int(total_data_points) / max(int(self.current_iteration), 1),
            'checkpoints_passed': self.checkpoint_count
        }

    # ==================== CHECKPOINT MANAGEMENT ====================

    def mark_checkpoint_complete(self) -> None:
        """
        Mark that a checkpoint has been passed and approved by user.
        Called after user approval at checkpoint.
        """
        self.checkpoint_count += 1

    # ==================== UTILITY METHODS ====================

    def _format_list(self, items: List[str]) -> str:
        """Format list for markdown."""
        if not items:
            return "None"
        return "\n".join([f"- {item}" for item in items])

    def _format_metadata(self, metadata: Dict) -> str:
        """Format metadata dict for storage."""
        if not metadata:
            return "No metadata"
        lines = []
        for key, value in metadata.items():
            if isinstance(value, (dict, list)):
                lines.append(f"**{key}:** {json.dumps(value)}")
            else:
                lines.append(f"**{key}:** {value}")
        return "\n".join(lines)

    # ==================== EXPORT ====================

    def export_state(self) -> Dict:
        """
        Export iteration manager state for debugging/logging.

        Returns:
            Dict with complete state snapshot
        """
        return {
            'session_id': self.session_id,
            'goal': self.goal,
            'max_iterations': self.max_iterations,
            'checkpoint_interval': self.checkpoint_interval,
            'current_iteration': self.current_iteration,
            'checkpoint_count': self.checkpoint_count,
            'cumulative_metrics': self.get_cumulative_metrics(),
            'iteration_history': self.get_iteration_history_summary()
        }


# ==================== MODULE-LEVEL EXPORTS ====================

__all__ = ['IterationManager', 'IterationResult']
