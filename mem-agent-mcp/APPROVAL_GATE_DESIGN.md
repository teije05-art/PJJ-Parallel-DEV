# Approval Gate Design Document
**Date:** October 29, 2025
**Purpose:** Design approval gates for proposal and checkpoint review in multi-iteration planning

---

## Overview

The multi-iteration planning system needs two approval gates:
1. **Proposal Approval Gate** - User reviews and approves the initial proposal before iterations begin
2. **Checkpoint Approval Gate** - User reviews iteration progress at checkpoints and approves continuation

Both gates pause execution and wait for user decision.

---

## 1. PROPOSAL APPROVAL GATE

### Purpose
User sees the initial proposal, decides whether to:
- ✅ **APPROVE** - Start iterations
- ❌ **REJECT** - Cancel planning
- 🔄 **REQUEST CHANGES** - Ask for proposal adjustments

### Flow

```
User Request (max_iterations > 1)
  ↓
Generate Proposal
  ↓
Return: ApprovalRequest
  {
    "status": "awaiting_approval",
    "approval_type": "proposal",
    "proposal": "...",
    "goal": "...",
    "estimated_iterations": 6,
    "checkpoint_interval": 3
  }
  ↓
[USER REVIEWS AND DECIDES]
  ↓
User Response
  {
    "approval_status": "approved|rejected|adjust_requested",
    "adjusted_proposal": "..." (optional, if adjust_requested),
    "feedback": "..." (optional)
  }
  ↓
IF approved → Execute multi-iteration planning
IF rejected → Return error/cancellation
IF adjust_requested → Regenerate proposal with feedback
```

### Implementation Details

#### Request Model
```python
class ApprovalRequest(BaseModel):
    """Request for user approval of proposal or checkpoint"""
    status: str  # "awaiting_approval"
    approval_type: str  # "proposal" or "checkpoint"
    approval_id: str  # Unique ID to track this request

    # For proposal approval
    proposal: Optional[str] = None
    goal: Optional[str] = None
    estimated_iterations: Optional[int] = None
    checkpoint_interval: Optional[int] = None

    # For checkpoint approval
    checkpoint_summary: Optional[str] = None
    iteration: Optional[int] = None
    total_iterations: Optional[int] = None
    insights: Optional[List[str]] = None

    timestamp: str
    session_id: str
```

#### Response Model
```python
class ApprovalResponse(BaseModel):
    """User's approval response"""
    approval_id: str  # Must match the ApprovalRequest
    approval_status: str  # "approved", "rejected", "adjust_requested"
    adjusted_proposal: Optional[str] = None  # If adjust_requested
    feedback: Optional[str] = None
    timestamp: str
```

#### Session Storage
Store pending approvals in session:
```python
session["pending_approvals"] = {
    "approval_id_1": {
        "type": "proposal",
        "request": ApprovalRequest(...),
        "status": "pending"
    }
}
```

---

## 2. CHECKPOINT APPROVAL GATE

### Purpose
User sees checkpoint summary every N iterations and decides:
- ✅ **APPROVE** - Continue iterations
- ❌ **PAUSE** - Stop current iteration and go to final synthesis
- 🔄 **ADJUST** - Modify strategy for next iterations

### Flow

```
Iteration N reached checkpoint
  ↓
Generate Checkpoint Summary (already implemented)
  ↓
Return: ApprovalRequest
  {
    "status": "awaiting_approval",
    "approval_type": "checkpoint",
    "approval_id": "checkpoint_iter3",
    "iteration": 3,
    "total_iterations": 6,
    "checkpoint_summary": "...",
    "insights": [...]
  }
  ↓
[USER REVIEWS AND DECIDES]
  ↓
User Response
  {
    "approval_id": "checkpoint_iter3",
    "approval_status": "approved|paused|adjust_strategy",
    "adjusted_strategy": "..." (optional)
  }
  ↓
IF approved → Continue with remaining iterations
IF paused → Skip to final synthesis
IF adjust_strategy → Modify context for next iterations
```

### Implementation Details

#### Checkpoint Iterator Enhancement
Current: Generator yields checkpoints with auto-approval
New: Generator yields checkpoints as ApprovalRequest, waits for response

```python
# Current (auto-approves):
yield {
    'type': 'checkpoint',
    'iteration': iteration_num,
    'summary': checkpoint_summary
}

# New (waits for approval):
yield {
    'type': 'awaiting_approval',
    'approval_type': 'checkpoint',
    'approval_id': f'checkpoint_iter{iteration_num}',
    'iteration': iteration_num,
    'total_iterations': max_iterations,
    'checkpoint_summary': checkpoint_summary,
    'insights': insights
}
# Generator pauses here
# Returns when checkpoint_response provided

# OR if approval rejected:
yield {
    'type': 'paused',
    'reason': 'user_requested_pause',
    'iteration': iteration_num,
    'proceed_to_synthesis': True
}
```

---

## 3. INTEGRATION POINTS

### Endpoint: /api/plan

**Step 1: Proposal Phase**
```python
# In start_planning():
if request.max_iterations > 1:
    # Generate proposal
    proposal_response = await generate_proposal(...)

    if proposal_response.status != 'success':
        return error

    proposal = proposal_response['proposal']

    # RETURN APPROVAL REQUEST (don't continue yet)
    approval_request = ApprovalRequest(
        status="awaiting_approval",
        approval_type="proposal",
        approval_id=f"proposal_{session_id}",
        proposal=proposal,
        goal=goal,
        estimated_iterations=request.max_iterations,
        checkpoint_interval=request.checkpoint_interval,
        timestamp=datetime.now().isoformat(),
        session_id=session_id
    )

    # Store in session
    session["pending_approvals"][approval_request.approval_id] = {
        "type": "proposal",
        "request": approval_request,
        "status": "pending"
    }

    return {
        "status": "awaiting_approval",
        "approval_request": approval_request.dict(),
        "session_id": session_id
    }
```

**Step 2: Proposal Approval Response**
```python
# New endpoint: /api/approve
@app.post("/api/approve")
async def submit_approval(request: ApprovalResponse):
    """User submits approval response"""

    session_id, session = get_or_create_session(request.approval_id)  # From session

    if request.approval_id not in session.get("pending_approvals", {}):
        return {"status": "error", "message": "Approval ID not found"}

    pending = session["pending_approvals"][request.approval_id]

    if request.approval_status == "rejected":
        # Delete pending approval
        del session["pending_approvals"][request.approval_id]
        return {
            "status": "cancelled",
            "message": "Planning cancelled"
        }

    if request.approval_status == "adjust_requested":
        # Regenerate proposal with feedback
        # Then return new ApprovalRequest
        pass

    if request.approval_status == "approved":
        # Move to execution
        if pending["type"] == "proposal":
            # Start multi-iteration planning
            proposal = pending["request"].proposal
            return await continue_multi_iteration_planning(
                session_id, proposal, request
            )

        elif pending["type"] == "checkpoint":
            # Continue iterations
            return await continue_iteration_after_checkpoint(
                session_id, request
            )
```

---

## 4. SESSION MANAGEMENT

### Session State Enhancement
```python
session["multi_iteration_state"] = {
    "proposal": "...",
    "goal": "...",
    "max_iterations": 6,
    "checkpoint_interval": 3,
    "current_iteration": 0,
    "pending_approvals": {},
    "completed_checkpoints": [],
    "iteration_results": [],
    "generator": None,  # Generator object for resuming
    "is_paused": False
}
```

### Session Persistence
Store approval state so user can return later:
```python
# Save to disk
session_file = memory_path / "sessions" / f"{session_id}.json"
session_file.write_text(json.dumps({
    "proposal": proposal,
    "pending_approval_id": approval_id,
    "status": "awaiting_approval"
}))
```

---

## 5. RESPONSE FORMATS

### Phase 1: Awaiting Proposal Approval
```json
{
    "status": "awaiting_approval",
    "approval_type": "proposal",
    "approval_id": "proposal_session123",
    "proposal": "**PROPOSAL TEXT HERE**",
    "goal": "User's goal",
    "estimated_iterations": 6,
    "checkpoint_interval": 3,
    "session_id": "session123",
    "timestamp": "2025-10-29T12:00:00Z",
    "next_action": "POST to /api/approve with ApprovalResponse"
}
```

### Phase 2: Planning in Progress
```json
{
    "status": "planning_in_progress",
    "session_id": "session123",
    "current_iteration": 2,
    "total_iterations": 6,
    "message": "Iteration 2 of 6 planning..."
}
```

### Phase 3: Awaiting Checkpoint Approval
```json
{
    "status": "awaiting_approval",
    "approval_type": "checkpoint",
    "approval_id": "checkpoint_iter3",
    "iteration": 3,
    "total_iterations": 6,
    "checkpoint_summary": "**CHECKPOINT TEXT HERE**",
    "insights": [
        "Top insight 1",
        "Top insight 2",
        "Top insight 3"
    ],
    "frameworks_evolved": 12,
    "data_points_collected": 45,
    "session_id": "session123",
    "timestamp": "2025-10-29T12:05:00Z",
    "next_action": "POST to /api/approve with ApprovalResponse"
}
```

### Phase 4: Final Plan Complete
```json
{
    "status": "complete",
    "session_id": "session123",
    "iterations_completed": 6,
    "total_iterations": 6,
    "final_plan": "**COMPLETE PLAN TEXT**",
    "plan_saved_to_memory": true,
    "memory_entities": [
        "executive_summary_report",
        "detailed_implementation_plan",
        ...
    ],
    "timestamp": "2025-10-29T12:10:00Z"
}
```

---

## 6. ERROR SCENARIOS

### Scenario 1: User Rejects Proposal
```json
{
    "status": "cancelled",
    "reason": "user_rejected_proposal",
    "message": "Planning cancelled. Please try again with a different approach.",
    "session_id": "session123"
}
```

### Scenario 2: User Pauses at Checkpoint
```json
{
    "status": "paused",
    "reason": "user_requested_pause",
    "iteration": 3,
    "total_iterations": 6,
    "message": "Planning paused. Proceeding to final synthesis with iterations 1-3.",
    "session_id": "session123",
    "next_action": "Plan will be synthesized and saved"
}
```

### Scenario 3: Session Expires
```json
{
    "status": "error",
    "error": "session_expired",
    "approval_id": "proposal_session123",
    "message": "Your session has expired. Please start planning again.",
    "session_id": "session123"
}
```

---

## 7. FRONTEND INTERACTION FLOW

### Timeline
```
T0: User submits planning request
    ↓
T1: Proposal generation (3-5 seconds)
    ↓
T2: System returns ApprovalRequest
    Frontend displays proposal with:
    - Proposal text
    - [APPROVE] [REJECT] [ADJUST] buttons
    ↓
T3: User clicks APPROVE
    ↓
T4: Multi-iteration planning starts
    Frontend shows progress: "Iteration 1/6..."
    ↓
T5: Checkpoint reached (after ~45 seconds for 3 iterations)
    ↓
T6: System returns checkpoint ApprovalRequest
    Frontend displays checkpoint with:
    - Summary text
    - Insights list
    - Progress chart
    - [CONTINUE] [PAUSE] [ADJUST] buttons
    ↓
T7: User clicks CONTINUE
    ↓
T8: Planning resumes
    ↓
T9: All iterations complete
    ↓
T10: Final plan displayed
    - Saved to memory
    - Ready for export
```

---

## 8. IMPLEMENTATION CHECKLIST

- [ ] Create ApprovalRequest and ApprovalResponse models
- [ ] Create /api/approve endpoint for handling responses
- [ ] Modify start_planning() to return ApprovalRequest for proposals
- [ ] Add approval tracking to session management
- [ ] Modify orchestrator.run_iterative_planning() to yield checkpoint ApprovalRequests
- [ ] Modify simple_chatbox.py to handle approval responses
- [ ] Add resumable generator pattern for paused iterations
- [ ] Store/retrieve approval state from session
- [ ] Handle session expiry for pending approvals
- [ ] Update error handling for rejection cases
- [ ] Create frontend UI for approval gates
- [ ] Test proposal approval flow
- [ ] Test checkpoint approval flow
- [ ] Test pause/resume functionality

---

## 9. BACKWARD COMPATIBILITY

### For Testing (auto-approve mode)
Add environment variable:
```python
APPROVAL_GATES_ENABLED = os.getenv("APPROVAL_GATES", "true").lower() == "true"

if not APPROVAL_GATES_ENABLED:
    # Auto-approve for testing
    approval_request = ...  # Still generate
    # But immediately approve it
    return continue_with_approved(approval_request)
```

Usage: `export APPROVAL_GATES=false` for auto-approval testing

---

## 10. TIMELINE FOR IMPLEMENTATION

- **Phase 1 (2-3 hours):** Create models and /api/approve endpoint
- **Phase 2 (2 hours):** Modify proposal flow to return ApprovalRequest
- **Phase 3 (3 hours):** Modify checkpoint flow to request approval
- **Phase 4 (2 hours):** Add session state management
- **Phase 5 (2 hours):** Error handling and edge cases
- **Phase 6 (2 hours):** Testing and validation

**Total Estimate:** 13-15 hours for full implementation

---

This design allows:
✅ User control over proposal and checkpoint progression
✅ Ability to reject or request adjustments
✅ Pausable iterations
✅ Session persistence
✅ Backward compatibility with auto-approval testing mode
