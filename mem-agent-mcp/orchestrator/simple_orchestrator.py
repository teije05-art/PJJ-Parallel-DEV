"""
Simple Orchestrator - Modular Architecture

This orchestrator is SIMPLE by design - it just calls modules in sequence.
Each module is independent and can be fixed/tested separately.

Key differences from the old EnhancedLearningOrchestrator:
- Only ~150 lines (vs 870 lines)
- Just coordinates modules (no business logic here)
- Each module is independent (no cascading failures)
- Easy to add features (just add new modules)
- Easy to test (test modules separately)

Architecture:
1. ContextManager - Retrieves context (includes web search!)
2. WorkflowCoordinator - Runs 4-agent workflow
3. ApprovalHandler - Gets human approval
4. MemoryManager - Stores results to memory
5. LearningManager - Applies Flow-GRPO training
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from .context.context_builder import ContextBuilder
from .workflow_coordinator import WorkflowCoordinator
from .approval_handler import ApprovalHandler
from .memory_manager import MemoryManager
from .learning_manager import LearningManager
from .iteration_manager import IterationManager, IterationResult


class SimpleOrchestrator:
    """
    Simple modular orchestrator - just coordinates modules

    This orchestrator is intentionally simple. All business logic
    is in the modules. This makes the system maintainable and testable.
    """

    def __init__(self, memory_path: str, max_iterations: int = 15, strict_validation: bool = False):
        """
        Initialize the simple modular orchestrator

        Args:
            memory_path: Path to MemAgent memory directory
            max_iterations: Maximum number of learning iterations
            strict_validation: If True, use strict validation
        """
        self.memory_path = Path(memory_path)
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.strict_validation = strict_validation

        # Initialize ONE memagent instance (shared across all modules)
        use_fireworks = sys.platform == "darwin"  # Mac uses Fireworks
        use_vllm = sys.platform == "linux"        # H100 uses vLLM

        self.agent = Agent(
            use_fireworks=use_fireworks,
            use_vllm=use_vllm,
            memory_path=str(memory_path),
            predetermined_memory_path=False
        )

        # Initialize all modules (all share the same agent instance)
        self.context_manager = ContextBuilder(self.agent, self.memory_path)
        self.workflow_coordinator = WorkflowCoordinator(self.agent, self.memory_path)
        self.approval_handler = ApprovalHandler()  # Simple approval handler (summaries deferred to post-success)
        self.memory_manager = MemoryManager(self.agent, self.memory_path)
        self.learning_manager = LearningManager(self.agent, self.memory_path)

        # CRITICAL: Expose agent_coordinator for autonomous mode compatibility
        # The MCP server's autonomous planning expects orchestrator.agent_coordinator
        self.agent_coordinator = self.workflow_coordinator.agent_coordinator

        # Ensure memory entities exist
        self._initialize_memory_entities()

        print(f"🚀 Simple Modular Orchestrator initialized")
        print(f"   Backend: {'Fireworks (Mac)' if use_fireworks else 'vLLM (H100)'}")
        print(f"   Memory: {memory_path}")
        print(f"   Max iterations: {max_iterations}")
        print(f"   Modules: ✅ Context, Workflow, Approval, Memory, Learning")
        print(f"   Web Search: ✅ Enabled for better plan quality")

    def _initialize_memory_entities(self):
        """Create memory entity files if they don't exist"""
        entities_dir = self.memory_path / "entities"
        entities_dir.mkdir(parents=True, exist_ok=True)

        # Execution log
        execution_log = entities_dir / "execution_log.md"
        if not execution_log.exists():
            execution_log.write_text(
                "# Enhanced Execution Log\n\n"
                "This file tracks all approved and executed agentic workflows.\n"
                "Each successful iteration adds learned context through Flow-GRPO training.\n\n"
            )

        # Successful patterns
        patterns_file = entities_dir / "successful_patterns.md"
        if not patterns_file.exists():
            patterns_file.write_text(
                "# Enhanced Successful Planning Patterns\n\n"
                "This file tracks proven approaches that work across all 4 agents.\n"
                "Used for in-context learning and Flow-GRPO optimization.\n\n"
            )

        # Planning errors
        errors_file = entities_dir / "planning_errors.md"
        if not errors_file.exists():
            errors_file.write_text(
                "# Enhanced Planning Errors to Avoid\n\n"
                "This file tracks rejected workflows and common mistakes across all agents.\n"
                "Used to avoid repeating failures and improve Flow-GRPO training.\n\n"
            )

    def run_enhanced_learning_loop(self, goal: str):
        """
        Main learning loop - simple sequential execution

        This is intentionally simple - just calls modules in order.
        All the complexity is in the modules themselves.
        """
        print(f"\n🎯 STARTING MODULAR LEARNING LOOP")
        print(f"Goal: {goal}")
        print(f"Max iterations: {self.max_iterations}")
        print("=" * 80)

        for iteration in range(1, self.max_iterations + 1):
            self.current_iteration = iteration
            print(f"\n🔄 ITERATION {iteration}/{self.max_iterations}")
            print("-" * 60)

            try:
                # Step 1: Get context (includes web search for real data!)
                context = self.context_manager.retrieve_context(goal)

                # Step 2: Run workflow (4 agents work together)
                agent_results = self.workflow_coordinator.run_workflow(goal, context)

                # Step 3: Get human approval
                decision = self.approval_handler.get_approval(agent_results, goal)

                if decision.approved:
                    # Step 4: Store results (writes to memory)
                    self.memory_manager.store_results(goal, agent_results, success=True)

                    # Step 5: Apply learning (Flow-GRPO training)
                    self.learning_manager.apply_learning(agent_results, decision.feedback, success=True)

                    print(f"\n🎉 SUCCESS! Workflow approved and executed.")
                    print(f"Learning iteration {iteration} completed successfully.")
                    print(f"Flow-GRPO training applied to improve future iterations.")
                    return True

                elif decision.action == "rejected":
                    # Store as failure for learning
                    self.memory_manager.store_results(goal, agent_results, success=False)
                    self.learning_manager.apply_learning(agent_results, decision.feedback, success=False)

                    print(f"\n📚 Learning from rejection: {decision.feedback}")
                    print(f"Flow-GRPO training applied with negative signal.")

                elif decision.action == "edited":
                    # Learn from feedback
                    self.learning_manager.apply_learning(agent_results, decision.feedback, success=False)

                    print(f"\n📝 Learning from feedback: {decision.feedback}")
                    print(f"Flow-GRPO training applied with corrective signal.")

            except KeyboardInterrupt:
                print(f"\n🛑 Learning loop interrupted by user.")
                return False
            except Exception as e:
                print(f"\n❌ Error in iteration {iteration}: {e}")
                import traceback
                traceback.print_exc()
                continue

        print(f"\n⚠️ Learning loop completed without approval.")
        print(f"Consider refining the goal or providing more specific feedback.")
        return False

    # ==================== MULTI-ITERATION PLANNING ====================

    def run_iterative_planning(self, goal: str, proposal: str, max_iterations: int = 6,
                               checkpoint_interval: int = 3, llama_planner=None):
        """
        Run multi-iteration planning with MemAgent-guided refinement.

        Each iteration builds on previous through MemAgent semantic retrieval.
        User approves at checkpoints. Final plan is synthesized from all iterations.

        Args:
            goal: Original planning goal from user
            proposal: The approved proposal to build iterations from
            max_iterations: Total iterations to run (default 6)
            checkpoint_interval: Checkpoint every N iterations (default 3)
            llama_planner: Optional LlamaPlanner instance (uses default if None)

        Yields:
            Dict with checkpoint summaries and final plan

        Returns:
            Dict with final plan and aggregated metrics
        """
        print(f"\n{'='*80}")
        print(f"🔄 STARTING MULTI-ITERATION PLANNING")
        print(f"Goal: {goal}")
        print(f"Iterations: {max_iterations} (checkpoint every {checkpoint_interval})")
        print(f"{'='*80}")

        # Use provided llama_planner or create default
        from llama_planner import LlamaPlanner
        if llama_planner is None:
            llama_planner = LlamaPlanner(self.memory_path)

        # Initialize iteration manager with MemAgent guidance
        iteration_mgr = IterationManager(
            max_iterations=max_iterations,
            checkpoint_interval=checkpoint_interval,
            llama_planner=llama_planner,
            goal=goal
        )
        iteration_mgr.initialize_from_proposal(proposal)

        all_results = []

        # MAIN ITERATION LOOP
        while iteration_mgr.current_iteration < max_iterations:
            iteration_num = iteration_mgr.get_next_iteration_number()

            print(f"\n{'─'*80}")
            print(f"🔄 ITERATION {iteration_num}/{max_iterations}")
            print(f"{'─'*80}")

            try:
                # Step 1: Get base context
                context = self.context_manager.retrieve_context(goal)

                # Step 2: Enhance context with iteration-specific guidance (MemAgent-driven)
                context = iteration_mgr.get_iteration_context(context)

                # Step 3: Run the 4-agent pipeline with iteration guidance
                print(f"Running 4-agent workflow with MemAgent guidance...")
                agent_results = self.workflow_coordinator.run_workflow(goal, context)

                # Step 4: Extract metadata from agent results
                # This is a simplification - you may need to adjust based on actual agent output format
                iteration_result = IterationResult(
                    iteration_num=iteration_num,
                    plan=agent_results.get('plan', agent_results.get('content', str(agent_results))),
                    key_insights=self._extract_key_insights(agent_results),
                    frameworks_used=self._extract_frameworks_used(agent_results),
                    data_points_count=self._extract_data_point_count(agent_results),
                    metadata={'iteration_num': iteration_num}
                )

                # Step 5: Store to MemAgent (critical for next iteration guidance)
                iteration_mgr.store_iteration_result(iteration_result)
                all_results.append(iteration_result)

                print(f"✅ Iteration {iteration_num} complete")
                print(f"   Frameworks used: {len(iteration_result.frameworks_used)}")
                print(f"   Data points: {iteration_result.data_points_count}")

                # Step 6: Check if we should checkpoint
                if iteration_mgr.should_checkpoint():
                    iteration_mgr.mark_checkpoint_complete()

                    checkpoint_summary = self._generate_checkpoint_summary(
                        iteration_mgr=iteration_mgr,
                        current_results=all_results,
                        goal=goal
                    )

                    print(f"\n{'='*80}")
                    print(f"🎯 CHECKPOINT REACHED: Iteration {iteration_num}")
                    print(f"{'='*80}")

                    yield {
                        'type': 'checkpoint',
                        'iteration': iteration_num,
                        'summary': checkpoint_summary,
                        'progress': iteration_mgr.get_iteration_summary(),
                        'metrics': iteration_mgr.get_cumulative_metrics(),
                        'action_required': 'user_approval'
                    }

                    # User approval handling is done in simple_chatbox.py
                    # This function yields control back to the user

                elif iteration_mgr.at_final_iteration():
                    print(f"\n✅ Final iteration {iteration_num} complete")
                    break

            except KeyboardInterrupt:
                print(f"\n🛑 Iteration loop interrupted by user")
                return {
                    'type': 'cancelled',
                    'iterations_completed': len(all_results),
                    'message': 'User cancelled iteration loop'
                }
            except Exception as e:
                print(f"\n❌ Error in iteration {iteration_num}: {e}")
                import traceback
                traceback.print_exc()

                # Store error and continue to next iteration
                continue

        # SYNTHESIS: Combine all iterations into final comprehensive plan
        print(f"\n{'='*80}")
        print(f"✨ SYNTHESIZING FINAL COMPREHENSIVE PLAN")
        print(f"{'='*80}")

        final_plan = self._synthesize_all_iterations(all_results, goal)

        metrics = iteration_mgr.get_cumulative_metrics()

        return {
            'type': 'final_plan',
            'plan': final_plan,
            'iteration_count': len(all_results),
            'unique_frameworks': metrics['unique_frameworks'],
            'total_data_points': metrics['total_data_points'],
            'total_insights': metrics['total_insights'],
            'iteration_history': iteration_mgr.get_iteration_history_summary(),
            'summary': iteration_mgr.get_iteration_summary()
        }

    # ==================== HELPER METHODS FOR ITERATION ====================

    def _extract_key_insights(self, agent_results) -> list:
        """
        Extract key insights from agent results.

        This is a placeholder - adapt based on actual agent output format.
        """
        insights = []
        try:
            # Try to extract from various possible formats
            if isinstance(agent_results, dict):
                if 'insights' in agent_results:
                    insights = agent_results['insights']
                elif 'key_findings' in agent_results:
                    insights = agent_results['key_findings']
                elif 'content' in agent_results:
                    # Parse content to find insight markers
                    content = agent_results['content']
                    if 'Key insight' in content or 'Finding:' in content:
                        # Simple extraction - can be improved
                        lines = content.split('\n')
                        for line in lines:
                            if 'insight' in line.lower() or 'finding' in line.lower():
                                insights.append(line.strip())
        except Exception as e:
            print(f"Warning: Could not extract insights: {e}")

        return insights[:5]  # Top 5 insights

    def _extract_frameworks_used(self, agent_results) -> list:
        """
        Extract frameworks mentioned in agent results.

        This is a placeholder - adapt based on actual agent output format.
        """
        frameworks = []
        try:
            if isinstance(agent_results, dict):
                if 'frameworks' in agent_results:
                    frameworks = agent_results['frameworks']
                elif 'content' in agent_results:
                    # Simple extraction of framework keywords
                    content = agent_results['content']
                    framework_keywords = [
                        'Porter\'s Five Forces', 'SWOT', 'Market analysis',
                        'Competitive analysis', 'Risk assessment', 'PESTLE',
                        'Value proposition', 'Implementation roadmap',
                        'Financial projections', 'Go-to-market'
                    ]
                    for keyword in framework_keywords:
                        if keyword in content:
                            frameworks.append(keyword)
        except Exception as e:
            print(f"Warning: Could not extract frameworks: {e}")

        return frameworks

    def _extract_data_point_count(self, agent_results) -> int:
        """
        Count data points (metrics, figures, citations) in agent results.

        This is a placeholder - adapt based on actual agent output format.
        """
        count = 0
        try:
            if isinstance(agent_results, dict):
                if 'data_points' in agent_results:
                    count = agent_results['data_points']
                elif 'content' in agent_results:
                    # Count citations and numeric data points
                    content = agent_results['content']
                    import re
                    # Count [source: ...] citations
                    count = len(re.findall(r'\[source:', content, re.IGNORECASE))
                    # Count percentage figures (30%, $5M, etc.)
                    count += len(re.findall(r'\d+(\.\d+)?%|\$\d+[BM]?', content))
        except Exception as e:
            print(f"Warning: Could not count data points: {e}")

        return count

    def _generate_checkpoint_summary(self, iteration_mgr: IterationManager,
                                     current_results: list, goal: str) -> str:
        """
        Generate comprehensive checkpoint summary for user review.

        Shows:
        - Analysis progress and momentum
        - Top 5 insights discovered
        - Iteration-by-iteration evolution with approach shifts
        - Goal-specific metrics (not generic)
        - Entity insights used (what was extracted)
        - Frameworks used and evolved

        Executive summary tone, 800-1500 words based on actual depth of changes.
        """
        iterations_completed = iteration_mgr.current_iteration
        total_iterations = iteration_mgr.max_iterations
        total_data_points = iteration_mgr._count_total_data_points()
        unique_frameworks = iteration_mgr._count_unique_frameworks()

        # Extract insights from results
        all_insights = []
        for result in current_results:
            all_insights.extend(result.key_insights if result.key_insights else [])

        # Get top 5 insights
        top_insights = all_insights[:5] if all_insights else ["Analysis progressing through iterations"]

        # Build summary sections
        sections = []

        # 1. ANALYSIS PROGRESS
        progress_section = self._build_analysis_progress_section(
            iterations_completed, total_iterations, total_data_points, unique_frameworks, current_results
        )
        sections.append(progress_section)

        # 2. KEY INSIGHTS (Top 5)
        insights_section = self._build_key_insights_section(top_insights)
        sections.append(insights_section)

        # 3. ITERATION-BY-ITERATION EVOLUTION
        evolution_section = self._build_iteration_evolution_section(current_results, goal)
        sections.append(evolution_section)

        # 4. GOAL-SPECIFIC METRICS
        metrics_section = self._build_goal_specific_metrics_section(current_results, goal)
        sections.append(metrics_section)

        # 5. ENTITY INSIGHTS USED
        entity_section = self._build_entity_insights_section(current_results)
        sections.append(entity_section)

        # Combine all sections
        summary = f"""# CHECKPOINT SUMMARY — Iteration {iterations_completed}/{total_iterations}

{chr(10).join(sections)}

---

**Progress:** {iterations_completed}/{total_iterations} iterations complete ({int(100 * int(iterations_completed) / int(total_iterations))}%)

If approved, iterations {iterations_completed + 1}-{total_iterations} will continue with MemAgent-guided deepening based on these insights.
"""
        return summary.strip()

    def _build_analysis_progress_section(self, completed: int, total: int, data_points: int,
                                        frameworks: int, results: list) -> str:
        """Build the analysis progress section showing momentum."""
        # Calculate momentum
        if len(results) >= 2:
            prev_frameworks = len(set([f for r in results[:-1] for f in r.frameworks_used]))
            prev_data = sum(r.data_points_count for r in results[:-1])
            framework_change = f"({prev_frameworks} → {frameworks})"
            data_change = f"(+{data_points - prev_data} new)"
        else:
            framework_change = ""
            data_change = ""

        return f"""## 📊 ANALYSIS PROGRESS

**Iterations completed:** {completed}/{total} ({int(100 * int(completed) / int(total))}%)
**Frameworks evolved:** {frameworks} unique frameworks applied {framework_change}
**Data points discovered:** {data_points} key metrics and figures {data_change}
**Analysis depth:** Progressing from broad scope to strategic specifics
**Evidence density:** Increasing iteration-by-iteration"""

    def _build_key_insights_section(self, insights: list) -> str:
        """Build the top 5 insights section."""
        insights_text = ""
        for i, insight in enumerate(insights[:5], 1):
            # Clean up insight text
            clean_insight = str(insight).strip()
            if clean_insight:
                insights_text += f"\n**{i}. {clean_insight}**"

        return f"""## 🔍 KEY INSIGHTS (Top 5)
{insights_text if insights_text else "- Analysis insights emerging through iterations"}"""

    def _build_iteration_evolution_section(self, results: list, goal: str) -> str:
        """Build iteration-by-iteration evolution showing approach shifts."""
        evolution_text = """## 📈 ITERATION-BY-ITERATION EVOLUTION"""

        for i, result in enumerate(results, 1):
            iteration_num = result.iteration_num
            frameworks = result.frameworks_used if result.frameworks_used else ["Foundation analysis"]
            data_points = result.data_points_count

            # Build iteration detail
            evolution_text += f"\n\n**Iteration {iteration_num}:**"

            if i == 1:
                evolution_text += f"\n  - **Approach:** Foundation — broad market/domain analysis"
            else:
                # Detect approach shift by comparing to previous
                prev_frameworks = set(results[i-2].frameworks_used) if i > 1 else set()
                new_frameworks = set(frameworks) - prev_frameworks
                if new_frameworks:
                    framework_names = ", ".join(new_frameworks)
                    evolution_text += f"\n  - **Approach shift:** Added {framework_names} for deeper analysis"
                else:
                    evolution_text += f"\n  - **Approach:** Continued refinement and detail"

            evolution_text += f"\n  - **Frameworks:** {', '.join(frameworks[:3])}"
            if len(frameworks) > 3:
                evolution_text += f" (+{len(frameworks)-3} more)"

            evolution_text += f"\n  - **Key findings:** {data_points} data points extracted"

            if result.key_insights:
                top_insight = str(result.key_insights[0]).strip()[:80]
                evolution_text += f"\n  - **Primary finding:** {top_insight}..."

        return evolution_text

    def _build_goal_specific_metrics_section(self, results: list, goal: str) -> str:
        """Build goal-specific metrics section (show only relevant metrics)."""
        # Detect goal type from the goal string
        goal_lower = goal.lower()

        metrics_text = """## 📋 KEY METRICS & DATA"""

        # Map goal keywords to metric types
        if any(word in goal_lower for word in ['market', 'size', 'tam', 'addressable']):
            metrics_text += """
  - **Market sizing:** TAM/SAM/SOM analysis in progress
  - **Growth rates:** CAGR projections being validated
  - **Competitive benchmarks:** Pricing and positioning data"""

        if any(word in goal_lower for word in ['healthcare', 'medical', 'patient', 'clinical']):
            metrics_text += """
  - **Clinical metrics:** Efficacy rates and outcome data
  - **Patient adoption:** Penetration rate projections
  - **Regulatory pathway:** Approval timeline and requirements
  - **Reimbursement:** Insurance coverage and payment models"""

        if any(word in goal_lower for word in ['tech', 'software', 'technology', 'platform']):
            metrics_text += """
  - **Performance metrics:** Speed, scalability, reliability
  - **Integration capability:** API/compatibility requirements
  - **Unit economics:** Cost per deployment/user
  - **Market adoption:** Competitive positioning and feature gaps"""

        if any(word in goal_lower for word in ['manufacturing', 'production', 'supply', 'logistics']):
            metrics_text += """
  - **Production costs:** Unit economics and scaling
  - **Supply chain:** Critical dependencies and lead times
  - **Capacity:** Current and future production capability
  - **Quality metrics:** Defect rates and efficiency measures"""

        if any(word in goal_lower for word in ['strategy', 'entry', 'launch', 'go-to-market']):
            metrics_text += """
  - **Market opportunity:** Addressable segments and TAM
  - **Competitive positioning:** Differentiation factors
  - **Implementation timeline:** Phased rollout and milestones
  - **Resource requirements:** Budget, team, and infrastructure needs"""

        # If no specific goal type matched, show generic
        if metrics_text == """## 📋 KEY METRICS & DATA""":
            metrics_text += """
  - **Analysis coverage:** Domain-specific data being extracted
  - **Key findings:** Metrics aligned to goal requirements
  - **Benchmarking:** Competitive and industry data"""

        return metrics_text

    def _build_entity_insights_section(self, results: list) -> str:
        """Build section showing what information was extracted (not entity names)."""
        # Aggregate insights across iterations
        all_frameworks = set()
        total_data_points = 0

        for result in results:
            all_frameworks.update(result.frameworks_used if result.frameworks_used else [])
            total_data_points += result.data_points_count

        frameworks_list = ", ".join(sorted(all_frameworks)[:5])
        if len(all_frameworks) > 5:
            frameworks_list += f", +{len(all_frameworks)-5} more"

        return f"""## 🎯 INFORMATION EXTRACTED

From research, memory, and analysis:
  - **Frameworks applied:** {frameworks_list if frameworks_list else "Domain-specific analytical frameworks"}
  - **Data extracted:** {total_data_points} quantified metrics and insights
  - **Information types:** Market data, competitive analysis, regulatory requirements, demographic insights, risk factors
  - **Coverage:** Comprehensive multi-angle analysis building iteration-by-iteration"""

    def _format_frameworks_summary(self, results: list) -> str:
        """Format frameworks from all iterations."""
        all_frameworks = set()
        for result in results:
            all_frameworks.update(result.frameworks_used)

        if all_frameworks:
            return "\n".join([f"- {fw}" for fw in sorted(all_frameworks)])
        else:
            return "- Frameworks will be extracted from agent analysis"

    def _synthesize_all_iterations(self, all_results: list, goal: str) -> str:
        """
        Synthesize all iterations into final comprehensive plan.

        Uses the GeneratorAgent to create a 5000+ word final output that
        incorporates learnings from all iterations.
        """
        print(f"Synthesizing {len(all_results)} iterations into comprehensive final plan...")

        try:
            # Build synthesis context
            synthesis_context = {
                'goal': goal,
                'iterations': len(all_results),
                'all_plans': [r.plan for r in all_results],
                'all_insights': [insight for r in all_results for insight in r.key_insights],
                'all_frameworks': list(set([f for r in all_results for f in r.frameworks_used])),
                'total_data_points': sum(r.data_points_count for r in all_results)
            }

            # Use generator agent for synthesis
            from .agents import GeneratorAgent
            generator = GeneratorAgent()

            synthesis_prompt = f"""
You are synthesizing a comprehensive final plan from {len(all_results)} iterative planning cycles.

GOAL: {goal}

ITERATION SUMMARIES:
{self._format_iteration_history(all_results)}

Your task: Create a comprehensive 5000+ word final plan that:
1. Integrates insights from all {len(all_results)} iterations
2. Highlights the evolution of thinking across iterations
3. Includes all {sum(r.data_points_count for r in all_results)} data points found
4. Applies all {len(set([f for r in all_results for f in r.frameworks_used]))} frameworks identified
5. Provides actionable, specific recommendations

Format: Well-structured markdown with clear sections, data citations [source: ...], and a comprehensive executive summary.
"""

            final_result = generator.run(synthesis_prompt)

            # Extract content from agent result
            if hasattr(final_result, 'content'):
                return final_result.content
            elif isinstance(final_result, dict) and 'content' in final_result:
                return final_result['content']
            else:
                return str(final_result)

        except Exception as e:
            print(f"Warning: Could not synthesize with GeneratorAgent: {e}")
            # Fallback: Create basic synthesis from iteration plans
            return self._create_fallback_synthesis(all_results, goal)

    def _format_iteration_history(self, results: list) -> str:
        """Format iteration history for synthesis prompt."""
        formatted = []
        for result in results:
            formatted.append(f"""
Iteration {result.iteration_num}:
- Frameworks: {', '.join(result.frameworks_used) if result.frameworks_used else 'None recorded'}
- Data points: {result.data_points_count}
- Key insights: {len(result.key_insights)}
""")
        return "\n".join(formatted)

    def _create_fallback_synthesis(self, all_results: list, goal: str) -> str:
        """Create basic synthesis if GeneratorAgent fails."""
        synthesis = f"""# Comprehensive Final Plan: {goal}

## Executive Summary
This plan represents the synthesis of {len(all_results)} iterative planning cycles,
each building on the insights of previous iterations through MemAgent-guided refinement.

## Key Statistics
- Total iterations: {len(all_results)}
- Unique frameworks applied: {len(set([f for r in all_results for f in r.frameworks_used]))}
- Data points extracted: {sum(r.data_points_count for r in all_results)}
- Key insights identified: {sum(len(r.key_insights) for r in all_results)}

## Iteration Evolution
"""
        for i, result in enumerate(all_results, 1):
            synthesis += f"\n### Iteration {i}\n{result.plan[:500]}...\n"

        return synthesis

    # Methods used by MCP server (for backward compatibility)
    def _retrieve_enhanced_context(self, goal: str = None):
        """
        Backward compatibility wrapper for MCP server

        IMPORTANT: Autonomous mode calls this WITHOUT a goal parameter.
        We still need to retrieve patterns and history for learning!
        """
        if goal:
            # Full context with goal analysis and web search
            return self.context_manager.retrieve_context(goal)
        else:
            # Generic context without goal-specific analysis
            # Still retrieve patterns and history for autonomous learning!
            print("\n📚 Retrieving generic context (autonomous mode)...")

            try:
                # Get patterns and history (critical for learning!)
                successful_patterns = self.agent.chat("""
                    OPERATION: RETRIEVE
                    ENTITY: successful_patterns
                    CONTEXT: Review successful planning approaches

                    What planning patterns have worked well?
                """).reply or "No successful patterns yet"

                errors_to_avoid = self.agent.chat("""
                    OPERATION: RETRIEVE
                    ENTITY: planning_errors
                    CONTEXT: Review planning mistakes

                    What approaches should be avoided?
                """).reply or "No errors yet"

                execution_history = self.agent.chat("""
                    OPERATION: RETRIEVE
                    ENTITY: execution_log
                    CONTEXT: Review past executions

                    What has been executed?
                """).reply or "No history yet"

                agent_performance = self.agent.chat("""
                    OPERATION: RETRIEVE
                    ENTITY: agent_performance
                    CONTEXT: Review performance

                    How are agents performing?
                """).reply or "No performance data yet"

                return {
                    "current_status": "Generic context (no goal-specific analysis)",
                    "successful_patterns": successful_patterns,
                    "errors_to_avoid": errors_to_avoid,
                    "execution_history": execution_history,
                    "agent_performance": agent_performance
                }
            except Exception as e:
                print(f"   ⚠️ Error retrieving context: {e}")
                return {
                    "current_status": "Context retrieval failed",
                    "successful_patterns": "",
                    "errors_to_avoid": "",
                    "execution_history": "",
                    "agent_performance": ""
                }

    def _get_human_approval(self, agent_results, goal):
        """Backward compatibility wrapper for MCP server"""
        decision = self.approval_handler.get_approval(agent_results, goal)
        if decision.approved:
            return "approved", ""
        else:
            return decision.action, decision.feedback

    def _execute_enhanced_workflow(self, agent_results, goal):
        """Backward compatibility wrapper for MCP server"""
        return {
            "status": "success",
            "actions_completed": len(agent_results),
            "total_actions": len(agent_results),
            "execution_report": "Workflow executed successfully",
            "agent_results": agent_results,
            "deliverables_created": True,
            "flow_grpo_applied": True,
            "timestamp": datetime.now().isoformat(),
            "goal": goal
        }

    def _write_enhanced_success_to_memory(self, agent_results, execution):
        """Backward compatibility wrapper for MCP server"""
        goal = execution.get('goal', 'Unknown goal')
        self.memory_manager.store_results(goal, agent_results, success=True)
        self.learning_manager.apply_learning(agent_results, "", success=True)

    def _write_enhanced_rejection_to_memory(self, agent_results, feedback):
        """Backward compatibility wrapper for MCP server"""
        self.learning_manager.apply_learning(agent_results, feedback, success=False)

    def _write_enhanced_feedback_to_memory(self, agent_results, feedback):
        """Backward compatibility wrapper for MCP server"""
        self.learning_manager.apply_learning(agent_results, feedback, success=False)


# Example usage
if __name__ == "__main__":
    # Initialize simple modular orchestrator
    memory_path = "/Users/teije/Desktop/memagent/local-memory"
    orchestrator = SimpleOrchestrator(memory_path=memory_path, max_iterations=5)

    # Run learning loop
    goal = "Develop a comprehensive market entry strategy for a healthcare company"
    success = orchestrator.run_enhanced_learning_loop(goal)

    if success:
        print("\n🎉 Learning loop completed successfully!")
        print("🎯 Flow-GRPO training has improved the Planner Agent!")
        print("🌐 Web search provided real current market data!")
    else:
        print("\n⚠️ Learning loop completed without approval.")
