"""
Llama Planner - Core Orchestration Engine

Bridges Llama's decisions with system capabilities:
1. Provides tool interfaces (search_memory, research, call_agents)
2. Manages approval workflow
3. Handles iterative research
4. Calls specialized agents dynamically
5. Tracks learning outcomes

This is where Llama's decisions become actions.
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from pathlib import Path

from agent.agent import Agent
from research_agent import ResearchAgent, ResearchResult

# Import existing agents (these are the specialized tools)
from orchestrator.agents import (
    PlannerAgent,
    VerifierAgent,
    ExecutorAgent,
    GeneratorAgent,
    BaseAgent,
    AgentResult
)


class ApprovalStatus(Enum):
    """Approval workflow status"""
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    ADJUSTED = "adjusted"


@dataclass
class PlanningApproach:
    """Llama's proposed approach for a planning task"""
    goal: str
    memory_entities: List[str]
    memory_percentage: float
    research_percentage: float
    research_focus: Optional[List[str]]
    agents_to_use: List[str]  # ["PlannerAgent", "VerifierAgent", etc]
    resource_estimate: Dict[str, Any]
    status: ApprovalStatus = ApprovalStatus.PROPOSED
    user_feedback: Optional[str] = None
    adjustments: Optional[Dict[str, Any]] = None
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self):
        """Convert to dict for JSON serialization"""
        return {
            "goal": self.goal,
            "memory_entities": self.memory_entities,
            "memory_percentage": self.memory_percentage,
            "research_percentage": self.research_percentage,
            "research_focus": self.research_focus,
            "agents_to_use": self.agents_to_use,
            "resource_estimate": self.resource_estimate,
            "status": self.status.value,
            "user_feedback": self.user_feedback,
            "adjustments": self.adjustments,
            "created_at": self.created_at
        }


@dataclass
class PlanningOutcome:
    """Result of a complete planning iteration"""
    goal: str
    approach: PlanningApproach
    memory_results: Dict[str, Any]
    research_results: Optional[ResearchResult]
    agent_results: Dict[str, AgentResult]
    final_output: str
    quality_score: Optional[float] = None
    user_rating: Optional[int] = None  # 1-5 stars
    feedback: Optional[str] = None
    completed_at: str = ""

    def __post_init__(self):
        if not self.completed_at:
            self.completed_at = datetime.now().isoformat()

    def to_dict(self):
        """Convert to dict for JSON serialization"""
        return {
            "goal": self.goal,
            "approach": self.approach.to_dict(),
            "memory_results": self.memory_results,
            "research_results": {
                "summary": self.research_results.summary if self.research_results else None,
                "sources": self.research_results.sources if self.research_results else None,
                "coverage": self.research_results.coverage if self.research_results else None,
            },
            "agent_results": {
                name: {
                    "output": result.output,
                    "success": result.success,
                    "error": result.error if not result.success else None
                }
                for name, result in self.agent_results.items()
            },
            "final_output": self.final_output,
            "quality_score": self.quality_score,
            "user_rating": self.user_rating,
            "feedback": self.feedback,
            "completed_at": self.completed_at
        }


class LlamaPlanner:
    """
    Core planning orchestrator that bridges Llama's decisions with system tools.

    Llama uses this to:
    1. Search selected memory entities
    2. Perform iterative web research
    3. Call specialized planning agents
    4. Get user approval before execution
    5. Track learning outcomes
    """

    def __init__(
        self,
        agent: Agent,
        memory_path: str,
        learning_log_path: Optional[str] = None
    ):
        self.agent = agent
        self.memory_path = memory_path
        self.research_agent = ResearchAgent(verbose=False)

        # Initialize specialized agents
        self.planning_agent = PlannerAgent(agent, memory_path)
        self.verifier_agent = VerifierAgent(agent, memory_path)
        self.executor_agent = ExecutorAgent(agent, memory_path)
        self.generator_agent = GeneratorAgent(agent, memory_path)

        # Learning tracking
        self.learning_log_path = learning_log_path or f"{memory_path}/learning_log.json"
        self.learning_history = self._load_learning_history()

        # Current planning state
        self.current_approach: Optional[PlanningApproach] = None
        self.current_memory_results: Optional[Dict] = None

    # ========================================
    # TOOL 1: Search Memory
    # ========================================

    def search_memory(
        self,
        entities: List[str],
        queries: List[str]
    ) -> Dict[str, Any]:
        """
        Search selected memory entities for relevant information.

        This is what Llama calls FIRST, before anything else.

        Args:
            entities: List of entity file names to search (without .md)
            queries: List of specific questions/search terms

        Returns:
            {
                "results": str - Found content
                "coverage": float - 0.0-1.0 estimate of completeness
                "entities_searched": int
                "gaps": list - What's still missing
                "sources": list - Entity names where content was found
            }
        """

        results = {
            "results": "",
            "coverage": 0.0,
            "entities_searched": 0,
            "gaps": queries.copy(),
            "sources": []
        }

        try:
            # Search each entity for the queries
            found_content = []
            entities_searched = 0

            for entity in entities:
                try:
                    # Read entity file
                    entity_path = Path(self.memory_path) / "entities" / f"{entity}.md"
                    if not entity_path.exists():
                        # Try without .md
                        entity_path = Path(self.memory_path) / "entities" / entity
                        if not entity_path.exists():
                            continue

                    with open(entity_path, 'r') as f:
                        content = f.read()

                    # Check if any query terms match this entity
                    found_relevant = False
                    for query in queries:
                        query_terms = set(query.lower().split())
                        content_terms = set(content.lower().split())

                        if any(term in content_terms for term in query_terms):
                            found_relevant = True
                            break

                    if found_relevant:
                        found_content.append(f"=== {entity}.md ===\n{content}\n")
                        results["sources"].append(entity)

                    entities_searched += 1

                except Exception as e:
                    pass

            results["results"] = "\n".join(found_content)
            results["entities_searched"] = entities_searched

            # Estimate coverage
            if found_content:
                # Rough heuristic: if we found content, assume >50% coverage
                results["coverage"] = 0.5 + (len(found_content) * 0.1)
                results["coverage"] = min(results["coverage"], 0.9)
            else:
                results["coverage"] = 0.0

            # Gaps = queries we didn't find good matches for
            if results["coverage"] < 0.7:
                results["gaps"] = [q for q in queries if not any(
                    term in results["results"].lower()
                    for term in q.lower().split()
                )]

            self.current_memory_results = results
            return results

        except Exception as e:
            results["error"] = str(e)
            return results

    # ========================================
    # TOOL 2: Iterative Research
    # ========================================

    def research(
        self,
        gaps: List[str],
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Perform iterative web research to fill identified gaps.

        This is what Llama calls after searching memory (if coverage insufficient).

        Args:
            gaps: List of specific gaps/questions to research
            max_iterations: Maximum search iterations

        Returns:
            {
                "summary": str - Research findings summary
                "sources": list - URLs found
                "key_data_points": list - Key numbers/data found
                "iterations": int - Searches performed
                "coverage": float - Estimated completeness
            }
        """

        try:
            result = self.research_agent.research(
                gaps=gaps,
                max_iterations=max_iterations
            )

            return {
                "summary": result.summary,
                "sources": result.sources,
                "key_data_points": result.key_data_points,
                "iterations": result.iterations_used,
                "coverage": result.coverage,
                "gaps_filled": result.gaps_filled,
                "gaps_remaining": result.gaps_remaining
            }

        except Exception as e:
            return {
                "error": str(e),
                "summary": "",
                "sources": [],
                "key_data_points": [],
                "iterations": 0,
                "coverage": 0.0
            }

    # ========================================
    # TOOL 3: Call Specialized Agents
    # ========================================

    def call_planner(
        self,
        goal: str,
        context: str,
        approach: str = ""
    ) -> Dict[str, Any]:
        """
        Call PlannerAgent to create strategic plan.

        Args:
            goal: User's goal/request
            context: JSON string or dict of context (memory + research)
            approach: How Llama wants to approach it (methodology guidance)

        Returns:
            {
                "plan": str - The actual plan
                "methodology": str - Approach used
                "success": bool
                "error": str - If failed
            }
        """

        try:
            # Parse context if string
            if isinstance(context, str):
                try:
                    context = json.loads(context)
                except:
                    pass

            # Format prompt for planner
            prompt = f"""
Create a strategic plan for the following:

GOAL: {goal}

CONTEXT:
{json.dumps(context, indent=2) if isinstance(context, dict) else context}

APPROACH: {approach}

Provide a detailed, actionable plan.
"""

            result = self.planning_agent.execute(prompt)

            return {
                "plan": result.output,
                "methodology": approach,
                "success": result.success,
                "error": result.error
            }

        except Exception as e:
            return {
                "plan": "",
                "methodology": approach,
                "success": False,
                "error": str(e)
            }

    def call_verifier(
        self,
        plan: str,
        context: str,
        criteria: str = ""
    ) -> Dict[str, Any]:
        """
        Call VerifierAgent to validate plan quality.

        Args:
            plan: The plan to verify
            context: Context (memory + research)
            criteria: What should the plan satisfy

        Returns:
            {
                "is_valid": bool
                "quality_score": float (0.0-1.0)
                "issues": list
                "recommendations": str
                "success": bool
            }
        """

        try:
            prompt = f"""
Verify the quality and feasibility of this plan:

PLAN:
{plan}

CONTEXT:
{json.dumps(context, indent=2) if isinstance(context, dict) else context}

VALIDATION CRITERIA: {criteria}

Assess feasibility, identify issues, and suggest improvements.
"""

            result = self.verifier_agent.execute(prompt)

            return {
                "is_valid": result.success,
                "quality_score": 0.75 if result.success else 0.3,
                "issues": [],
                "recommendations": result.output,
                "success": result.success
            }

        except Exception as e:
            return {
                "is_valid": False,
                "quality_score": 0.0,
                "issues": [str(e)],
                "recommendations": "",
                "success": False
            }

    def call_executor(
        self,
        plan: str,
        context: str,
        resources: str = ""
    ) -> Dict[str, Any]:
        """
        Call ExecutorAgent to create implementation details.

        Args:
            plan: The plan to implement
            context: Context information
            resources: Available resources

        Returns:
            {
                "implementation": str
                "timeline": str
                "resources_needed": str
                "success": bool
            }
        """

        try:
            prompt = f"""
Create detailed implementation steps for this plan:

PLAN:
{plan}

CONTEXT:
{json.dumps(context, indent=2) if isinstance(context, dict) else context}

AVAILABLE RESOURCES: {resources}

Provide specific steps, timeline, and resource requirements.
"""

            result = self.executor_agent.execute(prompt)

            return {
                "implementation": result.output,
                "timeline": "To be determined",
                "resources_needed": resources,
                "success": result.success
            }

        except Exception as e:
            return {
                "implementation": "",
                "timeline": "",
                "resources_needed": resources,
                "success": False
            }

    def call_generator(
        self,
        data: Dict[str, Any],
        format: str = "summary"
    ) -> Dict[str, Any]:
        """
        Call GeneratorAgent to synthesize results.

        Args:
            data: All gathered data to synthesize
            format: Output format (summary, detailed, etc)

        Returns:
            {
                "output": str - Synthesized result
                "sources_cited": str
                "confidence": float
                "success": bool
            }
        """

        try:
            prompt = f"""
Synthesize the following data into a {format}:

DATA:
{json.dumps(data, indent=2, default=str)}

Combine all information into a coherent, well-structured output.
"""

            result = self.generator_agent.execute(prompt)

            return {
                "output": result.output,
                "sources_cited": "See context in generated output",
                "confidence": 0.8 if result.success else 0.0,
                "success": result.success
            }

        except Exception as e:
            return {
                "output": "",
                "sources_cited": "",
                "confidence": 0.0,
                "success": False
            }

    # ========================================
    # APPROVAL & EXECUTION WORKFLOW
    # ========================================

    def propose_approach(
        self,
        goal: str,
        memory_results: Dict[str, Any],
        approach_plan: Dict[str, Any]
    ) -> PlanningApproach:
        """
        Create a formal approach proposal for user approval.

        Args:
            goal: The user's goal
            memory_results: Results from searching memory
            approach_plan: Dict with:
                - memory_percentage: float
                - research_percentage: float
                - research_focus: list of what to research
                - agents_to_use: list of agent names
                - resource_estimate: dict

        Returns:
            PlanningApproach object ready for approval
        """

        approach = PlanningApproach(
            goal=goal,
            memory_entities=memory_results.get("sources", []),
            memory_percentage=approach_plan.get("memory_percentage", 0.6),
            research_percentage=approach_plan.get("research_percentage", 0.4),
            research_focus=approach_plan.get("research_focus", []),
            agents_to_use=approach_plan.get("agents_to_use", []),
            resource_estimate=approach_plan.get("resource_estimate", {})
        )

        self.current_approach = approach
        return approach

    def get_approval(
        self,
        approach: PlanningApproach
    ) -> bool:
        """
        Wait for user approval of the proposed approach.

        In production, this would show UI and wait for user input.
        For now, returns approval status and captures feedback.

        Returns:
            True if approved, False if rejected/adjusted
        """

        # This will be integrated with simple_chatbox.py UI
        # For now, we provide the structure
        return approach.status == ApprovalStatus.APPROVED

    def process_user_feedback(
        self,
        approach: PlanningApproach,
        status: str,  # "approved", "rejected", "adjusted"
        feedback: Optional[str] = None
    ) -> PlanningApproach:
        """
        Process user feedback on the proposed approach.

        Args:
            approach: The approach being reviewed
            status: User's decision
            feedback: Optional feedback/adjustments

        Returns:
            Updated PlanningApproach
        """

        if status == "approved":
            approach.status = ApprovalStatus.APPROVED
        elif status == "rejected":
            approach.status = ApprovalStatus.REJECTED
        elif status == "adjusted":
            approach.status = ApprovalStatus.ADJUSTED
            approach.adjustments = json.loads(feedback) if feedback else {}

        approach.user_feedback = feedback
        self.current_approach = approach
        return approach

    # ========================================
    # LEARNING & OUTCOME TRACKING
    # ========================================

    def log_outcome(
        self,
        outcome: PlanningOutcome
    ) -> None:
        """
        Log planning outcome for learning and pattern analysis.

        Saves to learning_log.json for future analysis.
        """

        try:
            self.learning_history.append(outcome.to_dict())
            self._save_learning_history()
        except Exception as e:
            print(f"Warning: Failed to log outcome: {e}")

    def capture_user_rating(
        self,
        outcome: PlanningOutcome,
        rating: int,  # 1-5 stars
        feedback: str = ""
    ) -> PlanningOutcome:
        """
        Capture user feedback on plan quality.

        Args:
            outcome: The planning outcome
            rating: User's rating (1-5 stars)
            feedback: User's written feedback

        Returns:
            Updated outcome with rating
        """

        outcome.user_rating = rating
        outcome.feedback = feedback
        outcome.quality_score = rating / 5.0  # Convert to 0.0-1.0
        return outcome

    def analyze_learning_patterns(self) -> Dict[str, Any]:
        """
        Analyze learning history to find patterns.

        Returns patterns like:
        {
            "growth_strategy": {
                "avg_memory_percentage": 0.65,
                "avg_research_percentage": 0.35,
                "best_agents": ["PlannerAgent", "VerifierAgent"],
                "avg_quality_score": 0.78,
                "sample_size": 12
            },
            ...
        }
        """

        patterns = {}

        if not self.learning_history:
            return patterns

        # Group by goal type (simple heuristic: extract first few words)
        goals_by_type = {}
        for outcome in self.learning_history:
            goal = outcome.get("goal", "")
            goal_type = " ".join(goal.split()[:3]).lower()  # First 3 words

            if goal_type not in goals_by_type:
                goals_by_type[goal_type] = []
            goals_by_type[goal_type].append(outcome)

        # Analyze each goal type
        for goal_type, outcomes in goals_by_type.items():
            if len(outcomes) < 2:
                continue  # Need at least 2 samples

            memory_pcts = [o["approach"].get("memory_percentage", 0.5) for o in outcomes]
            research_pcts = [o["approach"].get("research_percentage", 0.5) for o in outcomes]
            agents_used = [o["approach"].get("agents_to_use", []) for o in outcomes]
            ratings = [o.get("user_rating", 3) for o in outcomes if o.get("user_rating")]

            patterns[goal_type] = {
                "avg_memory_percentage": sum(memory_pcts) / len(memory_pcts),
                "avg_research_percentage": sum(research_pcts) / len(research_pcts),
                "best_agents": self._most_common(agents_used),
                "avg_quality_score": sum(ratings) / len(ratings) if ratings else 0.5,
                "sample_size": len(outcomes)
            }

        return patterns

    def _most_common(self, lists: List[List[str]]) -> List[str]:
        """Find most commonly used agents across multiple lists."""
        from collections import Counter
        flat = [item for sublist in lists for item in sublist]
        if not flat:
            return []
        return [agent for agent, count in Counter(flat).most_common(2)]

    # ========================================
    # UTILITY METHODS
    # ========================================

    # ========================================
    # ENTITY SAVING (MemAgent Integration)
    # ========================================

    def save_plan(
        self,
        goal: str,
        plan_content: str,
        execution_metadata: Optional[Dict[str, Any]] = None,
        user_rating: Optional[int] = None,
        user_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save a completed plan to /local-memory/plans/ using MemAgent pattern.

        This is the primary method for persisting plans to memory after execution.

        Args:
            goal: The planning goal
            plan_content: The generated plan (3000-4000 words expected)
            execution_metadata: Dict with execution details like:
                - entities_searched: List of entity names
                - memory_coverage: float (0.0-1.0)
                - research_percentage: float
                - agents_called: List of agent names
                - execution_time_ms: int
            user_rating: Optional 1-5 star rating from user
            user_feedback: Optional text feedback from user

        Returns:
            {
                "status": "success" or "error",
                "plan_id": str,
                "plan_path": str,
                "learning_entity_saved": bool,
                "message": str,
                "error": str (if error)
            }
        """

        try:
            # Create plans directory if it doesn't exist
            plans_path = Path(self.memory_path) / "plans"
            plans_path.mkdir(parents=True, exist_ok=True)

            # Generate plan ID from goal and timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            goal_slug = goal[:50].lower().replace(' ', '_').replace('/', '_').replace('\\', '_')
            plan_id = f"plan_{goal_slug}_{timestamp}"
            plan_filename = f"{plan_id}.md"
            plan_file_path = plans_path / plan_filename

            # Prepare plan content with metadata
            metadata = execution_metadata or {}
            created_time = datetime.now().isoformat()

            plan_markdown = f"""# Plan: {goal}

**Plan ID:** {plan_id}
**Created:** {created_time}
**Status:** Completed

## Execution Metadata

- **Entities Searched:** {', '.join(metadata.get('entities_searched', []))}
- **Memory Coverage:** {metadata.get('memory_coverage', 0) * 100:.0f}%
- **Research Percentage:** {metadata.get('research_percentage', 0) * 100:.0f}%
- **Agents Called:** {', '.join(metadata.get('agents_called', []))}
- **Execution Time:** {metadata.get('execution_time_ms', 'N/A')} ms

## Plan Content

{plan_content}

---

## Plan Feedback

"""

            # Add user feedback if provided
            if user_rating:
                plan_markdown += f"- **User Rating:** {user_rating}/5 stars\n"
            if user_feedback:
                plan_markdown += f"- **User Feedback:** {user_feedback}\n"

            plan_markdown += f"\n*Generated by automated planning system.*\n"

            # Write plan to file
            plan_file_path.write_text(plan_markdown, encoding='utf-8')
            print(f"✅ Plan saved: {plan_filename}")

            # Create learning entity tracking this execution
            learning_entity_saved = self._save_learning_entity(
                goal=goal,
                plan_id=plan_id,
                execution_metadata=metadata,
                user_rating=user_rating,
                user_feedback=user_feedback
            )

            return {
                "status": "success",
                "plan_id": plan_id,
                "plan_path": str(plan_file_path),
                "plan_filename": plan_filename,
                "learning_entity_saved": learning_entity_saved,
                "message": f"Plan saved as {plan_filename}. Learning tracked."
            }

        except Exception as e:
            print(f"❌ Error saving plan: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "goal": goal
            }

    def _save_learning_entity(
        self,
        goal: str,
        plan_id: str,
        execution_metadata: Dict[str, Any],
        user_rating: Optional[int] = None,
        user_feedback: Optional[str] = None
    ) -> bool:
        """
        Save execution tracking data as a learning entity in /local-memory.

        This creates new entities that track what approaches worked for similar goals.

        Args:
            goal: The planning goal
            plan_id: ID of the saved plan
            execution_metadata: Execution details
            user_rating: User's feedback rating
            user_feedback: User's text feedback

        Returns:
            True if successful, False otherwise
        """

        try:
            from datetime import datetime

            # Create learning entity filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            learning_filename = f"execution_tracking_{plan_id}.md"

            learning_path = Path(self.memory_path) / "entities" / learning_filename

            # Create entities directory if it doesn't exist
            learning_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare learning entity content
            learning_content = f"""# Execution Tracking: {goal}

**Plan ID:** {plan_id}
**Tracked:** {datetime.now().isoformat()}

## Approach Used

- **Entities Searched:** {', '.join(execution_metadata.get('entities_searched', []))}
- **Memory Coverage:** {execution_metadata.get('memory_coverage', 0) * 100:.0f}%
- **Research Used:** {execution_metadata.get('research_percentage', 0) * 100:.0f}%
- **Agents Called:** {', '.join(execution_metadata.get('agents_called', []))}

## Outcome

"""

            if user_rating:
                learning_content += f"- **User Rating:** {user_rating}/5 ⭐\n"
            else:
                learning_content += f"- **User Rating:** Not yet rated\n"

            if user_feedback:
                learning_content += f"- **User Feedback:** {user_feedback}\n"

            learning_content += f"""
## Purpose

This entity tracks what worked for similar goals. Used by the learning system
to recommend approaches for future planning tasks with similar characteristics.

---
*Automatically generated for learning purposes.*
"""

            learning_path.write_text(learning_content, encoding='utf-8')
            print(f"📚 Learning entity saved: {learning_filename}")

            return True

        except Exception as e:
            print(f"⚠️  Warning: Failed to save learning entity: {e}")
            return False

    def _load_learning_history(self) -> List[Dict]:
        """Load learning history from file."""
        try:
            path = Path(self.learning_log_path)
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load learning history: {e}")
        return []

    def _save_learning_history(self) -> None:
        """Save learning history to file."""
        try:
            path = Path(self.learning_log_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(self.learning_history, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save learning history: {e}")


if __name__ == "__main__":
    # Example usage (requires actual agent setup)
    print("LlamaPlanner module loaded successfully")
