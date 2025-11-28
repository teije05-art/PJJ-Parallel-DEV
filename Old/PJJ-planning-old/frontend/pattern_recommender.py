"""
Pattern Recommender Module

Takes learned patterns from the learning analyzer and recommends them to Llama
during the planning process.

Responsibilities:
1. Query learning_analyzer for relevant patterns
2. Format patterns for Llama consumption
3. Score and rank patterns by relevance
4. Provide pattern-based planning context
5. Track pattern usage for feedback

This is where the learned knowledge gets fed back into the planning loop.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from .learning_analyzer import LearningAnalyzer
from .learning import FlowGRPOTrainer  # Phase 3.3: Flow-GRPO pattern scoring

DEBUG = True  # Phase 3.3: Enable debug output for pattern scoring


class PatternRecommender:
    """Recommends learned patterns for a given planning goal"""

    def __init__(self, memory_path: Path, flow_grpo_trainer: Optional[FlowGRPOTrainer] = None):
        """
        Initialize pattern recommender

        Args:
            memory_path: Path to local memory directory
            flow_grpo_trainer: Optional FlowGRPOTrainer instance for pattern effectiveness scoring (Phase 3.3)
        """
        self.memory_path = Path(memory_path)
        self.learning_analyzer = LearningAnalyzer(memory_path)
        self.flow_grpo_trainer = flow_grpo_trainer  # Phase 3.3: For pattern effectiveness
        self.usage_log = self.memory_path / "entities" / "pattern_usage_log.md"

        # Initialize usage log
        if not self.usage_log.exists():
            self.usage_log.write_text("""# Pattern Usage Log

Tracks which learned patterns have been recommended and their outcomes.

---
""")

    def get_pattern_context(self, goal: str, selected_plans: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get pattern-based context to include in planning prompts.

        This is the main method called by planner_agent.py before generating a plan.

        Args:
            goal: The user's planning goal
            selected_plans: Optional list of plan filenames to learn from.
                          If None, uses existing patterns without new analysis.
                          If provided, analyzes only these plans for learning.

        Returns:
            Dictionary with pattern-based context for Llama
        """
        print(f"\n🎯 PATTERN RECOMMENDER: Finding learned patterns for this goal...")

        # If user selected specific plans for learning, analyze them first
        if selected_plans:
            print(f"   📌 User selected {len(selected_plans)} plans for learning")
            self.learning_analyzer.analyze_selected_plans(selected_plans)

        # Get relevant patterns
        relevant_patterns = self.learning_analyzer.get_patterns_for_goal(goal, top_k=3)

        if not relevant_patterns:
            print("   ℹ️ No learned patterns available yet (system learning from scratch)")
            return {
                "has_learned_patterns": False,
                "patterns": [],
                "context": "",
                "selected_plans_analyzed": len(selected_plans) if selected_plans else 0
            }

        # Phase 3.3: Score patterns by Flow-GRPO effectiveness
        ranked_patterns = self.score_patterns_by_flow_effectiveness(relevant_patterns)
        if DEBUG:
            print(f"   📊 Patterns ranked by flow effectiveness")
            for i, p in enumerate(ranked_patterns[:3], 1):
                print(f"      {i}. {p.get('scenario', 'Unknown')}: {p.get('flow_effectiveness', 0.5):.3f}")

        # Format patterns for Llama
        formatted_patterns = self._format_patterns_for_llama(ranked_patterns, goal)

        return {
            "has_learned_patterns": True,
            "patterns": ranked_patterns,  # Phase 3.3: Return ranked patterns
            "context": formatted_patterns,
            "pattern_count": len(ranked_patterns),
            "selected_plans_analyzed": len(selected_plans) if selected_plans else 0
        }

    def get_available_plans_for_selection(self) -> Dict[str, Any]:
        """
        Get list of available plans for user to select which to learn from.

        Called before planning to show user the "Select Plans for Learning" gate.

        Returns:
            Dictionary with available plans and metadata
        """
        available_plans = self.learning_analyzer.get_available_plans()

        if not available_plans:
            return {
                "status": "no_plans",
                "plans": [],
                "message": "No completed plans available for learning"
            }

        return {
            "status": "success",
            "plans": available_plans,
            "total_count": len(available_plans),
            "message": f"Found {len(available_plans)} completed plans. Select which to learn from."
        }

    def _format_patterns_for_llama(self, patterns: List[Dict[str, Any]], goal: str) -> str:
        """
        Format learned patterns into natural language for Llama's planning prompt.

        Args:
            patterns: List of relevant patterns
            goal: The planning goal

        Returns:
            Formatted string for inclusion in Llama's prompt
        """
        if not patterns:
            return ""

        prompt_section = """
## LEARNED PATTERNS FROM PAST PLANNING

Based on successful past planning iterations similar to your goal, here are proven approaches:

"""

        for i, pattern in enumerate(patterns, 1):
            scenario = pattern.get("scenario", "Unknown scenario")
            effectiveness = pattern.get("effectiveness", 0) * 100
            similarity = pattern.get("similarity", 0) * 100
            block = pattern.get("block", "")

            # Extract frameworks and factors from the block
            frameworks = self._extract_section(block, "Consistently Used Frameworks", "Recommendation")
            factors = self._extract_section(block, "Common Success Factors", "Recommendation")

            prompt_section += f"""
### Pattern {i}: {scenario}
(Relevance: {similarity:.0f}%, Historical Success: {effectiveness:.0f}%)

"""

            if frameworks:
                prompt_section += f"**Recommended Frameworks:**\n{frameworks}\n\n"

            if factors:
                prompt_section += f"**Key Success Factors:**\n{factors}\n\n"

            prompt_section += "---\n\n"

        prompt_section += """
APPLY THESE PATTERNS IF RELEVANT:
- Use the frameworks that worked for similar scenarios in the past
- Incorporate the success factors that led to high-quality plans
- Adapt patterns to your specific context while retaining what made them effective

"""

        return prompt_section

    def _extract_section(self, block: str, start_marker: str, end_marker: str) -> str:
        """Extract a section of text between two markers"""
        import re

        pattern = f"{start_marker}:(.+?)(?:{end_marker}|$)"
        match = re.search(pattern, block, re.DOTALL | re.IGNORECASE)

        if match:
            content = match.group(1).strip()
            # Clean up the content
            lines = [line.strip() for line in content.split('\n') if line.strip() and line.strip().startswith('-')]
            return '\n'.join(lines[:5])  # Limit to 5 items

        return ""

    def log_pattern_usage(self, goal: str, patterns_recommended: List[Dict[str, Any]],
                         was_useful: Optional[bool] = None, feedback: str = "") -> None:
        """
        Log which patterns were recommended and how useful they were.

        Args:
            goal: The planning goal
            patterns_recommended: List of patterns that were recommended
            was_useful: Whether the patterns actually helped (optional)
            feedback: User feedback on pattern usefulness (optional)
        """
        timestamp = datetime.now().isoformat()

        log_entry = f"""
## Pattern Usage - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Goal:** {goal}
**Patterns Recommended:** {len(patterns_recommended)}
**Timestamp:** {timestamp}

**Recommended Patterns:**
"""

        for pattern in patterns_recommended:
            scenario = pattern.get("scenario", "Unknown")
            effectiveness = pattern.get("effectiveness", 0) * 100
            similarity = pattern.get("similarity", 0) * 100
            log_entry += f"\n- {scenario} (Effectiveness: {effectiveness:.0f}%, Similarity: {similarity:.0f}%)"

        if was_useful is not None:
            log_entry += f"\n**Usefulness:** {'✅ HELPFUL' if was_useful else '❌ NOT HELPFUL'}"

        if feedback:
            log_entry += f"\n**Feedback:** {feedback}"

        log_entry += "\n\n---\n\n"

        # Append to log
        with open(self.usage_log, 'a') as f:
            f.write(log_entry)

    def get_pattern_effectiveness_report(self) -> Dict[str, Any]:
        """
        Generate a report on how effective learned patterns have been.

        Returns:
            Report with pattern effectiveness metrics
        """
        print("\n📊 Generating pattern effectiveness report...")

        if not self.usage_log.exists():
            return {"status": "no_usage_data"}

        usage_content = self.usage_log.read_text()

        # Parse usage log
        helpful_count = usage_content.count("✅ HELPFUL")
        unhelpful_count = usage_content.count("❌ NOT HELPFUL")
        usage_count = usage_content.count("## Pattern Usage")

        if usage_count == 0:
            return {"status": "no_usage_data"}

        effectiveness = helpful_count / usage_count if usage_count > 0 else 0

        report = {
            "status": "success",
            "total_usages": usage_count,
            "helpful_count": helpful_count,
            "unhelpful_count": unhelpful_count,
            "effectiveness_rate": effectiveness * 100,
            "recommendation": self._generate_recommendation(effectiveness)
        }

        print(f"   ✅ Patterns used {usage_count} times")
        print(f"   ✅ Effectiveness: {effectiveness*100:.0f}%")
        print(f"   💡 {report['recommendation']}")

        return report

    def _generate_recommendation(self, effectiveness: float) -> str:
        """Generate a recommendation based on pattern effectiveness"""
        if effectiveness >= 0.9:
            return "Excellent! Learned patterns are very effective. Continue using them."
        elif effectiveness >= 0.7:
            return "Good! Learned patterns are generally helpful. Keep refining them."
        elif effectiveness >= 0.5:
            return "Fair. Patterns have some value. Need more data for better recommendations."
        elif effectiveness > 0:
            return "Patterns not very effective yet. System still learning. Need more iterations."
        else:
            return "No feedback yet. Continue using patterns while gathering effectiveness data."

    def suggest_pattern_refinements(self) -> List[str]:
        """
        Suggest ways to refine patterns based on usage history.

        Returns:
            List of refinement suggestions
        """
        suggestions = []

        # Read planning errors to see what went wrong
        errors_file = self.memory_path / "entities" / "planning_errors.md"
        if errors_file.exists():
            error_content = errors_file.read_text()

            # Common error patterns
            if "entity not found" in error_content.lower():
                suggestions.append("Consider validating all entity selections before planning")

            if "timeout" in error_content.lower():
                suggestions.append("Some patterns may be too complex - simplify approach")

            if "incomplete" in error_content.lower():
                suggestions.append("Add more comprehensive research to existing frameworks")

        # Read successful patterns for improvement ideas
        patterns_file = self.memory_path / "entities" / "successful_patterns.md"
        if patterns_file.exists() and errors_file.exists():
            patterns_content = patterns_file.read_text()
            error_content = errors_file.read_text()

            # Compare frequency of frameworks
            import re
            pattern_frameworks = set(re.findall(r'\*\*Framework[s]*:\*\*\s*(.+?)(?:\n|$)', patterns_content))
            error_frameworks = set(re.findall(r'Framework[s]*:\s*(.+?)(?:\n|$)', error_content))

            avoided_frameworks = error_frameworks - pattern_frameworks
            if avoided_frameworks:
                suggestions.append(f"Avoid these frameworks: {', '.join(avoided_frameworks)}")

        return suggestions if suggestions else ["Continue gathering data on pattern effectiveness"]

    def create_pattern_comparison(self, goal: str) -> Dict[str, Any]:
        """
        Create a comparison between planning with and without learned patterns.

        This helps understand the value of the learning loop.

        Args:
            goal: The planning goal

        Returns:
            Comparison metrics
        """
        patterns = self.learning_analyzer.get_patterns_for_goal(goal, top_k=5)

        if not patterns:
            return {
                "status": "no_patterns",
                "insight": "No learned patterns available yet. System will learn from this planning iteration."
            }

        total_effectiveness = sum(p.get("effectiveness", 0.5) for p in patterns)
        avg_effectiveness = total_effectiveness / len(patterns) if patterns else 0

        comparison = {
            "status": "patterns_available",
            "pattern_count": len(patterns),
            "average_effectiveness": avg_effectiveness * 100,
            "most_relevant": patterns[0].get("scenario", "Unknown") if patterns else None,
            "expected_improvement": f"{(avg_effectiveness - 0.6) * 100:.0f}% over baseline",
            "insight": self._generate_pattern_insight(patterns)
        }

        return comparison

    def score_patterns_by_flow_effectiveness(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Phase 3.3: Score patterns by their Flow-GRPO effectiveness.

        Ranks patterns based on flow scores from previous iterations.
        Patterns that contributed to high flow scores are ranked higher.

        Args:
            patterns: List of patterns to score

        Returns:
            Sorted list of patterns with flow effectiveness scores
        """
        if not self.flow_grpo_trainer:
            # No Flow-GRPO trainer available, return patterns as-is
            return patterns

        try:
            # Score each pattern based on its historical flow effectiveness
            scored_patterns = []
            top_patterns = self.flow_grpo_trainer.get_top_patterns(top_k=10)
            pattern_score_map = {name: score for name, score in top_patterns}

            for pattern in patterns:
                pattern_name = pattern.get("name", pattern.get("scenario", ""))
                flow_score = pattern_score_map.get(pattern_name, 0.5)  # Default 0.5 if not tracked

                pattern_with_score = pattern.copy()
                pattern_with_score['flow_effectiveness'] = flow_score
                scored_patterns.append(pattern_with_score)

            # Sort by flow effectiveness (descending)
            scored_patterns.sort(key=lambda p: p.get('flow_effectiveness', 0.5), reverse=True)

            return scored_patterns
        except Exception as e:
            # Fallback: return patterns as-is if scoring fails
            print(f"⚠️  Could not score patterns by flow effectiveness: {e}")
            return patterns

    def _generate_pattern_insight(self, patterns: List[Dict[str, Any]]) -> str:
        """Generate an insight about the available patterns"""
        if not patterns:
            return "Starting fresh - no learned patterns to guide planning yet."

        top_pattern = patterns[0]
        scenario = top_pattern.get("scenario", "Unknown")
        effectiveness = top_pattern.get("flow_effectiveness", top_pattern.get("effectiveness", 0.5))

        if effectiveness >= 0.8:
            return f"Strong learning available for {scenario} scenarios. Expect {effectiveness*100:.0f}% quality."
        elif effectiveness >= 0.6:
            return f"Moderate learning available for {scenario} scenarios. Plan quality will be above average."
        else:
            return f"Limited learning for {scenario} scenarios. This iteration will help improve future planning."
