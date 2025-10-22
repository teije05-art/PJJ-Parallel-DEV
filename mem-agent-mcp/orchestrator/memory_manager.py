"""
Memory Manager Module

Single Responsibility: Store results and update memory

This module handles all memory storage operations:
- Saves plan files to plans/ directory
- Updates execution log
- Updates successful/error patterns
- Populates entity files

No dependencies on: Context retrieval, agent execution, approval workflow
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from .agentflow_agents import AgentResult


class MemoryManager:
    """Manages all memory storage operations"""

    def __init__(self, agent: Agent, memory_path: Path):
        """
        Initialize memory manager

        Args:
            agent: The memagent instance (shared across all modules)
            memory_path: Path to memory directory
        """
        self.agent = agent
        self.memory_path = memory_path

    def store_results(self, goal: str, agent_results: Dict[str, AgentResult], success: bool):
        """
        Main entry point - stores all results to memory

        Args:
            goal: The planning goal
            agent_results: Results from all 4 agents
            success: Whether the workflow was approved (True) or rejected (False)
        """
        print("\n💾 MEMORY MANAGER: Storing results to memory...")

        if success:
            # Approved workflow - store as success
            self._store_successful_workflow(goal, agent_results)
        else:
            # Rejected workflow - store as error/learning
            self._store_rejected_workflow(goal, agent_results)

        # Always save the plan file for visibility
        self._save_plan_file(goal, agent_results)

        # Populate entities with agent content
        self._populate_entities(goal, agent_results)

        # Store deliverables
        self._store_deliverables(goal, agent_results)

        print("   ✅ All results stored to memory")

    def _store_successful_workflow(self, goal: str, agent_results: Dict[str, AgentResult]):
        """Store successful workflow to memory"""
        # Update execution log
        execution_log = self.memory_path / "entities" / "execution_log.md"
        if execution_log.exists():
            with open(execution_log, 'a') as f:
                f.write(f"\n## Enhanced Execution {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Goal:** {goal}\n")
                f.write(f"**Status:** SUCCESS ✅\n")
                f.write(f"**Flow-GRPO Training:** Applied\n\n")

                # Add agent-specific results
                f.write("**Agent Results:**\n")
                for agent_name, result in agent_results.items():
                    if isinstance(result, AgentResult):
                        f.write(f"- {agent_name}: {'✅ SUCCESS' if result.success else '❌ FAILED'}\n")
                f.write("\n")

        # Update successful patterns
        patterns_file = self.memory_path / "entities" / "successful_patterns.md"
        if patterns_file.exists():
            with open(patterns_file, 'a') as f:
                f.write(f"\n## Enhanced Successful Pattern - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Goal:** {goal}\n")
                f.write(f"**What Worked:** Coordinated workflow was approved and executed successfully\n")
                f.write(f"**Agent Coordination:** All agents worked together effectively\n")
                f.write(f"**Flow-GRPO Training:** Positive signal applied to Planner\n\n")

                # Add agent-specific success patterns
                f.write("**Agent-Specific Success Factors:**\n")
                if 'planner' in agent_results and agent_results['planner'].success:
                    f.write(f"- Planner: Strategic approach was effective\n")
                if 'executor' in agent_results and agent_results['executor'].success:
                    f.write(f"- Executor: Implementation method worked well\n")
                if 'verifier' in agent_results and agent_results['verifier'].success:
                    f.write(f"- Verifier: Validation approach was successful\n")
                if 'generator' in agent_results and agent_results['generator'].success:
                    f.write(f"- Generator: Synthesis method was effective\n")
                f.write("\n")

        print("   ✅ Successful workflow stored")

    def _store_rejected_workflow(self, goal: str, agent_results: Dict[str, AgentResult]):
        """Store rejected workflow to memory for learning"""
        errors_file = self.memory_path / "entities" / "planning_errors.md"
        if errors_file.exists():
            with open(errors_file, 'a') as f:
                f.write(f"\n## Enhanced Rejection - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Goal:** {goal}\n")
                f.write(f"**Status:** REJECTED ❌\n")
                f.write(f"**Flow-GRPO Training:** Negative signal applied to Planner\n\n")

                # Add agent-specific rejection insights
                f.write("**Agent Results at Rejection:**\n")
                for agent_name, result in agent_results.items():
                    if isinstance(result, AgentResult):
                        f.write(f"- {agent_name}: {'✅ SUCCESS' if result.success else '❌ FAILED'}\n")
                f.write("\n")

        print("   ✅ Rejected workflow stored for learning")

    def _save_plan_file(self, goal: str, agent_results: Dict[str, AgentResult]):
        """Save comprehensive plan to plans/ directory"""
        plans_dir = self.memory_path / "plans"
        plans_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        goal_slug = goal.replace(" ", "_").replace("/", "_").replace("\\", "_")[:50]
        plan_file = plans_dir / f"plan_{timestamp}_{goal_slug}.md"

        # Get agent results
        planner_result = agent_results.get('planner')
        verifier_result = agent_results.get('verifier')
        executor_result = agent_results.get('executor')
        generator_result = agent_results.get('generator')

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
*Generated by Modular Learning Orchestrator at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        plan_file.write_text(plan_content)
        print(f"   📄 Comprehensive plan saved to: {plan_file}")

    def _populate_entities(self, goal: str, agent_results: Dict[str, AgentResult]):
        """Populate entity files with agent content"""
        print("   📝 Populating entities with agent content...")

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
            'recommendations_and_next_steps': 'generator'
        }

        entities_dir = self.memory_path / "entities"

        for entity_name, agent_type in entity_mappings.items():
            try:
                agent_result = agent_results.get(agent_type)
                if agent_result and agent_result.success and agent_result.output:
                    entity_file = entities_dir / f"{entity_name}.md"

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
            except Exception as e:
                print(f"   ⚠️ Failed to populate {entity_name}: {e}")

        print("   ✅ Entities populated")

    def _store_deliverables(self, goal: str, agent_results: Dict[str, AgentResult]):
        """Store comprehensive deliverables"""
        deliverables_dir = self.memory_path / "deliverables"
        deliverables_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create comprehensive execution report
        planner_result = agent_results.get('planner')
        verifier_result = agent_results.get('verifier')
        executor_result = agent_results.get('executor')
        generator_result = agent_results.get('generator')

        execution_report = f"""# Enhanced Workflow Execution Report - {timestamp}

## Goal
{goal}

## Coordinated Agent Results

### 🧭 Planner Agent
{planner_result.output if planner_result else 'No planner results'}

### ✅ Verifier Agent
{verifier_result.output if verifier_result else 'No verifier results'}

### 🛠️ Executor Agent
{executor_result.output if executor_result else 'No executor results'}

### ✍️ Generator Agent
{generator_result.output if generator_result else 'No generator results'}

## Workflow Success Metrics
- Planner Success: {'✅' if planner_result and planner_result.success else '❌'}
- Verifier Success: {'✅' if verifier_result and verifier_result.success else '❌'}
- Executor Success: {'✅' if executor_result and executor_result.success else '❌'}
- Generator Success: {'✅' if generator_result and generator_result.success else '❌'}

---
*Executed by Modular Learning Orchestrator at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        execution_file = deliverables_dir / f"enhanced_execution_report_{timestamp}.md"
        execution_file.write_text(execution_report)

        print(f"   📁 Deliverables stored")
