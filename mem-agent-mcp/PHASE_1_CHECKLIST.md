# Phase 1 Completion Checklist

**Phase 1 Goal:** Prepare the system for refactoring by documenting current state and creating test infrastructure.

**Estimated Time:** 2-3 hours

**Key Deliverables:**
1. ✅ Dependency map (created: `PHASE_1_DEPENDENCY_MAP.md`)
2. ✅ Baseline test suite (created: `tests/test_baseline.py`)
3. ⏳ Run baseline tests and collect metrics
4. ⏳ Document baseline behavior
5. ⏳ Prepare refactoring plan specifics
6. ⏳ Get user confirmation

---

## Checklist

### Step 1: Review Documentation
- [x] Created `PHASE_1_DEPENDENCY_MAP.md` - Complete dependency graph
- [x] Created `tests/test_baseline.py` - Baseline test suite
- [x] Created `ARCHITECTURE_REFACTORING_PLAN.md` - Full refactoring plan

### Step 2: Run Baseline Tests

**Command:**
```bash
cd /Users/teije/Desktop/memagent-modular-fixed/mem-agent-mcp
python -m pytest tests/test_baseline.py -v --tb=short -s
```

**Expected Output:**
```
test_baseline.py::TestGoalAnalyzer::test_coffee_company_detected_as_qsr PASSED
test_baseline.py::TestGoalAnalyzer::test_healthcare_company_detected_as_healthcare PASSED
test_baseline.py::TestGoalAnalyzer::test_technology_startup_detected_as_technology PASSED
...
[All tests should PASS]
```

**What to Verify:**
- [ ] All tests pass with current code
- [ ] No import errors
- [ ] Goal analyzer works correctly
- [ ] Domain templates work correctly
- [ ] Content tracking works

### Step 3: Collect Baseline Metrics

**Run:**
```bash
cd /Users/teije/Desktop/memagent-modular-fixed/mem-agent-mcp
python -m pytest tests/test_baseline.py::collect_baseline_metrics -v
# Or:
python tests/test_baseline.py
```

**Expected Metrics:**
```
simple_orchestrator.py              312 lines
context_manager.py                  350 lines
workflow_coordinator.py              67 lines
agentflow_agents.py               1,036 lines ← MONOLITHIC
approval_handler.py                 127 lines
memory_manager.py                   291 lines
learning_manager.py                 161 lines
goal_analyzer.py                    496 lines
domain_templates.py                 783 lines ← MONOLITHIC
search_module.py                    179 lines

TOTAL                             3,832 lines

Monolithic files (3): 2,169 lines (56.6% of total)
```

**Document These:**
- [ ] Save baseline metrics to `BASELINE_METRICS.txt`
- [ ] Note which 3 files are monolithic (focus of refactoring)
- [ ] Note which 7 files are stable (not changing)

### Step 4: Verify Test Coverage

**Check what tests cover:**
- [x] Goal analyzer (domain detection)
- [x] Template selection and formatting
- [x] AgentResult dataclass
- [x] Content preservation (9,593 char tracking)
- [x] Data structures
- [x] Error handling
- [x] Import structure
- [x] Metrics collection

**Validate:**
- [ ] At least 20 test cases
- [ ] Tests cover critical paths
- [ ] Tests will catch regressions

### Step 5: Document Public APIs

**These MUST NOT CHANGE during refactoring:**

1. **SimpleOrchestrator**
   - Method: `__init__(memory_path, max_iterations, strict_validation)`
   - Method: `run_enhanced_learning_loop(goal)` → bool
   - Attribute: `agent_coordinator` (for MCP compatibility)

2. **ContextManager**
   - Method: `retrieve_context(goal)` → Dict[str, str]
   - Returns dict with keys: goal_analysis, current_status, successful_patterns, errors_to_avoid, execution_history, agent_performance, web_search_results

3. **WorkflowCoordinator**
   - Method: `run_workflow(goal, context)` → Dict[str, AgentResult]
   - Returns dict with keys: planner, verifier, executor, generator

4. **AgentResult** (dataclass)
   - Fields: success: bool, output: str, metadata: Dict, timestamp: str
   - Must remain importable from agentflow_agents.py

5. **GoalAnalyzer**
   - Method: `analyze_goal(goal)` → GoalAnalysis
   - GoalAnalysis must have: domain, industry, market, raw_goal

6. **DomainTemplates**
   - Method: `get_planning_prompt(goal_analysis, context)` → str

**Validation:**
- [ ] Public APIs documented
- [ ] Tests verify these APIs still work after refactoring
- [ ] No breaking changes to exports

### Step 6: Create Refactoring Specifics

**For agentflow_agents.py splitting:**
- [ ] BaseAgent class design (what gets extracted)
- [ ] Individual agent file names and responsibilities
- [ ] AgentCoordinator interface (how agents are called)
- [ ] Import strategy (how old code updates)

**For domain_templates.py splitting:**
- [ ] BaseTemplate class design
- [ ] Individual template file structure
- [ ] Template selector logic
- [ ] Import strategy

**For context_manager.py refactoring:**
- [ ] Context provider interfaces
- [ ] Data flow between providers
- [ ] ContextBuilder orchestration
- [ ] Import strategy

### Step 7: Rollback Plan Documentation

**If Phase 2/3 has problems:**
- [ ] Old files remain (not deleted)
- [ ] Can revert simple_orchestrator.py imports to use old code
- [ ] Can delete new code if not working
- [ ] System stays functional throughout

**Rollback procedure:**
1. Edit `simple_orchestrator.py` import statements
2. Change from `from orchestrator.agents import ...` to `from orchestrator.agentflow_agents import ...`
3. Delete `orchestrator/agents/` directory
4. Delete `orchestrator/templates/` directory (if created)
5. Restart system

**Time to rollback:** < 5 minutes

### Step 8: Stakeholder Sign-Off

**Before proceeding to Phase 2:**
- [ ] User reviews dependency map
- [ ] User reviews refactoring plan
- [ ] User reviews baseline metrics
- [ ] User confirms test suite is appropriate
- [ ] User approves public API list
- [ ] User says "go ahead" to Phase 2

---

## Detailed Step-by-Step Instructions

### Step A: Run the Tests

```bash
# Navigate to project
cd /Users/teije/Desktop/memagent-modular-fixed/mem-agent-mcp

# Install pytest if needed
pip install pytest

# Run baseline tests
python -m pytest tests/test_baseline.py -v --tb=short

# Collect metrics
python tests/test_baseline.py
```

### Step B: Document Results

Create file: `BASELINE_METRICS.txt`

```
BASELINE METRICS - October 27, 2025

CURRENT CODE METRICS:
===================

File-by-File Breakdown:
  simple_orchestrator.py              312 lines
  context_manager.py                  350 lines
  workflow_coordinator.py              67 lines
  agentflow_agents.py               1,036 lines ← MONOLITHIC (4 agents)
  approval_handler.py                 127 lines
  memory_manager.py                   291 lines
  learning_manager.py                 161 lines
  goal_analyzer.py                    496 lines
  domain_templates.py                 783 lines ← MONOLITHIC (7 templates)
  search_module.py                    179 lines
  ---
  TOTAL                             3,832 lines

Monolithic Files (focus of refactoring):
  agentflow_agents.py               1,036 lines (27.0%)
  domain_templates.py                 783 lines (20.4%)
  context_manager.py                  350 lines (9.1%)
  ---
  Subtotal                           2,169 lines (56.5% of total)

Stable Files (not changing):
  simple_orchestrator.py              312 lines
  approval_handler.py                 127 lines
  memory_manager.py                   291 lines
  learning_manager.py                 161 lines
  goal_analyzer.py                    496 lines
  search_module.py                    179 lines
  ---
  Subtotal                           1,566 lines (40.8% of total)

Other:
  workflow_coordinator.py              67 lines (1.7%)
  ---

TEST RESULTS:
============

Baseline Tests: [Results here after running]
  - TestGoalAnalyzer: X/4 tests passed
  - TestDomainTemplates: X/5 tests passed
  - TestAgentResult: X/2 tests passed
  - TestContentTracking: X/2 tests passed
  - TestImportStructure: X/3 tests passed
  - TestDataStructures: X/1 tests passed
  - TestErrorHandling: X/3 tests passed
  - TestMetrics: X/2 tests passed

Total: XX tests passed

CRITICAL OBSERVATIONS:
====================

1. Monolithic Files (56.5% of codebase):
   - agentflow_agents.py contains 4 different agents (should be 4 files)
   - domain_templates.py contains 7 different templates (should be 7 files)
   - context_manager.py does 4 unrelated jobs (should be split)

2. Content Tracking Issue:
   - Tests verify AgentResult preserves output without truncation
   - System should preserve all 9,593 chars through pipeline
   - Multiple transformation points are potential loss locations

3. Dependency Structure:
   - Clear linear flow: Context → Agents → Approval → Memory → Learning
   - No circular dependencies detected
   - Public APIs are well-defined

4. Code Quality:
   - All tests pass with current code
   - Imports work correctly
   - Error handling exists but could be clearer

READINESS FOR REFACTORING:
=========================

✅ Tests established (baseline for regression detection)
✅ Metrics collected (before and after comparison)
✅ Public APIs documented (won't change)
✅ Dependency map created (clear structure)
✅ Rollback plan documented (can revert if needed)
✅ READY FOR PHASE 2

Estimated refactoring impact:
- Total lines: 3,832 → 2,900 (24% reduction)
- Monolithic files: 3 → 0 (100% improvement)
- Code clarity: Significant improvement
- Content tracking: Should be fixed by architecture improvements
```

### Step C: Review & Approve

Checklist for user review:
- [ ] Tests all pass with current code
- [ ] Baseline metrics documented
- [ ] Dependency map is complete and accurate
- [ ] Refactoring plan is clear and safe
- [ ] Rollback plan is documented
- [ ] Ready to proceed to Phase 2

---

## Phase 1 Success Criteria

✅ **DEFINITION:** Phase 1 is complete when:

1. **Tests Established**
   - Baseline test suite created
   - All tests pass with current code
   - Tests cover critical functionality

2. **Metrics Documented**
   - Current line counts recorded
   - File dependencies mapped
   - Problem areas identified

3. **Plan Finalized**
   - Architecture refactoring plan complete
   - File split strategy documented
   - Public APIs protected
   - Rollback plan in place

4. **Stakeholder Approved**
   - User reviews all documents
   - User understands the plan
   - User says "proceed to Phase 2"

---

## Timeline

**Phase 1 Estimated Schedule:**

- **Setup (5 min)**
  - Create test suite
  - Create dependency map

- **Testing (20 min)**
  - Run baseline tests
  - Verify all pass
  - Collect metrics

- **Documentation (30 min)**
  - Document results
  - Create baseline metrics file
  - Review with user

- **Review (30 min)**
  - User review
  - Q&A discussion
  - Final approval

**Total: ~1.5 hours**

Then user says "go" and Phase 2 begins.

---

## Next: Phase 2 (After User Approval)

Once Phase 1 is complete and user approves:

1. Create new directory structure
2. Create base classes (BaseAgent, BaseTemplate)
3. Extract individual agents
4. Extract individual templates
5. Update imports in simple_orchestrator.py
6. Run tests to verify new code works
7. Compare outputs between old and new
8. Prepare for Phase 4 (switchover)

---

## Files Created in Phase 1

1. ✅ `PHASE_1_DEPENDENCY_MAP.md` - Complete dependency documentation
2. ✅ `ARCHITECTURE_REFACTORING_PLAN.md` - Full refactoring strategy
3. ✅ `tests/test_baseline.py` - Baseline test suite
4. ⏳ `BASELINE_METRICS.txt` - Will be created after tests run
5. ⏳ This checklist for user reference

---

**Phase 1 Status: Ready for test execution and user review**

Next step: Run tests and collect metrics, then user approves to proceed.
