"""
Learning Analyzer Module

Analyzes completed planning iterations and extracts learnable patterns.

Responsibilities:
1. Read completed plans from memory
2. Extract success patterns (what worked and why)
3. Identify failure patterns (what didn't work)
4. Calculate pattern effectiveness metrics
5. Store insights back to learning entities
6. Provide pattern recommendations for future planning

This is the "Memagent" side of the dual-LLM system - intelligent memory analysis.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ExtractedPattern:
    """A learned pattern extracted from successful planning"""
    pattern_name: str
    scenario: str  # Type of scenario (healthcare + market entry, etc)
    frameworks_used: List[str]
    success_factors: List[str]
    effectiveness_score: float  # 0-1, how well it worked
    use_count: int
    success_count: int
    last_used: str  # ISO timestamp

    def to_markdown(self) -> str:
        """Convert to markdown for storage"""
        return f"""
## {self.pattern_name}

**Scenario:** {self.scenario}
**Frameworks:** {', '.join(self.frameworks_used)}
**Success Factors:**
{chr(10).join([f"- {f}" for f in self.success_factors])}

**Effectiveness:** {self.effectiveness_score*100:.0f}% ({self.success_count}/{self.use_count} plans succeeded)
**Last Used:** {self.last_used}

---
"""


class LearningAnalyzer:
    """Analyzes completed plans and extracts patterns for future learning"""

    def __init__(self, memory_path: Path):
        """
        Initialize learning analyzer

        Args:
            memory_path: Path to local memory directory
        """
        self.memory_path = Path(memory_path)
        self.plans_dir = self.memory_path / "plans"
        self.entities_dir = self.memory_path / "entities"

        # Ensure directories exist
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        self.entities_dir.mkdir(parents=True, exist_ok=True)

    def get_available_plans(self) -> List[Dict[str, Any]]:
        """
        Get list of available plans for user selection.

        Returns:
            List of plan metadata dicts with file paths and info
        """
        if not self.plans_dir.exists():
            return []

        plan_files = sorted(self.plans_dir.glob("plan_*.md"), key=lambda x: x.stat().st_mtime, reverse=True)

        plans = []
        for plan_file in plan_files:
            try:
                content = plan_file.read_text()

                # Extract goal from plan
                goal_match = re.search(r'## Goal\n(.+?)(?:\n##|$)', content, re.DOTALL)
                goal = goal_match.group(1).strip()[:100] if goal_match else "Unknown goal"

                # Extract quality score
                quality_match = re.search(r'quality_score["\']?\s*[:=]\s*([\d.]+)', content, re.IGNORECASE)
                quality = float(quality_match.group(1)) if quality_match else 0.0

                # Get file mod time
                mod_time = datetime.fromtimestamp(plan_file.stat().st_mtime)

                plans.append({
                    "file": plan_file.name,
                    "path": str(plan_file),
                    "goal": goal,
                    "quality": quality,
                    "created": mod_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "size_kb": plan_file.stat().st_size / 1024
                })
            except Exception as e:
                continue

        return plans

    def analyze_selected_plans(self, plan_files: List[str]) -> Dict[str, Any]:
        """
        Analyze only selected plans (user-chosen for learning).

        This is the OPTIMIZED version that only processes selected plans,
        avoiding the API cost explosion from analyzing all plans.

        Args:
            plan_files: List of plan filenames to analyze (e.g., ["plan_1.md", "plan_2.md"])

        Returns:
            Summary of patterns found and patterns stored
        """
        print(f"\n🧠 LEARNING ANALYZER: Extracting patterns from {len(plan_files)} selected plans...")

        if not self.plans_dir.exists():
            print("   ⚠️ No plans directory found")
            return {"status": "no_plans", "patterns_extracted": 0, "selected_count": len(plan_files)}

        # Validate and locate selected plans
        valid_files = []
        for plan_filename in plan_files:
            plan_path = self.plans_dir / plan_filename
            if plan_path.exists():
                valid_files.append(plan_path)
            else:
                print(f"   ⚠️ Plan not found: {plan_filename}")

        if not valid_files:
            print("   ⚠️ No valid plans found to analyze")
            return {"status": "no_plans", "patterns_extracted": 0, "selected_count": 0}

        print(f"   📊 Analyzing {len(valid_files)} selected plans...")

        # Read and analyze each selected plan
        patterns_found = []
        scenarios_seen = {}

        for plan_file in valid_files:
            try:
                pattern = self._extract_pattern_from_plan(plan_file)
                if pattern:
                    patterns_found.append(pattern)

                    # Track scenario frequency
                    scenario_key = pattern.scenario
                    if scenario_key not in scenarios_seen:
                        scenarios_seen[scenario_key] = []
                    scenarios_seen[scenario_key].append(pattern)

                    print(f"   ✅ {plan_file.name}: {pattern.scenario}")

            except Exception as e:
                print(f"   ⚠️ Failed to analyze {plan_file.name}: {e}")
                continue

        # Store extracted patterns
        if patterns_found:
            self._store_patterns(patterns_found)

        # Calculate scenario-specific insights
        insights = self._generate_scenario_insights(scenarios_seen)

        print(f"   ✅ Extracted {len(patterns_found)} patterns from {len(valid_files)} plans")
        print(f"   ✅ Identified {len(scenarios_seen)} scenario types")
        if insights:
            print(f"   ✅ Generated {len(insights)} actionable insights")

        return {
            "status": "success",
            "patterns_extracted": len(patterns_found),
            "scenarios_identified": list(scenarios_seen.keys()),
            "insights_generated": len(insights),
            "selected_count": len(valid_files)
        }

    def analyze_all_completed_plans(self) -> Dict[str, Any]:
        """
        Analyze all completed plans in memory and extract learnings.

        NOTE: This is kept for backward compatibility, but is NOT recommended
        for production use with cost concerns. Use analyze_selected_plans() instead
        with user-selected plan list for cost control.

        Returns:
            Summary of patterns found and patterns stored
        """
        print("\n🧠 LEARNING ANALYZER: Extracting patterns from all completed plans...")

        if not self.plans_dir.exists():
            print("   ⚠️ No plans directory found - nothing to learn from yet")
            return {"status": "no_plans", "patterns_extracted": 0}

        # Find all completed plan files
        plan_files = list(self.plans_dir.glob("plan_*.md"))

        if not plan_files:
            print("   ⚠️ No completed plans found - nothing to learn from yet")
            return {"status": "no_plans", "patterns_extracted": 0}

        print(f"   📊 Found {len(plan_files)} completed plans to analyze")

        # Read and analyze each plan
        patterns_found = []
        scenarios_seen = {}

        for plan_file in sorted(plan_files):
            try:
                pattern = self._extract_pattern_from_plan(plan_file)
                if pattern:
                    patterns_found.append(pattern)

                    # Track scenario frequency
                    scenario_key = pattern.scenario
                    if scenario_key not in scenarios_seen:
                        scenarios_seen[scenario_key] = []
                    scenarios_seen[scenario_key].append(pattern)

            except Exception as e:
                print(f"   ⚠️ Failed to analyze {plan_file.name}: {e}")
                continue

        # Store extracted patterns
        if patterns_found:
            self._store_patterns(patterns_found)

        # Calculate scenario-specific insights
        insights = self._generate_scenario_insights(scenarios_seen)

        print(f"   ✅ Extracted {len(patterns_found)} patterns")
        print(f"   ✅ Identified {len(scenarios_seen)} scenario types")
        if insights:
            print(f"   ✅ Generated {len(insights)} actionable insights")

        return {
            "status": "success",
            "patterns_extracted": len(patterns_found),
            "scenarios_identified": list(scenarios_seen.keys()),
            "insights_generated": len(insights)
        }

    def _extract_pattern_from_plan(self, plan_file: Path) -> Optional[ExtractedPattern]:
        """
        Extract a learnable pattern from a completed plan file.

        Args:
            plan_file: Path to the plan markdown file

        Returns:
            ExtractedPattern if successful, None otherwise
        """
        try:
            content = plan_file.read_text()

            # Extract goal from plan
            goal_match = re.search(r'## Goal\n(.+?)(?:\n##|\Z)', content, re.DOTALL)
            goal = goal_match.group(1).strip() if goal_match else "Unknown goal"

            # Extract success indicators
            success_match = re.search(r'quality_score["\']?\s*[:=]\s*([\d.]+)', content, re.IGNORECASE)
            quality_score = float(success_match.group(1)) if success_match else 0.5
            quality_score = quality_score / 10.0 if quality_score > 1 else quality_score  # Normalize to 0-1

            # Extract frameworks used
            frameworks = self._extract_frameworks_from_content(content)

            # Extract success factors by looking for agent outputs
            success_factors = self._extract_success_factors(content)

            # Determine scenario type (domain + market)
            scenario = self._determine_scenario_type(goal)

            pattern = ExtractedPattern(
                pattern_name=f"{scenario} - {datetime.now().strftime('%Y-%m-%d')}",
                scenario=scenario,
                frameworks_used=frameworks,
                success_factors=success_factors,
                effectiveness_score=quality_score,
                use_count=1,
                success_count=1 if quality_score >= 0.7 else 0,
                last_used=datetime.now().isoformat()
            )

            return pattern

        except Exception as e:
            print(f"   ⚠️ Error extracting pattern: {e}")
            return None

    def _extract_frameworks_from_content(self, content: str) -> List[str]:
        """Extract framework names mentioned in the plan"""
        frameworks = []

        # Common planning frameworks
        framework_patterns = [
            r'(Porter\'s Five Forces)',
            r'(SWOT Analysis)',
            r'(Market Entry Framework)',
            r'(Risk Assessment)',
            r'(Competitive Analysis)',
            r'(Regulatory Framework)',
            r'(Strategic Planning)',
            r'(Implementation Timeline)',
            r'(Success Metrics)',
            r'(Lean Methodology)',
            r'(Agile Framework)',
            r'(Six Sigma)',
            r'(Value Chain Analysis)',
            r'(Stakeholder Analysis)'
        ]

        for pattern in framework_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                match = re.search(pattern, content, re.IGNORECASE)
                frameworks.append(match.group(1))

        return frameworks if frameworks else ["General Planning"]

    def _extract_success_factors(self, content: str) -> List[str]:
        """Extract what made this plan successful"""
        factors = []

        # Look for success indicators in agent outputs
        if re.search(r'SUCCESS|✅|success.*metric|strong', content, re.IGNORECASE):
            factors.append("Clear success metrics defined")

        if re.search(r'regulatory|compliance|legal|framework', content, re.IGNORECASE):
            factors.append("Regulatory considerations addressed")

        if re.search(r'competitive|market analysis|differentiation', content, re.IGNORECASE):
            factors.append("Competitive landscape analyzed")

        if re.search(r'timeline|schedule|phased|phase|milestone', content, re.IGNORECASE):
            factors.append("Clear implementation timeline")

        if re.search(r'risk|mitigation|contingency', content, re.IGNORECASE):
            factors.append("Risk management plan included")

        if re.search(r'resource|budget|cost|investment', content, re.IGNORECASE):
            factors.append("Resource and budget planning")

        if re.search(r'stakeholder|partner|collaboration', content, re.IGNORECASE):
            factors.append("Stakeholder engagement planned")

        return factors if factors else ["Comprehensive planning approach"]

    def _determine_scenario_type(self, goal: str) -> str:
        """Determine the scenario type from the goal"""
        goal_lower = goal.lower()

        # Domain detection
        domain = "general"
        if any(word in goal_lower for word in ['healthcare', 'medical', 'pharmaceutical', 'biotech', 'clinical']):
            domain = "healthcare"
        elif any(word in goal_lower for word in ['tech', 'software', 'ai', 'digital', 'saas', 'platform']):
            domain = "technology"
        elif any(word in goal_lower for word in ['manufacturing', 'factory', 'production', 'industrial']):
            domain = "manufacturing"
        elif any(word in goal_lower for word in ['retail', 'e-commerce', 'online']):
            domain = "retail"
        elif any(word in goal_lower for word in ['restaurant', 'food', 'cafe', 'qsr', 'dining']):
            domain = "qsr"

        # Market detection
        market = "global"
        if any(word in goal_lower for word in ['vietnam', 'vietnamese']):
            market = "vietnam"
        elif any(word in goal_lower for word in ['southeast asia', 'sea', 'singapore', 'thailand']):
            market = "southeast_asia"
        elif any(word in goal_lower for word in ['usa', 'united states', 'america', 'north america']):
            market = "north_america"
        elif any(word in goal_lower for word in ['europe', 'eu', 'germany', 'france']):
            market = "europe"
        elif any(word in goal_lower for word in ['asia', 'china', 'japan', 'korea']):
            market = "asia_pacific"

        # Activity detection
        activity = "general"
        if any(word in goal_lower for word in ['entering', 'enter', 'entry', 'enter market']):
            activity = "market_entry"
        elif any(word in goal_lower for word in ['expanding', 'expansion', 'expand']):
            activity = "expansion"
        elif any(word in goal_lower for word in ['launching', 'launch', 'launching']):
            activity = "launch"
        elif any(word in goal_lower for word in ['strategy', 'strategic']):
            activity = "strategy"

        return f"{domain} + {market} + {activity}"

    def _generate_scenario_insights(self, scenarios_seen: Dict[str, List[ExtractedPattern]]) -> List[str]:
        """Generate actionable insights from scenario analysis"""
        insights = []

        for scenario, patterns in scenarios_seen.items():
            if len(patterns) >= 2:
                # We've seen this scenario multiple times - extract meta-patterns
                avg_effectiveness = sum(p.effectiveness_score for p in patterns) / len(patterns)
                common_frameworks = self._extract_common_elements(
                    [p.frameworks_used for p in patterns]
                )
                common_factors = self._extract_common_elements(
                    [p.success_factors for p in patterns]
                )

                insight = f"""
## Scenario Pattern: {scenario}

**Frequency:** Seen {len(patterns)} times
**Average Effectiveness:** {avg_effectiveness*100:.0f}%

**Consistently Used Frameworks:**
{chr(10).join([f"- {f}" for f in common_frameworks])}

**Common Success Factors:**
{chr(10).join([f"- {f}" for f in common_factors])}

**Recommendation:** When planning for {scenario} scenarios, prioritize these frameworks and factors.

---
"""
                insights.append(insight)

        return insights

    def _extract_common_elements(self, lists: List[List[str]]) -> List[str]:
        """Extract elements that appear in multiple lists"""
        if not lists:
            return []

        # Count occurrences
        element_counts = {}
        for lst in lists:
            for element in lst:
                element_counts[element] = element_counts.get(element, 0) + 1

        # Return elements that appear in at least 50% of lists
        threshold = len(lists) / 2
        return [elem for elem, count in element_counts.items() if count >= threshold]

    def _store_patterns(self, patterns: List[ExtractedPattern]) -> None:
        """Store extracted patterns to learning entities"""

        # Update successful_patterns.md
        patterns_file = self.entities_dir / "successful_patterns.md"

        if not patterns_file.exists():
            patterns_file.write_text("# Successful Planning Patterns\n\nLearned from completed planning iterations.\n\n")

        # Append new patterns
        with open(patterns_file, 'a') as f:
            f.write(f"\n## Learning Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for pattern in patterns:
                f.write(pattern.to_markdown())

        print(f"   💾 Stored {len(patterns)} patterns to successful_patterns.md")

        # Update agent_performance.md with pattern effectiveness
        perf_file = self.entities_dir / "agent_performance.md"

        if perf_file.exists():
            with open(perf_file, 'a') as f:
                f.write(f"\n## Pattern Effectiveness - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for pattern in patterns:
                    f.write(f"- {pattern.scenario}: {pattern.effectiveness_score*100:.0f}% effective\n")

    def get_patterns_for_goal(self, goal: str, top_k: int = 3) -> List[ExtractedPattern]:
        """
        Get the most relevant learned patterns for a given goal.

        This is used by pattern_recommender.py to suggest patterns to Llama.

        Args:
            goal: The user's planning goal
            top_k: Number of patterns to return

        Returns:
            List of relevant ExtractedPattern objects
        """
        print(f"\n🔍 Finding learned patterns relevant to: {goal[:60]}...")

        # Determine scenario type
        target_scenario = self._determine_scenario_type(goal)

        # Read successful patterns
        patterns_file = self.entities_dir / "successful_patterns.md"
        if not patterns_file.exists():
            print("   ⚠️ No learned patterns yet")
            return []

        content = patterns_file.read_text()

        # Parse patterns from markdown (simple approach)
        # In production, would use more sophisticated parsing
        pattern_blocks = re.split(r'\n## (?!Scenario)', content)

        relevant_patterns = []
        for block in pattern_blocks:
            if "Scenario:" in block and "Effectiveness:" in block:
                # Try to extract pattern info
                scenario_match = re.search(r'Scenario:\s*(.+?)(?:\n|$)', block)
                effectiveness_match = re.search(r'Effectiveness:\s*(\d+)%', block)

                if scenario_match:
                    scenario = scenario_match.group(1).strip()
                    effectiveness = int(effectiveness_match.group(1)) / 100 if effectiveness_match else 0.5

                    # Score based on scenario similarity
                    similarity_score = self._calculate_scenario_similarity(target_scenario, scenario)

                    if similarity_score > 0.4:  # Must have some similarity
                        relevant_patterns.append({
                            "scenario": scenario,
                            "effectiveness": effectiveness,
                            "similarity": similarity_score,
                            "block": block,
                            "combined_score": (effectiveness * 0.6 + similarity_score * 0.4)
                        })

        # Sort by combined score and return top-k
        relevant_patterns.sort(key=lambda x: x["combined_score"], reverse=True)

        print(f"   ✅ Found {len(relevant_patterns)} potentially relevant patterns")
        if relevant_patterns:
            print(f"   📌 Top match: {relevant_patterns[0]['scenario']} ({relevant_patterns[0]['combined_score']*100:.0f}% relevance)")

        return relevant_patterns[:top_k]

    def _calculate_scenario_similarity(self, target: str, source: str) -> float:
        """Calculate similarity between two scenario descriptions"""
        target_parts = set(target.lower().split())
        source_parts = set(source.lower().split())

        if not target_parts or not source_parts:
            return 0.0

        intersection = len(target_parts & source_parts)
        union = len(target_parts | source_parts)

        return intersection / union if union > 0 else 0.0
