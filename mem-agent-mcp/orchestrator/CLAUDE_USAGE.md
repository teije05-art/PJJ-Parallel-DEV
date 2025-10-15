# Using the Orchestrator in Claude Desktop

The orchestrator is now integrated into your existing MCP server! Just talk to Claude naturally.

## 🎯 **No New Server Needed!**

The orchestrator tools are added to your **existing** `mcp_server/server.py`:
- ✅ Same server Claude already connects to
- ✅ Just restart Claude Desktop
- ✅ No new configuration needed
- ✅ Works alongside existing `use_memory_agent` tool

---

## 💬 **Example Conversation**

### **Starting a Planning Iteration**

```
You: Start a planning iteration for deploying the orchestrator to the H100 instance

Claude: 🔄 Let me start a new planning iteration...

[Claude uses start_planning_iteration tool]

🔄 ITERATION 1 - PLAN GENERATED

📋 PROPOSED PLAN:
────────────────────────────────────────────────────────────────────────────
[PLAN SUMMARY]
Deploy orchestrator infrastructure to H100 instance and configure for production.

[STATE s0]
Current state:
  - Orchestrator: tested locally on Mac
  - H100 instance: vLLM running with Llama 3.3 70B
  - Deployment: not configured
  - SSH access: available

[STEP 1] Transfer orchestrator files to H100
State: s0
Action: scp orchestrator/ to H100 instance
Preconditions:
  ✓ Local testing complete (from previous iteration)
  ✓ SSH credentials configured
  ✓ H100 instance accessible
Effects:
  + Orchestrator code on H100
  + Can import orchestrator module
Next state: s1

[STATE s1]
  - Orchestrator: files on H100
  - Can run orchestrator

[STEP 2] Configure for vLLM backend
State: s1
Action: Update orchestrator to use vLLM (already auto-detects)
Preconditions:
  ✓ Orchestrator files present (from s1)
  ✓ vLLM operational
Effects:
  + Auto-detects Linux platform
  + Uses vLLM instead of Fireworks
Next state: s2

[STATE s2]
  - Orchestrator: configured for H100
  - Ready for production use
────────────────────────────────────────────────────────────────────────────

✅ VALIDATION RESULTS:
────────────────────────────────────────────────────────────────────────────
Status: ✅ VALID

Precondition Check:
All preconditions satisfied. Local testing completed in previous iteration.
H100 instance accessible and vLLM operational. SSH access confirmed...

Conflict Check:
No conflicts with KPMG procedures. Deployment follows standard protocols...
────────────────────────────────────────────────────────────────────────────

💡 NEXT STEPS:
To approve this plan, say: "Approve the plan" or use approve_current_plan()
To reject this plan, say: "Reject because [reason]" or use reject_current_plan(reason)
To see learning progress, use view_learning_summary()

What would you like to do?
```

---

### **Approving the Plan**

```
You: Approve the plan

Claude: ✅ Approving and executing the plan...

[Claude uses approve_current_plan tool]

✅ PLAN APPROVED & EXECUTED

⚙️ Execution Results:
- Status: SUCCESS
- Actions completed: 2
- Timestamp: 2025-10-10T15:30:00

💾 Memory Updated (Learning!):
- ✅ Execution log updated
- ✅ Successful patterns recorded
- ✅ Next iteration will use this learned context

🎉 Iteration 1 complete!

The system has now learned from this successful deployment. 
The next iteration will be smarter!

Would you like to:
- Start another planning iteration?
- View what the system has learned?
- Continue with a different task?
```

---

### **Rejecting a Plan**

```
You: Start planning for skipping tests and deploying directly

Claude: 🔄 Starting iteration 2...

[Shows plan that skips testing phase]

📋 PROPOSED PLAN:
...
[STEP 1] Deploy directly to production
...

You: Reject this plan because it skips testing, which violates our procedures

Claude: ❌ Rejecting the plan with your feedback...

[Claude uses reject_current_plan tool]

❌ PLAN REJECTED

📝 Your Feedback: it skips testing, which violates our procedures

💾 Memory Updated (Learning from Mistake!):
- ✅ Error pattern recorded
- ✅ System will avoid this approach in future iterations
- ✅ Next iteration will have better understanding

🔄 Ready for next iteration!

The system has learned to avoid skipping testing. Future plans 
will always include proper testing phases!

Want to start a new iteration with this learned context?
```

---

### **⭐ Autonomous Mode (NEW! - For Large-Scale Learning)**

```
You: Start autonomous planning for Project Jupiter with 50 iterations, checkpoint every 10

Claude: 🤖 STARTING SEMI-AUTONOMOUS PLANNING

Goal: Project Jupiter
Target iterations: 50
Checkpoint interval: Every 10 iterations

The system will now run autonomously, pausing for your review at checkpoints.
Building up learned context progressively... 🧠

✅ Iteration 1: Auto-approved (valid)
✅ Iteration 2: Auto-approved (valid)
✅ Iteration 3: Auto-approved (valid)
✅ Iteration 4: Auto-approved (valid)
✅ Iteration 5: Auto-approved (valid)
✅ Iteration 6: Auto-approved (valid)
✅ Iteration 7: Auto-approved (valid)
✅ Iteration 8: Auto-approved (valid)
✅ Iteration 9: Auto-approved (valid)

🛑 CHECKPOINT at Iteration 10/50

Progress so far:
- Completed: 9 iterations
- Successful: 9
- Success rate: 100%

Current plan: [shows checkpoint plan]
Validation: ✅ VALID

OPTIONS:
1. To continue autonomously: use continue_autonomous_planning()
2. To approve current plan and continue: use approve_current_plan()
3. To stop autonomous mode: use stop_autonomous_planning()

What would you like to do?

You: Continue autonomously

Claude: 🔄 RESUMING AUTONOMOUS PLANNING

✅ Iterations 11-19 complete

🛑 CHECKPOINT at Iteration 20/50
...

[Continues until all 50 iterations complete]

🎉 AUTONOMOUS PLANNING COMPLETE!

Total iterations: 50
Successful: 50
Success rate: 100%

💾 Memory enriched with 50 iterations of learned context!

The system is now significantly smarter!
```

**Why use autonomous mode?**
- ✅ Build 50, 100, or 1000 iterations quickly
- ✅ Only review at checkpoints (every 5-10 iterations)
- ✅ 90% less human time required
- ✅ Massive context accumulation
- ✅ Perfect for overnight runs

**See:** `AUTONOMOUS_MODE.md` for full guide!

---

### **Viewing Learning Progress**

```
You: Show me what the system has learned

Claude: Let me check the learning summary...

[Claude uses view_learning_summary tool]

📊 LEARNING SUMMARY

Iterations Completed: 5
Successful Plans: 4
Rejected Plans: 1
Success Rate: 80.0%

📚 Learned Patterns:
### Pattern 1: Infrastructure Setup
### Pattern 2: Testing Workflow
### Pattern 3: Deployment Procedure
### Pattern 4: Configuration Management

❌ Known Errors to Avoid: 1
- Error: Skipping testing (violates procedures)

💡 The system gets smarter with each iteration!
Context accumulates in memory/entities/:
  - execution_log.md (successful iterations)
  - successful_patterns.md (proven approaches)
  - planning_errors.md (mistakes to avoid)

The system now has 4 proven patterns it will follow and 1 mistake 
it knows to avoid. Each new iteration benefits from this learning!
```

---

## 🔧 **Setup Instructions**

### **1. Restart Your Existing MCP Server**

The orchestrator tools are now part of your existing server!

```bash
# If running standalone
cd /Users/teije/Desktop/memagent/mem-agent-mcp
make serve-mcp

# Your Claude Desktop config already points to this server
# Just restart Claude Desktop to pick up the new tools
```

### **2. Restart Claude Desktop**

- Quit Claude Desktop completely
- Reopen Claude Desktop
- The new orchestrator tools are now available!

### **3. Verify Tools Are Available**

```
You: What tools do you have available?

Claude: I have access to:
- use_memory_agent (existing)
- start_planning_iteration (new!)
- approve_current_plan (new!)
- reject_current_plan (new!)
- view_learning_summary (new!)
```

---

## 🎯 **Natural Language Commands**

Claude understands these naturally:

**Starting iterations:**
- "Start a planning iteration for [goal]"
- "Begin planning for [task]"
- "Let's plan how to [goal]"

**Approving:**
- "Approve this plan"
- "Yes, execute this"
- "Looks good, proceed"

**Rejecting:**
- "Reject because [reason]"
- "No, this approach [problem]"
- "I don't approve - [feedback]"

**Viewing progress:**
- "Show me what the system learned"
- "What patterns have been identified?"
- "Display learning summary"

---

## 📊 **What Happens Behind The Scenes**

### **Iteration 1:**
```
You → Claude → start_planning_iteration tool
          ↓
    Retrieves minimal context (first time)
          ↓
    Llama generates plan with CoT
          ↓
    MemAgent validates
          ↓
    Claude shows you the plan
          ↓
You approve → approve_current_plan tool
          ↓
    Executes plan
          ↓
    Writes to memory (LEARNING!)
```

### **Iteration 2:**
```
You → Claude → start_planning_iteration tool
          ↓
    Retrieves ENRICHED context (learned from iter 1!)
          ↓
    Llama generates BETTER plan
          ↓
    Uses learned patterns
          ↓
    Claude shows improved plan
```

**The system gets smarter each time!** 🧠

---

## ✨ **Benefits**

### **User-Friendly:**
- ✅ Natural conversation (no technical commands)
- ✅ Claude explains everything clearly
- ✅ Anyone can approve/reject plans
- ✅ No terminal needed

### **Same Learning:**
- ✅ Memory accumulation (learns from successes)
- ✅ Error avoidance (learns from rejections)
- ✅ Chain-of-thought reasoning
- ✅ Progressive improvement

### **Same Infrastructure:**
- ✅ Uses existing MCP server
- ✅ No new server to configure
- ✅ Already connected to Claude
- ✅ Same memory system

---

## 🚀 **Getting Started**

1. **Restart Claude Desktop** (picks up new tools)

2. **Start your first iteration:**
   ```
   "Start a planning iteration for setting up the orchestrator"
   ```

3. **Review the plan** Claude shows you

4. **Approve or reject:**
   ```
   "Approve this plan"
   or
   "Reject because [your reason]"
   ```

5. **Continue learning:**
   ```
   "Start another iteration for [next goal]"
   ```

Each iteration makes the system smarter! 🎉

---

## 🔄 **Workflow Comparison**

### **Terminal Version:**
```
$ python orchestrator.py
Enter goal: [type goal]
[Shows plan]
Decision (y/n): y
```
❌ Technical, requires terminal access

### **Claude Version:**
```
You: Start planning for deploying orchestrator
Claude: [Shows plan]
You: Approve this
Claude: ✅ Done!
```
✅ Natural, anyone can use it!

---

## 💡 **Pro Tips**

1. **Be Specific in Rejections**
   - Good: "Reject because this skips testing, which is required by KPMG procedures"
   - Bad: "Reject because I don't like it"
   - Your feedback trains the system!

2. **Check Learning Progress**
   - Every few iterations, ask: "Show me what the system learned"
   - See how patterns accumulate

3. **Iterate Multiple Times**
   - The system gets smarter with more iterations
   - Try 5-10 iterations to see real improvement

4. **Use Both Tools**
   - Orchestrator for planning
   - `use_memory_agent` for querying memory
   - They work together!

---

## 🎉 **That's It!**

No new servers, no complex setup. Just talk to Claude naturally and approve/reject plans. The system learns from your decisions and gets progressively smarter!

Ready to test? Just restart Claude Desktop and say:

**"Start a planning iteration for Project Jupiter"**

