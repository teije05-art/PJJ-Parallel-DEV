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
from .agents import AgentResult


@dataclass
class ApprovalDecision:
    """Standard format for approval decisions"""
    approved: bool
    feedback: str
    action: str  # 'approved', 'rejected', 'edited', 'quit'


class ApprovalHandler:
    """Handles human approval workflow with LLM-based summarization"""

    def __init__(self, agent=None):
        """
        Initialize approval handler

        Args:
            agent: Optional Agent instance for generating summaries.
                   If not provided, will attempt to create one.
        """
        self.agent = agent

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

        # DEFERRED: Summary generation moved to post-success async call
        # This avoids extra LLM calls in the critical path
        # After approval, call generate_approval_summary_async() if needed

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

    def _generate_approval_summary(self, agent_results: dict, goal: str) -> str:
        """
        Generate an executive summary of the workflow results.

        This helps the human approver understand the plan quickly without
        reading through all the detailed outputs.

        Args:
            agent_results: Results from all 4 agents
            goal: The planning goal

        Returns:
            Concise executive summary (3-4 sentences)
        """
        try:
            # Prepare full outputs
            planner_output = agent_results.get('planner', type('obj', (), {'output': 'Not available'})()).output or 'Not available'
            verifier_output = agent_results.get('verifier', type('obj', (), {'output': 'Not available'})()).output or 'Not available'
            executor_output = agent_results.get('executor', type('obj', (), {'output': 'Not available'})()).output or 'Not available'

            # Verify validity
            verifier_valid = agent_results.get('verifier', type('obj', (), {'metadata': {}}))().metadata.get('is_valid', False)

            # Create summarization prompt
            summary_prompt = f"""You are creating an executive summary for a decision-maker who needs to quickly understand a strategic plan.

GOAL: {goal}

STRATEGIC PLAN (from Planner Agent):
{planner_output[:2000]}

VERIFICATION RESULTS (from Verifier Agent):
{verifier_output[:1000]}

EXECUTION RESULTS (from Executor Agent):
{executor_output[:1000]}

PLAN VALIDITY: {'VALID' if verifier_valid else 'INVALID'}

Create a concise executive summary (3-4 sentences) that answers:
1. What is this plan trying to accomplish?
2. Does the plan appear sound and complete?
3. What are the key risks or concerns?
4. Should this plan be approved?

Keep the summary clear, professional, and actionable.
Highlight any red flags that would prevent approval."""

            # Get summary from agent
            agent = self._get_agent_for_summary()
            if not agent:
                return "Unable to generate summary - agent not available"

            response = agent.chat(summary_prompt)
            summary = response.reply or "Unable to generate summary"

            # Ensure summary is reasonable length
            if len(summary) > 1000:
                summary = summary[:1000] + "..."

            if len(summary) < 50:
                # If summary is too short, generate a default one
                return f"Plan Status: {'Valid and ready for approval' if verifier_valid else 'Invalid - needs revision'}"

            return summary

        except Exception as e:
            print(f"   ⚠️ Summary generation failed: {e}")
            return "Unable to generate summary"

    def _get_agent_for_summary(self):
        """
        Get the agent instance for summary generation.

        This method supports both:
        - Standalone ApprovalHandler (may not have agent access)
        - ApprovalHandler within SimpleOrchestrator (has shared agent)

        Returns:
            Agent instance if available, None otherwise
        """
        if hasattr(self, 'agent') and self.agent:
            return self.agent

        # Fallback: try to create a temporary agent for summary
        try:
            from agent import Agent
            return Agent(use_fireworks=True, predetermined_memory_path=False)
        except Exception:
            # If agent creation fails, return None
            return None
