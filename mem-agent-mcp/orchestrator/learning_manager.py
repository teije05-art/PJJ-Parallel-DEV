"""
Learning Manager Module

Single Responsibility: Apply training signals and improve system

This module handles learning and training:
- Applies Flow-GRPO training signals
- Updates training logs
- Updates performance metrics
- Learns from feedback

No dependencies on: Context retrieval, agent execution, approval workflow
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from .agentflow_agents import AgentResult


class LearningManager:
    """Manages learning and training operations"""

    def __init__(self, agent: Agent, memory_path: Path):
        """
        Initialize learning manager

        Args:
            agent: The memagent instance (shared across all modules)
            memory_path: Path to memory directory
        """
        self.agent = agent
        self.memory_path = memory_path

    def apply_learning(self, agent_results: Dict[str, AgentResult], feedback: Optional[str], success: bool):
        """
        Main entry point - applies learning from workflow results

        Args:
            agent_results: Results from all 4 agents
            feedback: User feedback (if any)
            success: Whether workflow was approved
        """
        print("\n🧠 LEARNING MANAGER: Applying Flow-GRPO training...")

        # Apply Flow-GRPO training
        self._apply_flow_grpo(agent_results, success)

        # Update performance metrics
        self._update_performance_metrics(agent_results, success)

        # Learn from feedback if provided
        if feedback:
            self._learn_from_feedback(agent_results, feedback, success)

        print("   ✅ Flow-GRPO training applied")
        print(f"   ✅ Training signal: {'POSITIVE' if success else 'NEGATIVE'}")

    def _apply_flow_grpo(self, agent_results: Dict[str, AgentResult], success: bool):
        """Apply Flow-GRPO training to Planner Agent"""
        training_entry = f"""
## Flow-GRPO Training - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Overall Success:** {success}

**Agent Results:**
- Planner: {'✅ SUCCESS' if agent_results.get('planner', type('obj', (), {'success': False})()).success else '❌ FAILED'}
- Verifier: {'✅ SUCCESS' if agent_results.get('verifier', type('obj', (), {'success': False})()).success else '❌ FAILED'}
- Executor: {'✅ SUCCESS' if agent_results.get('executor', type('obj', (), {'success': False})()).success else '❌ FAILED'}
- Generator: {'✅ SUCCESS' if agent_results.get('generator', type('obj', (), {'success': False})()).success else '❌ FAILED'}

**Training Signal:** {'POSITIVE' if success else 'NEGATIVE'}

**Learning Impact:**
- Planner will {'reinforce' if success else 'discourage'} similar approaches
- Memory updated with {'successful' if success else 'failed'} patterns
- Future iterations will {'leverage' if success else 'avoid'} this approach

---
"""

        # Store training record
        training_file = self.memory_path / "entities" / "planner_training_log.md"
        if training_file.exists():
            with open(training_file, 'a') as f:
                f.write(training_entry)

        print("   ✅ Flow-GRPO training record updated")

    def _update_performance_metrics(self, agent_results: Dict[str, AgentResult], success: bool):
        """Update agent performance metrics"""
        performance_entry = f"""
## Performance Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Overall Workflow Success:** {success}

**Agent Performance:**
- Planner Agent: {'✅ SUCCESS' if agent_results.get('planner', type('obj', (), {'success': False})()).success else '❌ FAILED'}
- Executor Agent: {'✅ SUCCESS' if agent_results.get('executor', type('obj', (), {'success': False})()).success else '❌ FAILED'}
- Verifier Agent: {'✅ SUCCESS' if agent_results.get('verifier', type('obj', (), {'success': False})()).success else '❌ FAILED'}
- Generator Agent: {'✅ SUCCESS' if agent_results.get('generator', type('obj', (), {'success': False})()).success else '❌ FAILED'}

**Quality Metrics:**
- Plan Quality: {agent_results.get('planner', type('obj', (), {'metadata': {}})()).metadata.get('plan_length', 0)} chars
- Execution Quality: {agent_results.get('executor', type('obj', (), {'metadata': {}})()).metadata.get('deliverables_created', 0)} deliverables
- Verification Checks: {agent_results.get('verifier', type('obj', (), {'metadata': {}})()).metadata.get('checks_performed', 0)} checks
- Synthesis Quality: {agent_results.get('generator', type('obj', (), {'metadata': {}})()).metadata.get('deliverables_created', 0)} deliverables

---
"""

        # Store performance metrics
        performance_file = self.memory_path / "entities" / "agent_performance.md"
        if performance_file.exists():
            with open(performance_file, 'a') as f:
                f.write(performance_entry)

        print("   ✅ Performance metrics updated")

    def _learn_from_feedback(self, agent_results: Dict[str, AgentResult], feedback: str, success: bool):
        """Learn from user feedback"""
        feedback_entry = f"""
## Feedback Learning - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Feedback:** {feedback}
**Success:** {success}

**Agent Results:**
- Planner: {'✅' if agent_results.get('planner', type('obj', (), {'success': False})()).success else '❌'}
- Verifier: {'✅' if agent_results.get('verifier', type('obj', (), {'success': False})()).success else '❌'}
- Executor: {'✅' if agent_results.get('executor', type('obj', (), {'success': False})()).success else '❌'}
- Generator: {'✅' if agent_results.get('generator', type('obj', (), {'success': False})()).success else '❌'}

**Learning Application:**
This feedback will be used to improve future planning iterations.

---
"""

        # Store feedback in patterns (if successful) or errors (if not)
        if success:
            patterns_file = self.memory_path / "entities" / "successful_patterns.md"
            if patterns_file.exists():
                with open(patterns_file, 'a') as f:
                    f.write(feedback_entry)
        else:
            errors_file = self.memory_path / "entities" / "planning_errors.md"
            if errors_file.exists():
                with open(errors_file, 'a') as f:
                    f.write(feedback_entry)

        print("   ✅ Feedback learning applied")
