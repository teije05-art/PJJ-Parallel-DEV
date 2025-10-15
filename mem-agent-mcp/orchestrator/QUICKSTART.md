# Quick Start Guide

Get the orchestrator running in 5 minutes!

## Step 1: Verify Setup ✅

Check that you have:
- [x] mem-agent-mcp installed and working
- [x] Memory directory configured (`.memory_path` file)
- [x] Fireworks API key (Mac) or vLLM running (H100)

## Step 2: Run Your First Iteration 🚀

```bash
cd /Users/teije/Desktop/memagent/mem-agent-mcp/orchestrator
python orchestrator.py
```

You'll see:
```
🚀 Project Jupiter Learning Orchestrator
================================================================================
This system uses PDDL-INSTRUCT-inspired learning
Gets smarter with each iteration through memory accumulation
================================================================================

🎯 Enter planning goal (or press Enter for default):
```

**Press Enter** to use the default goal, or type your own!

## Step 3: Watch It Work 👀

### Iteration 1 starts with minimal context:

```
================================================================================
🔄 ITERATION 1/15
================================================================================

📚 STEP 1: Retrieving context from memory...
   ✓ Current status retrieved
   ✓ Successful patterns: 42 chars (first iteration - minimal!)
   ✓ Errors to avoid: 38 chars (no failures yet)
```

### Llama generates a plan:

```
🧠 STEP 2: Generating plan with chain-of-thought reasoning...
   ✓ Plan generated (1250 chars)
   ✓ Used learned context from memory
```

### MemAgent validates it:

```
✅ STEP 3: Validating plan with MemAgent...
   ✅ Plan is VALID
   ✓ Preconditions checked
   ✓ Conflicts checked
```

### You review and approve:

```
================================================================================
🔔 ITERATION 1: APPROVAL REQUIRED
================================================================================

📋 PROPOSED PLAN:
[Full plan with reasoning shown here]

✅ MEMAGENT VALIDATION:
✅ VALID - All checks passed

💡 OPTIONS:
  y     - Approve and execute plan
  n     - Reject plan (will learn from this)
  edit  - Provide corrective feedback

👉 Your decision (y/n/edit): 
```

**Type `y`** to approve!

### Memory gets updated (learning happens!):

```
💾 STEP 6: Writing success to memory (learning!)...
   ✅ Execution log updated
   ✅ Successful patterns recorded
   ✅ Memory enriched with learned context

✅ Plan approved and executed successfully!
   Memory updated with learned context.
```

## Step 4: Continue to Iteration 2 🔄

```
🔁 Continue to next planning cycle? (y/n): y
```

**Type `y`** to continue!

### Now watch the magic! 🪄

Iteration 2 starts with MORE context:

```
================================================================================
🔄 ITERATION 2/15
================================================================================

📚 STEP 1: Retrieving context from memory...
   ✓ Current status retrieved
   ✓ Successful patterns: 420 chars (learned from iteration 1!)  ← MORE CONTEXT!
   ✓ Errors to avoid: 38 chars
   ✓ Execution history: 280 chars (sees what worked!)            ← LEARNING!
```

**The plan will be better** because Llama now sees:
- What worked in iteration 1
- Proven successful patterns
- How to structure good plans

## Step 5: See The Learning 📊

After a few iterations, check what was learned:

```bash
# See successful plans
cat /Users/teije/Desktop/memagent/local-memory/entities/execution_log.md

# See learned patterns
cat /Users/teije/Desktop/memagent/local-memory/entities/successful_patterns.md

# See errors to avoid (if you rejected any)
cat /Users/teije/Desktop/memagent/local-memory/entities/planning_errors.md
```

## Example Session Output

Here's what a full iteration looks like:

```
================================================================================
🔄 ITERATION 3/15
================================================================================

📚 STEP 1: Retrieving context from memory...
   ✓ Current status retrieved
   ✓ Successful patterns: 820 chars
   ✓ Errors to avoid: 38 chars
   ✓ Execution history: 650 chars

🧠 STEP 2: Generating plan with chain-of-thought reasoning...

[PLAN SUMMARY]
Based on successful patterns from previous iterations, implement testing phase.

[STATE s0]
Initial state:
  - Orchestrator code: exists (from iteration 1)
  - Testing framework: not configured
  - Sample entities: exist

[STEP 1]
State: s0
Action: Configure testing environment
Preconditions:
  ✓ Orchestrator code exists
  ✓ Memory path accessible
  ✓ Sample entities available
Effects:
  + Test configuration created
  + Can run test suite
Next state: s1

[STATE s1]
Resulting state:
  - Orchestrator code: exists
  - Testing framework: configured
  - Can execute tests

[STEP 2]
State: s1
Action: Run validation tests
Preconditions:
  ✓ Test framework configured (from s1)
  ✓ Orchestrator functional
Effects:
  + Test results available
  + System validated
Next state: s2

[GOAL ACHIEVEMENT]
Goal: "Develop and test orchestrator"
Current state s2:
  ✓ Orchestrator exists
  ✓ Testing complete
  ✓ System validated
Status: ACHIEVED ✅

✅ STEP 3: Validating plan with MemAgent...
   ✅ Plan is VALID
   ✓ Preconditions checked
   ✓ Conflicts checked

================================================================================
🔔 ITERATION 3: APPROVAL REQUIRED
================================================================================

👉 Your decision (y/n/edit): y

⚙️  STEP 5: Executing plan...
   ✓ Action 1 completed
   ✓ Action 2 completed

💾 STEP 6: Writing success to memory (learning!)...
   ✅ Execution log updated
   ✅ Successful patterns recorded

✅ Plan approved and executed successfully!

🔁 Continue to next planning cycle? (y/n): n

================================================================================
🏁 Learning loop completed after 3 iterations
================================================================================

📊 LEARNING SUMMARY
================================================================================
Total iterations: 3
Successful plans: 3
Rejected plans: 0
Success rate: 100.0%

📚 Learned context now available for future iterations:
   - 3 successful patterns recorded
   - 0 error patterns to avoid
   - Memory enriched for next planning session
================================================================================
```

## Tips 💡

### Start Small
Run 3-5 iterations first to build basic learned context.

### Review Plans Carefully
Your approval/rejection is training data! The system learns from your decisions.

### Reject Bad Plans
Don't worry about rejecting - it teaches the system what NOT to do!

### Use the Edit Option
If a plan is close but needs tweaks, use "edit" to provide guidance.

### Check Memory Files
After each session, check the memory files to see what was learned.

## Common Workflows

### Quick Test (3 iterations)
```bash
python orchestrator.py
# Enter goal or use default
# Run 3 iterations: y, y, y, n
```

### Full Learning Session (10+ iterations)
```bash
python orchestrator.py
# Let it run through multiple cycles
# System gets progressively smarter
```

### View Learning Progress
```bash
python example_usage.py
# Choose option 3: Show learning progression
```

## Next Steps

1. ✅ Run your first 3-5 iterations
2. ✅ Check memory files to see learned context
3. ✅ Try rejecting a plan to see error learning
4. ✅ Run more iterations and watch plans improve
5. ✅ Transfer to H100 instance when ready

## Troubleshooting

### "ModuleNotFoundError: No module named 'agent'"
→ Make sure you're running from `orchestrator/` directory

### "Memory path not found"
→ Create `.memory_path` file in `mem-agent-mcp/` with your memory path

### Plans aren't improving
→ Need more iterations! Try 10-15 to build substantial context

### Fireworks API errors
→ Check your API key is configured correctly

## What's Happening Behind The Scenes

1. **Iteration 1**: Cold start, minimal context
   - Llama has basic project info
   - Generates reasonable but basic plan

2. **Iteration 2**: Warming up
   - Sees iteration 1's success
   - Uses proven pattern
   - Plan is more structured

3. **Iteration 5**: Getting smart
   - Has 4 successful examples
   - Knows what works
   - Avoids past mistakes

4. **Iteration 10+**: Expert level
   - Rich learned context
   - Sophisticated planning
   - Rarely needs corrections

This is **in-context learning** - no fine-tuning needed!

## Ready to Start? 🚀

```bash
cd /Users/teije/Desktop/memagent/mem-agent-mcp/orchestrator
python orchestrator.py
```

**Just press Enter** when prompted for a goal to use the default!

Type `y` to approve plans, `n` to reject, or `edit` to provide feedback.

The system gets smarter with each iteration! 🧠

