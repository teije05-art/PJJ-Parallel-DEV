"""
Context Manager for Planning System

Manages:
1. Goal-specific query generation
2. Entity/memory context retrieval
3. Research context gathering
4. DETAILED checkpoint summaries (1000+ words, not fragments)
5. Planning context formatting for agents
"""

import asyncio
import json
import re
from typing import Dict, Any, List, Optional


def generate_goal_specific_queries(goal: str) -> List[str]:
    """
    Generate intelligent, goal-specific search queries tailored to the goal.

    Returns list of targeted search queries based on goal characteristics.
    """
    goal_lower = goal.lower()
    queries = [goal]  # Always include goal itself

    # GROWTH/STRATEGY GOALS
    if any(word in goal_lower for word in ["growth", "strategy", "expand", "scale"]):
        queries.extend([
            "revenue metrics and growth rates",
            "customer acquisition cost (CAC) and lifetime value (LTV)",
            "market size and expansion opportunities",
            "competitive analysis and positioning",
            "historical growth patterns and trends",
        ])

    # PLANNING/EXECUTION GOALS
    if any(word in goal_lower for word in ["plan", "launch", "implement", "execute", "roadmap"]):
        queries.extend([
            "timeline and milestones",
            "resource requirements and dependencies",
            "implementation approach and methodology",
            "risk assessment and mitigation",
            "success metrics and KPIs",
        ])

    # DATA/ANALYSIS GOALS
    if any(word in goal_lower for word in ["analyze", "research", "data", "market"]):
        queries.extend([
            "current market trends and data",
            "key metrics and benchmarks",
            "industry standards and comparisons",
            "recent developments and changes",
        ])

    # FINANCIAL GOALS
    if any(word in goal_lower for word in ["financial", "budget", "cost", "revenue", "profit", "pricing"]):
        queries.extend([
            "financial projections and forecasts",
            "pricing strategies and models",
            "cost structure and optimization",
            "profitability metrics and benchmarks",
        ])

    # PRODUCT GOALS
    if any(word in goal_lower for word in ["product", "feature", "develop", "build"]):
        queries.extend([
            "product roadmap and features",
            "user requirements and feedback",
            "competitive product analysis",
            "technical architecture and requirements",
        ])

    # Remove duplicates and limit
    return list(dict.fromkeys(queries))[:15]


async def retrieve_memory_context(
    llama_planner: Any,
    selected_entities: Optional[List[str]] = None,
    goal: str = ""
) -> Dict[str, Any]:
    """
    Search memory for context relevant to goal.

    Args:
        llama_planner: LlamaPlanner instance
        selected_entities: Which entities to search in
        goal: User's goal (for relevance)

    Returns:
        Dictionary with memory search results
    """
    if not llama_planner:
        return {"results": [], "coverage": 0}

    try:
        queries = generate_goal_specific_queries(goal)

        memory_results = await asyncio.to_thread(
            llama_planner.search_memory,
            selected_entities or [],
            queries
        )

        return {
            "results": memory_results,
            "queries_run": queries,
            "coverage": 0.6 if memory_results else 0.0
        }
    except Exception as e:
        return {
            "results": [],
            "error": str(e),
            "coverage": 0
        }


async def build_planning_context(
    goal: str,
    selected_entities: List[str],
    selected_agents: List[str],
    llama_planner: Any,
    max_iterations: int = 1,
    checkpoint_interval: int = 2
) -> Dict[str, Any]:
    """
    Build complete planning context from all sources.

    FIXES: Ensures control values are stored with context.
    """
    # Generate queries
    queries = generate_goal_specific_queries(goal)

    # Retrieve memory context
    memory_context = await retrieve_memory_context(
        llama_planner,
        selected_entities,
        goal
    )

    # Build approach plan
    approach_plan = {
        "memory_percentage": 0.6,
        "research_percentage": 0.4,
        "research_focus": queries[:5],
        "agents_to_use": selected_agents,
        "resource_estimate": {
            "estimated_time_minutes": max_iterations * 5,
            "memory_searches": len(queries),
            "web_searches": 10,
            "agents_to_call": len(selected_agents)
        }
    }

    return {
        "goal": goal,
        "selected_entities": selected_entities,
        "selected_agents": selected_agents,
        "max_iterations": max_iterations,
        "checkpoint_interval": checkpoint_interval,
        "queries": queries,
        "memory_context": memory_context,
        "approach_plan": approach_plan
    }


async def generate_detailed_checkpoint_summary(
    agent: Any,
    goal: str,
    iteration_number: int,
    current_result: Dict[str, Any],
    previous_result: Optional[Dict[str, Any]] = None,
    debug: bool = False
) -> str:
    """
    Generate FULL checkpoint summary (1000+ words, not 50-word fragment).

    FIXES ISSUE #3: Creates detailed analysis of what's been done so far,
    not just JSON improvements data.

    Args:
        agent: Agent for Llama analysis
        goal: Planning goal
        iteration_number: Current iteration
        current_result: Current iteration results
        previous_result: Previous iteration for comparison
        debug: Enable debug output

    Returns:
        Full 1000+ word checkpoint summary
    """
    try:
        # Build comparison data
        current_frameworks = current_result.get("frameworks_used", [])
        previous_frameworks = previous_result.get("frameworks_used", []) if previous_result else []
        current_data_points = current_result.get("data_points_count", 0)
        previous_data_points = previous_result.get("data_points_count", 0) if previous_result else 0

        if iteration_number == 1 or not previous_result:
            # First checkpoint - summarize what we've learned so far
            prompt = f"""You are analyzing the first iteration of planning for this goal:

GOAL: {goal}

ITERATION 1 RESULTS:
- Frameworks Applied: {', '.join(current_frameworks) if current_frameworks else 'Initial frameworks'}
- Data Points Extracted: {current_data_points}
- Key Findings: {current_result.get('summary', 'Planning in progress')[:1000]}

Please provide a DETAILED (1000+ words) checkpoint summary that includes:

1. **Planning Approach Overview** (200 words)
   - How the system is approaching this goal
   - Key strategies identified
   - Initial frameworks applied and why they're relevant

2. **Data Gathering Analysis** (250 words)
   - What data has been collected so far
   - Which sources have been most valuable
   - What patterns are emerging from the data

3. **Frameworks and Methodologies** (250 words)
   - Which planning frameworks are being applied
   - How they fit together
   - Early insights from framework application

4. **Coverage and Completeness** (150 words)
   - What aspects of the goal have been covered
   - What areas need deeper exploration in next iterations
   - Gaps identified so far

5. **Key Findings So Far** (150 words)
   - Most important insights discovered
   - Initial recommendations forming
   - Surprising discoveries or angles

Provide a comprehensive narrative that shows the planning is making real progress and covers actual content being discovered. Make it detailed and specific to the goal provided."""

        else:
            # Subsequent checkpoints - show improvements
            new_frameworks = set(current_frameworks) - set(previous_frameworks)
            data_points_gained = current_data_points - previous_data_points

            prompt = f"""You are analyzing iteration {iteration_number} of planning for this goal:

GOAL: {goal}

ITERATION {iteration_number - 1} (Previous):
- Frameworks: {', '.join(previous_frameworks) if previous_frameworks else 'Initial frameworks'}
- Data Points: {previous_data_points}
- Summary: {previous_result.get('summary', 'Previous iteration')[: 500]}

ITERATION {iteration_number} (Current):
- Frameworks: {', '.join(current_frameworks) if current_frameworks else 'Updated frameworks'}
- Data Points: {current_data_points}
- Summary: {current_result.get('summary', 'Current iteration')[:500]}

NEW IN THIS ITERATION:
- New Frameworks Added: {', '.join(new_frameworks) if new_frameworks else 'Refining existing frameworks'}
- Data Points Gained: {data_points_gained}

Please provide a DETAILED (1000+ words) checkpoint summary that includes:

1. **Progress Update** (200 words)
   - How far along is the planning process
   - What milestone was just completed
   - Overall project health/status

2. **Iteration {iteration_number} Accomplishments** (300 words)
   - New frameworks introduced and their contribution
   - New data sources discovered
   - New angles of analysis uncovered
   - Specific findings from this iteration
   - How this iteration built on previous work

3. **Emerging Pattern Analysis** (250 words)
   - What patterns are emerging across iterations
   - How understanding has deepened
   - Connection points between frameworks
   - Integration of multiple data sources

4. **Quality and Depth Improvements** (200 words)
   - How has analysis quality improved
   - Specificity of recommendations
   - Confidence in findings
   - Areas where depth has increased significantly

5. **Next Steps and Remaining Work** (200 words)
   - What will be addressed in remaining iterations
   - Key questions still to be answered
   - Final pieces needed for comprehensive plan
   - Expected depth/quality of final output

Provide a comprehensive narrative showing real progress, actual new discoveries, and genuine improvements from the previous iteration. Be specific to the goal and findings."""

        if debug:
            print(f"   🧠 Generating detailed checkpoint summary for iteration {iteration_number}...")

        # Call agent to get detailed analysis
        checkpoint_analysis = await asyncio.to_thread(
            agent.chat,
            prompt
        )

        if debug:
            print(f"   ✓ Checkpoint summary generated ({len(checkpoint_analysis)} characters)")

        return checkpoint_analysis

    except Exception as e:
        # Fallback summary if analysis fails
        return f"""Checkpoint {iteration_number} Summary:

Planning is progressing on the goal: {goal}

Current Status:
- Frameworks applied: {', '.join(current_result.get('frameworks_used', []))}
- Data points collected: {current_result.get('data_points_count', 0)}
- Analysis depth: Increasing with each iteration
- Coverage: Expanding to cover more angles

The planning system has completed iteration {iteration_number} and identified key insights and frameworks for the goal. The next phase will continue to deepen analysis and refine recommendations.

Error in detailed analysis: {str(e)}
"""


async def analyze_iteration_improvements(
    agent: Any,
    goal: str,
    iteration_number: int,
    current_result: Dict[str, Any],
    previous_result: Optional[Dict[str, Any]] = None,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Generate structured improvement data for progress display.

    Returns JSON showing what improved from previous iteration.
    """
    try:
        if not previous_result or iteration_number <= 1:
            # First checkpoint
            return {
                "is_first_checkpoint": True,
                "status": "Completed first iteration cycle - ready for deeper analysis",
                "frameworks_count": len(current_result.get("frameworks_used", [])),
                "data_points": current_result.get("data_points_count", 0)
            }

        current_frameworks = current_result.get("frameworks_used", [])
        previous_frameworks = previous_result.get("frameworks_used", [])
        current_data_points = current_result.get("data_points_count", 0)
        previous_data_points = previous_result.get("data_points_count", 0)

        comparison_prompt = f"""Analyze the improvements from iteration {iteration_number - 1} to {iteration_number}.

GOAL: {goal}

PREVIOUS: Frameworks={previous_frameworks}, Data Points={previous_data_points}
CURRENT: Frameworks={current_frameworks}, Data Points={current_data_points}

Respond with ONLY this JSON (no other text):
{{
    "research_improvements": "New research areas discovered",
    "frameworks_applied": "New frameworks and their value",
    "use_cases_found": "New applications discovered",
    "analytical_improvements": "How analysis deepened",
    "key_discovery": "Most important new insight",
    "depth_increase": 7
}}"""

        if debug:
            print(f"   📊 Analyzing improvements...")

        response = await asyncio.to_thread(
            agent.chat,
            comparison_prompt
        )

        # Parse JSON
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                improvements = json.loads(json_match.group())
            else:
                improvements = {"status": "Analysis in progress"}
        except json.JSONDecodeError:
            improvements = {"status": "Refinement ongoing"}

        return {
            "is_first_checkpoint": False,
            "improvements": improvements,
            "comparison": {
                "frameworks_added": len(set(current_frameworks) - set(previous_frameworks)),
                "data_points_gained": current_data_points - previous_data_points,
                "depth_score": improvements.get("depth_increase", 5)
            }
        }

    except Exception as e:
        return {
            "is_first_checkpoint": False,
            "status": f"Improvements analysis ongoing: {str(e)}"
        }
