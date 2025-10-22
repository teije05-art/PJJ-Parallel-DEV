# Cursor AI Prompts for Restructuring

Use these prompts in sequence with Cursor AI to restructure your system into independent modules.

---

## Prompt 1: Create Context Manager Module

```
I need to extract all context retrieval logic from my orchestrator into an independent module.

Create a new file: mem-agent-mcp/orchestrator/context_manager.py

Requirements:
1. Create a ContextManager class with a single public method: retrieve_context(goal: str) -> Dict
2. Move these methods from EnhancedLearningOrchestrator to ContextManager:
   - _retrieve_enhanced_context
   - Any goal analysis logic
   - Any entity selection logic
   - Any pattern loading logic
3. The retrieve_context method should return a dictionary with:
   - 'goal_analysis': analyzed goal information
   - 'entities': relevant entity content
   - 'successful_patterns': successful patterns from memory
   - 'error_patterns': error patterns to avoid
   - 'execution_history': recent execution history
4. This module should NOT depend on:
   - Agent execution
   - Workflow coordination
   - Memory writing
   - Approval workflow
5. Update the imports and make sure it can access the goal_analyzer and domain_templates modules

After creating this, update orchestrator.py to use: self.context_manager.retrieve_context(goal)
instead of self._retrieve_enhanced_context(goal)
```

---

## Prompt 2: Create Memory Manager Module

```
I need to extract all memory storage and file writing logic into an independent module.

Create a new file: mem-agent-mcp/orchestrator/memory_manager.py

Requirements:
1. Create a MemoryManager class with a single public method: store_results(goal, results, success)
2. Move these methods from EnhancedLearningOrchestrator and AgentCoordinator:
   - _write_enhanced_success_to_memory
   - _store_workflow_results
   - _populate_entities_with_content
   - Any file writing logic for plans/ directory
   - Any logic that updates execution_log.md
   - Any logic that updates successful_patterns.md or planning_errors.md
3. The store_results method should handle:
   - Saving plan files to plans/ directory
   - Updating execution log
   - Updating patterns (successful or error based on success parameter)
   - Populating entity files
4. This module should NOT depend on:
   - Context retrieval
   - Agent execution
   - Approval workflow
5. Make sure it has access to the local-memory/ directory path

After creating this, update orchestrator.py and agentflow_agents.py to use:
self.memory_manager.store_results(goal, results, success=True)
```

---

## Prompt 3: Create Approval Handler Module

```
I need to extract the human approval workflow into an independent module.

Create a new file: mem-agent-mcp/orchestrator/approval_handler.py

Requirements:
1. Create an ApprovalHandler class with a single public method: get_approval(results) -> ApprovalDecision
2. Create an ApprovalDecision dataclass with fields:
   - approved: bool
   - feedback: str (optional)
   - action: str ('approve', 'reject', 'edit', 'quit')
3. Move these methods from EnhancedLearningOrchestrator:
   - _get_human_approval
   - Any display/formatting logic for showing results to user
   - Any input handling logic
4. The get_approval method should:
   - Display all agent results clearly
   - Show options: (y)es, (n)o, (e)dit feedback, (q)uit
   - Handle user input
   - Return an ApprovalDecision object
5. This module should NOT depend on:
   - Context retrieval
   - Agent execution
   - Memory storage

After creating this, update orchestrator.py to use:
decision = self.approval_handler.get_approval(results)
```

---

## Prompt 4: Separate Agents into Individual Files

```
I need to split the agentflow_agents.py file into separate files for each agent.

Tasks:
1. Create directory: mem-agent-mcp/agents/
2. Create these files:
   - base_agent.py (common functionality for all agents)
   - planner_agent.py (only PlannerAgent class)
   - verifier_agent.py (only VerifierAgent class)
   - executor_agent.py (only ExecutorAgent class)
   - generator_agent.py (only GeneratorAgent class)
   - agent_interface.py (simple interface for importing all agents)

Requirements for each agent file:
- Import only the base_agent if needed
- The agent class should have a single public method (generate_plan, verify, execute, synthesize)
- Each method should take: goal (str) and context (Dict) as parameters
- Each method should return: str (the agent's output)
- No agent should know about other agents
- No agent should handle memory storage
- No agent should handle approval workflow

Example structure for planner_agent.py:
```python
from agents.base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    def generate_plan(self, goal: str, context: Dict) -> str:
        # Only planning logic here
        pass
```

After creating these files:
1. Delete the old agentflow_agents.py
2. Update all imports to use: from agents.planner_agent import PlannerAgent
```

---

## Prompt 5: Create Workflow Coordinator

```
I need to create a simple workflow coordinator that calls agents in sequence.

Create a new file: mem-agent-mcp/orchestrator/workflow_coordinator.py

Requirements:
1. Create a WorkflowCoordinator class with a single public method: run_workflow(goal, context) -> WorkflowResults
2. Create a WorkflowResults dataclass with fields:
   - plan: str (from PlannerAgent)
   - verification: str (from VerifierAgent)
   - execution: str (from ExecutorAgent)
   - final_output: str (from GeneratorAgent)
3. The run_workflow method should:
   - Initialize all 4 agents
   - Call them in sequence: planner -> verifier -> executor -> generator
   - Each agent gets the goal and context
   - Return a WorkflowResults object with all outputs
4. This module should NOT depend on:
   - Context retrieval
   - Memory storage
   - Approval workflow

Import the agents from the new agents/ directory:
from agents.planner_agent import PlannerAgent
from agents.verifier_agent import VerifierAgent
from agents.executor_agent import ExecutorAgent
from agents.generator_agent import GeneratorAgent

After creating this, update orchestrator.py to use:
results = self.workflow_coordinator.run_workflow(goal, context)
```

---

## Prompt 6: Create Learning Manager Module

```
I need to extract the learning and training logic into an independent module.

Create a new file: mem-agent-mcp/orchestrator/learning_manager.py

Requirements:
1. Create a LearningManager class with a single public method: apply_learning(results, feedback, success)
2. Move these methods from AgentCoordinator:
   - _apply_flow_grpo_training
   - Any logic that updates planner_training_log.md
   - Any logic that updates agent_performance.md
   - Any performance metric calculation
3. The apply_learning method should:
   - Apply Flow-GRPO training signals
   - Update training logs
   - Update performance metrics
   - Learn from feedback (if provided)
4. This module should NOT depend on:
   - Context retrieval
   - Agent execution
   - Approval workflow
   - Memory storage (except for training-specific files)

After creating this, update orchestrator.py to use:
self.learning_manager.apply_learning(results, decision.feedback, success=True)
```

---

## Prompt 7: Simplify the Orchestrator

```
Now that we have independent modules, simplify the orchestrator to just call modules in sequence.

Update mem-agent-mcp/orchestrator/orchestrator.py:

Requirements:
1. Rename EnhancedLearningOrchestrator to SimpleOrchestrator
2. In __init__, initialize these modules:
   - self.context_manager = ContextManager()
   - self.workflow_coordinator = WorkflowCoordinator()
   - self.approval_handler = ApprovalHandler()
   - self.memory_manager = MemoryManager()
   - self.learning_manager = LearningManager()
3. Simplify run_enhanced_learning_loop to just call modules:
   ```python
   def run(self, goal: str):
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
           self.learning_manager.apply_learning(results, decision.feedback, success=True)
       else:
           # Store as failure
           self.memory_manager.store_results(goal, results, success=False)

       return decision.approved
   ```
4. Remove all business logic from the orchestrator - it should only call modules
5. The orchestrator should be less than 100 lines of code

This creates a clean, maintainable orchestrator where each step is independent.
```

---

## Prompt 8: Add Web Search Module (Optional Enhancement)

```
I want to add web search capability to improve plan quality by getting real, current information.

Create a new file: mem-agent-mcp/orchestrator/search_module.py

Requirements:
1. Create a SearchModule class with a method: search(query: str, num_results: int = 5) -> List[SearchResult]
2. Use a web search API (suggestions: SerpAPI, Brave Search API, or DuckDuckGo)
3. Create a SearchResult dataclass with fields:
   - title: str
   - url: str
   - snippet: str
   - source: str
4. The search method should:
   - Take a search query
   - Call the search API
   - Return a list of SearchResult objects
   - Handle errors gracefully (return empty list if search fails)

Then update context_manager.py:
1. Add SearchModule to ContextManager.__init__
2. In retrieve_context, add:
   ```python
   # Generate search query from goal
   search_query = f"{goal} best practices industry analysis"
   search_results = self.search_module.search(search_query)
   ```
3. Add search_results to the returned context dictionary

This gives your planner agent access to real, current web information when planning.
```

---

## Prompt 9: Test the Modular System

```
Now that we have a modular architecture, let's test each module independently.

Create a new file: mem-agent-mcp/tests/test_modules.py

Requirements:
1. Create test functions for each module:
   - test_context_manager(): Test context retrieval with a sample goal
   - test_workflow_coordinator(): Test agent workflow with mock context
   - test_approval_handler(): Test approval workflow with mock results
   - test_memory_manager(): Test storing results with mock data
   - test_learning_manager(): Test learning with mock results
2. Each test should:
   - Initialize only the module being tested
   - Provide mock input
   - Verify output
   - NOT depend on other modules
3. Run each test independently to verify modules work in isolation

This ensures that if one module breaks, you can test and fix it without affecting others.
```

---

## Usage Tips for Cursor AI

1. **Run prompts in sequence** - Each prompt builds on the previous one
2. **Test after each prompt** - Make sure the system still works before moving to the next
3. **Don't skip prompts** - Each step is important for clean architecture
4. **Ask Cursor to explain** - If you don't understand what it did, ask for clarification
5. **Save frequently** - Git commit after each successful prompt

## Expected Results

After running all prompts:
- Orchestrator will be simple (< 100 lines)
- Each module will be independent (can be tested alone)
- Fixing bugs will be easier (only touch one module)
- Adding features will be easier (no cascading changes)
- Error loops will be eliminated (changes don't break unrelated code)
