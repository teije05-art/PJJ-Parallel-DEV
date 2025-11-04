# MemAgent-MCP: Fix Recommendations

## Quick Summary
The system has **7 interconnected issues** preventing it from working correctly. All stem from:
1. **Hardcoded values** instead of using user selections
2. **Silent error handling** - errors are printed but not propagated
3. **Missing validation** - no checks that things actually exist before use
4. **Broken context flow** - data isn't passed through system correctly

---

## Fix Priority Matrix

### MUST FIX FIRST (Blocking all features)

#### 1. Remove Hardcoded Entity Names [HIGH - 1-2 hours]
**Status:** Entity names hardcoded in `goal_analyzer.py` override user selections

**Files to change:**
- `/orchestrator/goal_analyzer.py:531-554` - Remove hardcoded entity lists

**Current code:**
```python
if domain == 'technology':
    entities.extend(['tech_market_analysis', 'startup_ecosystem', 'digital_transformation'])
```

**Fix:**
```python
# REMOVE hardcoded entities - only use dynamic selections
# The goal_analyzer should ONLY determine domain/market/company_type
# It should NOT suggest entity names - those come from user or memory
# If domain needs specific context, use retrieval methods instead

def _determine_context_entities(self, domain: str, industry: str, market: str) -> List[str]:
    # Return EMPTY list - let frontend/context_manager handle entity selection
    return ['successful_patterns', 'planning_errors', 'execution_log']  # Only learning entities
```

**Why:** This is the root cause of Issue #1, #5, and #7. User selections are ignored.

---

#### 2. Add Entity Validation with Error Reporting [HIGH - 1 hour]
**Status:** Missing entities silently skipped, no feedback to user

**File:** `/llama_planner.py:202-233`

**Current code:**
```python
for entity in entities:
    try:
        entity_path = Path(self.memory_path) / "entities" / f"{entity}.md"
        if not entity_path.exists():
            continue  # SILENT SKIP
        # ...
    except Exception as e:
        pass  # SILENT SKIP
```

**Fix:**
```python
def search_memory(self, entities: List[str], queries: List[str]) -> Dict[str, Any]:
    results = {
        "results": "",
        "coverage": 0.0,
        "entities_searched": 0,
        "entities_found": [],  # NEW: Track what was found
        "entities_missing": [],  # NEW: Track what was missing
        "gaps": queries.copy(),
        "sources": []
    }
    
    found_content = []
    entities_searched = 0
    missing_entities = []  # NEW: Track missing
    
    for entity in entities:
        try:
            entity_path = Path(self.memory_path) / "entities" / f"{entity}.md"
            if not entity_path.exists():
                entity_path = Path(self.memory_path) / "entities" / entity
                if not entity_path.exists():
                    missing_entities.append(entity)  # NEW: Log missing
                    continue
            
            # ... rest of code ...
        except Exception as e:
            print(f"⚠️ Error reading entity {entity}: {e}")  # NEW: Log errors
            missing_entities.append(entity)
    
    results["entities_found"] = results["sources"]
    results["entities_missing"] = missing_entities  # NEW: Return missing list
    # ... rest ...
```

**Why:** User will know which entities exist and which don't. Enables proper error handling upstream.

---

#### 3. Fix Input Field ID Collision [HIGH - 30 minutes]
**Status:** Same HTML ID used for two different form inputs causing control mismatch

**File:** `/static/index.html`

**Current code:**
```html
<!-- Line 633 - SIDEBAR -->
<input type="number" id="max-iterations" value="9" ...>

<!-- Line 706 - MODAL -->
<input type="number" id="max-iterations" value="6" ...>
```

**Fix - Use unique IDs:**
```html
<!-- Line 633 - SIDEBAR -->
<input type="number" id="sidebar-max-iterations" value="9" ...>
<input type="number" id="sidebar-checkpoint-interval" value="3" ...>

<!-- Line 706 - MODAL (in approval gate) -->
<input type="number" id="modal-max-iterations" min="1" max="20" value="6" ...>
<input type="number" id="modal-checkpoint-interval" min="1" max="10" value="3" ...>
```

**Also update JavaScript:**
```javascript
// In approveApproach() function
const maxIterations = parseInt(document.getElementById('modal-max-iterations').value) || 6;
const checkpointInterval = parseInt(document.getElementById('modal-checkpoint-interval').value) || 3;

// In mode selector
const sidebarIterations = parseInt(document.getElementById('sidebar-max-iterations').value) || 9;
const sidebarCheckpoint = parseInt(document.getElementById('sidebar-checkpoint-interval').value) || 3;
```

**Why:** Fixes Issue #4 - different values can now be maintained for sidebar vs modal.

---

### SHOULD FIX NEXT (Data integrity issues)

#### 4. Add Proper Error Propagation [HIGH - 1 hour]
**Status:** Errors are printed to console but not returned to user

**Files:** 
- `/orchestrator/agents/agent_factory.py:135`
- `/orchestrator/agents/planner_agent.py:119-170`

**Current code (agent_factory.py):**
```python
planner_result = self.planner.generate_strategic_plan(goal, context)
results['planner'] = planner_result

if not planner_result.success:
    print(f"❌ Planning failed, stopping workflow")  # Only prints
    return results
```

**Fix:**
```python
planner_result = self.planner.generate_strategic_plan(goal, context)
results['planner'] = planner_result

if not planner_result.success:
    error_detail = planner_result.error or "Unknown error in planning"
    print(f"❌ Planning failed: {error_detail}")  # Print with detail
    
    # ALSO log for learning
    learning_entry = f"[PLANNING FAILED] {datetime.now().isoformat()}\n"
    learning_entry += f"Goal: {goal}\n"
    learning_entry += f"Error: {error_detail}\n"
    learning_file = Path(self.memory_path) / "entities" / "planning_errors.md"
    with open(learning_file, 'a') as f:
        f.write(learning_entry + "\n---\n")
    
    # Return error to user
    return {
        "status": "error",
        "error": error_detail,
        "message": f"Planning failed at step 1: {error_detail}"
    }
```

**Also in simple_chatbox.py - catch planning errors:**
```python
# In /api/execute-plan endpoint
try:
    # ... run planning ...
except Exception as e:
    yield f"data: {json.dumps({
        'type': 'error',
        'error': str(e),
        'details': traceback.format_exc()  # NEW: Full traceback
    })}\n\n"
```

**Why:** Users can now see what failed instead of just "planning failed".

---

#### 5. Use Actual Memory Search Results [MEDIUM - 1 hour]
**Status:** Proposal shows hardcoded "60% coverage" regardless of actual results

**File:** `/simple_chatbox.py:476-540`

**Current code:**
```python
memory_results = await asyncio.to_thread(
    llama_planner.search_memory,
    request.selected_entities or [],
    queries
)

# But then ignores memory_results and hardcodes coverage
approach_plan = {
    "memory_percentage": 0.6,  # HARDCODED
    "research_percentage": 0.4,  # HARDCODED
}

return ProposalResponse(
    memory_coverage=0.6,  # HARDCODED
    research_coverage=0.4,  # HARDCODED
)
```

**Fix:**
```python
memory_results = await asyncio.to_thread(
    llama_planner.search_memory,
    request.selected_entities or [],
    queries
)

# USE actual memory results
actual_memory_coverage = memory_results.get("coverage", 0.0)
actual_research_coverage = 0.4 if queries else 0.0  # Scale down research if low memory

approach_plan = {
    "memory_percentage": actual_memory_coverage,  # USE ACTUAL
    "research_percentage": actual_research_coverage,  # CALCULATED
}

# Also track which entities were found/missing
found_entities = memory_results.get("entities_found", [])
missing_entities = memory_results.get("entities_missing", [])

proposal_text = f"""
## Selected Entities Status
- Found: {', '.join(found_entities) if found_entities else 'None'}
- Missing: {', '.join(missing_entities) if missing_entities else 'None'}

## Memory Coverage
- Actual coverage from memory: {actual_memory_coverage * 100:.0f}%
- Will supplement with research: {actual_research_coverage * 100:.0f}%
"""

return ProposalResponse(
    memory_coverage=actual_memory_coverage,  # ACTUAL
    research_coverage=actual_research_coverage,  # ACTUAL
    entity_names=found_entities,  # Show what exists
    # ... add field for missing_entities ...
)
```

**Why:** Proposal now reflects reality - user can see if selected entities exist or not.

---

#### 6. Fix Threading Race Condition [MEDIUM - 45 minutes]
**Status:** Checkpoint approval signal can be lost due to race condition

**File:** `/approval_gates.py:340-361`

**Current code:**
```python
def wait_for_checkpoint_approval(self, session_id: str, timeout: int = 3600) -> bool:
    session = self.get(session_id)
    
    session.checkpoint_approval_event.clear()  # Clear BEFORE wait
    session.checkpoint_approved = False
    
    # Wait for approval
    session.checkpoint_approval_event.wait(timeout=timeout)  # Can miss signal!
    
    return session.checkpoint_approved
```

**Problem:** If approval comes between clear() and wait(), it's lost.

**Fix:**
```python
def wait_for_checkpoint_approval(self, session_id: str, checkpoint_num: int = 0, timeout: int = 3600) -> bool:
    """Wait for checkpoint approval - fixed race condition."""
    session = self.get(session_id)
    if not session:
        return False
    
    # Store expected checkpoint number
    session.expected_checkpoint = checkpoint_num
    
    # DO NOT CLEAR before checking if already approved
    # Instead, check if this checkpoint is already approved
    if session.checkpoint_approved and session.approved_checkpoint == checkpoint_num:
        return True
    
    # Only clear if we're waiting for a new checkpoint
    session.checkpoint_approval_event.clear()
    session.checkpoint_approved = False
    session.approved_checkpoint = None
    
    # Wait for approval
    is_set = session.checkpoint_approval_event.wait(timeout=timeout)
    
    # Verify we got approval for THIS checkpoint
    return is_set and session.approved_checkpoint == checkpoint_num
```

**Update set_checkpoint_approved:**
```python
def set_checkpoint_approved(self, session_id: str, checkpoint_num: int) -> bool:
    """Mark checkpoint as approved - with checkpoint number validation."""
    session = self.get(session_id)
    if session:
        session.checkpoint_approved = True
        session.approved_checkpoint = checkpoint_num  # NEW: Track which checkpoint
        session.checkpoint_approval_event.set()
        return True
    return False
```

**Why:** Approval signal can't be lost now - it's stored in session state.

---

#### 7. Stop Silencing Exceptions [MEDIUM - 1 hour]
**Status:** Exception handlers use `pass` instead of logging

**Files:**
- `/llama_planner.py:231-232`
- `/orchestrator/agents/planner_agent.py:155-170`

**Current code:**
```python
except Exception as e:
    pass  # SILENT!
```

**Fix:**
```python
except Exception as e:
    import traceback
    error_msg = f"{type(e).__name__}: {str(e)}"
    traceback.print_exc()  # Print full traceback
    
    # Also log to learning system
    if hasattr(self, 'memory_path'):
        error_file = Path(self.memory_path) / "entities" / "system_errors.md"
        with open(error_file, 'a') as f:
            f.write(f"\n## {datetime.now().isoformat()}\n")
            f.write(f"```\n{traceback.format_exc()}\n```\n")
    
    # Re-raise or return error (don't swallow)
    raise  # Let caller handle it
```

**Why:** Errors are now visible and logged for debugging.

---

### NICE TO HAVE (Robustness)

#### 8. Validate Agent Initialization [LOW - 1 hour]
**File:** `/approval_gates.py:25-32`

**Add health check:**
```python
class PlanningSession:
    def __init__(self, session_id: str, memory_path: str):
        self.id = session_id
        self.created_at = datetime.now().isoformat()
        self.memory_path = memory_path
        
        # Initialize agent with error handling
        try:
            self.agent = Agent(memory_path=memory_path)
            # Test connection
            test_response = self.agent.chat("What is 2+2?")  # Quick test
            if not test_response:
                raise RuntimeError("Agent returned empty response")
            self.agent_healthy = True
        except Exception as e:
            print(f"⚠️ Agent initialization failed: {e}")
            self.agent = None
            self.agent_healthy = False
            self.agent_error = str(e)
```

**Then check before using:**
```python
@app.post("/api/chat")
async def handle_chat(request: ChatRequest):
    session_id, session = session_manager.get_or_create(request.session_id)
    
    if not session.agent_healthy:
        raise HTTPException(
            status_code=503,
            detail=f"Agent not available: {session.agent_error}"
        )
    
    # Safe to use agent now
    response = await asyncio.to_thread(agent.chat, message)
```

**Why:** Users get clear message instead of cryptic connection error.

---

#### 9. Validate Context Before Planning [LOW - 45 minutes]
**File:** `/orchestrator/agents/planner_agent.py:62-72`

**Add validation:**
```python
project_context = self._retrieve_project_context(goal)
if not project_context or len(project_context.strip()) == 0:
    print(f"   ⚠️ WARNING: No project context retrieved")

successful_patterns = self._retrieve_successful_patterns()
if not successful_patterns:
    print(f"   ℹ️ INFO: No successful patterns found (first run?)")

if not project_context and not successful_patterns:
    # No context at all - warn but continue
    print(f"   ⚠️ WARNING: Planning with minimal context (no project data)")
```

**Why:** System won't silently plan with no data - user knows what's happening.

---

#### 10. Match Checkpoint Numbers [LOW - 30 minutes]
**File:** `/simple_chatbox.py:881-902`

**Current:**
```python
@app.post("/api/checkpoint-approval")
async def checkpoint_approval_endpoint(request: Dict[str, Any]):
    session_id = request.get("session_id")
    checkpoint_number = request.get("checkpoint", 0)  # Received but not used
    session_manager.set_checkpoint_approved(session_id)  # Doesn't pass checkpoint
```

**Fix:**
```python
@app.post("/api/checkpoint-approval")
async def checkpoint_approval_endpoint(request: Dict[str, Any]):
    session_id = request.get("session_id")
    checkpoint_number = request.get("checkpoint", 0)
    
    # Validate this is the checkpoint we're waiting for
    session = session_manager.get(session_id)
    if session and hasattr(session, 'expected_checkpoint'):
        if session.expected_checkpoint != checkpoint_number:
            return {
                "status": "error",
                "message": f"Checkpoint mismatch: expected {session.expected_checkpoint}, got {checkpoint_number}"
            }
    
    # Approve the specific checkpoint
    session_manager.set_checkpoint_approved(session_id, checkpoint_number)
    
    return {
        "status": "approved",
        "checkpoint": checkpoint_number
    }
```

**Why:** Can't accidentally approve wrong checkpoint.

---

## Implementation Order

**Phase 1 (Must do first - 4 hours):**
1. Remove hardcoded entity names (goal_analyzer.py)
2. Add entity validation (llama_planner.py)
3. Fix input field IDs (index.html)
4. Add error propagation (agent_factory.py)

**Phase 2 (Data integrity - 3 hours):**
5. Use actual memory results (simple_chatbox.py)
6. Fix threading race condition (approval_gates.py)
7. Stop silencing exceptions (multiple files)

**Phase 3 (Robustness - 2.5 hours):**
8. Validate agent init
9. Validate context
10. Match checkpoint numbers

**Total estimated time: 9.5 hours**

---

## Testing Checklist

After implementing fixes:

- [ ] Select specific entities in sidebar
- [ ] Verify proposal shows selected entities exist
- [ ] Verify proposal shows actual memory coverage (not hardcoded 60%)
- [ ] Set different max_iterations in sidebar (e.g., 3)
- [ ] Check approval modal still reads modal value (e.g., 6)
- [ ] Start planning with missing entities and verify error shows which ones are missing
- [ ] Planning failure shows actual error message (not just "planning failed")
- [ ] Reach checkpoint 1, approve it
- [ ] Reach checkpoint 2, approve it
- [ ] Verify planning continued (not stuck at checkpoint 1)
- [ ] Run complete planning iteration with proper entity searching

