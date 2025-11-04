"""Flow-GRPO Training for Project Jupiter

Phase 3 Implementation: Mid-iteration learning with reinforcement signals
- Records iteration outcomes (flow scores)
- Updates agent selection weights
- Tracks pattern effectiveness
- Optimizes agent coordination

Reference: AgentFlow with Flow-GRPO (lupantech/AgentFlow)
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import json


@dataclass
class IterationSignal:
    """Training signal from a single planning iteration."""
    iteration: int
    agent_name: str
    verification_quality: float  # 0-1, how well did verification go?
    user_approved: bool  # Did user approve the plan?
    reasoning_quality: float  # 0-1, how good was the reasoning?
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def calculate_flow_score(self) -> float:
        """Calculate the flow score (training reward) for this iteration.

        Formula: flow_score = verification × approval_bonus × reasoning_quality
        """
        approval_bonus = 1.0 if self.user_approved else 0.5
        flow_score = (
            self.verification_quality * 0.4 +
            (1.0 if self.user_approved else 0.0) * 0.4 +
            self.reasoning_quality * 0.2
        )
        return min(1.0, max(0.0, flow_score))


class FlowGRPOTrainer:
    """Trains agent selection and pattern effectiveness using Flow-GRPO.

    Key Features:
    - Mid-iteration learning (not batch at end)
    - Agent weight updates based on performance
    - Pattern effectiveness tracking
    - Exponential moving average for recent iterations

    Design:
    - Each iteration produces a flow_score (0-1)
    - Agent weights are updated: w = w + α × (flow_score - baseline)
    - Recent iterations weighted more heavily
    - Graceful degradation for low-performing agents
    """

    def __init__(self,
                 learning_rate: float = 0.05,
                 baseline_score: float = 0.5,
                 min_agent_weight: float = 0.1):
        """Initialize Flow-GRPO trainer.

        Args:
            learning_rate: How much to adjust weights per iteration (0.01 - 0.1)
            baseline_score: Expected baseline performance (0-1)
            min_agent_weight: Minimum weight for agents (prevent deletion)
        """
        self.learning_rate = learning_rate
        self.baseline_score = baseline_score
        self.min_agent_weight = min_agent_weight

        # Agent selection weights (start equal)
        self.agent_selection_weights: Dict[str, float] = {
            'planner': 1.0,
            'verifier': 1.0,
            'executor': 1.0,
            'generator': 1.0,
        }

        # Pattern tracking
        self.pattern_scores: Dict[str, float] = {}  # pattern_name → effectiveness score
        self.pattern_usage_count: Dict[str, int] = defaultdict(int)

        # Training history
        self.iteration_signals: List[IterationSignal] = []
        self.weight_history: Dict[str, List[Tuple[int, float]]] = defaultdict(list)  # agent → [(iteration, weight)]

        # Exponential moving average
        self.ema_alpha = 0.3  # Higher = more weight to recent iterations

        print(f"✅ FlowGRPOTrainer initialized (lr={learning_rate}, baseline={baseline_score})")

    def record_iteration_signal(self,
                               iteration: int,
                               agent_name: str,
                               verification_quality: float,
                               user_approved: bool,
                               reasoning_quality: float) -> float:
        """Record training signal from one iteration.

        Args:
            iteration: Iteration number
            agent_name: Which agent this signal is for
            verification_quality: How well did verification go? (0-1)
            user_approved: Did user approve the plan?
            reasoning_quality: How good was reasoning? (0-1)

        Returns:
            Calculated flow_score
        """
        signal = IterationSignal(
            iteration=iteration,
            agent_name=agent_name,
            verification_quality=verification_quality,
            user_approved=user_approved,
            reasoning_quality=reasoning_quality,
        )

        flow_score = signal.calculate_flow_score()
        self.iteration_signals.append(signal)

        # Update agent weight
        self._update_agent_weight(agent_name, flow_score)

        print(f"   📊 Flow-GRPO: {agent_name} flow_score={flow_score:.2f} → "
              f"weight={self.agent_selection_weights[agent_name]:.2f}")

        return flow_score

    def record_pattern_performance(self,
                                  pattern_name: str,
                                  flow_score: float,
                                  verification_passed: bool,
                                  user_approved: bool) -> None:
        """Record how well a pattern performed.

        Args:
            pattern_name: Name of the pattern used
            flow_score: Overall flow score for this iteration
            verification_passed: Did verification pass?
            user_approved: Did user approve?
        """
        # Calculate pattern effectiveness
        pattern_effectiveness = (
            flow_score * 0.5 +
            (1.0 if verification_passed else 0.0) * 0.3 +
            (1.0 if user_approved else 0.0) * 0.2
        )

        if pattern_name not in self.pattern_scores:
            self.pattern_scores[pattern_name] = pattern_effectiveness
        else:
            # Exponential moving average
            self.pattern_scores[pattern_name] = (
                self.ema_alpha * pattern_effectiveness +
                (1 - self.ema_alpha) * self.pattern_scores[pattern_name]
            )

        self.pattern_usage_count[pattern_name] += 1

        print(f"   🎯 Pattern '{pattern_name}': effectiveness={self.pattern_scores[pattern_name]:.2f}")

    def get_recommended_agent_sequence(self) -> List[Tuple[str, float]]:
        """Get agents sorted by selection weight (highest first).

        Returns:
            List of (agent_name, weight) tuples
        """
        sorted_agents = sorted(
            self.agent_selection_weights.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_agents

    def get_top_patterns(self, top_k: int = 3) -> List[Tuple[str, float]]:
        """Get top patterns by effectiveness.

        Args:
            top_k: Number of patterns to return

        Returns:
            List of (pattern_name, score) tuples
        """
        sorted_patterns = sorted(
            self.pattern_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_patterns[:top_k]

    def update_agent_weights(self) -> None:
        """Update all agent weights based on recent signals.

        Should be called periodically (e.g., after each iteration).
        """
        if not self.iteration_signals:
            return

        # Group signals by agent
        agent_signals: Dict[str, List[IterationSignal]] = defaultdict(list)
        for signal in self.iteration_signals:
            agent_signals[signal.agent_name].append(signal)

        # Update each agent's weight
        for agent_name, signals in agent_signals.items():
            if not signals:
                continue

            # Calculate average flow score for this agent
            avg_flow_score = sum(s.calculate_flow_score() for s in signals) / len(signals)

            # Weight recent iterations more
            recent_flow_score = signals[-1].calculate_flow_score() if signals else avg_flow_score

            # Use EMA
            ema_flow = self.ema_alpha * recent_flow_score + (1 - self.ema_alpha) * avg_flow_score

            # Update weight
            self._update_agent_weight(agent_name, ema_flow)

    def get_agent_weights(self) -> Dict[str, float]:
        """Get current agent selection weights.

        Returns:
            Dictionary mapping agent names to weights
        """
        return dict(self.agent_selection_weights)

    def should_skip_agent(self, agent_name: str, threshold: float = 0.2) -> bool:
        """Check if an agent should be skipped due to low performance.

        Args:
            agent_name: Agent to check
            threshold: Weight threshold below which to skip

        Returns:
            True if agent should be skipped
        """
        weight = self.agent_selection_weights.get(agent_name, 0.5)
        return weight < threshold

    def get_training_summary(self) -> Dict[str, Any]:
        """Get summary of training progress.

        Returns:
            Dictionary with training stats
        """
        if not self.iteration_signals:
            return {'total_iterations': 0}

        flow_scores = [s.calculate_flow_score() for s in self.iteration_signals]
        avg_flow = sum(flow_scores) / len(flow_scores) if flow_scores else 0.0
        max_flow = max(flow_scores) if flow_scores else 0.0
        min_flow = min(flow_scores) if flow_scores else 0.0

        approval_count = sum(1 for s in self.iteration_signals if s.user_approved)

        return {
            'total_iterations': len(self.iteration_signals),
            'avg_flow_score': avg_flow,
            'max_flow_score': max_flow,
            'min_flow_score': min_flow,
            'approvals': f"{approval_count}/{len(self.iteration_signals)}",
            'approval_rate': approval_count / len(self.iteration_signals) if self.iteration_signals else 0.0,
            'top_agents': dict(self.get_recommended_agent_sequence()[:2]),
            'top_patterns': dict(self.get_top_patterns(2)),
        }

    def reset_weights(self) -> None:
        """Reset all weights to equal values."""
        for agent in self.agent_selection_weights:
            self.agent_selection_weights[agent] = 1.0
        print("   🔄 Agent weights reset to 1.0")

    # ========== INTERNAL METHODS ==========

    def _update_agent_weight(self, agent_name: str, flow_score: float) -> None:
        """Update a single agent's weight.

        Uses: w_new = w_old + α × (flow_score - baseline)

        Args:
            agent_name: Agent to update
            flow_score: Current flow score
        """
        if agent_name not in self.agent_selection_weights:
            self.agent_selection_weights[agent_name] = 1.0

        old_weight = self.agent_selection_weights[agent_name]

        # Adjustment based on how well agent did vs. baseline
        adjustment = self.learning_rate * (flow_score - self.baseline_score)
        new_weight = old_weight + adjustment

        # Clamp to minimum
        new_weight = max(self.min_agent_weight, new_weight)

        # Normalize so weights stay reasonable
        total_weight = sum(self.agent_selection_weights.values())
        if total_weight > 0:
            # Renormalize periodically
            if total_weight > 10:
                scale_factor = 4.0 / total_weight
                for agent in self.agent_selection_weights:
                    self.agent_selection_weights[agent] *= scale_factor

        self.agent_selection_weights[agent_name] = new_weight

        # Track history
        iteration = len(self.iteration_signals)
        self.weight_history[agent_name].append((iteration, new_weight))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize trainer state to dictionary."""
        return {
            'agent_selection_weights': self.agent_selection_weights,
            'pattern_scores': self.pattern_scores,
            'learning_rate': self.learning_rate,
            'baseline_score': self.baseline_score,
            'iteration_count': len(self.iteration_signals),
            'training_summary': self.get_training_summary(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlowGRPOTrainer':
        """Deserialize trainer from dictionary."""
        trainer = cls(
            learning_rate=data.get('learning_rate', 0.05),
            baseline_score=data.get('baseline_score', 0.5)
        )
        trainer.agent_selection_weights = data.get('agent_selection_weights', trainer.agent_selection_weights)
        trainer.pattern_scores = data.get('pattern_scores', {})
        return trainer
