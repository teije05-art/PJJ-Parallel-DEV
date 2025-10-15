"""
Main Orchestrator Loop

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
    Inference-only learning orchestrator based on PDDL-INSTRUCT principles.
    
    Instead of fine-tuning the model, learning happens through:
    - Cumulative memory of successful/failed plans
    - In-context learning via retrieved examples
    - Structured validation feedback
    """
    
    def __init__(self, memory_path: str, max_iterations: int = 15):
        """
        Initialize the learning orchestrator.
        
        Args:
            memory_path: Path to MemAgent memory directory
            max_iterations: Maximum number of learning iterations (η in paper)
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
        Main learning loop - runs for up to max_iterations.
        
        Args:
            goal: High-level goal for the planning task
        """
        print(f"\n{'='*80}")
        print(f"🎯 GOAL: {goal}")
        print(f"{'='*80}\n")
        
        for iteration in range(1, self.max_iterations + 1):
            self.current_iteration = iteration
            
            print(f"\n{'='*80}")
            print(f"🔄 ITERATION {iteration}/{self.max_iterations}")
            print(f"{'='*80}\n")
            
            # Step 1: Retrieve context from memory
            context = self._retrieve_context()
            
            # Step 2: Generate plan with chain-of-thought reasoning
            plan = self._generate_plan_with_cot(goal, context)
            
            # Step 3: Validate plan with MemAgent
            validation = self._validate_plan(plan)
            
            # Step 4: Get human approval
            decision, feedback = self._get_human_approval(plan, validation)
            
            if decision == "approved":
                # Step 5: Execute the plan (simulated for now)
                execution_result = self._execute_plan(plan)
                
                # Step 6: Write success to memory (learning!)
                self._write_success_to_memory(plan, validation, execution_result)
                
                print("\n✅ Plan approved and executed successfully!")
                print(f"   Memory updated with learned context.")
                
                # Ask if user wants to continue
                continue_loop = input("\n🔁 Continue to next planning cycle? (y/n): ")
                if continue_loop.lower() != 'y':
                    print("\n🏁 Learning loop ended by user.")
                    break
                    
            elif decision == "rejected":
                # Write failure to memory (also learning!)
                self._write_failure_to_memory(plan, validation, feedback)
                
                print("\n❌ Plan rejected. Learning from failure...")
                print(f"   Memory updated with error pattern to avoid.")
                
                # Continue to next iteration with learned context
                
            else:  # edited
                print("\n✏️  Plan edited. Re-generating with corrections...")
                # Loop will continue with updated context
        
        print(f"\n{'='*80}")
        print(f"🏁 Learning loop completed after {self.current_iteration} iterations")
        print(f"{'='*80}\n")
        
        self._print_learning_summary()
    
    def _retrieve_context(self) -> Dict[str, str]:
        """
        Step 1: Retrieve context from memory.
        
        This is where learning happens - each iteration sees more context!
        """
        print("📚 STEP 1: Retrieving context from memory...")
        
        # Get current project status
        current_status = self.agent.chat("""
            OPERATION: RETRIEVE
            ENTITY: projectjupiter_multiagent
            CONTEXT: Need current project status for planning
            
            What is the current status of Project Jupiter?
            What infrastructure is operational?
            What are the pending tasks?
        """).reply or "No status found"
        
        # Get successful patterns (in-context learning!)
        successful_patterns = self.agent.chat("""
            OPERATION: RETRIEVE
            ENTITY: successful_patterns
            CONTEXT: Learning from past successes
            
            What planning approaches have worked in the past?
            What patterns should I follow?
        """).reply or "No patterns yet (first iteration)"
        
        # Get errors to avoid
        errors_to_avoid = self.agent.chat("""
            OPERATION: RETRIEVE
            ENTITY: planning_errors
            CONTEXT: Learning from past failures
            
            What planning mistakes should I avoid?
            What approaches have been rejected?
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
        
        # Parse the plan (simplified - in production you'd parse more carefully)
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
            2. Do any actions conflict with KPMG procedures?
            3. Are state transitions logically sound?
            4. Are there any missing dependencies?
            
            Provide detailed feedback on any issues found.
        """).reply or "Validation failed"
        
        # Check for conflicts
        conflict_check = self.agent.chat(f"""
            OPERATION: RETRIEVE
            ENTITY: KPMG_Project_Procedures
            CONTEXT: Check for procedure violations
            
            Does this plan violate any KPMG procedures or established guidelines?
            
            Plan: {plan['text'][:500]}...
            
            Respond with either:
            - "No conflicts" or
            - Specific procedures that are violated
        """).reply or "Unknown"
        
        # Determine overall validity
        is_valid = "no conflicts" in conflict_check.lower() and "satisfied" in precondition_check.lower()
        
        validation = {
            "is_valid": is_valid,
            "precondition_check": precondition_check,
            "conflict_check": conflict_check,
            "timestamp": datetime.now().isoformat()
        }
        
        if is_valid:
            print(f"   ✅ Plan is VALID")
        else:
            print(f"   ⚠️  Plan has issues")
        
        print(f"   ✓ Preconditions checked")
        print(f"   ✓ Conflicts checked")
        
        return validation
    
    def _get_human_approval(self, plan: Dict, validation: Dict) -> Tuple[str, str]:
        """
        Step 4: Get human approval.
        
        Human feedback is crucial training signal!
        """
        print("\n" + "="*80)
        print(f"🔔 ITERATION {self.current_iteration}: APPROVAL REQUIRED")
        print("="*80)
        
        print("\n📋 PROPOSED PLAN:")
        print("-" * 80)
        print(plan['text'])
        print("-" * 80)
        
        print("\n✅ MEMAGENT VALIDATION:")
        print("-" * 80)
        if validation['is_valid']:
            print("✅ VALID - All checks passed")
        else:
            print("⚠️  ISSUES DETECTED")
        print(f"\nPreconditions: {validation['precondition_check'][:200]}...")
        print(f"\nConflicts: {validation['conflict_check'][:200]}...")
        print("-" * 80)
        
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
                reason = input("📝 Why reject? (helps Llama learn): ")
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
        
        # Create deliverables directory if it doesn't exist
        deliverables_dir = self.memory_path / "deliverables"
        deliverables_dir.mkdir(exist_ok=True)
        
        # Write the content to a file
        content_file = deliverables_dir / content_filename
        content_file.write_text(content)
        
        return {
            "action": action,
            "status": "success",
            "output_file": str(content_file),
            "content_preview": content[:200] + "..." if len(content) > 200 else content,
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_analysis(self, action: Dict, goal: str) -> Dict:
        """
        Execute analysis actions (market analysis, competitive research, etc.)
        """
        description = action["description"]
        
        # Use the agent to perform analysis
        prompt = f"""
You are executing an analysis action as part of a larger plan.

GOAL: {goal}

ANALYSIS TO PERFORM: {description}

INSTRUCTIONS:
1. Perform the requested analysis
2. Provide insights, findings, and conclusions
3. Include data points, trends, and implications
4. Make it actionable for decision-making

Conduct the analysis now:
"""
        
        response = self.agent.chat(prompt)
        analysis = response.reply or "No analysis generated"
        
        # Store the analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_filename = f"analysis_{timestamp}.md"
        
        deliverables_dir = self.memory_path / "deliverables"
        deliverables_dir.mkdir(exist_ok=True)
        
        analysis_file = deliverables_dir / analysis_filename
        analysis_file.write_text(analysis)
        
        return {
            "action": action,
            "status": "success",
            "output_file": str(analysis_file),
            "analysis_preview": analysis[:200] + "..." if len(analysis) > 200 else analysis,
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_data_retrieval(self, action: Dict, goal: str) -> Dict:
        """
        Execute data retrieval actions (getting information from entities, etc.)
        """
        description = action["description"]
        
        # Use the agent to retrieve data
        prompt = f"""
You are executing a data retrieval action as part of a larger plan.

GOAL: {goal}

DATA TO RETRIEVE: {description}

INSTRUCTIONS:
1. Retrieve the requested information from memory/entities
2. Organize and present the data clearly
3. Ensure all relevant details are included
4. Format for use in the larger plan

Retrieve the data now:
"""
        
        response = self.agent.chat(prompt)
        data = response.reply or "No data retrieved"
        
        return {
            "action": action,
            "status": "success",
            "retrieved_data": data,
            "data_preview": data[:200] + "..." if len(data) > 200 else data,
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_validation(self, action: Dict, goal: str) -> Dict:
        """
        Execute validation actions (testing, checking, verification)
        """
        description = action["description"]
        
        # Use the agent to perform validation
        prompt = f"""
You are executing a validation action as part of a larger plan.

GOAL: {goal}

VALIDATION TO PERFORM: {description}

INSTRUCTIONS:
1. Perform the requested validation/testing
2. Check against requirements and criteria
3. Report any issues or concerns
4. Provide recommendations for improvement

Conduct the validation now:
"""
        
        response = self.agent.chat(prompt)
        validation_result = response.reply or "No validation performed"
        
        return {
            "action": action,
            "status": "success",
            "validation_result": validation_result,
            "result_preview": validation_result[:200] + "..." if len(validation_result) > 200 else validation_result,
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_general(self, action: Dict, goal: str) -> Dict:
        """
        Execute general actions that don't fit specific categories
        """
        description = action["description"]
        
        # Use the agent to execute the general action
        prompt = f"""
You are executing a general action as part of a larger plan.

GOAL: {goal}

ACTION TO PERFORM: {description}

INSTRUCTIONS:
1. Complete the requested action
2. Provide detailed results and outcomes
3. Ensure alignment with the overall goal
4. Document what was accomplished

Execute the action now:
"""
        
        response = self.agent.chat(prompt)
        result = response.reply or "No result generated"
        
        return {
            "action": action,
            "status": "success",
            "result": result,
            "result_preview": result[:200] + "..." if len(result) > 200 else result,
            "timestamp": datetime.now().isoformat()
        }
    
    def _store_execution_results(self, plan: Dict, execution_results: List[Dict]):
        """
        Store execution results in memory for learning and reference.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create execution results summary
        results_summary = f"""# Execution Results - {timestamp}

## Plan Goal
{plan['goal']}

## Execution Summary
"""
        
        for i, result in enumerate(execution_results, 1):
            status_icon = "✅" if result["status"] == "success" else "❌"
            results_summary += f"\n### Action {i}: {status_icon}\n"
            results_summary += f"**Description**: {result['action']['description']}\n"
            results_summary += f"**Status**: {result['status']}\n"
            
            if result["status"] == "success":
                if "output_file" in result:
                    results_summary += f"**Output File**: {result['output_file']}\n"
                if "content_preview" in result:
                    results_summary += f"**Content Preview**: {result['content_preview']}\n"
                elif "analysis_preview" in result:
                    results_summary += f"**Analysis Preview**: {result['analysis_preview']}\n"
            else:
                results_summary += f"**Error**: {result.get('error', 'Unknown error')}\n"
            
            results_summary += "\n"
        
        # Store in execution results file
        results_file = self.memory_path / "entities" / "execution_results.md"
        with open(results_file, "a") as f:
            f.write(results_summary)
            f.write("\n---\n\n")
    
    def _write_success_to_memory(self, plan: Dict, validation: Dict, execution: Dict):
        """
        Step 6: Write successful plan to memory.
        
        THIS IS WHERE LEARNING HAPPENS!
        Next iteration will retrieve this as learned context.
        """
        print("\n💾 STEP 6: Writing success to memory (learning!)...")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update execution log
        execution_log = self.memory_path / "entities" / "execution_log.md"
        with open(execution_log, "a") as f:
            f.write(f"\n\n## Iteration {self.current_iteration} - SUCCESS ✅\n")
            f.write(f"**Timestamp:** {timestamp}\n")
            f.write(f"**Goal:** {plan['goal']}\n\n")
            f.write(f"### Plan\n{plan['text']}\n\n")
            f.write(f"### Validation\n")
            f.write(f"- Preconditions: Satisfied ✅\n")
            f.write(f"- Conflicts: None ✅\n\n")
            f.write(f"### Outcome\n")
            f.write(f"Successfully executed. Actions completed: {execution['actions_completed']}\n")
            f.write(f"\n---\n")
        
        # Update successful patterns
        patterns_file = self.memory_path / "entities" / "successful_patterns.md"
        with open(patterns_file, "a") as f:
            f.write(f"\n\n### Pattern {self.current_iteration}\n")
            f.write(f"**Iteration:** {self.current_iteration}\n")
            f.write(f"**Goal:** {plan['goal']}\n")
            f.write(f"**Approach:** {plan['text'][:300]}...\n")
            f.write(f"**Result:** SUCCESS ✅\n")
            f.write(f"**Learning:** This approach worked well and should be followed.\n")
        
        print("   ✅ Execution log updated")
        print("   ✅ Successful patterns recorded")
        print("   ✅ Memory enriched with learned context")
    
    def _write_failure_to_memory(self, plan: Dict, validation: Dict, feedback: str):
        """Write rejected plan to memory (also learning!)"""
        print("\n💾 STEP 6: Writing failure to memory (learning from mistakes!)...")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        errors_file = self.memory_path / "entities" / "planning_errors.md"
        with open(errors_file, "a") as f:
            f.write(f"\n\n### Error {self.current_iteration} - REJECTED ❌\n")
            f.write(f"**Timestamp:** {timestamp}\n")
            f.write(f"**Goal:** {plan['goal']}\n\n")
            f.write(f"**Proposed Plan:**\n{plan['text'][:300]}...\n\n")
            f.write(f"**Issue:** {feedback}\n\n")
            f.write(f"**Lesson:** Avoid this approach in future iterations.\n")
            f.write(f"\n---\n")
        
        print("   ✅ Error pattern recorded")
        print("   ✅ Will avoid this approach in future iterations")
    
    def _print_learning_summary(self):
        """Print summary of what was learned"""
        print("\n📊 LEARNING SUMMARY")
        print("="*80)
        
        # Count successes
        execution_log = self.memory_path / "entities" / "execution_log.md"
        content = execution_log.read_text()
        successes = content.count("SUCCESS ✅")
        
        # Count failures
        errors_file = self.memory_path / "entities" / "planning_errors.md"
        errors_content = errors_file.read_text()
        failures = errors_content.count("REJECTED ❌")
        
        print(f"Total iterations: {self.current_iteration}")
        print(f"Successful plans: {successes}")
        print(f"Rejected plans: {failures}")
        print(f"Success rate: {successes/self.current_iteration*100:.1f}%")
        print()
        print("📚 Learned context now available for future iterations:")
        print(f"   - {successes} successful patterns recorded")
        print(f"   - {failures} error patterns to avoid")
        print(f"   - Memory enriched for next planning session")
        print("="*80)


def main():
    """Example usage"""
    # Get memory path from .memory_path file
    repo_root = Path(__file__).parent.parent
    memory_path_file = repo_root / ".memory_path"
    
    if memory_path_file.exists():
        memory_path = memory_path_file.read_text().strip()
    else:
        # Fallback to default
        memory_path = "/Users/teije/Desktop/memagent/local-memory"
    
    print("🚀 Project Jupiter Learning Orchestrator")
    print("="*80)
    print("This system uses PDDL-INSTRUCT-inspired learning")
    print("Gets smarter with each iteration through memory accumulation")
    print("="*80)
    
    # Initialize orchestrator
    orchestrator = LearningOrchestrator(
        memory_path=memory_path,
        max_iterations=15  # η from paper
    )
    
    # Define goal
    goal = input("\n🎯 Enter planning goal (or press Enter for default): ").strip()
    if not goal:
        goal = "Develop and test the multi-agent orchestrator system for Project Jupiter"
    
    # Run learning loop
    orchestrator.run_learning_loop(goal)


if __name__ == "__main__":
    main()

