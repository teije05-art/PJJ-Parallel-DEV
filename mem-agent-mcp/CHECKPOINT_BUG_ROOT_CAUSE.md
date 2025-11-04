# Root Cause Analysis: Checkpoint Approval Bug

## The Issue in One Sentence
**After user approves a checkpoint, the SSE stream sends a `checkpoint_approved` event but then doesn't properly resume the orchestrator's iteration loop to continue planning.**

---

## Technical Root Cause

### The Broken Code Flow

**File:** `simple_chatbox.py`, lines 1305-1330 (SSE Handler inside `event_stream()` function)

```python
for item in iteration_generator:
    if isinstance(item, dict):
        if item.get("type") == "checkpoint":
            checkpoint_count += 1
            checkpoint_data = {...}
            
            # Send checkpoint to frontend
            yield f"data: {json.dumps(checkpoint_data)}\n\n"
            
            # WAIT FOR APPROVAL (BLOCKS HERE)
            approval_received = session_manager.wait_for_checkpoint_approval(session_id)
            
            # Send approval confirmation
            if approval_received:
                yield f"data: {json.dumps({'type': 'checkpoint_approved'})}\n\n"
                # ← LOOP CONTINUES HERE
            else:
                yield f"data: {json.dumps({'type': 'checkpoint_rejected'})}\n\n"
                break
        
        elif item.get("type") == "final_plan":
            # Send final plan
            yield f"data: {json.dumps({'type': 'final_plan', ...})}\n\n"
```

### Why It's Broken

The loop structure has a critical flaw:

```
for item in iteration_generator:
    if item["type"] == "checkpoint":
        yield checkpoint_data
        wait_for_approval()        # BLOCKS
        yield checkpoint_approved  # After unblock
        # ← Loop continues here
        # But where does it get the NEXT item from?
        # It expects iteration_generator to yield the next item
        # But iteration_generator is still inside simple_orchestrator.py
        # which YIELDED the checkpoint and is now WAITING for something...
```

### What Happens Step By Step

1. **Iteration runs in orchestrator** (`simple_orchestrator.py:305-480`)
   - Calls workflow, gets results
   - Checks if should checkpoint (line 432)
   - **Yields checkpoint event** (line 447)
   - **Control returns to SSE handler** in simple_chatbox.py

2. **SSE handler receives checkpoint** (simple_chatbox.py:1268)
   - Gets `checkpoint_data` from `item`
   - **Yields** it to frontend (line 1299)
   - **Blocks at** `wait_for_checkpoint_approval()` (line 1311)

3. **Frontend receives checkpoint** (JavaScript in browser)
   - Shows approval modal
   - User clicks "Approve"
   - Sends POST to `/api/checkpoint-approval`

4. **Backend receives approval** (`/api/checkpoint-approval` endpoint, line 1429)
   - Puts approval in session queue (line 1472)
   - Returns success response

5. **SSE handler unblocks** (simple_chatbox.py:1311)
   - `wait_for_checkpoint_approval()` returns True
   - **Yields** `checkpoint_approved` (line 1324)
   - **Loop continues** (line 1325)

6. **Loop expects next item from orchestrator** 
   - Calls `next(iteration_generator)`
   - But orchestrator's `run_iterative_planning()` is at line 432-456:
     ```python
     if iteration_mgr.should_checkpoint():
         # Yielded checkpoint event
         yield {...}
         # ← After yield, execution stops here
         # ← Control was in SSE handler
         # ← Generator is SUSPENDED at this point
     ```
   - **Generator cannot resume!**
   - Orchestrator's execution was suspended at the checkpoint yield
   - The orchestrator code after the checkpoint yield never executes!

7. **What SHOULD happen** (but doesn't)
   - After checkpoint yield in orchestrator (line 447), there's nothing!
   - Orchestrator expects to continue to line 461+ but it's suspended
   - The generator will try to continue the for loop but:
     - The orchestrator's checkpoint handling returns nothing
     - The loop ends (StopIteration)
   - **Orchestrator NEVER continues to next iteration**

---

## The Real Problem

### Multi-Iteration Orchestrator Has No "Resume Logic"

**File:** `simple_orchestrator.py`, lines 432-456

```python
if iteration_mgr.should_checkpoint():
    checkpoint_summary = self._generate_checkpoint_summary(...)
    
    yield {
        'type': 'checkpoint',
        ...
    }
    # ← Generator SUSPENDS here
    # ← When it resumes, execution continues HERE (line 457)
    # ← But there's nothing to resume!
    # ← The while loop should continue to next iteration
    # ← But the orchestrator doesn't know if user approved or rejected!
```

### The Missing Pattern

**Single-iteration** (works because it doesn't need to):
```python
if self.max_iterations == 1:
    decision_approved = True  # Auto-approve
    # ... extract plan, yield final_plan, return
```

**Multi-iteration** (broken because it doesn't track approval):
```python
if iteration_mgr.should_checkpoint():
    yield checkpoint
    # ← Generator suspends
    # ← When resumes, how does it KNOW if approved?
    # ← It doesn't! No mechanism to track approval status!
```

---

## The Fix Required

### Option 1: Add Approval Tracking to Session (CORRECT)
The orchestrator needs to check the session to see if the checkpoint was approved:

```python
if iteration_mgr.should_checkpoint():
    yield {
        'type': 'checkpoint',
        'checkpoint_num': checkpoint_count
    }
    # After yield, when generator resumes:
    # Check if user approved by querying session
    approval_status = session_manager.was_checkpoint_approved(session_id, checkpoint_count)
    
    if not approval_status:
        # User rejected - exit loop
        break
    # If approved, loop continues to next iteration
```

### Option 2: Pass Approval Callback (COMPLEX)
Pass a callback function the orchestrator can check:

```python
def run_iterative_planning(self, ..., approval_checker=None):
    ...
    if iteration_mgr.should_checkpoint():
        yield checkpoint
        # Check approval via callback
        if approval_checker and not approval_checker(checkpoint_count):
            break
```

### Option 3: Use a Shared State Dict (SIMPLE)
Store approval decisions in a shared dict that orchestrator can poll:

```python
# In simple_chatbox.py SSE handler:
session_state = {
    'checkpoint_approvals': {}  # checkpoint_num -> True/False
}

# When approval received:
session_state['checkpoint_approvals'][checkpoint_num] = True

# In orchestrator:
if iteration_mgr.should_checkpoint():
    yield checkpoint
    # Poll shared state for approval
    while checkpoint_num not in session_state['checkpoint_approvals']:
        time.sleep(0.1)  # Poll every 100ms
    
    if not session_state['checkpoint_approvals'][checkpoint_num]:
        break
```

---

## Current Code vs What's Needed

### Current Architecture (Broken)

```
SSE Handler in simple_chatbox.py:
  for item in orchestrator.run_iterative_planning():
      if checkpoint:
          yield checkpoint_data
          wait_for_approval()  # Blocks until frontend approves
          yield checkpoint_approved
          # Loop continues... expecting next item from orchestrator
          # BUT orchestrator is suspended and can't resume without knowing approval!

Orchestrator in simple_orchestrator.py:
  while iteration < max:
      workflow.run()
      if should_checkpoint():
          yield checkpoint  # Suspends here
          # ← Can't continue because doesn't know approval status!
```

### Required Architecture (Should Work)

```
SSE Handler in simple_chatbox.py:
  for item in orchestrator.run_iterative_planning(session=session):
      if checkpoint:
          yield checkpoint_data
          wait_for_approval()  # Blocks until frontend approves
          yield checkpoint_approved
          # Loop continues to next item from orchestrator
          # Orchestrator resumes from checkpoint yield
          # Checks session for approval: ✅ approved
          # Continues to next iteration

Orchestrator in simple_orchestrator.py:
  while iteration < max:
      workflow.run()
      if should_checkpoint():
          yield checkpoint  # Suspends
          # On resume: Check if approved by querying session
          if not session_manager.was_checkpoint_approved(session_id, checkpoint_num):
              break  # User rejected, exit
          # Continue to next iteration
```

---

## The Key Missing Pieces

### In simple_orchestrator.py
**Missing:** After checkpoint yield, check if approved before continuing

```python
# MISSING THIS:
if iteration_mgr.should_checkpoint():
    yield checkpoint
    
    # ← NEED: Check approval status
    # approval_status = self.get_checkpoint_approval_from_session(...)
    # if not approval_status:
    #     break  # Exit planning
```

### In approval_gates.py
**Needs:** Method to check if checkpoint was approved

```python
# MISSING THIS METHOD:
def was_checkpoint_approved(self, session_id: str, checkpoint_num: int) -> bool:
    """Check if a specific checkpoint was approved by user."""
    session = self.get(session_id)
    if session:
        # Check if approval was recorded for this checkpoint
        return session.checkpoint_approvals.get(checkpoint_num, False)
    return False
```

### In simple_chatbox.py
**Needs:** Track which checkpoints were approved

```python
# MISSING THIS:
if approval_received:
    # Record that THIS checkpoint was approved
    session_manager.record_checkpoint_approval(session_id, checkpoint_count, True)
    yield f"data: {json.dumps({'type': 'checkpoint_approved'})}\n\n"
```

---

## Summary

| Component | Issue | Fix |
|-----------|-------|-----|
| **simple_orchestrator.py** | After checkpoint yield, doesn't check if approved before continuing | Add approval check before loop continues |
| **approval_gates.py** | No method to query checkpoint approval status | Add `was_checkpoint_approved()` method |
| **simple_chatbox.py** | Records approval in queue but orchestrator can't check it | Add `record_checkpoint_approval()` and ensure orchestrator can query it |
| **Session** | No persistent approval tracking across yield/resume | Need dict like `session.checkpoint_approvals[checkpoint_num] = True/False` |

---

## The Fix In Pseudocode

```python
# In simple_orchestrator.py run_iterative_planning():

while iteration_mgr.current_iteration < max_iterations:
    # ... run iteration ...
    
    if iteration_mgr.should_checkpoint():
        checkpoint_num = iteration_mgr.checkpoint_count
        
        # Yield checkpoint to SSE handler
        yield {
            'type': 'checkpoint',
            'checkpoint_num': checkpoint_num,
            ...
        }
        
        # ← GENERATOR SUSPENDS HERE ←
        
        # ← GENERATOR RESUMES HERE (after user approves/rejects) ←
        
        # NEW: Check if user approved THIS checkpoint
        if not session_manager.was_checkpoint_approved(session_id, checkpoint_num):
            # User rejected - stop planning
            break
        # If approved, loop continues to next iteration
    
    # Check if at final iteration
    if iteration_mgr.at_final_iteration():
        break

# After loop ends, yield final plan
yield {
    'type': 'final_plan',
    ...
}
```

