"""
Verifier Agent - Quality Assurance Specialist

Responsibilities:
- Validate plans against project requirements
- Check execution quality and completeness
- Verify compliance with standards
"""

import os
import sys
from pathlib import Path
from typing import Dict
from dataclasses import asdict

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from .base_agent import BaseAgent, AgentResult
from orchestrator.reasoning import VerificationFeedback, VerificationResult  # Phase 2: PDDL-INSTRUCT


class VerifierAgent(BaseAgent):
    """✅ Verifier Agent - The quality assurance specialist

    Responsibilities:
    - Validate plans against project requirements
    - Check execution quality and completeness
    - Verify compliance with standards
    - Provide detailed feedback for improvement
    """

    def verify_plan(self, plan: str, goal: str, context: Dict = None) -> AgentResult:
        """Verify a plan against project requirements and standards

        Args:
            plan: The strategic plan to verify
            goal: The original planning goal
            context: (Optional) Context dict that may include iteration information

        Returns:
            AgentResult with verification results
        """

        context = context or {}
        print(f"\n✅ VERIFIER AGENT: Validating strategic plan...")

        try:
            # Phase 2.4: Initialize VerificationFeedback for PDDL-INSTRUCT verification
            verifier = VerificationFeedback(domain=context.get('domain', 'general'))

            # Define preconditions for strategic planning
            preconditions = {
                "market_research_done": True,
                "requirements_defined": True,
                "context_analyzed": True
            }

            # Define expected effects for the plan
            expected_effects = {
                "strategic_plan_created": True,
                "success_metrics_defined": True,
                "timeline_established": True
            }

            # Create verification prompt with PDDL structure
            verification_prompt = f"""
You are the Verifier Agent in an advanced agentic system. Your role is to validate plans against project requirements and standards.

GOAL: {goal}

PLAN TO VERIFY:
{plan}

VERIFICATION CHECKLIST:
1. **PROJECT ALIGNMENT**: Does the plan align with project requirements?
2. **METHODOLOGY COMPLIANCE**: Does it use appropriate frameworks?
3. **DELIVERABLE COMPLETENESS**: Are all required deliverables addressed?
4. **TIMELINE REALISTIC**: Is the timeline achievable given constraints?
5. **RESOURCE ALLOCATION**: Are resources properly allocated?
6. **QUALITY STANDARDS**: Does it meet quality requirements?
7. **RISK MANAGEMENT**: Are risks properly identified and mitigated?
8. **CLIENT EXPECTATIONS**: Will it meet client expectations?
"""

            # ITERATION MODE: Add iteration-specific verification checks
            if context.get('iteration_mode'):
                iteration_num = context.get('iteration_number', 1)
                previous_plan = context.get('previous_plan', '')

                verification_prompt += f"""
9. **ITERATION PROGRESS** (Iteration {iteration_num}):
   - Is this plan demonstrably DEEPER than the previous iteration?
   - Does it add NEW insights, not repeat previous analysis?
   - Does it build on previous frameworks with additional specificity?
   - Are there NEW data points compared to iteration {iteration_num - 1}?

PREVIOUS ITERATION (for comparison):
{previous_plan[:1000]}...[truncated]

This verification must ensure we are PROGRESSING, not repeating.
"""

            verification_prompt += """
Provide detailed verification with:
- Overall assessment (VALID/INVALID)
- Specific compliance checks
- Missing elements or gaps
- Recommendations for improvement
- Risk assessment
"""

            if context.get('iteration_mode'):
                verification_prompt += f"\n- **Iteration Progress Assessment** (Iteration {context.get('iteration_number')}/{ context.get('max_iterations')}): Confirm plan is advancing\n"

            # Send to model for verification
            response = self.agent.chat(verification_prompt)
            verification_text = response.reply or "Verification failed"

            # Phase 2.4: Use VerificationFeedback to generate structured report
            verification_report = verifier.generate_verification_report(
                preconditions=preconditions,
                expected_effects=expected_effects,
                actual_outcome=verification_text,
                reasoning_steps=plan.split('\n')[:5],  # First 5 lines as reasoning steps
                context=context
            )

            # Determine if plan is valid based on verification report
            is_valid = verification_report.overall_validity

            # Serialize dataclass checks with enum handling
            precondition_check_dicts = []
            for check in verification_report.precondition_checks:
                check_dict = asdict(check)
                # Convert enum result to string
                if hasattr(check_dict.get('result'), 'value'):
                    check_dict['result'] = check_dict['result'].value
                precondition_check_dicts.append(check_dict)

            effect_check_dicts = []
            for check in verification_report.effect_checks:
                check_dict = asdict(check)
                # Convert enum result to string
                if hasattr(check_dict.get('result'), 'value'):
                    check_dict['result'] = check_dict['result'].value
                effect_check_dicts.append(check_dict)

            verification_metadata = {
                "goal": goal,
                "plan_length": len(plan),
                "is_valid": is_valid,
                "verification_length": len(verification_text),
                "checks_performed": self._count_verification_checks(verification_text),
                "precondition_checks": precondition_check_dicts,  # Phase 2.4: Store checks
                "effect_checks": effect_check_dicts,  # Phase 2.4: Store effects
                "reasoning_quality": verification_report.reasoning_quality_score  # Phase 2.4: Store quality score
            }

            result = self._wrap_result(
                success=True,
                output=verification_text,
                metadata=verification_metadata
            )

            # Log the verification action
            self._log_agent_action("verify_plan", result)

            status = "✅ VALID" if is_valid else "⚠️ INVALID"
            print(f"   {status} Plan verification completed")
            print(f"   ✅ {verification_metadata['checks_performed']} checks performed")

            return result

        except Exception as e:
            return self._handle_error("Verification", e)

    def verify_execution(self, execution_result: str, plan: str) -> AgentResult:
        """Verify execution results against the original plan

        Args:
            execution_result: The execution results to verify
            plan: The original plan that was executed

        Returns:
            AgentResult with execution verification results
        """

        print(f"\n✅ VERIFIER AGENT: Validating execution results...")

        try:
            verification_prompt = f"""
You are the Verifier Agent validating execution results against the original plan.

ORIGINAL PLAN:
{plan}

EXECUTION RESULTS:
{execution_result}

VERIFICATION CHECKLIST:
1. **COMPLETENESS**: Were all planned phases executed?
2. **QUALITY**: Do the deliverables meet expected standards?
3. **ACCURACY**: Are the outputs accurate and well-researched?
4. **FORMAT**: Do deliverables follow proper formats?
5. **TIMELINE**: Was execution completed within expected timeframe?
6. **RESOURCES**: Were resources used efficiently?
7. **CLIENT VALUE**: Will deliverables meet client needs?

Provide detailed assessment with:
- Overall execution quality (EXCELLENT/GOOD/SATISFACTORY/NEEDS_IMPROVEMENT)
- Specific quality metrics
- Areas of strength
- Areas needing improvement
- Recommendations for future executions
"""

            response = self.agent.chat(verification_prompt)
            verification_text = response.reply or "Execution verification failed"

            # Assess execution quality
            quality_score = self._assess_execution_quality(verification_text)

            verification_metadata = {
                "plan_length": len(plan),
                "execution_length": len(execution_result),
                "quality_score": quality_score,
                "verification_length": len(verification_text)
            }

            result = self._wrap_result(
                success=True,
                output=verification_text,
                metadata=verification_metadata
            )

            # Log the verification action
            self._log_agent_action("verify_execution", result)

            print(f"   ✅ Execution verification completed (Quality: {quality_score})")

            return result

        except Exception as e:
            return self._handle_error("Execution Verification", e)

    def _assess_validation(self, verification_text: str) -> bool:
        """Assess if plan is valid based on verification text

        Args:
            verification_text: Verification output text

        Returns:
            Boolean indicating if plan is valid
        """
        text_lower = verification_text.lower()
        if "invalid" in text_lower and "valid" not in text_lower:
            return False
        if "valid" in text_lower and "invalid" not in text_lower:
            return True
        # Default to valid if unclear
        return True

    def _assess_execution_quality(self, verification_text: str) -> str:
        """Assess execution quality based on verification text

        Args:
            verification_text: Verification output text

        Returns:
            Quality assessment string
        """
        text_lower = verification_text.lower()
        if "excellent" in text_lower:
            return "EXCELLENT"
        elif "good" in text_lower:
            return "GOOD"
        elif "satisfactory" in text_lower:
            return "SATISFACTORY"
        else:
            return "NEEDS_IMPROVEMENT"

    def _count_verification_checks(self, verification_text: str) -> int:
        """Count the number of verification checks mentioned

        Args:
            verification_text: Verification output text

        Returns:
            Number of checks performed
        """
        check_keywords = [
            "project alignment", "methodology compliance", "deliverable completeness",
            "timeline", "resource allocation", "quality standards", "risk management"
        ]
        count = 0
        for keyword in check_keywords:
            if keyword.lower() in verification_text.lower():
                count += 1
        return count
