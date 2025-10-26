# MemAgent-Modular System: Quick Reference Guide

## System Architecture at a Glance

```
MAIN LOOP: SimpleOrchestrator
├─ Iteration Loop (max 15 iterations)
│
├─ Step 1: CONTEXT RETRIEVAL
│  └─ ContextManager
│     ├─ GoalAnalyzer (detect domain, industry, market)
│     ├─ Retrieve memory entities (dynamic selection)
│     └─ Web search (DuckDuckGo, SerpAPI, or Brave)
│
├─ Step 2: AGENT WORKFLOW
│  └─ WorkflowCoordinator
│     └─ AgentCoordinator
│        ├─ Step 2a: 🧭 PlannerAgent
│        │  ├─ Analyze goal → Determine domain/template
│        │  ├─ Retrieve context (domain-specific)
│        │  ├─ Retrieve successful patterns
│        │  ├─ Retrieve error patterns to avoid
│        │  └─ Generate strategic plan
│        │
│        ├─ Step 2b: ✅ VerifierAgent
│        │  ├─ Validate plan against KPMG standards
│        │  ├─ 8-point verification checklist
│        │  └─ Flag as valid/invalid
│        │
│        ├─ Step 2c: 🛠️ ExecutorAgent
│        │  ├─ Execute plan using MemAgent
│        │  ├─ Create real deliverables
│        │  └─ Count phases and deliverables
│        │
│        ├─ Step 2d: ✅ VerifierAgent (again)
│        │  ├─ Validate execution results
│        │  └─ Assess quality (EXCELLENT/GOOD/SATISFACTORY)
│        │
│        └─ Step 2e: ✍️ GeneratorAgent
│           ├─ Integrate all agent outputs
│           ├─ Create final professional deliverables
│           └─ Synthesize results
│
├─ Step 3: HUMAN APPROVAL
│  └─ ApprovalHandler
│     ├─ Display agent results
│     └─ Get decision: y/n/edit/quit
│
├─ Step 4: MEMORY STORAGE (if approved or rejected)
│  └─ MemoryManager
│     ├─ Update execution_log.md (success/failure)
│     ├─ Update successful_patterns.md (if success)
│     ├─ Update planning_errors.md (if failure)
│     ├─ Save plan file
│     ├─ Populate entities
│     └─ Store deliverables
│
├─ Step 5: FLOW-GRPO LEARNING
│  └─ LearningManager
│     ├─ Update planner_training_log.md
│     │  ├─ POSITIVE signal (if approved)
│     │  └─ NEGATIVE signal (if rejected)
│     ├─ Update agent_performance.md
│     ├─ Store user feedback (if provided)
│     └─ Learn for next iteration
│
└─ DECISION:
   ├─ If APPROVED → Return True (exit loop)
   └─ If REJECTED/EDITED → Continue to next iteration
```

## Key Components Summary

### 1. ORCHESTRATOR MODULES (5 independent modules)

| Module | Purpose | Lines | Handles |
|--------|---------|-------|---------|
| **SimpleOrchestrator** | Main coordinator | ~295 | Orchestrates all modules in sequence |
| **ContextManager** | Context retrieval | ~240 | Goal analysis, entity retrieval, web search |
| **WorkflowCoordinator** | Agent workflow | ~68 | Calls AgentCoordinator, returns results |
| **ApprovalHandler** | Human approval | ~128 | Displays results, gets user decision |
| **MemoryManager** | Memory operations | ~292 | Stores results, updates entities, saves plans |
| **LearningManager** | Learning/training | ~162 | Flow-GRPO signals, performance tracking |

### 2. 4-AGENT SYSTEM

| Agent | Role | Key Method | Output |
|-------|------|-----------|--------|
| **🧭 Planner** | Strategic planning | `generate_strategic_plan()` | Multi-phase plan with actions |
| **✅ Verifier** | Quality validation | `verify_plan()` | Validation report + is_valid flag |
| **🛠️ Executor** | Implementation | `execute_plan()` | Actual deliverables + counts |
| **✍️ Generator** | Content synthesis | `synthesize_results()` | Final professional deliverables |

### 3. LEARNING SYSTEM (Flow-GRPO)

```
Iteration Outcome → Training Signal
     ↓
Approved → POSITIVE signal → Planner learns to repeat this approach
Rejected → NEGATIVE signal → Planner learns to avoid this approach
     ↓
Next iteration uses learned patterns
```

**Training Records**:
- `planner_training_log.md` - Flow-GRPO signals and learning
- `successful_patterns.md` - What works (in-context learning)
- `planning_errors.md` - What doesn't work
- `agent_performance.md` - Performance metrics

### 4. DOMAIN TEMPLATES

7 domains with specific templates:
1. **Healthcare** - Clinical dev, regulatory, medical device
2. **Technology** - Agile, lean startup, product-market fit
3. **Manufacturing** - Lean, six sigma, supply chain
4. **Retail** - Consumer behavior, e-commerce, brand
5. **Financial** - Banking, fintech, compliance
6. **QSR** - Restaurant ops, food service, market entry
7. **General** - Fallback for unknown domains

Each template includes:
- Domain-specific methodologies
- Industry considerations
- 3-phase action plan
- Risk mitigation strategies
- Success metrics

### 5. APPROVAL & FEEDBACK

```
User Options:
y     → Approve workflow (store success, apply positive learning)
n     → Reject with reason (store failure, apply negative learning)
edit  → Provide feedback (store feedback, apply corrective learning)
quit  → Stop orchestrator
```

## Data Structures

### AgentResult (used by all agents)
```python
@dataclass
class AgentResult:
    success: bool           # Whether operation succeeded
    output: str            # Detailed output/report
    metadata: Dict         # Domain-specific metadata
    timestamp: str         # ISO format timestamp
```

### ApprovalDecision (from user)
```python
@dataclass
class ApprovalDecision:
    approved: bool         # True if approved
    feedback: str         # User feedback/reason
    action: str           # 'approved', 'rejected', 'edited', 'quit'
```

### GoalAnalysis (from goal analyzer)
```python
@dataclass
class GoalAnalysis:
    domain: str           # e.g., 'healthcare', 'technology'
    industry: str         # e.g., 'pharmaceutical'
    market: str           # e.g., 'vietnam', 'southeast_asia'
    company_type: str     # e.g., 'startup', 'enterprise'
    objectives: List[str] # e.g., ['market entry', 'regulatory approval']
    context_entities: List[str]    # Which memory entities to retrieve
    methodologies: List[str]       # Domain-specific methodologies
    considerations: List[str]      # Key considerations
```

## Memory Structure

```
memory_path/
├── entities/
│   ├── LEARNING ENTITIES
│   │   ├── execution_log.md           (all executions)
│   │   ├── successful_patterns.md     (in-context learning)
│   │   ├── planning_errors.md         (error learning)
│   │   ├── planner_training_log.md    (Flow-GRPO training)
│   │   ├── agent_performance.md       (performance metrics)
│   │   └── agent_coordination.md      (coordination log)
│   │
│   └── CONTENT ENTITIES (populated by agents)
│       ├── executive_summary_report.md
│       ├── detailed_implementation_plan.md
│       ├── risk_assessment_and_mitigation_strategy.md
│       ├── quality_assurance_framework.md
│       ├── timeline_and_resource_allocation.md
│       ├── success_metrics_and_kpis.md
│       └── recommendations_and_next_steps.md
│
├── plans/
│   └── plan_{timestamp}_{goal_slug}.md    (comprehensive plan)
│
└── deliverables/
    └── enhanced_execution_report_{timestamp}.md
```

## Quick Start

```python
from mem_agent_mcp.orchestrator import SimpleOrchestrator

# Initialize
orchestrator = SimpleOrchestrator(
    memory_path="/path/to/memory",
    max_iterations=5
)

# Run learning loop
goal = "Develop healthcare market entry strategy for Vietnam"
success = orchestrator.run_enhanced_learning_loop(goal)

# Results stored automatically in memory
```

## Key Features

✅ **Modular Architecture** - Each module independent and testable
✅ **4-Agent Workflow** - Specialized agents with clear roles
✅ **Flow-GRPO Learning** - Outcomes broadcast back for training
✅ **Web Search Integration** - Real current data in plans
✅ **Domain-Specific Templates** - Tailored to 7+ domains
✅ **Human-in-the-Loop** - User approval and feedback integrated
✅ **Comprehensive Memory** - All results stored and analyzable
✅ **No Cascading Failures** - Modules independent
✅ **Clear Dependencies** - All flow downward, no circular deps
✅ **Extensible Design** - Easy to add domains, agents, modules

## File Map

```
mem-agent-mcp/orchestrator/
├── __init__.py                    (exports: SimpleOrchestrator, Agents)
├── simple_orchestrator.py         (main coordinator ~295 lines)
├── context_manager.py             (context retrieval ~240 lines)
├── workflow_coordinator.py        (agent workflow ~68 lines)
├── agentflow_agents.py           (4 agents + coordinator ~1037 lines)
├── approval_handler.py            (human approval ~128 lines)
├── memory_manager.py              (memory operations ~292 lines)
├── learning_manager.py            (Flow-GRPO learning ~162 lines)
├── goal_analyzer.py               (goal analysis ~380 lines)
├── domain_templates.py            (planning templates ~784 lines)
└── search_module.py               (web search ~180 lines)

TOTAL: ~3,566 lines (highly modular)
```

## Communication Flows

### Context → Planning
```
Goal → Analysis → Template Selection → 
Retrieve Context → Format with web search → 
Planning Prompt → Agent uses it
```

### Agents → Results
```
Planner → Plan → Verifier validates → 
Executor implements → Verifier validates execution → 
Generator synthesizes → Final deliverables
```

### Learning Feedback
```
Approval Decision → Training Signal → 
Memory Updated → Planner Uses Patterns → 
Next Plan Better Informed
```

## Interesting Design Decisions

1. **Single Agent Instance Across Modules**
   - One shared MemAgent for consistency
   - Exposed as `orchestrator.agent_coordinator` for compatibility

2. **Dynamic Context Selection**
   - Goal analyzed to determine relevant entities
   - Not hard-coded to KPMG QSR context
   - Flexible for any domain/goal

3. **Web Search Integration**
   - Falls back gracefully if unavailable
   - Supports 3 different providers
   - Dramatically improves plan quality

4. **Simple Coordinator Pattern**
   - 150 lines instead of 870
   - Just orchestrates modules
   - All business logic delegated

5. **Double Verification**
   - Verifies plan quality BEFORE execution
   - Verifies execution quality AFTER
   - Quality gates throughout

6. **Feedback Learning**
   - User rejections/edits are stored as lessons
   - Contributes to Flow-GRPO training
   - System improves from failures

---

**For complete details, see SYSTEM_ANALYSIS.md**
