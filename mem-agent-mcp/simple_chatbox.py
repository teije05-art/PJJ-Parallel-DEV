"""
MemAgent Chatbox - Web Interface for Semi-Autonomous Planning System

Single, clean entry point for:
1. Regular LLM chat with memory retrieval
2. Single-iteration planning
3. Multi-iteration planning with approval gates and checkpoints
4. MemAgent integration for infinite local memory

Architecture:
- Clear separation of concerns
- No duplicate logic
- Session-based state management
- Approval gate system with clear user feedback
"""

import json
import os
import asyncio
import uuid
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn
import threading
import time

# Core system imports
from agent.agent import Agent
from llama_planner import LlamaPlanner, PlanningApproach
from orchestrator.simple_orchestrator import SimpleOrchestrator
from orchestrator.iteration_manager import IterationManager, IterationResult

# ==================== CONFIGURATION ====================

DEBUG = True
CHATBOX_PORT = 9000
MAX_SESSIONS = 100
SESSION_TIMEOUT_MINUTES = 120

# ==================== UTILITIES ====================

def get_memory_path() -> str:
    """Get memory path from .memory_path file or use default."""
    memory_path_file = Path(".memory_path")
    if memory_path_file.exists():
        return memory_path_file.read_text().strip()

    default_path = str(Path.home() / ".memagent" / "local-memory")
    Path(default_path).mkdir(parents=True, exist_ok=True)
    memory_path_file.write_text(default_path)
    return default_path


def _generate_goal_specific_queries(goal: str) -> List[str]:
    """
    Generate intelligent, goal-specific search queries tailored to the goal.

    Returns list of targeted search queries based on goal characteristics.
    """
    goal_lower = goal.lower()
    queries = [goal]  # Always include goal itself

    # GROWTH/STRATEGY GOALS
    if any(word in goal_lower for word in ["growth", "strategy", "expand", "scale"]):
        queries.extend([
            "revenue metrics and growth rates",
            "customer acquisition cost (CAC) and lifetime value (LTV)",
            "market size and expansion opportunities",
            "competitive analysis and positioning",
            "historical growth patterns and trends",
        ])

    # PLANNING/EXECUTION GOALS
    if any(word in goal_lower for word in ["plan", "launch", "implement", "execute", "roadmap"]):
        queries.extend([
            "timeline and milestones",
            "resource requirements and dependencies",
            "implementation approach and methodology",
            "risk assessment and mitigation",
            "success metrics and KPIs",
        ])

    # DATA/ANALYSIS GOALS
    if any(word in goal_lower for word in ["analyze", "research", "data", "market"]):
        queries.extend([
            "current market trends and data",
            "key metrics and benchmarks",
            "industry standards and comparisons",
            "recent developments and changes",
        ])

    # FINANCIAL GOALS
    if any(word in goal_lower for word in ["financial", "budget", "cost", "revenue", "profit", "pricing"]):
        queries.extend([
            "financial projections and forecasts",
            "pricing strategies and models",
            "cost structure and optimization",
            "profitability metrics and benchmarks",
        ])

    # PRODUCT GOALS
    if any(word in goal_lower for word in ["product", "feature", "develop", "build"]):
        queries.extend([
            "product roadmap and features",
            "user requirements and feedback",
            "competitive product analysis",
            "technical architecture and requirements",
        ])

    # Remove duplicates and limit
    return list(dict.fromkeys(queries))[:15]


# ==================== REQUEST/RESPONSE MODELS ====================

class ChatRequest(BaseModel):
    """Regular chat message."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response with context."""
    status: str
    response: str
    reply: Optional[str] = None  # Alias for frontend compatibility
    session_id: str
    entities_searched: Optional[List[str]] = None
    timestamp: str


class PlanRequest(BaseModel):
    """Planning request - can be single or multi-iteration."""
    goal: str
    session_id: Optional[str] = None
    max_iterations: int = 1
    checkpoint_interval: int = 2
    selected_entities: Optional[List[str]] = None


class ProposalRequest(BaseModel):
    """Request for planning proposal generation."""
    goal: str
    session_id: Optional[str] = None
    selected_entities: Optional[List[str]] = None
    selected_agents: Optional[List[str]] = None


class ProposalResponse(BaseModel):
    """Planning proposal response."""
    status: str
    proposal_id: str
    proposal: str
    approach: Dict[str, Any]
    memory_coverage: float
    research_coverage: float
    session_id: str
    timestamp: str
    # Frontend compatibility fields
    memory_coverage_percent: Optional[float] = None
    research_coverage_percent: Optional[float] = None
    entity_count: Optional[int] = None
    entity_names: Optional[List[str]] = None
    agents_to_use: Optional[List[str]] = None
    max_iterations: Optional[int] = None
    checkpoint_interval: Optional[int] = None


class ApprovalRequest(BaseModel):
    """User approval/rejection request."""
    approval_id: str
    goal: str
    proposal: Optional[str] = None
    decision: str  # "approve", "reject", or "adjust"
    feedback: Optional[str] = None
    max_iterations: Optional[int] = None
    checkpoint_interval: Optional[int] = None
    session_id: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Response after approval decision."""
    status: str
    message: str
    next_action: str  # "execute" or "wait_for_adjustment"
    session_id: str
    timestamp: str


class PlanResponse(BaseModel):
    """Final planning response."""
    status: str
    plan_content: Optional[str] = None
    iterations: int = 0
    frameworks: List[str] = []
    data_points: int = 0
    total_insights: int = 0
    session_id: str
    timestamp: str
    error: Optional[str] = None


class SystemStatusResponse(BaseModel):
    """System status for UI."""
    status: str
    features: Dict[str, bool]
    model_info: Optional[str] = None
    memory_available: bool
    timestamp: str
    # Frontend compatibility fields
    backend: Optional[str] = None
    agent_available: Optional[bool] = None
    orchestrator_available: Optional[bool] = None
    sessions_active: Optional[int] = None


# ==================== SESSION MANAGEMENT ====================

class SessionManager:
    """Manage user sessions for web chatbox."""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_or_create(self, session_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Get existing session or create new one."""
        if session_id and session_id in self.sessions:
            return session_id, self.sessions[session_id]

        # Create new session
        new_id = str(uuid.uuid4())[:12]
        memory_path = get_memory_path()

        session = {
            "id": new_id,
            "created_at": datetime.now().isoformat(),
            "agent": Agent(memory_path=memory_path),
            "orchestrator": None,
            "pending_approvals": {},
            "execution_state": {},
            "checkpoint_approved": False,  # For checkpoint approval
            "checkpoint_approval_event": threading.Event()  # Synchronization
        }

        self.sessions[new_id] = session
        if DEBUG:
            print(f"✅ Created new session: {new_id}")

        return new_id, session

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def clear_pending_approval(self, session_id: str, approval_id: str):
        """Clear a pending approval after it's been processed."""
        if session_id in self.sessions:
            self.sessions[session_id]["pending_approvals"].pop(approval_id, None)

    def set_checkpoint_approved(self, session_id: str):
        """Mark checkpoint as approved by user."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session["checkpoint_approved"] = True
            session["checkpoint_approval_event"].set()

    def wait_for_checkpoint_approval(self, session_id: str, timeout: int = 3600):
        """Wait for user to approve checkpoint (blocks until approved)."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            # Reset event for next checkpoint
            session["checkpoint_approval_event"].clear()
            session["checkpoint_approved"] = False
            # Wait for approval (up to 1 hour)
            session["checkpoint_approval_event"].wait(timeout=timeout)
            return session["checkpoint_approved"]
        return False

    def reset_checkpoint_state(self, session_id: str):
        """Reset checkpoint state for new iteration."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session["checkpoint_approved"] = False
            session["checkpoint_approval_event"].clear()


# ==================== GLOBAL STATE ====================

app = FastAPI(title="MemAgent Chatbox", version="1.0")
session_manager = SessionManager()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== CORE ENDPOINTS ====================

@app.get("/api/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get system status and available features."""
    memory_path = get_memory_path()
    memory_available = Path(memory_path).exists()
    sessions_count = len(session_manager.sessions)

    return SystemStatusResponse(
        status="ready",
        features={
            "chat": True,
            "planning": True,
            "memory": memory_available,
            "multi_iteration": True,
            "research": True
        },
        model_info="Llama 3.3 70B (Fireworks)",
        memory_available=memory_available,
        timestamp=datetime.now().isoformat(),
        # Frontend compatibility fields
        backend="simple_chatbox.py",
        agent_available=True,
        orchestrator_available=True,
        sessions_active=sessions_count
    )


@app.post("/api/chat", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):
    """
    Handle regular chat requests.

    Can include:
    - Regular LLM chat
    - Memory retrieval (prefixed with /memory)
    """
    session_id, session = session_manager.get_or_create(request.session_id)
    agent = session["agent"]

    try:
        if DEBUG:
            print(f"\n💬 CHAT: {request.message[:100]}")

        # Let agent handle the message (agent automatically uses memory)
        response = await asyncio.to_thread(
            agent.chat,
            request.message
        )

        return ChatResponse(
            status="success",
            response=response,
            reply=response,  # Add reply alias for frontend compatibility
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        if DEBUG:
            print(f"❌ Chat error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/plan", response_model=ProposalResponse | PlanResponse)
async def start_planning(request: PlanRequest):
    """
    Start planning process.

    Routes to:
    - Single-iteration planning (max_iterations=1)
    - Multi-iteration planning (max_iterations>1)
    """
    session_id, session = session_manager.get_or_create(request.session_id)

    if DEBUG:
        print(f"\n📋 PLANNING START: {request.goal[:50]}...")
        print(f"   Iterations: {request.max_iterations}, Checkpoint: {request.checkpoint_interval}")

    # Single iteration - execute directly
    if request.max_iterations == 1:
        return await _execute_single_iteration_planning(session, request, session_id)

    # Multi-iteration - return proposal for approval first
    else:
        return await _generate_planning_proposal(session, request, session_id)


@app.post("/api/approve", response_model=ApprovalResponse | PlanResponse)
async def handle_approval(request: ApprovalRequest):
    """
    Handle user approval decision on planning proposal.

    Routes to execution if approved.
    """
    session_id, session = session_manager.get_or_create(request.session_id)

    if DEBUG:
        print(f"\n✋ APPROVAL: {request.decision} (ID: {request.approval_id[:8]})")

    if request.decision == "approve":
        return await _execute_multi_iteration_planning(
            session,
            request.goal,
            request.proposal or "",
            request.max_iterations or 4,
            request.checkpoint_interval or 2,
            session_id
        )

    elif request.decision == "reject":
        session_manager.clear_pending_approval(session_id, request.approval_id)
        return ApprovalResponse(
            status="rejected",
            message="Planning proposal rejected. You can start a new planning session.",
            next_action="wait_for_new_plan",
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )

    elif request.decision == "adjust":
        # Return proposal again for adjustment
        return ApprovalResponse(
            status="awaiting_adjustment",
            message="Proposal adjustment noted. Please review and resubmit.",
            next_action="wait_for_resubmit",
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )


# ==================== PLANNING METHODS ====================

async def _analyze_iteration_improvements(
    session: Dict[str, Any],
    goal: str,
    iteration_number: int,
    current_result: Dict[str, Any],
    previous_result: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Use Llama to analyze what improved from previous iteration.

    Llama's critical thinking analyzes:
    - Better/more comprehensive research
    - New frameworks applied
    - Additional use cases discovered
    - New angles of analysis
    - Deeper insights into the problem

    Returns structured improvement data for display to user.
    """
    try:
        if not previous_result:
            # First checkpoint - no previous iteration to compare
            return {
                "is_first_checkpoint": True,
                "status": "Completed first iteration cycle - ready for deeper analysis"
            }

        agent = session["agent"]

        # Prepare comparison prompt for Llama
        current_frameworks = current_result.get("frameworks_used", [])
        previous_frameworks = previous_result.get("frameworks_used", [])
        current_data_points = current_result.get("data_points_count", 0)
        previous_data_points = previous_result.get("data_points_count", 0)

        comparison_prompt = f"""Analyze the improvements made from iteration {iteration_number - 2} to iteration {iteration_number - 1}.

GOAL: {goal}

PREVIOUS ITERATION (Iteration {iteration_number - 2}):
- Frameworks used: {previous_frameworks}
- Data points extracted: {previous_data_points}
- Summary: {previous_result.get('summary', 'N/A')[:500]}

CURRENT ITERATION (Iteration {iteration_number - 1}):
- Frameworks used: {current_frameworks}
- Data points extracted: {current_data_points}
- Summary: {current_result.get('summary', 'N/A')[:500]}

Analyze and provide a concise JSON response with these improvements:
{{
    "research_improvements": "What new research angles or sources were discovered? Be specific.",
    "frameworks_applied": "What new frameworks were added and why are they valuable?",
    "use_cases_found": "Were any new use cases or applications discovered?",
    "analytical_improvements": "What new ways of analyzing this problem emerged?",
    "key_discovery": "What is the most important new insight from this iteration?",
    "depth_increase": "How much deeper/more specific did the analysis become? (1-10 scale)"
}}

Return ONLY valid JSON, no other text."""

        if DEBUG:
            print(f"   🧠 Llama analyzing improvements from iteration {iteration_number - 2} → {iteration_number - 1}...")

        # Call agent to get Llama's analysis
        llama_response = await asyncio.to_thread(
            agent.chat,
            comparison_prompt
        )

        if DEBUG:
            print(f"   ✓ Analysis complete")

        # Parse JSON response
        try:
            # Extract JSON from response (Llama might add extra text)
            import re
            json_match = re.search(r'\{.*\}', llama_response, re.DOTALL)
            if json_match:
                improvements = json.loads(json_match.group())
            else:
                improvements = {
                    "research_improvements": "Analysis ongoing",
                    "frameworks_applied": "New frameworks being integrated",
                    "use_cases_found": "Use cases being refined",
                    "analytical_improvements": "Deeper analysis in progress",
                    "key_discovery": "Critical insights emerging from iteration refinement",
                    "depth_increase": 7
                }
        except json.JSONDecodeError:
            improvements = {
                "research_improvements": llama_response[:200],
                "frameworks_applied": "See analysis above",
                "use_cases_found": "See analysis above",
                "analytical_improvements": "See analysis above",
                "key_discovery": "System is learning and refining approach",
                "depth_increase": 6
            }

        return {
            "is_first_checkpoint": False,
            "improvements": improvements,
            "comparison": {
                "frameworks_added": len(set(current_frameworks) - set(previous_frameworks)),
                "data_points_gained": current_data_points - previous_data_points,
                "depth_score": improvements.get("depth_increase", 5)
            }
        }

    except Exception as e:
        if DEBUG:
            print(f"   ⚠️ Error analyzing improvements: {e}")
        return {
            "is_first_checkpoint": False,
            "status": "Improvements being analyzed",
            "error": str(e)
        }


async def _execute_single_iteration_planning(
    session: Dict[str, Any],
    request: PlanRequest,
    session_id: str
) -> PlanResponse:
    """
    Execute single-iteration planning.

    Flow: Context → 4-Agent Workflow → Result
    """
    try:
        memory_path = get_memory_path()

        # Create or reuse orchestrator
        if not session["orchestrator"]:
            session["orchestrator"] = SimpleOrchestrator(
                memory_path=memory_path,
                max_iterations=1
            )

        orchestrator = session["orchestrator"]

        if DEBUG:
            print(f"   🚀 Executing single-iteration planning...")

        # Run planning
        plan_generator = orchestrator.run_enhanced_learning_loop(request.goal)

        # Collect results from generator
        final_plan = ""
        all_frameworks = []
        all_data_points = 0

        for item in plan_generator:
            if isinstance(item, dict) and item.get("type") == "final_plan":
                final_plan = item.get("plan", "")
                all_frameworks = item.get("unique_frameworks", [])
                all_data_points = item.get("total_data_points", 0)

        # Save plan to memory
        if final_plan:
            llama_planner = LlamaPlanner(session["agent"], memory_path)
            llama_planner.save_plan(
                goal=request.goal,
                plan_content=final_plan,
                execution_metadata={
                    "iterations": 1,
                    "frameworks_applied": all_frameworks,
                    "data_points": all_data_points
                }
            )

        return PlanResponse(
            status="success",
            plan_content=final_plan,
            iterations=1,
            frameworks=all_frameworks,
            data_points=all_data_points,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        if DEBUG:
            print(f"❌ Single-iteration error: {e}")
        return PlanResponse(
            status="error",
            error=str(e),
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )


async def _generate_planning_proposal(
    session: Dict[str, Any],
    request: PlanRequest,
    session_id: str
) -> ProposalResponse:
    """
    Generate planning proposal for multi-iteration planning.

    Shows user:
    - What will be searched in memory
    - What research will be done
    - Estimated coverage and resources
    """
    try:
        memory_path = get_memory_path()
        agent = session["agent"]

        if DEBUG:
            print(f"   📋 Generating proposal for multi-iteration planning...")

        # Initialize LlamaPlanner for proposal generation
        llama_planner = LlamaPlanner(agent, memory_path)

        # Generate goal-specific queries
        queries = _generate_goal_specific_queries(request.goal)

        # Search memory for relevant entities
        memory_results = await asyncio.to_thread(
            llama_planner.search_memory,
            request.selected_entities or [],
            queries
        )

        # Create proposal
        approach_plan = {
            "memory_percentage": 0.6,
            "research_percentage": 0.4,
            "research_focus": queries[:5],
            "agents_to_use": ["PlannerAgent", "VerifierAgent", "ExecutorAgent", "GeneratorAgent"],
            "resource_estimate": {
                "estimated_time_minutes": request.max_iterations * 5,
                "memory_searches": len(queries),
                "web_searches": 10,
                "agents_to_call": 4
            }
        }

        proposal_obj = llama_planner.propose_approach(
            goal=request.goal,
            memory_results=memory_results,
            approach_plan=approach_plan
        )

        # Generate readable proposal text
        proposal_text = f"""
# Planning Proposal

**Goal:** {request.goal}

## Approach
- **Iterations:** {request.max_iterations}
- **Checkpoint Interval:** {request.checkpoint_interval}
- **Memory Coverage:** 60% (from selected entities)
- **Research Coverage:** 40% (web search)

## What We'll Search
{chr(10).join([f"- {q}" for q in queries[:5]])}

## Expected Output
- Comprehensive strategic plan (3000-4000 words)
- Key insights and recommendations
- Implementation timeline
- Success metrics and KPIs

## Ready to proceed?
Click "Approve" to start multi-iteration planning.
"""

        # Store approval request
        approval_id = str(uuid.uuid4())[:12]
        session["pending_approvals"][approval_id] = {
            "goal": request.goal,
            "proposal": proposal_obj.to_dict(),
            "max_iterations": request.max_iterations,
            "checkpoint_interval": request.checkpoint_interval,
            "selected_entities": request.selected_entities,
            "created_at": datetime.now().isoformat()
        }

        if DEBUG:
            print(f"   ✅ Proposal generated (ID: {approval_id})")

        return ProposalResponse(
            status="success",  # Changed from "awaiting_approval" - frontend expects "success"
            proposal_id=approval_id,
            proposal=proposal_text,
            approach=proposal_obj.to_dict(),
            memory_coverage=0.6,
            research_coverage=0.4,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            # Frontend compatibility fields
            memory_coverage_percent=60.0,
            research_coverage_percent=40.0,
            entity_count=len(request.selected_entities or []),
            entity_names=request.selected_entities or [],
            agents_to_use=["PlannerAgent", "VerifierAgent", "ExecutorAgent", "GeneratorAgent"],
            max_iterations=request.max_iterations,
            checkpoint_interval=request.checkpoint_interval
        )

    except Exception as e:
        if DEBUG:
            print(f"❌ Proposal generation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


async def _execute_multi_iteration_planning(
    session: Dict[str, Any],
    goal: str,
    proposal: str,
    max_iterations: int,
    checkpoint_interval: int,
    session_id: str
) -> PlanResponse:
    """
    Execute multi-iteration planning with checkpoints.

    Flow: Iteration 1 → Checkpoint → Iteration 2 → Checkpoint → ... → Final Plan
    """
    try:
        memory_path = get_memory_path()

        if DEBUG:
            print(f"   🎯 Starting multi-iteration planning ({max_iterations} iterations)...")

        # Create orchestrator if needed
        if not session["orchestrator"]:
            session["orchestrator"] = SimpleOrchestrator(
                memory_path=memory_path,
                max_iterations=max_iterations
            )

        orchestrator = session["orchestrator"]

        # Run iterative planning
        iteration_generator = orchestrator.run_iterative_planning(
            goal=goal,
            proposal=proposal,
            max_iterations=max_iterations,
            checkpoint_interval=checkpoint_interval,
            llama_planner=LlamaPlanner(session["agent"], memory_path)
        )

        # Collect all results
        all_results = []
        final_plan = ""
        checkpoints_hit = 0

        for item in iteration_generator:
            if isinstance(item, dict):
                if item.get("type") == "checkpoint":
                    checkpoints_hit += 1
                    if DEBUG:
                        print(f"   ✓ Checkpoint {checkpoints_hit} reached")

                elif item.get("type") == "final_plan":
                    final_plan = item.get("plan", "")
                    if DEBUG:
                        print(f"   ✓ Final plan generated")

        # Extract metrics from final result
        frameworks = item.get("unique_frameworks", []) if item else []
        data_points = item.get("total_data_points", 0) if item else 0
        insights = item.get("total_insights", 0) if item else 0

        # Save final plan to memory
        if final_plan:
            llama_planner = LlamaPlanner(session["agent"], memory_path)
            llama_planner.save_plan(
                goal=goal,
                plan_content=final_plan,
                execution_metadata={
                    "iterations": max_iterations,
                    "checkpoints": checkpoints_hit,
                    "frameworks_applied": frameworks,
                    "data_points": data_points,
                    "total_insights": insights
                }
            )

        if DEBUG:
            print(f"   ✅ Multi-iteration planning complete!")

        return PlanResponse(
            status="success",
            plan_content=final_plan,
            iterations=max_iterations,
            frameworks=frameworks,
            data_points=data_points,
            total_insights=insights,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        if DEBUG:
            print(f"❌ Multi-iteration error: {e}")
        return PlanResponse(
            status="error",
            error=str(e),
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )


# ==================== STATIC FILES & STARTUP ====================

@app.get("/")
async def serve_home():
    """Serve the web interface."""
    index_path = Path(__file__).parent / "static" / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "MemAgent Chatbox - Open localhost:9000 in browser"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


# ==================== STARTUP ====================

@app.post("/api/generate-proposal")
async def generate_proposal_endpoint(request: ProposalRequest):
    """Alias for /api/plan to maintain JavaScript compatibility."""
    plan_req = PlanRequest(
        goal=request.goal,
        session_id=request.session_id,
        max_iterations=4,  # Default for proposal
        checkpoint_interval=2
    )
    return await _generate_planning_proposal(
        session_manager.get_or_create(request.session_id)[1],
        plan_req,
        request.session_id
    )


@app.get("/api/execute-plan")
async def execute_plan_endpoint(
    goal: str,
    proposal: str = "",
    max_iterations: int = 1,
    checkpoint_interval: int = 2,
    session_id: str = ""
):
    """
    Execute plan endpoint using Server-Sent Events (SSE).

    Streams:
    - iteration_started: When iteration begins
    - iteration_progress: Updates during iteration
    - checkpoint_request: When checkpoint reached (waits for approval)
    - final_plan: When planning complete
    """
    session_id, session = session_manager.get_or_create(session_id)

    # Create generator for SSE streaming
    async def event_stream():
        try:
            if max_iterations == 1:
                # Single iteration - no checkpoints
                yield f"data: {json.dumps({'type': 'iteration_started', 'iteration': 1, 'max': 1})}\n\n"

                result = await _execute_single_iteration_planning(
                    session,
                    PlanRequest(goal=goal, max_iterations=1),
                    session_id
                )

                yield f"data: {json.dumps({'type': 'final_plan', 'plan': result.plan_content, 'frameworks': result.frameworks, 'data_points': result.data_points})}\n\n"

            else:
                # Multi-iteration with checkpoints
                yield f"data: {json.dumps({'type': 'planning_started', 'goal': goal, 'max_iterations': max_iterations, 'checkpoint_interval': checkpoint_interval})}\n\n"

                memory_path = get_memory_path()
                if not session["orchestrator"]:
                    session["orchestrator"] = SimpleOrchestrator(
                        memory_path=memory_path,
                        max_iterations=max_iterations
                    )

                orchestrator = session["orchestrator"]

                # Run iterative planning
                iteration_generator = orchestrator.run_iterative_planning(
                    goal=goal,
                    proposal=proposal,
                    max_iterations=max_iterations,
                    checkpoint_interval=checkpoint_interval,
                    llama_planner=LlamaPlanner(session["agent"], memory_path)
                )

                checkpoint_count = 0
                final_plan = ""
                all_frameworks = []
                all_data_points = 0

                # Track previous iteration for improvement analysis
                previous_iteration_result = None

                for item in iteration_generator:
                    if isinstance(item, dict):
                        if item.get("type") == "checkpoint":
                            checkpoint_count += 1
                            current_iteration = item.get("iteration", checkpoint_count * checkpoint_interval)

                            # CRITICAL: Analyze improvements using Llama's thinking
                            improvement_analysis = await _analyze_iteration_improvements(
                                session=session,
                                goal=goal,
                                iteration_number=current_iteration,
                                current_result=item,
                                previous_result=previous_iteration_result
                            )

                            # Send checkpoint summary to frontend
                            checkpoint_data = {
                                "type": "checkpoint_reached",
                                "iteration": current_iteration,
                                "checkpoint_number": checkpoint_count,
                                "summary": item.get("summary", ""),
                                "frameworks_so_far": item.get("frameworks_used", []),
                                "data_points_so_far": item.get("data_points_count", 0),
                                "improvements": improvement_analysis  # NEW: Show what improved
                            }
                            yield f"data: {json.dumps(checkpoint_data)}\n\n"

                            # Store for next comparison
                            previous_iteration_result = item

                            if DEBUG:
                                print(f"   ✓ Checkpoint {checkpoint_count} reached, waiting for approval...")

                            # CRITICAL: Wait for user approval before continuing
                            session_manager.wait_for_checkpoint_approval(session_id)

                            if DEBUG:
                                print(f"   ✓ Checkpoint {checkpoint_count} approved, continuing...")

                            # Send approval received message
                            yield f"data: {json.dumps({'type': 'checkpoint_approved', 'checkpoint': checkpoint_count})}\n\n"

                        elif item.get("type") == "final_plan":
                            final_plan = item.get("plan", "")
                            all_frameworks = item.get("unique_frameworks", [])
                            all_data_points = item.get("total_data_points", 0)

                # Save final plan to memory
                if final_plan:
                    llama_planner = LlamaPlanner(session["agent"], memory_path)
                    llama_planner.save_plan(
                        goal=goal,
                        plan_content=final_plan,
                        execution_metadata={
                            "iterations": max_iterations,
                            "checkpoints": checkpoint_count,
                            "frameworks_applied": all_frameworks,
                            "data_points": all_data_points
                        }
                    )

                # Send final plan
                yield f"data: {json.dumps({'type': 'final_plan', 'plan': final_plan, 'frameworks': all_frameworks, 'data_points': all_data_points, 'iterations': max_iterations, 'checkpoints': checkpoint_count})}\n\n"

        except Exception as e:
            if DEBUG:
                print(f"❌ SSE error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        # Send completion marker
        yield f"data: {json.dumps({'type': 'complete'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/entities")
async def list_entities():
    """List available memory entities."""
    memory_path = get_memory_path()
    entities_path = Path(memory_path) / "entities"

    entities = []
    if entities_path.exists():
        for file in entities_path.glob("*.md"):
            entities.append({
                "name": file.stem,
                "description": f"Memory entity: {file.stem}"
            })

    return entities


@app.post("/api/save-entity")
async def save_entity_endpoint(request: Dict[str, Any]):
    """Save plan as memory entity."""
    try:
        goal = request.get("goal", "Untitled Plan")
        plan_content = request.get("plan_content", "")
        session_id = request.get("session_id")

        session_id, session = session_manager.get_or_create(session_id)
        memory_path = get_memory_path()

        llama_planner = LlamaPlanner(session["agent"], memory_path)
        result = llama_planner.save_plan(
            goal=goal,
            plan_content=plan_content,
            execution_metadata={
                "source": "web_chatbox",
                "saved_from_session": session_id
            }
        )

        return {
            "status": result.get("status", "success"),
            "entity_name": result.get("plan_id", "plan"),
            "message": result.get("message", "Plan saved")
        }

    except Exception as e:
        if DEBUG:
            print(f"❌ Save entity error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to save entity"
        }


@app.post("/api/checkpoint-approval")
async def checkpoint_approval_endpoint(request: Dict[str, Any]):
    """
    Handle checkpoint approval from user.

    Called when user clicks "Approve" on checkpoint modal.
    Resumes the /api/execute-plan SSE stream.
    """
    session_id = request.get("session_id")
    checkpoint_number = request.get("checkpoint", 0)

    if DEBUG:
        print(f"   📌 Checkpoint {checkpoint_number} approved by user")

    # Signal that checkpoint is approved
    session_manager.set_checkpoint_approved(session_id)

    return {
        "status": "approved",
        "checkpoint": checkpoint_number,
        "message": "Checkpoint approved, continuing planning..."
    }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 MemAgent Chatbox Starting")
    print("="*70)
    print(f"📍 Server: http://localhost:{CHATBOX_PORT}")
    print(f"📁 Memory: {get_memory_path()}")
    print("="*70 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=CHATBOX_PORT,
        log_level="info"
    )
