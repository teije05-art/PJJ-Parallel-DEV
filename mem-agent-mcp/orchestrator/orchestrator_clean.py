"""
Clean Learning Orchestrator

Implements PDDL-INSTRUCT-style learning through:
1. Chain-of-thought plan generation
2. Step-by-step validation
3. Human approval workflow
4. Memory accumulation for learning
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent


class LearningOrchestrator:
    """
    Clean learning orchestrator based on PDDL-INSTRUCT principles.
    
    Learning happens through:
    - Cumulative memory of successful/failed plans
    - In-context learning via retrieved examples
    - Structured validation feedback
    """
    
    def __init__(self, memory_path: str, max_iterations: int = 15):
        """
        Initialize the learning orchestrator.
        
        Args:
            memory_path: Path to MemAgent memory directory
            max_iterations: Maximum number of learning iterations
        """
        self.memory_path = Path(memory_path)
        self.max_iterations = max_iterations
        self.current_iteration = 0
        
        # Initialize agent with backend auto-detection
        use_fireworks = sys.platform == "darwin"  # Mac uses Fireworks
        use_vllm = sys.platform == "linux"        # H100 uses vLLM
        
        self.agent = Agent(
            use_fireworks=use_fireworks,
            use_vllm=use_vllm,
            memory_path=str(memory_path),
            predetermined_memory_path=False
        )
        
        # Ensure memory entities exist
        self._initialize_memory_entities()
        
        print(f"🚀 Learning Orchestrator initialized")
        print(f"   Backend: {'Fireworks (Mac)' if use_fireworks else 'vLLM (H100)'}")
        print(f"   Memory: {memory_path}")
        print(f"   Max iterations: {max_iterations}")
    
    def _initialize_memory_entities(self):
        """Create memory entity files if they don't exist"""
        entities_dir = self.memory_path / "entities"
        entities_dir.mkdir(parents=True, exist_ok=True)
        
        # Execution log for successful plans
        execution_log = entities_dir / "execution_log.md"
        if not execution_log.exists():
            execution_log.write_text(
                "# Execution Log\n\n"
                "This file tracks all approved and executed plans.\n"
                "Each successful iteration adds learned context.\n\n"
            )
        
        # Successful patterns
        patterns_file = entities_dir / "successful_patterns.md"
        if not patterns_file.exists():
            patterns_file.write_text(
                "# Successful Planning Patterns\n\n"
                "This file tracks proven approaches that work.\n"
                "Used for in-context learning.\n\n"
            )
        
        # Planning errors to avoid
        errors_file = entities_dir / "planning_errors.md"
        if not errors_file.exists():
            errors_file.write_text(
                "# Planning Errors to Avoid\n\n"
                "This file tracks rejected plans and common mistakes.\n"
                "Used to avoid repeating failures.\n\n"
            )
    
    def run_learning_loop(self, goal: str):
        """
        Main learning loop - the core PDDL-INSTRUCT process.
        
        This implements the iterative learning approach from the paper.
        """
        print(f"\n🎯 STARTING LEARNING LOOP")
        print(f"Goal: {goal}")
        print(f"Max iterations: {self.max_iterations}")
        print("=" * 60)
        
        for iteration in range(1, self.max_iterations + 1):
            self.current_iteration = iteration
            print(f"\n🔄 ITERATION {iteration}/{self.max_iterations}")
            print("-" * 40)
            
            try:
                # Step 1: Retrieve context (in-context learning!)
                context = self._retrieve_context()
                
                # Step 2: Generate plan with learned context
                plan = self._generate_plan_with_cot(goal, context)
                
                # Step 3: Validate plan
                validation = self._validate_plan(plan)
                
                # Step 4: Human approval
                approval, feedback = self._get_human_approval(plan)
                
                if approval == "approved":
                    # Step 5: Execute approved plan
                    execution = self._execute_plan(plan)
                    
                    # Step 6: Learn from success
                    self._write_success_to_memory(plan, validation, execution)
                    
                    print(f"\n🎉 SUCCESS! Plan approved and executed.")
                    print(f"Learning iteration {iteration} completed successfully.")
                    return True
                    
                elif approval == "rejected":
                    # Learn from rejection
                    self._write_rejection_to_memory(plan, feedback)
                    print(f"\n📚 Learning from rejection: {feedback}")
                    
                elif approval == "edited":
                    # Learn from feedback
                    self._write_feedback_to_memory(plan, feedback)
                    print(f"\n📝 Learning from feedback: {feedback}")
                    
            except KeyboardInterrupt:
                print(f"\n🛑 Learning loop interrupted by user.")
                return False
            except Exception as e:
                print(f"\n❌ Error in iteration {iteration}: {e}")
                continue
        
        print(f"\n⚠️ Learning loop completed without approval.")
        print(f"Consider refining the goal or providing more specific feedback.")
        return False
    
    def _retrieve_context(self) -> Dict[str, str]:
        """
        Step 1: Retrieve learned context from memory.
        
        This is the in-context learning part of PDDL-INSTRUCT.
        """
        print("\n📚 STEP 1: Retrieving context from memory...")
        
        # Get current project status
        current_status = self.agent.chat("""
            OPERATION: RETRIEVE
            ENTITY: project_jupiter
            CONTEXT: Current project status
            
            What is the current status of Project Jupiter?
            What infrastructure and capabilities are available?
        """).reply or "No current status available"
        
        # Get successful patterns
        successful_patterns = self.agent.chat("""
            OPERATION: RETRIEVE
            ENTITY: successful_patterns
            CONTEXT: Review successful planning approaches
            
            What planning patterns have worked well?
            What approaches led to successful plan approvals?
        """).reply or "No successful patterns yet (first iteration)"
        
        # Get errors to avoid
        errors_to_avoid = self.agent.chat("""
            OPERATION: RETRIEVE
            ENTITY: planning_errors
            CONTEXT: Review planning mistakes
            
            What planning approaches have been rejected?
            What common mistakes should be avoided?
        """).reply or "No errors yet (no failures)"
        
        # Get execution history
        execution_history = self.agent.chat("""
            OPERATION: RETRIEVE
            ENTITY: execution_log
            CONTEXT: Review past iterations
            
            What actions have been successfully executed?
            How many iterations have completed?
        """).reply or "No history yet (first iteration)"
        
        context = {
            "current_status": current_status,
            "successful_patterns": successful_patterns,
            "errors_to_avoid": errors_to_avoid,
            "execution_history": execution_history
        }
        
        print(f"   ✓ Current status retrieved")
        print(f"   ✓ Successful patterns: {len(successful_patterns)} chars")
        print(f"   ✓ Errors to avoid: {len(errors_to_avoid)} chars")
        print(f"   ✓ Execution history: {len(execution_history)} chars")
        
        return context
    
    def _generate_plan_with_cot(self, goal: str, context: Dict[str, str]) -> Dict:
        """
        Step 2: Generate plan using chain-of-thought reasoning.
        
        This follows the PDDL-INSTRUCT approach of explicit state-action-state reasoning.
        """
        print("\n🧠 STEP 2: Generating plan with chain-of-thought reasoning...")
        
        # Construct prompt with learned context (in-context learning!)
        prompt = f"""
You are an expert strategic planner. Generate a detailed, actionable plan for the given goal.

GOAL: {goal}

LEARNED CONTEXT (from previous iterations):

CURRENT PROJECT STATUS:
{context['current_status']}

SUCCESSFUL PATTERNS TO FOLLOW:
{context['successful_patterns']}

ERRORS TO AVOID:
{context['errors_to_avoid']}

EXECUTION HISTORY:
{context['execution_history']}

INSTRUCTIONS:
Generate a comprehensive, detailed plan with specific, actionable steps. Each step should be concrete and executable.

Format your response as:

[PLAN SUMMARY]
Brief description of the overall approach and key deliverables.

[DETAILED STEPS]

Step 1: [Specific Action Name]
- What: [Detailed description of what needs to be done]
- How: [Specific methodology or approach]
- Deliverable: [Concrete output or result]
- Timeline: [Specific timeframe]
- Resources: [What's needed to execute]

Step 2: [Specific Action Name]
- What: [Detailed description of what needs to be done]
- How: [Specific methodology or approach]
- Deliverable: [Concrete output or result]
- Timeline: [Specific timeframe]
- Resources: [What's needed to execute]

[Continue for all steps...]

[SUCCESS CRITERIA]
- [Specific, measurable criteria 1]
- [Specific, measurable criteria 2]
- [Specific, measurable criteria 3]

[RISK MITIGATION]
- [Potential risk 1]: [Specific mitigation strategy]
- [Potential risk 2]: [Specific mitigation strategy]

Remember:
- Be specific and actionable, not generic
- Include concrete deliverables and timelines
- Use learned patterns from successful iterations
- Avoid known error patterns
- Focus on what will actually be accomplished
"""
        
        response = self.agent.chat(prompt)
        plan_text = response.reply or ""
        
        # Parse the plan
        plan = {
            "text": plan_text,
            "goal": goal,
            "context_used": context,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"   ✓ Plan generated ({len(plan_text)} chars)")
        print(f"   ✓ Used learned context from memory")
        
        return plan
    
    def _validate_plan(self, plan: Dict) -> Dict:
        """
        Step 3: Validate plan using MemAgent.
        
        MemAgent acts like VAL in the paper - checking preconditions and state transitions.
        """
        print("\n✅ STEP 3: Validating plan with MemAgent...")
        
        # Validate preconditions
        precondition_check = self.agent.chat(f"""
            OPERATION: RETRIEVE
            CONTEXT: Validating plan preconditions
            
            Given the current Project Jupiter infrastructure and procedures,
            validate the following plan:
            
            {plan['text']}
            
            Check:
            1. Are all preconditions satisfied?
            2. Do any actions conflict with established procedures?
            3. Are state transitions logically sound?
            4. Are there any missing dependencies?
            
            Provide detailed feedback on any issues found.
        """).reply or "Validation failed"
        
        # Check for conflicts
        conflict_check = self.agent.chat(f"""
            OPERATION: RETRIEVE
            ENTITY: KPMG_Project_Procedures
            CONTEXT: Check for procedure violations
            
            Does this plan violate any established procedures or guidelines?
            Are there any compliance issues?
        """).reply or "No conflicts found"
        
        # Determine if plan is valid
        is_valid = "valid" in precondition_check.lower() and "conflict" not in conflict_check.lower()
        
        validation = {
            "is_valid": is_valid,
            "precondition_check": precondition_check,
            "conflict_check": conflict_check,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"   ✓ Preconditions checked")
        print(f"   ✓ Conflicts checked")
        print(f"   {'✅ Plan is VALID' if is_valid else '⚠️  Plan has issues'}")
        
        return validation
    
    def _get_human_approval(self, plan: Dict) -> Tuple[str, str]:
        """
        Step 4: Get human approval for the plan.
        
        This is the human-in-the-loop part of PDDL-INSTRUCT.
        """
        print("\n👤 STEP 4: Human approval required")
        print("=" * 50)
        print("📋 GENERATED PLAN:")
        print("-" * 30)
        print(plan['text'])
        print("-" * 30)
        
        print("\n💡 OPTIONS:")
        print("  y     - Approve and execute plan")
        print("  n     - Reject plan (will learn from this)")
        print("  edit  - Provide corrective feedback")
        print("  quit  - Stop orchestrator")
        
        while True:
            choice = input("\n👉 Your decision (y/n/edit/quit): ").lower().strip()
            
            if choice == 'y':
                return "approved", ""
            elif choice == 'n':
                reason = input("📝 Why reject? (helps system learn): ")
                return "rejected", reason
            elif choice == 'edit':
                feedback = input("📝 What changes needed?: ")
                return "edited", feedback
            elif choice == 'quit':
                print("\n🛑 Orchestrator stopped by user.")
                sys.exit(0)
            else:
                print("❌ Invalid choice. Please enter y, n, edit, or quit.")
    
    def _execute_plan(self, plan: Dict) -> Dict:
        """
        Step 5: Execute the approved plan using MemAgent.
        
        Uses MemAgent to execute the plan and create deliverables.
        """
        print("\n⚙️  STEP 5: Executing plan with MemAgent...")
        
        plan_text = plan['text']
        goal = plan['goal']
        
        # Use MemAgent to execute the plan
        execution_prompt = f"""
OPERATION: CREATE
ENTITY: plan_execution
CONTEXT: Executing approved plan

GOAL: {goal}

APPROVED PLAN:
{plan_text}

Execute this plan by:
1. Breaking down each step into specific actions
2. Creating detailed deliverables for each step
3. Documenting the execution process
4. Recording any insights or learnings

Provide a comprehensive execution report with specific deliverables and outcomes.
"""
        
        try:
            execution_response = self.agent.chat(execution_prompt)
            execution_text = execution_response.reply or "Execution completed"
            
            print(f"   ✅ Plan executed successfully")
            print(f"   📄 Execution report: {len(execution_text)} chars")
            
            # Store execution results
            result = {
                "status": "success",
                "execution_text": execution_text,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            print(f"   ❌ Plan execution failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _write_success_to_memory(self, plan: Dict, validation: Dict, execution: Dict):
        """
        Step 6: Write successful execution to memory for learning.
        
        This is where the PDDL-INSTRUCT learning happens - storing successful patterns.
        """
        print("\n💾 STEP 6: Writing success to memory (learning!)...")
        
        # Update execution log
        execution_log = self.memory_path / "entities" / "execution_log.md"
        if execution_log.exists():
            with open(execution_log, 'a') as f:
                f.write(f"\n## Execution {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Goal:** {plan['goal']}\n")
                f.write(f"**Status:** {execution['status']}\n")
                f.write(f"**Plan:** {plan['text'][:200]}...\n")
                f.write(f"**Execution:** {execution.get('execution_text', 'No details')[:200]}...\n\n")
        
        # Update successful patterns
        patterns_file = self.memory_path / "entities" / "successful_patterns.md"
        if patterns_file.exists():
            with open(patterns_file, 'a') as f:
                f.write(f"\n## Successful Pattern - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Goal Type:** {plan['goal'][:50]}...\n")
                f.write(f"**Successful Approach:** {plan['text'][:300]}...\n\n")
        
        print("   ✅ Execution log updated")
        print("   ✅ Successful patterns recorded")
        print("   ✅ Memory enriched with learned context")
    
    def _write_rejection_to_memory(self, plan: Dict, feedback: str):
        """Write rejection feedback to memory for learning."""
        print("\n📚 Learning from rejection...")
        
        errors_file = self.memory_path / "entities" / "planning_errors.md"
        if errors_file.exists():
            with open(errors_file, 'a') as f:
                f.write(f"\n## Rejection - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Goal:** {plan['goal']}\n")
                f.write(f"**Rejected Plan:** {plan['text'][:200]}...\n")
                f.write(f"**Rejection Reason:** {feedback}\n\n")
        
        print("   ✅ Rejection feedback recorded")
    
    def _write_feedback_to_memory(self, plan: Dict, feedback: str):
        """Write corrective feedback to memory for learning."""
        print("\n📝 Learning from feedback...")
        
        patterns_file = self.memory_path / "entities" / "successful_patterns.md"
        if patterns_file.exists():
            with open(patterns_file, 'a') as f:
                f.write(f"\n## Feedback - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Goal:** {plan['goal']}\n")
                f.write(f"**Original Plan:** {plan['text'][:200]}...\n")
                f.write(f"**Feedback:** {feedback}\n\n")
        
        print("   ✅ Feedback recorded")


# Example usage
if __name__ == "__main__":
    # Initialize orchestrator
    memory_path = "/Users/teije/Desktop/memagent/local-memory"
    orchestrator = LearningOrchestrator(memory_path=memory_path, max_iterations=5)
    
    # Run learning loop
    goal = "Develop a comprehensive market entry strategy for a tech company"
    success = orchestrator.run_learning_loop(goal)
    
    if success:
        print("\n🎉 Learning loop completed successfully!")
    else:
        print("\n⚠️ Learning loop completed without approval.")
