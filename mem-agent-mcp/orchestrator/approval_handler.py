"""
Approval Handler Module

Single Responsibility: Handle human approval workflow

This module handles user interaction:
- Displays agent results to user
- Gets user decision (approve/reject/edit)
- Returns decision object

No dependencies on: Context retrieval, agent execution, memory storage
"""

import sys
from typing import Tuple
from dataclasses import dataclass
from .agentflow_agents import AgentResult


@dataclass
class ApprovalDecision:
    """Standard format for approval decisions"""
    approved: bool
    feedback: str
    action: str  # 'approved', 'rejected', 'edited', 'quit'


class ApprovalHandler:
    """Handles human approval workflow"""

    def __init__(self):
        """Initialize approval handler"""
        pass

    def get_approval(self, agent_results: dict, goal: str) -> ApprovalDecision:
        """
        Main entry point - gets human approval for workflow results

        Args:
            agent_results: Results from all 4 agents
            goal: The planning goal

        Returns:
            ApprovalDecision with user's decision and feedback
        """
        print("\n👤 APPROVAL HANDLER: Requesting human approval...")
        print("=" * 80)

        # Display results from each agent
        self._display_results(agent_results, goal)

        # Get user decision
        decision = self._get_user_decision()

        return decision

    def _display_results(self, agent_results: dict, goal: str):
        """Display agent results to user"""
        print("📋 COORDINATED WORKFLOW RESULTS:")
        print("-" * 50)
        print(f"\n🎯 GOAL: {goal}\n")

        if 'planner' in agent_results:
            planner_result = agent_results['planner']
            print(f"\n🧭 PLANNER AGENT RESULTS:")
            print(f"Success: {'✅' if planner_result.success else '❌'}")
            print(f"Output: {planner_result.output[:300]}...")

        if 'verifier' in agent_results:
            verifier_result = agent_results['verifier']
            print(f"\n✅ VERIFIER AGENT RESULTS:")
            print(f"Success: {'✅' if verifier_result.success else '❌'}")
            print(f"Plan Valid: {'✅ VALID' if verifier_result.metadata.get('is_valid') else '⚠️ INVALID'}")
            print(f"Output: {verifier_result.output[:300]}...")

        if 'executor' in agent_results:
            executor_result = agent_results['executor']
            print(f"\n🛠️ EXECUTOR AGENT RESULTS:")
            print(f"Success: {'✅' if executor_result.success else '❌'}")
            print(f"Deliverables: {executor_result.metadata.get('deliverables_created', 0)}")
            print(f"Output: {executor_result.output[:300]}...")

        if 'generator' in agent_results:
            generator_result = agent_results['generator']
            print(f"\n✍️ GENERATOR AGENT RESULTS:")
            print(f"Success: {'✅' if generator_result.success else '❌'}")
            print(f"Deliverables: {generator_result.metadata.get('deliverables_created', 0)}")
            print(f"Output: {generator_result.output[:300]}...")

        print("-" * 50)

    def _get_user_decision(self) -> ApprovalDecision:
        """Get user's decision"""
        print("\n💡 OPTIONS:")
        print("  y     - Approve and execute coordinated workflow")
        print("  n     - Reject workflow (will learn from this)")
        print("  edit  - Provide corrective feedback")
        print("  quit  - Stop orchestrator")

        while True:
            choice = input("\n👉 Your decision (y/n/edit/quit): ").lower().strip()

            if choice == 'y':
                return ApprovalDecision(
                    approved=True,
                    feedback="",
                    action="approved"
                )
            elif choice == 'n':
                reason = input("📝 Why reject? (helps system learn): ")
                return ApprovalDecision(
                    approved=False,
                    feedback=reason,
                    action="rejected"
                )
            elif choice == 'edit':
                feedback = input("📝 What changes needed?: ")
                return ApprovalDecision(
                    approved=False,
                    feedback=feedback,
                    action="edited"
                )
            elif choice == 'quit':
                print("\n🛑 Orchestrator stopped by user.")
                sys.exit(0)
            else:
                print("❌ Invalid choice. Please enter y, n, edit, or quit.")
