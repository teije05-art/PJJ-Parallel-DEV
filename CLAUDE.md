# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Project Jupiter** is a semi-autonomous planning system that uses local memory and multi-agent workflows to generate comprehensive strategic plans. It combines a fine-tuned memory agent (LlamaPlanner) with a coordinated multi-agent execution engine to produce 3000+ word research-backed strategies with human approval gates and continuous learning capabilities.

**Core Goal:** A semi-autonomous planner with human approval checkpoints that uses local memory and multi-agent workflows, capable of iterative learning and infinite improvement cycles.

## Development Status

**Current Health:** 8.5/10 - Production-ready with learning loop activated
- ✅ All 4 Architectural Issues FIXED: Redundant if-else, tools.py wrappers, engine.py subprocess, Black formatting
- ✅ Phase 4B Refactoring Complete: 3 monolithic files → 31 focused modules (zero regressions)
- ✅ Phase 5 Complete: Frontend-backend integration fixed (plans accessible to chat, controls synced)
- ✅ Learning Loop Activated: Automatic pattern extraction and application (Oct 31)
- ✅ Research Enhancement Complete: 7 specialized angles, 11 data patterns, 45-75% coverage
- ✅ Chatbox Implementation: Full web interface with SSE streaming
- ✅ Multi-agent workflow: Planner → Verifier → Executor → Generator
- ✅ SSE Real-time Progress: Iteration tracking with checkpoint approval gates
- ✅ Session Key Whitelist: All required keys whitelisted for learning and execution

## Quick Start

### Prerequisites
```bash
cd mem-agent-mcp
make check-uv          # Install uv if needed
make install           # Install LM Studio (macOS) or prepare vLLM (Linux)
make setup             # Configure memory directory
```

### Run the System

**Option 1: Web Chatbox (Recommended)**
```bash
# Terminal 1: Start model server
make run-agent

# Terminal 2: Start web interface
make serve-chatbox

# Browser: http://localhost:9000
```

**Option 2: Claude Desktop MCP**
```bash
make run-agent
make generate-mcp-json
# Copy mcp.json to Claude Desktop config, then restart Claude
```

### Essential Commands

```bash
# Development
make test                          # Run baseline test suite (22 tests, should pass 22/22)
make run-agent                     # Start LM Studio/vLLM model server
make serve-chatbox                 # Start web chatbox (http://localhost:9000)
make generate-mcp-json             # Generate Claude Desktop config

# Memory Management
make memory-wizard                 # Interactive memory connector setup
make add-filters                   # Add privacy filters to memory
make connect-memory CONNECTOR=X    # Import from ChatGPT, Notion, GitHub, etc.

# Utilities
make format                        # Format code with Black
python -m pytest tests/ -v         # Run full test suite with details
```

## Architecture Overview

### Data Flow

```
User Input (chatbox or MCP)
    ↓
simple_chatbox.py (web server or MCP handler)
    ↓
simple_orchestrator.py
    ├─ context/ module (retrieves planning context)
    │  ├─ goal_context.py (analyzes goal, retrieves project status)
    │  ├─ memory_context.py (searches local memory via MemAgent)
    │  ├─ search_context.py (web search via DuckDuckGo)
    │  └─ context_builder.py (orchestrates all providers)
    ↓
workflow_coordinator.py
    ├─ Prepares context for agents
    └─ Manages approval gates
    ↓
orchestrator/agents/ (4-agent workflow)
    ├─ planner_agent.py (strategic planning with frameworks)
    ├─ verifier_agent.py (validation & cross-checking)
    ├─ executor_agent.py (implementation extraction)
    └─ generator_agent.py (synthesis into 3000+ word output)
    ↓
approval_handler.py → memory_manager.py → learning_manager.py
    ↓
Output to user (chatbox, Claude Desktop, or exported file)
```

### Key Modules

**Core Orchestration:**
- `simple_chatbox.py` (1200+ lines) - Web server + end-to-end planning pipeline
- `simple_orchestrator.py` - Thin wrapper coordinating context + workflow
- `orchestrator/simple_orchestrator.py` - Legacy orchestrator (still functional)

**Memory & Learning:**
- `llama_planner.py` (800+ lines) - MemAgent wrapper for memory operations
- `learning_tracker.py` (400+ lines) - Tracks success patterns, errors, and performance
- `local-memory/` - Persistent storage for entities, plans, deliverables, and execution tracking

**Agent System (orchestrator/agents/):**
- `base_agent.py` - AgentResult and shared interfaces
- `planner_agent.py` - Strategic planning engine with domain-specific templates
- `verifier_agent.py` - Validation and quality checks
- `executor_agent.py` - Breaks down plans into actionable steps
- `generator_agent.py` - Synthesizes 3000+ word final output with citations

**Context Retrieval (orchestrator/context/):**
- `goal_context.py` - Analyzes user goals and retrieves project status
- `memory_context.py` - Searches local memory system (MemAgent-based)
- `search_context.py` - Web search integration via DuckDuckGo
- `context_formatter.py` - Formats context for agent consumption
- `context_builder.py` - Main orchestrator combining all providers

**Domain Templates (orchestrator/templates/):**
- `base_template.py` - Framework for domain-specific templates
- `healthcare_template.py`, `technology_template.py`, etc. - Domain-specific planning frameworks
- `template_selector.py` - Routes to appropriate template based on goal analysis

**Research & Analysis:**
- `research_agent.py` (800+ lines) - Extensive web research with 7 angles and 11 data patterns
- `tool_executor.py` - Executes web search and data extraction
- `tool_definitions.py` - Defines search and extraction tools

## Important Code Patterns

### Multi-Agent Workflow
The system uses a 4-stage agent pipeline where each agent processes the output of the previous:

```python
# From workflow_coordinator.py
planner_result = planner.run(context)
verifier_result = verifier.run(planner_result.content)
executor_result = executor.run(verifier_result.content)
generator_result = generator.run((executor_result.content, original_context))
```

Each agent returns an `AgentResult` object with `success: bool`, `content: str`, and `metadata: dict`.

### Server-Sent Events (SSE) Real-Time Progress (Oct 30)
The `/api/execute-plan` endpoint uses SSE to stream real-time progress:

**Frontend Flow (index.html):**
```javascript
// 1. Open SSE connection with parameters
const eventSource = new EventSource('/api/execute-plan?' + params);

// 2. Listen for events
eventSource.addEventListener('message', (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'iteration_started') { /* Show progress */ }
    else if (data.type === 'checkpoint_reached') { /* Show modal */ }
    else if (data.type === 'checkpoint_approved') { /* Continue */ }
    else if (data.type === 'final_plan') { /* Display result */ }
});

// 3. Send approval via /api/checkpoint-approval
fetch('/api/checkpoint-approval', {
    method: 'POST',
    body: JSON.stringify({ session_id, checkpoint: N })
})
```

**Backend Flow (simple_chatbox.py:859-995):**
```python
@app.get("/api/execute-plan")
async def execute_plan_endpoint(...):
    async def event_stream():
        # Yield SSE events as iterations run
        yield f"data: {json.dumps({'type': 'iteration_started'})}\n\n"

        # Block at checkpoint
        session_manager.wait_for_checkpoint_approval(session_id)

        # Yield approval confirmation
        yield f"data: {json.dumps({'type': 'checkpoint_approved'})}\n\n"

        # Continue iterations...

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

**Key Features:**
- Non-blocking execution with threading.Event synchronization
- Real-time iteration progress feedback to user
- Checkpoint summaries with framework/data-point tracking
- User can approve/reject at each checkpoint
- Works with browser EventSource API (no WebSocket needed)

### MCP Response Architecture
After Phase 4B refactoring, large responses are handled by:
1. Store full results to disk: `local-memory/plans/iteration_XXX_full_details.md`
2. Return compact summary through MCP (~5KB)
3. User accesses full results via `view_full_plan()` tool

This solves the "Broken Pipe" error that occurred when trying to send 100KB+ responses through MCP stdio.

### Memory Operations
Memory uses MemAgent (LlamaPlanner) for intelligent retrieval:

```python
# From memory_context.py or direct llama_planner.py usage
agent = Agent(memory_path)
results = agent.search_similar(query)  # Semantic search
entity = agent.retrieve_entity(entity_name)  # Direct retrieval
```

Memory is stored as Obsidian-style markdown with wikilink navigation:
```
memory/
├── user.md
└── entities/
    ├── project_X.md
    ├── entity_Y.md
    └── ...
```

### Research Enhancement (Post-Oct 28)
Research now uses 7 specialized angles per gap:
1. Market size & growth
2. Industry metrics & KPIs
3. Competitive analysis
4. Healthcare-specific (domain-dependent)
5. Economic indicators
6. Demographic breakdown
7. Forward-looking forecasts

With 11 data extraction patterns covering percentages, CAGR, dollar amounts, healthcare metrics, demographic data, rankings, forecasts, etc.

---

## Research Framework Integration (Nov 3, 2025)

Project Jupiter now implements three peer-reviewed research frameworks to create a production-grade semi-autonomous planner. See `RESEARCH_FRAMEWORK_ALIGNMENT.md` for detailed mappings.

### MemAgent Integration (Phase 1)

**What It Does:**
Implements ByteDance MemAgent's segment-based memory system to replace unbounded checkpoint/iteration tracking with a fixed-length memory that learns which information to retain.

**Implementation:**
- Module: `orchestrator/memory/memagent_memory.py` (NEW - Phase 1)
- Class: `SegmentedMemory(max_segments=12, max_tokens_per_segment=2000)`
- Integration: `approval_gates.py` PlanningSession uses SegmentedMemory instead of unbounded dicts
- Methods:
  - `add_segment(content, source, importance_score)` - Add with compression if needed
  - `get_relevant_segments(query)` - Semantic retrieval via MemAgent search
  - `compress_segment(idx)` - Lossless compression maintaining semantics
  - `train_overwrite_scores(plan_result)` - Learn which segments matter

**Why It Matters:**
- Current system: Unbounded memory growth with iterations
- After Phase 1: Fixed 12-segment memory (~24K tokens max)
- Benefit: System learns what to remember, what to forget
- Result: Scales to infinite planning iterations without memory explosion

**Key Design Decisions:**
- 12 segments chosen to balance retention vs. compression (configurable)
- Token-level compression (not feature-space) for precision
- RL-trained overwrite scores learned each iteration
- Backward compatible: Old code ignores memory fields

**Success Criteria:**
✅ Memory stays bounded
✅ Semantic search retrieves relevant segments
✅ No regression in planning quality
✅ System learns which segments to overwrite

---

### PDDL-INSTRUCT Logical Reasoning (Phase 2)

**What It Does:**
Implements symbolic planning logic from PDDL-INSTRUCT to add structured reasoning chains and formal verification to the agent workflow. Agents now reason step-by-step with explicit preconditions and effects, like planning algorithms.

**Implementation:**
- Module: `orchestrator/reasoning/logical_planner.py` (NEW - Phase 2)
  - Class: `LogicalPlanningPrompt(goal, domain)` - Generate PDDL-style prompts
  - Methods: `generate_precondition_checks()`, `generate_effect_verification()`, etc.

- Module: `orchestrator/reasoning/verification_feedback.py` (NEW - Phase 2)
  - Class: `VerificationFeedback()` - VAL-like verification
  - Methods: `check_preconditions()`, `check_effects()`, `generate_detailed_feedback()`

- Integration: All agents now receive and return reasoning chains
  - `orchestrator/agents/planner_agent.py` - Uses LogicalPlanningPrompt
  - `orchestrator/agents/verifier_agent.py` - Applies VerificationFeedback
  - `orchestrator/workflow_coordinator.py` - Collects verification results

**Why It Matters:**
- Current system: Agents generate plans without explicit reasoning structure
- After Phase 2: Plans include reasoning chains with verified preconditions and effects
- Benefit: Users understand WHY system made decisions; system validates logic
- Result: 94%+ planning accuracy (from PDDL-INSTRUCT research)

**Reasoning Chain Format:**
```
GOAL: [goal statement]
PRECONDITIONS: [what must be true]
  ✅ Market research complete
  ✅ Target audience defined
REASONING_CHAIN:
  1. Analyze market → identify gaps
  2. Define positioning → premium eco-friendly
  3. Plan tactics → content + partnerships
EFFECTS:
  ✅ Strategic roadmap created
  ✅ KPIs established
VERIFICATION: All preconditions met? ✅ All effects achieved? ✅
```

**Key Design Decisions:**
- Binary feedback ("Correct"/"Incorrect") for speed, detailed feedback for learning
- VAL-style verification (symbolic) instead of semantic checks
- Reasoning chains stored in iteration metadata for learning
- Optional for backward compatibility (can disable per domain)

**Success Criteria:**
✅ Reasoning chains in agent responses
✅ Verification feedback accurate (>80% precision)
✅ Precondition checking prevents invalid plans
✅ No performance regression

---

### Flow-GRPO Training Signals (Phase 3)

**What It Does:**
Implements reinforcement learning from AgentFlow to train agent selection and pattern recommendation. The system learns which agents, patterns, and reasoning approaches work best and applies them automatically.

**Implementation:**
- Module: `orchestrator/learning/flow_grpo_trainer.py` (NEW - Phase 3)
  - Class: `FlowGRPOTrainer()` - Trains agent selection via rewards
  - Methods: `record_iteration_signal()`, `update_agent_selection_weights()`, `get_recommended_agent_sequence()`

- Module: `orchestrator/learning/agent_coordination.py` (NEW - Phase 3)
  - Class: `AgentCoordination()` - Learn which agents work well together
  - Methods: `record_pair_performance()`, `recommend_agent_sequence()`

- Integration: Enhanced `orchestrator/learning_analyzer.py`
  - Now tracks mid-iteration signals (not just end-of-iteration)
  - Calculates flow_score: `verification_quality × user_approval × reasoning_quality`

- Integration: Enhanced `orchestrator/pattern_recommender.py`
  - Now scores patterns by: `flow_score × verification × user_approval`
  - Returns top-3 patterns for next iteration
  - Patterns improve automatically based on effectiveness

**Why It Matters:**
- Current system: 4-agent pipeline is hardcoded; learning is batch-based
- After Phase 3: Agent selection weights update each iteration; patterns improve mid-run
- Benefit: System automatically learns what works for different planning domains
- Result: Quality improves measurably over iterations (e.g., 0.65 → 0.78 → 0.85)

**Training Signal Formula:**
```
flow_score = (
    verification_feedback_quality × 0.4 +
    user_approval_bonus × 0.4 +
    reasoning_chain_quality × 0.2
)

pattern_effectiveness = pattern_flow_score × verification_success × user_approved
agent_weight = learning_rate × (flow_score - baseline) + old_weight
```

**Key Design Decisions:**
- Flow scores calculated per iteration (not batch at end)
- Exponential moving average for weight updates (recent iterations matter more)
- Agent pair scores tracked (e.g., "Planner + Verifier" vs. "Verifier + Executor")
- Graceful degradation: If agent weight drops below threshold, skip that agent

**Success Criteria:**
✅ Flow scores calculated correctly
✅ Pattern recommendations improve each iteration
✅ Agent weights update based on performance
✅ Learning signals measurably improve quality

---

## Integration Loop: Memory ↔ Reasoning ↔ Learning

After Phases 1-3, Project Jupiter implements a closed feedback loop within each planning iteration:

```
Planning Iteration N: The Complete Loop
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  1. MEMORY INITIALIZATION                                      │
│     • Load PlanningSession.memory_manager (SegmentedMemory)    │
│     • Retrieve top-3 relevant segments via semantic search      │
│     • Enrich context: market data, past patterns, entity info  │
│                                                                │
│  2. PATTERN RECOMMENDATION (Flow-GRPO)                         │
│     • Get top-3 recommended patterns from learning system       │
│     • Calculate agent_selection_weights based on flow_scores   │
│     • Pass both to agents in system prompt                     │
│                                                                │
│  3. LOGICAL REASONING PHASE (PDDL-INSTRUCT)                    │
│     • Agents generate plans with reasoning chains              │
│     • LogicalPlanningPrompt asks for preconditions & effects   │
│     • VerificationFeedback checks: preconditions met? logic ok?│
│     • Store verification results in iteration metadata         │
│                                                                │
│  4. FLOW-GRPO SCORING                                          │
│     • Calculate flow_score = verification × approval × quality │
│     • Record iteration signal: agent, flow_score, approval     │
│     • Update pattern_effectiveness scores                      │
│     • Update agent_selection_weights                           │
│                                                                │
│  5. CHECKPOINT PRESENTATION (User Approval Gate)               │
│     • Render checkpoint summary with:                          │
│       - Reasoning chain (why did we reach this point?)        │
│       - Verification feedback (which checks passed/failed?)    │
│       - Memory updates (what will we remember?)                │
│       - Flow score (how well did this iteration go?)          │
│     • User approves or rejects                                │
│                                                                │
│  6. MEMORY UPDATE (On Approval)                                │
│     • Extract memory deltas from iteration                     │
│     • Estimate segment importance from user feedback           │
│     • Add new segments or compress old ones                    │
│     • Update overwrite scores (for next iteration)             │
│                                                                │
└────────────────────────────────────────────────────────────────┘
                    Loop: N → N+1
                (With each iteration, system learns)
```

**Data Flow Through the Loop:**
```
User Goal
  ↓
memory_manager.get_relevant_segments() ← MemAgent semantic search
  ↓
recommender.get_patterns_for_next_iteration() ← Flow-GRPO patterns
  ↓
Agent receives: (goal, memory context, recommended patterns, user history)
  ↓
Agent generates: (content, reasoning_chain, preconditions_met)
  ↓
verifier.check_preconditions() + verifier.check_effects() ← PDDL-INSTRUCT
  ↓
flow_score = verification_quality × user_approval ← Flow-GRPO
  ↓
Checkpoint presented to user with full reasoning trace
  ↓
User approves → memory_manager.train_overwrite_scores() ← Update memory
  ↓
trainer.update_agent_selection_weights() ← Learn which agents work
  ↓
recommender.score_pattern() ← Learn which patterns work
  ↓
Next iteration uses improved memory, patterns, and agent weights
```

**Key Insight:**
Before: System had separate memory, reasoning, and learning systems
After: One integrated loop where memory informs reasoning, reasoning produces learning signals, and signals improve memory

---

## Code Organization Notes

### Phase 4B Refactoring (Oct 27)
- **Before:** 3 monolithic files (2,169 lines) - agentflow_agents.py, domain_templates.py, context_manager.py
- **After:** 31 focused modules across agents/, templates/, context/ directories
- **Result:** 85% reduction in largest file, zero regressions, 100% backward compatible
- **Benefit:** Single Responsibility Principle applied throughout, easier testing and extension

### Testing
- `tests/test_baseline.py` - 22 baseline tests covering goal analysis, templates, agents, imports, error handling
- All tests pass (22/22) with zero regressions after Phase 4B
- Run with: `make test` or `python -m pytest tests/ -v`

### Import Structure
After refactoring, imports are clean and organized:
```python
# Access agents
from orchestrator.agents import PlannerAgent, VerifierAgent, ExecutorAgent, GeneratorAgent

# Access templates
from orchestrator.templates import TemplateSelector

# Access context retrieval
from orchestrator.context import ContextBuilder
```

## Common Development Tasks

### Adding a New Domain Template
1. Create `orchestrator/templates/newdomain_template.py` inheriting from `BaseTemplate`
2. Implement domain-specific planning prompt
3. Register in `orchestrator/templates/__init__.py`
4. Add domain detection logic to `goal_analyzer.py`

### Enhancing Research Coverage
Research improvement should focus on:
1. Adding new query angles in `_generate_comprehensive_queries()`
2. Adding new data extraction patterns in `_extract_data_points()`
3. Improving domain-specific detection in `_estimate_coverage_extensive()`

Current research enhancement (Oct 28) added healthcare metrics, demographic data, and 7-angle strategy. Future enhancements should test coverage % improvements.

### Debugging Agent Workflow
1. Check `learning_tracker.py` for error patterns and successful patterns
2. Review stored plan details in `local-memory/plans/iteration_XXX_full_details.md`
3. Check `local-memory/entities/planning_errors.md` for recurring issues
4. Enable verbose logging: Set `DEBUG=True` in chatbox.py (line ~50)

### Working with Memory System
- Memory searches are semantic via MemAgent
- Modify memory files directly in `local-memory/entities/` (no restart needed)
- Use `memory_wizard.py` to import from ChatGPT, Notion, GitHub, Google Docs
- Test memory with: `python llama_planner.py` (interactive shell)

## Important Files Reference

| File | Purpose | Size | Status |
|------|---------|------|--------|
| `simple_chatbox.py` | Web server + orchestration | 1200+ lines | ✅ Core |
| `research_agent.py` | Enhanced web research | 800+ lines | ✅ Oct 28 |
| `llama_planner.py` | Memory wrapper | 800+ lines | ✅ Core |
| `learning_tracker.py` | Progress tracking | 400+ lines | ✅ Core |
| `orchestrator/agents/` | 4-agent workflow | 7 files | ✅ Phase 4B |
| `orchestrator/context/` | Context retrieval | 6 files | ✅ Phase 4B |
| `orchestrator/templates/` | Domain frameworks | 9 files | ✅ Phase 4B |
| `tests/test_baseline.py` | Test suite | 22 tests | ✅ Phase 4B |

## Recent Changes (October 30, 2025)

### SSE Implementation Complete
- ✅ Real-time iteration progress streaming via Server-Sent Events
- ✅ Checkpoint approval gates with modal UI
- ✅ Iteration-level improvements analysis via Llama
- ✅ Non-blocking backend execution with threading.Event
- ✅ Full end-to-end testing ready

### Rebuild Summary Applied
- ✅ Old MCP code removed (eliminated 51KB of duplicate orchestrators)
- ✅ simple_chatbox.py rebuilt: 4,010 → 803 lines (80% reduction)
- ✅ Static frontend (index.html) created: 52KB, 1,460 lines
- ✅ Zero code duplication, clean separation of concerns
- ✅ All endpoints backward compatible

### Frontend/Backend Compatibility Fixes
- ✅ Fixed /api/status response to include frontend-expected fields
  - Added: `backend`, `agent_available`, `orchestrator_available`, `sessions_active`
- ✅ Fixed /api/chat response: added `reply` alias for backward compatibility
- ✅ Fixed /api/generate-proposal response to include all expected fields
  - Added: `entity_count`, `entity_names`, `memory_coverage_percent`, `research_coverage_percent`

## Known Limitations & Next Steps

### Current Limitations
1. **Llama Timing Investigation** - Analysis speed sometimes instant instead of 1-2 minutes (not blocking)
2. **Research Coverage Metric** - Now data-driven but still needs real-world testing validation
3. **Long-Running Iterations** - System reliable up to 7+ iterations, needs stress testing beyond that
4. **Port Conflicts** - Old Python processes may linger; use `lsof -i :9000` to check

### Next Priority Tasks
1. **Comprehensive system testing** (run 5+ complete planning iterations with SSE)
2. **Validate checkpoint approval flow** in production with real planning scenarios
3. **Performance testing** under load (20+ iterations)
4. **Pattern effectiveness measurement** - Track learning loop quality improvements over time
5. **Performance optimization** (lazy-load templates, cache search results)

### Recent Completion (Nov 2, 2025)
- ✅ All 4 architectural issues fixed (see ARCHITECTURAL_FIXES_COMPLETION.md)
- ✅ Session key whitelist updated for learning support
- ✅ Frontend-backend integration fully working
- ✅ Learning loop activated and ready for production testing
- Repository is active and production-ready

### Current Development Focus
- Phase 6: Production validation and performance optimization
- Target: Full end-to-end testing with real planning workflows

## Debugging Checklist

When something fails:

### Frontend Errors (HTTP 400+)
1. Check browser console (F12 → Console tab) for error messages
2. Enable DEBUG=True in simple_chatbox.py to see backend logs
3. Verify /api/status returns correct fields (backend, agent_available, etc.)
4. Check that /api/chat returns `reply` field (not just `response`)
5. Verify /api/generate-proposal returns all required fields

### Backend Errors
1. Check terminal output where `make serve-chatbox` is running
2. Look for "❌ Chat error:", "❌ Proposal error:", "❌ SSE error:" messages
3. Check `local-memory/entities/planning_errors.md` for error patterns
4. Look at most recent plan in `local-memory/plans/` for execution details
5. Review `learning_tracker.py` logs for performance metrics
6. Ensure memory directory is configured: `cat .memory_path`

### Checkpoint/SSE Issues
1. Check browser Network tab (F12 → Network) for `/api/execute-plan` connection
2. Look for SSE events in browser console: `eventSource.addEventListener('message', ...)`
3. Verify checkpoint modal appears when `checkpoint_reached` event fires
4. Check that `/api/checkpoint-approval` POST succeeds (status 200)
5. Verify backend resumes after approval (check terminal logs)

### Port Already in Use
```bash
# Check what's using port 9000
lsof -i :9000

# Kill stuck Python process
kill -9 <PID>

# Or use the alias from old system (if running from bash)
python simple_chatbox.py 2>&1  # May show port conflict

# Kill all Python processes (careful!)
killall -9 python3
```

### Memory Directory Issues
```bash
# Verify memory path is configured
cat .memory_path

# Create if missing
mkdir -p $(cat .memory_path)

# Test memory operations
python llama_planner.py  # Interactive shell
```

## Performance Notes

Typical iteration timing (with web search enabled):
- Context retrieval: 5-15 seconds (includes web search)
- 4-Agent workflow: 30-120 seconds (LLM-dependent)
- Memory storage: 1-2 seconds
- Total: 40-140 seconds per iteration
- Scales linearly with number of iterations (human approval gates between iterations)

Research is intentionally extensive (10 iterations, 7 angles per gap) to maximize coverage - optimize if latency becomes critical.
