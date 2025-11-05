# Technical Deep Dive: Executor/Generator Architecture Failure

## Executive Summary

The multi-iteration planning system fails to produce varying plans because of a fundamental architectural mismatch:

- **Planner Agent**: Generates TEXT plans only
- **Executor Agent**: Expects to READ FILES and create structured deliverables
- **Generator Agent**: Expects executor's FILE outputs for synthesis
- **Result**: Both executor and generator fail silently, producing 0 deliverables, falling back to repeating planner text

This document details the exact code locations, the failure mechanism, and what needs to change.

---

## Current Workflow Flow

### What SHOULD Happen (Intended Design)

```
User provides goal
  ↓
Context Manager retrieves web search + memory + goal analysis
  ↓
Planner Agent: Generates strategic plan with frameworks
  ↓
Verifier Agent: Validates plan logic
  ↓
Executor Agent:
  - Reads planner text
  - Extracts into structured deliverables (feasibility study, implementation plan, etc.)
  - Creates files on disk for each deliverable
  ✅ Returns list of created files
  ↓
Generator Agent:
  - Reads executor's files
  - Synthesizes comprehensive 3000+ word final plan
  ✅ Returns synthesized plan with citations
```

### What ACTUALLY Happens (Current Broken State)

```
User provides goal
  ↓
Context Manager retrieves web search + memory + goal analysis
  ↓
Planner Agent: Generates strategic plan with frameworks ✅
  ↓
Verifier Agent: Validates plan logic (marks invalid but continues) ⚠️
  ↓
Executor Agent:
  - Looks for files: manufacturing_feasibility_study.md, etc.
  - Files don't exist (planner created none)
  - Checks 13+ different file names in loop
  - Returns: 0 deliverables, produces nothing
  ❌ FAILS SILENTLY
  ↓
Generator Agent:
  - Expects to read executor's files
  - Files don't exist
  - Checks for Executive Summary Report.md, Implementation Plan.md, etc.
  - Returns: 0 deliverables
  ❌ FAILS SILENTLY
  ↓
Falls back to repeating planner text
```

---

## Code Evidence of the Failure

### Evidence #1: Executor Looking for Files That Don't Exist

**File**: `orchestrator/agents/executor_agent.py`

The executor contains logic like this (pattern repeats):

```python
# Looking for file that should have been created by planner
if os.path.exists("manufacturing_feasibility_study.md"):
    # Process it
else:
    # File doesn't exist - silently continue
```

**Log Output Evidence**:
```
File manufacturing_feasibility_study.md exists: False
File lean_manufacturing_principles_implementation_plan.md exists: False
File supply_chain_network_establishment_plan.md exists: False
File manufacturing_capacity_planning_and_resource_allocation_plan.md exists: False
... [13 more file checks]
... [entire pattern repeats]
```

Each file check is independent - NO feedback when files missing. Just returns:
```
✅ Plan executed (0 deliverables)
✅ 3 phases completed
```

### Evidence #2: Generator Also Looking for Files

**File**: `orchestrator/agents/generator_agent.py`

Same pattern - expects files:

```python
if os.path.exists("Executive Summary Report.md"):
    # Use it
else:
    # File doesn't exist - silently continue
```

**Log Output Evidence**:
```
File Executive Summary Report.md exists: False
File Detailed Implementation Plan.md exists: False
File Risk Assessment and Mitigation Strategy.md exists: False
File Quality Assurance Framework.md exists: False
File Timeline and Resource Allocation.md exists: False
File Success Metrics and KPIs.md exists: False
File Recommendations and Next Steps.md exists: False
... [repeats multiple times]
```

### Evidence #3: Why Iterations Are Identical

**File**: `orchestrator/simple_orchestrator.py`, lines ~480-500 (fallback synthesis)

When executor/generator fail:
```python
def _create_fallback_synthesis(self, all_results: list, goal: str) -> str:
    """Create basic synthesis if GeneratorAgent fails."""
    synthesis = f"""# Comprehensive Final Plan: {goal}
    ...
    for i, result in enumerate(all_results, 1):
        synthesis += f"\n### Iteration {i}\n{result.plan}\n"
    return synthesis
```

Since executor/generator return nothing meaningful:
- Iteration 1: Falls back to planner text
- Iteration 2: Falls back to planner text (same planner was used)
- Iteration 3: Falls back to planner text (same planner was used)

**Result**: Identical output all 3 iterations because planner produces similar text each iteration

---

## Why This Architectural Mismatch Exists

### Historical Context

The system appears to have been designed with a FILE-BASED workflow:

1. **Planner** → Creates plan files
2. **Executor** → Reads plan files, creates deliverable files
3. **Generator** → Reads deliverable files, synthesizes

But somewhere the implementation diverged:
- Planner was changed to generate text only (not create files)
- Executor/Generator were never updated to match
- Result: They still look for files that are never created

### Why It "Worked" Before

The system may have:
- Previously had planner creating files
- Or had a direct planner→generator path that bypassed executor
- Or had fallback synthesis that worked better

Current state shows the fallback mechanism is:
```
If executor/generator find 0 deliverables:
  → Fall back to just concatenating planner outputs
```

This works (no crashes) but produces bad results (no variation, no data integration).

---

## Secondary Failure: SegmentedMemory Not Used

### What SHOULD Happen

Memory data IS retrieved (from log):
```
✓ Successful patterns: 208 chars
✓ Errors to avoid: 207 chars
✓ Execution history: 186 chars
✓ Agent performance: 166 chars
```

This should be passed to agents in context. Log shows:
```
ℹ️ No segmented memory available (use approval_gates.py to enable)
```

**File**: `approval_gates.py`, lines 38-43

```python
self.memory_manager = SegmentedMemory(
    max_segments=12,
    max_tokens_per_segment=2000,
    memagent_client=self.agent
)
```

Memory IS initialized but marked as "not available". This suggests:
- SegmentedMemory.get_relevant_segments() might be returning empty
- OR context builder is not passing memory segments to agent prompts
- OR agents aren't checking for memory data in context

### Impact on Iterations

Without memory context, agents:
- Don't know what worked in iteration 1
- Don't know what to avoid from iteration 1
- Have no guidance to go deeper in iteration 2
- Produce similar output by default

---

## Tertiary Failure: PDDL-INSTRUCT Reasoning Not Extracted

### What Happens

From log:
```
→ Enhanced with PDDL-INSTRUCT reasoning chain request (16304 chars)...
→ Extracted 0 reasoning steps (quality: 0.00)
```

Reasoning extraction:
- Requests reasoning chains from model ✅
- Gets response with 16304 chars ✅
- Extracts: 0 steps ❌

### Why This Matters

PDDL-INSTRUCT is supposed to:
- Add structured reasoning to plans
- Track preconditions and effects
- Enable verification feedback
- Allow learning from what worked

With 0 reasoning steps extracted:
- Verification is ineffective
- Learning can't track why things worked
- Agents get no guidance on reasoning quality

---

## The Web Search Integration Gap

### What WORKS

```
✓ Web search complete: 25 results from 10 queries
✓ Web search results: 6929 chars
```

Web search IS running and retrieving real data.

### What DOESN'T WORK

From log analysis:
- Planner gets web search data in context ✅
- But doesn't explicitly cite sources ❌
- Just incorporates generically ❌
- No data extraction or structured use ❌

Example from planner output:
```
→ Web search data: 6929 chars
→ Building planning prompt from manufacturing template...
→ Planning prompt built: 15248 chars
```

The planner prompt includes search results (built into 15248 char prompt), but:
- Doesn't explicitly reference which articles
- Doesn't extract specific metrics
- Doesn't use search data as driving decisions
- Doesn't highlight "here's 5 key metrics you should focus on"

---

## What Needs to Be Fixed

### Priority 1: Executor/Generator Architecture (Blocking)

**Current Problem**: Both agents look for files that don't exist

**Fix Strategy**:
1. Executor should parse planner text (not look for files)
2. Executor should create in-memory Deliverable objects
3. Generator should synthesize from these objects
4. Both should return structured data, not rely on files

**Scope**: Moderate - affects 2 agents, ~200-300 lines

**Risk**: HIGH - if done wrong, no synthesis at all (broken system)

### Priority 2: SegmentedMemory Integration

**Current Problem**: Memory data retrieved but not used in prompts

**Fix Strategy**:
1. Ensure SegmentedMemory.get_relevant_segments() returns data
2. Pass memory segments explicitly in context to each agent
3. Agents reference memory in prompts

**Scope**: Small - mainly context passing, ~50 lines

**Risk**: LOW - adds context, doesn't break existing flow

### Priority 3: PDDL-INSTRUCT Extraction

**Current Problem**: Reasoning extraction returns 0 steps

**Fix Strategy**:
1. Debug why extraction fails (likely regex/parsing issue)
2. Implement proper reasoning chain parsing
3. Store chains in iteration metadata

**Scope**: Small to moderate, ~100 lines

**Risk**: LOW - affects verification, not core execution

### Priority 4: Data-Driven Planner Prompts

**Current Problem**: Planner incorporates data generically, no citations

**Fix Strategy**:
1. Modify planner prompt template to say "CITE web search sources"
2. Add domain-specific data requirements
3. Make planner extract key metrics from web search
4. Pass those to executor for deliverable structure

**Scope**: Moderate - affects prompts, extraction, ~150 lines

**Risk**: MEDIUM - changes agent behavior, needs careful testing

### Priority 5: Iteration Progression (Deepening)

**Current Problem**: Iterations 1-3 produce same content

**Fix Strategy**:
1. Pass iteration context explicitly to agents
2. Generator should vary synthesis per iteration
3. Add constraints like "iteration 2 must cover 2 new frameworks"
4. Use checkpoint summaries to inform next iteration

**Scope**: Large - affects multiple agents, ~200 lines

**Risk**: MEDIUM-HIGH - touches core iteration logic

---

## Data Flow Changes Needed

### Current Data Flow

```
Goal
  ↓
SearchContextProvider → web_search_results (6929 chars)
  ↓
MemoryManager → memory_segments (if enabled)
  ↓
PlannerPrompt ← includes both ✅
  ↓
Planner → outputs text
  ↓
Executor ← looks for files ❌
```

### Proposed Data Flow (Fix #1)

```
Goal
  ↓
SearchContextProvider → web_search_results (6929 chars) + citations
  ↓
MemoryManager → memory_segments + importance scores
  ↓
PlannerPrompt ← includes both with explicit citations
  ↓
Planner → outputs text + embedded citations
  ↓
Executor ← PARSES text (not files) ✅
  ↓
Extracts to Deliverable objects (in memory)
  ↓
Generator ← reads Deliverable objects ✅
  ↓
Synthesizes with variation per iteration
```

---

## Code Sections to Investigate Tomorrow

### 1. Executor Agent File Checking (The Problem)

**File**: `orchestrator/agents/executor_agent.py`
**Look for**: File existence checks, path construction
**Question**: Why does it expect files? When were they supposed to be created?
**Action needed**: Redesign to parse text instead

### 2. Generator Agent Synthesis (The Problem)

**File**: `orchestrator/agents/generator_agent.py`
**Look for**: File reading, synthesis from files
**Question**: How does it currently work if executor creates 0 files?
**Action needed**: Design to work with in-memory objects

### 3. Planner Agent Output (The Source)

**File**: `orchestrator/agents/planner_agent.py`
**Look for**: What gets returned? Does it create files?
**Question**: Is planner SUPPOSED to create files, or just output text?
**Action needed**: Confirm current design intent

### 4. Context Builder (The Medium)

**File**: `orchestrator/context/context_builder.py`
**Look for**: How is web_search_results passed? How is memory included?
**Question**: Are memory segments actually being retrieved?
**Action needed**: Verify data flow from retrieval to agents

### 5. Fallback Synthesis (The Temporary Solution)

**File**: `orchestrator/simple_orchestrator.py`, lines 874-895
**Look for**: _create_fallback_synthesis() function
**Question**: When is this called? What does it do with executor/generator results?
**Action needed**: Understand current fallback, plan upgrade path

### 6. SegmentedMemory Initialization (The Disabled Feature)

**File**: `approval_gates.py`, lines 38-43
**Look for**: SegmentedMemory setup, what "not available" means
**Question**: Why does log say "not available"?
**Action needed**: Enable and pass to agents

---

## Testing Strategy for Fixes

### Phase 1 Testing (After fixing executor/generator)

```
Run: Single iteration test
Expected:
  - Planner generates plan ✅
  - Executor extracts to objects ✅ (NEW)
  - Generator synthesizes (NEW)
  - Browser shows plan ✅

Check for regressions:
  - Manual planning iterations still work
  - Single iteration test unchanged
```

### Phase 2 Testing (After enabling memory)

```
Run: Two-iteration test
Expected:
  - Iteration 1 completes ✅
  - Memory context available ✅ (NEW)
  - Iteration 2 gets memory guidance ✅ (NEW)

Check:
  - Still produces different content?
  - Plans better quality?
```

### Phase 3 Testing (After data-driven prompts)

```
Run: Three-iteration test
Expected:
  - Each iteration has different metrics ✅
  - Web sources cited ✅
  - Iteration depth increases ✅

Check:
  - Plans substantively different?
  - Data quality good?
  - No API errors?
```

---

## Risk Assessment

| Change | Risk Level | Mitigation |
|--------|-----------|-----------|
| Executor redesign | HIGH | Test after each small change, have fallback ready |
| Generator redesign | HIGH | Keep current fallback working during transition |
| Memory integration | LOW | Additive change, test in isolation first |
| Planner prompt modification | MEDIUM | Test with various domains, check for failures |
| Iteration progression logic | MEDIUM-HIGH | Careful testing, incremental rollout |

**Overall Risk**: HIGH - This touches core planning pipeline

**Mitigation Strategy**:
1. Fix executor/generator first (highest priority blocker)
2. Test each change immediately
3. Keep git commits small and reversible
4. Have clear rollback plan if something breaks
5. Run full test suite after each phase

---

## Questions for Tomorrow

1. **Architecture Intent**: Were files supposed to be created by planner? Or is text-only correct?

2. **Executor Design**: Should executor:
   - Parse planner text and extract sections?
   - Call agents to extract from planner output?
   - Use regex/NLP to identify metrics?
   - Something else?

3. **Deliverable Structure**: What should in-memory Deliverable objects contain?
   - title, domain, metrics, citations, iteration_number?
   - Something more structured?
   - Raw text or parsed sections?

4. **Generator Variation**: How should generator vary synthesis per iteration?
   - Different order of sections?
   - Different emphasis on metrics?
   - Different formatting?
   - Literal deepening of same topics?

5. **Memory Enabling**: What's preventing SegmentedMemory from being "available"?
   - Uninitialized?
   - Returns empty?
   - Not passed to agents?

6. **PDDL Extraction**: Why does reasoning extraction return 0 steps?
   - Regex pattern not matching?
   - Model not returning formatted chains?
   - Extraction code broken?

7. **User Metrics Flow**: How should user-requested metrics be tracked through system?
   - Store in session/proposal?
   - Pass through context?
   - Mark as priority in domain guidance?

---

# Summary

The executor/generator failure is the ROOT CAUSE of identical iterations. Both agents fail silently due to architectural mismatch (looking for files that don't exist). The system falls back to repeating planner text.

Fixing this requires carefully redesigning the executor and generator to work with in-memory objects while maintaining the stable structure that keeps the system working.

This is a significant architectural change that must be done incrementally with careful testing after each phase.
