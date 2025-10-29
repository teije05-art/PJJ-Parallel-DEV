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
from typing import Dict

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from .base_agent import BaseAgent, AgentResult
from orchestrator.goal_analyzer import GoalAnalyzer
from orchestrator.templates import TemplateSelector


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

    def generate_strategic_plan(self, goal: str, context: Dict[str, str]) -> AgentResult:
        """Generate a strategic plan using MemAgent context and learned patterns

        Args:
            goal: The planning goal/objective
            context: Context data from context manager

        Returns:
            AgentResult with strategic plan or error details
        """

        print(f"\n🧭 PLANNER AGENT: Generating strategic plan...")

        try:
            # Analyze the goal to determine domain and context requirements
            goal_analysis = self.goal_analyzer.analyze_goal(goal)
            print(f"   → Goal Analysis: Domain={goal_analysis.domain}, Industry={goal_analysis.industry}")

            # Retrieve comprehensive context from MemAgent using dynamic selection
            project_context = self._retrieve_project_context(goal)
            successful_patterns = self._retrieve_successful_patterns()
            error_patterns = self._retrieve_error_patterns()
            current_state = self._retrieve_current_state()

            print(f"   → Context retrieved: project={len(project_context)} chars, patterns={len(successful_patterns)} chars")

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
                'web_search_results': web_search_results
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

            print(f"   → Sending prompt to model ({len(planning_prompt)} chars)...")
            try:
                response = self.agent.chat(planning_prompt)
                plan_text = response.reply or ""

                if not plan_text or plan_text.strip() == "":
                    error_msg = "Model returned empty response"
                    print(f"   ❌ {error_msg}")
                    raise ValueError(error_msg)

                print(f"   → Model responded with {len(plan_text)} chars")

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
                    "plan_length": len(plan_text)
                }

                result = self._wrap_result(
                    success=True,
                    output=plan_text,
                    metadata=plan_metadata
                )

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
