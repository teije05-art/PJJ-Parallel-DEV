import os
import sys
import socket
import asyncio
from typing import Optional

from fastmcp import FastMCP, Context

# Ensure repository root is on sys.path so we can import the `agent` package
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

FILTERS_PATH = os.path.join(REPO_ROOT, ".filters")

from agent import Agent
try:
    from mcp_server.settings import MEMORY_AGENT_NAME
    from mcp_server.settings import MLX_4BIT_MEMORY_AGENT_NAME
except Exception:
    # Fallback when executed as a script from inside the package directory
    from settings import MEMORY_AGENT_NAME
    MLX_4BIT_MEMORY_AGENT_NAME = "mem-agent-mlx@4bit"

# Import orchestrator for planning tools
try:
    from orchestrator.orchestrator import LearningOrchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False
    print("Warning: Orchestrator not available. Planning tools will be disabled.", file=sys.stderr)

# Initialize FastMCP (the installed version doesn't accept a timeout kwarg)
mcp = FastMCP("memory-agent-server")

# Global state for orchestrator (persists between tool calls)
_orchestrator_state = {
    "orchestrator": None,
    "current_plan": None,
    "current_validation": None,
    "current_iteration": 0,
    "autonomous_mode": False,
    "autonomous_target": 0,
    "autonomous_goal": None,  # Store the goal for resuming
    "checkpoint_interval": 5,  # Ask for approval every N iterations
    "auto_approve_confidence_threshold": 0.8  # Auto-approve if validation is very confident
}

def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _read_memory_path() -> str:
    """
    Read the absolute memory directory path from .memory_path at repo root.
    If invalid or missing, fall back to repo_root/memory/mcp-server and warn.
    """
    repo_root = _repo_root()
    default_path = os.path.join(repo_root, "memory", "mcp-server")
    memory_path_file = os.path.join(repo_root, ".memory_path")

    try:
        if os.path.exists(memory_path_file):
            with open(memory_path_file, "r") as f:
                raw = f.read().strip()
            raw = os.path.expanduser(os.path.expandvars(raw))
            if not os.path.isabs(raw):
                raw = os.path.abspath(os.path.join(repo_root, raw))
            if os.path.isdir(raw):
                return raw
            else:
                print(
                    f"Warning: Path in .memory_path is not a directory: {raw}.\n"
                    f"Falling back to default: {default_path}",
                    file=sys.stderr,
                )
        else:
            print(
                ".memory_path not found. Run 'make setup' or 'make setup-cli'.\n"
                f"Falling back to default: {default_path}",
                file=sys.stderr,
            )
    except Exception as exc:
        print(
            f"Warning: Failed to read .memory_path: {type(exc).__name__}: {exc}.\n"
            f"Falling back to default: {default_path}",
            file=sys.stderr,
        )

    # Ensure fallback exists
    try:
        os.makedirs(default_path, exist_ok=True)
    except Exception:
        pass
    return os.path.abspath(default_path)


# Initialize the agent
IS_DARWIN = sys.platform == "darwin"

def _read_mlx_model_name(default_model: str) -> str:
    """
    Read the MLX model name from .mlx_model_name at repo root.
    Falls back to the provided default when missing/invalid.
    """
    repo_root = _repo_root()
    model_file = os.path.join(repo_root, ".mlx_model_name")
    try:
        if os.path.exists(model_file):
            with open(model_file, "r") as f:
                raw = f.read().strip()
            # Strip surrounding quotes if present
            if raw.startswith("\"") and raw.endswith("\"") and len(raw) >= 2:
                raw = raw[1:-1]
            if raw.startswith("'") and raw.endswith("'") and len(raw) >= 2:
                raw = raw[1:-1]
            if raw:
                return raw
    except Exception:
        pass
    return default_model

def _read_filters() -> str:
    """
    Read the filters from .filters at repo root.
    """
    try:
        with open(FILTERS_PATH, "r") as f:
            return f.read().strip()
    except Exception:
        return ""

@mcp.tool
async def use_memory_agent(question: str, ctx: Context) -> str:
    """
    Provide the local memory agent with structured queries for long-term information storage and retrieval across conversations.

    **IMPORTANT: DO NOT use this tool for planning goals or autonomous planning workflows.**
    **This tool is for general memory operations only, not for the orchestrator planning system.**
    **The orchestrator handles its own entity lookups automatically.**

    **Query Structure:**
    Format queries with clear operations and entity identifiers:

    OPERATION: [CREATE | UPDATE | RETRIEVE | DELETE]
    ENTITY: [specific_entity_name_in_snake_case]
    CONTEXT: [brief description of what this entity stores]
    CONTENT: [the actual information to store/retrieve]

    **Guidelines:**
    1. Always maintain consistent entity naming - once an entity is created, use the exact same name
    2. For project tracking, use descriptive entity names like "ProjectName_Component_Type"
    3. When updating, preserve existing information unless explicitly told to replace
    4. Add relevant context from the conversation to make queries self-contained
    5. For retrieval, specify exactly which entity to query

    **Examples:**

    User: "I'm switching to VastAI B200 GPUs, keep track of this"
    Query to agent:
    OPERATION: CREATE
    ENTITY: VastAI_B200_Migration_Status
    CONTEXT: Tracks progress of migrating GPU infrastructure to VastAI B200 instances
    CONTENT: User has initiated migration to VastAI B200 GPU instances. Migration started [date].

    User: "I've completed the SSH setup"
    Query to agent:
    OPERATION: UPDATE
    ENTITY: VastAI_B200_Migration_Status
    CONTEXT: Adding completed step to migration progress
    CONTENT: SSH setup completed. [Add to existing progress log]

    User: "What's my progress on the VastAI migration?"
    Query to agent:
    OPERATION: RETRIEVE
    ENTITY: VastAI_B200_Migration_Status
    CONTEXT: User wants to see current migration progress

    **Entity Naming Conventions:**
    - Projects: ProjectName_Status, ProjectName_Steps, ProjectName_Issues
    - Documentation: Topic_Guide, Topic_Reference, Topic_Examples
    - Progress tracking: Task_Progress, Task_Blockers, Task_Completed
    - Technical setup: Service_Configuration, Service_Credentials, Service_Setup_Steps

    **Error Handling:**
    - If entity name is ambiguous, ask user to clarify before proceeding
    - If operation type is unclear, default to RETRIEVE and ask for confirmation
    - If updating a non-existent entity, suggest creating it first

    **Context Preservation:**
    - Always include relevant conversation context in the CONTEXT field
    - Reference previous entities when creating related ones
    - Maintain conversation thread continuity in entity names

    **Query Validation:**
    Before sending to memory agent, ensure:
    - Operation type is explicitly stated
    - Entity name follows naming conventions
    - Context provides sufficient background
    - Content is specific and actionable

    **Common Scenarios:**

    User: "I'm stuck on this problem"
    Query to agent:
    OPERATION: CREATE
    ENTITY: Current_Issue_Blocking_Progress
    CONTEXT: User encountering blocker in current work
    CONTENT: [Specific problem description and current status]

    User: "Remember this for later"
    Query to agent:
    OPERATION: CREATE
    ENTITY: [Infer from context]_Reference_Note
    CONTEXT: User wants to save information for future reference
    CONTENT: [The information to remember]

    Args:
        question: The structured query to be processed by the agent.

    Returns:
        The response from the agent.
    """
    try:
        agent = Agent(
            use_fireworks=True,
            use_vllm=False,
            predetermined_memory_path=False,
            memory_path=_read_memory_path(),
        )

        filters = _read_filters()

        if len(filters) > 0:
            question = question + "\n\n" + "<filter>" + filters + "</filter>"

        loop = asyncio.get_running_loop()
        fut = loop.run_in_executor(None, agent.chat, question)

        # heartbeat loop: indeterminate progress
        while not fut.done():
            await ctx.report_progress(progress=1)   # no total -> indeterminate
            await asyncio.sleep(2)

        result = await fut
        await ctx.report_progress(progress=1, total=1)  # 100%
        return (result.reply or "").strip()
    except Exception as exc:
        return f"agent_error: {type(exc).__name__}: {exc}"


# ============================================================================
# ORCHESTRATOR TOOLS (For conversational planning approval in Claude)
# ============================================================================

def _ensure_orchestrator():
    """Initialize orchestrator if not already done"""
    if not ORCHESTRATOR_AVAILABLE:
        return None
    
    if _orchestrator_state["orchestrator"] is None:
        memory_path = _read_memory_path()
        # Use lenient validation for autonomous mode by default
        _orchestrator_state["orchestrator"] = LearningOrchestrator(
            memory_path=memory_path,
            max_iterations=15,
            strict_validation=False  # Lenient validation for autonomous mode
        )
    return _orchestrator_state["orchestrator"]

def _reset_orchestrator():
    """Reset orchestrator to ensure fresh instance with updated code"""
    if ORCHESTRATOR_AVAILABLE:
        _orchestrator_state["orchestrator"] = None
        print("🔄 Orchestrator reset - will create fresh instance with updated validation logic")


@mcp.tool()
async def start_planning_iteration(goal: str, ctx: Context) -> str:
    """
    Start a new planning iteration with chain-of-thought reasoning.
    
    This tool initiates the PDDL-INSTRUCT-style learning loop:
    1. Retrieves learned context from memory
    2. Generates plan with explicit state-action-state reasoning
    3. Validates plan against project requirements
    4. Presents plan for user approval
    
    CRITICAL: The goal parameter is a plain text string that should be passed directly to the orchestrator.
    DO NOT use use_memory_agent to create entity lookups from words in the goal.
    DO NOT split the goal into tokens or try to find matching entities.
    The orchestrator will handle all memory operations internally.
    Simply pass the goal string as-is to the orchestrator.
    
    Use this to begin planning for any strategic goal.
    After reviewing the plan, use approve_current_plan() or reject_current_plan().
    
    Args:
        goal: The planning goal (e.g., "Deploy orchestrator to H100 instance")
    
    Returns:
        Formatted plan with reasoning, validation results, and approval instructions
    """
    try:
        orchestrator = _ensure_orchestrator()
        if not orchestrator:
            return "❌ Orchestrator not available. Make sure orchestrator module is installed."
        
        await ctx.report_progress(progress=1, total=5)
        
        # Step 1: Retrieve context
        context = orchestrator._retrieve_context()
        await ctx.report_progress(progress=2, total=5)
        
        # Step 2: Generate plan with CoT
        plan = orchestrator._generate_plan_with_cot(goal, context)
        await ctx.report_progress(progress=3, total=5)
        
        # Step 3: Validate
        validation = orchestrator._validate_plan(plan)
        await ctx.report_progress(progress=4, total=5)
        
        # Store in global state
        _orchestrator_state["current_plan"] = plan
        _orchestrator_state["current_validation"] = validation
        _orchestrator_state["current_iteration"] += 1
        
        await ctx.report_progress(progress=5, total=5)
        
        # Format for presentation
        iteration = _orchestrator_state["current_iteration"]
        
        # Ensure plan text is not empty
        plan_text = plan.get('text', '')
        if not plan_text or len(plan_text.strip()) == 0:
            plan_text = "❌ ERROR: Plan generation failed - no plan text generated"
        
        result = f"""🔄 ITERATION {iteration} - PLAN GENERATED

📋 PROPOSED PLAN:
{'-'*80}
{plan_text}
{'-'*80}

✅ VALIDATION RESULTS:
{'-'*80}
Status: {'✅ VALID' if validation['is_valid'] else '⚠️ ISSUES DETECTED'}

Precondition Check:
{validation['precondition_check']}

Conflict Check:
{validation['conflict_check']}
{'-'*80}

💡 NEXT STEPS:
To approve this plan, say: "Approve the plan" or use approve_current_plan()
To reject this plan, say: "Reject because [reason]" or use reject_current_plan(reason)
To see learning progress, use view_learning_summary()

📁 PLAN DETAILS:
- Goal: {plan.get('goal', 'Unknown')}
- Generated: {plan.get('timestamp', 'Unknown')}
- Plan Length: {len(plan_text)} characters
"""
        return result
        
    except Exception as exc:
        return f"❌ Error in planning iteration: {type(exc).__name__}: {exc}"


@mcp.tool()
async def approve_current_plan(ctx: Context) -> str:
    """
    Approve the current plan and execute it.
    
    This approves the plan from the most recent start_planning_iteration() call.
    The plan will be executed and the system will learn from this success.
    
    Returns:
        Execution results and confirmation that memory was updated
    """
    try:
        if _orchestrator_state["current_plan"] is None:
            return "❌ No plan to approve. Start a planning iteration first with start_planning_iteration(goal)."
        
        orchestrator = _ensure_orchestrator()
        plan = _orchestrator_state["current_plan"]
        validation = _orchestrator_state["current_validation"]
        
        await ctx.report_progress(progress=1, total=3)
        
        # Execute the plan
        execution_result = orchestrator._execute_plan(plan)
        await ctx.report_progress(progress=2, total=3)
        
        # Write success to memory (LEARNING!)
        orchestrator._write_success_to_memory(plan, validation, execution_result)
        await ctx.report_progress(progress=3, total=3)
        
        # Clear current plan
        _orchestrator_state["current_plan"] = None
        _orchestrator_state["current_validation"] = None
        
        # Get execution details
        execution_text = execution_result.get('execution_text', 'No execution details available')
        deliverables_created = execution_result.get('deliverables_created', False)
        
        result = f"""✅ PLAN APPROVED & EXECUTED

⚙️ Execution Results:
- Status: {execution_result['status'].upper()}
- Actions completed: {execution_result['actions_completed']}
- Deliverables created: {'✅ YES' if deliverables_created else '❌ NO'}
- Timestamp: {execution_result['timestamp']}

📄 Execution Details:
{'-'*60}
{execution_text}
{'-'*60}

💾 Memory Updated (Learning!):
- ✅ Execution log updated
- ✅ Successful patterns recorded
- ✅ Deliverables stored in memory
- ✅ Next iteration will use this learned context

🎉 Iteration {_orchestrator_state['current_iteration']} complete!

Want to continue? Start a new iteration with start_planning_iteration(goal).
"""
        return result
        
    except Exception as exc:
        return f"❌ Error approving plan: {type(exc).__name__}: {exc}"


@mcp.tool()
async def reject_current_plan(reason: str, ctx: Context) -> str:
    """
    Reject the current plan with feedback.
    
    This rejects the plan from the most recent start_planning_iteration() call.
    Your feedback helps the system learn what NOT to do in future iterations.
    
    Args:
        reason: Why you're rejecting the plan (e.g., "Skips testing phase")
    
    Returns:
        Confirmation that the system learned from this rejection
    """
    try:
        if _orchestrator_state["current_plan"] is None:
            return "❌ No plan to reject. Start a planning iteration first with start_planning_iteration(goal)."
        
        orchestrator = _ensure_orchestrator()
        plan = _orchestrator_state["current_plan"]
        validation = _orchestrator_state["current_validation"]
        
        # Write failure to memory (also learning!)
        orchestrator._write_failure_to_memory(plan, validation, reason)
        
        # Clear current plan
        _orchestrator_state["current_plan"] = None
        _orchestrator_state["current_validation"] = None
        
        result = f"""
❌ PLAN REJECTED

📝 Your Feedback: {reason}

💾 Memory Updated (Learning from Mistake!):
- ✅ Error pattern recorded
- ✅ System will avoid this approach in future iterations
- ✅ Next iteration will have better understanding

🔄 Ready for next iteration!
Start a new planning cycle with start_planning_iteration(goal).
The system will now avoid the rejected approach.
"""
        return result
        
    except Exception as exc:
        return f"❌ Error rejecting plan: {type(exc).__name__}: {exc}"


@mcp.tool()
async def view_learning_summary(ctx: Context) -> str:
    """
    View what the system has learned so far.
    
    Shows:
    - Number of iterations completed
    - Success/failure rate
    - Learned patterns
    - Known errors to avoid
    
    Returns:
        Summary of accumulated learning
    """
    try:
        orchestrator = _ensure_orchestrator()
        if not orchestrator:
            return "❌ Orchestrator not available."
        
        from pathlib import Path
        memory_path = Path(_read_memory_path())
        
        # Read execution log
        execution_log = memory_path / "entities" / "execution_log.md"
        if execution_log.exists():
            content = execution_log.read_text()
            successes = content.count("SUCCESS ✅")
        else:
            successes = 0
        
        # Read errors
        errors_file = memory_path / "entities" / "planning_errors.md"
        if errors_file.exists():
            errors_content = errors_file.read_text()
            failures = errors_content.count("REJECTED ❌")
        else:
            failures = 0
        
        # Read patterns
        patterns_file = memory_path / "entities" / "successful_patterns.md"
        patterns_preview = ""
        if patterns_file.exists():
            patterns_content = patterns_file.read_text()
            # Get first few patterns
            lines = patterns_content.split('\n')
            pattern_lines = [l for l in lines if l.startswith('### Pattern')][:5]
            patterns_preview = '\n'.join(pattern_lines)
        
        total = _orchestrator_state["current_iteration"]
        success_rate = (successes / total * 100) if total > 0 else 0
        
        result = f"""
📊 LEARNING SUMMARY

Iterations Completed: {total}
Successful Plans: {successes}
Rejected Plans: {failures}
Success Rate: {success_rate:.1f}%

📚 Learned Patterns:
{patterns_preview if patterns_preview else "No patterns yet (run some iterations!)"}

❌ Known Errors to Avoid: {failures}

💡 The system gets smarter with each iteration!
Context accumulates in memory/entities/:
  - execution_log.md (successful iterations)
  - successful_patterns.md (proven approaches)
  - planning_errors.md (mistakes to avoid)

Start a new iteration to continue learning: start_planning_iteration(goal)
"""
        return result
        
    except Exception as exc:
        return f"❌ Error viewing summary: {type(exc).__name__}: {exc}"


@mcp.tool()
async def start_autonomous_planning(
    goal: str,
    num_iterations: int,
    checkpoint_every: int = 5,
    ctx: Context = None
) -> str:
    """
    Start semi-autonomous planning loop for multiple iterations.
    
    The system will run multiple planning iterations automatically, pausing
    for human approval at regular checkpoints. This enables building up
    substantial learned context over many iterations without requiring
    approval for every single step.
    
    The system will:
    1. Run N iterations automatically
    2. Auto-approve plans that pass validation (learning from each)
    3. Pause every checkpoint_every iterations for human review
    4. Accumulate learned context progressively
    5. Get smarter with each iteration
    
    CRITICAL: The goal parameter is a plain text string that should be passed directly to the orchestrator.
    DO NOT use use_memory_agent to create entity lookups from words in the goal.
    DO NOT split the goal into tokens or try to find matching entities.
    The orchestrator will handle all memory operations internally.
    Simply pass the goal string as-is to the orchestrator.
    
    Perfect for building up 10-50+ iterations of learned context!
    
    Args:
        goal: The overarching planning goal
        num_iterations: Total number of iterations to run (e.g., 20, 50, 100)
        checkpoint_every: Pause for approval every N iterations (default: 5)
    
    Returns:
        Progress updates and checkpoint summaries
    """
    try:
        # Reset orchestrator to ensure fresh instance with updated validation logic
        _reset_orchestrator()
        orchestrator = _ensure_orchestrator()
        if not orchestrator:
            return "❌ Orchestrator not available."
        
        # Set autonomous mode and store goal for resuming
        _orchestrator_state["autonomous_mode"] = True
        _orchestrator_state["autonomous_target"] = num_iterations
        _orchestrator_state["autonomous_goal"] = goal
        _orchestrator_state["checkpoint_interval"] = checkpoint_every
        
        results = []
        iterations_since_checkpoint = 0
        successful = 0
        failed = 0
        
        results.append(f"""
🤖 STARTING SEMI-AUTONOMOUS PLANNING

Goal: {goal}
Target iterations: {num_iterations}
Checkpoint interval: Every {checkpoint_every} iterations

The system will now run autonomously, pausing for your review at checkpoints.
Building up learned context progressively... 🧠
""")
        
        if ctx:
            await ctx.report_progress(progress=0, total=num_iterations)
        
        for i in range(num_iterations):
            iteration_num = _orchestrator_state["current_iteration"] + 1
            
            try:
                # Step 1: Retrieve context (gets richer each iteration!)
                context = orchestrator._retrieve_context()
                
                # Step 2: Generate plan
                plan = orchestrator._generate_plan_with_cot(goal, context)
                
                # Step 3: Validate
                validation = orchestrator._validate_plan(plan)
                
                # Store plan
                _orchestrator_state["current_plan"] = plan
                _orchestrator_state["current_validation"] = validation
                _orchestrator_state["current_iteration"] = iteration_num
                
                # Check if we should pause for human review
                iterations_since_checkpoint += 1
                is_checkpoint = (iterations_since_checkpoint >= checkpoint_every)
                
                print(f"🔍 DEBUG: Checkpoint logic")
                print(f"   iterations_since_checkpoint: {iterations_since_checkpoint}")
                print(f"   checkpoint_every: {checkpoint_every}")
                print(f"   is_checkpoint: {is_checkpoint}")
                
                # Debug logging for autonomous mode
                print(f"🔍 DEBUG: Iteration {iteration_num}")
                print(f"   validation['is_valid']: {validation['is_valid']}")
                print(f"   is_checkpoint: {is_checkpoint}")
                print(f"   iterations_since_checkpoint: {iterations_since_checkpoint}")
                print(f"   checkpoint_every: {checkpoint_every}")
                
                # Auto-approve if valid and not at checkpoint
                if validation['is_valid'] and not is_checkpoint:
                    print(f"✅ AUTO-APPROVING: validation['is_valid']={validation['is_valid']}, is_checkpoint={is_checkpoint}")
                    # Execute automatically
                    execution_result = orchestrator._execute_plan(plan)
                    orchestrator._write_success_to_memory(plan, validation, execution_result)
                    
                    successful += 1
                    results.append(f"✅ Iteration {iteration_num}: Auto-approved (valid)")
                    
                    # Clear for next iteration
                    _orchestrator_state["current_plan"] = None
                    _orchestrator_state["current_validation"] = None
                    
                elif is_checkpoint:
                    print(f"🛑 CHECKPOINT: validation['is_valid']={validation['is_valid']}, is_checkpoint={is_checkpoint}")
                    # Pause for human review
                    results.append(f"""
🛑 CHECKPOINT at Iteration {iteration_num}/{num_iterations}

Progress so far:
- Completed: {i} iterations
- Successful: {successful}
- Failed: {failed}
- Success rate: {(successful/(i+1)*100) if i > 0 else 0:.1f}%

Current plan:
{plan['text']}

Validation: {'✅ VALID' if validation['is_valid'] else '⚠️ ISSUES'}

OPTIONS:
1. To continue autonomously: use continue_autonomous_planning()
2. To approve current plan and continue: use approve_current_plan()
3. To stop autonomous mode: use stop_autonomous_planning()

Autonomous mode PAUSED at checkpoint.
""")
                    iterations_since_checkpoint = 0
                    
                    # Exit loop and wait for user decision
                    _orchestrator_state["autonomous_mode"] = "paused"
                    break
                    
                else:
                    # Invalid plan - pause for review
                    print(f"❌ INVALID PLAN: validation['is_valid']={validation['is_valid']}, is_checkpoint={is_checkpoint}")
                    results.append(f"""
⚠️ PAUSING at Iteration {iteration_num} - Plan validation issues

{validation['precondition_check']}

The system detected issues and is pausing for your review.
Use reject_current_plan(reason) to provide feedback, then continue.
""")
                    _orchestrator_state["autonomous_mode"] = "paused"
                    break
                
                if ctx:
                    await ctx.report_progress(progress=i+1, total=num_iterations)
                    
            except Exception as exc:
                failed += 1
                results.append(f"❌ Iteration {iteration_num}: Error - {exc}")
        
        # If we completed all iterations without pausing
        if iterations_since_checkpoint > 0 and i == num_iterations - 1:
            results.append(f"""
🎉 AUTONOMOUS PLANNING COMPLETE!

Total iterations: {num_iterations}
Successful: {successful}
Failed: {failed}
Success rate: {(successful/num_iterations*100):.1f}%

💾 Memory enriched with {num_iterations} iterations of learned context!

The system is now significantly smarter. Use view_learning_summary() to see what was learned.
""")
            _orchestrator_state["autonomous_mode"] = False
        
        return "\n".join(results)
        
    except Exception as exc:
        _orchestrator_state["autonomous_mode"] = False
        return f"❌ Error in autonomous planning: {type(exc).__name__}: {exc}"


@mcp.tool()
async def continue_autonomous_planning(ctx: Context) -> str:
    """
    Continue autonomous planning from last checkpoint.
    
    Use this after reviewing a checkpoint to continue the autonomous loop.
    The system will run until the next checkpoint or completion.
    
    Returns:
        Confirmation that autonomous mode resumed
    """
    try:
        if _orchestrator_state["autonomous_mode"] != "paused":
            return "❌ Not currently at a checkpoint. Start autonomous planning first with start_autonomous_planning()."
        
        current_iter = _orchestrator_state["current_iteration"]
        target_iter = _orchestrator_state["autonomous_target"]
        goal = _orchestrator_state["autonomous_goal"]
        checkpoint_interval = _orchestrator_state["checkpoint_interval"]
        remaining = target_iter - current_iter
        
        # If there's a current plan, approve it first
        result_msg = ""
        if _orchestrator_state["current_plan"] is not None:
            orchestrator = _ensure_orchestrator()
            plan = _orchestrator_state["current_plan"]
            validation = _orchestrator_state["current_validation"]
            
            execution_result = orchestrator._execute_plan(plan)
            orchestrator._write_success_to_memory(plan, validation, execution_result)
            
            result_msg = f"✅ Checkpoint plan approved.\n"
            
            _orchestrator_state["current_plan"] = None
            _orchestrator_state["current_validation"] = None
        
        # Continue autonomous planning with remaining iterations
        continuation_result = await start_autonomous_planning(
            goal=goal,
            num_iterations=remaining,
            checkpoint_every=checkpoint_interval,
            ctx=ctx
        )
        
        return f"""
{result_msg}
🔄 RESUMING AUTONOMOUS PLANNING

Current iteration: {current_iter}
Target iteration: {target_iter}
Remaining: {remaining} iterations

{continuation_result}
"""
        
    except Exception as exc:
        return f"❌ Error continuing: {type(exc).__name__}: {exc}"


@mcp.tool()
async def stop_autonomous_planning(ctx: Context) -> str:
    """
    Stop autonomous planning mode.
    
    Use this to exit autonomous mode and return to manual iteration control.
    
    Returns:
        Summary of what was accomplished
    """
    try:
        if not _orchestrator_state["autonomous_mode"]:
            return "ℹ️ Not currently in autonomous mode."
        
        iterations_completed = _orchestrator_state["current_iteration"]
        
        _orchestrator_state["autonomous_mode"] = False
        _orchestrator_state["autonomous_target"] = 0
        _orchestrator_state["autonomous_goal"] = None
        _orchestrator_state["current_plan"] = None
        _orchestrator_state["current_validation"] = None
        
        return f"""
🛑 AUTONOMOUS PLANNING STOPPED

Iterations completed: {iterations_completed}

💾 Memory has been updated with all successful iterations.
The system has learned from this session.

You can:
- View what was learned: use view_learning_summary()
- Start manual iterations: use start_planning_iteration(goal)
- Start new autonomous session: use start_autonomous_planning(goal, num_iterations)
"""
        
    except Exception as exc:
        return f"❌ Error stopping: {type(exc).__name__}: {exc}"


if __name__ == "__main__":
    # Configure transport from environment; default to stdio when run by a client
    transport = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()

    if transport == "http":
        host = os.getenv("MCP_HOST", "127.0.0.1")
        path = os.getenv("MCP_PATH", "/mcp/")
        port_str = os.getenv("MCP_PORT", "")

        # If no port provided (or set to 0), choose a free one to avoid conflicts
        if not port_str or port_str == "0":
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, 0))
                port = s.getsockname()[1]
        else:
            try:
                port = int(port_str)
            except ValueError:
                # Fallback to a free port if invalid value provided
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((host, 0))
                    port = s.getsockname()[1]

        mcp.run(transport="http", host=host, port=port, path=path)
    else:
        # Use stdio transport by default or when explicitly requested
        mcp.run(transport="stdio")


