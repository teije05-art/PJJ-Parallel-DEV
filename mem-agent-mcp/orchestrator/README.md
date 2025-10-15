# Project Jupiter Learning Orchestrator

PDDL-INSTRUCT-inspired planning system adapted for inference-only learning.

## 🎯 **Two Ways to Use**

### **1. Claude Desktop (Recommended - User Friendly!)**
Talk naturally to Claude to approve/reject plans:
```
"Start a planning iteration for deploying orchestrator"
"Approve this plan"
"Reject because it skips testing"
```
**See:** `CLAUDE_USAGE.md`

### **2. Terminal (Developer Mode)**
Direct command-line interface:
```bash
python orchestrator.py
```
**See:** `QUICKSTART.md`

Both use the same learning system!

---

## Overview

This orchestrator implements the MIT paper's approach to teaching LLMs to plan, but adapted for inference-only (no fine-tuning needed). Learning happens through:

1. **Chain-of-thought reasoning**: Explicit state-action-state transitions
2. **Validation feedback**: MemAgent validates each step like VAL in the paper
3. **Human approval**: User feedback provides training signal (via Claude or terminal)
4. **Memory accumulation**: Each iteration adds learned context

## How It Works

```
ITERATION 1: Minimal context
  ↓
Generate plan with CoT → Validate with MemAgent → Get human approval
  ↓
Write to memory (execution_log.md, successful_patterns.md)
  ↓
ITERATION 2: Now has learned context!
  ↓
Generate BETTER plan (learns from iteration 1) → Validate → Approve
  ↓
More memory accumulation
  ↓
ITERATION N: System is now expert at planning!
```

## Resource Requirements

### Mac (Fireworks):
- **VRAM**: 0 GB (uses API)
- **RAM**: ~500 MB (orchestrator script)
- **Cost**: Fireworks API calls

### H100 Instance (vLLM):
- **VRAM**: 1-2 GB temporary per inference call
- **Total**: 80 GB (existing) + 1-2 GB (orchestrator) = 81-82 GB / 90 GB ✅
- **RAM**: ~500 MB (orchestrator script)

## Quick Start

### 1. Run on Mac (Testing)

```bash
cd /Users/teije/Desktop/memagent/mem-agent-mcp/orchestrator
python orchestrator.py
```

### 2. Run on H100 Instance (Production)

```bash
# Copy to instance
scp -r orchestrator/ user@h100-instance:/path/to/mem-agent-mcp/

# Run on instance
cd /path/to/mem-agent-mcp/orchestrator
python orchestrator.py
```

The script auto-detects backend:
- **macOS**: Uses Fireworks
- **Linux**: Uses vLLM

## Example Session

```
🚀 Project Jupiter Learning Orchestrator
================================================================================
This system uses PDDL-INSTRUCT-inspired learning
Gets smarter with each iteration through memory accumulation
================================================================================

🎯 Enter planning goal: Implement orchestrator infrastructure

================================================================================
🔄 ITERATION 1/15
================================================================================

📚 STEP 1: Retrieving context from memory...
   ✓ Current status retrieved
   ✓ Successful patterns: 42 chars (first iteration)
   ✓ Errors to avoid: 38 chars (no failures yet)

🧠 STEP 2: Generating plan with chain-of-thought reasoning...
   ✓ Plan generated (1250 chars)
   ✓ Used learned context from memory

✅ STEP 3: Validating plan with MemAgent...
   ✅ Plan is VALID
   ✓ Preconditions checked
   ✓ Conflicts checked

================================================================================
🔔 ITERATION 1: APPROVAL REQUIRED
================================================================================

📋 PROPOSED PLAN:
[STATE s0]
Current: MCP running, orchestrator not exists
...
[ACTION] Create directory structure
...

✅ MEMAGENT VALIDATION:
✅ VALID - All checks passed

💡 OPTIONS:
  y     - Approve and execute plan
  n     - Reject plan (will learn from this)
  edit  - Provide corrective feedback

👉 Your decision (y/n/edit): y

⚙️  STEP 5: Executing plan...
   ⏳ Executing actions...
   ✓ Action 1 completed
   ✓ Action 2 completed

💾 STEP 6: Writing success to memory (learning!)...
   ✅ Execution log updated
   ✅ Successful patterns recorded
   ✅ Memory enriched with learned context

✅ Plan approved and executed successfully!
   Memory updated with learned context.

🔁 Continue to next planning cycle? (y/n): y

================================================================================
🔄 ITERATION 2/15
================================================================================

📚 STEP 1: Retrieving context from memory...
   ✓ Successful patterns: 420 chars (learned from iteration 1!)
   ...
```

## Memory Files

The orchestrator creates/updates these memory entities:

### `entities/execution_log.md`
Tracks all successful iterations. Next iterations retrieve this as learned context.

```markdown
## Iteration 1 - SUCCESS ✅
**Goal:** Implement orchestrator
**Plan:** Create directory → Implement code
**Outcome:** Successfully executed
```

### `entities/successful_patterns.md`
Proven approaches that work well.

```markdown
### Pattern 1
**Approach:** Infrastructure setup (directory → code)
**Result:** SUCCESS ✅
**Learning:** This approach works, follow it
```

### `entities/planning_errors.md`
Mistakes to avoid (from rejected plans).

```markdown
### Error 1 - REJECTED ❌
**Plan:** Deploy without testing
**Issue:** Violates KPMG procedures
**Lesson:** Always include testing phase
```

## Key Differences from Paper

| **Paper (Fine-Tuning)** | **Our System (Inference)** |
|-------------------------|----------------------------|
| Updates model weights | Updates memory context |
| Requires 40GB+ VRAM | Requires 1-2GB temporary |
| 30 hours training | Runs immediately |
| Specialized model | General model + memory |
| Learning in weights | Learning in context |

## Learning Process

### Iteration 1 (Cold Start)
- **Context**: Minimal (just project status)
- **Planning**: Basic approach
- **Outcome**: May need corrections

### Iteration 5 (Warming Up)
- **Context**: 4 successful patterns + error patterns
- **Planning**: Uses proven approaches
- **Outcome**: Higher success rate

### Iteration 15 (Expert)
- **Context**: 10+ successful patterns + known errors
- **Planning**: Sophisticated, avoids pitfalls
- **Outcome**: Consistently good plans

## Customization

### Change Max Iterations

```python
orchestrator = LearningOrchestrator(
    memory_path=memory_path,
    max_iterations=20  # Default: 15 (η in paper)
)
```

### Custom Goal

```python
orchestrator.run_learning_loop(
    goal="Your custom planning goal here"
)
```

## Architecture

```
┌─────────────────────────────────────┐
│  Orchestrator Loop (Python script)  │
│  Resource: ~500MB RAM               │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Llama 3.3 70B (Already running)   │
│  Mac: Fireworks API                 │
│  H100: vLLM (80GB)                  │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  MemAgent Memory (Markdown files)   │
│  - execution_log.md                 │
│  - successful_patterns.md           │
│  - planning_errors.md               │
│  THIS IS WHERE LEARNING HAPPENS!    │
└─────────────────────────────────────┘
```

## Troubleshooting

### "Agent not found" error
Make sure you're in the `mem-agent-mcp/orchestrator/` directory and the parent directory has the `agent` module.

### "Memory path not found" error
Create a `.memory_path` file in `mem-agent-mcp/` with your memory directory path.

### High memory usage on H100
Each inference call uses 1-2GB temporarily. If you're hitting limits, reduce batch size or wait between calls.

## Next Steps

1. Test locally on Mac with Fireworks
2. Verify memory accumulation works
3. Run 5-10 iterations to build learned context
4. Transfer to H100 instance
5. Run production planning sessions

## Paper Reference

Based on: "Teaching LLMs to Plan: Logical Chain-of-Thought Instruction Tuning for Symbolic Planning" (Verma et al., MIT CSAIL)

Key adaptations:
- Inference-only (no fine-tuning)
- Memory-based learning (no weight updates)
- Human-in-the-loop approval
- Domain-specific (Project Jupiter)

