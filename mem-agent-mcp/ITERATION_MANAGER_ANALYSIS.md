# CRITICAL ARCHITECTURAL ANALYSIS: Iteration Manager Session Scoping Bug

**Date:** October 30, 2025
**Status:** BUG CONFIRMED - Critical correctness issue
**Severity:** HIGH - Cross-session contamination possible

---

## EXECUTIVE SUMMARY

The `iteration_manager.py` has a **critical architectural flaw** in how it handles session-scoped entity retrieval. The code attempts to call `search_similar()` and `store_entity()` methods on `llama_planner` that **do not exist**, creating a cascade failure where:

1. **Session ID is created** (line 92) with timestamp: `planning_session_20251030_120000`
2. **Entity prefix is created** (line 93): `memory_entity_prefix = "planning_session_20251030_120000"`
3. **Entities ARE stored** with session prefix (lines 116, 337)
4. **BUT retrieval is broken** - `search_similar()` method doesn't exist on LlamaPlanner
5. **Result:** Falls back to fallback insights (line 235) which may be from ANY session

---

## 1. SESSION SCOPING IN ITERATION_MANAGER.PY

### Session ID Creation (Lines 92-93)

```python
# Memory naming for this planning session
self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
self.memory_entity_prefix = f"planning_session_{self.session_id}"
```

**Status:** ✅ CORRECT
- Session ID is unique per planning session (timestamp-based)
- Prefix is consistently named: `planning_session_20251030_120000`
- Examples:
  - Session A: `planning_session_20251030_120000`
  - Session B: `planning_session_20251030_120100`

**Observation:** This prefix is intended to scope entities to a single session but is **only used in entity naming, not in search filtering**.

---

## 2. ENTITY NAMING CONVENTION

### initialize_from_proposal() - Line 116

```python
self.llama_planner.store_entity(
    entity_name=f"{self.memory_entity_prefix}_proposal",
    content=proposal
)
```

**Entity Name:** `planning_session_20251030_120000_proposal`
**Status:** ✅ CORRECT - Properly prefixed with session ID

### store_iteration_result() - Line 337

```python
entity_name = f"{self.memory_entity_prefix}_iteration_{iteration_result.iteration_num}"
```

**Entity Names:**
- Iteration 1: `planning_session_20251030_120000_iteration_1`
- Iteration 2: `planning_session_20251030_120000_iteration_2`
- Iteration 3: `planning_session_20251030_120000_iteration_3`

**Status:** ✅ CORRECT - Session scoped by design

---

## 3. SEARCH SCOPING IN _retrieve_previous_insights() - CRITICAL BUG

### The Problem: Lines 204-226

```python
def _retrieve_previous_insights(self) -> str:
    """
    Retrieve previous iteration insights using MemAgent semantic search.
    """
    try:
        iteration_num = self.current_iteration
        previous_iteration = self.iteration_history[-1]

        query = f"""Key insights, findings, and learnings from planning iteration {iteration_num}
        for goal: {self.goal}. What did we discover? What changed our understanding?"""

        retrieved_insights = self.llama_planner.search_similar(  # LINE 223 - METHOD DOESN'T EXIST!
            query=query,
            max_results=5
        )

        if retrieved_insights:
            formatted = "**MemAgent-retrieved insights from previous iteration:**\n"
            for i, insight in enumerate(retrieved_insights, 1):
                formatted += f"- {insight}\n"
            return formatted
        else:
            return self._fallback_previous_insights(previous_iteration)

    except Exception as e:
        print(f"Warning: MemAgent semantic search failed: {e}")
        previous_iteration = self.iteration_history[-1]
        return self._fallback_previous_insights(previous_iteration)
```

### The Critical Issue:

1. **`search_similar()` method does not exist** on LlamaPlanner
   - Checked `/llama_planner.py` (1000 lines)
   - Method is called but never defined
   - This will raise `AttributeError`

2. **Session scoping is NOT passed to search_similar()**
   - Method is called with only: `query` and `max_results`
   - No `session_id` parameter
   - No filter to scope results to THIS session

3. **Fallback silently uses local history**
   - When search fails (which it always will), fallback uses:
   - `previous_iteration = self.iteration_history[-1]`
   - This works for now because local history is correct
   - BUT if search is ever fixed, it will search ALL entities globally

### The Bug Scenario:

```
2025-10-30 12:00:00 - Session A starts
  ├─ initialize_from_proposal("Strategy for company X")
  │  └─ Stores: planning_session_20251030_120000_proposal
  └─ Iteration 1 stores: planning_session_20251030_120000_iteration_1
     └─ With insights about "market analysis"

2025-10-30 12:15:00 - Session B starts (different user!)
  ├─ initialize_from_proposal("Strategy for company Y")
  │  └─ Stores: planning_session_20251030_120100_proposal
  └─ Iteration 1 stores: planning_session_20251030_120100_iteration_1
     └─ With insights about "market analysis" (same topic!)

2025-10-30 12:20:00 - Session A continues
  └─ Iteration 2 calls get_iteration_guidance()
     └─ Calls _retrieve_previous_insights()
        └─ Calls search_similar("market analysis")
           └─ CURRENT: Falls back to local history (correct by accident)
           └─ IF FIXED: Would search ALL entities and might find Session B's iteration 1!
```

---

## 4. THE MISSING METHOD: search_similar()

### Verification: Does it exist anywhere?

**Search Result:** NO
- Grep search across entire codebase for `search_similar`
- Only 1 match: Line 223 in `iteration_manager.py` (the call site)
- Zero definitions

### What LlamaPlanner Actually Has:

```python
# Methods that exist in llama_planner.py:
- search_memory(entities, queries)  # Searches specified entities
- research(gaps)                    # Web research
- call_planner()
- call_verifier()
- call_executor()
- call_generator()
- propose_approach()
- get_approval()
- process_user_feedback()
- log_outcome()
- capture_user_rating()
- analyze_learning_patterns()
- save_plan()
```

**Missing Methods:**
- ❌ `search_similar(query, max_results)` - DOESN'T EXIST
- ❌ `store_entity(entity_name, content)` - DOESN'T EXIST
- ❌ `retrieve_entity(entity_name)` - DOESN'T EXIST

### Lines where missing methods are called:

1. **Line 115-118** - `store_entity()` in `initialize_from_proposal()`
2. **Line 223-226** - `search_similar()` in `_retrieve_previous_insights()`
3. **Line 342-345** - `store_entity()` in `store_iteration_result()`

---

## 5. CURRENT IMPLEMENTATION GAP

### memory_entity_prefix Usage

**Where it's USED:**
- Line 116: `f"{self.memory_entity_prefix}_proposal"`
- Line 337: `f"{self.memory_entity_prefix}_iteration_{iteration_result.iteration_num}"`

**Where it's NOT USED (the bug!):**
- Line 223: `search_similar(query, max_results)`  ← Should be `search_similar(query, max_results, session_id=self.session_id)`
- No mechanism to pass session_id to search

### The Fundamental Problem:

The `memory_entity_prefix` is created and used for **naming** but not for **scoping searches**. The search mechanism has no way to filter results by session.

---

## 6. CORRECT BEHAVIOR DESIGN

What SHOULD happen:

```python
# Iteration 1 completes
iteration_result_1 = IterationResult(iteration_num=1, plan="...", ...)
iteration_manager.store_iteration_result(iteration_result_1)
# Creates: planning_session_20251030_120000_iteration_1

# Iteration 2 starts
guidance = iteration_manager.get_iteration_guidance()
  # Calls: _retrieve_previous_insights()
  # Calls: search_similar(
  #   query="Key insights from iteration 1",
  #   max_results=5,
  #   session_id="planning_session_20251030_120000"  # CRITICAL: MISSING!
  # )
  # search_similar() MUST:
  #   - Search ONLY files matching pattern "planning_session_20251030_120000_*"
  #   - NOT search "planning_session_20251030_120100_*" from other sessions
  #   - Return iteration 1 insights from THIS session ONLY
```

**Current:** Falls back to local array (works by accident)
**Should Be:** Session-aware semantic search

---

## 7. IMPLEMENTATION QUESTION: How to pass session_id to search_similar()?

### Option A: Session-Aware (RECOMMENDED)

```python
retrieved_insights = self.llama_planner.search_similar(
    query=query,
    max_results=5,
    session_id=self.session_id  # Filter to this session only
)
```

**Pros:**
- Prevents cross-session contamination
- Explicit scoping
- Safe by design

**Cons:**
- Requires change to llama_planner signature
- Needs implementation of filtering logic

### Option B: Session-Unaware (CURRENT - BROKEN)

```python
retrieved_insights = self.llama_planner.search_similar(
    query=query,
    max_results=5
)
```

**Pros:**
- No changes needed
- Works globally

**Cons:**
- **CRITICAL BUG:** Returns results from ANY session
- Cross-session contamination
- Violates isolation principle

### Option C: Hybrid (NOT RECOMMENDED)

```python
retrieved_insights = self.llama_planner.search_similar(
    query=query,
    max_results=5,
    session_id=self.session_id  # Optional, defaults to None (all sessions)
)
```

**Pros:**
- Backward compatible
- Flexible

**Cons:**
- Dangerous default (searches all sessions)
- Requires discipline to always pass session_id

---

## 8. CROSS-REFERENCE ANALYSIS: Is session_id passed to LlamaPlanner?

### Line 58: __init__ parameters

```python
def __init__(self, max_iterations: int, checkpoint_interval: int,
             llama_planner, goal: str):
```

**Status:** ❌ session_id NOT passed to __init__
- LlamaPlanner is passed by reference
- But session_id remains private in IterationManager
- LlamaPlanner has no way to know which session is calling it

### Line 82: Assignment

```python
self.llama_planner = llama_planner
```

**Status:** ❌ session_id NOT communicated
- LlamaPlanner is just stored
- No session context passed

### Missing: Session awareness in LlamaPlanner

LlamaPlanner would need:

```python
def __init__(self, agent, memory_path, session_id=None):
    self.session_id = session_id  # Store it
    
def search_similar(self, query, max_results=5, session_id=None):
    # Use session_id to scope results
    search_session = session_id or self.session_id
    # Filter entities to only those matching:
    # /entities/planning_session_{search_session}_*
```

---

## 9. ARCHITECTURAL DECISION MATRIX

| Approach | Session-Scoped | Safe | Simple | Recommended |
|----------|---|---|---|---|
| **A: Session-Aware (explicit param)** | ✅ YES | ✅ SAFE | ⚠️ MODERATE | ⭐ YES |
| **B: Session-Unaware (current)** | ❌ NO | ❌ BROKEN | ✅ SIMPLE | ❌ NO |
| **C: Hybrid (optional param)** | ⚠️ DEPENDS | ⚠️ IF PARAM PASSED | ✅ SIMPLE | ❌ NO |

**RECOMMENDATION: Option A (Session-Aware with explicit parameter)**

Reasoning:
1. Prevents cross-session contamination by design
2. Makes session boundaries explicit
3. Easier to test (can verify session scoping)
4. Safer for production use with multiple concurrent users

---

## 10. ERROR SCENARIOS TO PREVENT

### Scenario 1: Session A Iteration 2 gets Session B Iteration 1 insights

```
Session A: session_id = "20251030_120000"
  ├─ Iteration 1: stores planning_session_20251030_120000_iteration_1
  │  └─ Insight: "Market analysis shows 20% CAGR"
  └─ Iteration 2: calls search_similar("market analysis")
     └─ If unscoped, finds: planning_session_20251030_120100_iteration_1 (WRONG SESSION!)

Session B: session_id = "20251030_120100" (started 100 seconds later)
  └─ Iteration 1: stores planning_session_20251030_120100_iteration_1
     └─ Insight: "Market analysis shows 15% CAGR"
```

**Prevention:** Pass `session_id` to `search_similar()`, filter by prefix

### Scenario 2: Session A Iteration 2 uses insights from different goal entirely

```
Session A: goal = "Healthcare market strategy"
  └─ Iteration 1: "Hospital network is main focus"

Session B: goal = "Real estate market strategy"  
  └─ Iteration 1: "Market analysis" ← Same words!

Session A Iteration 2: search_similar("market analysis")
  └─ Could find Session B results if unscoped!
```

**Prevention:** Session scoping prevents cross-goal contamination by default

### Scenario 3: Iteration searching returns 3-session-old results

```
Session A opened: 2025-10-30 12:00:00 - Now at iteration 2
Session B opened: 2025-10-30 12:15:00 - Now at iteration 3
Session C opened: 2025-10-30 12:30:00 - Now at iteration 1

Session A Iteration 2: search_similar("market")
  └─ If unscoped, might find relevant result from Session C iteration 1
  └─ But also might find stale results from Session A iteration 1 (no problem)
  └─ PROBLEM: Could find Session C's iteration 1 which is from different goal!
```

**Prevention:** Only search within session's own entities

### Scenario 4: Cross-contamination of planning contexts

```
Session A: "Create 5-year growth strategy"
  └─ Iteration 1: References "revenue targets", "market size"

Session B: "Analyze competitive landscape"
  └─ Iteration 1: References "competitor pricing", "market share"

Session A Iteration 2: search_similar("market")
  └─ Could find Session B's competitor analysis!
  └─ WRONG CONTEXT: Mixing growth strategy with competitor analysis
```

**Prevention:** Session boundary prevents context mixing

---

## 11. ROOT CAUSE ANALYSIS

Why does this bug exist?

1. **Incomplete Implementation:**
   - `search_similar()` was planned but never implemented
   - `store_entity()` was planned but never implemented
   - Calls were added but methods not defined

2. **Fallback Masks the Bug:**
   - Exception is caught (line 237)
   - Falls back to local history (line 235)
   - System still works, so bug goes unnoticed
   - LOCAL HISTORY IS ALWAYS CORRECT (no cross-session contamination)

3. **Session Scoping Half-Implemented:**
   - Session ID created (line 92) ✅
   - Entity naming includes session (lines 116, 337) ✅
   - Search does NOT filter by session (line 223) ❌
   - Gap between naming and searching

---

## 12. IMPLEMENTATION STATUS

### What Exists:

**In LlamaPlanner:**
- `search_memory(entities, queries)` - Searches specified entity list
- No session awareness
- No semantic search of all entities

**In iteration_manager.py:**
- Session ID creation ✅
- Entity naming with session prefix ✅
- Attempt to call `search_similar()` ❌ (doesn't exist)
- Attempt to call `store_entity()` ❌ (doesn't exist)
- Fallback to local history ✅ (masks bug)

### What's Missing:

**Methods needed:**
1. `LlamaPlanner.search_similar(query, max_results, session_id)`
2. `LlamaPlanner.store_entity(entity_name, content)`
3. `LlamaPlanner.retrieve_entity(entity_name)`

**Filtering logic:**
- Scope entity searches to specific session
- Pattern matching on entity name prefixes

---

## 13. FALLBACK ANALYSIS: Why it works (for now)

Current code uses fallback (line 243-251):

```python
def _fallback_previous_insights(self, previous_iteration: IterationResult) -> str:
    """Fallback formatting if MemAgent search fails."""
    if previous_iteration.key_insights:
        formatted = "**Insights from previous iteration (direct storage):**\n"
        for insight in previous_iteration.key_insights[:5]:  # Top 5 insights
            formatted += f"- {insight}\n"
        return formatted
    else:
        return "**Previous iteration insights:** Insights were stored in MemAgent memory.\n"
```

**Why it's safe:**
- `previous_iteration = self.iteration_history[-1]`
- `self.iteration_history` is **instance-level array**
- Only contains THIS session's iterations
- No cross-session contamination possible at fallback level

**Why it masks the bug:**
- System works despite missing methods
- Bug would only appear if fallback is removed
- Or if MemAgent storage/retrieval is used

---

## 14. RECOMMENDED FIX

### Step 1: Add methods to LlamaPlanner

```python
def store_entity(self, entity_name: str, content: str) -> bool:
    """Store entity to /local-memory/entities/{entity_name}.md"""
    try:
        entity_path = Path(self.memory_path) / "entities" / f"{entity_name}.md"
        entity_path.parent.mkdir(parents=True, exist_ok=True)
        entity_path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"Warning: Failed to store entity: {e}")
        return False

def search_similar(self, query: str, max_results: int = 5, session_id: str = None) -> List[str]:
    """
    Search for similar entities using semantic similarity or keyword matching.
    
    Args:
        query: Search query
        max_results: Maximum results to return
        session_id: If provided, only search entities matching this session
        
    Returns:
        List of relevant entity contents, limited to max_results
    """
    try:
        entities_dir = Path(self.memory_path) / "entities"
        if not entities_dir.exists():
            return []
        
        results = []
        
        # List all entity files
        for entity_file in entities_dir.glob("*.md"):
            # Filter by session_id if provided
            if session_id and not entity_file.stem.startswith(f"planning_session_{session_id}"):
                continue
            
            # Read entity content
            content = entity_file.read_text(encoding='utf-8')
            
            # Simple keyword matching (can be upgraded to semantic search)
            query_terms = set(query.lower().split())
            content_lower = content.lower()
            
            if any(term in content_lower for term in query_terms):
                results.append(content)
                if len(results) >= max_results:
                    break
        
        return results
    except Exception as e:
        print(f"Warning: search_similar failed: {e}")
        return []
```

### Step 2: Update iteration_manager to pass session_id

```python
retrieved_insights = self.llama_planner.search_similar(
    query=query,
    max_results=5,
    session_id=self.session_id  # CRITICAL: Pass session_id
)
```

### Step 3: Document the session scoping

Add to IterationManager class docstring:

```python
"""
Session Scoping Guarantee:
- Each planning session gets unique session_id (timestamp-based)
- All entities are prefixed: planning_session_{session_id}_*
- Searches are scoped to THIS session ONLY
- No cross-session contamination is possible
"""
```

---

## 15. VERIFICATION CHECKLIST

After implementing fixes:

- [ ] `search_similar()` method exists in LlamaPlanner
- [ ] `search_similar()` accepts `session_id` parameter
- [ ] `search_similar()` filters results by session
- [ ] `store_entity()` method exists in LlamaPlanner
- [ ] `store_entity()` writes to /local-memory/entities/
- [ ] `retrieve_entity()` method exists (if needed)
- [ ] Entity names include session prefix
- [ ] Cross-session contamination test passes
- [ ] Session A iteration doesn't get Session B insights
- [ ] Local fallback still works

---

## 16. TEST CASE: Cross-Session Contamination

```python
def test_cross_session_contamination():
    """
    Verify that Iteration 2 in Session A doesn't get insights from Session B
    """
    # Create two separate iteration managers (simulating two sessions)
    session_a = IterationManager(max_iterations=3, checkpoint_interval=3,
                                llama_planner=llama_a, goal="Goal A")
    session_b = IterationManager(max_iterations=3, checkpoint_interval=3,
                                llama_planner=llama_b, goal="Goal B")
    
    # Session A: Iteration 1 stores specific insights
    result_a1 = IterationResult(
        iteration_num=1,
        plan="Plan A1",
        key_insights=["Session A specific insight"]
    )
    session_a.store_iteration_result(result_a1)
    
    # Session B: Iteration 1 stores different insights
    result_b1 = IterationResult(
        iteration_num=1,
        plan="Plan B1",
        key_insights=["Session B specific insight"]
    )
    session_b.store_iteration_result(result_b1)
    
    # Session A: Iteration 2 should NOT get Session B insights
    session_a.current_iteration = 0  # Reset to get guidance
    guidance_a2 = session_a.get_iteration_guidance()
    
    # Assertion: Session A's iteration 2 guidance should not mention Session B
    assert "Session B specific insight" not in guidance_a2
    assert "Session A specific insight" in guidance_a2
```

---

## CONCLUSION

The iteration_manager has a **critical architectural gap** between session ID creation and session-aware search. While the fallback mechanism keeps it working in practice, the underlying bug is:

1. **Methods don't exist:** `search_similar()` is called but not defined
2. **No session filtering:** Even if method existed, it has no way to scope by session
3. **Hidden by fallback:** Local history works, masking the broken search
4. **Could cause contamination:** If fallback is removed or search is used, cross-session contamination is possible

**Recommended Fix:** Implement session-aware `search_similar()` with explicit session_id parameter to prevent cross-session contamination by design.

**Priority:** HIGH - Implement before removing fallback or adding real semantic search

