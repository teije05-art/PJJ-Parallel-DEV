"""
Generator Agent - Content Synthesis Specialist

Responsibilities:
- Synthesize information from all agents
- Generate final deliverables and reports
- Create comprehensive documentation

PHASE 2 (Nov 5, 2025): Synthesizes from Deliverable objects (from Phase 1 executor)
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Union

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from agent.model import get_model_response
from .base_agent import BaseAgent, AgentResult

# Import Deliverable class from executor (Phase 1)
try:
    from .executor_agent import Deliverable
except ImportError:
    # Fallback if import structure changes
    Deliverable = None


# Helper Functions for Phase 2

def format_deliverables_for_synthesis(deliverables: List[Any]) -> str:
    """Format Deliverable objects as readable text for LLM synthesis (Phase 2)

    Takes the executor's Deliverable objects and formats them nicely for
    the synthesis prompt, including all content, citations, and metrics.

    Args:
        deliverables: List of Deliverable objects from executor

    Returns:
        Formatted string with all deliverable content
    """
    if not deliverables:
        return "No deliverables provided"

    formatted = "COMPLETED DELIVERABLES:\n"
    formatted += "=" * 70 + "\n\n"

    for i, deliverable in enumerate(deliverables, 1):
        # Handle both Deliverable objects and dict-like objects
        title = deliverable.title if hasattr(deliverable, 'title') else deliverable.get('title', f'Deliverable {i}')
        content = deliverable.content if hasattr(deliverable, 'content') else deliverable.get('content', '')
        citations = deliverable.citations if hasattr(deliverable, 'citations') else deliverable.get('citations', [])
        metrics = deliverable.metrics if hasattr(deliverable, 'metrics') else deliverable.get('metrics', {})

        formatted += f"## {i}. {title}\n\n"
        formatted += f"{content}\n\n"

        if citations:
            formatted += f"**Sources:** {', '.join(citations[:3])}\n"

        if metrics:
            formatted += f"**Key Metrics:** {metrics}\n"

        formatted += "\n" + "-" * 70 + "\n\n"

    return formatted


def get_iteration_guidance(iteration_num: int, max_iterations: int) -> str:
    """Get iteration-specific guidance for synthesis (Phase 2)

    For iteration 1: Focus on comprehensive overview
    For iteration 2+: Emphasize what's NEW and what's DEEPER

    Args:
        iteration_num: Current iteration number
        max_iterations: Total iterations planned

    Returns:
        Iteration-specific guidance text
    """
    if iteration_num == 1:
        return """
This is the FIRST iteration of planning. Focus on:
- Comprehensive market overview
- Clear understanding of opportunities and constraints
- Basic feasibility assessment
- Initial strategic direction
"""
    else:
        return f"""
This is iteration {iteration_num} of {max_iterations}. You should:
- Build on insights from previous iterations (iteration 1)
- Go DEEPER into analysis and strategy
- ADD NEW FRAMEWORKS and approaches not covered before
- Emphasize what has changed in your understanding
- Provide more specific, tactical recommendations
- Increase level of detail and specificity

Make this iteration SUBSTANTIVELY DIFFERENT from iteration 1, not just a repetition.
"""


class GeneratorAgent(BaseAgent):
    """✍️ Generator Agent - The content synthesis specialist

    Responsibilities:
    - Synthesize information from all agents
    - Generate final deliverables and reports
    - Create comprehensive documentation
    - Coordinate final output creation
    """

    def synthesize_results(self, planner_result: AgentResult, executor_result: AgentResult,
                          verifier_result: AgentResult, goal: str, context: Dict = None) -> AgentResult:
        """Synthesize results from all agents into final deliverables (Phase 2)

        PHASE 2 (Nov 5, 2025): Receives Deliverable objects from executor (Phase 1)
        - Extracts deliverables from executor_result
        - Formats them for synthesis
        - Creates LLM synthesis that uses deliverable content
        - Varies synthesis based on iteration number

        Args:
            planner_result: Results from Planner Agent (text)
            executor_result: Results from Executor Agent (list of Deliverable objects in Phase 1)
            verifier_result: Results from Verifier Agent (text)
            goal: The original planning goal
            context: (Optional) Context dict with iteration_number, max_iterations, etc.

        Returns:
            AgentResult with synthesized final plan text
        """

        context = context or {}
        iteration_num = context.get('iteration_number', 1)
        max_iterations = context.get('max_iterations', 1)
        is_final = iteration_num >= max_iterations

        if context.get('iteration_mode'):
            if is_final:
                print(f"\n✍️ GENERATOR AGENT: Synthesizing FINAL results (Iteration {iteration_num}/{max_iterations})...")
            else:
                print(f"\n✍️ GENERATOR AGENT: Synthesizing iteration {iteration_num}/{max_iterations} results...")
        else:
            print(f"\n✍️ GENERATOR AGENT: Synthesizing final results...")

        try:
            # PHASE 2: Extract deliverables from executor_result
            # In Phase 1, executor returns Deliverable objects in executor_result.output
            deliverables = executor_result.output if isinstance(executor_result.output, list) else []
            deliverable_count = len(deliverables) if deliverables else 0

            if deliverables:
                print(f"   📦 Received {deliverable_count} deliverables from executor")
                # Format deliverables for synthesis
                formatted_deliverables = format_deliverables_for_synthesis(deliverables)
            else:
                print(f"   ⚠️ No deliverables received from executor, using fallback")
                formatted_deliverables = "No structured deliverables available"

            # Get iteration-specific guidance
            iteration_guidance = get_iteration_guidance(iteration_num, max_iterations)

            # Build synthesis prompt that USES the deliverable data
            synthesis_prompt = f"""
You are the Generator Agent. Your role is to synthesize completed planning deliverables into a comprehensive final strategic plan.

PLANNING GOAL: {goal}

ITERATION: {iteration_num} of {max_iterations}

COMPLETED DELIVERABLES (from execution phase):
{formatted_deliverables}

PLANNER'S STRATEGIC DIRECTION:
{planner_result.output[:1000]}...

PLANNING VALIDATION (from verification):
{verifier_result.output[:500]}...

ITERATION GUIDANCE:
{iteration_guidance}

YOUR TASK - SYNTHESIZE INTO COMPREHENSIVE PLAN:

1. **USE THE DELIVERABLE CONTENT**: Build your final plan around the actual deliverables above
2. **INTEGRATE INSIGHTS**: Combine all perspectives into coherent narrative
3. **MAINTAIN DATA INTEGRITY**: Keep specific metrics, numbers, and citations from deliverables
4. **PROFESSIONAL STRUCTURE**: Organize as comprehensive strategic plan with clear sections
5. **ITERATION-SPECIFIC FOCUS**: {f"For iteration 1: Broad overview. For iteration {iteration_num}: Emphasize depth and NEW insights." if iteration_num > 1 else "Establish clear strategic foundation"}

CREATE A COMPREHENSIVE FINAL PLAN that:
- Synthesizes the deliverables into unified strategic vision
- Maintains all key data and metrics from source deliverables
- Provides actionable next steps
- Is suitable for iteration {iteration_num} of planning
- Shows progression from iteration 1 if this is iteration {iteration_num}+ (NEW analysis, DEEPER insights)

Format as professional, data-driven strategic plan.
"""

            # Call LLM to synthesize
            response = self.agent.chat(synthesis_prompt)
            synthesis_text = response.reply or "Synthesis failed"

            # Parse synthesis results
            synthesis_metadata = {
                "goal": goal,
                "iteration": iteration_num,
                "planner_success": planner_result.success,
                "executor_success": executor_result.success,
                "executor_deliverables": deliverable_count,
                "verifier_success": verifier_result.success,
                "synthesis_length": len(synthesis_text),
                "phase": "2_generator_synthesis"
            }

            result = self._wrap_result(
                success=True,
                output=synthesis_text,
                metadata=synthesis_metadata
            )

            # Log the synthesis action
            self._log_agent_action("synthesize_results", result)

            print(f"   ✅ Synthesized from {deliverable_count} deliverables")
            print(f"   ✅ Final plan: {len(synthesis_text)} chars")

            return result

        except Exception as e:
            return self._handle_error("Synthesis", e)
