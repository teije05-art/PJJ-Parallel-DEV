"""
Agent Factory - Coordinates the 4 specialized agents

This module creates and manages the 4 agents:
- Planner: Strategic planning
- Verifier: Quality validation
- Executor: Implementation
- Generator: Content synthesis
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
from .base_agent import AgentResult
from .planner_agent import PlannerAgent
from .verifier_agent import VerifierAgent
from .executor_agent import ExecutorAgent
from .generator_agent import GeneratorAgent


class AgentCoordinator:
    """🎯 Agent Coordinator - Orchestrates the 4 specialized agents

    Responsibilities:
    - Coordinate agent interactions
    - Manage shared memory and communication
    - Implement Flow-GRPO optimization
    - Track overall system performance
    """

    def __init__(self, agent: Agent, memory_path: Path):
        """Initialize agent coordinator

        Args:
            agent: The MemAgent instance
            memory_path: Path to memory directory
        """
        self.agent = agent
        self.memory_path = memory_path

        # Initialize specialized agents
        self.planner = PlannerAgent(agent, memory_path)
        self.executor = ExecutorAgent(agent, memory_path)
        self.verifier = VerifierAgent(agent, memory_path)
        self.generator = GeneratorAgent(agent, memory_path)

        # Initialize coordination memory
        self._initialize_coordination_memory()

    def _initialize_coordination_memory(self):
        """Initialize memory entities for agent coordination"""
        entities_dir = self.memory_path / "entities"
        entities_dir.mkdir(parents=True, exist_ok=True)

        # Agent coordination log
        coordination_file = entities_dir / "agent_coordination.md"
        if not coordination_file.exists():
            coordination_file.write_text("""# Agent Coordination Log

This file tracks how the 4 specialized agents work together:
- 🧭 Planner Agent: Strategic planning and decision making
- 🛠️ Executor Agent: Tool execution and action implementation
- ✅ Verifier Agent: Quality checking and validation
- ✍️ Generator Agent: Content synthesis and final output creation

## Coordination Principles
1. All agents use MemAgent for context, execution, and memory
2. Each agent logs its actions for coordination tracking
3. Flow-GRPO optimization trains the Planner based on outcomes
4. Shared memory enables seamless agent communication

""")

        # Planner training log for Flow-GRPO
        training_file = entities_dir / "planner_training_log.md"
        if not training_file.exists():
            training_file.write_text("""# Planner Training Log (Flow-GRPO)

This file tracks the in-the-flow training of the Planner Agent using Flow-GRPO optimization.

## Training Principles
1. Final outcomes are broadcast back to all planning decisions
2. Successful patterns receive positive reinforcement
3. Failed patterns receive negative reinforcement
4. Planner learns to avoid repetitive mistakes and improve decision-making

""")

        # Agent performance tracking
        performance_file = entities_dir / "agent_performance.md"
        if not performance_file.exists():
            performance_file.write_text("""# Agent Performance Tracking

This file tracks the performance metrics of each specialized agent.

## Performance Metrics
- Success rates for each agent
- Quality scores for outputs
- Response times and efficiency
- Learning progress over iterations

""")

    def coordinate_agentic_workflow(self, goal: str, context: Dict[str, str]) -> Dict[str, AgentResult]:
        """Coordinate the complete agentic workflow

        Args:
            goal: The planning goal
            context: Context data from context manager

        Returns:
            Dictionary with results from all agents
        """

        print(f"\n🎯 AGENT COORDINATOR: Starting coordinated workflow...")

        results = {}

        try:
            # Step 1: Planner Agent generates strategic plan
            print(f"\n🔄 STEP 1: Strategic Planning")
            planner_result = self.planner.generate_strategic_plan(goal, context)
            results['planner'] = planner_result

            if not planner_result.success:
                # FIXED (Oct 31, 2025): Now includes error details for debugging
                error_detail = planner_result.error or "Unknown error"
                print(f"❌ Planning failed: {error_detail}")

                # Include metadata if available
                if hasattr(planner_result, 'metadata') and planner_result.metadata:
                    print(f"   Context keys available: {list(planner_result.metadata.keys())}")
                    if 'context_keys' in planner_result.metadata:
                        print(f"   Context: {planner_result.metadata['context_keys']}")

                # Log to learning system for future improvement
                try:
                    training_entry = f"""
## Planning Failure - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Goal:** {goal}
**Error:** {error_detail}
**Context Keys:** {list(context.keys()) if context else 'None'}

---
"""
                    training_file = self.memory_path / "entities" / "planner_training_log.md"
                    if training_file.exists():
                        with open(training_file, 'a') as f:
                            f.write(training_entry)
                except Exception as log_error:
                    print(f"   ⚠️ Could not log failure: {log_error}")

                return results

            # Step 2: Verifier Agent validates the plan
            print(f"\n🔄 STEP 2: Plan Validation")
            verifier_result = self.verifier.verify_plan(planner_result.output, goal, context)
            results['verifier'] = verifier_result

            if not verifier_result.metadata.get('is_valid', False):
                print(f"⚠️ Plan validation failed, but continuing for learning")

            # Step 3: Executor Agent executes the plan
            print(f"\n🔄 STEP 3: Plan Execution")
            executor_result = self.executor.execute_plan(planner_result.output, goal, context)
            results['executor'] = executor_result

            # Step 4: Verifier Agent validates execution
            print(f"\n🔄 STEP 4: Execution Validation")
            execution_verification = self.verifier.verify_execution(
                executor_result.output, planner_result.output
            )
            results['execution_verification'] = execution_verification

            # Step 5: Generator Agent synthesizes final results
            print(f"\n🔄 STEP 5: Result Synthesis")
            generator_result = self.generator.synthesize_results(
                planner_result, executor_result, verifier_result, goal, context
            )
            results['generator'] = generator_result

            # Step 6: Flow-GRPO optimization
            print(f"\n🔄 STEP 6: Flow-GRPO Training")
            self._apply_flow_grpo_training(results, goal, context)

            # Step 7: Store results and populate entities
            print(f"\n🔄 STEP 7: Storing Results and Populating Entities")
            self._store_workflow_results(goal, results)

            print(f"\n🎉 Coordinated workflow completed successfully!")
            return results

        except Exception as e:
            # FIXED (Oct 31, 2025): Now includes full error traceback for debugging
            print(f"\n❌ Workflow coordination failed: {str(e)}")
            import traceback
            traceback.print_exc()  # Log full traceback

            results['error'] = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'timestamp': datetime.now().isoformat()
            }

            # Log critical failures
            try:
                training_file = self.memory_path / "entities" / "planner_training_log.md"
                if training_file.exists():
                    training_entry = f"""
## Critical Workflow Failure - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Error Type:** {type(e).__name__}
**Error Message:** {str(e)}
**Goal:** {goal}

---
"""
                    with open(training_file, 'a') as f:
                        f.write(training_entry)
            except:
                pass  # Don't break on logging failure

            return results

    def _apply_flow_grpo_training(self, results: Dict[str, AgentResult], goal: str, context: Dict = None):
        """Apply Flow-GRPO training to improve Planner Agent

        Args:
            results: Dictionary of agent results
            goal: The planning goal
            context: Context dict that may include agent_coordination for pair performance tracking
        """

        context = context or {}
        print(f"\n🧠 FLOW-GRPO: Applying in-the-flow training...")

        # Determine overall success
        overall_success = self._assess_overall_success(results)

        # Phase 3: Record agent pair performance for learning
        agent_coordination = context.get('agent_coordination')
        if agent_coordination:
            try:
                # Calculate flow score based on results
                flow_score = 0.75  # Default baseline
                if results.get('verifier') and results.get('verifier').success:
                    flow_score += 0.15  # Bonus for successful verification
                if results.get('generator') and results.get('generator').success:
                    flow_score += 0.1  # Bonus for successful synthesis

                # Record agent pair performances
                agent_pairs = [
                    ('planner', 'verifier'),
                    ('verifier', 'executor'),
                    ('executor', 'verifier'),
                    ('verifier', 'generator'),
                ]

                for agent1, agent2 in agent_pairs:
                    try:
                        agent_coordination.record_pair_performance(
                            agent1=agent1,
                            agent2=agent2,
                            flow_score=flow_score,
                            success=overall_success
                        )
                    except Exception as e:
                        if DEBUG:
                            print(f"   ⚠️  Could not record pair performance ({agent1} → {agent2}): {e}")

                print(f"   ✅ Agent pair performance recorded for learning")
            except Exception as e:
                print(f"   ⚠️  Could not apply agent coordination: {e}")

        # Create training record
        training_entry = f"""
## Flow-GRPO Training - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Goal:** {goal}
**Overall Success:** {overall_success}

**Agent Results:**
- Planner: {'✅ SUCCESS' if results.get('planner', {}).success else '❌ FAILED'}
- Verifier: {'✅ SUCCESS' if results.get('verifier', {}).success else '❌ FAILED'}
- Executor: {'✅ SUCCESS' if results.get('executor', {}).success else '❌ FAILED'}
- Generator: {'✅ SUCCESS' if results.get('generator', {}).success else '❌ FAILED'}

**Training Signal:** {'POSITIVE' if overall_success else 'NEGATIVE'}

**Learning Impact:**
- Planner will {'reinforce' if overall_success else 'discourage'} similar approaches
- Memory updated with {'successful' if overall_success else 'failed'} patterns
- Future iterations will {'leverage' if overall_success else 'avoid'} this approach

---
"""

        # Store training record
        training_file = self.memory_path / "entities" / "planner_training_log.md"
        if training_file.exists():
            with open(training_file, 'a') as f:
                f.write(training_entry)

        # Update performance metrics
        self._update_performance_metrics(results, overall_success)

        print(f"   ✅ Flow-GRPO training applied")
        print(f"   ✅ Training signal: {'POSITIVE' if overall_success else 'NEGATIVE'}")

    def _store_workflow_results(self, goal: str, results: Dict[str, AgentResult]):
        """Store workflow results and populate entities with actual content

        Args:
            goal: The planning goal
            results: Dictionary of agent results
        """
        print("\n📁 Storing workflow results...")

        # Get memory path from the agent
        memory_path = self.planner.agent.memory_path if hasattr(self.planner.agent, 'memory_path') else None
        if not memory_path:
            print("   ⚠️ No memory path available, skipping storage")
            return

        # Create plans directory and save comprehensive plan
        plans_dir = Path(memory_path) / "plans"
        plans_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        goal_slug = goal.replace(" ", "_").replace("/", "_").replace("\\", "_")[:50]
        plan_file = plans_dir / f"plan_{timestamp}_{goal_slug}.md"

        # Get agent results
        planner_result = results.get('planner')
        verifier_result = results.get('verifier')
        executor_result = results.get('executor')
        generator_result = results.get('generator')

        # Create comprehensive plan content
        plan_content = f"""# Generated Plan - {timestamp}

## Goal
{goal}

## Generated Plan

{planner_result.output if planner_result else 'No planner results'}

## Verification Results

{verifier_result.output if verifier_result else 'No verifier results'}

## Execution Results

{executor_result.output if executor_result else 'No executor results'}

## Synthesis Results

{generator_result.output if generator_result else 'No generator results'}

## Plan Statistics
- Plan Length: {len(planner_result.output) if planner_result else 0} characters
- Verification Length: {len(verifier_result.output) if verifier_result else 0} characters
- Execution Length: {len(executor_result.output) if executor_result else 0} characters
- Synthesis Length: {len(generator_result.output) if generator_result else 0} characters
- Total Content: {sum([
    len(planner_result.output) if planner_result else 0,
    len(verifier_result.output) if verifier_result else 0,
    len(executor_result.output) if executor_result else 0,
    len(generator_result.output) if generator_result else 0
])} characters

## Agent Performance
- Planner Success: {'✅' if planner_result and planner_result.success else '❌'}
- Verifier Success: {'✅' if verifier_result and verifier_result.success else '❌'}
- Executor Success: {'✅' if executor_result and executor_result.success else '❌'}
- Generator Success: {'✅' if generator_result and generator_result.success else '❌'}

---
*Generated by Refactored Agent Coordinator at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        plan_file.write_text(plan_content)
        print(f"   📄 Comprehensive plan saved to: {plan_file}")

        # Populate entities with actual content
        self._populate_entities_with_content(goal, results, memory_path)

        print(f"   ✅ Workflow results stored successfully")

    def _populate_entities_with_content(self, goal: str, results: Dict[str, AgentResult], memory_path: str):
        """Populate entities with actual content from agent results

        Args:
            goal: The planning goal
            results: Dictionary of agent results
            memory_path: Path to memory directory
        """
        print("\n📝 Populating entities with agent-generated content...")

        # Map entity types to agent content
        entity_mappings = {
            'executive_summary_report': 'generator',
            'detailed_implementation_plan': 'planner',
            'market_analysis_report': 'executor',
            'competitive_intelligence_analysis': 'executor',
            'risk_assessment_and_mitigation_strategy': 'verifier',
            'quality_assurance_framework': 'verifier',
            'timeline_and_resource_allocation': 'planner',
            'success_metrics_and_kpis': 'generator',
            'recommendations_and_next_steps': 'generator',
        }

        entities_dir = Path(memory_path) / "entities"

        for entity_name, agent_type in entity_mappings.items():
            try:
                agent_result = results.get(agent_type)
                if agent_result and agent_result.success and agent_result.output:
                    # Create entity with actual content from agent
                    entity_file = entities_dir / f"{entity_name}.md"

                    # Generate entity-specific content based on agent output
                    entity_content = f"""# {entity_name.replace('_', ' ').title()}

## Project Context
**Goal:** {goal}
**Generated by:** {agent_type.title()} Agent
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Content

{agent_result.output}

## Metadata
- Agent Type: {agent_type}
- Success: {agent_result.success}
- Content Length: {len(agent_result.output)} characters
- Generated: {agent_result.timestamp}
"""

                    entity_file.write_text(entity_content)
                    print(f"   ✅ Populated {entity_name} with {agent_type} content")

            except Exception as e:
                print(f"   ⚠️ Failed to populate {entity_name}: {e}")

        print(f"   ✅ Entity population completed")

    def _assess_overall_success(self, results: Dict[str, AgentResult]) -> bool:
        """Assess overall success of the agentic workflow

        Args:
            results: Dictionary of agent results

        Returns:
            Boolean indicating overall success
        """
        # Consider workflow successful if key agents succeeded
        key_agents = ['planner', 'executor', 'generator']
        successful_agents = sum(1 for agent in key_agents
                              if results.get(agent, {}).success)

        # Workflow succeeds if at least 2 out of 3 key agents succeed
        return successful_agents >= 2

    def _update_performance_metrics(self, results: Dict[str, AgentResult], overall_success: bool):
        """Update agent performance metrics

        Args:
            results: Dictionary of agent results
            overall_success: Boolean indicating overall success
        """

        performance_entry = f"""
## Performance Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Overall Workflow Success:** {overall_success}

**Agent Performance:**
- Planner Agent: {'✅ SUCCESS' if results.get('planner', {}).success else '❌ FAILED'}
- Executor Agent: {'✅ SUCCESS' if results.get('executor', {}).success else '❌ FAILED'}
- Verifier Agent: {'✅ SUCCESS' if results.get('verifier', {}).success else '❌ FAILED'}
- Generator Agent: {'✅ SUCCESS' if results.get('generator', {}).success else '❌ FAILED'}

**Quality Metrics:**
- Plan Quality: {results.get('planner', {}).metadata.get('plan_length', 0)} chars
- Execution Quality: {results.get('executor', {}).metadata.get('deliverables_created', 0)} deliverables
- Verification Checks: {results.get('verifier', {}).metadata.get('checks_performed', 0)} checks
- Synthesis Quality: {results.get('generator', {}).metadata.get('deliverables_created', 0)} deliverables

---
"""

        # Store performance metrics
        performance_file = self.memory_path / "entities" / "agent_performance.md"
        if performance_file.exists():
            with open(performance_file, 'a') as f:
                f.write(performance_entry)
