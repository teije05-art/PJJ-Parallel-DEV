"""
Generator Agent - Content Synthesis Specialist

Responsibilities:
- Synthesize information from all agents
- Generate final deliverables and reports
- Create comprehensive documentation
"""

import os
import sys
from pathlib import Path
from typing import Dict

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from .base_agent import BaseAgent, AgentResult


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
        """Synthesize results from all agents into final deliverables

        Args:
            planner_result: Results from Planner Agent
            executor_result: Results from Executor Agent
            verifier_result: Results from Verifier Agent
            goal: The original planning goal
            context: (Optional) Context dict that may include iteration information

        Returns:
            AgentResult with synthesized final results
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
            synthesis_prompt = f"""
You are the Generator Agent in an advanced agentic system. Your role is to synthesize results from all agents into comprehensive final deliverables.

GOAL: {goal}

PLANNER AGENT RESULTS:
{planner_result.output}

EXECUTOR AGENT RESULTS:
{executor_result.output}

VERIFIER AGENT RESULTS:
{verifier_result.output}

SYNTHESIS INSTRUCTIONS:
Create comprehensive final deliverables that:

1. **INTEGRATE ALL PERSPECTIVES**: Combine planning, execution, and verification insights
2. **CREATE PROFESSIONAL DOCUMENTS**: Generate standard deliverables
3. **PROVIDE EXECUTIVE SUMMARY**: Clear overview for stakeholders
4. **INCLUDE DETAILED ANALYSIS**: Comprehensive technical details
5. **ADD IMPLEMENTATION GUIDANCE**: Practical next steps and recommendations
6. **ENSURE QUALITY**: Meet all standards and client expectations

DELIVERABLES TO CREATE:
- Executive Summary Report
- Detailed Implementation Plan
- Risk Assessment and Mitigation Strategy
- Quality Assurance Framework
- Timeline and Resource Allocation
- Success Metrics and KPIs
- Recommendations and Next Steps

Use MemAgent to store each deliverable as a separate entity for easy access and reference.
"""

            response = self.agent.chat(synthesis_prompt)
            synthesis_text = response.reply or "Synthesis failed"

            # Parse synthesis results
            synthesis_metadata = {
                "goal": goal,
                "planner_success": planner_result.success,
                "executor_success": executor_result.success,
                "verifier_success": verifier_result.success,
                "synthesis_length": len(synthesis_text),
                "deliverables_created": self._count_synthesis_deliverables(synthesis_text)
            }

            result = self._wrap_result(
                success=True,
                output=synthesis_text,
                metadata=synthesis_metadata
            )

            # Log the synthesis action
            self._log_agent_action("synthesize_results", result)

            print(f"   ✅ Results synthesized ({synthesis_metadata['deliverables_created']} deliverables)")
            print(f"   ✅ All agent results integrated")

            return result

        except Exception as e:
            return self._handle_error("Synthesis", e)

    def _count_synthesis_deliverables(self, synthesis_text: str) -> int:
        """Count the number of deliverables created in synthesis

        Args:
            synthesis_text: Synthesis output text

        Returns:
            Number of deliverables
        """
        deliverable_keywords = [
            "executive summary", "implementation plan", "risk assessment",
            "quality assurance", "timeline", "success metrics", "recommendations"
        ]
        count = 0
        for keyword in deliverable_keywords:
            if keyword.lower() in synthesis_text.lower():
                count += 1
        return count
