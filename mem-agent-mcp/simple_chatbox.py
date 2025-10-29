#!/usr/bin/env python3
"""
Enhanced Web Chatbox for MEM Agent
Supports both interactive chat AND autonomous planning loops
Works exactly like Claude Desktop MCP, but in a browser with better emoji/Unicode support.

Usage:
    1. Start model server: make run-agent
    2. Run this script: python simple_chatbox.py
    3. Open browser: http://localhost:9000

Features:
    - Regular chat mode (/api/chat endpoint)
    - Autonomous planning mode (/api/plan endpoint)
    - Full Unicode and emoji support (browser-native)
    - No MCP protocol overhead
    - Direct Agent + Orchestrator integration
"""

import asyncio
import os
import sys
import uuid
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add repo to Python path
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(REPO_ROOT, "mem-agent-mcp"))

# Import Agent and Orchestrator
try:
    from agent.agent import Agent
    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Agent: {e}")
    AGENT_AVAILABLE = False

try:
    from orchestrator.simple_orchestrator import SimpleOrchestrator
    from orchestrator.iteration_manager import IterationManager, IterationResult
    ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Orchestrator: {e}")
    ORCHESTRATOR_AVAILABLE = False

# Import Llama Planner Components (Phase 1 - New Intelligent Planning System)
try:
    from llama_planner import LlamaPlanner, PlanningApproach, PlanningOutcome
    LLAMA_PLANNER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import LlamaPlanner: {e}")
    LLAMA_PLANNER_AVAILABLE = False

try:
    from research_agent import ResearchAgent
    RESEARCH_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import ResearchAgent: {e}")
    RESEARCH_AGENT_AVAILABLE = False

try:
    from learning_tracker import LearningTracker
    LEARNING_TRACKER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import LearningTracker: {e}")
    LEARNING_TRACKER_AVAILABLE = False

try:
    from tool_definitions import get_tool_definitions
    FUNCTION_CALLING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import tool definitions: {e}")
    FUNCTION_CALLING_AVAILABLE = False

# Import Phase 2 - Fireworks Function Calling Integration
try:
    from fireworks_wrapper import FireworksClient, get_fireworks_client
    FIREWORKS_WRAPPER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import FireworksClient: {e}")
    FIREWORKS_WRAPPER_AVAILABLE = False

try:
    from tool_executor import (
        execute_tool,
        ToolExecutionContext,
        create_tool_executor
    )
    TOOL_EXECUTOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import tool_executor: {e}")
    TOOL_EXECUTOR_AVAILABLE = False

# ============================================================================
# Configuration & Platform Detection
# ============================================================================

def get_memory_path() -> str:
    """Read memory path from .memory_path file, or use default."""
    # Look for .memory_path in current directory (mem-agent-mcp)
    memory_file = Path(REPO_ROOT) / ".memory_path"
    if memory_file.exists():
        return memory_file.read_text().strip()
    # Fallback to default
    default = os.path.join(REPO_ROOT, "memory", "mcp-server")
    os.makedirs(default, exist_ok=True)
    return default

def get_backend_config() -> tuple[bool, bool]:
    """
    Detect backend based on platform.
    Returns: (use_fireworks, use_vllm)
    """
    if sys.platform == "darwin":
        # macOS: Use Fireworks AI (cloud-based)
        return True, False
    elif sys.platform == "linux":
        # Linux: Use vLLM (local H100 GPU)
        return False, True
    else:
        # Windows or other: Try Fireworks, fallback to OpenRouter
        return True, False

def get_model_name() -> str:
    """Get model name - use MLX on macOS, vLLM on Linux."""
    if sys.platform == "darwin":
        model_file = Path(REPO_ROOT) / "mem-agent-mcp" / ".mlx_model_name"
        if model_file.exists():
            return model_file.read_text().strip()
        return "mem-agent-mlx-4bit"
    return "driaforall/mem-agent"

# ============================================================================
# Session Management
# ============================================================================

sessions: Dict[str, Dict] = {}

def get_or_create_session(session_id: Optional[str] = None) -> tuple[str, Dict]:
    """Get or create a session with Agent instance."""
    if session_id is None:
        session_id = str(uuid.uuid4())

    if session_id not in sessions:
        use_fireworks, use_vllm = get_backend_config()

        sessions[session_id] = {
            "agent": Agent(
                model=get_model_name(),
                use_fireworks=use_fireworks,
                use_vllm=use_vllm,
                memory_path=get_memory_path(),
                predetermined_memory_path=False
            ),
            "orchestrator": None,
            "created_at": datetime.now().isoformat(),
            "messages": []
        }

    return session_id, sessions[session_id]

def get_or_create_orchestrator(session_id: str) -> Optional[SimpleOrchestrator]:
    """Get or create orchestrator for autonomous planning."""
    if not ORCHESTRATOR_AVAILABLE:
        return None

    _, session = get_or_create_session(session_id)

    if session["orchestrator"] is None:
        memory_path = get_memory_path()
        session["orchestrator"] = SimpleOrchestrator(
            memory_path=memory_path,
            max_iterations=15,
            strict_validation=False  # Lenient validation for autonomous mode
        )

    return session["orchestrator"]

# ============================================================================
# FastAPI App Setup
# ============================================================================

app = FastAPI(
    title="Project Jupiter Planner",
    description="Autonomous planning system with memory-augmented agents"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    """Request for regular chat"""
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Response from chat"""
    reply: str
    session_id: str
    timestamp: str

class PlanRequest(BaseModel):
    """Request for autonomous planning"""
    goal: str
    session_id: Optional[str] = None
    max_iterations: int = 9
    checkpoint_interval: int = 3

class PlanResponse(BaseModel):
    """Response from planning"""
    status: str
    iterations: int
    results: dict
    session_id: str
    timestamp: str
    execution_time: float
    # Enhanced for browser display
    plan_content: Optional[str] = None  # Full plan text to display
    web_search_results: Optional[dict] = None  # Web search with URLs
    agent_outputs: Optional[dict] = None  # Actual agent outputs

class SystemStatusResponse(BaseModel):
    """System status information"""
    agent_available: bool
    orchestrator_available: bool
    # Phase 1 - New intelligent planning system
    llama_planner_available: bool
    research_agent_available: bool
    learning_tracker_available: bool
    function_calling_available: bool
    # Phase 2 - Fireworks function calling integration
    fireworks_wrapper_available: bool
    tool_executor_available: bool
    backend: str
    memory_path: str
    sessions_active: int

# ============================================================================
# Mode Detection Helper
# ============================================================================

def parse_mode_from_message(message: str) -> tuple[str, str]:
    """
    Parse mode prefix from message.

    Returns: (mode, cleaned_message)
        mode: 'chat', 'memory', 'plan', or None (default to current)
        cleaned_message: message without the prefix

    Examples:
        "/chat Tell me about XYZ" → ('chat', 'Tell me about XYZ')
        "/memory RETRIEVE successful_patterns" → ('memory', 'RETRIEVE successful_patterns')
        "/plan Develop market strategy" → ('plan', 'Develop market strategy')
        "Tell me about XYZ" → (None, 'Tell me about XYZ')
    """
    if not message:
        return None, message

    message = message.strip()

    # Check for mode prefix
    if message.startswith('/chat '):
        return 'chat', message[6:].strip()  # Remove '/chat '
    elif message.startswith('/memory '):
        return 'memory', message[8:].strip()  # Remove '/memory '
    elif message.startswith('/plan '):
        return 'plan', message[6:].strip()  # Remove '/plan '

    # No prefix detected
    return None, message

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/status", response_model=SystemStatusResponse)
async def get_status():
    """Get system status and capabilities."""
    use_fireworks, use_vllm = get_backend_config()
    backend = "Fireworks AI (macOS)" if use_fireworks else "vLLM (Linux)" if use_vllm else "OpenRouter"

    return SystemStatusResponse(
        agent_available=AGENT_AVAILABLE,
        orchestrator_available=ORCHESTRATOR_AVAILABLE,
        # Phase 1 - New intelligent planning system availability
        llama_planner_available=LLAMA_PLANNER_AVAILABLE,
        research_agent_available=RESEARCH_AGENT_AVAILABLE,
        learning_tracker_available=LEARNING_TRACKER_AVAILABLE,
        function_calling_available=FUNCTION_CALLING_AVAILABLE,
        # Phase 2 - Fireworks function calling integration availability
        fireworks_wrapper_available=FIREWORKS_WRAPPER_AVAILABLE,
        tool_executor_available=TOOL_EXECUTOR_AVAILABLE,
        backend=backend,
        memory_path=get_memory_path(),
        sessions_active=len(sessions)
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Regular chat endpoint - interactive conversation with agent.
    Supports mode selection via /chat, /memory, or /plan prefixes.

    Examples:
        - "/chat Tell me about market trends" → Chat mode (general conversation)
        - "/memory RETRIEVE successful_patterns" → Memory mode (memory operations)
        - "/plan Create a market strategy" → Redirects to planning endpoint
    """
    if not AGENT_AVAILABLE:
        raise HTTPException(status_code=500, detail="Agent not available")

    # Parse mode from message
    detected_mode, clean_message = parse_mode_from_message(request.message)

    # If /plan prefix detected, reject (should use /api/plan endpoint)
    if detected_mode == 'plan':
        return ChatResponse(
            reply="⚠️ Plan requests should use the Planning Mode (/plan prefix). Switch to the Planning tab or use the /api/plan endpoint directly. Your message: " + clean_message,
            session_id=request.session_id or str(uuid.uuid4()),
            timestamp=datetime.now().isoformat()
        )

    session_id, session = get_or_create_session(request.session_id)
    agent = session["agent"]

    # Use cleaned message (remove prefix if present)
    message_to_send = clean_message if detected_mode else request.message

    try:
        # Call agent in thread pool (it's blocking)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, agent.chat, message_to_send)

        # Store in session history (with original message for context)
        session["messages"].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat()
        })
        session["messages"].append({
            "role": "agent",
            "content": result.reply or "No response",
            "timestamp": datetime.now().isoformat()
        })

        return ChatResponse(
            reply=result.reply or "I don't have a response.",
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        return ChatResponse(
            reply=f"Error: {str(e)}",
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )

@app.post("/api/plan", response_model=PlanResponse)
async def start_planning(request: PlanRequest):
    """
    Autonomous planning endpoint - runs multi-iteration planning loop.
    Uses the SimpleOrchestrator to coordinate 4-agent workflow with learning.
    Supports /plan prefix (optional, since this is the planning endpoint).

    Examples:
        - "Develop market entry strategy" → Directly to planning
        - "/plan Develop market strategy" → Also to planning (same as above)
        - "/chat Something" → Rejected (use /api/chat endpoint instead)
    """
    if not ORCHESTRATOR_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Orchestrator not available. Check that orchestrator module is installed."
        )

    # Parse mode from goal
    detected_mode, clean_goal = parse_mode_from_message(request.goal)

    # If /chat or /memory prefix detected, reject
    if detected_mode == 'chat':
        return PlanResponse(
            status="error",
            iterations=0,
            results={"error": "Chat requests should use Chat Mode. Use /api/chat endpoint instead."},
            session_id=request.session_id or str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            execution_time=0
        )
    elif detected_mode == 'memory':
        return PlanResponse(
            status="error",
            iterations=0,
            results={"error": "Memory operations should use Memory mode (/memory prefix). Use /api/chat endpoint with /memory prefix instead."},
            session_id=request.session_id or str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            execution_time=0
        )

    # Use cleaned goal (remove /plan prefix if present)
    goal_to_plan = clean_goal if detected_mode == 'plan' else request.goal

    session_id, session = get_or_create_session(request.session_id)

    try:
        start_time = time.time()
        orchestrator = get_or_create_orchestrator(session_id)

        # Run planning iterations in thread pool (blocking operation)
        loop = asyncio.get_running_loop()

        # ROUTE: Single iteration vs Multi-iteration planning
        if request.max_iterations > 1:
            # Multi-iteration planning with MemAgent guidance
            print(f"\n🔄 Routing to MULTI-ITERATION planning (iterations={request.max_iterations})")

            # Get proposal first (required for multi-iteration mode)
            if not hasattr(request, 'proposal') or not request.proposal:
                # Generate proposal if not provided
                print(f"Generating proposal for multi-iteration planning...")
                proposal_request = ProposalRequest(goal=goal_to_plan, session_id=session_id)
                proposal_response = await generate_proposal(proposal_request)

                if proposal_response.get('status') != 'success':
                    return PlanResponse(
                        status="error",
                        iterations=0,
                        results={"error": "Could not generate proposal for multi-iteration planning"},
                        session_id=session_id,
                        timestamp=datetime.now().isoformat(),
                        execution_time=time.time() - start_time
                    )

                proposal = proposal_response.get('proposal', '')
            else:
                proposal = request.proposal

            # Package multi-iteration planning task
            async def run_planning():
                return await loop.run_in_executor(
                    None,
                    lambda: _run_multi_iteration_planning_with_memagent(
                        orchestrator,
                        goal=goal_to_plan,
                        proposal=proposal,
                        max_iterations=request.max_iterations,
                        checkpoint_interval=getattr(request, 'checkpoint_interval', 3)
                    )
                )

        else:
            # Single iteration planning (existing mode)
            print(f"\n🎯 Routing to SINGLE-ITERATION planning")

            # Package the planning task
            async def run_planning():
                return await loop.run_in_executor(
                    None,
                    lambda: _run_planning_iterations(
                        orchestrator, goal_to_plan, request.max_iterations
                    )
                )

        results = await run_planning()

        execution_time = time.time() - start_time

        # Store in session
        session["messages"].append({
            "role": "user",
            "content": f"Plan: {request.goal}",
            "timestamp": datetime.now().isoformat()
        })
        session["messages"].append({
            "role": "agent",
            "content": f"Planning completed in {execution_time:.1f}s with {results['completed_iterations']} iterations",
            "timestamp": datetime.now().isoformat()
        })

        return PlanResponse(
            status="success" if results["success"] else "partial",
            iterations=results["completed_iterations"],
            results=results,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            execution_time=execution_time,
            plan_content=results.get("combined_plan", ""),
            web_search_results=results.get("web_search_results"),
            agent_outputs=results.get("agent_outputs")
        )

    except Exception as e:
        import traceback
        traceback.print_exc()

        return PlanResponse(
            status="error",
            iterations=0,
            results={"error": str(e)},
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            execution_time=time.time() - start_time
        )

def _run_planning_iterations(orchestrator, goal: str, max_iterations: int) -> dict:
    """
    Internal function to run planning iterations.
    Called in thread pool from /api/plan endpoint.

    This mimics what the MCP server's autonomous planning does,
    but extracts and returns actual content for browser display.
    """
    print(f"\n{'='*80}")
    print(f"🚀 STARTING AUTONOMOUS PLANNING LOOP (Chatbox Interface)")
    print(f"Goal: {goal}")
    print(f"Max iterations: {max_iterations}")
    print(f"{'='*80}\n")

    completed_iterations = 0
    iteration_results = []
    combined_plan = []
    last_agent_outputs = {}
    web_search_results = {}

    try:
        for iteration in range(1, max_iterations + 1):
            print(f"\n🔄 ITERATION {iteration}/{max_iterations}")
            print("-" * 60)

            try:
                # Get context (includes web search!)
                print(f"[Step 1/4] Retrieving context...")
                context = orchestrator._retrieve_enhanced_context(goal)
                print(f"[Step 1/4] ✅ Context retrieved")

                # Extract web search results from context
                if "web_search_results" in context:
                    web_search_results[f"iteration_{iteration}"] = context["web_search_results"]

                # Coordinate agents
                print(f"[Step 2/4] Running 4-agent workflow...")
                agent_results = orchestrator.agent_coordinator.coordinate_agentic_workflow(goal, context)
                print(f"[Step 2/4] ✅ Agents completed")

                # Extract actual content from agent results
                planner_output = ""
                verifier_output = ""
                executor_output = ""
                generator_output = ""

                # Get outputs from agent results (each is an AgentResult with .output field)
                # NOTE: No truncation - displaying full content for transparency
                if "planner" in agent_results and hasattr(agent_results["planner"], "output"):
                    planner_output = agent_results["planner"].output
                    last_agent_outputs["planner"] = planner_output  # Full output for display
                    combined_plan.append(f"## 🎯 Planner Output (Iteration {iteration})\n{planner_output}\n")

                if "verifier" in agent_results and hasattr(agent_results["verifier"], "output"):
                    verifier_output = agent_results["verifier"].output
                    last_agent_outputs["verifier"] = verifier_output  # Full output
                    combined_plan.append(f"## ✅ Verifier Analysis (Iteration {iteration})\n{verifier_output}\n")

                if "executor" in agent_results and hasattr(agent_results["executor"], "output"):
                    executor_output = agent_results["executor"].output
                    last_agent_outputs["executor"] = executor_output  # Full output
                    combined_plan.append(f"## 🚀 Executor Plan (Iteration {iteration})\n{executor_output}\n")

                if "generator" in agent_results and hasattr(agent_results["generator"], "output"):
                    generator_output = agent_results["generator"].output
                    last_agent_outputs["generator"] = generator_output  # Full output
                    combined_plan.append(f"## 📝 Generator Summary (Iteration {iteration})\n{generator_output}\n")

                # Store and process results
                print(f"[Step 3/4] Storing results to memory...")
                orchestrator.memory_manager.store_results(goal, agent_results, success=True)
                orchestrator.learning_manager.apply_learning(agent_results, "", success=True)
                print(f"[Step 3/4] ✅ Results stored and learning applied")

                # Record iteration
                completed_iterations += 1
                # Build agent status - safely handle both AgentResult objects and dicts
                agents_status = {}
                for agent_name in ["planner", "verifier", "executor", "generator"]:
                    agent_obj = agent_results.get(agent_name)
                    if agent_obj is None:
                        agents_status[agent_name] = False
                    elif hasattr(agent_obj, 'success'):
                        # AgentResult object
                        agents_status[agent_name] = agent_obj.success
                    elif isinstance(agent_obj, dict) and 'success' in agent_obj:
                        # Dict representation
                        agents_status[agent_name] = agent_obj['success']
                    else:
                        agents_status[agent_name] = False

                iteration_results.append({
                    "iteration": iteration,
                    "success": True,
                    "agents": agents_status,
                    "content_length": len(planner_output) + len(verifier_output) + len(executor_output) + len(generator_output)
                })

                print(f"[Step 4/4] ✅ ITERATION {iteration} COMPLETE\n")

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"❌ Error in iteration {iteration}: {e}")
                print(f"Details:\n{error_details}")

                iteration_results.append({
                    "iteration": iteration,
                    "success": False,
                    "error": str(e),
                    "error_details": error_details
                })

                # Record that we hit an error so chatbox can show it
                break  # Stop on error so user can decide whether to retry

        print(f"\n{'='*80}")
        print(f"✅ PLANNING LOOP COMPLETED")
        print(f"Successful iterations: {completed_iterations}/{max_iterations}")
        print(f"Total plan content: {len(''.join(combined_plan))} characters")
        print(f"{'='*80}\n")

        return {
            "success": completed_iterations > 0,
            "completed_iterations": completed_iterations,
            "total_iterations": max_iterations,
            "iterations": iteration_results,
            "goal": goal,
            "timestamp": datetime.now().isoformat(),
            "combined_plan": "\n".join(combined_plan),
            "agent_outputs": last_agent_outputs,
            "web_search_results": web_search_results
        }

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "completed_iterations": completed_iterations,
            "total_iterations": max_iterations,
            "iterations": iteration_results,
            "error": str(e),
            "goal": goal,
            "timestamp": datetime.now().isoformat(),
            "combined_plan": "\n".join(combined_plan),
            "agent_outputs": last_agent_outputs,
            "web_search_results": web_search_results
        }


def _run_multi_iteration_planning_with_memagent(orchestrator, goal: str, proposal: str,
                                               max_iterations: int, checkpoint_interval: int) -> dict:
    """
    Multi-iteration planning with MemAgent-guided refinement.

    Each iteration builds on previous through MemAgent semantic retrieval.
    Checkpoints are collected and displayed, but execution continues automatically.

    Args:
        orchestrator: SimpleOrchestrator instance
        goal: Original planning goal
        proposal: The approved proposal to build iterations from
        max_iterations: Total iterations to run (e.g., 6, 20)
        checkpoint_interval: Checkpoint every N iterations (e.g., 3)

    Returns:
        Dict with final plan, metrics, and iteration history
    """
    print(f"\n{'='*80}")
    print(f"🔄 STARTING MULTI-ITERATION PLANNING WITH MEMAGENT GUIDANCE")
    print(f"Goal: {goal}")
    print(f"Iterations: {max_iterations} (checkpoint every {checkpoint_interval})")
    print(f"{'='*80}\n")

    completed_iterations = 0
    memagent_failures = 0
    checkpoints = []
    final_result = None

    try:
        # Initialize and get generator
        from llama_planner import LlamaPlanner
        llama_planner = LlamaPlanner(orchestrator.memory_path)

        iteration_generator = orchestrator.run_iterative_planning(
            goal=goal,
            proposal=proposal,
            max_iterations=max_iterations,
            checkpoint_interval=checkpoint_interval,
            llama_planner=llama_planner
        )

        # Consume generator
        for item in iteration_generator:
            item_type = item.get('type')

            if item_type == 'error':
                # Error from generator - track failures
                memagent_failures += 1
                error_msg = item.get('message', 'Unknown error')
                print(f"\n⚠️ Iteration error: {error_msg}")

                if memagent_failures > 2:
                    # Prevent cascading failures
                    print(f"\n❌ Multiple failures detected ({memagent_failures}). Stopping iteration loop.")
                    return {
                        "success": False,
                        "completed_iterations": completed_iterations,
                        "total_iterations": max_iterations,
                        "checkpoints": checkpoints,
                        "error": f"Repeated failures: {error_msg}",
                        "goal": goal,
                        "timestamp": datetime.now().isoformat()
                    }

            elif item_type == 'checkpoint':
                # Checkpoint reached
                checkpoint_num = item.get('iteration', completed_iterations)
                print(f"\n{'='*80}")
                print(f"🎯 CHECKPOINT: Iteration {checkpoint_num}/{max_iterations}")
                print(f"{'='*80}")

                # Display checkpoint summary if available
                if 'summary' in item:
                    print(f"\n{item['summary']}\n")

                # Collect checkpoint for return
                checkpoints.append({
                    'iteration': checkpoint_num,
                    'summary': item.get('summary', ''),
                    'progress': item.get('progress', ''),
                    'metrics': item.get('metrics', {})
                })

                # Auto-approve checkpoint and continue
                print(f"✅ Auto-approving and continuing to next iterations...")

            elif item_type == 'final_plan':
                # Final result from generator
                print(f"\n{'='*80}")
                print(f"✨ SYNTHESIS COMPLETE")
                print(f"{'='*80}")

                final_result = item
                completed_iterations = item.get('iteration_count', max_iterations)

                print(f"\n📊 FINAL METRICS:")
                print(f"   Iterations completed: {completed_iterations}")
                print(f"   Unique frameworks: {item.get('unique_frameworks', 0)}")
                print(f"   Total data points: {item.get('total_data_points', 0)}")
                print(f"   Total insights: {item.get('total_insights', 0)}")

            elif item_type == 'cancelled':
                # User cancelled
                print(f"\n🛑 Planning cancelled by user")
                return {
                    "success": False,
                    "completed_iterations": completed_iterations,
                    "total_iterations": max_iterations,
                    "checkpoints": checkpoints,
                    "reason": "cancelled",
                    "goal": goal,
                    "timestamp": datetime.now().isoformat()
                }

        # Validate that we got a final result
        if final_result is None:
            print(f"\n⚠️ Generator completed without final plan")
            return {
                "success": False,
                "completed_iterations": completed_iterations,
                "total_iterations": max_iterations,
                "checkpoints": checkpoints,
                "error": "Generator did not produce final plan",
                "goal": goal,
                "timestamp": datetime.now().isoformat()
            }

        # Return final result with checkpoint history
        result = {
            "success": True,
            "completed_iterations": final_result.get('iteration_count', max_iterations),
            "total_iterations": max_iterations,
            "checkpoints": checkpoints,
            "goal": goal,
            "timestamp": datetime.now().isoformat(),
            "combined_plan": final_result.get('plan', ''),
            "unique_frameworks": final_result.get('unique_frameworks', 0),
            "total_data_points": final_result.get('total_data_points', 0),
            "total_insights": final_result.get('total_insights', 0),
            "iteration_history": final_result.get('iteration_history', []),
            "summary": final_result.get('summary', '')
        }

        print(f"\n✅ MULTI-ITERATION PLANNING COMPLETE")
        print(f"Total plan content: {len(result['combined_plan'])} characters")
        print(f"Checkpoints reached: {len(checkpoints)}")
        print(f"{'='*80}\n")

        return result

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "completed_iterations": completed_iterations,
            "total_iterations": max_iterations,
            "checkpoints": checkpoints,
            "error": str(e),
            "goal": goal,
            "timestamp": datetime.now().isoformat()
        }

# ============================================================================
# Phase 1C: New Intelligent Planning Endpoints
# ============================================================================

@app.get("/api/entities")
async def get_entities():
    """Return list of memory entities available for selection."""
    try:
        memory_path = get_memory_path()
        entities_dir = Path(memory_path) / "entities"

        entities = []
        if entities_dir.exists():
            for entity_file in entities_dir.glob("*.md"):
                name = entity_file.stem
                # Try to extract description from file (first line)
                try:
                    content = entity_file.read_text()
                    lines = content.split('\n')
                    description = lines[0].strip() if lines else ""
                except:
                    description = ""

                entities.append({
                    "name": name,
                    "description": description,
                    "path": str(entity_file.relative_to(memory_path))
                })

        return entities
    except Exception as e:
        print(f"Error getting entities: {e}")
        return []


@app.get("/api/entity-preview/{entity_name}")
async def get_entity_preview(entity_name: str):
    """
    Get preview of entity content for proposal generation.

    Returns first 500 characters + metadata for size estimation.
    """
    try:
        memory_path = get_memory_path()
        entity_path = Path(memory_path) / "entities" / f"{entity_name}.md"

        if not entity_path.exists():
            return {
                "status": "error",
                "error": f"Entity '{entity_name}' not found"
            }

        content = entity_path.read_text(encoding='utf-8')

        # Return preview (first 500 chars) + metadata
        preview = content[:500] + ("..." if len(content) > 500 else "")

        return {
            "status": "success",
            "entity_name": entity_name,
            "preview": preview,
            "total_length": len(content),
            "line_count": content.count('\n') + 1,
            "has_content": len(content.strip()) > 50
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "entity_name": entity_name
        }


# ============================================================================
# EXECUTION METADATA EXTRACTION HELPERS
# ============================================================================
# These functions extract REAL values from Fireworks execution response
# for accurate learning tracking (not placeholders)

def _extract_memory_coverage_from_execution(response: Dict[str, Any]) -> float:
    """
    Extract actual memory coverage from search_memory tool execution.

    Returns float between 0.0-1.0 representing coverage percentage from actual search.
    """
    try:
        if "execution_log" not in response:
            return 0.0

        for execution in response["execution_log"]:
            if execution.get("tool") == "search_memory":
                # Parse the tool result JSON
                result_str = execution.get("result", "{}")
                if isinstance(result_str, str):
                    result = json.loads(result_str)
                else:
                    result = result_str

                # Extract coverage from the search_memory result
                coverage = result.get("coverage", 0.0)
                print(f"   ✓ Found search_memory coverage: {coverage*100:.0f}%")
                return float(coverage)

        # If no search_memory tool was called, return 0
        print(f"   ⚠️  No search_memory tool execution found")
        return 0.0

    except Exception as e:
        print(f"   ⚠️  Error extracting memory coverage: {e}")
        return 0.0


def _extract_research_coverage_from_execution(response: Dict[str, Any]) -> float:
    """
    Extract actual research coverage from research tool execution.

    Returns float between 0.0-1.0 representing coverage percentage from research.
    """
    try:
        if "execution_log" not in response:
            return 0.0

        for execution in response["execution_log"]:
            if execution.get("tool") == "research":
                # Parse the tool result JSON
                result_str = execution.get("result", "{}")
                if isinstance(result_str, str):
                    result = json.loads(result_str)
                else:
                    result = result_str

                # Extract coverage from the research result
                coverage = result.get("coverage", 0.0)
                print(f"   ✓ Found research coverage: {coverage*100:.0f}%")
                return float(coverage)

        # If no research tool was called, return 0
        print(f"   ⚠️  No research tool execution found")
        return 0.0

    except Exception as e:
        print(f"   ⚠️  Error extracting research coverage: {e}")
        return 0.0


def _extract_agents_called_from_execution(response: Dict[str, Any]) -> List[str]:
    """
    Extract which agents were actually called during execution.

    Returns list of agent names that were actually invoked.
    """
    try:
        agents_called = set()

        if "execution_log" not in response:
            return []

        for execution in response["execution_log"]:
            tool_name = execution.get("tool", "")

            # Map tool names to agent names
            if tool_name == "call_planner":
                agents_called.add("planner")
            elif tool_name == "call_verifier":
                agents_called.add("verifier")
            elif tool_name == "call_executor":
                agents_called.add("executor")
            elif tool_name == "call_generator":
                agents_called.add("generator")

        result = sorted(list(agents_called))
        print(f"   ✓ Agents actually called: {', '.join(result) if result else 'none'}")
        return result

    except Exception as e:
        print(f"   ⚠️  Error extracting agents called: {e}")
        return []


def _calculate_execution_time_from_response(response: Dict[str, Any]) -> int:
    """
    Calculate total execution time from response metadata.

    Returns time in milliseconds as integer.
    """
    try:
        # If response has timing info, use it
        if "execution_time_ms" in response:
            return int(response["execution_time_ms"])

        # Otherwise, return 0 (timing not tracked in current response format)
        # In future, we could track timestamps in execution_log
        return 0

    except Exception as e:
        print(f"   ⚠️  Error calculating execution time: {e}")
        return 0


def _generate_goal_specific_queries(goal: str) -> List[str]:
    """
    Generate intelligent, goal-specific search queries.

    Instead of generic queries, this creates queries tailored to what the goal actually needs.
    It identifies data types, metrics, and context that would be relevant.

    Returns list of targeted search queries.
    """
    goal_lower = goal.lower()
    queries = []

    # Always include the goal itself
    queries.append(goal)

    # Identify goal characteristics and generate targeted queries
    # GROWTH/STRATEGY GOALS
    if any(word in goal_lower for word in ["growth", "strategy", "expand", "scale"]):
        queries.extend([
            "revenue metrics and growth rates",
            "customer acquisition cost (CAC) and lifetime value (LTV)",
            "market size and expansion opportunities",
            "competitive analysis and positioning",
            "historical growth patterns and trends",
            "resource allocation and budget constraints"
        ])

    # PLANNING/EXECUTION GOALS
    if any(word in goal_lower for word in ["plan", "launch", "implement", "execute", "roadmap"]):
        queries.extend([
            "timeline and milestones",
            "resource requirements and dependencies",
            "implementation approach and methodology",
            "risk assessment and mitigation",
            "success metrics and KPIs",
            "stakeholder requirements"
        ])

    # DATA/ANALYSIS GOALS
    if any(word in goal_lower for word in ["analyze", "analyze", "research", "data", "market"]):
        queries.extend([
            "current market trends and data",
            "key metrics and benchmarks",
            "industry standards and comparisons",
            "recent developments and changes",
            "data sources and validation",
            "statistical patterns"
        ])

    # FINANCIAL GOALS
    if any(word in goal_lower for word in ["budget", "revenue", "cost", "pricing", "financial", "roi"]):
        queries.extend([
            "financial metrics and ratios",
            "budget allocation and constraints",
            "pricing models and strategies",
            "revenue streams and forecasts",
            "cost optimization opportunities",
            "profitability analysis"
        ])

    # PRODUCT/FEATURE GOALS
    if any(word in goal_lower for word in ["product", "feature", "build", "develop", "release"]):
        queries.extend([
            "user requirements and personas",
            "competitive feature comparison",
            "technical implementation approach",
            "user feedback and pain points",
            "release timeline and phases",
            "success criteria"
        ])

    # MARKETING/SALES GOALS
    if any(word in goal_lower for word in ["marketing", "sales", "customer", "engagement", "retention"]):
        queries.extend([
            "customer segments and personas",
            "marketing channels and effectiveness",
            "sales cycle and conversion rates",
            "customer acquisition and retention",
            "engagement metrics",
            "competitive marketing strategies"
        ])

    # OPERATIONAL GOALS
    if any(word in goal_lower for word in ["optimize", "efficiency", "process", "system", "workflow"]):
        queries.extend([
            "current process and bottlenecks",
            "best practices and standards",
            "performance metrics and benchmarks",
            "automation opportunities",
            "resource utilization",
            "system requirements"
        ])

    # Add universal queries for all goals
    queries.extend([
        "metrics and KPIs",
        "performance indicators",
        "success criteria",
        "key data points and numbers"
    ])

    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        q_lower = q.lower()
        if q_lower not in seen:
            seen.add(q_lower)
            unique_queries.append(q)

    return unique_queries


class ProposalRequest(BaseModel):
    """Request for generating a planning proposal."""
    goal: str
    selected_entities: List[str]
    selected_agents: List[str] = []  # planner, verifier, executor, generator
    session_id: Optional[str] = None


@app.post("/api/generate-proposal")
async def generate_proposal(request: ProposalRequest):
    """
    Generate a 200-300 word planning proposal with ACTUAL memory search.

    KEY: This does REAL memory search to calculate actual coverage percentages.
    We don't estimate - we search the selected entities and see what we find.
    This is a critical part of the memory-first approach.

    Process:
    1. Initialize LlamaPlanner (memory search tool, not LLM)
    2. Generate intelligent queries from the goal
    3. Search selected entities for relevant information
    4. Calculate ACTUAL memory coverage based on findings
    5. Calculate research coverage as gap filler
    6. Build proposal based on real findings
    """
    print(f"\n📋 GENERATING PROPOSAL WITH ACTUAL MEMORY SEARCH...")
    print(f"Goal: {request.goal}")
    print(f"Selected entities: {request.selected_entities}")
    print(f"Selected agents: {request.selected_agents}")

    try:
        memory_path = get_memory_path()
        session_id, session = get_or_create_session(request.session_id)
        agent = session["agent"]

        # Step 1: Initialize LlamaPlanner for memory operations (NOT for LLM calls)
        # LlamaPlanner.search_memory() is a memory search tool, not an LLM tool
        planner = LlamaPlanner(agent, memory_path)

        # Step 2: LLAMA STRATEGIC ANALYSIS - Let Llama think about the goal
        # This is where Llama actually thinks strategically (1-2 minutes)
        print(f"\n🧠 PHASE 1: LLAMA STRATEGIC ANALYSIS")
        print(f"   Llama will analyze the goal and decide what to search for...")

        try:
            from fireworks import LLM

            print(f"   ⏳ Waiting for Llama strategic analysis (this takes 1-2 minutes)...")

            # Create analysis prompt for Llama
            analysis_prompt = f"""You are a strategic planning analyst analyzing a planning goal.

GOAL: {request.goal}

AVAILABLE MEMORY ENTITIES TO SEARCH:
{chr(10).join([f"  • {e}" for e in request.selected_entities])}

Your task: Analyze this goal deeply and provide strategic guidance for planning.

Respond with:
1. GOAL ANALYSIS: What does this goal require? Break down the strategic requirements.
2. KEY DATA NEEDS: What specific data points, metrics, and information do we need to find?
3. ENTITY SELECTION: Which of the available entities are most relevant? Why?
4. SEARCH STRATEGY: What specific, data-driven search queries would retrieve the right information?
5. APPROACH: How should we approach this planning effort?

Be specific and strategic. Think about what information would actually help solve this goal."""

            # Use direct Fireworks API (not call_with_tools which requires tool_executor)
            fireworks_client = get_fireworks_client()
            llm = LLM(
                model="accounts/fireworks/models/llama-v3p3-70b-instruct",
                deployment_type="serverless",
                api_key=fireworks_client.api_key
            )

            response = llm.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a strategic planning advisor. Provide deep, strategic analysis for planning goals."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )

            llama_analysis = response.choices[0].message.content
            print(f"   ✓ Strategic analysis complete ({len(llama_analysis)} chars)")

        except Exception as e:
            print(f"   ⚠️  Warning: Could not get Llama analysis: {e}")
            llama_analysis = ""

        # Step 3: Generate INTELLIGENT, GOAL-SPECIFIC queries
        # These queries are customized to what the goal actually needs
        print(f"\n🔍 PHASE 2: QUERY GENERATION")
        print(f"   Generating goal-specific search queries...")

        # Use helper function to generate smart queries tailored to this goal
        queries = _generate_goal_specific_queries(request.goal)
        print(f"   Created {len(queries)} goal-specific search queries")
        for i, q in enumerate(queries[:5], 1):
            print(f"     {i}. {q}")

        # Step 4: Search selected entities for relevant information
        print(f"\n📚 PHASE 3: MEMORY SEARCH")
        print(f"   Searching {len(request.selected_entities)} selected entities...")
        memory_results = planner.search_memory(request.selected_entities, queries)

        print(f"   ✓ Memory search complete")
        print(f"   • Coverage: {memory_results['coverage']*100:.0f}%")
        print(f"   • Entities found: {len(memory_results['sources'])}")
        print(f"   • Gaps identified: {len(memory_results['gaps'])}")

        # Step 4: Calculate ACTUAL coverage from memory search
        actual_memory_coverage = memory_results["coverage"]
        actual_research_coverage = 1.0 - actual_memory_coverage

        print(f"\n📊 ACTUAL COVERAGE (from real memory search):")
        print(f"   • Memory coverage: {actual_memory_coverage*100:.0f}%")
        print(f"   • Research coverage: {actual_research_coverage*100:.0f}%")
        print(f"   • Gaps to fill: {memory_results['gaps'][:3]}")

        # Step 5: Get entity information for display
        entity_previews = []
        for entity_name in request.selected_entities:
            try:
                entity_path = Path(memory_path) / "entities" / f"{entity_name}.md"
                if entity_path.exists():
                    content = entity_path.read_text(encoding='utf-8')
                    preview = content[:300]
                    entity_previews.append({
                        "name": entity_name,
                        "preview": preview,
                        "length": len(content),
                        "was_searched": entity_name in memory_results['sources']
                    })
            except Exception as e:
                print(f"⚠️  Could not read entity {entity_name}: {e}")

        # Step 6: Default agents if none selected
        if not request.selected_agents:
            agents_to_use = ["planner"]
        else:
            agents_to_use = request.selected_agents

        # Step 7: Generate proposal text based on ACTUAL findings
        agent_text = ", ".join(agents_to_use).title()

        # Build gap description
        gaps_str = ", ".join(memory_results['gaps'][:3]) if memory_results['gaps'] else "None identified"
        found_entities = ", ".join(memory_results['sources']) if memory_results['sources'] else "None matched queries"

        # Extract actual content found
        actual_content_found = memory_results.get('results', '')

        # Build detailed entity summary with actual content found
        entity_summaries = []
        for entity_name in memory_results['sources']:
            # Find the entity preview
            entity_info = next((e for e in entity_previews if e["name"] == entity_name), None)
            if entity_info:
                preview_text = entity_info["preview"]
                # Get first couple of sentences/bullet points as summary
                summary_lines = []
                for line in preview_text.split('\n')[:5]:
                    if line.strip() and len(line.strip()) > 10:
                        summary_lines.append(f"     • {line.strip()[:100]}")

                entity_summaries.append(f"""
📄 {entity_name} ({entity_info["length"]} chars)
   Status: ✓ RELEVANT CONTENT FOUND
   Preview of information:
{chr(10).join(summary_lines[:3])}""")

        entity_content_block = "\n".join(entity_summaries) if entity_summaries else "\n   ⊘ No relevant content found in selected entities"

        proposal = f"""
🎯 PLANNING GOAL: {request.goal}
{'='*70}

🧠 LLAMA'S STRATEGIC ANALYSIS:

{llama_analysis if llama_analysis else "[Strategic analysis could not be generated]"}

{'='*70}

📚 ACTUAL CONTENT FOUND IN YOUR MEMORY:
{entity_content_block}

📊 WHAT YOUR MEMORY PROVIDES:

✓ ENTITIES SEARCHED: {len(request.selected_entities)}
✓ ENTITIES WITH RELEVANT CONTENT: {len(memory_results['sources'])} ({found_entities})
✓ MEMORY COVERAGE: {int(actual_memory_coverage*100)}% of information needed
   └─ Your existing knowledge provides solid foundational data

⊘ INFORMATION GAPS IDENTIFIED: {len(memory_results['gaps'])} gaps requiring research
✓ RESEARCH COVERAGE: {int(actual_research_coverage*100)}%
   └─ These specific gaps will be researched: {gaps_str}

🔧 AGENTS TO USE:
  • {agent_text} - Will synthesize your memory with research findings

📋 EXECUTION PLAN (Based on Strategic Analysis):

PHASE 1: DIRECT TOOL EXECUTION
  1. Search the {len(memory_results['sources'])} entities with relevant content
  2. Extract all useful information found
  3. Research the {len(memory_results['gaps'])} identified gaps
     • Using goal-specific search queries
     • Focusing on KEY NUMBERS and current data
     • Getting benchmarks and trends

PHASE 2: LLAMA SYNTHESIS
  1. {agent_text} analyzes your memory + research findings
  2. Creates comprehensive strategic plan (3,000-4,000 words)
  3. Backs recommendations with specific data points from both sources

PHASE 3: LEARNING TRACKING
  1. Plan saved to /local-memory/plans/ for future reference
  2. Execution data tracked for pattern learning
  3. Next similar goal will benefit from what worked

📌 APPROVAL NEEDED:

This approach is based on:
• Strategic analysis of your planning goal (shown above)
• Actual findings from your {len(request.selected_entities)} selected entities
• Identification of {len(memory_results['gaps'])} specific gaps for targeted research

Ready to proceed with this approach?

{'='*70}

[APPROVE] - Execute with this approach
[ADJUST] - Tell me what to change
[REJECT] - Try a different approach
"""

        print(f"✅ Proposal generated ({len(proposal)} chars) based on actual memory search")

        return {
            "status": "success",
            "goal": request.goal,
            "proposal": proposal.strip(),
            "entity_count": len(request.selected_entities),
            "entity_names": [e["name"] for e in entity_previews],
            "memory_coverage_percent": int(actual_memory_coverage * 100),
            "research_coverage_percent": int(actual_research_coverage * 100),
            "agents_to_use": agents_to_use,
            "gaps_identified": memory_results['gaps'],
            "entities_with_content": memory_results['sources'],
            "session_id": session_id
        }

    except Exception as e:
        print(f"❌ Error generating proposal: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e),
            "goal": request.goal
        }


# ============================================================================
# OPTION C: DIRECT EXECUTION HANDLER (NOT FIREWORKS FUNCTION CALLING)
# ============================================================================
# This replaces the broken Fireworks function calling approach.
# Instead of hoping Llama uses tools, we call them directly and feed results to Llama.

async def synthesize_plan_with_llama(
    goal: str,
    execution_results: Dict[str, Any],
    fireworks_client: Any
) -> str:
    """
    Use Llama to synthesize execution results into a comprehensive plan.

    This is a SINGLE Fireworks API call (not function calling).
    Llama receives all the data and focuses on synthesis, not tool selection.

    Args:
        goal: Original planning goal
        execution_results: Results from execute_plan_direct()
        fireworks_client: Fireworks client for API call

    Returns:
        Comprehensive 3,000-4,000 word strategic plan
    """
    print(f"\n🧠 SYNTHESIS: Using Llama to generate comprehensive plan...")

    # Prepare synthesis context
    memory_findings = execution_results.get("memory_results", {}).get("results", "No memory findings")
    research_findings = execution_results.get("research_results", {}).get("summary", "No research performed")
    planner_output = execution_results.get("agent_results", {}).get("planner", {}).get("output", "")
    verifier_output = execution_results.get("agent_results", {}).get("verifier", {}).get("output", "")
    executor_output = execution_results.get("agent_results", {}).get("executor", {}).get("output", "")

    # Create synthesis prompt
    synthesis_prompt = f"""You are synthesizing a COMPREHENSIVE STRATEGIC PLAN based on thorough research and analysis.

Your job is to create an EXTENSIVE, detailed plan that is 3,000-4,000+ WORDS in length.

ORIGINAL GOAL:
{goal}

MEMORY FINDINGS (from selected entities - internal knowledge):
{memory_findings[:2000]}

RESEARCH FINDINGS (from web search - current market data):
{research_findings[:2000]}

STRATEGIC PLANNING OUTPUT (from planning agents):
{planner_output[:2000]}

PLAN VALIDATION (if performed):
{verifier_output[:1000] if verifier_output else 'No validation performed'}

EXECUTION DETAILS (if needed):
{executor_output[:1000] if executor_output else 'No execution details generated'}

REQUIREMENTS FOR YOUR PLAN:
1. MINIMUM 3,000-4,000 WORDS (this is not negotiable - extensive and thorough)
2. Directly address the planning goal with strategic depth
3. Integrate findings from both internal memory AND external research
4. Include SPECIFIC DATA POINTS, METRICS, PERCENTAGES, and BENCHMARKS
5. When citing research data or statistics, INCLUDE THE SOURCE URL in brackets [source: URL]
6. Provide clear, actionable recommendations with specific next steps
7. Well-structured with clear sections, subsections, and logical flow
8. Include implementation timeline with specific phases and milestones
9. Include success metrics and KPIs for measuring progress
10. Discuss key assumptions, risks, and mitigation strategies
11. Reference both historical context (from memory) and current market trends (from research)
12. Be thorough, detailed, and comprehensive - assume this plan will guide important strategic decisions

STRUCTURE RECOMMENDATIONS:
- Executive Summary (300-400 words)
- Situation Analysis (500-600 words) - memory findings + research context
- Strategic Opportunities (600-700 words) - gaps, market dynamics, inflection points
- Recommended Strategy & Approach (700-800 words) - detailed recommendations
- Implementation Plan (500-600 words) - phases, timeline, resources
- Success Metrics & KPIs (200-300 words)
- Risk Analysis & Mitigation (300-400 words)
- Conclusion & Next Steps (200-300 words)

NOW CREATE THE COMPREHENSIVE 3,000-4,000+ WORD STRATEGIC PLAN:
(Remember: This should be extensive, well-researched, data-backed, and include source citations)"""

    try:
        # Single Fireworks API call (no function calling)
        from fireworks import LLM

        llm = LLM(
            model="accounts/fireworks/models/llama-v3p3-70b-instruct",
            deployment_type="serverless",
            api_key=fireworks_client.api_key
        )

        response = llm.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert strategic planner synthesizing comprehensive plans from research and analysis."
                },
                {
                    "role": "user",
                    "content": synthesis_prompt
                }
            ],
            max_tokens=4096,
            temperature=0.7,
            top_p=0.9
        )

        plan = response.choices[0].message.content
        print(f"   ✓ Plan generated: {len(plan)} characters")
        return plan

    except Exception as e:
        print(f"   ❌ Synthesis error: {e}")
        import traceback
        traceback.print_exc()
        return f"Error synthesizing plan: {str(e)}"


async def execute_plan_direct(
    goal: str,
    selected_entities: List[str],
    selected_agents: List[str],
    planner: Any,
    research_agent: Any,
    agent: Any
) -> Dict[str, Any]:
    """
    Execute planning using direct tool calls (Option C).

    This function:
    1. Calls search_memory DIRECTLY (memory-first pattern)
    2. Calls research DIRECTLY (targeted data search)
    3. Calls planning agents DIRECTLY (guaranteed execution)
    4. Collects all results for Llama synthesis
    5. Returns complete context for plan generation

    Returns:
        Dictionary with:
        - memory_results: What was found in memory
        - research_results: What was researched
        - agent_results: What agents recommended
        - execution_metadata: Real values (coverage %, agents called, etc.)
    """
    print(f"\n{'='*70}")
    print(f"⚡ OPTION C EXECUTION (Direct Tool Calls)")
    print(f"{'='*70}")

    execution_results = {
        "memory_results": None,
        "research_results": None,
        "agent_results": {},
        "execution_metadata": {},
        "errors": []
    }

    try:
        # STEP 1: DIRECT MEMORY SEARCH (Memory-First Pattern)
        print(f"\n📚 STEP 1: Searching selected memory entities...")
        print(f"   Entities: {', '.join(selected_entities)}")

        memory_results = planner.search_memory(selected_entities, [
            goal,
            "key metrics and benchmarks",
            "performance indicators",
            "strategic analysis",
            "market data"
        ])

        execution_results["memory_results"] = memory_results
        actual_memory_coverage = memory_results.get("coverage", 0.0)

        print(f"   ✓ Memory coverage: {actual_memory_coverage*100:.0f}%")
        print(f"   ✓ Entities with content: {len(memory_results.get('sources', []))}")
        print(f"   ✓ Gaps identified: {len(memory_results.get('gaps', []))}")

        # STEP 2: DIRECT RESEARCH (Fill Identified Gaps)
        print(f"\n🌐 STEP 2: Researching identified gaps...")
        gaps_to_research = memory_results.get('gaps', [])[:5]  # Top 5 gaps

        research_results = None
        actual_research_coverage = 0.0

        if gaps_to_research and research_agent:
            try:
                # research() is synchronous, NOT async - don't await it
                research_results = research_agent.research(gaps_to_research, max_iterations=3)
                execution_results["research_results"] = {
                    "summary": research_results.summary,
                    "sources": research_results.sources,
                    "key_data_points": research_results.key_data_points,
                    "coverage": research_results.coverage,
                    "iterations_used": research_results.iterations_used,
                    "gaps_filled": research_results.gaps_filled,
                    "gaps_remaining": research_results.gaps_remaining
                }
                actual_research_coverage = research_results.coverage

                print(f"   ✓ Research coverage: {actual_research_coverage*100:.0f}%")
                print(f"   ✓ Sources found: {len(research_results.sources)}")
                print(f"   ✓ Key data points: {len(research_results.key_data_points)}")
            except Exception as e:
                print(f"   ⚠️  Research error: {e}")
                execution_results["research_results"] = None
                execution_results["errors"].append(f"Research failed: {str(e)}")
        else:
            print(f"   ⚠️  No gaps to research or research agent unavailable")
            actual_research_coverage = 0.0
            execution_results["research_results"] = None

        # STEP 3: DIRECT AGENT CALLS (Planning)
        print(f"\n🤖 STEP 3: Calling planning agents...")
        print(f"   Selected agents: {', '.join(selected_agents)}")

        agents_called = []
        research_summary = ""
        if research_results:
            # research_results is still a ResearchResult dataclass here, not a dict
            # Use the dataclass attributes directly, not .get()
            research_summary = research_results.summary[:1000]

        combined_context = f"""
GOAL: {goal}

MEMORY FINDINGS:
{memory_results.get('results', 'No memory findings')[:1000]}

RESEARCH FINDINGS:
{research_summary if research_summary else 'No research performed'}

IDENTIFIED GAPS:
{', '.join(gaps_to_research) if gaps_to_research else 'All gaps filled'}
"""

        # Call Planner Agent (always)
        if 'planner' in selected_agents or True:  # Always call planner
            try:
                print(f"   • Calling PlannerAgent...")
                from pathlib import Path
                from orchestrator.agents import PlannerAgent

                planning_agent = PlannerAgent(agent, str(Path(planner.memory_path)))
                planner_result = planning_agent.generate_strategic_plan(
                    goal,
                    {"context": combined_context}
                )
                # Convert AgentResult dataclass to dict for consistent access
                execution_results["agent_results"]["planner"] = {
                    "success": planner_result.success,
                    "output": planner_result.output,
                    "metadata": planner_result.metadata,
                    "timestamp": planner_result.timestamp
                }
                agents_called.append("planner")
                print(f"     ✓ PlannerAgent completed")
            except Exception as e:
                print(f"     ⚠️  PlannerAgent error: {e}")
                execution_results["errors"].append(f"Planner error: {str(e)}")

        # Call Verifier Agent (if selected)
        if 'verifier' in selected_agents:
            try:
                print(f"   • Calling VerifierAgent...")
                from orchestrator.agents import VerifierAgent

                verifier_agent = VerifierAgent(agent, str(Path(planner.memory_path)))
                verifier_result = verifier_agent.verify_plan(
                    execution_results["agent_results"].get("planner", {}).get("output", ""),
                    {"context": combined_context}
                )
                # Convert AgentResult dataclass to dict for consistent access
                execution_results["agent_results"]["verifier"] = {
                    "success": verifier_result.success,
                    "output": verifier_result.output,
                    "metadata": verifier_result.metadata,
                    "timestamp": verifier_result.timestamp
                }
                agents_called.append("verifier")
                print(f"     ✓ VerifierAgent completed")
            except Exception as e:
                print(f"     ⚠️  VerifierAgent error: {e}")

        # Call Executor Agent (if selected)
        if 'executor' in selected_agents:
            try:
                print(f"   • Calling ExecutorAgent...")
                from orchestrator.agents import ExecutorAgent

                executor_agent = ExecutorAgent(agent, str(Path(planner.memory_path)))
                # ExecutorAgent.execute_plan takes: plan (str), goal (str)
                executor_result = executor_agent.execute_plan(
                    plan=execution_results["agent_results"].get("planner", {}).get("output", ""),
                    goal=goal
                )
                # Convert AgentResult dataclass to dict for consistent access
                execution_results["agent_results"]["executor"] = {
                    "success": executor_result.success,
                    "output": executor_result.output,
                    "metadata": executor_result.metadata,
                    "timestamp": executor_result.timestamp
                }
                agents_called.append("executor")
                print(f"     ✓ ExecutorAgent completed")
            except Exception as e:
                print(f"     ⚠️  ExecutorAgent error: {e}")

        # STEP 4: Prepare Execution Metadata (REAL VALUES)
        print(f"\n📊 STEP 4: Preparing execution metadata...")

        execution_results["execution_metadata"] = {
            "memory_coverage": actual_memory_coverage,  # REAL - from search
            "research_coverage": actual_research_coverage,  # REAL - from research
            "agents_called": agents_called,  # REAL - what we actually called
            "entities_searched": selected_entities,
            "gaps_identified": len(gaps_to_research),
            "execution_status": "success"
        }

        print(f"   ✓ Memory coverage: {actual_memory_coverage*100:.0f}%")
        print(f"   ✓ Research coverage: {actual_research_coverage*100:.0f}%")
        print(f"   ✓ Agents called: {', '.join(agents_called) if agents_called else 'none'}")

        return execution_results

    except Exception as e:
        print(f"\n❌ Execution error: {e}")
        import traceback
        traceback.print_exc()
        execution_results["errors"].append(f"Critical error: {str(e)}")
        return execution_results


class SaveEntityRequest(BaseModel):
    """Request model for saving a plan as an entity."""
    goal: str
    plan_content: str
    entity_name: Optional[str] = None  # If not provided, generate from goal
    session_id: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Request model for approach approval."""
    approach: dict
    status: str  # approved, rejected, adjusted
    adjustment: Optional[str] = None
    session_id: Optional[str] = None


@app.post("/api/save-entity")
async def save_entity(request: SaveEntityRequest):
    """Save a completed plan as a new entity in memory."""
    try:
        memory_path = get_memory_path()

        # Generate entity name if not provided
        if request.entity_name:
            entity_name = request.entity_name
        else:
            # Generate from goal: use first 50 chars, replace spaces with underscores
            slug = request.goal[:50].lower().replace(' ', '_').replace('/', '_').replace('\\', '_')
            # Add timestamp for uniqueness
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            entity_name = f"plan_{slug}_{timestamp}"

        # Ensure .md extension
        if not entity_name.endswith('.md'):
            entity_name += '.md'

        entity_path = Path(memory_path) / "entities" / entity_name

        # Create entities directory if it doesn't exist
        entity_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare content with metadata
        from datetime import datetime as dt
        created_time = dt.now().isoformat()
        content = f"""# Planning Result: {request.goal}

**Created:** {created_time}
**Status:** Completed

## Plan

{request.plan_content}

---
*This entity was generated by the automated planning system.*
"""

        # Write to file
        entity_path.write_text(content, encoding='utf-8')

        print(f"✅ Plan saved as entity: {entity_name}")

        return {
            "status": "success",
            "entity_name": entity_name,
            "entity_path": str(entity_path),
            "message": f"Plan saved as new entity: {entity_name}",
            "session_id": request.session_id
        }

    except Exception as e:
        print(f"❌ Error saving entity: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e),
            "goal": request.goal
        }


@app.post("/api/approve-approach")
async def approve_approach(request: ApprovalRequest):
    """Handle user approval/rejection/adjustment of planning approach."""
    session_id, session = get_or_create_session(request.session_id)

    if request.status == "approved":
        # Mark approach as approved and ready for execution
        session["pending_approval"] = None
        session["approach_status"] = "approved"
        return {
            "status": "approved",
            "session_id": session_id,
            "message": "Approach approved. Executing plan..."
        }

    elif request.status == "rejected":
        # User rejected the approach
        session["pending_approval"] = None
        session["approach_status"] = "rejected"
        return {
            "status": "rejected",
            "session_id": session_id,
            "message": "Approach rejected. Please try a different goal."
        }

    elif request.status == "adjusted":
        # User provided adjustment feedback
        session["pending_approval"] = None
        session["user_adjustment"] = request.adjustment
        session["approach_status"] = "adjusted"
        return {
            "status": "adjusted",
            "adjustment": request.adjustment,
            "session_id": session_id,
            "message": "Adjustment received. Revising approach..."
        }

    return {
        "status": "error",
        "session_id": session_id,
        "message": "Invalid approval status"
    }


class ExecutePlanRequest(BaseModel):
    """Request model for executing plan with Llama decision-making."""
    goal: Optional[str] = None
    selected_entities: List[str] = []
    session_id: Optional[str] = None
    approval_status: Optional[str] = None  # "approved", "adjusted", "rejected"
    adjusted_approach: Optional[str] = None  # User adjustments to approach
    proposal_only: bool = False  # If True, only propose without executing tools
    selected_agents: List[str] = []  # Which agents to use: ["planner", "verifier", "executor", "generator"]
    max_iterations: int = 1  # Multi-iteration planning support (1 = single iteration)
    checkpoint_interval: int = 3  # Checkpoint every N iterations (for multi-iteration mode)
    proposal: Optional[str] = None  # Approved proposal for multi-iteration mode


@app.post("/api/execute-plan")
async def execute_plan(request: ExecutePlanRequest):
    """
    Execute planning with Llama as intelligent decision-maker.

    Flow:
    1. Initialize LlamaPlanner with agent
    2. Load Llama's system prompt
    3. Call Fireworks with function calling
    4. Handle tool calls and results
    5. Show approval gate when approach is proposed
    6. Continue execution after approval
    7. Log outcome for learning

    Returns:
    - status: "success" or "awaiting_approval" or "error"
    - If awaiting_approval: approach data for approval gate UI
    - If success: final plan and results
    """

    if not LLAMA_PLANNER_AVAILABLE:
        return {
            "status": "error",
            "session_id": request.session_id or "unknown",
            "error": "LlamaPlanner not available"
        }

    if not FIREWORKS_WRAPPER_AVAILABLE:
        return {
            "status": "error",
            "session_id": request.session_id or "unknown",
            "error": "Fireworks wrapper not available"
        }

    session_id, session = get_or_create_session(request.session_id)
    agent = session["agent"]
    memory_path = get_memory_path()

    print(f"\n{'='*80}")
    print(f"🎯 EXECUTE PLAN")
    print(f"{'='*80}")

    # Check if this is an approval continuation
    if request.approval_status == "approved":
        print(f"✅ User approved approach - continuing execution...")
        if "pending_proposal" in session and session["pending_proposal"]:
            print(f"Resuming with stored proposal")
        request.goal = session.get("current_goal", request.goal)
        request.selected_entities = session.get("current_entities", request.selected_entities)

    print(f"Goal: {request.goal}")
    print(f"Selected entities: {request.selected_entities}")
    print(f"Session: {session_id}")

    # ROUTE: Check if multi-iteration planning is requested
    if request.max_iterations and request.max_iterations > 1:
        print(f"\n🔄 Routing to MULTI-ITERATION planning (iterations={request.max_iterations})")

        # For multi-iteration, we need a proposal
        if not request.proposal:
            print(f"⚠️ Multi-iteration mode requires a proposal. Generating...")
            proposal_request = ProposalRequest(goal=request.goal, session_id=session_id)
            proposal_response = await generate_proposal(proposal_request)

            if proposal_response.get('status') != 'success':
                return {
                    "status": "error",
                    "session_id": session_id,
                    "error": "Could not generate proposal for multi-iteration planning"
                }

            proposal = proposal_response.get('proposal', '')
        else:
            proposal = request.proposal

        # Use the multi-iteration planning flow
        orchestrator = get_or_create_orchestrator(session_id)
        from llama_planner import LlamaPlanner
        llama_planner = LlamaPlanner(orchestrator.memory_path)

        loop = asyncio.get_running_loop()

        async def run_planning():
            return await loop.run_in_executor(
                None,
                lambda: _run_multi_iteration_planning_with_memagent(
                    orchestrator,
                    goal=request.goal,
                    proposal=proposal,
                    max_iterations=request.max_iterations,
                    checkpoint_interval=request.checkpoint_interval
                )
            )

        results = await run_planning()

        return PlanResponse(
            status="success" if results.get('success') else "error",
            iterations=results.get('completed_iterations', 0),
            results=results,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            execution_time=0.0,
            plan_content=results.get('combined_plan', ''),
            web_search_results=results.get('web_search_results')
        )

    try:
        # Step 1: Initialize LlamaPlanner
        print(f"\n📋 Initializing LlamaPlanner...")
        planner = LlamaPlanner(agent, memory_path)

        # Step 2: Load system prompt
        print(f"📖 Loading system prompt...")
        prompt_path = Path(REPO_ROOT) / "llama_planner_prompt.txt"
        if prompt_path.exists():
            system_prompt = prompt_path.read_text()
        else:
            # Fallback prompt if file not found
            system_prompt = "You are Llama 3.3 70B, a strategic planning assistant."

        # Step 3: Get tool definitions
        print(f"🔧 Loading tool definitions...")
        tools = get_tool_definitions()

        # Step 4: Create initial message
        # CRITICAL: Tell Llama this is EXECUTION MODE (approval already given)
        # Do NOT tell it to propose - tell it to execute immediately
        initial_message = f"""
EXECUTION APPROVED - EXECUTE IMMEDIATELY

Goal: {request.goal}

Selected memory entities: {', '.join(request.selected_entities) if request.selected_entities else 'None'}

You have user approval to execute. Use the available tools to:
1. Search your selected memory entities
2. Research data gaps aggressively (focus on KEY NUMBERS and current data)
3. Call planning agents with complete context
4. Deliver a comprehensive 3,000-4,000 word plan

START EXECUTING NOW. Do not propose or ask for approval. Execute with the tools provided.
        """.strip()

        messages = [
            {"role": "user", "content": initial_message}
        ]

        # Step 5: Initialize ResearchAgent for direct execution
        print(f"⚙️  Initializing ResearchAgent...")
        try:
            research_agent = ResearchAgent(verbose=False)
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize ResearchAgent: {e}")
            research_agent = None

        # ========================================================================
        # OPTION C: HYBRID EXECUTION ARCHITECTURE
        # ========================================================================
        # 1. Direct tool calls (guaranteed execution)
        # 2. Llama synthesis (intelligent planning)
        # 3. Real metadata collection for learning
        # ========================================================================

        print(f"\n🚀 OPTION C: Hybrid Execution Starting...")
        print(f"   Phase 1: Direct tool execution (memory → research → agents)")
        print(f"   Phase 2: Llama synthesis (intelligent planning)")
        print(f"   Phase 3: Metadata collection (learning tracking)")

        # Phase 1: Direct Tool Execution
        print(f"\n📋 PHASE 1: Direct Tool Execution")
        print(f"{'='*60}")

        execution_results = await execute_plan_direct(
            goal=request.goal,
            selected_entities=request.selected_entities,
            selected_agents=["planner", "verifier", "executor"] if not request.proposal_only else [],
            planner=planner,
            research_agent=research_agent,
            agent=agent
        )

        # Check for critical errors
        if execution_results["errors"]:
            print(f"\n⚠️  Execution errors detected:")
            for error in execution_results["errors"]:
                print(f"   • {error}")

        # Get Fireworks client for synthesis
        try:
            fireworks_client = get_fireworks_client()
        except Exception as e:
            return {
                "status": "error",
                "session_id": session_id,
                "error": f"Failed to initialize Fireworks client: {str(e)}"
            }

        # Phase 2: Llama Synthesis
        print(f"\n🧠 PHASE 2: Llama Synthesis")
        print(f"{'='*60}")

        final_plan = await synthesize_plan_with_llama(
            goal=request.goal,
            execution_results=execution_results,
            fireworks_client=fireworks_client
        )

        print(f"✓ Synthesis complete: {len(final_plan)} characters")

        # Phase 3: Metadata Collection and Learning
        print(f"\n💾 PHASE 3: Saving to Memory with Real Metadata")
        print(f"{'='*60}")

        # Extract REAL metadata from execution results
        actual_memory_coverage = execution_results["execution_metadata"]["memory_coverage"]
        actual_research_coverage = execution_results["execution_metadata"]["research_coverage"]
        actual_agents_called = execution_results["execution_metadata"]["agents_called"]

        print(f"   ✓ Memory coverage: {actual_memory_coverage*100:.0f}%")
        print(f"   ✓ Research coverage: {actual_research_coverage*100:.0f}%")
        print(f"   ✓ Agents called: {', '.join(actual_agents_called) if actual_agents_called else 'none'}")

        # Prepare execution metadata for learning tracking (REAL values)
        execution_metadata = {
            "entities_searched": request.selected_entities,
            "memory_coverage": actual_memory_coverage,  # REAL - from direct execution
            "research_percentage": actual_research_coverage,  # REAL - from direct execution
            "agents_called": actual_agents_called,  # REAL - what was actually called
            "gaps_identified": execution_results["execution_metadata"].get("gaps_identified", 0),
            "execution_status": "success"
        }

        # Save the plan using LlamaPlanner's save_plan method (MemAgent pattern)
        save_result = planner.save_plan(
            goal=request.goal,
            plan_content=final_plan,
            execution_metadata=execution_metadata
        )

        # Check if save was successful
        if save_result["status"] == "success":
            print(f"✅ Plan saved to memory with real metadata")
            print(f"   • Plan ID: {save_result.get('plan_id')}")
            print(f"   • Location: /local-memory/plans/")

            return {
                "status": "success",
                "session_id": session_id,
                "goal": request.goal,
                "selected_entities": request.selected_entities,
                "final_plan": final_plan,
                "plan_length": len(final_plan),
                "plan_saved": True,
                "plan_id": save_result.get("plan_id"),
                "plan_filename": save_result.get("plan_filename"),
                "learning_tracked": save_result.get("learning_entity_saved", False),
                "metadata": {
                    "memory_coverage": actual_memory_coverage,
                    "research_coverage": actual_research_coverage,
                    "agents_called": actual_agents_called,
                    "gaps_identified": execution_metadata.get("gaps_identified", 0)
                },
                "message": f"✅ Planning completed! Plan saved as {save_result.get('plan_filename')}"
            }
        else:
            # Plan generation succeeded but saving failed
            print(f"⚠️  Warning: Plan generated but saving to memory failed")

            return {
                "status": "partial_success",
                "session_id": session_id,
                "goal": request.goal,
                "selected_entities": request.selected_entities,
                "final_plan": final_plan,
                "plan_length": len(final_plan),
                "plan_saved": False,
                "save_error": save_result.get("error"),
                "metadata": {
                    "memory_coverage": actual_memory_coverage,
                    "research_coverage": actual_research_coverage,
                    "agents_called": actual_agents_called
                },
                "message": "Planning completed but saving to memory failed. Check logs."
            }

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            "status": "error",
            "session_id": session_id,
            "error": str(e)
        }

# ============================================================================
# Web UI (HTML/CSS/JavaScript)
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the web interface."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Jupiter Planner</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html, body {
            height: 100%;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
                'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
        }

        body {
            background: #f9f9f9;
            display: flex;
            flex-direction: column;
        }

        .container {
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        .sidebar {
            width: 300px;
            background: white;
            border-right: 1px solid #e0e0e0;
            padding: 20px;
            overflow-y: auto;
            box-shadow: 2px 0 4px rgba(0,0,0,0.05);
        }

        .sidebar h2 {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #333;
        }

        .mode-selector {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
        }

        .mode-btn {
            flex: 1;
            padding: 10px;
            border: 2px solid #d1d5db;
            background: white;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
            color: #666;
        }

        .mode-btn.active {
            border-color: #2563eb;
            background: #eff6ff;
            color: #2563eb;
        }

        .mode-btn:hover:not(.active) {
            border-color: #9ca3af;
            background: #f9fafb;
        }

        .status-info {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 6px;
            padding: 12px;
            font-size: 12px;
            color: #166534;
            margin-bottom: 20px;
        }

        .status-info strong {
            display: block;
            margin-bottom: 4px;
        }

        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        .header {
            background: white;
            border-bottom: 1px solid #e0e0e0;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        .header h1 {
            font-size: 24px;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 4px;
        }

        .header p {
            font-size: 14px;
            color: #6b7280;
        }

        .current-mode {
            display: inline-block;
            background: #dbeafe;
            color: #1e40af;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 10px;
        }

        #chatbox {
            flex: 1;
            overflow-y: auto;
            padding: 30px;
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
        }

        .message {
            margin-bottom: 20px;
            animation: fadeIn 0.3s ease-in;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .message-label {
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .message-content {
            padding: 15px 18px;
            border-radius: 8px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 14px;
        }

        .message.user .message-label {
            color: #2563eb;
        }

        .message.user .message-content {
            background: #eff6ff;
            color: #1e40af;
        }

        .message.agent .message-label {
            color: #059669;
        }

        .message.agent .message-content {
            background: #f0fdf4;
            color: #166534;
        }

        .message.planning .message-label {
            color: #9333ea;
        }

        .message.planning .message-content {
            background: #faf5ff;
            color: #6b21a8;
        }

        .input-container {
            border-top: 1px solid #e0e0e0;
            background: white;
            padding: 20px;
            box-shadow: 0 -2px 4px rgba(0,0,0,0.05);
        }

        .input-wrapper {
            max-width: 900px;
            margin: 0 auto;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        #message-input {
            flex: 1;
            min-width: 200px;
            padding: 12px 16px;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }

        #message-input:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        .btn-group {
            display: flex;
            gap: 10px;
        }

        button {
            padding: 12px 24px;
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }

        button:hover:not(:disabled) {
            background: #1d4ed8;
        }

        button:disabled {
            background: #9ca3af;
            cursor: not-allowed;
        }

        .btn-secondary {
            background: #6b7280;
        }

        .btn-secondary:hover:not(:disabled) {
            background: #4b5563;
        }

        .loading {
            display: inline-block;
            margin-left: 5px;
        }

        .loading::after {
            content: '...';
            animation: dots 1.5s steps(4, end) infinite;
        }

        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }

        .empty-state {
            text-align: center;
            color: #9ca3af;
            margin-top: 100px;
        }

        .empty-state svg {
            width: 64px;
            height: 64px;
            margin-bottom: 16px;
            opacity: 0.5;
        }

        .empty-state p {
            font-size: 15px;
            margin-top: 10px;
        }

        .status-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #e0e0e0;
            border-top-color: #2563eb;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
            .container {
                flex-direction: column;
            }

            .sidebar {
                width: 100%;
                border-right: none;
                border-bottom: 1px solid #e0e0e0;
            }

            .main-content {
                flex: 1;
            }
        }

        /* ============================================ */
        /* ENTITY SELECTOR CSS (Phase 1B) */
        /* ============================================ */

        .sidebar-panel {
            margin-bottom: 20px;
        }

        .sidebar-panel h3 {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #333;
        }

        .search-box {
            margin-bottom: 12px;
        }

        .search-box input {
            width: 100%;
            padding: 8px;
            border: 1px solid #d1d5db;
            border-radius: 4px;
            font-size: 13px;
        }

        .entity-list {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #d1d5db;
            border-radius: 4px;
            margin-bottom: 12px;
        }

        .entity-item {
            padding: 8px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: all 0.2s;
        }

        .entity-item:hover {
            background: #f3f4f6;
        }

        .entity-item.selected {
            background: #dbeafe;
            border-left: 3px solid #2563eb;
        }

        .entity-checkbox {
            margin-right: 6px;
        }

        .agent-list {
            max-height: 250px;
            overflow-y: auto;
            border: 1px solid #d1d5db;
            border-radius: 4px;
            margin-bottom: 12px;
        }

        .agent-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: flex-start;
            gap: 8px;
        }

        .agent-item:hover {
            background: #f3f4f6;
        }

        .agent-item.selected {
            background: #dbeafe;
            border-left: 3px solid #2563eb;
        }

        .agent-checkbox {
            margin-right: 6px;
            margin-top: 3px;
        }

        .entity-controls,
        .selection-summary {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            gap: 8px;
        }

        .entity-controls button {
            flex: 1;
            padding: 6px;
            font-size: 12px;
            border: 1px solid #d1d5db;
            background: white;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .entity-controls button:hover {
            background: #f9fafb;
        }

        /* ============================================ */
        /* APPROVAL GATE MODAL CSS (Phase 1B) */
        /* ============================================ */

        .modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }

        .modal-content {
            background: white;
            border-radius: 8px;
            max-width: 600px;
            max-height: 90vh;
            overflow-y: auto;
            padding: 24px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
        }

        .modal-content h2 {
            margin-bottom: 20px;
            color: #333;
        }

        .approval-section {
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid #e5e7eb;
        }

        .approval-section h3 {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 10px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .goal-box,
        .info-box {
            padding: 12px;
            background: #f9fafb;
            border-radius: 4px;
            font-size: 13px;
            line-height: 1.5;
            color: #333;
            border-left: 3px solid #2563eb;
        }

        .approval-controls {
            display: flex;
            gap: 8px;
            margin-top: 12px;
        }

        .btn {
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-approve {
            background: #10b981;
            color: white;
        }

        .btn-approve:hover {
            background: #059669;
        }

        .btn-reject {
            background: #ef4444;
            color: white;
        }

        .btn-reject:hover {
            background: #dc2626;
        }

        .btn-adjust {
            background: #3b82f6;
            color: white;
        }

        .btn-adjust:hover {
            background: #2563eb;
        }

        .btn-confirm {
            background: #10b981;
            color: white;
        }

        .btn-cancel {
            background: #999;
            color: white;
        }

        #adjustment-text {
            width: 100%;
            padding: 8px;
            border: 1px solid #d1d5db;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            resize: vertical;
        }

        .btn-small {
            padding: 6px 10px;
            font-size: 11px;
            border: 1px solid #d1d5db;
            background: white;
            border-radius: 4px;
            cursor: pointer;
        }

        .btn-small:hover {
            background: #f9fafb;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Sidebar -->
        <div class="sidebar">
            <h2>Mode</h2>
            <div class="mode-selector">
                <button class="mode-btn active" data-mode="chat">💬 Chat</button>
                <button class="mode-btn" data-mode="plan">🎯 Plan</button>
            </div>

            <div class="status-info" id="status-info">
                <strong>System Status</strong>
                <div id="status-content">Loading...</div>
            </div>

            <!-- Entity Selector (Phase 1B) -->
            <div id="entity-selector-panel" class="sidebar-panel" style="display: none;">
                <h3>📚 Select Memory Entities</h3>

                <div class="search-box">
                    <input type="text" id="entity-search" placeholder="Search entities..."
                           onkeyup="filterEntities(this.value)">
                </div>

                <div id="entity-list" class="entity-list">
                    <!-- Populated by JavaScript -->
                </div>

                <div class="entity-controls">
                    <button class="btn-small" onclick="saveEntitySelection()">Save</button>
                    <button class="btn-small" onclick="clearEntitySelection()">Clear</button>
                </div>

                <div class="selection-summary">
                    <small id="selection-count">Selected: 0</small>
                </div>
            </div>

            <!-- Agent Selector (Phase 1D) -->
            <div id="agent-selector-panel" class="sidebar-panel" style="display: none;">
                <h3>🔧 Select Planning Agents</h3>

                <div id="agent-list" class="agent-list">
                    <!-- Populated by JavaScript -->
                </div>

                <div class="entity-controls" style="margin-top: 10px;">
                    <button class="btn-small" onclick="saveAgentSelection()">Save</button>
                </div>

                <div class="selection-summary">
                    <small id="agent-selection-count">Selected: 0</small>
                </div>
            </div>

            <h2>Planning Options</h2>
            <div id="planning-options" style="display: none;">
                <label style="display: block; margin-bottom: 10px; font-size: 13px;">
                    Max Iterations:
                    <input type="number" id="max-iterations" value="9" min="1" max="30" style="width: 100%; padding: 6px; border: 1px solid #d1d5db; border-radius: 4px; margin-top: 4px;">
                </label>
                <label style="display: block; font-size: 13px;">
                    Checkpoint Interval:
                    <input type="number" id="checkpoint-interval" value="3" min="1" max="10" style="width: 100%; padding: 6px; border: 1px solid #d1d5db; border-radius: 4px; margin-top: 4px;">
                </label>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <!-- Header -->
            <div class="header">
                <div>
                    <h1>Project Jupiter Planner <span class="current-mode" id="current-mode">Chat Mode</span></h1>
                    <p>Memory-augmented autonomous planning system</p>
                </div>
            </div>

            <!-- Chat Area -->
            <div id="chatbox">
                <div class="empty-state">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                    <p id="empty-message">Start a conversation with your memory agent</p>
                </div>
            </div>

            <!-- Input Area -->
            <div class="input-container">
                <div class="input-wrapper">
                    <input
                        type="text"
                        id="message-input"
                        placeholder="Ask me anything or describe your planning goal..."
                        autocomplete="off"
                    >
                    <div class="btn-group">
                        <button id="send-btn">Send</button>
                        <button id="clear-btn" class="btn-secondary">Clear</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Approval Gate Modal (Phase 1B) -->
        <div id="approval-gate-modal" class="modal" style="display: none;">
            <div class="modal-content">
                <h2>✨ Approve Planning Approach</h2>

                <div class="approval-section">
                    <h3>Goal</h3>
                    <div id="approval-goal" class="goal-box"></div>
                </div>

                <div class="approval-section">
                    <h3>Memory Search</h3>
                    <div id="approval-memory" class="info-box"></div>
                </div>

                <div class="approval-section">
                    <h3>Proposed Approach</h3>
                    <div id="approval-approach" class="info-box"></div>
                </div>

                <div class="approval-controls">
                    <button class="btn btn-approve" onclick="approveApproach()">✓ APPROVE</button>
                    <button class="btn btn-reject" onclick="rejectApproach()">✗ REJECT</button>
                    <button class="btn btn-adjust" onclick="toggleAdjustmentForm()">? ADJUST</button>
                </div>

                <div id="adjustment-form" style="display: none;" class="approval-section">
                    <h3>Describe Changes</h3>
                    <textarea id="adjustment-text" placeholder="Describe what you'd like to change..."
                              rows="3"></textarea>
                    <div class="approval-controls">
                        <button class="btn btn-confirm" onclick="submitAdjustment()">Send</button>
                        <button class="btn btn-cancel" onclick="toggleAdjustmentForm()">Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // State management
        let currentMode = 'chat';
        let sessionId = localStorage.getItem('mem_agent_session_id');
        const chatbox = document.getElementById('chatbox');
        const input = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        const clearBtn = document.getElementById('clear-btn');
        const modeButtons = document.querySelectorAll('.mode-btn');
        const planningOptions = document.getElementById('planning-options');
        const currentModeLabel = document.getElementById('current-mode');
        const emptyMessage = document.getElementById('empty-message');

        // Load system status
        async function loadStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                const statusContent = document.getElementById('status-content');
                statusContent.innerHTML = `
                    <strong>Backend:</strong> ${data.backend}<br>
                    <strong>Agent:</strong> ${data.agent_available ? '✅' : '❌'}<br>
                    <strong>Planning:</strong> ${data.orchestrator_available ? '✅' : '❌'}<br>
                    <strong>Sessions:</strong> ${data.sessions_active}
                `;
            } catch (error) {
                document.getElementById('status-content').textContent = 'Status unavailable';
            }
        }

        // Mode switching
        modeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                modeButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentMode = btn.dataset.mode;

                if (currentMode === 'chat') {
                    planningOptions.style.display = 'none';
                    input.placeholder = 'Ask me anything or describe your planning goal...';
                    currentModeLabel.textContent = 'Chat Mode';
                    emptyMessage.textContent = 'Start a conversation with your memory agent';
                } else {
                    planningOptions.style.display = 'block';
                    input.placeholder = 'Describe your planning goal...';
                    currentModeLabel.textContent = 'Planning Mode';
                    emptyMessage.textContent = 'Start autonomous planning iterations';
                }
            });
        });

        // Parse mode prefix from message
        function parseModePrefix(message) {
            if (message.startsWith('/chat ')) {
                return { mode: 'chat', clean: message.substring(6).trim() };
            } else if (message.startsWith('/memory ')) {
                return { mode: 'memory', clean: message.substring(8).trim() };
            } else if (message.startsWith('/plan ')) {
                return { mode: 'plan', clean: message.substring(6).trim() };
            }
            return { mode: null, clean: message };
        }

        // Send message
        async function sendMessage() {
            const userInput = input.value.trim();
            if (!userInput) return;

            input.value = '';
            sendBtn.disabled = true;
            sendBtn.innerHTML = 'Thinking<span class="loading"></span>';

            const emptyState = chatbox.querySelector('.empty-state');
            if (emptyState) emptyState.remove();

            // Check for approval commands when awaiting approval
            if (window.awaitingApproval && userInput.toUpperCase() === 'APPROVE') {
                addMessage(userInput, 'user');

                try {
                    // Send approval to continue execution
                    const response = await fetch('/api/execute-plan', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            session_id: sessionId,
                            approval_status: 'approved'
                        })
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }

                    const data = await response.json();
                    sessionId = data.session_id;
                    localStorage.setItem('mem_agent_session_id', sessionId);

                    // Handle the response (should be success status)
                    if (data.status === 'success') {
                        window.awaitingApproval = false;
                        let planContent = `✅ Planning executed successfully!\n\n${data.final_plan || 'Plan completed.'}`;
                        addMessage(planContent, 'agent');
                    } else {
                        addMessage(`Unexpected status: ${data.status}`, 'agent');
                    }

                } catch (error) {
                    addMessage(`Error: ${error.message}`, 'agent');
                } finally {
                    sendBtn.disabled = false;
                    sendBtn.textContent = 'Send';
                    input.focus();
                }
                return;
            }

            // Detect mode from prefix
            const { mode: detectedMode, clean: cleanMessage } = parseModePrefix(userInput);
            const effectiveMode = detectedMode || currentMode;

            // Display message with original input (including prefix)
            addMessage(userInput, effectiveMode === 'chat' ? 'user' : 'planning');

            try {
                if (effectiveMode === 'plan') {
                    // Phase 1: Generate proposal first (without executing tools)
                    console.log('Phase 1: Generating proposal...');
                    addMessage('🔄 Analyzing goal and generating proposal...', 'agent');

                    const proposalResponse = await fetch('/api/generate-proposal', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            goal: userInput,
                            selected_entities: selectedEntities,
                            selected_agents: selectedAgents,
                            session_id: sessionId
                        })
                    });

                    if (!proposalResponse.ok) {
                        throw new Error(`Failed to generate proposal: HTTP ${proposalResponse.status}`);
                    }

                    const proposalData = await proposalResponse.json();

                    if (proposalData.status === 'success') {
                        // Show the proposal in the modal with all breakdown details
                        showProposalModal(
                            userInput,
                            proposalData.proposal,
                            {
                                entity_count: proposalData.entity_count,
                                entity_names: proposalData.entity_names,
                                memory_coverage_percent: proposalData.memory_coverage_percent,
                                research_coverage_percent: proposalData.research_coverage_percent,
                                agents_to_use: proposalData.agents_to_use,
                                session_id: proposalData.session_id
                            }
                        );

                        // Store pending execution data
                        window.pendingExecution = {
                            goal: userInput,
                            selected_entities: selectedEntities,
                            selected_agents: selectedAgents,
                            session_id: sessionId,
                            proposal: proposalData.proposal
                        };
                    } else {
                        addMessage(`❌ Failed to generate proposal: ${proposalData.error || 'Unknown error'}`, 'agent');
                    }

                    sendBtn.disabled = false;
                    sendBtn.textContent = 'Send';
                    input.focus();
                    return;
                }

                // Chat mode
                const endpoint = '/api/chat';
                const body = {
                    message: userInput,
                    session_id: sessionId
                };

                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();
                sessionId = data.session_id;
                localStorage.setItem('mem_agent_session_id', sessionId);

                if (effectiveMode === 'chat') {
                    addMessage(data.reply, 'agent');
                } else {
                    // PLANNING MODE - Handle different statuses from /api/execute-plan
                    let planContent = '';

                    if (data.status === 'awaiting_approval') {
                        // Llama proposed an approach - show approval gate
                        planContent = `
🔍 APPROACH PROPOSAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${data.proposal || 'No proposal details available'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

To proceed, type one of:
  APPROVE - Execute the plan as proposed
  ADJUST - Tell me what to change
  REJECT - Cancel and start over
                        `.trim();

                        addMessage(planContent, 'agent');

                        // Store that we're waiting for approval
                        window.awaitingApproval = true;
                        window.pendingApprovalSessionId = data.session_id;

                    } else if (data.status === 'error') {
                        planContent = `
❌ Planning failed: ${data.message || 'Unknown error'}

Error details:
${data.error || 'No additional error information available'}
                        `.trim();
                        addMessage(planContent, 'agent');

                    } else if (data.status === 'success') {
                        // Full execution completed
                        planContent = `
✅ Planning completed successfully

📊 Execution Summary:
  • Goal: ${data.goal || 'Not specified'}
  • Selected Entities: ${data.selected_entities ? data.selected_entities.join(', ') : 'None'}
  • Tools Executed: ${data.tool_executions || 0}
  • Iterations: ${data.iterations || 0}
  • Status: ${data.status.toUpperCase()}
                        `.trim();

                        // Add the complete plan
                        planContent += `\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 COMPLETE PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`;

                        // Display the full plan content
                        if (data.final_plan && data.final_plan.trim().length > 0) {
                            planContent += `\n\n${data.final_plan}`;
                        } else {
                            planContent += `\n\n⚠️ No plan content generated.`;
                        }

                        // Add summary footer
                        planContent += `\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Session Information
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  • Session ID: ${data.session_id || 'Not available'}
  • Memory-first approach: Search entities first, research fills gaps
  • Plan grounded in: ${data.selected_entities && data.selected_entities.length > 0 ? data.selected_entities.join(', ') : 'General knowledge'}
`;
                        addMessage(planContent, 'agent');
                        window.awaitingApproval = false;
                    } else {
                        // Unknown status
                        planContent = `Unexpected response status: ${data.status}`;
                        addMessage(planContent, 'agent');
                    }
                }

            } catch (error) {
                addMessage(`Error: ${error.message}`, 'agent');
            } finally {
                sendBtn.disabled = false;
                sendBtn.textContent = 'Send';
                input.focus();
            }
        }

        // Add message to chat
        function addMessage(text, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;

            const label = document.createElement('div');
            label.className = 'message-label';
            label.textContent = sender === 'user' ? 'You' : sender === 'agent' ? 'Agent' : 'Planning';

            const content = document.createElement('div');
            content.className = 'message-content';
            content.textContent = text;

            messageDiv.appendChild(label);
            messageDiv.appendChild(content);
            chatbox.appendChild(messageDiv);
            chatbox.scrollTop = chatbox.scrollHeight;
        }

        // Event listeners
        sendBtn.addEventListener('click', sendMessage);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        clearBtn.addEventListener('click', () => {
            chatbox.innerHTML = `
                <div class="empty-state">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                    <p>${currentMode === 'chat' ? 'Start a conversation with your memory agent' : 'Start autonomous planning iterations'}</p>
                </div>
            `;
        });

        // ============================================
        // ENTITY SELECTOR JAVASCRIPT (Phase 1B)
        // ============================================

        let selectedEntities = [];

        async function initEntitySelector() {
            // Load entity list from memory directory
            try {
                const response = await fetch('/api/entities');
                const entities = await response.json();

                // Load saved selection from localStorage
                const savedSelection = localStorage.getItem('llama_selected_entities');
                selectedEntities = savedSelection ? JSON.parse(savedSelection) : [];

                // Render entity list
                renderEntityList(entities);

                // Show entity selector when in planning mode
                document.getElementById('entity-selector-panel').style.display = 'block';
            } catch (e) {
                console.error('Failed to init entity selector:', e);
            }
        }

        function renderEntityList(entities) {
            const list = document.getElementById('entity-list');
            list.innerHTML = entities.map(entity => `
                <div class="entity-item ${selectedEntities.includes(entity.name) ? 'selected' : ''}">
                    <input type="checkbox" class="entity-checkbox"
                           data-entity-name="${entity.name}"
                           ${selectedEntities.includes(entity.name) ? 'checked' : ''}>
                    <span onclick="toggleEntityBySpan('${entity.name}')">${entity.name}</span>
                    <small style="display: block; margin-top: 4px; color: #999;">
                        ${entity.description || 'No description'}
                    </small>
                </div>
            `).join('');

            // Add event listeners to checkboxes
            document.querySelectorAll('.entity-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', (e) => {
                    const entityName = checkbox.getAttribute('data-entity-name');
                    toggleEntity(entityName);
                });
            });

            updateSelectionSummary();
        }

        function toggleEntityBySpan(name) {
            const checkbox = document.querySelector(`input[data-entity-name="${name}"]`);
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                toggleEntity(name);
            }
        }

        function toggleEntity(name) {
            if (selectedEntities.includes(name)) {
                selectedEntities = selectedEntities.filter(e => e !== name);
            } else {
                selectedEntities.push(name);
            }
            saveEntitySelection();
        }

        function saveEntitySelection() {
            localStorage.setItem('llama_selected_entities', JSON.stringify(selectedEntities));
            updateSelectionSummary();
        }

        function clearEntitySelection() {
            selectedEntities = [];
            saveEntitySelection();
        }

        function filterEntities(query) {
            const items = document.querySelectorAll('.entity-item');
            items.forEach(item => {
                const name = item.textContent.toLowerCase();
                item.style.display = name.includes(query.toLowerCase()) ? 'block' : 'none';
            });
        }

        function updateSelectionSummary() {
            document.getElementById('selection-count').textContent =
                `Selected: ${selectedEntities.length}`;
        }

        // ============================================
        // AGENT SELECTOR JAVASCRIPT (Phase 1D)
        // ============================================

        let selectedAgents = [];
        const availableAgents = [
            { name: 'planner', label: 'Planner', description: 'Strategic planning specialist' },
            { name: 'verifier', label: 'Verifier', description: 'Plan validation expert' },
            { name: 'executor', label: 'Executor', description: 'Implementation details' },
            { name: 'generator', label: 'Generator', description: 'Results synthesis' }
        ];

        async function initAgentSelector() {
            try {
                // Load saved selection from localStorage
                const savedSelection = localStorage.getItem('llama_selected_agents');
                selectedAgents = savedSelection ? JSON.parse(savedSelection) : ['planner'];

                // Render agent list
                renderAgentList();

                // Show agent selector
                const agentPanel = document.getElementById('agent-selector-panel');
                if (agentPanel) {
                    agentPanel.style.display = 'block';
                }
            } catch (e) {
                console.error('Failed to init agent selector:', e);
            }
        }

        function renderAgentList() {
            const list = document.getElementById('agent-list');
            if (!list) return;

            list.innerHTML = availableAgents.map(agent => `
                <div class="agent-item ${selectedAgents.includes(agent.name) ? 'selected' : ''}">
                    <input type="checkbox" class="agent-checkbox"
                           data-agent-name="${agent.name}"
                           ${selectedAgents.includes(agent.name) ? 'checked' : ''}>
                    <div>
                        <span onclick="toggleAgentBySpan('${agent.name}')">${agent.label}</span>
                        <small style="display: block; margin-top: 4px; color: #999;">
                            ${agent.description}
                        </small>
                    </div>
                </div>
            `).join('');

            // Add event listeners to checkboxes
            document.querySelectorAll('.agent-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', (e) => {
                    const agentName = checkbox.getAttribute('data-agent-name');
                    toggleAgent(agentName);
                });
            });

            updateAgentSummary();
        }

        function toggleAgentBySpan(name) {
            const checkbox = document.querySelector(`input[data-agent-name="${name}"]`);
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                toggleAgent(name);
            }
        }

        function toggleAgent(name) {
            if (selectedAgents.includes(name)) {
                selectedAgents = selectedAgents.filter(a => a !== name);
            } else {
                selectedAgents.push(name);
            }
            saveAgentSelection();
        }

        function saveAgentSelection() {
            localStorage.setItem('llama_selected_agents', JSON.stringify(selectedAgents));
            updateAgentSummary();
        }

        function updateAgentSummary() {
            const summary = document.getElementById('agent-selection-count');
            if (summary) {
                summary.textContent = `Selected: ${selectedAgents.length}`;
            }
        }

        // ============================================
        // PROPOSAL MODAL JAVASCRIPT (Phase 2)
        // ============================================

        let pendingExecution = null;

        function showProposalModal(goal, proposal, breakdown) {
            // Store execution data
            pendingExecution = {
                goal: goal,
                proposal: proposal,
                breakdown: breakdown
            };

            // Populate modal with proposal content
            document.getElementById('approval-goal').textContent = goal;

            document.getElementById('approval-memory').innerHTML = `
                <strong>📊 Analysis</strong>
                <p><strong>Entities to search:</strong> ${breakdown.entity_names.join(', ')}</p>
                <p><strong>Memory coverage:</strong> ${breakdown.memory_coverage_percent}%</p>
                <p><strong>Research coverage:</strong> ${breakdown.research_coverage_percent}%</p>
                <p><strong>Agents:</strong> ${breakdown.agents_to_use.join(', ')}</p>
            `;

            document.getElementById('approval-approach').innerHTML = `
                <strong>📋 Proposal</strong>
                <div style="max-height: 300px; overflow-y: auto; padding: 10px; background: #f9fafb; border-radius: 4px; font-size: 13px; line-height: 1.5; white-space: pre-wrap; word-wrap: break-word;">
                    ${proposal}
                </div>
            `;

            // Show modal
            document.getElementById('approval-gate-modal').style.display = 'flex';
        }

        async function approveApproach() {
            if (!pendingExecution) {
                alert('No pending execution found');
                return;
            }

            const sendBtn = document.getElementById('send-btn');
            sendBtn.disabled = true;
            sendBtn.textContent = 'Executing...';

            try {
                // Phase 2: Execute the plan with tools
                console.log('Phase 2: Executing approved plan...');
                const response = await fetch('/api/execute-plan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        goal: pendingExecution.goal,
                        selected_entities: pendingExecution.breakdown.entity_names,
                        selected_agents: pendingExecution.breakdown.agents_to_use,
                        session_id: sessionId,
                        approval_status: 'approved'
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();
                sessionId = data.session_id;
                localStorage.setItem('mem_agent_session_id', sessionId);

                // Hide modal
                document.getElementById('approval-gate-modal').style.display = 'none';

                // Display results
                if (data.status === 'success') {
                    const chatbox = document.getElementById('chatbox');
                    let resultContent = `
✅ Planning completed successfully!

📊 Execution Summary:
  • Goal: ${data.goal || 'Not specified'}
  • Selected Entities: ${(data.selected_entities || []).join(', ')}
  • Tools Executed: ${data.tool_executions || 0}
  • Iterations: ${data.iterations || 0}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 COMPLETE PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${data.final_plan || '⚠️ No plan content generated.'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`;
                    addMessage(resultContent, 'agent');

                    // Phase 3: Save plan as entity in memory
                    console.log('Phase 3: Saving plan as entity...');
                    try {
                        const saveResponse = await fetch('/api/save-entity', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                goal: pendingExecution.goal,
                                plan_content: data.final_plan || 'Plan executed but no content generated',
                                session_id: sessionId
                            })
                        });

                        if (saveResponse.ok) {
                            const saveData = await saveResponse.json();
                            if (saveData.status === 'success') {
                                addMessage(`💾 Plan saved to memory as entity: ${saveData.entity_name}`, 'agent');
                            } else {
                                console.warn('Failed to save entity:', saveData.error);
                                addMessage('⚠️ Plan completed but could not be saved to memory.', 'agent');
                            }
                        }
                    } catch (err) {
                        console.warn('Error saving entity:', err);
                        addMessage('⚠️ Plan completed but encountered error saving to memory.', 'agent');
                    }

                    // Plan is done - reset state
                    pendingExecution = null;
                    window.awaitingApproval = false;
                } else {
                    addMessage(`❌ Execution failed: ${data.error || 'Unknown error'}`, 'agent');
                }

            } catch (error) {
                addMessage(`Error during execution: ${error.message}`, 'agent');
            } finally {
                sendBtn.disabled = false;
                sendBtn.textContent = 'Send';
                const input = document.getElementById('message-input');
                if (input) input.focus();
            }
        }

        function rejectApproach() {
            // Close modal and reset
            document.getElementById('approval-gate-modal').style.display = 'none';
            pendingExecution = null;

            // Show rejection message
            addMessage('❌ Planning approach rejected. You can enter a new goal or adjust your entity/agent selection.', 'agent');
        }

        function toggleAdjustmentForm() {
            const form = document.getElementById('adjustment-form');
            form.style.display = form.style.display === 'none' ? 'block' : 'none';
        }

        function submitAdjustment() {
            const adjustment = document.getElementById('adjustment-text').value;
            if (!adjustment.trim()) {
                alert('Please enter your adjustment request');
                return;
            }

            // Close modal
            document.getElementById('approval-gate-modal').style.display = 'none';

            // Display adjustment request
            addMessage(`🔄 Adjustment requested: ${adjustment}`, 'user');
            addMessage('⚠️ Please modify your entity/agent selection and try again with a new goal.', 'agent');

            // Reset
            pendingExecution = null;
            document.getElementById('adjustment-text').value = '';
            toggleAdjustmentForm();
        }

        // Initialize
        loadStatus();
        setInterval(loadStatus, 5000);
        input.focus();
        initEntitySelector();
        initAgentSelector();
    </script>
</body>
</html>
    """

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    if not AGENT_AVAILABLE:
        print("❌ ERROR: Agent module not available!")
        print("Make sure you're in the correct directory and dependencies are installed.")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("🚀 MEM AGENT - ENHANCED CHATBOX INTERFACE")
    print("=" * 80)
    print()
    print("Features:")
    print("  ✅ Interactive chat mode (regular agent conversations)")
    print("  ✅ Autonomous planning mode (multi-iteration loops)")
    print("  ✅ Full Unicode/emoji support (browser-native)")
    print("  ✅ No MCP protocol overhead")
    print()
    print("Requirements:")
    print("  1. Model server running: make run-agent")
    print("  2. Memory path configured: make setup")
    print()

    use_fireworks, use_vllm = get_backend_config()
    backend = "Fireworks AI (macOS)" if use_fireworks else "vLLM (Linux)" if use_vllm else "OpenRouter"
    print(f"Backend: {backend}")
    print(f"Memory: {get_memory_path()}")
    print(f"Orchestrator: {'✅ Available' if ORCHESTRATOR_AVAILABLE else '⚠️  Not available'}")
    print()
    print("Starting server on: http://localhost:9000")
    print("=" * 80)
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    )
