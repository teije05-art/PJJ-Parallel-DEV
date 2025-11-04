# Visual Flow Diagrams: Single vs Multi-Iteration

## Architecture Diagram

```
                    simple_chatbox.py
                    ================
                         /api/plan
                            |
                    ________|________
                   |                 |
         max_iterations == 1   max_iterations > 1
                   |                 |
                   |                 |
        ┌──────────┴─────────┐   ┌──┴──────────────────┐
        |                    |   |                     |
        v                    v   v                     v
   _execute_           _generate_          [Frontend shows
   single_iteration    planning_proposal    proposal modal]
   _planning()         ()                   
        |                    |
        |                    v
        |              store_proposal()
        |              [Save control values]
        |                    |
        |                    v
        |              ProposalResponse
        |                    |
        |                    v
        |                [Wait for user approval]
        |                    |
        |                    v
        |              /api/approve
        |                    |
        |      ┌─────────────┘
        |      |
        v      v
    ┌───────────────────────────────────┐
    | _execute_multi_iteration_planning |
    | (max_iterations from stored proposal)
    └───────────────────────────────────┘
        |
        v
    orchestrator.run_iterative_planning()
        |
        v
    /api/execute-plan (SSE streaming)
```

---

## Single-Iteration Detailed Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   SINGLE-ITERATION PLANNING                     │
│                        (WORKING ✅)                             │
└─────────────────────────────────────────────────────────────────┘

Step 1: Request
  /api/plan
  {
    goal: "...",
    max_iterations: 1
  }
  
Step 2: Route
  simple_chatbox.py:423
  if request.max_iterations == 1:
    return _execute_single_iteration_planning()

Step 3: Create Orchestrator
  simple_chatbox.py:502-506
  orchestrator = SimpleOrchestrator(
    memory_path=memory_path,
    max_iterations=1
  )

Step 4: Call Orchestrator Method
  simple_chatbox.py:513
  plan_generator = orchestrator.run_enhanced_learning_loop(goal)

Step 5: Orchestrator Executes (simple_orchestrator.py:145)
  for iteration in range(1, 1 + 1):  # Runs once
    context = context_manager.retrieve_context(goal)
    agent_results = workflow_coordinator.run_workflow(goal, context)
    
    if max_iterations == 1:  # Line 175
      decision_approved = True  # AUTO-APPROVE
    
    plan_content = agent_results.get("generator").output
    
    yield {
      "type": "final_plan",
      "plan": plan_content,
      "unique_frameworks": [...],
      "total_data_points": N
    }
    return

Step 6: Collect Results
  simple_chatbox.py:523-532
  for item in plan_generator:
    if item.get("type") == "final_plan":
      final_plan = item.get("plan")
      all_frameworks = item.get("unique_frameworks")

Step 7: Return Response
  simple_chatbox.py:537-545
  return PlanResponse(
    status="success",
    plan_content=final_plan,
    iterations=1,
    frameworks=all_frameworks
  )

Result: User gets plan immediately ✅
```

---

## Multi-Iteration Detailed Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                   MULTI-ITERATION PLANNING                       │
│                  (BROKEN AT CHECKPOINT ❌)                       │
└──────────────────────────────────────────────────────────────────┘

PHASE 1: PROPOSAL GENERATION
════════════════════════════

Step 1: Request
  /api/plan
  {
    goal: "...",
    max_iterations: 4,
    checkpoint_interval: 2
  }

Step 2: Route
  simple_chatbox.py:428
  return _generate_planning_proposal(session, request, session_id)

Step 3: Generate Proposal
  simple_chatbox.py:771-836
  llama_planner = LlamaPlanner(agent, memory_path)
  queries = generate_goal_specific_queries(goal)
  memory_results = llama_planner.search_memory(...)
  proposal_text = build comprehensive proposal...

Step 4: Store Control Values
  simple_chatbox.py:951-960
  session_manager.store_proposal(
    session_id=session_id,
    goal=goal,
    max_iterations=4,           ← CRITICAL
    checkpoint_interval=2,      ← CRITICAL
    ...
  )

Step 5: Return Proposal
  simple_chatbox.py:966-985
  return ProposalResponse(
    status="success",
    proposal=proposal_text,
    max_iterations=4,
    checkpoint_interval=2,
    ...
  )

Result: Frontend shows proposal modal, waits for approval


PHASE 2: USER APPROVAL OF PROPOSAL
═══════════════════════════════════

Step 6: User Reviews Proposal (Frontend)
  [Proposal Modal]
  [User clicks "Approve & Execute"]

Step 7: Send Approval
  /api/approve
  {
    session_id: "...",
    decision: "approve",
    goal: "..."
  }

Step 8: Retrieve Control Values
  simple_chatbox.py:448-450
  stored_proposal = session_manager.get_proposal(session_id)
  max_iterations = stored_proposal["max_iterations"]        # 4
  checkpoint_interval = stored_proposal["checkpoint_interval"] # 2

Step 9: Execute Planning
  simple_chatbox.py:452-459
  return _execute_multi_iteration_planning(
    session,
    goal,
    proposal,
    max_iterations=4,        ← FROM STORED
    checkpoint_interval=2,   ← FROM STORED
    session_id
  )


PHASE 3: MULTI-ITERATION EXECUTION (SSE STREAMING)
═══════════════════════════════════════════════════

Step 10: Create Orchestrator
  simple_chatbox.py:1013-1017
  orchestrator = SimpleOrchestrator(
    memory_path=memory_path,
    max_iterations=4
  )

Step 11: Open SSE Stream
  simple_chatbox.py:1214-1351
  async def event_stream():
    if max_iterations == 1:
      # (Single iteration path)
    else:
      # Multi-iteration path
      iteration_generator = orchestrator.run_iterative_planning(
        goal=goal,
        max_iterations=4,
        checkpoint_interval=2
      )
      
      for item in iteration_generator:
        if item.get("type") == "checkpoint":
          ...  (CHECKPOINT HANDLING)
        elif item.get("type") == "final_plan":
          ...  (FINAL PLAN)

Step 12: Stream Opens
  /api/execute-plan?goal=...&max_iterations=4&...
  SSE connection established
  Frontend: EventSource('/api/execute-plan?...')


ITERATION 1
═══════════

Step 13: Iteration 1 Runs (Orchestrator)
  simple_orchestrator.py:305-390
  
  iteration_num = 1
  context = context_manager.retrieve_context(goal)
  agent_results = workflow_coordinator.run_workflow(goal, context)
  [4-agent pipeline executes]
  
  iteration_result = IterationResult(
    iteration_num=1,
    plan=output,
    frameworks=[...],
    data_points=50
  )
  
  Check if checkpoint: should_checkpoint() → False (not at interval)

Step 14: Iteration 2 Runs (Orchestrator)
  simple_orchestrator.py:305-390
  
  iteration_num = 2
  context = context_manager.retrieve_context(goal)
  agent_results = workflow_coordinator.run_workflow(goal, context)
  [4-agent pipeline executes]
  
  iteration_result = IterationResult(...)
  
  Check if checkpoint: should_checkpoint() → True (iteration % 2 == 0)
  checkpoint_count = 1


CHECKPOINT REACHED
══════════════════

Step 15: Checkpoint Reached (Orchestrator)
  simple_orchestrator.py:432-456
  
  checkpoint_summary = generate_checkpoint_summary(...)
  
  yield {
    'type': 'checkpoint',
    'iteration': 2,
    'checkpoint_count': 1,
    'summary': '...',
    ...
  }
  
  # ← GENERATOR SUSPENDS HERE ←

Step 16: SSE Handler Receives Checkpoint
  simple_chatbox.py:1267-1330
  
  item = {
    'type': 'checkpoint',
    ...
  }
  
  checkpoint_count += 1
  checkpoint_data = {
    "type": "checkpoint_reached",
    "iteration": 2,
    "checkpoint_number": 1,
    ...
  }

Step 17: Send Checkpoint to Frontend
  simple_chatbox.py:1299
  yield f"data: {json.dumps(checkpoint_data)}\n\n"
  
  Frontend receives:
  {"type": "checkpoint_reached", "iteration": 2, ...}

Step 18: Show Approval Modal
  Frontend:
  [Checkpoint Approval Modal]
  [Approve] [Reject]

Step 19: Wait for User Approval (BLOCKS)
  simple_chatbox.py:1310-1311
  approval_received = session_manager.wait_for_checkpoint_approval(session_id)
  
  Backend blocks here in approval_gates.py:412
  while waiting for message from approval queue

Step 20: User Clicks Approve
  Frontend:
  POST /api/checkpoint-approval
  {
    session_id: "...",
    checkpoint: 1,
    decision: "approve"
  }

Step 21: Approval Received (Endpoint)
  simple_chatbox.py:1429-1487
  
  session_id = request.get("session_id")
  decision = request.get("decision")  # "approve"
  approved = (decision == "approve")  # True
  
  success = session_manager.set_checkpoint_approved(
    session_id,
    checkpoint_number=1,
    approved=True
  )

Step 22: Approval Queued
  approval_gates.py:375
  session.checkpoint_approval_queue.put(True, block=False)
  
  Also sets event for backward compatibility

Step 23: Wait Unblocks
  approval_gates.py:412
  approval_received = session.checkpoint_approval_queue.get(timeout=3600)
  # Returns True
  return True

Step 24: Send Approval Confirmation
  simple_chatbox.py:1321-1325
  
  if approval_received:
    yield f"data: {json.dumps({'type': 'checkpoint_approved'})}\n\n"
    
    Frontend receives:
    {"type": "checkpoint_approved", "checkpoint": 1}
    [Modal closes]
    
    # ← Loop tries to continue here

Step 25: Get Next Item from Generator
  simple_chatbox.py:1325 (loop continues)
  
  for item in iteration_generator:
    # Loop calls: item = next(iteration_generator)
    # Expects orchestrator to resume and yield next event
    
    ❌ PROBLEM HERE:
    Orchestrator's generator is suspended at line 447:
    
    yield {...}  # Checkpoint yield
    # ← Generator was suspended here
    # ← No code to handle approval status
    # ← When resumed, execution continues to line 457
    # ← But line 457+ has no checkpoint approval logic
    
    The generator just ends without yielding anything else!
    StopIteration is raised
    Loop exits unexpectedly


WHAT SHOULD HAPPEN (BUT DOESN'T)
═════════════════════════════════

After checkpoint yield (orchestrator.py:447), code should be:

  if iteration_mgr.should_checkpoint():
    yield checkpoint
    
    # NEW: Check if user approved
    if not session_manager.was_checkpoint_approved(session_id, checkpoint_num):
      break  # User rejected, stop planning
    
    # If approved, while loop continues to next iteration
  
  # Line 461+: Check if final iteration
  if iteration_mgr.at_final_iteration():
    break

Then orchestrator continues:
- Iteration 3 runs
- Iteration 4 runs
- Loop ends (max_iterations reached)
- Orchestrator yields final_plan

Then SSE handler receives:
  {"type": "final_plan", "plan": "..."}
  
And sends to frontend:
  final_plan event
  
Frontend displays:
  [Plan Display]


CURRENT BROKEN BEHAVIOR
═══════════════════════

Step 25b: Generator Ends Unexpectedly
  for item in iteration_generator:
    # item = next(...) raises StopIteration
    # Loop exits
  
  # Line 1332+: Falls through without yielding final_plan
  # Or yields incomplete/empty final_plan

Frontend receives:
  Nothing (or timeout)
  [Spinner spinning forever]
  [No plan displayed]
  [User confused]

```

---

## Checkpoint Approval Mechanism Diagram

### How It Works (Should Be)

```
┌────────────────────────────────────────────────────────────────┐
│                 CHECKPOINT APPROVAL QUEUE                      │
│                                                                │
│  PlanningSession.checkpoint_approval_queue = queue.Queue(1)  │
│                                                                │
│  Thread 1: SSE Handler (simple_chatbox.py)                    │
│  ────────────────────────────────────────────────────         │
│    |                                                           │
│    v                                                           │
│  approval_received = wait_for_checkpoint_approval()           │
│    |                                                           │
│    v (BLOCKS HERE)                                            │
│  session.checkpoint_approval_queue.get(timeout=3600)          │
│    |                                                           │
│    | Waiting for message from another thread...               │
│    |                                                           │
│    └─────────────────────┐                                    │
│                          │                                    │
│                          │                                    │
│  Thread 2: Approval Handler (/api/checkpoint-approval)       │
│  ────────────────────────────────────────────────────────     │
│                          │                                    │
│                          v                                    │
│                   set_checkpoint_approved(True)               │
│                          │                                    │
│                          v (UNBLOCKS Thread 1)               │
│        session.checkpoint_approval_queue.put(True)            │
│                          │                                    │
│                          v                                    │
│                   Return {"status": "success"}                │
│                                                                │
│                          │                                    │
│                          v                                    │
│  Thread 1 Resumes: approval_received = True                   │
│  approval_gates.py:413                                        │
│    |                                                           │
│    v                                                           │
│  return True                                                  │
│                                                                │
│  SSE Handler continues (simple_chatbox.py:1321)               │
│  yield checkpoint_approved                                    │
│  Loop tries to get next item from orchestrator                │
│    |                                                           │
│    ❌ Orchestrator doesn't know approval happened!            │
│    ❌ No mechanism to tell it to continue                     │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### What's Missing

```
The orchestrator generator needs feedback:

Current (Broken):
  orchestrator.run_iterative_planning()
    └─ yield checkpoint
    └─ [Suspended - no way to know approval status]
    └─ [Can't continue]

Should Be:
  orchestrator.run_iterative_planning(session=session)
    └─ yield checkpoint
    └─ [Check approval] session.was_checkpoint_approved(num)?
    └─ [If No] break
    └─ [If Yes] continue to next iteration
    └─ [Eventually] yield final_plan
```

---

## Session State Timeline

```
Timeline of Session State Changes
═════════════════════════════════

T0: Request arrives
  /api/plan (max_iterations=4)
  session_manager.get_or_create(session_id)
  session.proposal_data = {}
  session.checkpoint_approval_queue = empty

T1: Proposal Generated
  simple_chatbox.py:951
  session.proposal_data = {
    "goal": "...",
    "max_iterations": 4,        ← STORED
    "checkpoint_interval": 2,   ← STORED
    ...
  }

T2: User Approves Proposal
  /api/approve (decision="approve")
  max_iterations = session.proposal_data["max_iterations"]
  checkpoint_interval = session.proposal_data["checkpoint_interval"]
  [Values retrieved from session ✓]

T3: Iteration 2 Complete, Checkpoint Reached
  simple_orchestrator.py:447
  yield checkpoint event
  [Waiting for approval...]

T4: User Clicks Approve
  /api/checkpoint-approval (decision="approve")
  approved = True
  
  ❌ MISSING: Record approval in session
  session.checkpoint_approvals[1] = True
  
  session.checkpoint_approval_queue.put(True)
  [Queue has approval message ✓]

T5: SSE Handler Unblocks
  approval_gates.py:412
  approval_received = session.checkpoint_approval_queue.get()
  # Returns True
  approval_received = True
  
  ❌ MISSING: Orchestrator doesn't know!
  ❌ Need: Some way for orchestrator to check approval

T6: SSE Handler Continues
  simple_chatbox.py:1325
  for item in iteration_generator:
    # Expects next item from orchestrator
    
    ❌ Orchestrator is suspended at checkpoint yield
    ❌ Doesn't know approval happened
    ❌ Has no code to check session for approval status
    ❌ Generator ends without continuing

T7: What Should Happen
  ✓ Orchestrator checks: was_checkpoint_approved(session_id, 1)?
  ✓ Returns True
  ✓ while loop continues
  ✓ Iteration 3 runs
  ✓ Eventually final_plan yielded
  ✓ SSE handler receives and sends to frontend
  ✓ Frontend displays plan
```

---

## Method Call Stack

### Single-Iteration Call Stack

```
simple_chatbox.py (/api/plan)
  └─ start_planning()
     └─ _execute_single_iteration_planning()
        └─ SimpleOrchestrator.run_enhanced_learning_loop()
           └─ for iteration in range(1, 2):
              ├─ ContextBuilder.retrieve_context()
              ├─ WorkflowCoordinator.run_workflow()
              │  ├─ PlannerAgent.run()
              │  ├─ VerifierAgent.run()
              │  ├─ ExecutorAgent.run()
              │  └─ GeneratorAgent.run()
              └─ yield {"type": "final_plan"}
        └─ return PlanResponse()
```

### Multi-Iteration Call Stack (With Bug)

```
simple_chatbox.py (/api/plan)
  └─ start_planning()
     └─ _generate_planning_proposal()
        └─ ProposalResponse()

[User Approves]

simple_chatbox.py (/api/approve)
  └─ handle_approval()
     └─ _execute_multi_iteration_planning()
        └─ SimpleOrchestrator.run_iterative_planning()
           └─ while iteration_mgr.current_iteration < max:
              ├─ ContextBuilder.retrieve_context()
              ├─ WorkflowCoordinator.run_workflow()
              │  ├─ PlannerAgent.run()
              │  ├─ VerifierAgent.run()
              │  ├─ ExecutorAgent.run()
              │  └─ GeneratorAgent.run()
              └─ if should_checkpoint():
                 └─ yield {"type": "checkpoint"}
                    ❌ STOPS HERE - generator suspended

simple_chatbox.py (/api/execute-plan - SSE handler)
  └─ event_stream()
     └─ for item in iteration_generator:
        └─ if item["type"] == "checkpoint":
           ├─ yield checkpoint_data
           ├─ wait_for_checkpoint_approval()
           │  [BLOCKS until approval]
           └─ [Unblocks on approval]
              ├─ yield checkpoint_approved
              └─ for item in iteration_generator:
                 ❌ STUCK: Generator doesn't resume
                 ❌ StopIteration raised
                 ❌ Loop exits unexpectedly

[NEVER REACHED]

simple_orchestrator.py (Continuation of run_iterative_planning)
  ❌ After checkpoint yield - would continue to next iteration
  ❌ But orchestrator doesn't know approval happened!
  ❌ No mechanism to check session for approval status!
```

---

## Summary: Where the Flows Diverge

```
SINGLE-ITERATION vs MULTI-ITERATION DIVERGENCE
═══════════════════════════════════════════════

Common Entry:  /api/plan endpoint (simple_chatbox.py:404)
                    |
        ____________|____________
       |                         |
  DIVERGENCE POINT:
  if request.max_iterations == 1
       |                         |
    YES                         NO
       |                         |
       v                         v
  run_enhanced_          _generate_planning
  learning_loop()        _proposal()
   (lines 145)            (lines 735)
       |                         |
       v                         v
  [Single method]      [Proposal → User → Approval]
       |                         |
       v                         v
  Auto-approve      run_iterative_planning()
  (line 175)            (lines 261)
       |                         |
       v                         v
  yield final_plan   CHECKPOINT HANDLING
  (line 212)            |
       |                |
       v                v
  PlanResponse    wait_for_approval()
  ✅ WORKS         └─ ❌ BROKEN
                      Generator doesn't resume
```

