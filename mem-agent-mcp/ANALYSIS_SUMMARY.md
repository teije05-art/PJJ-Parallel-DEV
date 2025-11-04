# Analysis Summary: Single vs Multi-Iteration Planning

## Key Findings

### 1. Two Completely Different Orchestrator Methods

The system doesn't reuse the same orchestrator method. Instead:

- **Single-iteration**: Calls `SimpleOrchestrator.run_enhanced_learning_loop()` 
  - Location: `simple_orchestrator.py:145-257`
  - Auto-approves (line 175)
  - Yields one `final_plan` event (line 212)

- **Multi-iteration**: Calls `SimpleOrchestrator.run_iterative_planning()`
  - Location: `simple_orchestrator.py:261-502`
  - User-approved at checkpoints (line 432)
  - Yields multiple `checkpoint` events, then `final_plan` (line 493)

### 2. Control Values (iterations, checkpoint_interval)

**Where Stored:**
- During proposal generation: `session.proposal_data` (approval_gates.py:192)
- Retrieved during approval: (simple_chatbox.py:448-450)

**Both flows use the same session management** via `SessionManager` (one global instance)

### 3. The Broken Multi-Iteration Flow

The bug is in the **yield/resume pattern**:

1. Orchestrator yields `checkpoint` event (simple_orchestrator.py:447)
2. Generator suspends at that yield point
3. SSE handler receives checkpoint, yields it to frontend
4. SSE handler waits for approval
5. Approval received and queued
6. SSE handler yields `checkpoint_approved`
7. Loop tries to get next item from generator
8. **BROKEN**: Generator cannot resume because:
   - Orchestrator doesn't know if checkpoint was approved
   - No code path after the yield to handle approval result
   - Generator ends without continuing iterations

### 4. Root Cause

**File:** `simple_orchestrator.py`, lines 432-456

```python
if iteration_mgr.should_checkpoint():
    yield {'type': 'checkpoint', ...}
    # ← GENERATOR SUSPENDS HERE
    # ← After resume, execution continues to line 457
    # ← But line 457+ doesn't handle checkpoint approval!
    # ← Generator doesn't know approval status!
```

### 5. Missing Logic

The orchestrator needs to:
1. After yielding checkpoint, know whether user approved/rejected
2. Continue to next iteration if approved
3. Exit if rejected

Currently, there's no mechanism to communicate approval status back to the orchestrator.

---

## Detailed Findings

### Single-Iteration Flow (WORKING)

```
/api/plan (max_iterations=1)
  ↓
_execute_single_iteration_planning()
  ↓
orchestrator.run_enhanced_learning_loop()
  ↓
[runs 4-agent workflow once]
  ↓
[auto-approves at line 175]
  ↓
[yields final_plan at line 212]
  ↓
PlanResponse sent to user
✅ WORKS
```

### Multi-Iteration Flow (BROKEN AT CHECKPOINT)

```
/api/plan (max_iterations>1)
  ↓
_generate_planning_proposal()
  ↓
store_proposal() saves max_iterations, checkpoint_interval
  ↓
[Frontend shows approval modal]
  ↓
/api/approve
  ↓
_execute_multi_iteration_planning(max_iterations, checkpoint_interval)
  ↓
orchestrator.run_iterative_planning()
  ↓
[Iteration 1: runs 4-agent workflow]
  ↓
[should_checkpoint() = True at iteration 2]
  ↓
[yields checkpoint at line 447]
  ↓
[SSE handler receives checkpoint]
  ↓
[SSE handler yields checkpoint_data]
  ↓
[SSE handler blocks at wait_for_checkpoint_approval()]
  ↓
[Frontend shows checkpoint approval modal]
  ↓
/api/checkpoint-approval
  ↓
[Approval queued in session]
  ↓
[SSE handler unblocks]
  ↓
[SSE handler yields checkpoint_approved]
  ↓
[SSE handler loop tries to continue]
  ↓
❌ Generator doesn't resume properly
   Orchestrator's loop never continues
   No next item from generator
   Planning stops
```

---

## Code Reference Summary

| Component | Location | Purpose |
|-----------|----------|---------|
| Single-iteration entry | simple_chatbox.py:423-424 | Routes to single-iteration method |
| Single-iteration execution | simple_chatbox.py:487-557 | Calls orchestrator and collects result |
| Single-iteration orchestrator | simple_orchestrator.py:145-257 | One iteration, auto-approve, return plan |
| Multi-iteration entry | simple_chatbox.py:427-428 | Routes to proposal generation |
| Proposal generation | simple_chatbox.py:735-990 | Generates proposal, stores control values |
| Multi-iteration approval | simple_chatbox.py:431-480 | Retrieves control values, executes |
| Multi-iteration execution | simple_chatbox.py:993-1077 | Calls orchestrator, handles checkpoints |
| Multi-iteration orchestrator | simple_orchestrator.py:261-502 | Multiple iterations, checkpoints, user approval |
| SSE streaming | simple_chatbox.py:1214-1351 | Streams events to frontend |
| Checkpoint approval | simple_chatbox.py:1429-1487 | Receives user's approve/reject decision |
| Session management | approval_gates.py:140-456 | Stores proposals, plans, approvals |
| Queue system | approval_gates.py:361-422 | Handles checkpoint approval blocking |

---

## Session Management

### PlanningSession (approval_gates.py:24-138)

**Stores per session:**
- `agent`: The Agent instance
- `memory_manager`: SegmentedMemory for learning
- `orchestrator`: SimpleOrchestrator instance
- `generated_plan`: Final plan content
- `plan_metadata`: Plan stats (frameworks, data points, etc)
- `proposal_data`: Proposal details + **control values** (max_iterations, checkpoint_interval)
- `checkpoint_summaries`: Full summaries per checkpoint
- `checkpoint_approval_queue`: Queue for approval blocking (queue.Queue)
- `selected_plans_for_learning`: Plans to learn from

### SessionManager (approval_gates.py:140-456)

**Key Methods:**
- `get_or_create()`: Get or create session
- `store_proposal()`: Save proposal with control values (line 171)
- `get_proposal()`: Retrieve stored proposal (line 207)
- `set_checkpoint_approved()`: Queue approval (line 361)
- `wait_for_checkpoint_approval()`: Block until approval received (line 389)
- `store_plan()`: Save completed plan (line 228)

---

## Specific Answers to Your Questions

### Q1: Do both flows use the same orchestrator?
**A:** Same class (`SimpleOrchestrator`), different methods:
- Single: `run_enhanced_learning_loop()` (line 145)
- Multi: `run_iterative_planning()` (line 261)

### Q2: What's the key difference in how they generate and return plans?
**A:** 
- Single: Runs workflow once, auto-approves, yields plan
- Multi: Runs workflow multiple times, yields checkpoints for approval, then yields plan

### Q3: How does frontend receive plan completion in single-iteration?
**A:** SSE event: `{"type": "final_plan", "plan": content, ...}` (line 1227)

### Q4: What SHOULD happen when user approves checkpoint?
**A:** 
1. Approval sent to `/api/checkpoint-approval`
2. Queued in session
3. SSE handler unblocks from `wait_for_checkpoint_approval()`
4. **Should**: Orchestrator checks approval status and continues
5. **Actually**: Orchestrator doesn't know approval status, loop breaks

### Q5: Are they using the same session management system?
**A:** YES - both use same `SessionManager` instance (global)
- Control values stored in `session.proposal_data`
- Approval queued in `session.checkpoint_approval_queue`
- Plan stored in `session.generated_plan`

---

## Files Generated

This analysis created two detailed documents:

1. **FLOW_ANALYSIS.md** - Complete code flow analysis with line numbers
2. **CHECKPOINT_BUG_ROOT_CAUSE.md** - Root cause analysis and fix options

Both are in the project root directory.

