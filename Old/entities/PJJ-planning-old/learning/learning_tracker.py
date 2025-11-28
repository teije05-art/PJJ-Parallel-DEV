"""
Learning Tracker - Pattern Recognition and Recommendations

Analyzes planning history to:
1. Identify successful approach patterns
2. Track approach effectiveness by goal type
3. Recommend approaches for similar future goals
4. Measure learning progress over time
"""

import json
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


class LearningTracker:
    """
    Analyzes planning outcomes to improve future decisions.

    What it tracks:
    - Approach ratio effectiveness (% memory vs % research)
    - Agent sequence quality
    - Time efficiency
    - User satisfaction trends
    - Goal type patterns
    """

    def __init__(self, learning_log_path: str):
        self.learning_log_path = learning_log_path
        self.outcomes = self._load_outcomes()
        self.patterns = {}
        self._analyze_patterns()

    def _load_outcomes(self) -> List[Dict]:
        """Load all recorded planning outcomes."""
        try:
            path = Path(self.learning_log_path)
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load outcomes: {e}")
        return []

    def _analyze_patterns(self) -> None:
        """Analyze all outcomes to identify patterns."""
        if not self.outcomes:
            return

        # Group by goal type
        self.patterns = self._group_by_goal_type()

        # Calculate patterns for each group
        for goal_type in self.patterns:
            outcomes = self.patterns[goal_type]
            self.patterns[goal_type] = self._analyze_goal_type(outcomes)

    def _group_by_goal_type(self) -> Dict[str, List[Dict]]:
        """
        Group outcomes by goal type.

        Goal type = first 3 words of goal (lowercase)
        """
        grouped = defaultdict(list)

        for outcome in self.outcomes:
            goal = outcome.get("goal", "")
            goal_words = goal.lower().split()[:3]
            goal_type = " ".join(goal_words)

            grouped[goal_type].append(outcome)

        return grouped

    def _analyze_goal_type(self, outcomes: List[Dict]) -> Dict:
        """
        Analyze outcomes for a specific goal type.

        Returns analysis with:
        - Approach statistics
        - Agent effectiveness
        - Quality metrics
        - Recommendations
        """

        if not outcomes:
            return {}

        # Extract approach details
        approaches = [o.get("approach", {}) for o in outcomes]
        memory_pcts = [a.get("memory_percentage", 0.5) for a in approaches]
        research_pcts = [a.get("research_percentage", 0.5) for a in approaches]
        agents_lists = [a.get("agents_to_use", []) for a in approaches]

        # Extract quality metrics
        ratings = [o.get("user_rating") for o in outcomes if o.get("user_rating")]
        quality_scores = [o.get("quality_score") for o in outcomes if o.get("quality_score")]

        # Calculate statistics
        memory_avg = sum(memory_pcts) / len(memory_pcts) if memory_pcts else 0.5
        memory_std = self._std_dev(memory_pcts) if len(memory_pcts) > 1 else 0.0
        research_avg = sum(research_pcts) / len(research_pcts) if research_pcts else 0.5
        research_std = self._std_dev(research_pcts) if len(research_pcts) > 1 else 0.0

        # Agent frequency analysis
        agent_frequency = Counter()
        for agents in agents_lists:
            agent_frequency.update(agents)

        # Quality analysis
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.5

        # Find best performing outcomes
        best_outcome = max(outcomes, key=lambda o: o.get("user_rating", 0))
        best_approach = best_outcome.get("approach", {})

        return {
            "sample_count": len(outcomes),
            "approach": {
                "memory_percentage": {
                    "average": round(memory_avg, 2),
                    "std_dev": round(memory_std, 2),
                    "recommended": round(memory_avg, 2)
                },
                "research_percentage": {
                    "average": round(research_avg, 2),
                    "std_dev": round(research_std, 2),
                    "recommended": round(research_avg, 2)
                }
            },
            "agents": {
                "most_common": [agent for agent, count in agent_frequency.most_common(3)],
                "frequency": dict(agent_frequency),
                "recommended_sequence": [agent for agent, count in agent_frequency.most_common(3)]
            },
            "quality": {
                "avg_user_rating": round(avg_rating, 1),
                "avg_quality_score": round(avg_quality, 2),
                "success_rate": round(len(ratings) / len(outcomes), 2) if outcomes else 0.0
            },
            "best_approach": {
                "memory": best_approach.get("memory_percentage"),
                "research": best_approach.get("research_percentage"),
                "agents": best_approach.get("agents_to_use"),
                "rating": best_outcome.get("user_rating")
            }
        }

    def get_recommendation(self, goal: str) -> Optional[Dict]:
        """
        Get recommended approach for a goal based on past patterns.

        Args:
            goal: User's goal statement

        Returns:
            Recommended approach dict, or None if no pattern found
        """

        # Extract goal type (first 3 words)
        goal_words = goal.lower().split()[:3]
        goal_type = " ".join(goal_words)

        # Look for exact or similar match
        matching_pattern = self.patterns.get(goal_type)

        if not matching_pattern or matching_pattern.get("sample_count", 0) < 2:
            return None  # Not enough data to recommend

        # Build recommendation
        recommendation = {
            "goal_type": goal_type,
            "confidence": min(0.5 + (matching_pattern.get("sample_count", 0) * 0.1), 1.0),
            "based_on_samples": matching_pattern.get("sample_count"),
            "suggested_approach": {
                "memory_percentage": matching_pattern["approach"]["memory_percentage"]["recommended"],
                "research_percentage": matching_pattern["approach"]["research_percentage"]["recommended"],
                "agents_to_use": matching_pattern["agents"]["recommended_sequence"],
                "reasoning": self._generate_recommendation_text(matching_pattern)
            },
            "expected_quality": matching_pattern["quality"]["avg_user_rating"]
        }

        return recommendation

    def _generate_recommendation_text(self, pattern: Dict) -> str:
        """Generate human-readable explanation of recommendation."""
        memory = pattern["approach"]["memory_percentage"]["recommended"]
        research = pattern["approach"]["research_percentage"]["recommended"]
        agents = pattern["agents"]["recommended_sequence"]
        rating = pattern["quality"]["avg_user_rating"]
        samples = pattern["sample_count"]

        text = (
            f"Based on {samples} successful planning iterations, this goal type performs best with: "
            f"{memory:.0%} memory + {research:.0%} research. "
            f"Recommended agents: {', '.join(agents)}. "
            f"Average user satisfaction: {rating:.1f}/5 stars."
        )

        return text

    def get_goal_type_stats(self, goal_type: str) -> Optional[Dict]:
        """Get detailed statistics for a specific goal type."""
        return self.patterns.get(goal_type)

    def get_all_goal_types(self) -> List[str]:
        """Get all goal types with recorded data."""
        return list(self.patterns.keys())

    def get_performance_trends(self) -> Dict:
        """
        Get system performance trends over time.

        Returns:
        {
            "total_planning_attempts": int,
            "average_quality_over_time": [float],  # Moving average
            "user_satisfaction_trend": [float],
            "approach_diversity": float (0-1),  # How varied are approaches?
            "learning_progress": str  # Improving/stable/declining
        }
        """

        if not self.outcomes:
            return {}

        # Sort by date
        sorted_outcomes = sorted(
            self.outcomes,
            key=lambda o: o.get("completed_at", "")
        )

        # Calculate moving average of quality (window=5)
        window_size = 5
        quality_scores = [o.get("quality_score", 0.5) for o in sorted_outcomes]
        moving_avg = []
        for i in range(len(quality_scores)):
            window = quality_scores[max(0, i-window_size):i+1]
            moving_avg.append(sum(window) / len(window))

        # User satisfaction trend
        ratings = [o.get("user_rating", 3) for o in sorted_outcomes]
        rating_moving_avg = []
        for i in range(len(ratings)):
            window = ratings[max(0, i-window_size):i+1]
            rating_moving_avg.append(sum(window) / len(window))

        # Approach diversity (how different are approach ratios?)
        memory_pcts = [o["approach"].get("memory_percentage", 0.5) for o in sorted_outcomes]
        approach_diversity = self._std_dev(memory_pcts) if memory_pcts else 0.0

        # Learning progress
        if len(moving_avg) > 5:
            recent = moving_avg[-5:]
            old = moving_avg[-10:-5]
            if old:
                trend = "improving" if sum(recent) > sum(old) else "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "total_planning_attempts": len(self.outcomes),
            "average_quality_over_time": [round(x, 2) for x in moving_avg],
            "user_satisfaction_trend": [round(x, 2) for x in rating_moving_avg],
            "approach_diversity": round(approach_diversity, 2),
            "learning_progress": trend
        }

    def get_approach_effectiveness(self) -> Dict:
        """
        Analyze which approach ratios work best overall.

        Returns analysis of memory% vs research% effectiveness
        """

        if not self.outcomes:
            return {}

        # Group outcomes by memory percentage (rounded to nearest 10%)
        buckets = defaultdict(list)
        for outcome in self.outcomes:
            memory = outcome["approach"].get("memory_percentage", 0.5)
            # Round to nearest 10%
            bucket = round(memory * 10) * 10
            buckets[bucket].append(outcome)

        # Calculate average quality for each bucket
        effectiveness = {}
        for bucket, outcomes in buckets.items():
            ratings = [o.get("user_rating", 3) for o in outcomes]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
            effectiveness[f"{bucket}% memory"] = {
                "avg_rating": round(avg_rating, 1),
                "sample_count": len(outcomes)
            }

        return effectiveness

    # ========================================
    # Utility Methods
    # ========================================

    def _std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def export_insights(self, output_path: str) -> None:
        """
        Export all insights to a markdown file for review.

        Useful for understanding what the system has learned.
        """

        try:
            with open(output_path, 'w') as f:
                f.write("# Learning Insights\n\n")

                # Overview
                f.write("## System Performance\n")
                trends = self.get_performance_trends()
                f.write(f"- Total planning attempts: {trends.get('total_planning_attempts')}\n")
                f.write(f"- Learning trend: {trends.get('learning_progress')}\n")
                f.write(f"- Approach diversity: {trends.get('approach_diversity')}\n\n")

                # Goal type analysis
                f.write("## Goal Type Patterns\n\n")
                for goal_type in sorted(self.get_all_goal_types()):
                    pattern = self.get_goal_type_stats(goal_type)
                    f.write(f"### {goal_type.title()}\n")
                    f.write(f"- Samples: {pattern['sample_count']}\n")
                    f.write(f"- Recommended: {pattern['approach']['memory_percentage']['recommended']:.0%} memory + "
                           f"{pattern['approach']['research_percentage']['recommended']:.0%} research\n")
                    f.write(f"- Best agents: {', '.join(pattern['agents']['recommended_sequence'])}\n")
                    f.write(f"- Avg quality: {pattern['quality']['avg_user_rating']:.1f}/5\n\n")

                # Effectiveness analysis
                f.write("## Approach Effectiveness\n")
                effectiveness = self.get_approach_effectiveness()
                for approach, stats in sorted(effectiveness.items(), key=lambda x: x[1]['avg_rating'], reverse=True):
                    f.write(f"- {approach}: {stats['avg_rating']:.1f}/5 ({stats['sample_count']} samples)\n")

            print(f"Insights exported to {output_path}")

        except Exception as e:
            print(f"Failed to export insights: {e}")


if __name__ == "__main__":
    # Example usage
    tracker = LearningTracker("memory/learning_log.json")
    print(f"Loaded {len(tracker.outcomes)} planning outcomes")
    print(f"Found patterns for {len(tracker.get_all_goal_types())} goal types")
    print(f"\nPerformance trends: {tracker.get_performance_trends()}")
