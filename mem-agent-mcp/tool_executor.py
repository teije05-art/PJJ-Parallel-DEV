"""
Tool Executor for Fireworks Function Calling

Executes the tools that Llama calls through function calling. CRITICAL ARCHITECTURE:

⚠️  MEMORY vs LLM DISTINCTION:
The system has two types of tools:

MEMORY TOOLS (use the memory system, NOT LLMs):
- search_memory: Searches entity files in /local-memory/entities/
  Uses: context.planner.search_memory() - reads files directly
  Returns: actual coverage, found content, identified gaps

This is the "memory-first" pattern. Memory operations happen via file I/O, not via LLM calls.

LLM PLANNING TOOLS (use planning agents):
- call_planner: Strategic planning via PlannerAgent
- call_verifier: Validation via VerifierAgent
- call_executor: Implementation details via ExecutorAgent
- call_generator: Synthesis via GeneratorAgent

RESEARCH TOOLS (web search, fills gaps):
- research: Iterative web search via ResearchAgent

WORKFLOW:
1. Llama calls search_memory → gets actual memory coverage
2. Llama identifies gaps → calls research for missing information
3. Llama calls planning agents with complete context
4. Results fed back to Llama for synthesis

Each tool is implemented as an async function that:
1. Receives arguments from Llama
2. Calls appropriate service (memory, research, or agent)
3. Formats result as JSON string
4. Returns to Fireworks for feeding back to Llama
"""

import json
import asyncio
from typing import Dict, Any, Optional, Callable

# Import specialized agents
try:
    from orchestrator.agents import (
        PlannerAgent,
        VerifierAgent,
        ExecutorAgent,
        GeneratorAgent,
        AgentResult
    )
except ImportError:
    PlannerAgent = None
    VerifierAgent = None
    ExecutorAgent = None
    GeneratorAgent = None
    AgentResult = None


class ToolExecutionContext:
    """
    Context for tool execution.

    Holds references to agent, planner, and other components needed by tools.
    """

    def __init__(
        self,
        agent: Any = None,
        planner: Any = None,
        research_agent: Any = None,
        learning_tracker: Any = None,
        memory_path: str = "",
        selected_entities: list = None,
        session: Dict = None
    ):
        self.agent = agent
        self.planner = planner
        self.research_agent = research_agent
        self.learning_tracker = learning_tracker
        self.memory_path = memory_path
        self.selected_entities = selected_entities or []
        self.session = session or {}


async def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    context: ToolExecutionContext
) -> str:
    """
    Execute a tool and return result as JSON string.

    ARCHITECTURE NOTE:
    This is where Llama's decisions become actions. Llama calls tools via function calling,
    and this dispatcher routes them to handlers. The critical distinction:

    MEMORY TASKS (should read files, not call Llama):
    - search_memory → reads entity files, calculates coverage
    - Uses context.planner.search_memory() (file-based, not LLM-based)

    LLM TASKS (should call planning agents):
    - call_planner → calls PlannerAgent LLM
    - call_verifier → calls VerifierAgent LLM
    - call_executor → calls ExecutorAgent LLM
    - call_generator → calls GeneratorAgent LLM

    RESEARCH TASKS (web search, fills gaps from memory):
    - research → calls ResearchAgent for web search

    Args:
        tool_name: Name of tool to execute (from Llama's function call)
        arguments: Arguments from Llama
        context: ToolExecutionContext with:
            - planner: Memory search tool (NOT Llama)
            - agent: MemAgent for planning agents
            - research_agent: Web search agent
            - selected_entities: User-approved entities to search
            - memory_path: Path to memory storage

    Returns:
        JSON string with tool result

    Raises:
        ValueError: If tool_name is unknown
    """

    print(f"🔧 Executing tool: {tool_name}")

    try:
        if tool_name == "search_memory":
            return await handle_search_memory(arguments, context)

        elif tool_name == "research":
            return await handle_research(arguments, context)

        elif tool_name == "call_planner":
            return await handle_call_planner(arguments, context)

        elif tool_name == "call_verifier":
            return await handle_call_verifier(arguments, context)

        elif tool_name == "call_executor":
            return await handle_call_executor(arguments, context)

        elif tool_name == "call_generator":
            return await handle_call_generator(arguments, context)

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return json.dumps({
            "status": "error",
            "tool": tool_name,
            "error": str(e)
        })


# ============================================================================
# Tool Handlers
# ============================================================================

async def handle_search_memory(args: Dict, context: ToolExecutionContext) -> str:
    """
    Handle search_memory tool call.

    ⚠️ CRITICAL: This is a MEMORY operation, NOT an LLM operation.

    This function reads entity files from the memory system. It does NOT call Llama.
    - planner.search_memory() is a file-reading utility, not an LLM call
    - Entity files are stored in /local-memory/entities/
    - This implements the "memory-first" pattern

    Searches selected memory entities for specific information.

    Args:
        args: {"entities": [...], "queries": [...]}
        context: ToolExecutionContext with planner (memory search tool)

    Returns:
        JSON string with search results:
        {
            "status": "success",
            "coverage": float (0.0-1.0),
            "content": str (found information),
            "gaps": list (missing information),
            "sources": list (entities where content was found),
            "entities_searched": int,
            "queries": list
        }
    """

    if not context.planner:
        return json.dumps({
            "status": "error",
            "error": "LlamaPlanner (memory search tool) not initialized"
        })

    entities = args.get("entities", [])
    queries = args.get("queries", [])

    print(f"   🔍 MEMORY SEARCH: Searching {len(entities)} entities for {len(queries)} queries")
    print(f"      (This reads entity files, not calling Llama)")

    # Use only selected entities if specified
    # This ensures we only search memory the user approved
    if context.selected_entities:
        entities = [e for e in entities if e in context.selected_entities]
        if not entities:
            print(f"      ⚠️  Query filtered to 0 entities (not in selected set)")

    if not entities:
        return json.dumps({
            "status": "warning",
            "coverage": 0.0,
            "content": "",
            "gaps": queries,
            "sources": [],
            "message": "No selected entities to search"
        })

    try:
        # Call planner's search_memory method
        # This reads entity files and searches for query matches
        # Returns actual coverage based on what was found
        results = context.planner.search_memory(entities, queries)

        # Extract the actual content from results
        # Note: planner.search_memory returns "results" key with the found content
        content = results.get("results", "")

        # If content is empty, try to get it from "content" key for compatibility
        if not content:
            content = results.get("content", "")

        print(f"      ✓ Found content in {len(results.get('sources', []))} entities")
        print(f"      ✓ Memory coverage: {results.get('coverage', 0.0)*100:.0f}%")
        print(f"      ✓ Information gaps identified: {len(results.get('gaps', []))}")

        # Format results for Llama to use
        return json.dumps({
            "status": "success",
            "coverage": results.get("coverage", 0.0),
            "content": content,
            "gaps": results.get("gaps", queries),  # Gaps Llama should research
            "sources": results.get("sources", entities),
            "entities_searched": results.get("entities_searched", len(entities)),
            "queries": queries
        })

    except Exception as e:
        print(f"      ✗ Memory search error: {str(e)}")
        return json.dumps({
            "status": "error",
            "error": str(e),
            "entities_searched": entities,
            "queries": queries
        })


async def handle_research(args: Dict, context: ToolExecutionContext) -> str:
    """
    Handle research tool call.

    Performs iterative web research to fill identified gaps.

    Args:
        args: {"gaps": [...], "max_iterations": int}
        context: ToolExecutionContext

    Returns:
        JSON string with research results
    """

    if not context.research_agent:
        return json.dumps({
            "status": "error",
            "error": "ResearchAgent not initialized"
        })

    gaps = args.get("gaps", [])
    max_iterations = args.get("max_iterations", 3)

    print(f"   Researching {len(gaps)} gaps (max {max_iterations} iterations)")

    if not gaps:
        return json.dumps({
            "status": "warning",
            "message": "No gaps to research"
        })

    try:
        # Call research agent
        result = await context.research_agent.research(gaps, max_iterations)

        # Format results
        return json.dumps({
            "status": "success",
            "summary": result.summary,
            "sources": result.sources,
            "key_data_points": result.key_data_points,
            "coverage": result.coverage,
            "iterations_used": result.iterations_used,
            "gaps_filled": result.gaps_filled,
            "gaps_remaining": result.gaps_remaining
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "gaps_requested": gaps
        })


async def handle_call_planner(args: Dict, context: ToolExecutionContext) -> str:
    """
    Handle call_planner tool call.

    Creates a strategic plan based on goal and context.

    Args:
        args: {"goal": str, "context": str, "approach": str (optional)}
        context: ToolExecutionContext

    Returns:
        JSON string with plan
    """

    if not context.agent:
        return json.dumps({
            "status": "error",
            "error": "Agent not initialized"
        })

    goal = args.get("goal", "")
    context_text = args.get("context", "")
    approach = args.get("approach", "")

    print(f"   Planning goal: {goal[:50]}...")

    if not goal:
        return json.dumps({
            "status": "error",
            "error": "Goal is required for planning"
        })

    try:
        # Create PlannerAgent and call generate_strategic_plan
        if PlannerAgent is None:
            # Fallback: try to call through the agent if available
            if hasattr(context.agent, 'call_tool'):
                plan_result = await context.agent.call_tool(
                    "planner",
                    {
                        "goal": goal,
                        "context": context_text,
                        "approach": approach
                    }
                )
            else:
                return json.dumps({
                    "status": "error",
                    "error": "PlannerAgent not available and agent.call_tool not found"
                })
        else:
            # Use PlannerAgent directly
            from pathlib import Path
            planner = PlannerAgent(context.agent, Path(context.memory_path))
            plan_result = planner.generate_strategic_plan(
                goal,
                {"context": context_text, "approach": approach}
            )

        # Plan result should be AgentResult dataclass
        if hasattr(plan_result, 'output'):
            plan_text = plan_result.output
        else:
            plan_text = str(plan_result)

        return json.dumps({
            "status": "success",
            "plan": plan_text,
            "reasoning": getattr(plan_result, 'reasoning', ''),
            "steps": getattr(plan_result, 'steps', []),
            "success": True
        })

    except Exception as e:
        import traceback
        return json.dumps({
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()[:500],
            "goal": goal
        })


async def handle_call_verifier(args: Dict, context: ToolExecutionContext) -> str:
    """
    Handle call_verifier tool call.

    Validates plan feasibility and provides feedback.

    Args:
        args: {"plan": str, "context": str, "criteria": str (optional)}
        context: ToolExecutionContext

    Returns:
        JSON string with verification results
    """

    if not context.agent:
        return json.dumps({
            "status": "error",
            "error": "Agent not initialized"
        })

    plan = args.get("plan", "")
    context_text = args.get("context", "")
    criteria = args.get("criteria", "")

    print(f"   Verifying plan ({len(plan)} chars)...")

    if not plan:
        return json.dumps({
            "status": "error",
            "error": "Plan is required for verification"
        })

    try:
        # Call VerifierAgent through agent
        verification = await context.agent.call_tool(
            "verifier",
            {
                "plan": plan,
                "context": context_text,
                "criteria": criteria
            }
        )

        return json.dumps({
            "status": "success",
            "is_feasible": verification.get("is_feasible", False),
            "feasibility_score": verification.get("feasibility_score", 0.0),
            "feedback": verification.get("feedback", ""),
            "risks": verification.get("risks", []),
            "suggestions": verification.get("suggestions", [])
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


async def handle_call_executor(args: Dict, context: ToolExecutionContext) -> str:
    """
    Handle call_executor tool call.

    Generates detailed implementation steps from a plan.

    Args:
        args: {"plan": str, "context": str, "resources": str (optional)}
        context: ToolExecutionContext

    Returns:
        JSON string with implementation details
    """

    if not context.agent:
        return json.dumps({
            "status": "error",
            "error": "Agent not initialized"
        })

    plan = args.get("plan", "")
    context_text = args.get("context", "")
    resources = args.get("resources", "")

    print(f"   Creating execution plan ({len(plan)} chars)...")

    if not plan:
        return json.dumps({
            "status": "error",
            "error": "Plan is required for execution details"
        })

    try:
        # Call ExecutorAgent through agent
        execution_details = await context.agent.call_tool(
            "executor",
            {
                "plan": plan,
                "context": context_text,
                "resources": resources
            }
        )

        return json.dumps({
            "status": "success",
            "steps": execution_details.get("steps", []),
            "timeline": execution_details.get("timeline", ""),
            "resource_requirements": execution_details.get("resource_requirements", {}),
            "milestones": execution_details.get("milestones", []),
            "success": True
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


async def handle_call_generator(args: Dict, context: ToolExecutionContext) -> str:
    """
    Handle call_generator tool call.

    Synthesizes and formats results from multiple sources.

    Args:
        args: {"data": str, "format": str (optional)}
        context: ToolExecutionContext

    Returns:
        JSON string with synthesized output
    """

    if not context.agent:
        return json.dumps({
            "status": "error",
            "error": "Agent not initialized"
        })

    data = args.get("data", "")
    output_format = args.get("format", "summary")

    print(f"   Generating {output_format} output...")

    if not data:
        return json.dumps({
            "status": "error",
            "error": "Data is required for generation"
        })

    try:
        # Call GeneratorAgent through agent
        generated = await context.agent.call_tool(
            "generator",
            {
                "data": data,
                "format": output_format
            }
        )

        return json.dumps({
            "status": "success",
            "output": generated.get("output", ""),
            "format": output_format,
            "quality_score": generated.get("quality_score", 0.0),
            "success": True
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "format": output_format
        })


# ============================================================================
# Execution Summary
# ============================================================================

def create_tool_executor(context: ToolExecutionContext) -> callable:
    """
    Create a tool executor function bound to a specific context.

    Returns a callable that can be passed to FireworksClient.

    Args:
        context: ToolExecutionContext with agent, planner, etc.

    Returns:
        Async callable: async def (tool_name: str, args: Dict) -> str
    """

    async def executor(tool_name: str, args: Dict) -> str:
        return await execute_tool(tool_name, args, context)

    return executor


# ============================================================================
# Main Entry Point (for testing)
# ============================================================================

if __name__ == "__main__":
    # Simple test
    print("Tool Executor Module")
    print("Available tools:")
    print("  • search_memory")
    print("  • research")
    print("  • call_planner")
    print("  • call_verifier")
    print("  • call_executor")
    print("  • call_generator")
