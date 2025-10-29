# Phase 1: Dependency Map & Current System State

**Date:** October 27, 2025

**Purpose:** Document all file dependencies and relationships before refactoring.

---

## File Dependency Graph

### Entry Point: simple_chatbox.py
```
simple_chatbox.py (browser UI)
  ↓
simple_orchestrator.py (main coordinator)
  ├── imports Agent (MCP)
  ├── imports ContextManager
  ├── imports WorkflowCoordinator
  ├── imports ApprovalHandler
  ├── imports MemoryManager
  └── imports LearningManager
```

### Layer 1: SimpleOrchestrator (simple_orchestrator.py - 312 lines)

**File:** `orchestrator/simple_orchestrator.py`

**Imports:**
- `Agent` (from `agent.py`)
- `ContextManager` (from `orchestrator/context_manager.py`)
- `WorkflowCoordinator` (from `orchestrator/workflow_coordinator.py`)
- `ApprovalHandler` (from `orchestrator/approval_handler.py`)
- `MemoryManager` (from `orchestrator/memory_manager.py`)
- `LearningManager` (from `orchestrator/learning_manager.py`)

**Exports:**
- `SimpleOrchestrator` class

**Key Methods:**
- `__init__()` - Initializes all modules
- `run_enhanced_learning_loop(goal)` - Main entry point
- `_initialize_memory_entities()` - Setup
- Backward compatibility wrappers

**Called by:** `simple_chatbox.py`

**Calls:** All 5 major modules

---

### Layer 2A: ContextManager (context_manager.py - 350 lines)

**File:** `orchestrator/context_manager.py`

**Imports:**
- `Agent` (from `agent.py`)
- `GoalAnalyzer` (from `orchestrator/goal_analyzer.py`)
- (Indirectly imports search_module via goal analysis)

**Exports:**
- `ContextManager` class

**Key Methods:**
- `retrieve_context(goal)` - Main entry
- `_retrieve_project_status(goal_analysis)` - Gets memory data
- `_retrieve_successful_patterns()` - Gets memory data
- `_retrieve_error_patterns()` - Gets memory data
- `_retrieve_execution_history()` - Gets memory data
- `_retrieve_agent_performance()` - Gets memory data
- `_retrieve_web_search_results(goal, goal_analysis)` - **Does web search!**

**Called by:** `SimpleOrchestrator.run_enhanced_learning_loop()`

**Calls:**
- `GoalAnalyzer.analyze_goal()`
- `Agent.chat()` (for memory queries)
- Web search implementation (internal to this file)

**Data Flow:**
```
goal → analyze → retrieve 5 memory pieces + web search → combine → return context dict
```

---

### Layer 2B: WorkflowCoordinator (workflow_coordinator.py - 67 lines)

**File:** `orchestrator/workflow_coordinator.py`

**Imports:**
- `Agent` (from `agent.py`)
- `AgentCoordinator` (from `orchestrator/agentflow_agents.py`)
- `AgentResult` (from `orchestrator/agentflow_agents.py`)

**Exports:**
- `WorkflowCoordinator` class
- Re-exports `AgentResult`

**Key Methods:**
- `run_workflow(goal, context)` - Main entry
  - Calls `self.agent_coordinator.coordinate_agentic_workflow(goal, context)`

**Called by:** `SimpleOrchestrator.run_enhanced_learning_loop()`

**Calls:** `AgentCoordinator.coordinate_agentic_workflow()`

**Data Flow:**
```
goal + context → AgentCoordinator → 4 agents execute → results dict
```

---

### Layer 2C: ApprovalHandler (approval_handler.py - 127 lines)

**File:** `orchestrator/approval_handler.py`

**Imports:**
- (No internal dependencies)

**Exports:**
- `ApprovalHandler` class
- `ApprovalDecision` dataclass

**Key Methods:**
- `get_approval(agent_results, goal)` - Main entry (terminal input)
- `request_approval(iteration_result)` - New checkpoint-based approval

**Called by:** `SimpleOrchestrator.run_enhanced_learning_loop()`

**Calls:** None (only input/output)

**Data Flow:**
```
agent_results → ask user → return decision/feedback
```

---

### Layer 2D: MemoryManager (memory_manager.py - 291 lines)

**File:** `orchestrator/memory_manager.py`

**Imports:**
- `Agent` (from `agent.py`)

**Exports:**
- `MemoryManager` class

**Key Methods:**
- `store_results(goal, agent_results, success)` - Main entry
- Various `_write_*()` methods for storage

**Called by:** `SimpleOrchestrator.run_enhanced_learning_loop()`

**Calls:** `Agent.chat()` (for memory operations)

**Data Flow:**
```
agent_results → format → write to memory entities → return
```

---

### Layer 2E: LearningManager (learning_manager.py - 161 lines)

**File:** `orchestrator/learning_manager.py`

**Imports:**
- `Agent` (from `agent.py`)

**Exports:**
- `LearningManager` class

**Key Methods:**
- `apply_learning(agent_results, feedback, success)` - Main entry

**Called by:** `SimpleOrchestrator.run_enhanced_learning_loop()`

**Calls:** `Agent.chat()` (for Flow-GRPO training)

**Data Flow:**
```
agent_results + feedback → train → update memory
```

---

### Layer 3A: AgentCoordinator (agentflow_agents.py - 1,036 lines)

**File:** `orchestrator/agentflow_agents.py` ⚠️ **MONOLITHIC - TO BE SPLIT**

**Imports:**
- `Agent` (from `agent.py`)
- `GoalAnalyzer` (from `orchestrator/goal_analyzer.py`)
- `DomainTemplates` (from `orchestrator/domain_templates.py`)

**Exports:**
- `AgentResult` dataclass ✅ (used everywhere)
- `BaseAgent` class
- `PlannerAgent` class (lines 71-250)
- `VerifierAgent` class (lines 251-500)
- `ExecutorAgent` class (lines 501-750)
- `GeneratorAgent` class (lines 751-1000)
- `AgentCoordinator` class (lines 1001-1036)

**Key Methods (per agent):**
- `PlannerAgent.generate_strategic_plan(goal, context)` → `AgentResult`
- `VerifierAgent.verify_plan(planner_result)` → `AgentResult`
- `ExecutorAgent.execute_plan(verifier_result)` → `AgentResult`
- `GeneratorAgent.generate_summary(executor_result)` → `AgentResult`

**AgentCoordinator:**
- `coordinate_agentic_workflow(goal, context)` → dict of 4 results

**Called by:** `WorkflowCoordinator.run_workflow()`

**Calls:**
- `GoalAnalyzer.analyze_goal()`
- `DomainTemplates.get_planning_prompt()`
- `Agent.chat()` (for model execution)

**Data Flow:**
```
goal + context
  → Planner (strategic_plan)
  → Verifier (verification)
  → Executor (implementation)
  → Generator (synthesis)
  → results dict
```

**REFACTORING OPPORTUNITY:**
- Currently contains 4 different agents (should be 4 files)
- `BaseAgent` class is good foundation (extract to shared file)
- Each agent should be: `{name}_agent.py` (250-300 lines each)
- `AgentCoordinator` orchestrates the 4 (50 lines)

---

### Layer 3B: DomainTemplates (domain_templates.py - 783 lines)

**File:** `orchestrator/domain_templates.py` ⚠️ **MONOLITHIC - TO BE SPLIT**

**Imports:**
- (No dependencies, pure data)

**Exports:**
- `DomainTemplates` class

**Key Methods:**
- `get_planning_prompt(goal_analysis, context)` - Main entry
  - Selects template based on goal_analysis.domain
  - Formats template with context
  - Returns prompt string

**Called by:** `PlannerAgent.generate_strategic_plan()`

**Calls:** None (pure Python string formatting)

**Data Flow:**
```
goal_analysis + context → select template → format → return prompt string
```

**Contains (7 templates):**
1. Healthcare template (lines 100-180)
2. Technology template (lines 181-260)
3. Manufacturing template (lines 261-340)
4. QSR template (lines 341-420)
5. Retail template (lines 421-500)
6. Financial Services template (lines 501-580)
7. General/Default template (lines 581-783)

**REFACTORING OPPORTUNITY:**
- Each template is 80-200 lines
- All follow same structure (sections with placeholders)
- Should have `BaseTemplate` class (100 lines)
- Each domain in separate file: `{domain}_template.py` (100-120 lines each)
- `TemplateSelector` class (50 lines) to choose right template

---

### Layer 3C: GoalAnalyzer (goal_analyzer.py - 496 lines)

**File:** `orchestrator/goal_analyzer.py`

**Imports:**
- (No dependencies)

**Exports:**
- `GoalAnalyzer` class
- `GoalAnalysis` dataclass

**Key Methods:**
- `analyze_goal(goal)` → `GoalAnalysis`
- `_detect_domain()` - Weighted scoring (recently fixed!)
- `_analyze_industry()` - Industry classification
- `_extract_market_info()` - Market detection

**Called by:**
- `ContextManager.retrieve_context()`
- `PlannerAgent.generate_strategic_plan()`
- `SearchModule` (for web search queries)

**Calls:** None (pure analysis)

**Data Flow:**
```
goal → analyze → return GoalAnalysis(domain, industry, market, ...)
```

**Status:** ✅ Recently refactored with weighted scoring system. Good shape.

---

### Layer 4: SearchModule (search_module.py - 179 lines)

**File:** `orchestrator/search_module.py`

**Imports:**
- (External: duckduckgo_search)

**Exports:**
- `SearchModule` class
- Various search functions

**Key Methods:**
- `comprehensive_web_search(goal, goal_analysis)` - Main entry
- `_search_market_analysis()` - Specific searches
- `_search_competitive_landscape()` - Specific searches
- `_search_case_studies()` - Specific searches
- `_search_trends()` - Specific searches
- `_search_regulatory()` - Specific searches
- `_search_expert_insights()` - Specific searches

**Called by:** `ContextManager._retrieve_web_search_results()`

**Calls:** `duckduckgo_search` library

**Data Flow:**
```
goal + goal_analysis → run 24 searches → collect 120+ results → format as markdown → return 30KB+ string
```

**Status:** ✅ Working well. Returns domain-aware search results (fixed from previous bug).

---

## Dependency Chains

### Chain 1: User Query → Planning
```
simple_chatbox.py
  └─ SimpleOrchestrator.run_enhanced_learning_loop(goal)
     ├─ ContextManager.retrieve_context(goal)
     │  ├─ GoalAnalyzer.analyze_goal(goal)
     │  └─ SearchModule.comprehensive_web_search(goal, analysis)
     │
     ├─ WorkflowCoordinator.run_workflow(goal, context)
     │  └─ AgentCoordinator.coordinate_agentic_workflow(goal, context)
     │     ├─ PlannerAgent.generate_strategic_plan(goal, context)
     │     │  ├─ GoalAnalyzer.analyze_goal(goal) [REPEATED]
     │     │  └─ DomainTemplates.get_planning_prompt(analysis, context)
     │     │
     │     ├─ VerifierAgent.verify_plan(planner_result)
     │     ├─ ExecutorAgent.execute_plan(verifier_result)
     │     └─ GeneratorAgent.generate_summary(executor_result)
     │
     ├─ ApprovalHandler.get_approval(agent_results, goal)
     ├─ MemoryManager.store_results(goal, agent_results, success)
     └─ LearningManager.apply_learning(agent_results, feedback, success)
```

**Observations:**
- `GoalAnalyzer.analyze_goal()` called **twice** (in ContextManager and PlannerAgent)
- Possible caching opportunity
- Overall flow is linear and understandable

### Chain 2: Data Transformations
```
Raw goal string
  ↓ (ContextManager)
  → GoalAnalysis object
  ↓
  → Full context dict (6 components)
  ↓ (WorkflowCoordinator)
  → Passed to 4 agents
  ↓ (Each agent)
  → AgentResult (success, output, metadata, timestamp)
  ↓ (AgentCoordinator)
  → Dict of 4 AgentResults
  ↓ (ApprovalHandler)
  → ApprovalDecision
  ↓ (MemoryManager)
  → Stored as multiple entities
  ↓ (simple_chatbox.py)
  → Displayed to user
```

**This is where 9,593 chars can be lost!**
- Each transformation point is potential loss
- Need to track sizes at each step
- Refactored version will have fewer transformation points

---

## Files NOT Being Refactored (Stable)

These files are working well and should remain as-is:

1. **orchestrator/goal_analyzer.py** (496 lines)
   - Recently fixed with weighted scoring
   - Stable, working correctly
   - Keep as-is

2. **orchestrator/approval_handler.py** (127 lines)
   - Simple approval flow
   - Clean implementation
   - Keep as-is

3. **orchestrator/memory_manager.py** (291 lines)
   - Storage is working
   - Keep as-is

4. **orchestrator/learning_manager.py** (161 lines)
   - Flow-GRPO training logic
   - Keep as-is

5. **orchestrator/search_module.py** (179 lines)
   - Web search working correctly
   - Keep as-is

6. **orchestrator/__init__.py**
   - Keep as-is

---

## Files Being Refactored (Critical)

### 1. agentflow_agents.py (1,036 lines) → Split into:
```
orchestrator/agents/
├── __init__.py (30 lines)
├── base_agent.py (150 lines) - Common logic
├── planner_agent.py (250 lines)
├── verifier_agent.py (200 lines)
├── executor_agent.py (180 lines)
├── generator_agent.py (150 lines)
└── agent_factory.py (50 lines) - Factory + coordinator
```

**Total:** 1,010 lines (slightly less than original due to reduced duplication)

### 2. domain_templates.py (783 lines) → Split into:
```
orchestrator/templates/
├── __init__.py (30 lines)
├── base_template.py (100 lines) - Framework
├── healthcare_template.py (120 lines)
├── technology_template.py (120 lines)
├── manufacturing_template.py (120 lines)
├── qsr_template.py (120 lines)
├── retail_template.py (120 lines)
├── financial_template.py (120 lines)
├── general_template.py (120 lines)
└── template_selector.py (50 lines)
```

**Total:** 1,000 lines (more files but similar total, much clearer organization)

### 3. context_manager.py (350 lines) → Keep but refactor:
```
orchestrator/context/
├── __init__.py (30 lines)
├── context_builder.py (150 lines) - Orchestrates gathering
├── goal_context.py (80 lines) - Goal analysis
├── memory_context.py (80 lines) - Memory retrieval
├── search_context.py (100 lines) - Web search
└── context_formatter.py (50 lines) - Final formatting
```

**Total:** 490 lines (more detailed breakdown, but same functionality)

### 4. simple_orchestrator.py (312 lines) → Simplify to (200 lines):
- Remove backward compatibility code (needed for MCP only)
- Simplify import statements
- Cleaner main loop logic

---

## Expected Changes After Refactoring

### Before (Current)
- 3,832 total lines
- 11 files
- 3 monolithic files doing 4-7 things each
- 7+ data transformation points

### After (Proposed)
- ~2,900 total lines (24% reduction)
- 35+ files (clearer organization)
- Each file: single responsibility
- 2-3 data transformation points (less chance of loss)

### Code Organization
- **Agents:** 4 separate files instead of 1 monolithic file
- **Templates:** 7 separate files instead of 1 monolithic file
- **Context:** 5 separate providers instead of 1 mixed-concern file
- **Orchestration:** Simplified main coordinator

---

## Testing Strategy

### Test Suite Structure
```
tests/
├── test_orchestrator.py (Integration tests)
├── test_context_manager.py (Context retrieval)
├── test_workflow_coordinator.py (Agent workflow)
├── test_agents/
│   ├── test_planner_agent.py
│   ├── test_verifier_agent.py
│   ├── test_executor_agent.py
│   └── test_generator_agent.py
├── test_templates/
│   ├── test_template_selection.py
│   └── test_domain_templates.py
└── test_integration/
    ├── test_content_preservation.py (9,593 char test!)
    └── test_approval_workflow.py
```

### Key Test Cases
1. **Content Preservation:** Full iteration produces 9,593 chars consistently
2. **Agent Output:** Each agent produces expected output
3. **Template Selection:** Domain detection selects correct template
4. **Approval Workflow:** Checkpoint approval works correctly
5. **Error Handling:** Errors are caught and displayed
6. **Memory Storage:** Results stored correctly
7. **No Regressions:** Old tests still pass with new code

---

## Checklist for Phase 1 Completion

- [ ] Create `test_baseline.py` - Baseline behavior tests
- [ ] Create `test_suite.py` - Main test suite
- [ ] Run baseline tests with current code
- [ ] Document baseline results (metrics)
- [ ] Create directory structure documentation
- [ ] Map all imports and dependencies
- [ ] Identify potential circular dependencies
- [ ] List all public APIs (must not change)
- [ ] Prepare rollback plan
- [ ] Get user confirmation to proceed to Phase 2

---

## Next Steps

Once Phase 1 is complete:
1. **Phase 2:** Create new directory structure + refactored code
2. **Phase 3:** Run tests, compare outputs
3. **Phase 4:** Switch orchestrator to new code
4. **Phase 5:** Clean up old monolithic files
5. **Phase 6:** Documentation updates

---

**Status:** Ready to create test suite and baseline documentation.
