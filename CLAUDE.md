# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mem-agent-mcp** is a semi-autonomous planning system that uses local memory and multi-agent workflows to generate comprehensive strategic plans. It combines a fine-tuned memory agent (LlamaPlanner) with a coordinated multi-agent execution engine to produce 3000+ word research-backed strategies with human approval gates.

**Core Goal:** A semi-autonomous planner with human approval checkpoints that uses local memory and multi-agent workflows, capable of iterative learning and improvement.

## Development Status

**Current Health:** 7.6/10 - Production-ready for beta testing
- ✅ Phase 4B Refactoring Complete: 3 monolithic files → 31 focused modules (zero regressions)
- ✅ Research Enhancement Complete: 7 specialized angles, 11 data patterns, 45-75% coverage
- ✅ Chatbox Implementation: Full web interface (alternative to MCP)
- ✅ Multi-agent workflow: Planner → Verifier → Executor → Generator
- ⏳ Minor: Llama timing investigation (not blocking)

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

## Known Limitations & Next Steps

### Current Limitations
1. **Llama Timing Investigation** - Analysis speed sometimes instant instead of 1-2 minutes (need logging to verify)
2. **Research Coverage Metric** - Now data-driven but still needs real-world testing validation
3. **Long-Running Iterations** - System reliable up to 7+ iterations, needs stress testing beyond that

### Next Priority Tasks (Not implemented)
1. Comprehensive system testing (run 5+ complete planning iterations)
2. Validate research coverage percentages in practice
3. Investigate and fix Llama analysis timing issue
4. Performance optimization (lazy-load templates, cache search results)
5. Unit tests for individual context providers and agents

### Git Notes
- Repository is active (Oct 28 2025 most recent)
- Major phases completed: Refactoring (Phase 4B), Research Enhancement (Oct 28)
- Ready for next development phase: testing and validation

## Debugging Checklist

When something fails:
1. Check `local-memory/entities/planning_errors.md` for error patterns
2. Look at most recent plan in `local-memory/plans/` for execution details
3. Review `learning_tracker.py` logs for performance metrics
4. Check MCP response size (if using Claude Desktop) - should be compact summary
5. Verify research tool found data (check coverage % in proposal)
6. Ensure memory directory is configured: `cat .memory_path`

## Performance Notes

Typical iteration timing (with web search enabled):
- Context retrieval: 5-15 seconds (includes web search)
- 4-Agent workflow: 30-120 seconds (LLM-dependent)
- Memory storage: 1-2 seconds
- Total: 40-140 seconds per iteration
- Scales linearly with number of iterations (human approval gates between iterations)

Research is intentionally extensive (10 iterations, 7 angles per gap) to maximize coverage - optimize if latency becomes critical.
