"""Agent Coordination Learning for Project Jupiter

Phase 3 Implementation: Learn which agents work well together
- Tracks agent pair performance
- Learns optimal agent sequences
- Recommends dynamic agent pipelines
- Prevents inefficient combinations

Reference: AgentFlow learns agent coordination through performance feedback
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime


@dataclass
class AgentPairPerformance:
    """Performance metrics for an agent pair."""
    agent1: str
    agent2: str
    flow_scores: List[float] = field(default_factory=list)
    success_count: int = 0  # Number of successful interactions
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_average_score(self) -> float:
        """Get average flow score for this pair."""
        if not self.flow_scores:
            return 0.5
        return sum(self.flow_scores) / len(self.flow_scores)

    def get_success_rate(self) -> float:
        """Get success rate (0-1)."""
        if not self.flow_scores:
            return 0.5
        return self.success_count / len(self.flow_scores)


class AgentCoordination:
    """Learn which agents work well together.

    Key Features:
    - Tracks pairs of agents (e.g., Planner → Verifier)
    - Scores based on combined performance
    - Recommends optimal agent sequences
    - Prevents inefficient pipelines

    Design:
    - Each agent pair has a performance score
    - Scores updated based on flow_score outcomes
    - Sequences chosen to maximize total performance
    - Graceful fallback for new pairs
    """

    def __init__(self):
        """Initialize agent coordination tracker."""
        # Standard agent order (fallback)
        self.default_sequence = ['planner', 'verifier', 'executor', 'generator']

        # Track pair performances
        self.pair_performances: Dict[Tuple[str, str], AgentPairPerformance] = {}

        # Track sequence performance
        self.sequence_scores: Dict[Tuple[str, ...], List[float]] = defaultdict(list)

        # Agent availability flags
        self.agent_available: Dict[str, bool] = {
            'planner': True,
            'verifier': True,
            'executor': True,
            'generator': True,
        }

        print("✅ AgentCoordination initialized")

    def record_pair_performance(self,
                               agent1: str,
                               agent2: str,
                               flow_score: float,
                               success: bool = True) -> None:
        """Record performance of an agent pair.

        Args:
            agent1: First agent in pair
            agent2: Second agent in pair
            flow_score: How well did they work together? (0-1)
            success: Was this a successful interaction?
        """
        pair_key = (agent1, agent2)

        if pair_key not in self.pair_performances:
            self.pair_performances[pair_key] = AgentPairPerformance(
                agent1=agent1,
                agent2=agent2
            )

        perf = self.pair_performances[pair_key]
        perf.flow_scores.append(flow_score)
        if success:
            perf.success_count += 1

        print(f"   🔗 Agent pair ({agent1} → {agent2}): "
              f"score={flow_score:.2f}, avg={perf.get_average_score():.2f}")

    def record_sequence_performance(self,
                                   sequence: Tuple[str, ...],
                                   flow_score: float) -> None:
        """Record performance of a full agent sequence.

        Args:
            sequence: Tuple of agents in order
            flow_score: Overall performance (0-1)
        """
        self.sequence_scores[sequence].append(flow_score)

    def get_pair_score(self, agent1: str, agent2: str) -> float:
        """Get performance score for an agent pair.

        Args:
            agent1: First agent
            agent2: Second agent

        Returns:
            Score (0-1), 0.5 for untested pairs
        """
        pair_key = (agent1, agent2)

        if pair_key not in self.pair_performances:
            return 0.5  # Neutral score for untested pairs

        return self.pair_performances[pair_key].get_average_score()

    def recommend_agent_sequence(self,
                                available_agents: Optional[List[str]] = None,
                                max_sequence_length: int = 4) -> List[str]:
        """Recommend best agent sequence based on learned pair performances.

        Uses dynamic programming to find highest-scoring sequence.

        Args:
            available_agents: List of agents to consider (default: all)
            max_sequence_length: Maximum sequence length

        Returns:
            Recommended sequence of agent names
        """
        if available_agents is None:
            available_agents = self.default_sequence

        # Filter out unavailable agents
        available = [a for a in available_agents if self.agent_available.get(a, True)]

        if not available:
            return self.default_sequence

        # If we have learned sequences, use the best one
        if self.sequence_scores:
            best_sequence = max(
                self.sequence_scores.items(),
                key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0
            )
            return list(best_sequence[0])

        # Otherwise, construct best sequence using pair scores
        # Start with first agent
        sequence = [available[0]]

        # Greedily add best next agent
        while len(sequence) < min(max_sequence_length, len(available)):
            best_next_agent = None
            best_score = 0.0

            for agent in available:
                if agent not in sequence:
                    pair_score = self.get_pair_score(sequence[-1], agent)
                    if pair_score > best_score:
                        best_score = pair_score
                        best_next_agent = agent

            if best_next_agent:
                sequence.append(best_next_agent)
            else:
                # Add any remaining agent
                for agent in available:
                    if agent not in sequence:
                        sequence.append(agent)
                        break

        return sequence

    def should_skip_agent_pair(self, agent1: str, agent2: str,
                              threshold: float = 0.3) -> bool:
        """Check if a pair should be skipped due to low performance.

        Args:
            agent1: First agent
            agent2: Second agent
            threshold: Score threshold below which to skip

        Returns:
            True if pair should be skipped
        """
        pair_key = (agent1, agent2)

        if pair_key not in self.pair_performances:
            return False  # No data, don't skip

        score = self.pair_performances[pair_key].get_average_score()
        return score < threshold

    def mark_agent_unavailable(self, agent_name: str) -> None:
        """Mark an agent as temporarily unavailable.

        Args:
            agent_name: Agent to mark unavailable
        """
        self.agent_available[agent_name] = False
        print(f"   ⚠️ Agent '{agent_name}' marked unavailable")

    def mark_agent_available(self, agent_name: str) -> None:
        """Mark an agent as available again.

        Args:
            agent_name: Agent to mark available
        """
        self.agent_available[agent_name] = True
        print(f"   ✓ Agent '{agent_name}' marked available")

    def get_coordination_summary(self) -> Dict[str, Any]:
        """Get summary of agent coordination learning.

        Returns:
            Dictionary with coordination stats
        """
        if not self.pair_performances:
            return {
                'total_pairs_learned': 0,
                'recommended_sequence': self.default_sequence
            }

        pair_scores = {
            f"{p[0]}->{p[1]}": perf.get_average_score()
            for p, perf in self.pair_performances.items()
        }

        best_sequence = self.recommend_agent_sequence()

        return {
            'total_pairs_learned': len(self.pair_performances),
            'pair_scores': pair_scores,
            'recommended_sequence': best_sequence,
            'sequence_performance': {
                str(seq): sum(scores) / len(scores) if scores else 0
                for seq, scores in self.sequence_scores.items()
            } if self.sequence_scores else {},
        }

    def reset_learning(self) -> None:
        """Reset all learned coordination data."""
        self.pair_performances.clear()
        self.sequence_scores.clear()
        print("   🔄 Agent coordination learning reset")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize coordination state."""
        pair_data = {
            f"{p[0]}->{p[1]}": {
                'avg_score': perf.get_average_score(),
                'success_count': perf.success_count,
                'total_interactions': len(perf.flow_scores),
            }
            for p, perf in self.pair_performances.items()
        }

        sequence_data = {
            str(seq): {
                'avg_score': sum(scores) / len(scores) if scores else 0,
                'count': len(scores),
            }
            for seq, scores in self.sequence_scores.items()
        }

        return {
            'pair_performances': pair_data,
            'sequence_performance': sequence_data,
            'agent_availability': self.agent_available,
            'summary': self.get_coordination_summary(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentCoordination':
        """Deserialize coordination from dictionary."""
        coord = cls()

        # Restore availability
        coord.agent_available.update(data.get('agent_availability', {}))

        # Note: Full pair_performance restoration would require more data
        # This is a simplified restoration

        return coord
