"""
Proposal Agent - Pre-Planning Analysis Specialist

Responsibilities:
- Analyze user goals and planning prerequisites
- Accept user-selected entities and plans at face value (no re-evaluation)
- Detect domain and select appropriate planning template
- Identify frameworks that will be used
- Calculate context coverage based on user selections
- Identify remaining research gaps
- Generate meaningful proposal for user approval

This agent runs BEFORE the multi-iteration planning loop, making the approval
stage meaningful by showing actual analysis rather than placeholders.

CRITICAL PRINCIPLES:
1. User selections are final. We analyze what the user chose, not re-judge choices.
2. MemAgent NEVER autonomously searches the entire memory.
3. Every MemAgent query includes explicit constraint: "ANALYZE ONLY WITHIN: [user-selected items]"
4. No autonomous memory scouring. This maintains true human-in-the-loop operation.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from .base_agent import BaseAgent, AgentResult
from orchestrator.goal_analyzer import GoalAnalyzer
from orchestrator.templates import TemplateSelector
from orchestrator.context import ContextBuilder


class ProposalAgent(BaseAgent):
    """🎯 Proposal Agent - Pre-Planning Analysis Specialist

    Responsibilities:
    - Analyze planning prerequisites based on user selections
    - Detect domain and select appropriate template
    - Identify frameworks that will apply
    - Calculate coverage based on user-selected entities and plans
    - Identify research gaps without re-judging user selections
    - Generate a meaningful proposal with actual analysis

    CRITICAL DESIGN PRINCIPLES:
    1. User selections are final - no re-evaluation of choices
    2. MemAgent operates ONLY within user-selected boundaries
    3. Every MemAgent query includes explicit constraint
    4. No autonomous memory scouring - true human-in-the-loop

    This agent respects user selections as final and analyzes what they chose
    without re-judging. MemAgent stays within user-defined boundaries.
    """

    def __init__(self, agent: Agent, memory_path: Path):
        """Initialize proposal agent

        Args:
            agent: The Fireworks API agent instance
            memory_path: Path to memory directory
        """
        super().__init__(agent, memory_path)
        self.goal_analyzer = GoalAnalyzer()
        self.domain_templates = TemplateSelector()

    def analyze_and_propose(self, goal: str, selected_entities: Optional[List[str]] = None,
                           selected_plans: Optional[List[str]] = None) -> AgentResult:
        """Analyze planning prerequisites and generate proposal

        Args:
            goal: The user's planning goal
            selected_entities: List of entity names user selected from memory (user-approved, no re-eval)
            selected_plans: List of past plan names user selected for learning (user-approved, no re-eval)

        Returns:
            AgentResult with proposal text and metadata
        """

        print(f"\n🎯 PROPOSAL AGENT: Analyzing planning prerequisites...")

        try:
            # Step 1: Analyze goal to detect domain and requirements
            print(f"   1️⃣ Analyzing goal for domain detection...")
            goal_analysis = self.goal_analyzer.analyze_goal(goal)
            detected_domain = goal_analysis.domain
            print(f"      ✓ Domain detected: {detected_domain}")

            # Step 2: Select appropriate template
            print(f"   2️⃣ Selecting domain-specific template...")
            template = self.domain_templates.get_template(detected_domain)
            template_name = template.__class__.__name__
            print(f"      ✓ Template selected: {template_name}")

            # Step 3: Extract frameworks from template
            print(f"   3️⃣ Extracting frameworks from template...")
            frameworks = self._extract_frameworks_from_template(template, goal_analysis)
            print(f"      ✓ Frameworks identified: {len(frameworks)} frameworks")

            # Step 4: Analyze coverage based on USER-SELECTED entities and plans
            # CRITICAL: We accept these as-is without re-evaluation
            print(f"   4️⃣ Analyzing context coverage...")
            coverage = self._calculate_coverage_from_selections(
                goal=goal,
                selected_entities=selected_entities or [],
                selected_plans=selected_plans or [],
                frameworks=frameworks,
                goal_analysis=goal_analysis
            )
            print(f"      ✓ Coverage calculated")
            print(f"         - Memory coverage: {coverage['memory_coverage']:.0%}")
            print(f"         - Research coverage: {coverage['research_coverage']:.0%}")
            print(f"         - Research gaps: {len(coverage['research_gaps'])} identified")

            # Step 4.5: NEW - Analyze selected entities with constrained MemAgent calls
            # One MemAgent call per entity for relevance validation
            print(f"   4️⃣ Analyzing selected entities...")
            entity_analyses = []
            for entity_name in (selected_entities or []):
                entity_content = self._read_entity_file(entity_name)
                if entity_content:
                    analysis = self._analyze_entity_relevance(goal, entity_name, entity_content)
                    entity_analyses.append(analysis)
                    print(f"      ✓ {entity_name}: Relevance {analysis['relevance_score']:.0%}")

            entity_aggregation = self._aggregate_entity_analysis(entity_analyses)
            print(f"      ✓ Entity analysis complete: {entity_aggregation['assessment']}")

            # Step 4.6: NEW - Analyze selected plans with constrained MemAgent calls
            # One MemAgent call per plan for framework identification
            print(f"   4️⃣ Analyzing selected plans...")
            plan_analyses = []
            for plan_name in (selected_plans or []):
                plan_content = self._read_plan_file(plan_name)
                if plan_content:
                    analysis = self._analyze_plan_frameworks(goal, plan_name, plan_content)
                    plan_analyses.append(analysis)
                    print(f"      ✓ {plan_name}: Readiness {analysis['readiness_score']:.0%}")

            plan_aggregation = self._aggregate_plan_analysis(plan_analyses)
            print(f"      ✓ Plan analysis complete: {plan_aggregation['assessment']}")

            # Step 5: Generate proposal text using agent
            print(f"   5️⃣ Generating proposal text...")
            proposal_text = self._generate_proposal_text(
                goal=goal,
                goal_analysis=goal_analysis,
                domain=detected_domain,
                frameworks=frameworks,
                selected_entities=selected_entities or [],
                selected_plans=selected_plans or [],
                coverage=coverage,
                entity_aggregation=entity_aggregation,
                plan_aggregation=plan_aggregation
            )
            print(f"      ✓ Proposal generated ({len(proposal_text)} characters)")

            # Step 6: Calculate confidence level
            print(f"   6️⃣ Calculating approach confidence...")
            confidence_level = self._calculate_confidence_level(
                selected_entities_count=len(selected_entities or []),
                selected_plans_count=len(selected_plans or []),
                frameworks=frameworks,
                coverage=coverage
            )
            print(f"      ✓ Confidence level: {confidence_level:.0%}")

            # Prepare metadata
            metadata = {
                "domain": detected_domain,
                "template": template_name,
                "frameworks_to_use": frameworks,
                "frameworks_count": len(frameworks),

                # NEW: Entity validation results (from constrained MemAgent analysis)
                "entity_relevance": {
                    "entities_analyzed": entity_aggregation['entities_analyzed'],
                    "entities_relevant": entity_aggregation['entities_relevant'],
                    "coverage_percent": entity_aggregation['coverage_percent'],
                    "assessment": entity_aggregation['assessment'],
                    "details": entity_aggregation['details']
                },

                # NEW: Plan framework results (from constrained MemAgent analysis)
                "plan_framework_readiness": {
                    "plans_analyzed": plan_aggregation['plans_analyzed'],
                    "frameworks_found": plan_aggregation['frameworks_found'],
                    "frameworks_count": plan_aggregation['frameworks_count'],
                    "readiness_percent": round(plan_aggregation['readiness_score'] * 100, 1),
                    "assessment": plan_aggregation['assessment'],
                    "details": plan_aggregation['details']
                },

                # NEW: MemAgent validation evidence
                "memagent_validation": {
                    "entities_constrained_calls": len(entity_analyses),
                    "plans_constrained_calls": len(plan_analyses),
                    "constraint_pattern": "ANALYZED ONLY WITHIN user-selected items",
                    "validation_timestamp": datetime.now().isoformat()
                },

                # EXISTING: Keep all existing metadata for consistency
                "memory_coverage_percent": round(coverage['memory_coverage'] * 100, 1),
                "research_coverage_percent": round(coverage['research_coverage'] * 100, 1),
                "selected_entities": selected_entities or [],
                "selected_entities_count": len(selected_entities or []),
                "selected_plans": selected_plans or [],
                "selected_plans_count": len(selected_plans or []),
                "research_gaps": coverage['research_gaps'],
                "research_gaps_count": len(coverage['research_gaps']),
                "confidence_level": round(confidence_level, 2),
                "estimated_iterations": self._estimate_iterations(coverage),
                "analysis_timestamp": datetime.now().isoformat()
            }

            # Log agent action
            self._log_agent_action("analyze_and_propose", AgentResult(
                success=True,
                output=proposal_text,
                metadata=metadata,
                timestamp=datetime.now().isoformat()
            ))

            return self._wrap_result(
                success=True,
                output=proposal_text,
                metadata=metadata
            )

        except Exception as e:
            return self._handle_error("analyze_and_propose", e)

    def _calculate_coverage_from_selections(self, goal: str, selected_entities: List[str],
                                           selected_plans: List[str],
                                           frameworks: List[str],
                                           goal_analysis: Any) -> Dict[str, Any]:
        """Calculate context coverage based on USER-SELECTED entities and plans

        CRITICAL: This accepts user selections as-is without re-evaluation.
        We measure what the user chose, not question whether it was the right choice.

        Args:
            goal: The planning goal
            selected_entities: Entities user selected (accepted as-is)
            selected_plans: Past plans user selected (accepted as-is)
            frameworks: Frameworks identified for this domain
            goal_analysis: Analyzed goal information

        Returns:
            Dict with coverage percentages and identified research gaps
        """

        # Calculate coverage based on:
        # 1. Number of entities selected (represents historical context)
        # 2. Number of past plans selected (represents learned patterns)
        # 3. Number of frameworks available (represents domain knowledge)

        # Base: each selected entity provides ~15% memory coverage (assuming domain-appropriate)
        entity_coverage = min(len(selected_entities) * 0.15, 0.60)

        # Bonus: each past plan selected adds learning context (~10% per plan)
        plan_coverage = min(len(selected_plans) * 0.10, 0.20)

        # Total memory coverage
        memory_coverage = min(entity_coverage + plan_coverage, 0.75)
        research_coverage = 1.0 - memory_coverage

        # Identify research gaps based on domain
        research_gaps = self._identify_research_gaps(
            goal=goal,
            domain=goal_analysis.domain,
            selected_entities_count=len(selected_entities),
            selected_plans_count=len(selected_plans)
        )

        return {
            'memory_coverage': memory_coverage,
            'research_coverage': research_coverage,
            'research_gaps': research_gaps,
            'entity_contribution': entity_coverage,
            'plan_contribution': plan_coverage
        }

    def _identify_research_gaps(self, goal: str, domain: str,
                               selected_entities_count: int,
                               selected_plans_count: int) -> List[str]:
        """Identify likely research gaps based on domain and selections

        Args:
            goal: The planning goal
            domain: Detected domain
            selected_entities_count: How many entities user selected
            selected_plans_count: How many past plans user selected

        Returns:
            List of research gap descriptions
        """

        gaps = []

        # Domain-specific gap identification
        domain_gaps = {
            'healthcare': [
                'Regulatory landscape and compliance requirements',
                'Current clinical evidence and research findings',
                'Market pricing and reimbursement trends',
                'Competitive landscape and benchmarks'
            ],
            'technology': [
                'Current market trends and technology adoption rates',
                'Competitive landscape and feature parity',
                'Customer sentiment and market fit signals',
                'Emerging technologies and future roadmap'
            ],
            'financial': [
                'Current market conditions and economic indicators',
                'Competitive positioning and peer benchmarks',
                'Regulatory environment and compliance landscape',
                'Risk assessment and scenario modeling'
            ],
            'manufacturing': [
                'Supply chain complexity and cost structures',
                'Production capacity and efficiency benchmarks',
                'Market demand and growth projections',
                'Competitive manufacturing capabilities'
            ],
            'retail': [
                'Consumer behavior and purchasing trends',
                'Competitive retail landscape and positioning',
                'Channel strategy and omnichannel dynamics',
                'Inventory and logistics optimization'
            ],
            'qsr': [
                'Consumer preferences and market trends',
                'Competitive landscape and menu strategies',
                'Operational metrics and benchmarks',
                'Supply chain and unit economics'
            ]
        }

        potential_gaps = domain_gaps.get(domain, domain_gaps['healthcare'])

        # Reduce gaps if user provided good context
        if selected_entities_count > 0 or selected_plans_count > 0:
            # User selected context, so assume they've covered some gaps
            # Start with all gaps, but we'll research them anyway
            gaps = potential_gaps
        else:
            # No user context selected, more research needed
            gaps = potential_gaps

        return gaps

    def _extract_frameworks_from_template(self, template: Any, goal_analysis: Any) -> List[str]:
        """Extract framework names from the selected template

        Args:
            template: The domain template instance
            goal_analysis: The goal analysis object

        Returns:
            List of framework names
        """

        frameworks = []

        try:
            # Check if template has a get_frameworks method
            if hasattr(template, 'get_frameworks'):
                frameworks = template.get_frameworks(goal_analysis)
            # Otherwise, extract from template attributes
            elif hasattr(template, 'primary_frameworks'):
                frameworks = template.primary_frameworks
            else:
                # Fallback: generic frameworks based on domain
                domain = goal_analysis.domain
                default_frameworks = {
                    'healthcare': ['Clinical Impact Assessment', 'Regulatory Compliance Framework', 'Market Access Strategy'],
                    'technology': ['Product-Market Fit Analysis', 'Technical Architecture Framework', 'Growth Strategy'],
                    'financial': ['Financial Risk Assessment', 'Portfolio Analysis Framework', 'Investment Strategy'],
                    'manufacturing': ['Supply Chain Optimization', 'Production Efficiency Framework', 'Quality Management'],
                    'retail': ['Omnichannel Strategy', 'Consumer Segmentation Framework', 'Pricing Strategy'],
                    'qsr': ['Operational Excellence Framework', 'Menu Engineering', 'Customer Experience Strategy']
                }
                frameworks = default_frameworks.get(domain, ['Strategic Analysis', 'Market Assessment', 'Implementation Planning'])

        except Exception as e:
            print(f"      ⚠️ Framework extraction failed: {e}")
            frameworks = ['Strategic Planning', 'Market Analysis', 'Implementation Strategy']

        return frameworks

    def _calculate_confidence_level(self, selected_entities_count: int,
                                   selected_plans_count: int,
                                   frameworks: List[str],
                                   coverage: Dict[str, float]) -> float:
        """Calculate confidence level in the proposed approach

        Args:
            selected_entities_count: Number of entities user selected
            selected_plans_count: Number of past plans user selected
            frameworks: List of frameworks to use
            coverage: Coverage percentages

        Returns:
            Confidence score (0.0 - 1.0)
        """

        confidence = 0.65  # Base confidence (user made selections, so we're starting strong)

        # Boost confidence based on entities selected
        if selected_entities_count >= 3:
            confidence += 0.15
        elif selected_entities_count >= 1:
            confidence += 0.10

        # Boost confidence based on past plans selected
        if selected_plans_count >= 2:
            confidence += 0.10
        elif selected_plans_count >= 1:
            confidence += 0.05

        # Boost confidence based on frameworks
        if len(frameworks) >= 3:
            confidence += 0.10

        # Cap at 0.95 (even with everything, leave room for uncertainty)
        return min(confidence, 0.95)

    def _read_entity_file(self, entity_name: str) -> Optional[str]:
        """Read entity file from local-memory/entities/entities/

        Safely reads and returns entity content, with truncation for MemAgent context window.

        Args:
            entity_name: Name of entity file (without .md extension)

        Returns:
            File content (truncated to 3000 chars) or None if not found
        """
        try:
            # Handle both with and without .md extension
            if entity_name.endswith('.md'):
                entity_path = self.memory_path / "entities" / entity_name
            else:
                entity_path = self.memory_path / "entities" / f"{entity_name}.md"
            if entity_path.exists():
                content = entity_path.read_text(encoding='utf-8')
                # Truncate for MemAgent context window
                if len(content) > 3000:
                    content = content[:3000] + "\n[... content truncated for analysis ...]"
                return content
            else:
                print(f"         ⚠️ Entity file not found: {entity_path}")
                return None
        except Exception as e:
            print(f"         ⚠️ Error reading entity {entity_name}: {e}")
            return None

    def _read_plan_file(self, plan_name: str) -> Optional[str]:
        """Read plan file from local-memory/plans/

        Safely reads and returns plan content, with truncation for MemAgent context window.

        Args:
            plan_name: Name of plan file (without .md extension)

        Returns:
            File content (truncated to 3000 chars) or None if not found
        """
        try:
            # Handle both with and without .md extension
            if plan_name.endswith('.md'):
                plan_path = self.memory_path / "plans" / plan_name
            else:
                plan_path = self.memory_path / "plans" / f"{plan_name}.md"
            if plan_path.exists():
                content = plan_path.read_text(encoding='utf-8')
                # Truncate for MemAgent context window
                if len(content) > 3000:
                    content = content[:3000] + "\n[... content truncated for analysis ...]"
                return content
            else:
                print(f"         ⚠️ Plan file not found: {plan_path}")
                return None
        except Exception as e:
            print(f"         ⚠️ Error reading plan {plan_name}: {e}")
            return None

    def _analyze_entity_relevance(self, goal: str, entity_name: str,
                                 entity_content: str) -> Dict[str, Any]:
        """Analyze ONE entity's relevance to goal using constrained MemAgent call

        USER-CONSTRAINED APPROACH: MemAgent analyzes ONLY this entity file.
        One MemAgent call per entity - validates relevance without autonomous searching.

        Args:
            goal: The planning goal
            entity_name: Name of the entity
            entity_content: Content from the entity file

        Returns:
            Dict with:
            - entity_name: str
            - relevant: bool
            - relevance_score: 0.0-1.0
            - assessment: str describing relevance
            - key_insights: str with key insights for goal
        """
        try:
            # CONSTRAINED MEMAGENT CALL
            query = f"""
OPERATION: ENTITY_RELEVANCE_VALIDATION
GOAL: {goal}

CONSTRAINT: Analyze ONLY WITHIN this user-selected entity file.
This entity was explicitly selected by the user. Analyze it, don't search elsewhere.

Entity: {entity_name}
Content: {entity_content}

For goal: {goal}

Answer these questions:
1. Is this entity relevant to the goal? (Yes/No)
2. Relevance score (0.0 to 1.0, where 1.0 is perfect relevance)
3. Assessment: In 1-2 sentences, what knowledge does this entity provide?
4. Key insights: What 1-2 key insights from this entity will help planning?

Be concise. Respond with: Relevant: [Yes/No], Score: [0.0-1.0], Assessment: [text], Insights: [text]
"""

            response = self.agent.chat(query)
            response_text = response.reply or ""

            # Parse response
            relevant = "yes" in response_text.lower()
            relevance_score = 0.5  # Default

            # Try to extract score from response
            if "score:" in response_text.lower():
                parts = response_text.lower().split("score:")
                if len(parts) > 1:
                    score_str = parts[1].split(",")[0].strip()
                    try:
                        relevance_score = float(score_str)
                        relevance_score = max(0.0, min(relevance_score, 1.0))  # Clamp 0-1
                    except ValueError:
                        pass

            # Extract assessment and insights
            assessment = "Relevance validated"
            key_insights = ""
            if "assessment:" in response_text.lower():
                parts = response_text.lower().split("assessment:")
                if len(parts) > 1:
                    assessment = parts[1].split("insights:")[0].strip()

            if "insights:" in response_text.lower():
                parts = response_text.lower().split("insights:")
                if len(parts) > 1:
                    key_insights = parts[1].strip()

            return {
                "entity_name": entity_name,
                "relevant": relevant,
                "relevance_score": relevance_score,
                "assessment": assessment,
                "key_insights": key_insights,
                "constraint": "ANALYZED ONLY WITHIN user-selected entity file"
            }

        except Exception as e:
            print(f"         ⚠️ Entity analysis failed for {entity_name}: {e}")
            return {
                "entity_name": entity_name,
                "relevant": False,
                "relevance_score": 0.0,
                "assessment": f"Analysis failed: {str(e)}",
                "key_insights": "",
                "constraint": "ANALYZED ONLY WITHIN user-selected entity file"
            }

    def _analyze_plan_frameworks(self, goal: str, plan_name: str,
                                plan_content: str) -> Dict[str, Any]:
        """Analyze ONE plan's frameworks/patterns using constrained MemAgent call

        USER-CONSTRAINED APPROACH: MemAgent analyzes ONLY this plan file.
        One MemAgent call per plan - identifies frameworks without autonomous searching.

        Args:
            goal: The planning goal
            plan_name: Name of the plan
            plan_content: Content from the plan file

        Returns:
            Dict with:
            - plan_name: str
            - frameworks_identified: List[str]
            - frameworks_count: int
            - readiness_score: 0.0-1.0
            - assessment: str describing readiness
        """
        try:
            # CONSTRAINED MEMAGENT CALL
            query = f"""
OPERATION: PLAN_FRAMEWORK_ANALYSIS
GOAL: {goal}

CONSTRAINT: Analyze ONLY WITHIN this user-selected plan file.
This plan was explicitly selected by the user. Analyze it, don't search elsewhere.

Plan: {plan_name}
Content: {plan_content}

For goal: {goal}

Answer these questions:
1. What frameworks, methodologies, or approaches does this plan demonstrate? (List them)
2. How applicable are these frameworks to the current goal? (Yes/Partially/No)
3. Readiness score (0.0 to 1.0, where 1.0 is completely ready to inform current planning)
4. Assessment: In 1-2 sentences, how ready is this plan to help current planning?

Be concise. Respond with: Frameworks: [list], Applicability: [Yes/Partially/No], Readiness: [0.0-1.0], Assessment: [text]
"""

            response = self.agent.chat(query)
            response_text = response.reply or ""

            # Parse response
            frameworks_identified = []
            readiness_score = 0.5  # Default

            # Try to extract frameworks
            if "frameworks:" in response_text.lower():
                parts = response_text.lower().split("frameworks:")
                if len(parts) > 1:
                    framework_str = parts[1].split("applicability:")[0].strip()
                    # Split by comma or semicolon
                    frameworks_identified = [f.strip() for f in framework_str.split(",") if f.strip()]

            # Try to extract readiness score
            if "readiness:" in response_text.lower():
                parts = response_text.lower().split("readiness:")
                if len(parts) > 1:
                    score_str = parts[1].split("assessment:")[0].strip()
                    try:
                        readiness_score = float(score_str)
                        readiness_score = max(0.0, min(readiness_score, 1.0))  # Clamp 0-1
                    except ValueError:
                        pass

            # Extract assessment
            assessment = "Plan frameworks identified"
            if "assessment:" in response_text.lower():
                parts = response_text.lower().split("assessment:")
                if len(parts) > 1:
                    assessment = parts[1].strip()

            return {
                "plan_name": plan_name,
                "frameworks_identified": frameworks_identified,
                "frameworks_count": len(frameworks_identified),
                "readiness_score": readiness_score,
                "assessment": assessment,
                "constraint": "ANALYZED ONLY WITHIN user-selected plan file"
            }

        except Exception as e:
            print(f"         ⚠️ Plan analysis failed for {plan_name}: {e}")
            return {
                "plan_name": plan_name,
                "frameworks_identified": [],
                "frameworks_count": 0,
                "readiness_score": 0.0,
                "assessment": f"Analysis failed: {str(e)}",
                "constraint": "ANALYZED ONLY WITHIN user-selected plan file"
            }

    def _aggregate_entity_analysis(self, entity_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from analyzing N entities

        Summarizes per-entity analysis results into overall coverage assessment.

        Args:
            entity_analyses: List of results from _analyze_entity_relevance()

        Returns:
            Dict with aggregated results:
            - entities_analyzed: int
            - entities_relevant: int
            - coverage_percent: float
            - assessment: str
            - details: list of per-entity results
        """
        if not entity_analyses:
            return {
                "entities_analyzed": 0,
                "entities_relevant": 0,
                "coverage_percent": 0.0,
                "assessment": "No entities selected for analysis",
                "details": []
            }

        # Count relevant entities
        relevant_count = sum(1 for e in entity_analyses if e.get("relevant", False))

        # Calculate average relevance score
        avg_relevance = sum(e.get("relevance_score", 0.0) for e in entity_analyses) / len(entity_analyses)
        coverage_percent = avg_relevance * 100

        # Generate assessment based on coverage
        if coverage_percent >= 80:
            assessment = f"Excellent entity coverage - {relevant_count} of {len(entity_analyses)} entities highly relevant"
        elif coverage_percent >= 60:
            assessment = f"Good entity coverage - {relevant_count} of {len(entity_analyses)} entities relevant and well-aligned"
        elif coverage_percent >= 40:
            assessment = f"Moderate entity coverage - {relevant_count} of {len(entity_analyses)} entities provide useful context"
        elif coverage_percent > 0:
            assessment = f"Limited entity coverage - {relevant_count} of {len(entity_analyses)} entities marginally relevant"
        else:
            assessment = "No relevant entities - consider selecting different entities"

        return {
            "entities_analyzed": len(entity_analyses),
            "entities_relevant": relevant_count,
            "coverage_percent": coverage_percent,
            "assessment": assessment,
            "details": entity_analyses
        }

    def _aggregate_plan_analysis(self, plan_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from analyzing N plans

        Summarizes per-plan analysis results into overall framework readiness assessment.

        Args:
            plan_analyses: List of results from _analyze_plan_frameworks()

        Returns:
            Dict with aggregated results:
            - plans_analyzed: int
            - frameworks_found: list of all unique frameworks
            - frameworks_count: int total frameworks across all plans
            - readiness_score: float average readiness
            - assessment: str
            - details: list of per-plan results
        """
        if not plan_analyses:
            return {
                "plans_analyzed": 0,
                "frameworks_found": [],
                "frameworks_count": 0,
                "readiness_score": 0.0,
                "assessment": "No plans selected for analysis",
                "details": []
            }

        # Collect all unique frameworks
        all_frameworks = []
        for plan_result in plan_analyses:
            frameworks = plan_result.get("frameworks_identified", [])
            for fw in frameworks:
                if fw not in all_frameworks:
                    all_frameworks.append(fw)

        # Calculate average readiness
        avg_readiness = sum(p.get("readiness_score", 0.0) for p in plan_analyses) / len(plan_analyses)
        readiness_percent = avg_readiness * 100

        # Generate assessment based on readiness
        if readiness_percent >= 80:
            assessment = f"Excellent plan readiness - {len(all_frameworks)} frameworks identified, plans highly aligned"
        elif readiness_percent >= 60:
            assessment = f"Good plan readiness - {len(all_frameworks)} frameworks identified, solid foundation for planning"
        elif readiness_percent >= 40:
            assessment = f"Moderate plan readiness - {len(all_frameworks)} frameworks identified, some adaptation needed"
        elif readiness_percent > 0:
            assessment = f"Limited plan readiness - {len(all_frameworks)} frameworks identified, significant adaptation needed"
        else:
            assessment = "Plans not ready - consider selecting plans more closely aligned with current goal"

        return {
            "plans_analyzed": len(plan_analyses),
            "frameworks_found": all_frameworks,
            "frameworks_count": len(all_frameworks),
            "readiness_score": avg_readiness,
            "assessment": assessment,
            "details": plan_analyses
        }

    def _estimate_iterations(self, coverage: Dict[str, float]) -> int:
        """Estimate number of iterations needed based on research coverage

        Args:
            coverage: Coverage percentages

        Returns:
            Estimated number of iterations
        """

        research_coverage = coverage.get('research_coverage', 0.5)

        # More research needed = more iterations
        if research_coverage >= 0.8:
            return 5  # Heavy research needed
        elif research_coverage >= 0.6:
            return 4  # Moderate research
        elif research_coverage >= 0.4:
            return 3  # Some research
        else:
            return 2  # Minimal research needed

    def _generate_proposal_text(self, goal: str, goal_analysis: Any,
                               domain: str, frameworks: List[str],
                               selected_entities: List[str],
                               selected_plans: List[str],
                               coverage: Dict[str, Any],
                               entity_aggregation: Optional[Dict[str, Any]] = None,
                               plan_aggregation: Optional[Dict[str, Any]] = None) -> str:
        """Generate the proposal text for user review

        Args:
            goal: The planning goal
            goal_analysis: Analyzed goal information
            domain: Detected domain
            frameworks: Frameworks to use
            selected_entities: Entity names user selected
            selected_plans: Plan names user selected
            coverage: Coverage percentages and gaps
            entity_aggregation: NEW - Results from entity relevance analysis
            plan_aggregation: NEW - Results from plan framework analysis

        Returns:
            Formatted proposal text (800-1000 words)
        """

        memory_pct = round(coverage['memory_coverage'] * 100, 0)
        research_pct = round(coverage['research_coverage'] * 100, 0)
        gaps = coverage.get('research_gaps', [])

        proposal = f"""# 🎯 Planning Proposal: {goal}

## Executive Summary

We're ready to develop a comprehensive plan for: **{goal}**

After analyzing your goal and your selected resources, we've identified a **{domain.upper()}** domain approach using {len(frameworks)} specialized frameworks.

---

## 📊 Planning Approach & Context Coverage

**Detected Domain:** {domain.capitalize()}

**Your Selected Resources:**
- **Memory Entities:** {', '.join(selected_entities) if selected_entities else '(None selected)'}
- **Past Plans for Learning:** {', '.join(selected_plans) if selected_plans else '(None selected)'}

**Context Coverage Breakdown:**
- **From Your Selections:** {memory_pct}%
  - Historical context and institutional knowledge from your selected entities
  - Learned patterns from {len(selected_plans)} past planning sessions
- **Research Coverage Needed:** {research_pct}%
  - Market validation and current data
  - Competitive landscape and industry trends
  - Emerging factors and forward-looking analysis

---

## 🏗️ Domain-Specific Frameworks

This planning session will apply {len(frameworks)} **{domain.capitalize()}** frameworks:

"""

        for i, framework in enumerate(frameworks, 1):
            proposal += f"{i}. **{framework}**\n"

        proposal += f"""

---

## 🔍 Research Focus Areas

To complement your {memory_pct}% memory coverage, we'll research:

"""

        for i, gap in enumerate(gaps[:4], 1):  # Show top 4 gaps
            proposal += f"- {gap}\n"

        proposal += f"""

---

## 📈 Planning Workflow

### Phase 1: Foundation Analysis
- Review your {len(selected_entities)} selected entities
- Extract patterns from {len(selected_plans) if selected_plans else 'historical'} past planning sessions
- Establish baseline and success criteria

### Phase 2: Strategic Development
- Apply {len(frameworks)} domain frameworks to your goal
- Integrate your institutional knowledge with market research
- Validate assumptions and identify dependencies

### Phase 3: Implementation Roadmap
- Break down strategy into actionable steps
- Define owners, timelines, and success metrics
- Create prioritized execution plan

### Phase 4: Synthesis & Review
- Consolidate into comprehensive strategic plan
- Verify logical consistency and completeness
- Present for your approval

---

## 📋 Your Selected Context - Validation Results

Based on detailed analysis of your selections using our constrained MemAgent system:

"""

        # Entity Analysis Results
        if entity_aggregation and entity_aggregation['entities_analyzed'] > 0:
            proposal += f"""### Entity Relevance Analysis
**Analyzed {entity_aggregation['entities_analyzed']} entities:** {entity_aggregation['assessment']}

- Relevant entities: {entity_aggregation['entities_relevant']}/{entity_aggregation['entities_analyzed']}
- Coverage strength: {entity_aggregation['coverage_percent']:.0f}%

"""
        else:
            proposal += "### Entity Relevance Analysis\nNo entities selected for analysis.\n\n"

        # Plan Analysis Results
        if plan_aggregation and plan_aggregation['plans_analyzed'] > 0:
            proposal += f"""### Plan Framework Analysis
**Analyzed {plan_aggregation['plans_analyzed']} past plans:** {plan_aggregation['assessment']}

- Frameworks identified: {plan_aggregation['frameworks_count']}
- Readiness for current goal: {plan_aggregation['readiness_score']:.0%}

"""
            if plan_aggregation['frameworks_found']:
                proposal += "Identified frameworks from your plans:\n"
                for fw in plan_aggregation['frameworks_found'][:5]:
                    proposal += f"- {fw}\n"
                proposal += "\n"
        else:
            proposal += "### Plan Framework Analysis\nNo plans selected for analysis.\n\n"

        # Validation Confidence Summary
        proposal += """### Validation Confidence
Your selections have been validated by our constrained analysis system. Entities and past plans were analyzed ONLY WITHIN the boundaries you selected - no autonomous memory scouring. This ensures true human-in-the-loop operation.

**Proceeding with validated context + research coverage = comprehensive planning approach**

---

## ✅ Planning Readiness

**Memory Foundation:** {memory_pct}% - {"Excellent" if memory_pct >= 60 else "Good" if memory_pct >= 40 else "Building"} institutional knowledge base

**Research Plan:** {research_pct}% - {"Focused gaps" if research_pct < 40 else "Moderate research" if research_pct < 60 else "Comprehensive validation"}

**Confidence Level:** {self._calculate_confidence_level(len(selected_entities), len(selected_plans), frameworks, coverage):.0%} - Solid approach with strong foundation

**Estimated Duration:** {self._estimate_iterations(coverage)} iteration(s)
- Each iteration: ~30-60 minutes + your approval at checkpoint
- You maintain full control with approval gates at each stage

---

## 🚀 Ready to Begin

Click **"Approve & Execute"** to start the planning process. You'll receive:

✅ Real-time progress updates after each iteration
✅ Detailed checkpoint reviews before proceeding
✅ Your approval required to continue to next iteration
✅ Final comprehensive plan incorporating all approved feedback

**Your selections are set. Ready to proceed?**
"""

        return proposal
