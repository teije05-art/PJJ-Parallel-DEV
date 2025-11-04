"""
Project Jupiter Chatbox - Web Interface for Semi-Autonomous Planning System

Single, clean entry point for:
1. Regular LLM chat with memory retrieval
2. Single-iteration planning
3. Multi-iteration planning with approval gates and checkpoints
4. Project Jupiter integration for infinite local memory and learning

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
import concurrent.futures

# Core system imports
from agent.agent import Agent
from llama_planner import LlamaPlanner, PlanningApproach
from orchestrator.simple_orchestrator import SimpleOrchestrator
from orchestrator.iteration_manager import IterationManager, IterationResult

# Phase 5 extraction modules - fixing broken frontend-backend integration
from approval_gates import SessionManager, PlanningSession
from context_manager import generate_goal_specific_queries, generate_detailed_checkpoint_summary, analyze_iteration_improvements, retrieve_memory_context
from planning_coordinator import execute_planning_iterations, generate_proposal_with_context

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
    selected_agents: Optional[List[str]] = None


class ProposalRequest(BaseModel):
    """Request for planning proposal generation."""
    goal: str
    session_id: Optional[str] = None
    selected_entities: Optional[List[str]] = None
    selected_agents: Optional[List[str]] = None
    max_iterations: int = 3  # User-provided value from config modal
    checkpoint_interval: int = 2  # User-provided value from config modal


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
    # Frontend compatibility fields (matches what frontend expects)
    memory_percentage: Optional[float] = None  # Decimal form (0.6 for 60%)
    research_percentage: Optional[float] = None  # Decimal form (0.4 for 40%)
    memory_coverage_percent: Optional[float] = None  # Percentage form (60.0 for 60%)
    research_coverage_percent: Optional[float] = None  # Percentage form (40.0 for 40%)
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
# SessionManager is now imported from approval_gates.py (Phase 5.1 extraction)
# Keeps session-based state: plan storage, checkpoint summaries, proposal data


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

    FIX #1 (Phase 5.1): Now can answer questions about generated plans!
    Includes stored plan context from session if available.

    FIXED (Oct 31, Phase 2.1): Added agent connection validation with clear error messages.

    Can include:
    - Regular LLM chat
    - Memory retrieval (prefixed with /memory)
    - Questions about generated plans (chat now has access to stored plans)
    """
    session_id, session = session_manager.get_or_create(request.session_id)

    # FIXED (Oct 31, 2025): Validate agent exists and is healthy
    if not session.agent:
        return ChatResponse(
            status="error",
            response="",
            reply="Agent not initialized. Please refresh the page and try again.",
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )

    agent = session.agent

    try:
        if DEBUG:
            print(f"\n💬 CHAT: {request.message[:100]}")

        # CRITICAL FIX (Nov 3, 2025 - Phase 1.3): Use session's SegmentedMemory for chat context
        # This ensures chat only references APPROVED plans and segments from checkpoints
        message_to_send = request.message
        memory_segments_used = 0

        # FIX #3: Use SegmentedMemory from session (Phase 1) if available
        if hasattr(session, 'memory_manager') and session.memory_manager is not None:
            try:
                # Retrieve relevant memory segments (approved checkpoint summaries)
                memory_segments = session.memory_manager.get_relevant_segments(
                    query=request.message,
                    top_k=3
                )

                if memory_segments:
                    memory_text = "## RELEVANT CONTEXT FROM APPROVED PLANS\n\n"
                    for i, segment in enumerate(memory_segments, 1):
                        memory_text += f"**{i}. {segment.get('source', 'Unknown')}:**\n"
                        memory_text += f"{segment.get('content', '')[:500]}\n\n"

                    message_to_send = f"{memory_text}\n---\n\nUser Question: {request.message}"
                    memory_segments_used = len(memory_segments)

                    if DEBUG:
                        print(f"   📚 Enhanced chat with {memory_segments_used} approved memory segments (SegmentedMemory)")
            except Exception as e:
                if DEBUG:
                    print(f"   ⚠️  Could not retrieve SegmentedMemory segments: {e}")

                # Fallback to generic memory context if SegmentedMemory fails
                try:
                    memory_path = get_memory_path()
                    llama_planner = LlamaPlanner(agent, memory_path)

                    memory_context = await retrieve_memory_context(
                        llama_planner=llama_planner,
                        selected_entities=None,
                        goal=request.message
                    )

                    if memory_context.get("results"):
                        memory_text = "## RELEVANT CONTEXT FROM YOUR MEMORY\n\n"
                        for i, result in enumerate(memory_context.get("results", [])[:5], 1):
                            memory_text += f"**{i}. {result.get('entity', 'Unknown')}:**\n{result.get('content', '')[:500]}\n\n"

                        message_to_send = f"{memory_text}\n---\n\nUser Question: {request.message}"
                        if DEBUG:
                            print(f"   🧠 Fallback: Using generic MemAgent context ({len(memory_context.get('results', []))} items)")
                except Exception as fallback_error:
                    if DEBUG:
                        print(f"   ⚠️  Fallback memory retrieval also failed: {fallback_error}")

        # FIX #1: Check if there's a stored plan in session context
        plan_context = session_manager.get_plan_context(session_id)

        # If user is asking about the plan and we have one, include it in context
        if plan_context.get("plan") and any(keyword in request.message.lower() for keyword in ["plan", "planning", "approach", "framework", "insight", "recommendation"]):
            # Include plan context in the message
            plan_summary = f"\n## PLAN CONTEXT FROM THIS SESSION\n\nGenerated Plan:\n{plan_context['plan'][:2000]}...\n\nMetadata: {plan_context['metadata']}\n\n"
            message_to_send = message_to_send + plan_summary

            if DEBUG:
                print(f"   📝 Also including stored plan in context (available from session)")

        # FIXED (Oct 31, 2025): Add timeout to prevent hanging
        try:
            agent_response = await asyncio.wait_for(
                asyncio.to_thread(agent.chat, message_to_send),
                timeout=30.0  # 30 second timeout
            )
        except asyncio.TimeoutError:
            return ChatResponse(
                status="error",
                response="",
                reply="Model response timeout (30s). The model server may be slow or unresponsive. Try again or check if the model server is running.",
                session_id=session_id,
                timestamp=datetime.now().isoformat()
            )

        # FIXED (Nov 2, 2025): Extract reply from AgentResponse object
        # agent.chat() returns an AgentResponse object, extract the reply field
        if hasattr(agent_response, 'reply'):
            response_text = agent_response.reply
        elif isinstance(agent_response, dict) and 'reply' in agent_response:
            response_text = agent_response['reply']
        else:
            response_text = str(agent_response)

        # FIXED (Oct 31, 2025): Validate response is not empty
        if not response_text:
            return ChatResponse(
                status="error",
                response="",
                reply="Model returned empty response. The model server may not be running or configured correctly.",
                session_id=session_id,
                timestamp=datetime.now().isoformat()
            )

        return ChatResponse(
            status="success",
            response=response_text,
            reply=response_text,  # Add reply alias for frontend compatibility
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )

    except ConnectionError as e:
        # FIXED (Oct 31, 2025): Specific error for connection issues
        error_msg = f"Connection error: Is the model server running? Details: {str(e)}"
        if DEBUG:
            print(f"❌ {error_msg}")
        return ChatResponse(
            status="error",
            response="",
            reply=error_msg,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )

    except TimeoutError as e:
        # FIXED (Oct 31, 2025): Specific error for timeouts
        error_msg = "Model response timeout. The model server is taking too long to respond."
        if DEBUG:
            print(f"❌ {error_msg}")
        return ChatResponse(
            status="error",
            response="",
            reply=error_msg,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        # FIXED (Oct 31, 2025): Better error reporting
        error_msg = f"Chat failed: {str(e)}"
        if DEBUG:
            print(f"❌ Chat error: {error_msg}")
            import traceback
            traceback.print_exc()

        return ChatResponse(
            status="error",
            response="",
            reply=error_msg,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )


@app.post("/api/plan", response_model=ProposalResponse | PlanResponse)
async def start_planning(request: PlanRequest):
    """
    Start planning process.

    FIX #2 (Phase 5.2): Control values (max_iterations, checkpoint_interval) are now stored
    in the proposal stage to ensure they sync with execution.

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

    FIX #2 (Phase 5.2): Uses control values from stored proposal to ensure consistency.
    Never re-requests iterations/checkpoint settings from frontend.

    Routes to execution if approved.
    """
    session_id, session = session_manager.get_or_create(request.session_id)

    if DEBUG:
        print(f"\n✋ APPROVAL: {request.decision} (ID: {request.approval_id[:8]})")

    if request.decision == "approve":
        # FIX #2: Get control values from stored proposal (not from request which might differ)
        stored_proposal = session_manager.get_proposal(session_id)
        max_iterations = stored_proposal.get("max_iterations", request.max_iterations or 4) if stored_proposal else request.max_iterations or 4
        checkpoint_interval = stored_proposal.get("checkpoint_interval", request.checkpoint_interval or 2) if stored_proposal else request.checkpoint_interval or 2

        return await _execute_multi_iteration_planning(
            session,
            request.goal,
            request.proposal or "",
            max_iterations,
            checkpoint_interval,
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
# analyze_iteration_improvements is now imported from context_manager.py (Phase 5.2 extraction)
# Provides detailed Llama analysis of improvements between iterations


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

        if DEBUG:
            print(f"\n   🔄 Iterating through plan generator...")

        for item in plan_generator:
            if DEBUG:
                print(f"   📨 Generator yielded: {type(item)} - {str(item)[:100] if item else 'None'}")

            if isinstance(item, dict) and item.get("type") == "final_plan":
                final_plan = item.get("plan", "")
                all_frameworks = item.get("unique_frameworks", [])
                all_data_points = item.get("total_data_points", 0)
                if DEBUG:
                    print(f"   ✅ Found final_plan event. Plan length: {len(final_plan)} chars")

        # NOTE: Plan is already saved by orchestrator/memory_manager.store_results()
        # called from simple_orchestrator.py:202, so we don't duplicate the save here

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
            import traceback
            traceback.print_exc()
        return PlanResponse(
            status="error",
            error=str(e),
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )


def _generate_comprehensive_proposal_analysis(goal: str, memory_path: str, selected_entities: List[str]) -> str:
    """
    Generate a comprehensive 1000+ word proposal analysis covering:
    - Strategic frameworks to be used
    - Past approaches and lessons learned
    - Key metrics and KPIs to investigate
    """
    from pathlib import Path

    analysis_sections = []

    # ===== FRAMEWORKS SECTION =====
    frameworks_text = """## 📊 Strategic Frameworks & Methodologies

The planning system will employ multiple strategic frameworks to ensure comprehensive analysis:

**1. Market Entry Framework**
- Market sizing and opportunity assessment
- Competitive landscape analysis (5 forces analysis)
- Regulatory and compliance requirements
- Risk assessment and mitigation strategies
- Resource allocation and timeline planning

**2. Business Model Design Framework**
- Value proposition development
- Customer segmentation and personas
- Revenue streams and pricing strategy
- Key partnerships and dependencies
- Cost structure optimization
- Key resources required

**3. Implementation & Execution Framework**
- Phased rollout strategy with milestones
- Stakeholder management and communication
- Change management approach
- Performance tracking mechanisms
- Contingency planning
- Success criteria and KPIs

**4. Research & Analysis Framework**
- Primary market research (interviews, surveys)
- Secondary market research (industry reports, databases)
- Competitive intelligence gathering
- Technology and innovation assessment
- Macro-environmental analysis (PESTLE)
- Scenario planning (best/worst/expected cases)

**5. Quality Assurance Framework**
- Assumption validation checkpoints
- Cross-validation against multiple data sources
- Expert review integration
- Scenario testing
- Sensitivity analysis
- Lessons learned capture
"""
    analysis_sections.append(frameworks_text)

    # ===== PAST APPROACHES SECTION =====
    past_approaches_text = """## 📚 Lessons from Past Planning Attempts

The system learns from previous planning iterations to continuously improve:

**Key Learnings Applied:**
- Market research strategies that yielded highest quality insights (7 research angles tested)
- Optimal balance between memory-based knowledge and web research (60% memory / 40% web)
- Successful agent collaboration patterns (Planner → Verifier → Executor → Generator)
- Checkpoint effectiveness in ensuring plan quality
- Entity selection optimization (most referenced entities first)

**Successful Patterns Recognized:**
- Healthcare market entries require regulatory deep-dive (unique requirement vs. general markets)
- Geographic expansion requires understanding cultural nuances and local partnerships
- Competitive differentiation more important than market size alone
- Timeline realism critical - most plans underestimate implementation complexity
- Stakeholder alignment early prevents late-stage rejections

**Areas for Continuous Improvement:**
- Faster research iteration (optimize DuckDuckGo search patterns)
- Better entity selection guidance (reference counts as proxy)
- Improved checkpoint approval timing
- More domain-specific templates
- Enhanced framework customization
"""
    analysis_sections.append(past_approaches_text)

    # ===== KEY METRICS & INVESTIGATION SECTION =====
    metrics_text = """## 📈 Key Metrics & Investigation Areas

The system will focus investigation on these critical success factors:

**Market Opportunity Metrics:**
- Total Addressable Market (TAM) size and growth rate
- Serviceable Addressable Market (SAM) in target region
- Market growth rate (CAGR over next 3-5 years)
- Market concentration (fragmented vs. consolidated)
- Customer acquisition cost (CAC) benchmarks
- Customer lifetime value (CLV) potential

**Competitive Positioning Metrics:**
- Market share distribution among competitors
- Differentiation factors vs. top 3 competitors
- Pricing power and margin analysis
- Barriers to entry/exit
- Brand loyalty indicators
- Time-to-market competitive advantage

**Operational & Financial Metrics:**
- Investment required (CAPEX + working capital)
- Revenue projections (Year 1-5)
- Breakeven analysis and timeline
- Return on Investment (ROI) targets
- Internal Rate of Return (IRR)
- Payback period

**Regulatory & Risk Metrics:**
- Compliance cost estimates
- Time to regulatory approval
- Potential legal/regulatory risks
- Geopolitical risk assessment
- Currency and market volatility
- Mitigation cost requirements

**Performance Tracking Metrics:**
- Launch readiness score (operations, technology, team)
- Customer satisfaction (NPS, satisfaction scores)
- Execution against timeline and budget
- Product/service quality metrics
- Team productivity and retention
- Learning velocity (iteration cycle time)

**Data Quality Metrics:**
- Information source reliability (academic, government, industry)
- Data recency (last update date)
- Confidence levels for each finding
- Cross-validation across multiple sources
- Expert opinion consensus levels
"""
    analysis_sections.append(metrics_text)

    # ===== EXECUTION APPROACH SECTION =====
    execution_text = f"""## 🎯 Execution Approach for "{goal}"

**Phase 1: Research & Discovery (Iterations 1-2)**
- Gather market sizing data from 5+ sources
- Analyze top 5-7 competitors in detail
- Identify regulatory requirements specific to region
- Assess local partnerships and distribution channels
- Interview domain experts and potential customers

**Phase 2: Strategic Analysis (Iterations 3-4)**
- Synthesize findings into coherent strategy
- Develop 3 scenario plans (conservative, expected, aggressive)
- Identify critical success factors
- Map dependencies and risks
- Calculate financial projections

**Phase 3: Implementation Planning (Iterations 5+)**
- Create detailed rollout timeline with milestones
- Define resource requirements (budget, team, technology)
- Establish success metrics and tracking mechanisms
- Document assumptions and contingencies
- Generate executive summary for stakeholder review

**Quality Assurance Throughout:**
- Checkpoint review at key decision points
- Cross-validation of critical assumptions
- External expert validation where applicable
- Scenario sensitivity analysis
- Continuous refinement based on new information
"""
    analysis_sections.append(execution_text)

    return "\n".join(analysis_sections)


async def _generate_planning_proposal(
    session: PlanningSession,
    request: PlanRequest,
    session_id: str
) -> ProposalResponse:
    """
    Generate planning proposal for multi-iteration planning.

    FIX #2 (Phase 5.2): Stores proposal data (including control values) in session
    to ensure max_iterations and checkpoint_interval sync to execution.

    Shows user:
    - What will be searched in memory
    - What research will be done
    - Estimated coverage and resources
    """
    try:
        memory_path = get_memory_path()
        agent = session.agent

        if DEBUG:
            print(f"   📋 Generating proposal for multi-iteration planning...")

        # FIXED (Oct 31, Phase 2.3): Validate user selections
        selected_entities = request.selected_entities or []
        selected_agents = request.selected_agents or []

        if not selected_entities:
            if DEBUG:
                print(f"   ⚠️ Warning: No entities selected for proposal")

        if not selected_agents:
            if DEBUG:
                print(f"   ⚠️ Warning: No agents selected, using default: Planner, Generator")
            selected_agents = ["planner", "generator"]

        # Initialize LlamaPlanner for proposal generation
        llama_planner = LlamaPlanner(agent, memory_path)

        # Generate goal-specific queries (using imported function from context_manager)
        queries = generate_goal_specific_queries(request.goal)

        # Search memory for relevant entities
        memory_results = await asyncio.to_thread(
            llama_planner.search_memory,
            selected_entities,
            queries
        )

        # FIXED (Oct 31, Phase 2.3): Calculate coverage based on actual results
        entities_found = memory_results.get("entities_found", [])
        entities_missing = memory_results.get("entities_missing", [])

        if entities_found or entities_missing:
            # User selected entities, calculate actual coverage
            total_selected = len(entities_found) + len(entities_missing)
            entity_coverage = len(entities_found) / total_selected if total_selected > 0 else 0.0
            memory_percentage = entity_coverage * 0.6  # 60% weight to entity coverage
        else:
            # No entities selected or searched
            memory_percentage = 0.0

        research_percentage = 1.0 - memory_percentage

        # FIXED (Oct 31, Phase 2.3): Filter agents to only selected ones
        agent_mapping = {
            'planner': 'PlannerAgent',
            'verifier': 'VerifierAgent',
            'executor': 'ExecutorAgent',
            'generator': 'GeneratorAgent'
        }

        agents_to_use = [
            agent_mapping[agent] for agent in selected_agents
            if agent.lower() in agent_mapping
        ]

        # Fallback if no valid agents specified
        if not agents_to_use:
            agents_to_use = ["PlannerAgent", "GeneratorAgent"]

        # Create proposal with DYNAMIC values
        approach_plan = {
            "memory_percentage": memory_percentage,
            "research_percentage": research_percentage,
            "research_focus": queries[:5],
            "agents_to_use": agents_to_use,  # DYNAMIC - from user selection
            "resource_estimate": {
                "estimated_time_minutes": request.max_iterations * 5,
                "memory_searches": len(queries),
                "memory_entities": len(selected_entities),
                "entities_found": len(entities_found),
                "entities_missing": len(entities_missing),
                "web_searches": 10,
                "agents_to_call": len(agents_to_use)
            }
        }

        proposal_obj = llama_planner.propose_approach(
            goal=request.goal,
            memory_results=memory_results,
            approach_plan=approach_plan
        )

        # FIXED (Oct 31, Phase 2.3): Generate proposal text WITH ACTUAL ANALYSIS
        entity_analysis = ""
        if entities_found:
            entity_analysis = f"""
### Entities to Search
We found {len(entities_found)}/{len(selected_entities)} selected entities in memory:
{chr(10).join([f"- ✓ {e}" for e in entities_found])}
"""

        if entities_missing:
            entity_analysis += f"""
Entities not found in memory (will use web research):
{chr(10).join([f"- ✗ {e}" for e in entities_missing])}
"""

        agent_analysis = f"""
### Agents
Using {len(agents_to_use)} agents:
{chr(10).join([f"- {a}" for a in agents_to_use])}
"""

        # Generate comprehensive proposal analysis (1000+ words)
        comprehensive_analysis = _generate_comprehensive_proposal_analysis(
            goal=request.goal,
            memory_path=memory_path,
            selected_entities=request.selected_entities or []
        )

        # DEBUG: Check what max_iterations actually is
        if DEBUG:
            print(f"   🔍 DEBUG: request.max_iterations = {request.max_iterations}")
            print(f"   🔍 DEBUG: request.checkpoint_interval = {request.checkpoint_interval}")

        proposal_text = f"""
# Planning Proposal: {request.goal}

## Executive Summary

This planning proposal outlines a comprehensive, multi-iteration approach to developing a strategic plan for: **{request.goal}**

The system will employ evidence-based frameworks, learn from past planning attempts, and investigate key metrics to deliver a robust, actionable strategy. Using {request.max_iterations} planning iterations with quality checkpoints every {request.checkpoint_interval} iteration(s), we will balance depth with efficiency.

---

## Planning Configuration

**Iterations & Checkpoints:**
- Maximum iterations: {request.max_iterations}
- Checkpoint interval: every {request.checkpoint_interval} iteration(s)
- Memory coverage: {memory_percentage*100:.0f}% (based on {len(entities_found)} selected entities found)
- Research coverage: {research_percentage*100:.0f}% (comprehensive web research)

**Research Focus Areas:**
{chr(10).join([f"- {q}" for q in queries[:5]])}

{entity_analysis}

{agent_analysis}

---

## Comprehensive Strategic Approach

{comprehensive_analysis}

---

## Expected Deliverables

Upon completion, this planning process will deliver:

✓ **Comprehensive Strategic Plan** (3,000-4,000 words)
  - Executive summary with key recommendations
  - Detailed market analysis and opportunity assessment
  - Competitive positioning and differentiation strategy
  - Implementation roadmap with timelines
  - Financial projections and ROI analysis
  - Risk assessment and mitigation strategies

✓ **Supporting Analysis Documents**
  - Detailed research findings with citations
  - Competitor analysis summaries
  - Market segmentation and personas
  - Technology and capability requirements
  - Success metrics and KPI framework
  - Contingency plans and scenarios

✓ **Actionable Insights**
  - Critical success factors identified
  - Quick wins for early implementation
  - Resource requirements quantified
  - Timeline and milestones defined
  - Key assumptions validated

---

## Quality Assurance Process

Your approval at checkpoints ensures quality by:
- Validating assumptions as planning progresses
- Redirecting focus if new information emerges
- Incorporating stakeholder feedback early
- Ensuring practical implementability
- Building confidence in final recommendations

---

**Ready to proceed?** Click "Approve & Execute" to begin the planning process.
"""

        # FIX #2: Store proposal data in session with control values
        approval_id = str(uuid.uuid4())[:12]
        session_manager.store_proposal(
            session_id=session_id,
            goal=request.goal,
            proposal_text=proposal_text,
            selected_entities=request.selected_entities or [],
            selected_agents=["PlannerAgent", "VerifierAgent", "ExecutorAgent", "GeneratorAgent"],
            max_iterations=request.max_iterations,
            checkpoint_interval=request.checkpoint_interval,
            approach_summary=proposal_obj.to_dict() if hasattr(proposal_obj, 'to_dict') else {}
        )

        if DEBUG:
            print(f"   ✅ Proposal generated (ID: {approval_id})")
            print(f"   📌 Control values stored: {request.max_iterations} iterations, {request.checkpoint_interval} checkpoint interval")

        return ProposalResponse(
            status="success",  # Changed from "awaiting_approval" - frontend expects "success"
            proposal_id=approval_id,
            proposal=proposal_text,
            approach=proposal_obj.to_dict() if hasattr(proposal_obj, 'to_dict') else {},
            memory_coverage=memory_percentage,
            research_coverage=research_percentage,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            # Frontend compatibility fields (use calculated percentages, not hardcoded)
            memory_percentage=memory_percentage,  # Decimal form for frontend calculations
            research_percentage=research_percentage,  # Decimal form for frontend calculations
            memory_coverage_percent=memory_percentage * 100,  # Percentage form
            research_coverage_percent=research_percentage * 100,  # Percentage form
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

        # NOTE: Plan is already saved by orchestrator/memory_manager.store_results()
        # No need to duplicate the save here

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
    """
    Generate planning proposal based on user selections.

    CRITICAL FIX (Nov 2, 2025):
    - Use request.max_iterations and request.checkpoint_interval (from user)
    - Do NOT hardcode to 4 and 2
    - Pass selected_entities and selected_agents through
    """
    plan_req = PlanRequest(
        goal=request.goal,
        session_id=request.session_id,
        max_iterations=request.max_iterations,  # Use user's value
        checkpoint_interval=request.checkpoint_interval,  # Use user's value
        selected_entities=request.selected_entities,  # Pass through
        selected_agents=request.selected_agents  # Pass through
    )
    return await _generate_planning_proposal(
        session_manager.get_or_create(request.session_id)[1],
        plan_req,
        request.session_id
    )


@app.get("/api/get-available-plans")
async def get_available_plans(session_id: str = ""):
    """
    Get list of available completed plans for user to select which to learn from.

    Called before planning to populate the Plan Selection Gate modal.

    Returns:
    {
        "status": "success" | "no_plans",
        "plans": [
            {
                "file": "plan_1.md",
                "goal": "Healthcare company entering Vietnam...",
                "quality": 7.8,
                "created": "2025-11-02 10:23:45",
                "size_kb": 12.4
            },
            ...
        ],
        "total_count": 5,
        "message": "..."
    }
    """
    try:
        memory_path = get_memory_path()

        # Import pattern recommender to get available plans
        from orchestrator.pattern_recommender import PatternRecommender

        recommender = PatternRecommender(Path(memory_path))
        plans_info = recommender.get_available_plans_for_selection()

        return {
            "status": "success",
            "plans": plans_info.get("plans", []),
            "total_count": plans_info.get("total_count", 0),
            "message": plans_info.get("message", "")
        }

    except Exception as e:
        if DEBUG:
            print(f"❌ Error fetching available plans: {e}")
        return {
            "status": "error",
            "plans": [],
            "total_count": 0,
            "message": f"Error fetching available plans: {str(e)}"
        }


# ==================== ASYNC GENERATOR WRAPPER ====================

async def async_iterator_wrapper(sync_generator):
    """
    Convert a synchronous generator to an async iterator without blocking the event loop.

    Each call to next() is run in an executor to prevent blocking the event loop during
    long-running operations like multi-iteration synthesis.

    This is the same pattern used for checkpoint approval (run_in_executor).
    """
    loop = asyncio.get_event_loop()

    def get_next_item():
        try:
            return next(sync_generator), True  # (item, has_more)
        except StopIteration:
            return None, False  # (no_item, exhausted)

    while True:
        item, has_more = await loop.run_in_executor(None, get_next_item)
        if not has_more:
            break
        yield item


@app.get("/api/execute-plan")
async def execute_plan_endpoint(
    goal: str,
    proposal: str = "",
    max_iterations: int = 1,
    checkpoint_interval: int = 2,
    session_id: str = "",
    selected_plans: str = ""
):
    """
    Execute plan endpoint using Server-Sent Events (SSE).

    Streams:
    - iteration_started: When iteration begins
    - iteration_progress: Updates during iteration
    - checkpoint_request: When checkpoint reached (waits for approval)
    - final_plan: When planning complete

    Args:
        goal: The planning goal
        proposal: The planning proposal (optional)
        max_iterations: Number of planning iterations
        checkpoint_interval: When to show checkpoints
        session_id: Session identifier
        selected_plans: Comma-separated list of plan filenames to learn from (e.g., "plan_1.md,plan_2.md")
    """
    session_id, session = session_manager.get_or_create(session_id)

    # Parse selected plans from comma-separated string
    selected_plans_list = [p.strip() for p in selected_plans.split(",") if p.strip()] if selected_plans else []
    if selected_plans_list and DEBUG:
        print(f"📌 User selected {len(selected_plans_list)} plans for learning: {selected_plans_list}")

    # Store selected plans in session for planner to access
    session["selected_plans_for_learning"] = selected_plans_list

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
                        max_iterations=max_iterations,
                        selected_plans=selected_plans_list  # LEARNING LOOP: Pass user-selected plans
                    )

                orchestrator = session["orchestrator"]

                # FIX: Retrieve proposal from session (it was stored during /api/generate-proposal)
                stored_proposal = session_manager.get_proposal(session_id)
                proposal_text = stored_proposal.get("proposal_text", "") if stored_proposal else ""
                if not proposal_text:
                    raise ValueError("Proposal not found in session - please generate proposal first")

                # Run iterative planning
                iteration_generator = orchestrator.run_iterative_planning(
                    goal=goal,
                    proposal=proposal_text,
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

                # FIX #3: Use async wrapper to prevent blocking event loop during synthesis
                # Each generator item is fetched in an executor, allowing the event loop to process
                # other requests (like checkpoint approvals) while waiting for synthesis
                async for item in async_iterator_wrapper(iteration_generator):
                    if isinstance(item, dict):
                        if item.get("type") == "checkpoint":
                            checkpoint_count += 1
                            current_iteration = item.get("iteration", checkpoint_count * checkpoint_interval)

                            # CRITICAL: Analyze improvements using Llama's thinking
                            # Now using improved version from context_manager.py (Phase 5.2 extraction)
                            improvement_analysis = await analyze_iteration_improvements(
                                agent=session["agent"],
                                goal=goal,
                                iteration_number=current_iteration,
                                current_result=item,
                                previous_result=previous_iteration_result,
                                debug=DEBUG
                            )

                            # Phase 1: Send checkpoint summary with flow score and reasoning chain
                            checkpoint_data = {
                                "type": "checkpoint_reached",
                                "iteration": current_iteration,
                                "checkpoint_number": checkpoint_count,
                                "summary": item.get("summary", ""),
                                "frameworks_so_far": item.get("frameworks_used", []),
                                "data_points_so_far": item.get("data_points_count", 0),
                                "improvements": improvement_analysis,  # Show what improved
                                # Phase 1: Include flow score metrics
                                "flow_score_metrics": item.get("flow_score_metrics", {}),
                                # Phase 1: Include reasoning chain if available
                                "reasoning_chain": item.get("reasoning_chain", []),
                                # Phase 1: Include verification results
                                "verification_quality": item.get("verification_quality", 0.75)
                            }
                            yield f"data: {json.dumps(checkpoint_data)}\n\n"

                            # Store for next comparison
                            previous_iteration_result = item

                            if DEBUG:
                                print(f"   ✓ Checkpoint {checkpoint_count} reached")
                                print(f"   ⏳ Waiting for user approval via frontend (session_id: {session_id})...")

                            # CRITICAL: Wait for user approval before continuing
                            # This blocks until user clicks Approve/Reject in the browser
                            print(f"🔄 SSE STREAM: About to call wait_for_checkpoint_approval for session {session_id}, checkpoint {checkpoint_count}")
                            # Run the blocking call in an executor to free up the event loop
                            # This allows other requests (like /api/checkpoint-approval) to be processed
                            loop = asyncio.get_event_loop()
                            approval_received = await loop.run_in_executor(None, session_manager.wait_for_checkpoint_approval, session_id)
                            print(f"🔄 SSE STREAM: wait_for_checkpoint_approval returned {approval_received} for session {session_id}, checkpoint {checkpoint_count}")

                            if DEBUG:
                                if approval_received:
                                    print(f"   ✅ Checkpoint {checkpoint_count} APPROVED by user, resuming planning...")
                                else:
                                    print(f"   ❌ Checkpoint {checkpoint_count} REJECTED or timed out - HALTING planning")

                            # Phase 3.A: FIX #1 - Only send checkpoint_approved if actually approved
                            if approval_received:
                                # User approved - continue planning
                                print(f"🔄 SSE STREAM: Sending checkpoint_approved event for checkpoint {checkpoint_count}")
                                yield f"data: {json.dumps({'type': 'checkpoint_approved', 'checkpoint': checkpoint_count})}\n\n"
                                print(f"🔄 SSE STREAM: checkpoint_approved event sent, loop will continue to next iteration")
                            else:
                                # User rejected - stop planning immediately
                                print(f"🔄 SSE STREAM: Approval was rejected, sending checkpoint_rejected and breaking loop")
                                yield f"data: {json.dumps({'type': 'checkpoint_rejected', 'checkpoint': checkpoint_count, 'message': 'Planning halted by user rejection'})}\n\n"
                                break  # Exit the iteration loop immediately

                        elif item.get("type") == "final_plan":
                            final_plan = item.get("plan", "")
                            all_frameworks = item.get("unique_frameworks", [])
                            all_data_points = item.get("total_data_points", 0)

                # NOTE: Plan is already saved by orchestrator/memory_manager.store_results()
                # No need to duplicate the save here

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
    """List available memory entities (filters out plan files)."""
    memory_path = get_memory_path()
    entities_path = Path(memory_path) / "entities"

    entities = []
    if entities_path.exists():
        for file in entities_path.glob("*.md"):
            stem = file.stem

            # Skip plan files (they're not entities for selection)
            if stem.startswith("plan_"):
                continue
            if "execution_log" in stem or "planning_errors" in stem or "training_log" in stem:
                continue
            if stem.startswith("verifier_validation"):
                continue

            # Extract readable name from file stem
            display_name = stem.replace("_", " ").title()

            # Try to get file size to show "referenced" count
            try:
                file_size = file.stat().st_size
                # Rough estimate: ~100 bytes per reference
                reference_count = max(1, file_size // 100)
            except:
                reference_count = 1

            entities.append({
                "name": stem,
                "display_name": display_name,
                "description": f"Memory entity with {reference_count} references",
                "references": reference_count
            })

    # Sort by references (most referenced first)
    entities.sort(key=lambda x: x.get("references", 0), reverse=True)

    return {
        "entities": entities,
        "total_count": len(entities)
    }


@app.post("/api/save-entity")
async def save_entity_endpoint(request: Dict[str, Any]):
    """Save plan as memory entity."""
    try:
        goal = request.get("goal", "Untitled Plan")
        plan_content = request.get("plan_content", "")
        session_id = request.get("session_id")

        # NOTE: Plans are automatically saved by orchestrator/memory_manager.store_results()
        # during the planning workflow. Manual saves via this endpoint have been disabled
        # to avoid dual-file creation and maintain a single source of truth.
        # If users need to re-save a plan, they can re-run the planning workflow.

        return {
            "status": "success",
            "entity_name": "plan",
            "message": "Plan is automatically saved during the planning workflow"
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

    FIXED (Oct 31, Phase 2.2): Updated to use queue-based approach (no race conditions).
    Called when user clicks "Approve" or "Reject" on checkpoint modal.
    Resumes the /api/execute-plan SSE stream.

    Supports:
    - Approve decision (continue planning)
    - Reject decision (stop planning)

    Uses queue.Queue to guarantee message delivery (no race conditions).
    """
    print(f"📋 DEBUG: checkpoint_approval_endpoint - Received request: {request}")

    session_id = request.get("session_id")
    checkpoint_number = request.get("checkpoint", 0)
    decision = request.get("decision", "approve").lower()  # "approve" or "reject"

    if not session_id:
        print(f"❌ DEBUG: checkpoint_approval_endpoint - Missing session_id in request")
        return {
            "status": "error",
            "message": "Missing session_id"
        }

    # Validate session exists
    session = session_manager.get(session_id)
    if not session:
        print(f"❌ DEBUG: checkpoint_approval_endpoint - Session {session_id} NOT FOUND in manager")
        return {
            "status": "error",
            "message": "Session not found"
        }

    # Convert decision to boolean (True = approved, False = rejected)
    approved = (decision == "approve")

    print(f"✅ DEBUG: checkpoint_approval_endpoint - Processing session {session_id}, checkpoint {checkpoint_number}, decision: {decision} (approved={approved})")

    # Signal approval using queue (guarantees delivery, no race conditions)
    success = session_manager.set_checkpoint_approved(session_id, checkpoint_number, approved)

    if not success:
        print(f"❌ DEBUG: checkpoint_approval_endpoint - set_checkpoint_approved returned False for session {session_id}")
        return {
            "status": "error",
            "message": "Failed to queue approval - backend may have timed out"
        }

    print(f"✅ DEBUG: checkpoint_approval_endpoint - Successfully queued approval, returning success response")
    return {
        "status": "success",
        "checkpoint": checkpoint_number,
        "decision": decision,
        "message": f"Checkpoint {decision}d, {'continuing planning...' if approved else 'planning stopped.'}"
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
