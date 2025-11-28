"""PDDL-INSTRUCT Logical Planning for Project Jupiter

Phase 2 Implementation: Symbolic Planning with Chain-of-Thought Reasoning
- Precondition checking
- Effect verification
- Reasoning chain generation
- Logical soundness validation

Reference: PDDL-INSTRUCT: Teaching LLMs to Plan with Logical Chain-of-Thought
Instruction Tuning (2509.13351v1)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ReasoningLevel(Enum):
    """Level of detail in reasoning output."""
    BRIEF = "brief"  # Just the plan
    STANDARD = "standard"  # Plan + reasoning chain
    DETAILED = "detailed"  # Full reasoning with verification


@dataclass
class Precondition:
    """A precondition that must be met for an action."""
    name: str  # e.g., "market_research_complete"
    description: str  # Human-readable description
    how_to_verify: str  # How to check if it's met
    met: Optional[bool] = None  # Whether this precondition is met


@dataclass
class Effect:
    """An effect that should result from an action."""
    name: str  # e.g., "strategic_roadmap_created"
    description: str  # What this effect means
    how_to_verify: str  # How to check if it occurred
    occurred: Optional[bool] = None  # Whether this effect actually occurred


@dataclass
class ReasoningChainStep:
    """A single step in a logical reasoning chain."""
    number: int  # Step number (1, 2, 3, ...)
    action: str  # The action taken
    reasoning: str  # Why this action makes sense
    expected_outcome: str  # What should result from this
    depends_on: List[int]  # Which previous steps this depends on


class LogicalPlanningPrompt:
    """Generates PDDL-style reasoning prompts for agents.

    Key Features:
    - Precondition checking before planning
    - Effect verification after planning
    - Structured reasoning chain format
    - Logical soundness validation

    Design:
    - Preconditions: What must be true for valid planning
    - Reasoning: Step-by-step logical chain
    - Effects: What should change as a result
    - Verification: Check all preconditions and effects
    """

    def __init__(self, goal: str, domain: str = "general"):
        """Initialize logical planning prompt.

        Args:
            goal: The planning goal
            domain: Domain type (e.g., "ecommerce", "healthcare", "technology")
        """
        self.goal = goal
        self.domain = domain
        self.preconditions: List[Precondition] = []
        self.expected_effects: List[Effect] = []
        self.reasoning_level = ReasoningLevel.STANDARD

    def add_precondition(self,
                        name: str,
                        description: str,
                        how_to_verify: str) -> 'LogicalPlanningPrompt':
        """Add a precondition that must be met.

        Args:
            name: Internal name (e.g., "market_research_complete")
            description: Human-readable description
            how_to_verify: How to verify this condition is met

        Returns:
            Self for method chaining
        """
        self.preconditions.append(
            Precondition(name=name, description=description, how_to_verify=how_to_verify)
        )
        return self

    def add_expected_effect(self,
                           name: str,
                           description: str,
                           how_to_verify: str) -> 'LogicalPlanningPrompt':
        """Add an expected effect of the planning.

        Args:
            name: Internal name (e.g., "strategic_roadmap_created")
            description: What this effect means
            how_to_verify: How to check if it occurred

        Returns:
            Self for method chaining
        """
        self.expected_effects.append(
            Effect(name=name, description=description, how_to_verify=how_to_verify)
        )
        return self

    def generate_precondition_checks(self, context: Dict[str, Any]) -> str:
        """Generate text for checking preconditions against context.

        Args:
            context: Planning context with available information

        Returns:
            Formatted text listing preconditions to check
        """
        if not self.preconditions:
            return ""

        output = ["## Precondition Verification\n"]
        output.append("For this goal to be achieved, the following preconditions must be met:\n")

        for i, precond in enumerate(self.preconditions, 1):
            output.append(f"{i}. **{precond.description}**")
            output.append(f"   - How to verify: {precond.how_to_verify}")
            output.append("")

        return "\n".join(output)

    def generate_effect_verification(self) -> str:
        """Generate text asking for effect verification.

        Returns:
            Formatted text about expected effects to verify
        """
        if not self.expected_effects:
            return ""

        output = ["## Expected Effects\n"]
        output.append("This plan should result in the following effects:\n")

        for i, effect in enumerate(self.expected_effects, 1):
            output.append(f"{i}. **{effect.description}**")
            output.append(f"   - Verification method: {effect.how_to_verify}")
            output.append("")

        return "\n".join(output)

    def generate_reasoning_chain_prompt(self) -> str:
        """Generate prompt requesting structured reasoning chain.

        Returns:
            Formatted prompt for reasoning generation
        """
        output = [
            "## Reasoning Chain\n",
            "Please provide a step-by-step reasoning chain for achieving this goal.\n",
            "Format each step as:\n",
            "1. **ACTION**: [what to do]",
            "2. **WHY**: [reasoning for this action]",
            "3. **EXPECTED OUTCOME**: [what should result]\n",
            "Make sure each step logically follows from previous steps.\n"
        ]
        return "\n".join(output)

    def generate_full_prompt(self,
                            context: Dict[str, Any],
                            reasoning_level: Optional[ReasoningLevel] = None) -> str:
        """Generate complete PDDL-style prompt for agents.

        Args:
            context: Planning context
            reasoning_level: How detailed the reasoning should be

        Returns:
            Complete prompt for LLM
        """
        level = reasoning_level or self.reasoning_level

        sections = [
            f"## Goal\n{self.goal}\n",
            self.generate_precondition_checks(context),
        ]

        if level in [ReasoningLevel.STANDARD, ReasoningLevel.DETAILED]:
            sections.append(self.generate_reasoning_chain_prompt())

        sections.append(self.generate_effect_verification())

        if level == ReasoningLevel.DETAILED:
            sections.append(self._generate_verification_section())

        return "\n".join(s for s in sections if s)

    def _generate_verification_section(self) -> str:
        """Generate section asking for verification after planning.

        Returns:
            Verification prompt
        """
        output = [
            "## Verification Checklist\n",
            "After proposing your plan, verify:\n",
            "- [ ] All preconditions are satisfied",
            "- [ ] Each step logically follows from previous steps",
            "- [ ] All expected effects would be achieved",
            "- [ ] No contradictory assumptions",
            "- [ ] Plan is feasible with given constraints\n"
        ]
        return "\n".join(output)

    def verify_preconditions(self, context: Dict[str, Any]) -> Dict[str, bool]:
        """Verify preconditions against context.

        Args:
            context: Planning context

        Returns:
            Dictionary mapping precondition names to verification results
        """
        results = {}

        for precond in self.preconditions:
            # Simple keyword matching - can be enhanced
            relevant_keys = [k.lower() for k in context.keys() if k]
            precond_keywords = set(precond.name.lower().split('_'))

            met = any(kw in key for key in relevant_keys for kw in precond_keywords)
            results[precond.name] = met

        return results

    def score_reasoning_quality(self, reasoning_chain: List[ReasoningChainStep]) -> float:
        """Score the quality of a reasoning chain (0-1).

        Args:
            reasoning_chain: List of reasoning steps

        Returns:
            Quality score
        """
        if not reasoning_chain:
            return 0.0

        score = 0.5  # Base score

        # Check for proper sequencing
        if all(step.depends_on for step in reasoning_chain[1:]):
            score += 0.2

        # Check for clear reasoning
        avg_reasoning_length = sum(len(s.reasoning) for s in reasoning_chain) / len(reasoning_chain)
        if avg_reasoning_length > 50:  # Substantial reasoning
            score += 0.15

        # Check for realistic outcomes
        if all(step.expected_outcome for step in reasoning_chain):
            score += 0.15

        return min(1.0, score)

    def extract_reasoning_chain(self,
                               response_text: str) -> List[ReasoningChainStep]:
        """Extract reasoning chain from LLM response.

        Simple parsing - extracts numbered steps.

        Args:
            response_text: Response from LLM

        Returns:
            List of reasoning chain steps
        """
        steps = []
        lines = response_text.split('\n')

        current_step = None
        step_number = 0

        for line in lines:
            line = line.strip()

            # Look for step markers
            if line.startswith(('1.', '2.', '3.', '4.', '5.')) or \
               line.startswith(('**1.', '**2.', '**3.', '**4.', '**5.')):
                step_number += 1
                current_step = ReasoningChainStep(
                    number=step_number,
                    action="",
                    reasoning="",
                    expected_outcome="",
                    depends_on=[step_number - 1] if step_number > 1 else []
                )
                steps.append(current_step)

            # Extract action, reasoning, outcome
            if current_step:
                if 'ACTION' in line.upper() or 'STEP' in line.upper():
                    current_step.action = line
                elif 'WHY' in line.upper() or 'REASON' in line.upper():
                    current_step.reasoning = line
                elif 'OUTCOME' in line.upper() or 'RESULT' in line.upper():
                    current_step.expected_outcome = line

        return steps


# Domain-specific templates
class EcommercePlanningPrompt(LogicalPlanningPrompt):
    """PDDL prompt specialized for ecommerce planning."""

    def __init__(self, goal: str):
        super().__init__(goal, domain="ecommerce")

        # Add ecommerce-specific preconditions
        self.add_precondition(
            "market_research_complete",
            "Market research has been conducted",
            "Check if market size, trends, and competitive analysis are available"
        ).add_precondition(
            "target_audience_defined",
            "Target audience has been clearly defined",
            "Check if demographic, psychographic, and behavioral profiles exist"
        ).add_precondition(
            "budget_constraints_clear",
            "Budget and resource constraints are defined",
            "Check if marketing budget and timeline are specified"
        )

        # Add ecommerce-specific expected effects
        self.add_expected_effect(
            "marketing_strategy_created",
            "A comprehensive marketing strategy has been created",
            "Check for documented strategy with specific tactics and channels"
        ).add_expected_effect(
            "kpis_established",
            "Key performance indicators have been established",
            "Check for measurable metrics and success criteria"
        ).add_expected_effect(
            "implementation_timeline_defined",
            "Implementation timeline with phases has been defined",
            "Check for phased rollout plan with milestones"
        )


class HealthcarePlanningPrompt(LogicalPlanningPrompt):
    """PDDL prompt specialized for healthcare planning."""

    def __init__(self, goal: str):
        super().__init__(goal, domain="healthcare")

        # Add healthcare-specific preconditions
        self.add_precondition(
            "clinical_evidence_reviewed",
            "Clinical evidence and guidelines have been reviewed",
            "Check for citations of medical literature and standards"
        ).add_precondition(
            "patient_needs_assessed",
            "Patient needs and constraints have been assessed",
            "Check for documented patient population analysis"
        ).add_precondition(
            "regulatory_framework_understood",
            "Regulatory and compliance framework is understood",
            "Check for HIPAA, FDA, or other relevant compliance consideration"
        )

        # Add healthcare-specific expected effects
        self.add_expected_effect(
            "clinical_pathway_defined",
            "Clinical pathway or protocol has been defined",
            "Check for documented procedures and decision trees"
        ).add_expected_effect(
            "patient_outcomes_measurable",
            "Patient outcomes are measurable and tracked",
            "Check for defined outcome metrics and monitoring plan"
        ).add_expected_effect(
            "compliance_assured",
            "Compliance with regulations has been assured",
            "Check for documented compliance measures"
        )
