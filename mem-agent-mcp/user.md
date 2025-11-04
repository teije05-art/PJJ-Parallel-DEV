# Project Jupiter: Developer Context

## Project Overview

**Project Jupiter** is a semi-autonomous AI planning system implementing three peer-reviewed research frameworks:

1. **MemAgent** (ByteDance/Tsinghua, 2507.02259v1) - Fixed-length segment-based memory
2. **PDDL-INSTRUCT** (2509.13351v1) - Logical reasoning chains with formal verification
3. **Flow-GRPO** (AgentFlow, lupantech) - Reinforcement learning for agent coordination

The system generates comprehensive strategic plans (3000+ words) for complex domains with human approval gates and continuous self-improvement.

---

## Current Development Status

**Health: 9/10 - Documentation-First Phase (Nov 3, 2025)**

### Completed (Phases 0-6)
- ✅ Core 4-agent architecture (Planner → Verifier → Executor → Generator)
- ✅ Session management with queue-based approvals
- ✅ SSE real-time progress streaming
- ✅ 31-module modular structure (no monolithic regressions)
- ✅ Phase 6: Complete documentation with research framework alignment
  - ✅ `RESEARCH_FRAMEWORK_ALIGNMENT.md` created
  - ✅ `CLAUDE.md` updated with MemAgent, PDDL, Flow-GRPO sections
  - ✅ Integration loop architecture documented
  - ✅ Implementation phase map created

### In Progress (Phases 1-5)
- **Phase 1** (Days 1-2): MemAgent memory system (segment-based, bounded)
- **Phase 2** (Days 3-4): PDDL-INSTRUCT logical reasoning (verification feedback)
- **Phase 3** (Days 5-6): Flow-GRPO training signals (pattern learning)
- **Phase 4** (Days 7-8): Integration loop (memory ↔ reasoning ↔ learning)
- **Phase 5** (Days 9-10): Testing & validation (zero regressions)

**Frontend Work**: DEFERRED until backend perfect

---

## Architecture at a Glance

```
User Input (Web or MCP)
    ↓
Session Management (approval_gates.py)
    ├─ SegmentedMemory (Phase 1 - MemAgent)
    ├─ reasoning_chains (Phase 2 - PDDL)
    └─ pattern_scores (Phase 3 - Flow-GRPO)
    ↓
Context Retrieval (orchestrator/context/)
    ├─ Goal analysis
    ├─ Memory retrieval (semantic via MemAgent)
    ├─ Web search (7 angles, 11 patterns)
    └─ Entity context (planning history)
    ↓
4-Agent Workflow (orchestrator/agents/)
    ├─ Planner: Strategic planning with PDDL preconditions
    ├─ Verifier: Verification feedback on reasoning
    ├─ Executor: Implementation breakdown
    └─ Generator: 3000+ word synthesis
    ↓
Learning System (orchestrator/learning/)
    ├─ Flow-GRPO scoring (verification × approval)
    ├─ Pattern effectiveness tracking
    ├─ Agent coordination learning
    └─ Memory importance scoring
    ↓
Output & Storage
    ├─ Checkpoint approval gates (human-in-loop)
    ├─ Plan storage (local-memory/plans/)
    ├─ Pattern storage (successful_patterns.md)
    └─ Error tracking (planning_errors.md)
```

---

## Key Modules & Their Purpose

### Core Orchestration
- **`simple_chatbox.py`** (1,488 lines) - Web server + end-to-end pipeline
  - FastAPI with SSE streaming
  - Session management
  - Integrated planning loop

### Memory Management (Phase 1)
- **`orchestrator/memory/memagent_memory.py`** (NEW) - SegmentedMemory class
  - Fixed-length memory (12 segments max)
  - Semantic search retrieval
  - Compression for old segments
  - RL-trained overwrite scores

### Reasoning & Verification (Phase 2)
- **`orchestrator/reasoning/logical_planner.py`** (NEW) - Logical prompts
- **`orchestrator/reasoning/verification_feedback.py`** (NEW) - VAL-style verification
  - Precondition checking
  - Effect verification
  - Detailed feedback generation

### Learning & Coordination (Phase 3)
- **`orchestrator/learning/flow_grpo_trainer.py`** (NEW) - Flow-GRPO training
- **`orchestrator/learning/agent_coordination.py`** (NEW) - Agent pair scoring
- **`orchestrator/learning_analyzer.py`** (ENHANCED) - Mid-iteration signals
- **`orchestrator/pattern_recommender.py`** (ENHANCED) - Flow-score tracking

### Agent System
- **`orchestrator/agents/base_agent.py`** - AgentResult interface
- **`orchestrator/agents/planner_agent.py`** - Strategic planning with PDDL
- **`orchestrator/agents/verifier_agent.py`** - Verification & feedback
- **`orchestrator/agents/executor_agent.py`** - Action breakdown
- **`orchestrator/agents/generator_agent.py`** - Final synthesis

### Context Retrieval
- **`orchestrator/context/context_builder.py`** - Orchestrates all providers
- **`orchestrator/context/memory_context.py`** - MemAgent semantic search
- **`orchestrator/context/goal_context.py`** - Goal analysis
- **`orchestrator/context/search_context.py`** - Web research (7 angles)

### Backend Integration
- **`llama_planner.py`** (1,112 lines) - MemAgent wrapper
  - Semantic search operations
  - Memory delta extraction
  - Segment importance estimation

---

## Development Philosophy

### Quality Over Speed
- Deep thinking before coding
- Research-first architecture
- Comprehensive documentation before implementation
- Measurable success criteria for each phase

### Backend-First Approach
- Perfect the planning engine (Phases 1-5)
- ONLY then touch the frontend (deferred)
- Ensures backend reliability independent of UI

### Research-Backed Implementation
- All code maps to peer-reviewed papers
- See `RESEARCH_FRAMEWORK_ALIGNMENT.md` for detailed mappings
- Clear "why" for every architectural decision

### Backward Compatibility
- No breaking changes to existing APIs
- Old code continues to work
- New features opt-in where possible

---

## Critical Data Structures

### PlanningSession (approval_gates.py)

```python
class PlanningSession:
    # Memory system (Phase 1)
    memory_manager: SegmentedMemory  # Fixed 12 segments, bounded growth

    # Reasoning chains (Phase 2)
    reasoning_chains: Dict[int, List[str]]  # iteration → reasoning steps
    verification_feedback: Dict[int, Dict]  # iteration → feedback results

    # Learning signals (Phase 3)
    iteration_signals: Dict[int, Dict]  # iteration → flow_score, approval
    pattern_scores: Dict[str, float]  # pattern_name → effectiveness
    agent_selection_weights: Dict[str, float]  # agent_name → weight

    # Session state
    proposal_data: Dict  # Approved parameters
    generated_plan: str  # Final plan output
    plan_metadata: Dict  # Frameworks, iterations, checkpoints
```

### Iteration Signal (Phase 3)

```python
iteration_signal = {
    'iteration': 1,
    'agent_name': 'planner',
    'flow_score': 0.82,  # 0-1, based on verification + approval
    'verification_feedback': {
        'precondition_1': True,
        'precondition_2': True,
        'effect_1': True,
    },
    'user_approved': True,
    'reasoning_quality': 0.89,  # Quality of reasoning chain
    'timestamp': '2025-11-03T...'
}
```

---

## Integration Loop (The Heart of the System)

Each planning iteration executes this complete loop:

```
ITERATION N EXECUTION FLOW:

1. LOAD MEMORY
   memory_segments = session.memory_manager.get_relevant_segments(goal)
   → Retrieves top-3 segments via semantic search

2. GET PATTERNS
   patterns = recommender.get_patterns_for_next_iteration()
   → Returns top-3 patterns by effectiveness (Flow-GRPO scores)

3. RETRIEVE CONTEXT
   context = context_builder.build(goal, entities, memory_segments, patterns)
   → Enriched with market research, entity info, recommended patterns

4. RUN AGENTS
   planner_result = planner.run(context)  # with reasoning chain + PDDL
   verifier_result = verifier.run(planner_result.content)
   executor_result = executor.run(verifier_result.content)
   generator_result = generator.run((executor_result.content, context))

   → Each agent returns: (content, reasoning_chain, verification_feedback)

5. SCORE ITERATION
   flow_score = calculate_flow_score(
       verification_quality=verifier_result.verification_accuracy,
       user_approval=user_will_approve,  # predictive until checkpoint
       reasoning_quality=avg(agent_reasoning_quality)
   )

6. SHOW CHECKPOINT
   Display to user:
   - Reasoning chain: "Why did we reach this point?"
   - Verification results: "Which checks passed/failed?"
   - Memory updates: "What will we remember?"
   - Flow score: "How well did this iterate?"

   → User approves or rejects

7. LEARN (on approval)
   memory_manager.train_overwrite_scores(plan_results)
   trainer.record_iteration_signal(flow_score, verification, approval)
   recommender.update_pattern_scores(flow_score, verification, approval)
   coordinator.record_pair_performance(agent_pairs, flow_score)

   → System learns which segments matter, which patterns work, which agents are effective

8. UPDATE MEMORY (on approval)
   memory_delta = extract_memory_delta(iteration_results)
   segment_importance = estimate_importance(memory_delta, user_feedback)
   memory_manager.add_segment(memory_delta, importance=segment_importance)

   → Bounded memory grows with iteration

NEXT ITERATION:
   Use improved memory → use better patterns → get better reasoning
   → Quality improves measurably with each iteration
```

---

## Success Metrics

### For Each Phase
- **Phase 1 (MemAgent)**: Memory bounded at 12 segments, semantic search works, no regression
- **Phase 2 (PDDL)**: Reasoning chains present, verification >80% accurate, no regression
- **Phase 3 (Flow-GRPO)**: Flow scores calculated, patterns improve, agent weights update
- **Phase 4 (Integration)**: Loop executes smoothly, memory updates on approval, quality improves
- **Phase 5 (Testing)**: 22/22 baseline tests pass, new tests pass, performance acceptable

### Overall Project Success
✅ Backend perfectly implements three research frameworks
✅ Memory ↔ Reasoning ↔ Learning loop is closed and functional
✅ Quality improves measurably over iterations
✅ Zero regressions in existing functionality
✅ Users understand system's decision-making (full reasoning transparency)

---

## Key Relationships to Files

**For Understanding MemAgent (Phase 1):**
- See: `RESEARCH_FRAMEWORK_ALIGNMENT.md` (MemAgent section)
- See: `CLAUDE.md` (MemAgent Integration section)
- Implementation: `orchestrator/memory/memagent_memory.py`
- Integration: `approval_gates.py` (PlanningSession.memory_manager)

**For Understanding PDDL (Phase 2):**
- See: `RESEARCH_FRAMEWORK_ALIGNMENT.md` (PDDL-INSTRUCT section)
- See: `CLAUDE.md` (PDDL-INSTRUCT section)
- Implementation: `orchestrator/reasoning/`
- Integration: `orchestrator/agents/` and `orchestrator/workflow_coordinator.py`

**For Understanding Flow-GRPO (Phase 3):**
- See: `RESEARCH_FRAMEWORK_ALIGNMENT.md` (Flow-GRPO section)
- See: `CLAUDE.md` (Flow-GRPO Training section)
- Implementation: `orchestrator/learning/flow_grpo_trainer.py`, `agent_coordination.py`
- Integration: `orchestrator/learning_analyzer.py`, `pattern_recommender.py`

**For Integration Loop (Phase 4):**
- See: `CLAUDE.md` (Integration Loop section)
- Implementation: `orchestrator/integration/planning_loop.py`
- Integration: `simple_chatbox.py` (main execution flow)

**For Testing (Phase 5):**
- See: `tests/test_baseline.py` (existing 22 tests)
- New: `tests/test_memagent_integration.py`
- New: `tests/test_logical_reasoning.py`
- New: `tests/test_flow_grpo.py`
- New: `tests/test_integrated_loop.py`

---

## When Something Breaks

1. **Check the research docs**: `RESEARCH_FRAMEWORK_ALIGNMENT.md` explains WHY we do things
2. **Check CLAUDE.md**: Has detailed implementation sections for each framework
3. **Check tests**: Run `make test` to ensure no regressions
4. **Check phase requirements**: Each phase has specific success criteria
5. **Check data flow**: Trace through the Integration Loop section above

---

## Next Immediate Steps

1. ✅ Phase 6 Documentation Complete (RESEARCH_FRAMEWORK_ALIGNMENT.md, CLAUDE.md updates, user.md updated)
2. 🔄 Phase 1: Implement SegmentedMemory (orchestrator/memory/memagent_memory.py)
3. 🔄 Phase 2: Implement LogicalPlanningPrompt & VerificationFeedback
4. 🔄 Phase 3: Implement FlowGRPOTrainer & AgentCoordination
5. 🔄 Phase 4: Create IntegratedPlanningLoop & wire everything together
6. 🔄 Phase 5: Write comprehensive tests, ensure zero regressions
7. ⏸️ Phase 6+: Frontend work (DEFERRED - do NOT touch UI until backend perfect)

---

## Philosophy Quote

*"Quality over quantity. We have all week. Think deeply about each change. Backend first, frontend later. Research-backed. One integrated loop."*

The system is not done when it runs. It's done when it's elegant, well-documented, research-grounded, and perfectly implements three peer-reviewed frameworks in service of semi-autonomous planning with human oversight.

