"""
Planner Agent - Strategic Planning Specialist

Responsibilities:
- Analyze project context and requirements
- Generate comprehensive strategic plans
- Leverage learned patterns and avoid known errors
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from .base_agent import BaseAgent, AgentResult
from orchestrator.goal_analyzer import GoalAnalyzer
from orchestrator.templates import TemplateSelector
from orchestrator.reasoning import LogicalPlanningPrompt, ReasoningLevel  # Phase 2: PDDL-INSTRUCT
from orchestrator.pattern_recommender import PatternRecommender  # LEARNING LOOP INTEGRATION


class PlannerAgent(BaseAgent):
    """🧭 Planner Agent - The strategic decision maker

    Responsibilities:
    - Analyze project context from MemAgent
    - Generate high-level strategic plans
    - Decide on tool usage and action sequences
    - Coordinate with other agents through shared memory
    """

    def __init__(self, agent: Agent, memory_path: Path):
        """Initialize planner agent

        Args:
            agent: The MemAgent instance
            memory_path: Path to memory directory
        """
        super().__init__(agent, memory_path)
        self.goal_analyzer = GoalAnalyzer()
        self.domain_templates = TemplateSelector()
        self.pattern_recommender = None  # Will be initialized with trainer when context is available

    def generate_strategic_plan(self, goal: str, context: Dict[str, str],
                                selected_plans: Optional[List[str]] = None) -> AgentResult:
        """Generate a strategic plan using MemAgent context and learned patterns

        Args:
            goal: The planning goal/objective
            context: Context data from context manager
            selected_plans: Optional list of plan filenames user selected for learning

        Returns:
            AgentResult with strategic plan or error details
        """

        print(f"\n🧭 PLANNER AGENT: Generating strategic plan...")

        try:
            # Phase 4.1: Initialize PatternRecommender with Flow-GRPO trainer from context
            flow_grpo_trainer = context.get('flow_grpo_trainer')

            # Initialize pattern_recommender on first use with trainer from context
            if self.pattern_recommender is None:
                self.pattern_recommender = PatternRecommender(self.memory_path, flow_grpo_trainer=flow_grpo_trainer)
                if flow_grpo_trainer:
                    print(f"   ✓ Pattern recommender initialized with Flow-GRPO trainer for effectiveness scoring")
                else:
                    print(f"   ℹ️ Pattern recommender initialized without trainer (will use existing patterns)")
            elif flow_grpo_trainer and not self.pattern_recommender.flow_grpo_trainer:
                # Update trainer if we didn't have it before
                self.pattern_recommender.flow_grpo_trainer = flow_grpo_trainer
                print(f"   ✓ Pattern recommender updated with Flow-GRPO trainer for effectiveness scoring")

            # Analyze the goal to determine domain and context requirements
            goal_analysis = self.goal_analyzer.analyze_goal(goal)
            print(f"   → Goal Analysis: Domain={goal_analysis.domain}, Industry={goal_analysis.industry}")

            # Phase 2.3: Initialize LogicalPlanningPrompt for PDDL-INSTRUCT reasoning
            logical_prompt = LogicalPlanningPrompt(goal=goal, domain=goal_analysis.domain)

            # Add domain-appropriate preconditions
            logical_prompt.add_precondition(
                name="context_analyzed",
                description="Market and business context has been analyzed",
                how_to_verify="Check for market analysis and competitive positioning"
            )
            logical_prompt.add_precondition(
                name="requirements_defined",
                description="Project requirements and success criteria are defined",
                how_to_verify="Check for clear objectives and KPIs"
            )

            # Add domain-appropriate expected effects
            logical_prompt.add_expected_effect(
                name="strategic_plan_created",
                description="Comprehensive strategic plan has been created",
                how_to_verify="Check for documented strategy with timeline and tactics"
            )
            logical_prompt.add_expected_effect(
                name="success_metrics_defined",
                description="Success metrics and KPIs have been defined",
                how_to_verify="Check for measurable outcomes"
            )

            # Retrieve comprehensive context from MemAgent using dynamic selection
            project_context = self._retrieve_project_context(goal)
            successful_patterns = self._retrieve_successful_patterns()
            error_patterns = self._retrieve_error_patterns()
            current_state = self._retrieve_current_state()

            print(f"   → Context retrieved: project={len(project_context)} chars, patterns={len(successful_patterns)} chars")

            # LEARNING LOOP INTEGRATION: Get learned patterns from previous planning
            print(f"   → Checking for learned patterns...")
            pattern_context = self.pattern_recommender.get_pattern_context(goal, selected_plans=selected_plans)
            learned_patterns_info = pattern_context.get('context', '')

            if pattern_context.get('has_learned_patterns'):
                plans_analyzed = pattern_context.get('selected_plans_analyzed', 0)
                print(f"   ✅ Found {pattern_context.get('pattern_count', 0)} relevant learned patterns to apply")
                if plans_analyzed > 0:
                    print(f"   📌 Analyzed {plans_analyzed} user-selected plans for learning")
            else:
                print(f"   ℹ️ No learned patterns yet (system will learn from this iteration)")

            # Prepare context data for template
            web_search_results = context.get('web_search_results', 'No web search results available')
            print(f"   → Web search data: {len(web_search_results)} chars")

            context_data = {
                'goal': goal,
                'project_context': project_context,
                'successful_patterns': successful_patterns,
                'error_patterns': error_patterns,
                'execution_history': current_state,
                'current_status': context.get('current_status', 'No previous context'),
                'web_search_results': web_search_results,
                'learned_patterns': learned_patterns_info  # LEARNING LOOP: Add learned patterns to context
            }

            # ITERATION MODE: Add MemAgent-guided iteration context if in multi-iteration planning
            if context.get('iteration_mode'):
                iteration_num = context.get('iteration_number', 1)
                max_iterations = context.get('max_iterations', 1)

                # Add iteration guidance (from MemAgent retrieval)
                context_data['iteration_guidance'] = context.get('iteration_guidance', '')
                context_data['iteration_number'] = iteration_num
                context_data['max_iterations'] = max_iterations

                # Include previous iteration data for reference (not template, but guidance)
                if iteration_num > 1:
                    context_data['previous_plan'] = context.get('previous_plan', '')
                    context_data['previous_insights'] = context.get('previous_insights', [])
                    context_data['previous_frameworks'] = context.get('previous_frameworks', [])
                    print(f"   → Iteration {iteration_num}: Including previous iteration guidance for MemAgent-based refinement")
                else:
                    print(f"   → Iteration 1: Starting from proposal")

            # Generate domain-specific planning prompt
            print(f"   → Building planning prompt from {goal_analysis.domain} template...")
            try:
                planning_prompt = self.domain_templates.get_planning_prompt(goal_analysis, context_data)
                print(f"   → Planning prompt built: {len(planning_prompt)} chars")
            except Exception as e:
                error_msg = f"Template formatting failed: {str(e)}"
                print(f"   ❌ {error_msg}")
                raise

            # Phase 2.3: Enhance prompt with PDDL-INSTRUCT reasoning chain request
            precondition_checks = logical_prompt.generate_precondition_checks(context_data)
            pddl_prompt_enhancement = f"""
{precondition_checks}

REASONING_CHAIN_REQUEST:
As you develop the strategic plan, please structure your reasoning as follows:

1. **ANALYZE_CONTEXT**: What information from the provided context is most relevant?
2. **IDENTIFY_GAPS**: What are the key gaps or challenges to address?
3. **DEVELOP_STRATEGY**: What strategic approach will address these gaps?
4. **DEFINE_TACTICS**: What specific tactical actions will execute this strategy?
5. **ESTABLISH_METRICS**: How will we measure success?

For each step, explain your reasoning clearly so the plan is transparent and verifiable.

MAIN_PLANNING_TASK:
{planning_prompt}

Expected Effects: The plan should clearly define the strategic approach, specific actions, timeline, and success metrics.
"""
            pddl_enhanced_prompt = pddl_prompt_enhancement

            print(f"   → Enhanced with PDDL-INSTRUCT reasoning chain request ({len(pddl_enhanced_prompt)} chars)...")
            print(f"   → Sending to model...")
            try:
                response = self.agent.chat(pddl_enhanced_prompt)
                plan_text = response.reply or ""

                if not plan_text or plan_text.strip() == "":
                    error_msg = "Model returned empty response"
                    print(f"   ❌ {error_msg}")
                    raise ValueError(error_msg)

                print(f"   → Model responded with {len(plan_text)} chars")

                # Phase 2.3: Extract reasoning chain from response
                reasoning_chain = logical_prompt.extract_reasoning_chain(plan_text)
                reasoning_chain_quality = logical_prompt.score_reasoning_quality(reasoning_chain) if reasoning_chain else 0.0

                print(f"   → Extracted {len(reasoning_chain)} reasoning steps (quality: {reasoning_chain_quality:.2f})")

                # Parse and validate the plan
                plan_metadata = {
                    "goal": goal,
                    "domain": goal_analysis.domain,
                    "industry": goal_analysis.industry,
                    "market": goal_analysis.market,
                    "company_type": goal_analysis.company_type,
                    "context_entities_used": goal_analysis.context_entities,
                    "methodologies_applied": goal_analysis.methodologies,
                    "project_context_retrieved": len(project_context),
                    "patterns_applied": len(successful_patterns),
                    "errors_avoided": len(error_patterns),
                    "plan_length": len(plan_text),
                    "reasoning_chain": [step.dict() if hasattr(step, 'dict') else step for step in reasoning_chain],  # Phase 2.3: Store reasoning chain
                    "reasoning_quality": reasoning_chain_quality  # Phase 2.3: Store quality score
                }

                result = self._wrap_result(
                    success=True,
                    output=plan_text,
                    metadata=plan_metadata
                )

                # LEARNING LOOP INTEGRATION: Log pattern usage
                if pattern_context.get('has_learned_patterns'):
                    patterns_used = pattern_context.get('patterns', [])
                    self.pattern_recommender.log_pattern_usage(
                        goal=goal,
                        patterns_recommended=patterns_used,
                        feedback="Plan generated - will gather feedback on usefulness"
                    )
                    print(f"   📊 Logged pattern usage for learning feedback")

                # Log the planning action
                self._log_agent_action("generate_strategic_plan", result)

                print(f"   ✅ Strategic plan generated ({len(plan_text)} chars)")
                print(f"   ✅ Domain: {goal_analysis.domain} | Industry: {goal_analysis.industry} | Market: {goal_analysis.market}")
                print(f"   ✅ Used {len(goal_analysis.context_entities)} context entities: {', '.join(goal_analysis.context_entities)}")
                print(f"   ✅ Applied {len(goal_analysis.methodologies)} domain-specific methodologies")
                print(f"   ✅ Used {plan_metadata['patterns_applied']} learned patterns")
                print(f"   ✅ Avoided {plan_metadata['errors_avoided']} error patterns")

                return result

            except Exception as e:
                return self._handle_error("Planning", e)

        except Exception as e:
            return self._handle_error("Planning", e)

    def _retrieve_project_context(self, goal: str) -> str:
        """Retrieve project context dynamically based on goal analysis

        Args:
            goal: The planning goal

        Returns:
            Formatted project context string
        """
        try:
            # Analyze the goal to determine relevant context
            goal_analysis = self.goal_analyzer.analyze_goal(goal)

            # Retrieve context from multiple relevant entities
            context_parts = []

            for entity in goal_analysis.context_entities:
                try:
                    response = self.agent.chat(f"""
                        OPERATION: RETRIEVE
                        ENTITY: {entity}
                        CONTEXT: Comprehensive project context for strategic planning

                        Provide detailed information about:
                        - Current project status and requirements
                        - Industry-specific methodologies and frameworks
                        - Market dynamics and competitive landscape
                        - Regulatory requirements and compliance standards
                        - Quality standards and best practices
                        - Any specific challenges and considerations
                    """)
                    if response.reply and response.reply.strip():
                        context_parts.append(f"=== {entity.upper()} CONTEXT ===\n{response.reply}")
                except:
                    continue

            if context_parts:
                combined_context = "\n\n".join(context_parts)
                return combined_context
            else:
                # Fallback to generic context if no specific entities found
                return self._retrieve_generic_context(goal_analysis)

        except Exception as e:
            return f"Context retrieval failed: {str(e)}"

    def _retrieve_generic_context(self, goal_analysis) -> str:
        """Retrieve generic context when no specific entities are available

        Args:
            goal_analysis: Analyzed goal information

        Returns:
            Generic context string
        """
        try:
            response = self.agent.chat(f"""
                OPERATION: RETRIEVE
                ENTITY: successful_patterns
                CONTEXT: Generic strategic planning context

                Provide information about:
                - General strategic planning approaches
                - Market entry methodologies
                - Business development frameworks
                - Risk assessment protocols
                - Success metrics and KPIs
            """)
            return response.reply or "No generic context available"
        except:
            return "Generic context retrieval failed"

    def _retrieve_successful_patterns(self) -> str:
        """Retrieve successful planning patterns from MemAgent

        Returns:
            Successful patterns string
        """
        try:
            response = self.agent.chat("""
                OPERATION: RETRIEVE
                ENTITY: successful_patterns
                CONTEXT: Proven planning approaches

                What planning patterns have worked well?
                What specific approaches led to successful outcomes?
                What methodologies proved effective?
            """)
            return response.reply or "No successful patterns available"
        except:
            return "Pattern retrieval failed"

    def _retrieve_error_patterns(self) -> str:
        """Retrieve error patterns to avoid from MemAgent

        Returns:
            Error patterns string
        """
        try:
            response = self.agent.chat("""
                OPERATION: RETRIEVE
                ENTITY: planning_errors
                CONTEXT: Planning mistakes to avoid

                What planning approaches have been rejected?
                What common mistakes should be avoided?
                What patterns led to failures?
            """)
            return response.reply or "No error patterns available"
        except:
            return "Error pattern retrieval failed"

    def _retrieve_current_state(self) -> str:
        """Retrieve current project state from MemAgent

        Returns:
            Current state string
        """
        try:
            response = self.agent.chat("""
                OPERATION: RETRIEVE
                ENTITY: execution_log
                CONTEXT: Current project state

                What is the current state of the project?
                What has been completed?
                What is the next priority?
            """)
            return response.reply or "No current state available"
        except:
            return "Current state retrieval failed"
