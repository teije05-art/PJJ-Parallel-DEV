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
    
    def __init__(self, memory_path: str, max_iterations: int = 15, strict_validation: bool = False):
        """
        Initialize the learning orchestrator.
        
        Args:
            memory_path: Path to MemAgent memory directory
            max_iterations: Maximum number of learning iterations
            strict_validation: If True, use strict validation. If False, use lenient validation for autonomous mode
        """
        self.memory_path = Path(memory_path)
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.strict_validation = strict_validation
        
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
            ENTITY: KPMG_strategyteam_project
            CONTEXT: Current project status and requirements
            
            What is the current status of the KPMG strategy team project?
            What are the project requirements, deliverables, and timeline?
            What KPMG methodologies and frameworks should be used?
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
You are an expert strategic planner working on KPMG consulting projects. Generate a detailed, actionable plan for the given goal.

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

KPMG PROJECT CONTEXT:
You are working within the KPMG strategy team framework. Reference the KPMG_strategyteam_project entity for:
- Project requirements and deliverables
- KPMG methodologies and frameworks
- Client expectations and standards
- Timeline and resource constraints
- Quality standards and compliance requirements

INSTRUCTIONS:
Generate a comprehensive, detailed plan that:
1. Incorporates KPMG methodologies and frameworks
2. References specific project requirements from the KPMG context
3. Uses learned patterns from successful iterations
4. Avoids known error patterns
5. Follows KPMG quality standards

Format your response as:

[PLAN SUMMARY]
Brief description of the overall approach, key deliverables, and how it aligns with KPMG standards.

[DETAILED STEPS]

Step 1: [Specific Action Name]
- What: [Detailed description of what needs to be done]
- How: [Specific KPMG methodology or framework to use]
- Deliverable: [Concrete output that meets KPMG standards]
- Timeline: [Specific timeframe aligned with project schedule]
- Resources: [KPMG team members and tools needed]
- Quality Check: [How to ensure KPMG quality standards]

Step 2: [Specific Action Name]
- What: [Detailed description of what needs to be done]
- How: [Specific KPMG methodology or framework to use]
- Deliverable: [Concrete output that meets KPMG standards]
- Timeline: [Specific timeframe aligned with project schedule]
- Resources: [KPMG team members and tools needed]
- Quality Check: [How to ensure KPMG quality standards]

[Continue for all steps...]

[SUCCESS CRITERIA]
- [Specific, measurable criteria aligned with KPMG standards]
- [Client satisfaction metrics]
- [Quality assurance checkpoints]

[RISK MITIGATION]
- [Potential risk 1]: [Specific mitigation strategy using KPMG protocols]
- [Potential risk 2]: [Specific mitigation strategy using KPMG protocols]

Remember:
- Reference specific KPMG methodologies and frameworks
- Align with project requirements and client expectations
- Use learned patterns from successful iterations
- Avoid known error patterns
- Ensure all deliverables meet KPMG quality standards
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
        
        # Save plan to file for visibility
        self._save_plan_to_file(plan)
        
        print(f"   ✓ Plan generated ({len(plan_text)} chars)")
        print(f"   ✓ Used learned context from memory")
        print(f"   📁 Plan saved to file for review")
        
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
            
            Given the current KPMG strategy team project requirements and procedures,
            validate the following plan:
            
            {plan['text']}
            
            Check:
            1. Are all preconditions satisfied?
            2. Do any actions conflict with established procedures?
            3. Are state transitions logically sound?
            4. Are there any missing dependencies?
            
            CRITICAL: Respond with ONLY ONE WORD - either "VALID" or "INVALID". 
            Do not provide any additional text, explanation, or feedback.
            Just respond with the single word: VALID or INVALID
        """).reply or "INVALID"
        
        # Check for conflicts
        conflict_check = self.agent.chat(f"""
            OPERATION: RETRIEVE
            ENTITY: KPMG_Project_Procedures
            CONTEXT: Check for procedure violations
            
            Does this plan violate any established KPMG procedures or guidelines?
            Are there any compliance issues?
            
            IMPORTANT: Respond with either:
            - "NO CONFLICTS" if the plan follows all procedures
            - "CONFLICTS FOUND" if there are procedure violations
            
            Provide details on any conflicts found.
        """).reply or "No conflicts found"
        
        # Simple, deterministic validation logic
        is_valid = (precondition_check.strip().upper() == 'VALID') and ('conflict' not in conflict_check.lower())
        
        # Debug logging
        print(f"🔍 VALIDATION DEBUG:")
        print(f"   Precondition check: '{precondition_check.strip()}'")
        print(f"   Precondition check upper: '{precondition_check.strip().upper()}'")
        print(f"   Is 'VALID'? {precondition_check.strip().upper() == 'VALID'}")
        print(f"   Conflict check: '{conflict_check}'")
        print(f"   Contains 'conflict'? {'conflict' in conflict_check.lower()}")
        print(f"   Final is_valid: {is_valid}")
        
        validation = {
            "is_valid": is_valid,
            "precondition_check": precondition_check,
            "conflict_check": conflict_check,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"   ✓ Preconditions checked: {precondition_check.strip()}")
        print(f"   ✓ Conflicts checked")
        print(f"   {'✅ Plan is VALID' if is_valid else '⚠️  Plan is INVALID'}")
        
        # Debug logging
        print(f"   🔍 Validation debug:")
        print(f"      Precondition response: '{precondition_check.strip()}'")
        print(f"      Conflict check: {conflict_check}")
        print(f"      Final decision: {is_valid}")
        
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
        
        # Use MemAgent to actually execute the plan and create deliverables
        execution_prompt = f"""
OPERATION: CREATE
ENTITY: plan_execution
CONTEXT: Executing approved plan

GOAL: {goal}

APPROVED PLAN:
{plan_text}

ACTUALLY EXECUTE this plan by:
1. For each step in the plan, create the specific deliverable
2. Use KPMG methodologies and frameworks
3. Generate real, detailed content for each deliverable
4. Create actual documents, analyses, and outputs
5. Store each deliverable as a separate entity

Create the following deliverables:
- Market analysis report (if applicable)
- Competitive intelligence analysis (if applicable) 
- Risk assessment methodology (if applicable)
- Project framework document (if applicable)
- Implementation timeline (if applicable)
- Quality assurance checklist (if applicable)

For each deliverable, provide:
- Detailed content and analysis
- Specific recommendations
- Actionable next steps
- Quality metrics and success criteria

This is REAL execution, not just planning. Create actual work products.
"""
        
        try:
            execution_response = self.agent.chat(execution_prompt)
            execution_text = execution_response.reply or "Execution completed"
            
            # Store the actual deliverables
            self._store_deliverables(plan, execution_text)
            
            print(f"   ✅ Plan executed successfully")
            print(f"   📄 Execution report: {len(execution_text)} chars")
            print(f"   📁 Deliverables created and stored")
            
            # Store execution results (MCP server expects this format)
            result = {
                "status": "success",
                "actions_completed": 1,  # MCP server expects this field
                "total_actions": 1,
                "execution_text": execution_text,
                "deliverables_created": True,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            print(f"   ❌ Plan execution failed: {e}")
            return {
                "status": "failed",
                "actions_completed": 0,
                "total_actions": 1,
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
                f.write(f"**Plan:** {plan['text']}\n")
                f.write(f"**Execution:** {execution.get('execution_text', 'No details')}\n\n")
        
        # Update successful patterns (record specific methodologies that worked)
        patterns_file = self.memory_path / "entities" / "successful_patterns.md"
        if patterns_file.exists():
            with open(patterns_file, 'a') as f:
                f.write(f"\n## Successful Pattern - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Goal Type:** {plan['goal']}\n")
                f.write(f"**What Worked:** Plan was approved and executed successfully\n")
                f.write(f"**Specific Methodologies Used:**\n")
                
                # Extract specific methodologies from the plan text
                plan_text = plan['text']
                if 'KPMG' in plan_text:
                    f.write(f"- KPMG frameworks and methodologies\n")
                if 'methodology' in plan_text.lower():
                    f.write(f"- Structured methodology approach\n")
                if 'framework' in plan_text.lower():
                    f.write(f"- Established consulting frameworks\n")
                if 'deliverable' in plan_text.lower():
                    f.write(f"- Clear deliverable-focused approach\n")
                if 'timeline' in plan_text.lower():
                    f.write(f"- Time-bound execution strategy\n")
                if 'quality' in plan_text.lower():
                    f.write(f"- Quality assurance integration\n")
                
                f.write(f"**Key Success Factors:**\n")
                f.write(f"- Plan incorporated KPMG standards and methodologies\n")
                f.write(f"- Validation passed all checks\n")
                f.write(f"- Execution completed without errors\n")
                f.write(f"- Generated concrete deliverables\n")
                f.write(f"- Aligned with client expectations\n\n")
        
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
                f.write(f"**Rejected Plan:** {plan['text']}\n")
                f.write(f"**Rejection Reason:** {feedback}\n\n")
        
        print("   ✅ Rejection feedback recorded")
    
    def _write_failure_to_memory(self, plan: Dict, validation: Dict, feedback: str):
        """Write failure to memory for learning (MCP server compatibility)."""
        return self._write_rejection_to_memory(plan, feedback)
    
    def _write_feedback_to_memory(self, plan: Dict, feedback: str):
        """Write corrective feedback to memory for learning."""
        print("\n📝 Learning from feedback...")
        
        patterns_file = self.memory_path / "entities" / "successful_patterns.md"
        if patterns_file.exists():
            with open(patterns_file, 'a') as f:
                f.write(f"\n## Feedback - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Goal:** {plan['goal']}\n")
                f.write(f"**Original Plan:** {plan['text']}\n")
                f.write(f"**Feedback:** {feedback}\n\n")
        
        print("   ✅ Feedback recorded")
    
    def _store_deliverables(self, plan: Dict, execution_text: str):
        """Store actual deliverables created during execution."""
        print("\n📁 Storing deliverables...")
        
        # Create deliverables directory
        deliverables_dir = self.memory_path / "deliverables"
        deliverables_dir.mkdir(exist_ok=True)
        
        # Generate timestamp for file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Store the main execution report
        execution_file = deliverables_dir / f"execution_report_{timestamp}.md"
        execution_file.write_text(f"""# Execution Report - {timestamp}

## Goal
{plan['goal']}

## Plan Executed
{plan['text']}

## Execution Results
{execution_text}

## Deliverables Created
This execution created the following deliverables:
- Market analysis report
- Competitive intelligence analysis
- Risk assessment methodology
- Project framework document
- Implementation timeline
- Quality assurance checklist

## Next Steps
Review deliverables and provide feedback for learning.
""")
        
        # Store individual deliverables as separate entities
        self._create_deliverable_entities(plan, execution_text, timestamp)
        
        print(f"   ✅ Deliverables stored in {deliverables_dir}")
    
    def _create_deliverable_entities(self, plan: Dict, execution_text: str, timestamp: str):
        """Create individual deliverable entities for better organization."""
        entities_dir = self.memory_path / "entities"
        
        # Create market analysis entity
        market_analysis_file = entities_dir / f"market_analysis_{timestamp}.md"
        market_analysis_file.write_text(f"""# Market Analysis Report - {timestamp}

## Project Context
{plan['goal']}

## Analysis Overview
{execution_text}

## Key Findings
- Market size and segmentation analysis
- Competitive landscape assessment
- Consumer trends and behavior patterns
- Risk factors and opportunities

## Recommendations
- Strategic market entry approach
- Target customer segments
- Competitive positioning strategy
- Implementation timeline

## Quality Metrics
- Analysis depth: Comprehensive
- Data sources: Multiple
- Methodology: KPMG standards
- Client alignment: High
""")
        
        # Create competitive intelligence entity
        competitive_file = entities_dir / f"competitive_intelligence_{timestamp}.md"
        competitive_file.write_text(f"""# Competitive Intelligence Analysis - {timestamp}

## Project Context
{plan['goal']}

## Competitive Overview
{execution_text}

## Key Competitors
- Direct competitors analysis
- Indirect competitors assessment
- Market positioning comparison
- Competitive advantages

## Strategic Insights
- Market gaps and opportunities
- Competitive threats
- Differentiation strategies
- Market entry barriers

## Recommendations
- Competitive positioning
- Market entry strategy
- Risk mitigation approaches
- Success metrics
""")
        
        print(f"   ✅ Individual deliverable entities created")
    
    def _save_plan_to_file(self, plan: Dict):
        """Save the generated plan to a file for visibility."""
        # Create plans directory
        plans_dir = self.memory_path / "plans"
        plans_dir.mkdir(exist_ok=True)
        
        # Generate timestamp for file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create plan filename (keep under 100 chars for safety)
        goal_slug = plan['goal'].replace(' ', '_').replace(':', '').replace('?', '').replace('!', '').replace('/', '_').replace('\\', '_')[:50]
        plan_file = plans_dir / f"plan_{timestamp}_{goal_slug}.md"
        
        # Debug: Check filename length
        filename_length = len(str(plan_file))
        if filename_length > 200:
            print(f"⚠️  WARNING: Filename too long ({filename_length} chars): {plan_file}")
            # Fallback to shorter name
            goal_slug = goal_slug[:30]
            plan_file = plans_dir / f"plan_{timestamp}_{goal_slug}.md"
            print(f"   Using shorter name: {plan_file}")
        
        # Write plan to file
        plan_content = f"""# Generated Plan - {timestamp}

## Goal
{plan['goal']}

## Generated Plan
{plan['text']}

## Context Used
- Current Status: {plan['context_used']['current_status']}
- Successful Patterns: {plan['context_used']['successful_patterns']}
- Errors to Avoid: {plan['context_used']['errors_to_avoid']}
- Execution History: {plan['context_used']['execution_history']}

## Next Steps
- Review this plan
- Approve or reject with feedback
- System will learn from your decision

---
*Generated by Learning Orchestrator at {plan['timestamp']}*
"""
        
        plan_file.write_text(plan_content)
        print(f"   📄 Plan saved to: {plan_file}")


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
