# AI Planner System Modularization Plan

## Current Problem
The orchestrator and agent scripts contain 10-20 interdependent functions, causing error loops where fixing one issue breaks another. The system needs to be split into independent modules that can be called separately.

## Proposed Module Architecture

### 1. **Context Module** (`context_manager.py`)
**Single Responsibility**: Retrieve and prepare context for planning

```python
class ContextManager:
    def retrieve_context(self, goal: str) -> Dict:
        """Main entry point - returns all context needed"""
        pass

    def _analyze_goal(self, goal: str) -> GoalAnalysis:
        """Analyzes goal to determine domain, industry, etc."""
        pass

    def _select_entities(self, analysis: GoalAnalysis) -> List[str]:
        """Selects relevant entity files based on analysis"""
        pass

    def _load_patterns(self) -> Patterns:
        """Loads successful and error patterns"""
        pass
```

**No dependencies on**: Agent execution, workflow coordination, memory writing

---

### 2. **Agent Module** (`agents/`)
Split the monolithic agents into separate files:

```
agents/
├── base_agent.py          # Base agent class with common functionality
├── planner_agent.py       # Strategic planning only
├── verifier_agent.py      # Verification only
├── executor_agent.py      # Execution only
├── generator_agent.py     # Content synthesis only
└── agent_interface.py     # Simple interface for calling agents
```

**Each agent**:
- Takes input (goal + context)
- Returns output (its specific result)
- Has NO knowledge of other agents
- Has NO knowledge of memory storage
- Has NO knowledge of approval workflow

**Example**:
```python
# agents/planner_agent.py
class PlannerAgent:
    def generate_plan(self, goal: str, context: Dict) -> str:
        """Generates strategic plan. That's it."""
        # Only planning logic here
        pass
```

---

### 3. **Workflow Module** (`workflow_coordinator.py`)
**Single Responsibility**: Call agents in sequence and combine results

```python
class WorkflowCoordinator:
    def __init__(self):
        self.planner = PlannerAgent()
        self.verifier = VerifierAgent()
        self.executor = ExecutorAgent()
        self.generator = GeneratorAgent()

    def run_workflow(self, goal: str, context: Dict) -> WorkflowResults:
        """Runs agents in sequence, returns combined results"""
        plan = self.planner.generate_plan(goal, context)
        verification = self.verifier.verify(plan, context)
        execution = self.executor.execute(plan, context)
        final = self.generator.synthesize(plan, verification, execution)

        return WorkflowResults(plan, verification, execution, final)
```

**No dependencies on**: Memory storage, approval workflow, learning

---

### 4. **Approval Module** (`approval_handler.py`)
**Single Responsibility**: Handle human approval workflow

```python
class ApprovalHandler:
    def get_approval(self, results: WorkflowResults) -> ApprovalDecision:
        """Shows results to user, gets decision"""
        pass

    def _display_results(self, results: WorkflowResults):
        """Formats and displays results"""
        pass

    def _get_user_input(self) -> str:
        """Gets user decision (y/n/edit)"""
        pass
```

**No dependencies on**: Context retrieval, agent execution, memory storage

---

### 5. **Memory Module** (`memory_manager.py`)
**Single Responsibility**: Store results and update memory

```python
class MemoryManager:
    def store_results(self, goal: str, results: WorkflowResults, success: bool):
        """Main entry point - stores everything"""
        pass

    def _save_plan_file(self, goal: str, results: WorkflowResults):
        """Saves to plans/ directory"""
        pass

    def _update_patterns(self, results: WorkflowResults, success: bool):
        """Updates successful/error patterns"""
        pass

    def _update_execution_log(self, goal: str, success: bool):
        """Updates execution log"""
        pass

    def _populate_entities(self, results: WorkflowResults):
        """Populates entity files"""
        pass
```

**No dependencies on**: Context retrieval, agent execution, approval

---

### 6. **Learning Module** (`learning_manager.py`)
**Single Responsibility**: Apply training signals and improve system

```python
class LearningManager:
    def apply_learning(self, results: WorkflowResults, feedback: str):
        """Applies Flow-GRPO training and learns from iteration"""
        pass

    def _apply_flow_grpo(self, results: WorkflowResults):
        """Applies Flow-GRPO training"""
        pass

    def _update_performance_metrics(self, results: WorkflowResults):
        """Updates agent performance metrics"""
        pass
```

**No dependencies on**: Context retrieval, approval, memory storage

---

### 7. **Orchestrator** (`simple_orchestrator.py`)
**Single Responsibility**: Call modules in order

```python
class SimpleOrchestrator:
    def __init__(self):
        self.context_manager = ContextManager()
        self.workflow_coordinator = WorkflowCoordinator()
        self.approval_handler = ApprovalHandler()
        self.memory_manager = MemoryManager()
        self.learning_manager = LearningManager()

    def run(self, goal: str):
        """Simple sequential execution"""
        # Step 1: Get context
        context = self.context_manager.retrieve_context(goal)

        # Step 2: Run workflow
        results = self.workflow_coordinator.run_workflow(goal, context)

        # Step 3: Get approval
        decision = self.approval_handler.get_approval(results)

        if decision.approved:
            # Step 4: Store results
            self.memory_manager.store_results(goal, results, success=True)

            # Step 5: Apply learning
            self.learning_manager.apply_learning(results, decision.feedback)
        else:
            # Store as failure for learning
            self.memory_manager.store_results(goal, results, success=False)
```

**Key difference**: The orchestrator is now SIMPLE - it just calls modules. Each module is independent and can be tested/fixed separately.

---

## Benefits of This Architecture

### 1. **Independent Testing**
- Test context retrieval without running agents
- Test agents without touching memory
- Test approval workflow in isolation

### 2. **Easy Debugging**
- Error in planning? Only look at `planner_agent.py`
- Error in memory storage? Only look at `memory_manager.py`
- No more cascading failures

### 3. **Incremental Changes**
- Want to improve plan quality? Only modify `planner_agent.py`
- Want to change approval flow? Only modify `approval_handler.py`
- Other modules keep working

### 4. **Easy to Add Features**
- Add web search? Create `search_module.py`, pass to context manager
- Add new agent? Create new file in `agents/`, add to workflow coordinator
- No need to touch existing code

---

## Migration Strategy

### Phase 1: Extract Context Manager (Low Risk)
1. Create `context_manager.py`
2. Move context retrieval methods from orchestrator
3. Update orchestrator to call `context_manager.retrieve_context()`
4. Test: Does planning still work?

### Phase 2: Extract Memory Manager (Low Risk)
1. Create `memory_manager.py`
2. Move all storage/file writing methods
3. Update orchestrator to call `memory_manager.store_results()`
4. Test: Are results still saved correctly?

### Phase 3: Extract Approval Handler (Low Risk)
1. Create `approval_handler.py`
2. Move approval workflow methods
3. Update orchestrator to call `approval_handler.get_approval()`
4. Test: Can user still approve/reject?

### Phase 4: Separate Agents (Medium Risk)
1. Create `agents/` directory
2. Create `base_agent.py` with common functionality
3. Split each agent into its own file
4. Test each agent individually
5. Update workflow coordinator

### Phase 5: Simplify Orchestrator (Low Risk)
1. Orchestrator now just calls modules
2. Remove all business logic from orchestrator
3. Test end-to-end workflow

---

## Key Principles

1. **Single Responsibility**: Each module does ONE thing
2. **No Circular Dependencies**: Modules don't import each other
3. **Clear Interfaces**: Each module has clear input/output
4. **Independent Testing**: Each module can be tested alone
5. **Fail Isolated**: Error in one module doesn't break others

---

## Example: Adding Web Search

With this architecture, adding web search is simple:

```python
# search_module.py
class SearchModule:
    def search(self, query: str) -> List[SearchResult]:
        """Searches web and returns results"""
        pass

# Update context_manager.py
class ContextManager:
    def __init__(self):
        self.search = SearchModule()

    def retrieve_context(self, goal: str) -> Dict:
        analysis = self._analyze_goal(goal)
        entities = self._select_entities(analysis)
        patterns = self._load_patterns()

        # NEW: Add web search results
        search_results = self.search.search(goal)

        return {
            'analysis': analysis,
            'entities': entities,
            'patterns': patterns,
            'search_results': search_results  # NEW
        }
```

Only 2 files changed. No risk to agents, workflow, approval, or memory.

---

## Next Steps

Choose one:
1. **Let Claude do it**: Upload scripts, Claude restructures the code
2. **Give prompts to Cursor**: Use the prompts below to have Cursor do it
3. **Hybrid**: Have Claude create the module structure, then you iterate with Cursor

See `CURSOR_PROMPTS.md` for detailed prompts to give Cursor AI.
