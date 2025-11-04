"""VAL-Style Verification for PDDL-INSTRUCT Reasoning

Phase 2 Implementation: Logical validation of planning outputs
- Precondition checking
- Effect verification
- Reasoning chain validation
- Detailed feedback generation

Reference: PDDL-INSTRUCT uses VAL (PDDL Validator) for formal verification
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class FeedbackLevel(Enum):
    """Level of detail in feedback."""
    BINARY = "binary"  # Just correct/incorrect
    DETAILED = "detailed"  # What went wrong


class VerificationResult(Enum):
    """Result of a verification check."""
    PASS = "pass"  # Check passed
    FAIL = "fail"  # Check failed
    UNCERTAIN = "uncertain"  # Cannot determine


@dataclass
class PreconditionCheck:
    """Result of checking a single precondition."""
    name: str
    description: str
    result: VerificationResult
    explanation: str


@dataclass
class EffectCheck:
    """Result of checking a single effect."""
    name: str
    description: str
    result: VerificationResult
    explanation: str


@dataclass
class VerificationReport:
    """Complete verification report for a plan."""
    timestamp: str
    precondition_checks: List[PreconditionCheck]
    effect_checks: List[EffectCheck]
    reasoning_quality_score: float  # 0-1
    overall_validity: bool  # True if all checks pass
    detailed_feedback: str


class VerificationFeedback:
    """VAL-like verification for logical reasoning.

    Key Features:
    - Precondition verification (are prerequisites met?)
    - Effect verification (do expected outcomes occur?)
    - Reasoning chain validation (are steps logical?)
    - Detailed feedback generation

    Design:
    - Binary feedback: simple correct/incorrect
    - Detailed feedback: what specifically went wrong
    - Confidence scoring: how sure we are
    """

    def __init__(self, domain: str = "general"):
        """Initialize verification system.

        Args:
            domain: Planning domain (for domain-specific checks)
        """
        self.domain = domain
        self.verification_history: List[VerificationReport] = []

    def check_preconditions(self,
                           preconditions: Dict[str, bool],
                           context: Dict[str, Any]) -> Tuple[List[PreconditionCheck], bool]:
        """Verify preconditions are met.

        Args:
            preconditions: Dict mapping precondition names to expected values
            context: Planning context to verify against

        Returns:
            Tuple of (detailed checks, all_passed)
        """
        checks = []
        all_passed = True

        for name, expected_met in preconditions.items():
            # Simple check: does context have evidence this precondition is met?
            context_lower = {k.lower(): v for k, v in context.items()}
            keywords = set(name.lower().split('_'))

            # Check if any context key matches precondition name
            found = False
            evidence = None

            for ctx_key, ctx_val in context_lower.items():
                if any(kw in ctx_key for kw in keywords):
                    found = True
                    evidence = str(ctx_val)[:100]  # First 100 chars
                    break

            if found == expected_met:
                result = VerificationResult.PASS
                explanation = f"Precondition '{name}' is {'satisfied' if expected_met else 'correctly not required'}"
                if evidence:
                    explanation += f". Evidence: {evidence}"
            else:
                result = VerificationResult.FAIL
                explanation = f"Precondition '{name}' is {'NOT satisfied' if expected_met else 'unexpectedly required'}"
                all_passed = False

            checks.append(PreconditionCheck(
                name=name,
                description=name.replace('_', ' ').title(),
                result=result,
                explanation=explanation
            ))

        return checks, all_passed

    def check_effects(self,
                     expected_effects: Dict[str, Any],
                     actual_outcome: str) -> Tuple[List[EffectCheck], bool]:
        """Verify effects of planning occurred.

        Args:
            expected_effects: Effects that should occur
            actual_outcome: What actually happened (plan content)

        Returns:
            Tuple of (detailed checks, all_occurred)
        """
        checks = []
        all_occurred = True

        for effect_name, effect_expected in expected_effects.items():
            # Check if effect is mentioned in actual outcome
            effect_keywords = set(effect_name.lower().split('_'))
            outcome_words = set(actual_outcome.lower().split())

            # Simple match: does outcome mention the effect?
            mentioned = any(kw in outcome_words for kw in effect_keywords)

            if mentioned == effect_expected:
                result = VerificationResult.PASS
                explanation = f"Effect '{effect_name}' is {'achieved' if effect_expected else 'correctly not achieved'}"
            else:
                result = VerificationResult.FAIL
                explanation = f"Effect '{effect_name}' is {'NOT achieved' if effect_expected else 'unexpectedly achieved'}"
                all_occurred = False

            checks.append(EffectCheck(
                name=effect_name,
                description=effect_name.replace('_', ' ').title(),
                result=result,
                explanation=explanation
            ))

        return checks, all_occurred

    def validate_reasoning_chain(self,
                                reasoning_steps: List[str]) -> float:
        """Validate logical coherence of reasoning chain.

        Args:
            reasoning_steps: List of reasoning steps

        Returns:
            Quality score (0-1)
        """
        if not reasoning_steps or len(reasoning_steps) < 2:
            return 0.3

        score = 0.5  # Base score

        # Check for proper progression (steps get more specific)
        avg_step_length = sum(len(step) for step in reasoning_steps) / len(reasoning_steps)
        if avg_step_length > 50:  # Substantial reasoning
            score += 0.2

        # Check for logical markers (therefore, thus, consequently, etc.)
        logical_markers = {'therefore', 'thus', 'consequently', 'as a result', 'this means',
                          'which', 'implying', 'resulting in', 'leading to'}
        step_text = ' '.join(reasoning_steps).lower()

        marker_count = sum(1 for marker in logical_markers if marker in step_text)
        if marker_count >= 2:
            score += 0.15

        # Check for potential contradictions
        contradictions = self._find_contradictions(step_text)
        if contradictions == 0:
            score += 0.15
        else:
            score -= contradictions * 0.05

        return min(1.0, max(0.0, score))

    def generate_binary_feedback(self, validity: bool) -> str:
        """Generate simple correct/incorrect feedback.

        Args:
            validity: Whether plan is valid

        Returns:
            Simple feedback string
        """
        return "✅ Correct" if validity else "❌ Incorrect"

    def generate_detailed_feedback(self,
                                  precondition_checks: List[PreconditionCheck],
                                  effect_checks: List[EffectCheck],
                                  reasoning_score: float) -> str:
        """Generate detailed feedback on what went wrong/right.

        Args:
            precondition_checks: Results of precondition verification
            effect_checks: Results of effect verification
            reasoning_score: Quality score of reasoning

        Returns:
            Detailed feedback text
        """
        output = []

        # Precondition summary
        precond_passed = sum(1 for c in precondition_checks if c.result == VerificationResult.PASS)
        output.append(f"## Preconditions: {precond_passed}/{len(precondition_checks)} ✓")

        for check in precondition_checks:
            status = "✅" if check.result == VerificationResult.PASS else "❌"
            output.append(f"  {status} {check.name}: {check.explanation}")

        output.append("")

        # Effect summary
        effects_passed = sum(1 for c in effect_checks if c.result == VerificationResult.PASS)
        output.append(f"## Effects: {effects_passed}/{len(effect_checks)} ✓")

        for check in effect_checks:
            status = "✅" if check.result == VerificationResult.PASS else "❌"
            output.append(f"  {status} {check.name}: {check.explanation}")

        output.append("")

        # Reasoning quality
        output.append(f"## Reasoning Quality: {reasoning_score:.1%}")
        if reasoning_score >= 0.8:
            output.append("  Strong logical coherence and clear progression")
        elif reasoning_score >= 0.6:
            output.append("  Reasonable logic with some gaps")
        else:
            output.append("  Weak logical structure - needs improvement")

        return "\n".join(output)

    def generate_verification_report(self,
                                    preconditions: Dict[str, bool],
                                    expected_effects: Dict[str, Any],
                                    actual_outcome: str,
                                    reasoning_steps: List[str],
                                    context: Dict[str, Any]) -> VerificationReport:
        """Generate complete verification report.

        Args:
            preconditions: Preconditions to check
            expected_effects: Expected effects to verify
            actual_outcome: Actual plan outcome
            reasoning_steps: Reasoning chain steps
            context: Planning context

        Returns:
            Complete VerificationReport
        """
        # Run all checks
        precond_checks, precond_all_passed = self.check_preconditions(preconditions, context)
        effect_checks, effects_all_occurred = self.check_effects(expected_effects, actual_outcome)
        reasoning_quality = self.validate_reasoning_chain(reasoning_steps)

        # Determine overall validity
        overall_validity = precond_all_passed and effects_all_occurred and reasoning_quality > 0.5

        # Generate feedback
        detailed_feedback = self.generate_detailed_feedback(
            precond_checks, effect_checks, reasoning_quality
        )

        # Create report
        report = VerificationReport(
            timestamp=datetime.now().isoformat(),
            precondition_checks=precond_checks,
            effect_checks=effect_checks,
            reasoning_quality_score=reasoning_quality,
            overall_validity=overall_validity,
            detailed_feedback=detailed_feedback
        )

        # Store in history
        self.verification_history.append(report)

        return report

    def _find_contradictions(self, text: str) -> int:
        """Find potential logical contradictions in text.

        Args:
            text: Text to analyze

        Returns:
            Number of potential contradictions found
        """
        contradiction_patterns = [
            ('must' in text and 'cannot' in text),
            ('always' in text and 'never' in text),
            ('increase' in text and 'decrease' in text),
            ('yes' in text and 'no' in text),
        ]

        return sum(1 for pattern in contradiction_patterns if pattern)

    def score_plan_validity(self,
                           precondition_results: List[PreconditionCheck],
                           effect_results: List[EffectCheck],
                           reasoning_quality: float) -> float:
        """Calculate overall plan validity score (0-1).

        Args:
            precondition_results: Precondition check results
            effect_results: Effect check results
            reasoning_quality: Reasoning quality score

        Returns:
            Overall validity score
        """
        precond_score = sum(1 for c in precondition_results if c.result == VerificationResult.PASS) / len(precondition_results) if precondition_results else 0.5

        effect_score = sum(1 for c in effect_results if c.result == VerificationResult.PASS) / len(effect_results) if effect_results else 0.5

        # Weighted average
        validity = (
            precond_score * 0.3 +
            effect_score * 0.3 +
            reasoning_quality * 0.4
        )

        return validity

    def get_verification_summary(self) -> Dict[str, Any]:
        """Get summary of all verifications performed.

        Returns:
            Summary statistics
        """
        if not self.verification_history:
            return {'total_reports': 0}

        total = len(self.verification_history)
        passed = sum(1 for r in self.verification_history if r.overall_validity)

        avg_reasoning = sum(r.reasoning_quality_score for r in self.verification_history) / total

        return {
            'total_reports': total,
            'passed': passed,
            'pass_rate': passed / total,
            'avg_reasoning_quality': avg_reasoning,
            'most_common_failure': self._find_most_common_failure(),
        }

    def _find_most_common_failure(self) -> Optional[str]:
        """Find most common type of failure across history.

        Returns:
            Most common failure type, or None if all pass
        """
        failures = []

        for report in self.verification_history:
            for check in report.precondition_checks:
                if check.result == VerificationResult.FAIL:
                    failures.append(f"Precondition: {check.name}")

            for check in report.effect_checks:
                if check.result == VerificationResult.FAIL:
                    failures.append(f"Effect: {check.name}")

        if not failures:
            return None

        # Return most common
        from collections import Counter
        return Counter(failures).most_common(1)[0][0]
