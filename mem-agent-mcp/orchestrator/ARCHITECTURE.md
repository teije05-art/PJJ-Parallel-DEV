# Architecture: Learning Orchestrator Loop

Complete technical breakdown of how the system works.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LEARNING ORCHESTRATOR LOOP                    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                    Iteration N                          │    │
│  │                                                          │    │
│  │  Step 1: Retrieve Context                               │    │
│  │    ↓                                                     │    │
│  │  Step 2: Generate Plan with CoT                         │    │
│  │    ↓                                                     │    │
│  │  Step 3: Validate with MemAgent                         │    │
│  │    ↓                                                     │    │
│  │  Step 4: Human Approval                                 │    │
│  │    ↓                                                     │    │
│  │  Step 5: Execute Plan                                   │    │
│  │    ↓                                                     │    │
│  │  Step 6: Write to Memory (LEARNING!)                    │    │
│  │    ↓                                                     │    │
│  │  Iteration N+1 (with MORE context)                      │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Orchestrator (Python Script)

**File**: `orchestrator.py`  
**Class**: `LearningOrchestrator`  
**Resources**: ~500MB RAM, 0 VRAM  

**Key Methods**:
- `run_learning_loop(goal)`: Main entry point
- `_retrieve_context()`: Gets learned patterns from memory
- `_generate_plan_with_cot()`: Calls Llama with structured prompt
- `_validate_plan()`: Uses MemAgent as validator
- `_get_human_approval()`: Interactive approval workflow
- `_write_success_to_memory()`: Accumulates learned context
- `_write_failure_to_memory()`: Learns from mistakes

### 2. Llama 3.3 70B (Planning Engine)

**Backend**: Fireworks API (Mac) or vLLM (H100)  
**Resources**: 
- Mac: 0 VRAM (API calls)
- H100: 80GB (already allocated) + 1-2GB temporary per call  

**What It Does**:
- Generates plans using chain-of-thought reasoning
- Learns via in-context examples (not weight updates)
- Sees accumulated context from memory
- Gets progressively better with more iterations

**Example Input** (Iteration 1):
```
GOAL: Implement orchestrator

LEARNED CONTEXT:
Current status: MCP running, orchestrator not exists
Successful patterns: (empty - first iteration)
Errors to avoid: (empty)
...
```

**Example Input** (Iteration 5):
```
GOAL: Implement orchestrator

LEARNED CONTEXT:
Current status: Phase 2 complete
Successful patterns:
  - Pattern 1: Directory setup works well
  - Pattern 2: Test before deploy
  - Pattern 3: Check KPMG procedures
  - Pattern 4: Validate preconditions
Errors to avoid:
  - Error 1: Skipping tests (rejected in iteration 3)
...
```

**Notice**: Iteration 5 has MUCH more context!

### 3. MemAgent (Validator & Memory)

**Backend**: Markdown files in `memory/entities/`  
**Resources**: ~1GB disk space  

**Two Roles**:

#### Role A: Validator (like VAL in paper)
Checks each plan against:
- Project status
- Preconditions
- KPMG procedures
- Dependencies
- Past patterns

#### Role B: Memory Store (where learning lives)
Stores three types of memory:

**`execution_log.md`**: Successful iterations
```markdown
## Iteration 1 - SUCCESS ✅
**Plan**: Create directory → Implement code
**Reasoning**: s0 → a1 → s1 → a2 → s2
**Outcome**: Completed successfully

## Iteration 2 - SUCCESS ✅
**Plan**: Configure testing → Run tests
**Reasoning**: Used Pattern 1 from iteration 1
**Outcome**: Completed successfully
```

**`successful_patterns.md`**: Proven approaches
```markdown
### Pattern 1: Infrastructure Setup
**Approach**: Create directory → Implement code
**Success rate**: 100% (used 3 times)
**When to use**: Setting up new components

### Pattern 2: Testing Workflow  
**Approach**: Configure → Test → Validate
**Success rate**: 100% (used 2 times)
**When to use**: Quality assurance phase
```

**`planning_errors.md`**: Mistakes to avoid
```markdown
### Error 1: Skip Testing
**Plan**: Deploy directly without testing
**Issue**: Violates KPMG procedures
**User feedback**: "Always test first"
**Lesson**: Include testing in all deployment plans
```

### 4. Human (Training Signal)

**Interface**: Terminal (interactive prompts)  
**Resources**: Human time ⏰  

**Decisions**:
- **Approve (y)**: Tells system "this approach works"
- **Reject (n)**: Tells system "avoid this approach"  
- **Edit**: Provides corrective guidance

**Impact**: Each decision becomes training data!

## Data Flow

### Iteration 1 (Cold Start)

```
┌──────────────────────────────────────────────────────────┐
│ STEP 1: Retrieve Context                                 │
├──────────────────────────────────────────────────────────┤
│ execution_log.md      → "No history yet"                 │
│ successful_patterns.md → "No patterns yet"               │
│ planning_errors.md    → "No errors yet"                  │
│ projectjupiter*.md    → "H100 ready, orchestrator needed"│
│                                                           │
│ Context Size: ~500 chars                                 │
└──────────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 2: Generate Plan                                    │
├──────────────────────────────────────────────────────────┤
│ Llama input: Goal + 500 chars context                    │
│ Llama output: Plan with CoT reasoning                    │
│                                                           │
│ [STATE s0] MCP running, orchestrator not exists          │
│ [ACTION a1] Create directory                             │
│ [STATE s1] Directory exists                              │
│ [ACTION a2] Implement code                               │
│ [STATE s2] Code exists                                   │
│                                                           │
│ Plan Size: ~1200 chars                                   │
└──────────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 3: Validate                                         │
├──────────────────────────────────────────────────────────┤
│ MemAgent checks:                                         │
│   ✓ MCP running?          → Yes                          │
│   ✓ Write permissions?    → Yes                          │
│   ✓ KPMG violations?      → No                           │
│   ✓ Preconditions met?    → Yes                          │
│                                                           │
│ Result: VALID ✅                                          │
└──────────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 4: Human Approval                                   │
├──────────────────────────────────────────────────────────┤
│ User sees: Plan + Validation                             │
│ User decides: y (approve)                                │
│                                                           │
│ Decision: APPROVED ✅                                     │
└──────────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 5: Execute                                          │
├──────────────────────────────────────────────────────────┤
│ Action 1: Create directory  → ✅                          │
│ Action 2: Implement code    → ✅                          │
│                                                           │
│ Result: SUCCESS ✅                                        │
└──────────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 6: Write to Memory (LEARNING!)                     │
├──────────────────────────────────────────────────────────┤
│ execution_log.md      ← Add iteration 1 success          │
│ successful_patterns.md ← Add "infrastructure setup"      │
│                                                           │
│ Memory grew by: ~400 chars                               │
│ Total context now: ~900 chars                            │
└──────────────────────────────────────────────────────────┘
```

### Iteration 2 (Learning Kicks In!)

```
┌──────────────────────────────────────────────────────────┐
│ STEP 1: Retrieve Context                                 │
├──────────────────────────────────────────────────────────┤
│ execution_log.md      → "Iteration 1: SUCCESS"           │
│ successful_patterns.md → "Pattern: directory → code"     │
│ planning_errors.md    → "No errors yet"                  │
│ projectjupiter*.md    → "Orchestrator exists, test next" │
│                                                           │
│ Context Size: ~900 chars ← MORE THAN ITERATION 1!        │
└──────────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 2: Generate Plan (Now Informed!)                   │
├──────────────────────────────────────────────────────────┤
│ Llama input: Goal + 900 chars context                    │
│              ↑                                            │
│              Includes learned pattern from iteration 1!  │
│                                                           │
│ Llama uses learned pattern:                              │
│   "Infrastructure setup: directory → code worked"        │
│   → Apply same pattern to testing phase                  │
│                                                           │
│ [STATE s0] Orchestrator exists (learned this!)           │
│ [ACTION a1] Create test directory (uses pattern!)        │
│ [STATE s1] Test dir exists                               │
│ [ACTION a2] Implement tests (follows pattern!)           │
│ [STATE s2] Tests implemented                             │
│                                                           │
│ Plan is BETTER because it learned from iteration 1! 🎯   │
└──────────────────────────────────────────────────────────┘
```

## Learning Mechanism

### Traditional Fine-Tuning (Paper's Approach)
```
Training Phase (30 hours, 40GB VRAM):
  Input: Domain + Problem + Feedback
  Process: Backpropagation → Update weights
  Output: Specialized model

Inference Phase:
  Input: New problem
  Output: Plan (from learned weights)
```

### Our Approach (In-Context Learning)
```
No Training Phase! ✅

Inference Phase (immediate, 1-2GB VRAM):
  Input: Goal + Memory context
  Process: Llama sees examples in prompt
  Output: Plan informed by examples

Memory accumulation:
  Iteration 1: 500 chars context
  Iteration 2: 900 chars context
  Iteration 5: 2000 chars context
  Iteration 10: 4000 chars context
  
Learning happens in context, not weights!
```

## Resource Usage

### Mac (Fireworks API)

| Component | VRAM | RAM | Disk |
|-----------|------|-----|------|
| Orchestrator | 0 GB | 0.5 GB | - |
| Llama (API) | 0 GB | - | - |
| MemAgent | 0 GB | - | 1 GB |
| **Total** | **0 GB** | **0.5 GB** | **1 GB** |

💰 **Cost**: Fireworks API calls (~$0.20 per 1M tokens)

### H100 Instance (vLLM)

| Component | VRAM | RAM | Disk |
|-----------|------|-----|------|
| Orchestrator | 0 GB | 0.5 GB | - |
| vLLM (running) | 80 GB | - | - |
| Inference calls | +1-2 GB (temporary) | - | - |
| MemAgent | 0 GB | - | 1 GB |
| **Peak Total** | **81-82 GB / 90 GB** | **0.5 GB** | **1 GB** |

✅ **Fits comfortably!**

## Iteration Timeline

### What Happens Each Iteration

```
Iteration 1 (Cold Start):
  Time: ~2-3 minutes
  Context: 500 chars (minimal)
  Plan quality: Basic
  Learning: Establishes baseline
  
Iteration 2 (First Learning):
  Time: ~2-3 minutes
  Context: 900 chars (growing!)
  Plan quality: Improved
  Learning: Uses iteration 1 pattern
  
Iteration 5 (Getting Smart):
  Time: ~2-3 minutes
  Context: 2000 chars (rich!)
  Plan quality: Good
  Learning: Multiple proven patterns
  
Iteration 10 (Expert):
  Time: ~2-3 minutes
  Context: 4000 chars (expert level!)
  Plan quality: Excellent
  Learning: Sophisticated understanding
  
Iteration 15 (Mastery):
  Time: ~2-3 minutes
  Context: 6000+ chars (comprehensive!)
  Plan quality: Exceptional
  Learning: Rarely needs corrections
```

## Comparison to Paper

| Aspect | Paper (PDDL-INSTRUCT) | Our System |
|--------|----------------------|------------|
| Learning Method | Fine-tuning | In-context learning |
| Training Time | 30 hours | 0 (immediate) |
| VRAM for Training | 48 GB | 0 GB |
| VRAM for Inference | ~8 GB | 1-2 GB (temporary) |
| Where Learning Lives | Model weights | Memory files |
| Validation | VAL (PDDL validator) | MemAgent |
| Human Feedback | None (automated) | Yes (approval loop) |
| Domain | PDDL planning | Project Jupiter |
| Performance Gain | 28% → 94% accuracy | Progressive improvement |
| Iterations (η) | 10-15 (training loops) | 10-15 (inference loops) |

## Why This Works

### 1. Large Context Window
Llama 3.3 has ~128K token context:
- Can see ALL past successes
- Can see ALL past failures
- Can see current project state
- Still has room for reasoning

### 2. Chain-of-Thought
Forces explicit reasoning:
- Must check preconditions
- Must track state changes
- Must validate effects
- Can't skip logical steps

### 3. External Validation
MemAgent provides ground truth:
- Like VAL in the paper
- Checks against real project state
- Verifies KPMG procedures
- Prevents hallucination

### 4. Human Signal
User approval is training data:
- Approve → System learns "do this"
- Reject → System learns "avoid this"
- Edit → System gets corrective guidance

### 5. Cumulative Memory
Each iteration adds context:
- Successful patterns accumulate
- Error patterns accumulate
- Understanding deepens
- Plans improve

## Extending The System

### Add New Validation Rules
```python
def _validate_plan(self, plan):
    # Existing checks...
    
    # Add custom check
    security_check = self.agent.chat(f"""
        Does this plan have security implications?
        {plan['text']}
    """)
    
    validation['security'] = security_check
    return validation
```

### Add New Memory Types
```python
# Create new memory entity
performance_metrics = memory / "entities" / "performance_metrics.md"

# Track plan execution time, resource usage, etc.
```

### Customize CoT Prompting
```python
def _generate_plan_with_cot(self, goal, context):
    # Modify prompt structure
    # Add domain-specific reasoning steps
    # Include custom constraints
```

## Next: Testing

Ready to test? See `QUICKSTART.md`!

```bash
cd /Users/teije/Desktop/memagent/mem-agent-mcp/orchestrator
python orchestrator.py
```

The system is ready to learn! 🚀

