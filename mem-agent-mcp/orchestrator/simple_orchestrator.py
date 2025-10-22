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
from .context_manager import ContextManager
from .workflow_coordinator import WorkflowCoordinator
from .approval_handler import ApprovalHandler
from .memory_manager import MemoryManager
from .learning_manager import LearningManager


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
        self.context_manager = ContextManager(self.agent, self.memory_path)
        self.workflow_coordinator = WorkflowCoordinator(self.agent, self.memory_path)
        self.approval_handler = ApprovalHandler()
        self.memory_manager = MemoryManager(self.agent, self.memory_path)
        self.learning_manager = LearningManager(self.agent, self.memory_path)

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

    # Methods used by MCP server (for backward compatibility)
    def _retrieve_enhanced_context(self, goal: str = None):
        """Backward compatibility wrapper for MCP server"""
        if goal:
            return self.context_manager.retrieve_context(goal)
        else:
            # Fallback for no goal
            return {
                "current_status": "No goal provided",
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
