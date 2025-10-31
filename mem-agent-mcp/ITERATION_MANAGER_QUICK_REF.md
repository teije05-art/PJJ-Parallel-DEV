# ITERATION MANAGER BUG - QUICK REFERENCE

## The Bug in One Sentence
**Iteration manager calls `search_similar()` and `store_entity()` methods on LlamaPlanner that don't exist, and even if they did, they're not session-scoped.**

---

## Critical Files

| File | Location | Issue |
|------|----------|-------|
| **iteration_manager.py** | `/orchestrator/iteration_manager.py` | Calls missing methods; no session scoping in search |
| **llama_planner.py** | `/llama_planner.py` | Missing `search_similar()`, `store_entity()`, `retrieve_entity()` |

---

## Code References

### Lines Calling Missing Methods

| Line | Method | Code | File |
|------|--------|------|------|
| 115-118 | `store_entity()` | `self.llama_planner.store_entity(entity_name=f"{self.memory_entity_prefix}_proposal", content=proposal)` | iteration_manager.py |
| 223-226 | `search_similar()` | `retrieved_insights = self.llama_planner.search_similar(query=query, max_results=5)` | iteration_manager.py |
| 342-345 | `store_entity()` | `self.llama_planner.store_entity(entity_name=entity_name, content=iteration_storage)` | iteration_manager.py |

### What EXISTS vs What's MISSING

**What EXISTS:**
- `self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')` (line 92) ✅
- `self.memory_entity_prefix = f"planning_session_{self.session_id}"` (line 93) ✅
- Entity names with session prefix (lines 116, 337) ✅
- Exception handling with fallback (line 237) ✅
- Fallback to local history (line 235) ✅

**What's MISSING:**
- ❌ `LlamaPlanner.search_similar(query, max_results, session_id)` 
- ❌ `LlamaPlanner.store_entity(entity_name, content)`
- ❌ `LlamaPlanner.retrieve_entity(entity_name)`
- ❌ Session filtering logic in search
- ❌ Session ID passed to search_similar()

---

## Why It's Not Caught

The system **appears to work** because:
1. `search_similar()` call raises `AttributeError`
2. Exception is caught (line 237)
3. Falls back to `self.iteration_history[-1]` (line 235)
4. Local history is correct (no cross-session contamination at this level)
5. Bug is hidden by the fallback

---

## The Cross-Session Contamination Scenario

```
Session A: Planning_session_20251030_120000
├─ Iteration 1: stores planning_session_20251030_120000_iteration_1
│  └─ Insight: "Market shows 20% CAGR for enterprise software"

Session B: Planning_session_20251030_120100  
├─ Iteration 1: stores planning_session_20251030_120100_iteration_1
│  └─ Insight: "Market shows 5% CAGR for consumer software"

Session A Iteration 2: get_iteration_guidance()
├─ Calls: _retrieve_previous_insights()
├─ Calls: search_similar("market analysis")
├─ CURRENTLY: Falls back to local history → Gets Session A iteration 1 ✅
├─ IF FIXED WITHOUT SESSION SCOPING: Could find Session B iteration 1 ❌
└─ IF FIXED WITH SESSION SCOPING: Gets Session A iteration 1 only ✅
```

---

## The Fix (Three Steps)

### Step 1: Add `search_similar()` to LlamaPlanner

```python
def search_similar(self, query: str, max_results: int = 5, session_id: str = None) -> List[str]:
    """Search entities, optionally filtered by session_id."""
    try:
        entities_dir = Path(self.memory_path) / "entities"
        if not entities_dir.exists():
            return []
        
        results = []
        for entity_file in entities_dir.glob("*.md"):
            # CRITICAL: Filter by session if provided
            if session_id and not entity_file.stem.startswith(f"planning_session_{session_id}"):
                continue
            
            content = entity_file.read_text(encoding='utf-8')
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

### Step 2: Add `store_entity()` to LlamaPlanner

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
```

### Step 3: Pass `session_id` in iteration_manager.py line 223

**Before:**
```python
retrieved_insights = self.llama_planner.search_similar(
    query=query,
    max_results=5
)
```

**After:**
```python
retrieved_insights = self.llama_planner.search_similar(
    query=query,
    max_results=5,
    session_id=self.session_id  # CRITICAL: Add this
)
```

---

## Architecture Pattern

### CORRECT (What should happen):
```
Session ID (timestamp) 
    ↓
Entity prefix (session_id_*)
    ↓
Entity naming (planning_session_20251030_120000_iteration_1)
    ↓
Entity storage (writes to /entities/)
    ↓
Entity search WITH SESSION FILTER (only search planning_session_20251030_120000_*)
    ↓
Result: Only gets THIS session's entities
```

### BROKEN (What's happening):
```
Session ID (timestamp) ✅
    ↓
Entity prefix (session_id_*) ✅
    ↓
Entity naming (planning_session_20251030_120000_iteration_1) ✅
    ↓
Entity storage (writes to /entities/) ❌ Method doesn't exist
    ↓
Entity search WITH NO SESSION FILTER ❌ Method doesn't exist, no parameter
    ↓
Result: Would search ALL entities if method existed
```

---

## Test to Verify Fix

```python
def test_session_isolation():
    """Ensure Session A iteration 2 doesn't get Session B iteration 1"""
    
    # Session A and B have different session_ids
    assert session_a.session_id != session_b.session_id
    assert "planning_session_" in session_a.memory_entity_prefix
    
    # Both store iteration 1
    session_a.store_iteration_result(result_a1)
    session_b.store_iteration_result(result_b1)
    
    # Session A iteration 2 search should only find session_a entities
    retrieved = session_a.llama_planner.search_similar(
        query="market",
        session_id=session_a.session_id
    )
    
    # Should contain Session A's content
    assert any("Session A" in r for r in retrieved)
    # Should NOT contain Session B's content
    assert not any("Session B" in r for r in retrieved)
```

---

## Impact Assessment

| Scenario | Current | With Fix |
|----------|---------|----------|
| Session A Iteration 2 retrieves Session A Iteration 1 insights | ✅ Works (via fallback) | ✅ Works (via search) |
| Session A Iteration 2 accidentally gets Session B insights | ✅ Prevented (fallback local) | ✅ Prevented (session filter) |
| Adding real semantic search without session filter | ❌ Cross-contamination | ✅ Safe |
| Removing fallback mechanism | ❌ Complete failure | ✅ Works |
| Multiple concurrent planning sessions | ⚠️ At risk | ✅ Safe |

---

## Priority

**SEVERITY:** HIGH - Critical correctness issue
**TIMELINE:** Fix before:
1. Removing fallback mechanism
2. Adding semantic search capabilities
3. Production deployment with concurrent users

---

## References

- **Analysis Document:** `/tmp/iteration_manager_analysis.md` (16 sections, comprehensive)
- **Files Affected:**
  - `/orchestrator/iteration_manager.py` (main issue)
  - `/llama_planner.py` (missing implementations)
- **Test File:** `/tests/test_multi_iteration_integration.py`

