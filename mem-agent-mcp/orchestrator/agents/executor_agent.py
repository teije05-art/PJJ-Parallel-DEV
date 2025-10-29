"""
Executor Agent - Implementation Specialist

Responsibilities:
- Execute plans by implementing actions
- Create deliverables
- Track execution progress
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


class ExecutorAgent(BaseAgent):
    """🛠️ Executor Agent - The implementation specialist

    Responsibilities:
    - Execute plans by calling appropriate tools
    - Implement actions and create deliverables
    - Coordinate with MemAgent for execution tracking
    - Provide detailed execution feedback
    """

    def execute_plan(self, plan: str, goal: str, context: Dict = None) -> AgentResult:
        """Execute a strategic plan using MemAgent tools and capabilities

        Args:
            plan: The strategic plan to execute
            goal: The original planning goal
            context: (Optional) Context dict that may include iteration information

        Returns:
            AgentResult with execution results
        """

        context = context or {}
        iteration_num = context.get('iteration_number', 1)
        max_iterations = context.get('max_iterations', 1)

        if context.get('iteration_mode'):
            print(f"\n🛠️ EXECUTOR AGENT: Executing iteration {iteration_num}/{max_iterations}...")
        else:
            print(f"\n🛠️ EXECUTOR AGENT: Executing strategic plan...")

        try:
            # Create execution prompt that uses MemAgent for actual work
            execution_prompt = f"""
You are the Executor Agent in an advanced agentic system. Your role is to actually implement plans and create real deliverables using MemAgent capabilities.

GOAL: {goal}

STRATEGIC PLAN TO EXECUTE:
{plan}

INSTRUCTIONS:
Actually execute this plan by:

1. **CREATE REAL DELIVERABLES**: Use MemAgent to create actual work products, not just descriptions
2. **IMPLEMENT EACH PHASE**: Execute each phase of the plan systematically
3. **APPLY METHODOLOGIES**: Apply specific frameworks and tools
4. **TRACK PROGRESS**: Record each step and its outcomes
5. **GENERATE CONCRETE OUTPUTS**: Create documents, analyses, frameworks, etc.

EXECUTION APPROACH:
For each phase in the plan, create the specific deliverables mentioned:
- Market analysis reports (if applicable)
- Competitive intelligence analysis (if applicable)
- Risk assessment methodology (if applicable)
- Project framework documents (if applicable)
- Implementation timelines (if applicable)
- Quality assurance checklists (if applicable)
- Survey/interview guides (if applicable)
- Case studies (if applicable)

Use MemAgent operations to:
- CREATE entities for each deliverable
- STORE detailed content and analysis
- TRACK execution progress
- GENERATE actionable recommendations

This is REAL execution - create actual work products that meet high standards.
"""

            response = self.agent.chat(execution_prompt)
            execution_text = response.reply or "Execution failed"

            # Parse execution results
            execution_metadata = {
                "goal": goal,
                "plan_length": len(plan),
                "execution_length": len(execution_text),
                "deliverables_created": self._count_deliverables(execution_text),
                "phases_executed": self._count_phases(plan)
            }

            result = self._wrap_result(
                success=True,
                output=execution_text,
                metadata=execution_metadata
            )

            # Log the execution action
            self._log_agent_action("execute_plan", result)

            print(f"   ✅ Plan executed ({execution_metadata['deliverables_created']} deliverables)")
            print(f"   ✅ {execution_metadata['phases_executed']} phases completed")

            return result

        except Exception as e:
            return self._handle_error("Execution", e)

    def _count_deliverables(self, execution_text: str) -> int:
        """Count the number of deliverables mentioned in execution text

        Args:
            execution_text: Execution output text

        Returns:
            Number of deliverables
        """
        deliverable_keywords = [
            "market analysis", "competitive intelligence", "risk assessment",
            "project framework", "implementation timeline", "quality assurance",
            "survey guide", "interview guide", "case study", "report"
        ]
        count = 0
        for keyword in deliverable_keywords:
            if keyword.lower() in execution_text.lower():
                count += 1
        return count

    def _count_phases(self, plan_text: str) -> int:
        """Count the number of phases in the plan

        Args:
            plan_text: Plan text

        Returns:
            Number of phases
        """
        return plan_text.lower().count("phase")
