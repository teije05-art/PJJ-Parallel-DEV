import os
import sys
import socket
import asyncio
import time
from datetime import datetime
from typing import Optional
from pathlib import Path

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
    from orchestrator.simple_orchestrator import SimpleOrchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False
    print("Warning: Orchestrator not available. Planning tools will be disabled.", file=sys.stderr)

# Initialize FastMCP (the installed version doesn't accept a timeout kwarg)
mcp = FastMCP("memory-agent-server")

# Global state for enhanced orchestrator (persists between tool calls)
_orchestrator_state = {
    "orchestrator": None,
    "current_plan": None,
    "current_validation": None,
    "current_agent_results": None,  # Store results from 4 specialized agents
    "current_context": None,  # Store context including web search results for display
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
    """Initialize enhanced orchestrator if not already done"""
    if not ORCHESTRATOR_AVAILABLE:
        return None
    
    if _orchestrator_state["orchestrator"] is None:
        memory_path = _read_memory_path()
        # Use lenient validation for autonomous mode by default
        _orchestrator_state["orchestrator"] = SimpleOrchestrator(
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
    start_time = time.time()
    try:
        print(f"[STEP 0] start_planning_iteration called with goal: {goal[:100]}")

        step1_start = time.time()
        orchestrator = _ensure_orchestrator()
        if not orchestrator:
            return "❌ Orchestrator not available. Make sure orchestrator module is installed."
        print(f"[STEP 1a] Orchestrator initialized ({time.time()-step1_start:.2f}s), retrieving context...")
        await ctx.report_progress(progress=1, total=6)

        # Step 1: Retrieve enhanced context
        step2_start = time.time()
        print(f"[STEP 1b] Calling _retrieve_enhanced_context...")
        context = orchestrator._retrieve_enhanced_context(goal)
        step2_time = time.time() - step2_start
        print(f"[STEP 1c] Context retrieved: {len(str(context))} chars ({step2_time:.2f}s)")
        await ctx.report_progress(progress=2, total=6)

        # Step 2: Coordinate agentic workflow (4 specialized agents)
        step3_start = time.time()
        print(f"[STEP 2a] Starting 4-agent workflow...")
        agent_results = orchestrator.agent_coordinator.coordinate_agentic_workflow(goal, context)
        step3_time = time.time() - step3_start
        print(f"[STEP 2b] 4-agent workflow completed with {len(agent_results)} results ({step3_time:.2f}s)")
        await ctx.report_progress(progress=3, total=6)

        # Store in global state (enhanced format)
        print(f"[STEP 3a] Storing plan and validation results...")
        _orchestrator_state["current_plan"] = agent_results['planner']
        _orchestrator_state["current_validation"] = agent_results['verifier']
        _orchestrator_state["current_agent_results"] = agent_results
        # Store only the web search results string, not the entire context (which contains non-serializable objects)
        _orchestrator_state["current_context"] = {"web_search_results": context.get("web_search_results", "")}
        _orchestrator_state["current_iteration"] += 1
        print(f"[STEP 3b] State stored, preparing output...")

        await ctx.report_progress(progress=4, total=6)

        # Format for presentation
        print(f"[STEP 4a] Formatting presentation output...")
        iteration = _orchestrator_state["current_iteration"]

        await ctx.report_progress(progress=5, total=6)

        # Ensure agent results are available
        print(f"[STEP 4b] Extracting agent results...")
        planner_result = agent_results['planner']
        verifier_result = agent_results['verifier']
        executor_result = agent_results['executor']
        generator_result = agent_results['generator']

        plan_text = planner_result.output if planner_result else ''
        if not plan_text or len(plan_text.strip()) == 0:
            plan_text = "❌ ERROR: Enhanced planning failed - no plan generated"

        print(f"[STEP 4c] Storing full results to memory to avoid large MCP response...")

        # CRITICAL FIX: Don't return all agent outputs through MCP stdio
        # MCP stdio has buffer limits that cause "Broken Pipe" errors
        # Store full results to disk/memory instead, return only a compact summary

        from pathlib import Path
        memory_path = Path(orchestrator.memory_path)
        plans_dir = memory_path / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)

        # Store the full detailed results
        full_results_file = plans_dir / f"iteration_{iteration:03d}_full_details.md"

        full_content = f"""# Planning Iteration {iteration} - Complete Results

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Goal:** {goal}
**Execution Time:** {time.time() - start_time:.2f} seconds

---

## 🧭 Planner Agent - Strategic Plan

**Status:** {'✅ SUCCESS' if planner_result.success else '❌ FAILED'}

{planner_result.output if planner_result else 'No planner output available'}

---

## ✅ Verifier Agent - Validation & Review

**Status:** {'✅ SUCCESS' if verifier_result.success else '❌ FAILED'}
**Validation Result:** {'✅ VALID' if verifier_result.metadata.get('is_valid') else '⚠️ ISSUES DETECTED'}

{verifier_result.output if verifier_result else 'No verifier output available'}

---

## 🛠️ Executor Agent - Implementation Details

**Status:** {'✅ SUCCESS' if executor_result.success else '❌ FAILED'}
**Deliverables Created:** {executor_result.metadata.get('deliverables_created', 0)}

{executor_result.output if executor_result else 'No executor output available'}

---

## ✍️ Generator Agent - Synthesis & Final Output

**Status:** {'✅ SUCCESS' if generator_result.success else '❌ FAILED'}
**Synthesized Deliverables:** {generator_result.metadata.get('deliverables_created', 0)}

{generator_result.output if generator_result else 'No generator output available'}

---

## 🎓 Learning & Training

**Flow-GRPO Training:** ✅ Applied based on overall workflow success
**Overall Assessment:** {'✅ VALID - Ready for approval and execution' if verifier_result.metadata.get('is_valid') else '⚠️ ISSUES FOUND - Review before approval'}

*This complete output has been stored to memory for persistent reference and future learning.*
"""

        try:
            full_results_file.write_text(full_content)
            print(f"[STEP 4d] Full results saved: {full_results_file.name}")
        except Exception as e:
            print(f"[WARNING] Could not save full results: {e}")

        # Build a COMPACT summary for MCP response (keeps it under 5KB to avoid broken pipe)
        print(f"[STEP 4e] Building compact summary for MCP response...")
        result = f"""✅ PLANNING ITERATION {iteration} COMPLETED

🎯 AGENT RESULTS SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  🧭 Planner Agent........{'✅ SUCCESS' if planner_result.success else '❌ FAILED'}
  ✅ Verifier Agent........{'✅ SUCCESS' if verifier_result.success else '❌ FAILED'} ({'VALID' if verifier_result.metadata.get('is_valid') else 'REVIEW'})
  🛠️  Executor Agent........{'✅ SUCCESS' if executor_result.success else '❌ FAILED'}
  ✍️  Generator Agent.......{'✅ SUCCESS' if generator_result.success else '❌ FAILED'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 ITERATION DETAILS
  • Goal: {goal[:60]}{'...' if len(goal) > 60 else ''}
  • Status: {'✅ VALID - Ready for approval' if verifier_result.metadata.get('is_valid') else '⚠️ Issues detected - review needed'}
  • Time: {time.time() - start_time:.1f} seconds
  • Results stored to memory for persistent access

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 WHAT'S NEXT?

1️⃣  VIEW COMPLETE PLAN:
    → use_memory_agent("retrieve iteration {iteration} complete results")
    → Or use: view_full_plan()

2️⃣  REVIEW SPECIFIC CONTENT:
    → Browse entities: list_entities()
    → View entity: view_entity_content(entity_name)

3️⃣  MAKE A DECISION:
    → Approve: approve_current_plan()
    → Reject: reject_current_plan(reason)

4️⃣  TRACK LEARNING:
    → view_learning_summary()

🎓 YOUR SYSTEM IS LEARNING:
   Each iteration generates Flow-GRPO training signals that improve planning.
   More iterations = smarter, more detailed plans with better patterns.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        total_time = time.time() - start_time
        print(f"[STEP 5] Summary created ({len(result)} chars) - Total time: {total_time:.2f}s")
        await ctx.report_progress(progress=6, total=6)
        print(f"[COMPLETE] start_planning_iteration completed successfully in {total_time:.2f}s")
        return result

    except Exception as exc:
        import traceback
        total_time = time.time() - start_time
        print(f"[ERROR] Exception in start_planning_iteration after {total_time:.2f}s: {type(exc).__name__}: {exc}")
        traceback.print_exc()
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
        agent_results = _orchestrator_state.get("current_agent_results", {})
        plan = _orchestrator_state["current_plan"]
        
        await ctx.report_progress(progress=1, total=3)
        
        # Execute the enhanced workflow
        goal = plan.goal if hasattr(plan, 'goal') else 'Unknown goal'
        execution_result = orchestrator._execute_enhanced_workflow(agent_results, goal)
        await ctx.report_progress(progress=2, total=3)
        
        # Write success to memory (LEARNING!)
        orchestrator._write_enhanced_success_to_memory(agent_results, execution_result)
        await ctx.report_progress(progress=3, total=3)

        # Clear current plan and agent results
        _orchestrator_state["current_plan"] = None
        _orchestrator_state["current_validation"] = None
        _orchestrator_state["current_agent_results"] = None
        _orchestrator_state["current_context"] = None  # Clear context after approval

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
        agent_results = _orchestrator_state.get("current_agent_results", {})
        plan = _orchestrator_state["current_plan"]
        
        # Write rejection to memory (LEARNING!)
        orchestrator._write_enhanced_rejection_to_memory(agent_results, reason)

        # Clear current plan and agent results
        _orchestrator_state["current_plan"] = None
        _orchestrator_state["current_validation"] = None
        _orchestrator_state["current_agent_results"] = None
        _orchestrator_state["current_context"] = None  # Clear context after rejection
        
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
async def view_full_plan(ctx: Context) -> str:
    """
    View the complete plan and all generated content from the most recent planning iteration.
    
    This shows the full comprehensive plan without truncation, along with all agent outputs
    and generated deliverables.
    
    Returns:
        Complete plan details, agent outputs, and generated content
    """
    try:
        if _orchestrator_state["current_plan"] is None:
            return "❌ No plan available. Start a planning iteration first with start_planning_iteration(goal)."
        
        agent_results = _orchestrator_state.get("current_agent_results", {})
        plan = _orchestrator_state["current_plan"]
        context = _orchestrator_state.get("current_context", {})

        # Get full outputs from all agents
        planner_result = agent_results.get('planner')
        verifier_result = agent_results.get('verifier')
        executor_result = agent_results.get('executor')
        generator_result = agent_results.get('generator')

        # Get web search results from context
        web_search_results = context.get("web_search_results", "No web search results available")

        result = f"""📋 COMPLETE PLAN AND GENERATED CONTENT

🌐 WEB RESEARCH DATA SOURCES:
{'-'*80}
{web_search_results}

{'-'*80}

🎯 FULL COMPREHENSIVE PLAN:
{'-'*80}
{planner_result.output if planner_result else 'No planner results'}

✅ COMPLETE VERIFICATION RESULTS:
{'-'*80}
{verifier_result.output if verifier_result else 'No verifier results'}

🛠️ COMPLETE EXECUTION RESULTS:
{'-'*80}
{executor_result.output if executor_result else 'No executor results'}

✍️ COMPLETE SYNTHESIS RESULTS:
{'-'*80}
{generator_result.output if generator_result else 'No generator results'}

📁 GENERATED ENTITIES:
{'-'*80}
"""
        
        # List all generated entity files
        entities_dir = Path(_orchestrator_state.get("memory_path", "/Users/teije/Desktop/memagent/local-memory")) / "entities"
        if entities_dir.exists():
            entity_files = list(entities_dir.glob("*.md"))
            for entity_file in sorted(entity_files):
                if entity_file.name not in ["execution_log.md", "successful_patterns.md", "planning_errors.md", "agent_performance.md"]:
                    result += f"- {entity_file.name}\n"
        
        result += f"""
{'-'*80}
📊 PLAN STATISTICS:
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

💡 NEXT STEPS:
- To approve this plan: "Approve the plan" or use approve_current_plan()
- To reject this plan: "Reject because [reason]" or use reject_current_plan(reason)
- To see learning progress: use view_learning_summary()
"""
        
        return result
        
    except Exception as exc:
        return f"❌ Error viewing full plan: {type(exc).__name__}: {exc}"


@mcp.tool()
async def view_entity_content(ctx: Context, entity_name: str) -> str:
    """
    View the content of a specific entity file.
    
    Args:
        entity_name: Name of the entity file to view (without .md extension)
    
    Returns:
        Complete content of the specified entity file
    """
    try:
        entities_dir = Path(_orchestrator_state.get("memory_path", "/Users/teije/Desktop/memagent/local-memory")) / "entities"
        entity_file = entities_dir / f"{entity_name}.md"
        
        if not entity_file.exists():
            return f"❌ Entity '{entity_name}' not found. Available entities:\n" + "\n".join([
                f"- {f.stem}" for f in entities_dir.glob("*.md") 
                if f.name not in ["execution_log.md", "successful_patterns.md", "planning_errors.md", "agent_performance.md"]
            ])
        
        content = entity_file.read_text(encoding='utf-8')
        
        return f"""📄 ENTITY CONTENT: {entity_name}

{'-'*80}
{content}
{'-'*80}

📊 STATISTICS:
- File Size: {len(content)} characters
- Lines: {content.count(chr(10)) + 1}
- Last Modified: {datetime.fromtimestamp(entity_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}
"""
        
    except Exception as exc:
        return f"❌ Error viewing entity '{entity_name}': {type(exc).__name__}: {exc}"


@mcp.tool()
async def cleanup_empty_entities(ctx: Context) -> str:
    """
    Clean up empty or placeholder entities created by the system.
    
    This removes entities that contain only placeholder text or are empty,
    keeping only entities with actual content.
    
    Returns:
        Summary of cleanup actions taken
    """
    try:
        entities_dir = Path(_orchestrator_state.get("memory_path", "/Users/teije/Desktop/memagent/local-memory")) / "entities"
        
        if not entities_dir.exists():
            return "❌ No entities directory found."
        
        # Define patterns that indicate empty/placeholder entities
        empty_patterns = [
            "This file will store",
            "This entity will be populated",
            "This entity contains information relevant to the current project",
            "This document outlines",
            "This file contains",
            "This entity contains",
            "This file is used to store",
            "This file tracks",
            "This file contains information about"
        ]
        
        cleaned_count = 0
        kept_count = 0
        empty_entities = []
        content_entities = []
        
        for entity_file in entities_dir.glob("*.md"):
            try:
                content = entity_file.read_text(encoding='utf-8').strip()
                
                # Skip if file is empty or very short
                if len(content) < 50:
                    entity_file.unlink()
                    cleaned_count += 1
                    empty_entities.append(entity_file.name)
                    continue
                
                # Check if content matches empty patterns
                is_empty = any(pattern in content for pattern in empty_patterns)
                
                if is_empty:
                    entity_file.unlink()
                    cleaned_count += 1
                    empty_entities.append(entity_file.name)
                else:
                    kept_count += 1
                    content_entities.append(entity_file.name)
                    
            except Exception as e:
                print(f"Error processing {entity_file.name}: {e}")
                continue
        
        result = f"""🧹 ENTITY CLEANUP COMPLETED

📊 Cleanup Summary:
- Empty entities removed: {cleaned_count}
- Content entities kept: {kept_count}
- Total entities processed: {cleaned_count + kept_count}

🗑️ Removed Empty Entities:
{chr(10).join(f"- {name}" for name in empty_entities[:10])}
{'...' if len(empty_entities) > 10 else ''}

✅ Kept Content Entities:
{chr(10).join(f"- {name}" for name in content_entities[:10])}
{'...' if len(content_entities) > 10 else ''}

💡 Next Steps:
- Run a new planning iteration to create properly populated entities
- Use view_full_plan() to see the comprehensive plan
- Use view_entity_content(entity_name) to view specific entities
"""
        
        return result
        
    except Exception as exc:
        return f"❌ Error during cleanup: {type(exc).__name__}: {exc}"


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
        
        total = int(successes) + int(failures)
        success_rate = (int(successes) / int(total) * 100) if int(total) > 0 else 0
        
        result = f"""
📊 LEARNING SUMMARY

Total Iterations: {total}
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
                # Step 1: Retrieve enhanced context (gets richer each iteration!)
                context = orchestrator._retrieve_enhanced_context(goal)
                
                # Step 2: Coordinate agentic workflow (4 specialized agents)
                agent_results = orchestrator.agent_coordinator.coordinate_agentic_workflow(goal, context)
                
                # Step 3: Extract plan and validation from agent results
                plan = agent_results['planner']
                validation = agent_results['verifier']
                
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
                print(f"   validation.metadata.get('is_valid'): {validation.metadata.get('is_valid')}")
                print(f"   is_checkpoint: {is_checkpoint}")
                print(f"   iterations_since_checkpoint: {iterations_since_checkpoint}")
                print(f"   checkpoint_every: {checkpoint_every}")
                
                # Auto-approve if valid and not at checkpoint
                if validation.metadata.get('is_valid', False) and not is_checkpoint:
                    print(f"✅ AUTO-APPROVING: validation.metadata.get('is_valid')={validation.metadata.get('is_valid')}, is_checkpoint={is_checkpoint}")
                    # Execute automatically using enhanced workflow
                    execution_result = orchestrator._execute_enhanced_workflow(agent_results, goal)
                    orchestrator._write_enhanced_success_to_memory(agent_results, execution_result)
                    
                    successful += 1
                    results.append(f"✅ Iteration {iteration_num}: Auto-approved (valid)")
                    
                    # Clear for next iteration
                    _orchestrator_state["current_plan"] = None
                    _orchestrator_state["current_validation"] = None
                    
                elif is_checkpoint:
                    print(f"🛑 CHECKPOINT: validation.metadata.get('is_valid')={validation.metadata.get('is_valid')}, is_checkpoint={is_checkpoint}")
                    # Pause for human review
                    results.append(f"""
🛑 CHECKPOINT at Iteration {iteration_num}/{num_iterations}

Progress so far:
- Completed: {i} iterations
- Successful: {successful}
- Failed: {failed}
- Success rate: {(int(successful)/int(i+1)*100) if i > 0 else 0:.1f}%

Current plan:
{plan.output}

Validation: {'✅ VALID' if validation.metadata.get('is_valid') else '⚠️ ISSUES'}

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
                    print(f"❌ INVALID PLAN: validation.metadata.get('is_valid')={validation.metadata.get('is_valid')}, is_checkpoint={is_checkpoint}")
                    results.append(f"""
⚠️ PAUSING at Iteration {iteration_num} - Plan validation issues

{validation.output}

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
Success rate: {(int(successful)/int(num_iterations)*100):.1f}%

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
            agent_results = _orchestrator_state.get("current_agent_results", {})
            
            execution_result = orchestrator._execute_enhanced_workflow(agent_results, goal)
            orchestrator._write_enhanced_success_to_memory(agent_results, execution_result)
            
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


@mcp.tool()
async def list_entities(ctx: Context) -> str:
    """
    List all available entities in the memory system.
    
    This tool provides a comprehensive list of all entity files that can be viewed
    or queried through the memory system. Perfect for discovering what information
    is available before making specific queries.
    
    Returns:
        Formatted list of all available entities with basic information
    """
    try:
        from pathlib import Path
        
        # Get memory path
        memory_path = Path(_read_memory_path())
        entities_dir = memory_path / "entities"
        
        if not entities_dir.exists():
            return "❌ No entities directory found. Memory system may not be initialized."
        
        # Get all entity files
        entity_files = list(entities_dir.glob("*.md"))
        
        if not entity_files:
            return "📁 No entities found in the memory system."
        
        # Categorize entities
        system_entities = []
        project_entities = []
        other_entities = []
        
        for entity_file in sorted(entity_files):
            entity_name = entity_file.stem
            file_size = entity_file.stat().st_size
            
            # Categorize based on name patterns
            if entity_name in ["execution_log", "successful_patterns", "planning_errors", "agent_performance", "agent_coordination", "planner_training_log"]:
                system_entities.append((entity_name, file_size))
            elif any(keyword in entity_name.lower() for keyword in ["project", "plan", "deliverable", "report", "analysis", "strategy", "framework", "timeline", "kpi", "metric"]):
                project_entities.append((entity_name, file_size))
            else:
                other_entities.append((entity_name, file_size))
        
        # Format the response
        result = "📚 AVAILABLE ENTITIES\n"
        result += "=" * 50 + "\n\n"
        
        if system_entities:
            result += "🔧 SYSTEM ENTITIES (Learning & Performance):\n"
            for entity_name, file_size in system_entities:
                size_kb = file_size / 1024
                result += f"  • {entity_name} ({size_kb:.1f} KB)\n"
            result += "\n"
        
        if project_entities:
            result += "📋 PROJECT ENTITIES (Content & Deliverables):\n"
            for entity_name, file_size in project_entities:
                size_kb = file_size / 1024
                result += f"  • {entity_name} ({size_kb:.1f} KB)\n"
            result += "\n"
        
        if other_entities:
            result += "📄 OTHER ENTITIES:\n"
            for entity_name, file_size in other_entities:
                size_kb = file_size / 1024
                result += f"  • {entity_name} ({size_kb:.1f} KB)\n"
            result += "\n"
        
        result += f"📊 SUMMARY:\n"
        result += f"  Total entities: {len(entity_files)}\n"
        result += f"  System entities: {len(system_entities)}\n"
        result += f"  Project entities: {len(project_entities)}\n"
        result += f"  Other entities: {len(other_entities)}\n\n"
        
        result += "💡 USAGE:\n"
        result += "  • View specific entity: use view_entity_content(entity_name)\n"
        result += "  • Query entities: use use_memory_agent(question)\n"
        result += "  • View learning progress: use view_learning_summary()\n"
        
        return result
        
    except Exception as exc:
        return f"❌ Error listing entities: {type(exc).__name__}: {exc}"


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


