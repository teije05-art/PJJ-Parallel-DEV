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
from typing import Dict, Optional
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
    ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Orchestrator: {e}")
    ORCHESTRATOR_AVAILABLE = False

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
    backend: str
    memory_path: str
    sessions_active: int

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
        backend=backend,
        memory_path=get_memory_path(),
        sessions_active=len(sessions)
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Regular chat endpoint - interactive conversation with agent.
    Works exactly like Claude Desktop, but without MCP protocol overhead.
    """
    if not AGENT_AVAILABLE:
        raise HTTPException(status_code=500, detail="Agent not available")

    session_id, session = get_or_create_session(request.session_id)
    agent = session["agent"]

    try:
        # Call agent in thread pool (it's blocking)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, agent.chat, request.message)

        # Store in session history
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

    This is the key feature that fixes the broken-pipe issues with Claude Desktop.
    The browser handles Unicode/emoji natively, so no JSON parsing problems.
    """
    if not ORCHESTRATOR_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Orchestrator not available. Check that orchestrator module is installed."
        )

    session_id, session = get_or_create_session(request.session_id)

    try:
        start_time = time.time()
        orchestrator = get_or_create_orchestrator(session_id)

        # Run planning iterations in thread pool (blocking operation)
        loop = asyncio.get_running_loop()

        # Package the planning task
        async def run_planning():
            return await loop.run_in_executor(
                None,
                lambda: _run_planning_iterations(
                    orchestrator, request.goal, request.max_iterations
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
                if "planner" in agent_results and hasattr(agent_results["planner"], "output"):
                    planner_output = agent_results["planner"].output
                    last_agent_outputs["planner"] = planner_output[:1000]  # First 1000 chars for display
                    combined_plan.append(f"## 🎯 Planner Output (Iteration {iteration})\n{planner_output[:3000]}\n")

                if "verifier" in agent_results and hasattr(agent_results["verifier"], "output"):
                    verifier_output = agent_results["verifier"].output
                    last_agent_outputs["verifier"] = verifier_output[:1000]
                    combined_plan.append(f"## ✅ Verifier Analysis (Iteration {iteration})\n{verifier_output[:2000]}\n")

                if "executor" in agent_results and hasattr(agent_results["executor"], "output"):
                    executor_output = agent_results["executor"].output
                    last_agent_outputs["executor"] = executor_output[:1000]
                    combined_plan.append(f"## 🚀 Executor Plan (Iteration {iteration})\n{executor_output[:2000]}\n")

                if "generator" in agent_results and hasattr(agent_results["generator"], "output"):
                    generator_output = agent_results["generator"].output
                    last_agent_outputs["generator"] = generator_output[:1000]
                    combined_plan.append(f"## 📝 Generator Summary (Iteration {iteration})\n{generator_output[:2000]}\n")

                # Store and process results
                print(f"[Step 3/4] Storing results to memory...")
                orchestrator.memory_manager.store_results(goal, agent_results, success=True)
                orchestrator.learning_manager.apply_learning(agent_results, "", success=True)
                print(f"[Step 3/4] ✅ Results stored and learning applied")

                # Record iteration
                completed_iterations += 1
                iteration_results.append({
                    "iteration": iteration,
                    "success": True,
                    "agents": {
                        "planner": hasattr(agent_results.get("planner"), "success") and agent_results["planner"].success,
                        "verifier": hasattr(agent_results.get("verifier"), "success") and agent_results["verifier"].success,
                        "executor": hasattr(agent_results.get("executor"), "success") and agent_results["executor"].success,
                        "generator": hasattr(agent_results.get("generator"), "success") and agent_results["generator"].success,
                    },
                    "content_length": len(planner_output) + len(verifier_output) + len(executor_output) + len(generator_output)
                })

                print(f"[Step 4/4] ✅ ITERATION {iteration} COMPLETE\n")

            except Exception as e:
                print(f"❌ Error in iteration {iteration}: {e}")
                import traceback
                traceback.print_exc()

                iteration_results.append({
                    "iteration": iteration,
                    "success": False,
                    "error": str(e)
                })

                continue

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

        // Send message
        async function sendMessage() {
            const message = input.value.trim();
            if (!message) return;

            input.value = '';
            sendBtn.disabled = true;
            sendBtn.innerHTML = 'Thinking<span class="loading"></span>';

            const emptyState = chatbox.querySelector('.empty-state');
            if (emptyState) emptyState.remove();

            addMessage(message, currentMode === 'chat' ? 'user' : 'planning');

            try {
                const endpoint = currentMode === 'chat' ? '/api/chat' : '/api/plan';
                const body = {
                    message: message,
                    session_id: sessionId
                };

                if (currentMode === 'plan') {
                    body.goal = message;
                    body.max_iterations = parseInt(document.getElementById('max-iterations').value);
                    body.checkpoint_interval = parseInt(document.getElementById('checkpoint-interval').value);
                    delete body.message;
                }

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

                if (currentMode === 'chat') {
                    addMessage(data.reply, 'agent');
                } else {
                    // PLANNING MODE - Display comprehensive results
                    let planContent = `
✅ Planning completed in ${data.execution_time.toFixed(1)}s

📊 Results:
  • Iterations: ${data.iterations}/${data.results.total_iterations}
  • Status: ${data.status.toUpperCase()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 WEB SEARCH RESULTS & SOURCES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    `.trim();

                    // Display web search results with URLs
                    if (data.web_search_results && Object.keys(data.web_search_results).length > 0) {
                        planContent += `\n\nWeb search provided current market data, competitor analysis, and industry trends:\n`;
                        let searchCount = 0;
                        for (let iterKey in data.web_search_results) {
                            const searchText = data.web_search_results[iterKey];
                            if (searchText && searchText.trim().length > 0) {
                                searchCount++;
                                // Extract URLs from search results
                                const urlMatches = searchText.match(/https?:\/\/[^\s\)]+/g) || [];
                                if (urlMatches.length > 0) {
                                    planContent += `\n[${iterKey}] Found ${urlMatches.length} sources:\n`;
                                    urlMatches.slice(0, 5).forEach(url => {
                                        planContent += `  • ${url}\n`;
                                    });
                                }
                            }
                        }
                        if (searchCount === 0) {
                            planContent += `\n⚠️  Web search enabled but no external data was needed for this goal.\n`;
                        }
                    } else {
                        planContent += `\nWeb search data: Processing current market information...\n`;
                    }

                    // Display agent outputs
                    planContent += `\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👥 AGENT OUTPUTS (First 500 chars each)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;

                    if (data.agent_outputs) {
                        if (data.agent_outputs.planner) {
                            planContent += `\n🎯 Planner Strategy:\n${data.agent_outputs.planner.substring(0, 500)}...\n`;
                        }
                        if (data.agent_outputs.verifier) {
                            planContent += `\n✅ Verifier Analysis:\n${data.agent_outputs.verifier.substring(0, 500)}...\n`;
                        }
                        if (data.agent_outputs.executor) {
                            planContent += `\n🚀 Executor Plan:\n${data.agent_outputs.executor.substring(0, 500)}...\n`;
                        }
                        if (data.agent_outputs.generator) {
                            planContent += `\n📝 Generator Summary:\n${data.agent_outputs.generator.substring(0, 500)}...\n`;
                        }
                    }

                    // Display full plan content
                    if (data.plan_content && data.plan_content.trim().length > 0) {
                        planContent += `\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 COMPLETE PLAN CONTENT (${data.plan_content.length} chars total)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
                        planContent += data.plan_content.substring(0, 3000);
                        if (data.plan_content.length > 3000) {
                            planContent += `\n\n[... ${data.plan_content.length - 3000} more characters saved to memory ...]\n`;
                        }
                    }

                    planContent += `\n\n📁 Full details saved to: ~/.../local-memory/plans/\n`;

                    addMessage(planContent, 'agent');
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

        // Initialize
        loadStatus();
        setInterval(loadStatus, 5000);
        input.focus();
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
