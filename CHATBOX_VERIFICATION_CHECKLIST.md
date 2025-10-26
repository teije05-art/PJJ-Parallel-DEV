# ✅ Chatbox Verification Checklist

Use this checklist to verify the chatbox implementation is working correctly.

---

## Pre-Flight Checks

### Environment Setup
- [ ] Python 3.11+ installed (`python --version`)
- [ ] `uv` package manager installed (`uv --version`)
- [ ] Repository cloned/available at: `/Users/teije/Desktop/memagent-modular-fixed`
- [ ] Memory path configured (`cat mem-agent-mcp/.memory_path`)

### Dependencies
- [ ] `make install` completed successfully
- [ ] No missing dependencies reported
- [ ] Model (MLX/vLLM) available and working

---

## File Verification

### New Files Created
- [ ] `simple_chatbox.py` exists (1032 lines)
- [ ] `CHATBOX_GUIDE.md` exists (comprehensive guide)
- [ ] `CHATBOX_QUICKREF.md` exists (quick reference)
- [ ] `CHATBOX_IMPLEMENTATION_SUMMARY.md` exists (technical details)
- [ ] `CHATBOX_VERIFICATION_CHECKLIST.md` exists (this file)

### Modified Files
- [ ] `mem-agent-mcp/Makefile` has `serve-chatbox` target
- [ ] `make help` lists `serve-chatbox` as option #11

### Unchanged Files
- [ ] `mcp_server/server.py` still works
- [ ] `orchestrator/simple_orchestrator.py` unchanged
- [ ] `agent/agent.py` unchanged
- [ ] Memory directory structure unchanged

---

## Server Startup Tests

### Step 1: Start Model Server
```bash
cd mem-agent-mcp
make run-agent
```

**Verification:**
- [ ] Command completes without errors
- [ ] Server starts on port 8000
- [ ] "Model loaded" message appears
- [ ] No Python exceptions in output

**For macOS:**
- [ ] LM Studio opens (or already running)
- [ ] Model selected (4-bit/8-bit/bf16)
- [ ] Port 8000 is listening: `lsof -i :8000`

**For Linux:**
- [ ] vLLM starts
- [ ] Port 8000 is listening
- [ ] Model (driaforall/mem-agent) loading

### Step 2: Start Chatbox (New Terminal)
```bash
cd mem-agent-mcp
make serve-chatbox
```

**Verification:**
- [ ] Command completes without errors
- [ ] Message appears: "Starting server on: http://localhost:9000"
- [ ] Port 9000 is listening: `lsof -i :9000`
- [ ] No Python exceptions in output
- [ ] Status indicators show:
  - [ ] ✅ MEM AGENT - ENHANCED CHATBOX INTERFACE
  - [ ] ✅ Backend: Fireworks AI (macOS) or vLLM (Linux)
  - [ ] ✅ Memory: /path/to/memory
  - [ ] ✅ Orchestrator: ✅ Available

---

## Browser Tests

### Connection Test
- [ ] Open http://localhost:9000 in browser
- [ ] Page loads without errors
- [ ] No "Connection refused" messages
- [ ] UI renders properly (no CSS errors)
- [ ] Logo visible: "Project Jupiter Planner"

### Status Check
- [ ] Sidebar shows system status
- [ ] Backend: ✅ (Fireworks or vLLM)
- [ ] Agent: ✅
- [ ] Planning: ✅
- [ ] Sessions: 1

### Mode Switching
- [ ] Click "💬 Chat" button
  - [ ] Becomes active (blue highlight)
  - [ ] Input placeholder changes to "Ask me anything..."
  - [ ] Empty state shows correct message
- [ ] Click "🎯 Plan" button
  - [ ] Becomes active (blue highlight)
  - [ ] Planning options appear on left
  - [ ] Input placeholder changes to "Describe your planning goal..."
  - [ ] Empty state shows correct message

---

## Chat Mode Tests

### Simple Chat
- [ ] Click 💬 Chat mode
- [ ] Type: "Hello"
- [ ] Click Send or press Enter
- [ ] Agent responds (may take 30-60s)
- [ ] Response appears in chat
- [ ] Formatting looks correct
- [ ] Message thread is visible

### Memory-Based Chat
- [ ] Ask: "What is in my memory?"
- [ ] Agent gives relevant response (based on actual entities)
- [ ] Response uses memory content
- [ ] Not generic response

### Multi-Turn Conversation
- [ ] Ask: "Tell me about your capabilities"
- [ ] Follow-up: "Can you plan for me?"
- [ ] Follow-up: "How long does planning take?"
- [ ] Conversation maintains context
- [ ] All responses are coherent

### Error Handling
- [ ] Try very long input (500+ characters)
- [ ] Try special characters: 😀🎯→✅
- [ ] Try empty input (nothing sent)
- [ ] System handles gracefully

---

## Planning Mode Tests

### Basic Planning (3 Iterations)
- [ ] Click 🎯 Plan mode
- [ ] Set Max Iterations to 3
- [ ] Type: "Create a simple marketing plan"
- [ ] Click Send
- [ ] Wait for completion (~3-5 minutes)
- [ ] See completion message in browser
- [ ] Shows: "✅ Planning completed in XXs"
- [ ] Shows: "Iterations: 3/3"

**Check Memory Files:**
```bash
ls -la ~/.../local-memory/plans/
cat ~/.../local-memory/plans/iteration_001_full_details.md
```
- [ ] File `iteration_001_full_details.md` exists
- [ ] File has full content (thousands of lines)
- [ ] Contains: Planner output
- [ ] Contains: Verifier output
- [ ] Contains: Executor output
- [ ] Contains: Generator output

### Medium Planning (9 Iterations)
- [ ] Set Max Iterations to 9
- [ ] Type: "Develop a market entry strategy for healthcare in Vietnam"
- [ ] Click Send
- [ ] Wait for completion (~10-15 minutes)
- [ ] Observe progress in browser
- [ ] Browser stays responsive
- [ ] No errors in console

**Check Memory:**
```bash
ls -la ~/.../local-memory/plans/iteration_*
wc -l ~/.../local-memory/plans/iteration_*/full_details.md
```
- [ ] Multiple iteration files exist
- [ ] Each file has substantial content
- [ ] Latest file is: `iteration_009_full_details.md`

### Long Planning (Full Iteration)
- [ ] Set Max Iterations to your desired number (e.g., 9)
- [ ] Describe a complex goal
- [ ] Monitor all 4 steps
- [ ] System doesn't crash
- [ ] Browser stays usable
- [ ] Can see results in memory

---

## Feature Tests

### Unicode/Emoji Support
- [ ] All emoji display correctly in browser
  - [ ] 🎯 Goal emoji
  - [ ] ✅ Success checkmark
  - [ ] ❌ Error X
  - [ ] 🔄 Rotation arrow
  - [ ] → Right arrow
  - [ ] 💬 Chat bubble
  - [ ] 🧭 Compass
  - [ ] ✍️ Writing hand

### Session Persistence
- [ ] Start chat
- [ ] Type: "Remember this is session 1"
- [ ] Refresh browser (Cmd+R)
- [ ] Session ID maintained (localStorage)
- [ ] Can continue conversation
- [ ] Chat history visible

### Multiple Sessions
- [ ] Open two browser tabs
- [ ] Both show different session IDs
- [ ] Both can chat independently
- [ ] Both share same memory
- [ ] No interference between tabs

### Status Updates
- [ ] Sidebar status updates periodically
- [ ] Sessions counter reflects open sessions
- [ ] Backend status stays ✅

---

## Edge Case Tests

### Long Input
- [ ] Paste 1000 character goal
- [ ] System processes without truncation
- [ ] Planning works with long goal

### Special Characters
- [ ] Use goal with quotes: "Market's \"premium\" strategy"
- [ ] Use unicode: "市场进入 (Market Entry) in Vietnam"
- [ ] Use emojis in goal: "🚀 Rocket strategy 🎯"
- [ ] All process correctly

### Network Issues
- [ ] Stop model server mid-planning
- [ ] Chat request should timeout/error
- [ ] Error message appears in browser
- [ ] System doesn't crash
- [ ] Can restart and continue

### Browser Issues
- [ ] Close browser mid-planning
- [ ] Model server continues running
- [ ] Planning completes in background
- [ ] Results saved to memory
- [ ] Can reopen browser and see memory

---

## Memory System Tests

### Execution Log
```bash
cat ~/.../local-memory/entities/execution_log.md
```
- [ ] File exists
- [ ] Contains recent execution records
- [ ] Shows planning iterations
- [ ] Has timestamps

### Successful Patterns
```bash
cat ~/.../local-memory/entities/successful_patterns.md
```
- [ ] File exists
- [ ] Contains learned patterns
- [ ] Gets updated after each iteration
- [ ] Patterns are meaningful

### Planning Errors
```bash
cat ~/.../local-memory/entities/planning_errors.md
```
- [ ] File exists
- [ ] Contains error records (even if empty initially)
- [ ] Gets updated on planning failures
- [ ] Format is markdown

### Agent Performance
```bash
cat ~/.../local-memory/entities/agent_performance.md
```
- [ ] File exists
- [ ] Contains agent metrics
- [ ] Shows success rates
- [ ] Updates after planning

---

## Performance Tests

### Startup Time
- [ ] Chatbox starts in <10 seconds
- [ ] Model server ready in ~30 seconds
- [ ] Browser loads in <2 seconds

### Response Time
- [ ] Chat responses: 30-120 seconds
- [ ] Status API: <500ms
- [ ] Browser UI: <100ms response to clicks

### Planning Iteration Time
- [ ] Each iteration: 40-140 seconds
- [ ] Context retrieval: 5-15s
- [ ] 4-agent workflow: 30-120s
- [ ] Storage & learning: 1-2s

### Long-Running Stability
- [ ] 9+ iteration planning completes
- [ ] No memory leaks (memory stays ~same)
- [ ] No CPU spinning (stays responsive)
- [ ] Browser doesn't slow down

---

## Compatibility Tests

### With MCP Server
- [ ] MCP server still works: `make serve-mcp`
- [ ] Chatbox still works: `make serve-chatbox`
- [ ] Both use same memory
- [ ] Results in memory accessible to both

### With CLI
- [ ] Chat CLI still works: `make chat-cli`
- [ ] Same memory accessible
- [ ] No interference between interfaces

### With Memory Connectors
- [ ] Memory imports still work
- [ ] `make memory-wizard` works
- [ ] Imported data accessible in chatbox

---

## Documentation Tests

### Chatbox Guide
- [ ] `CHATBOX_GUIDE.md` is readable
- [ ] Contains all needed information
- [ ] Examples are accurate
- [ ] Troubleshooting section helps

### Quick Reference
- [ ] `CHATBOX_QUICKREF.md` is concise
- [ ] Keyboard shortcuts work
- [ ] Terminal commands work
- [ ] Examples run successfully

### Implementation Summary
- [ ] `CHATBOX_IMPLEMENTATION_SUMMARY.md` is clear
- [ ] Technical details are accurate
- [ ] Architecture diagram makes sense
- [ ] Endpoints documented correctly

---

## Cleanup & Troubleshooting

### Before Testing
- [ ] Clear browser cache (Cmd+Shift+Delete)
- [ ] Close all previous instances
- [ ] Fresh model server start

### If Tests Fail

**Chatbox won't start:**
1. [ ] Check port 9000 not in use: `lsof -i :9000`
2. [ ] Kill if needed: `kill -9 <PID>`
3. [ ] Check model server running
4. [ ] Check Python errors in terminal

**Browser won't connect:**
1. [ ] Check port 9000 listening: `lsof -i :9000`
2. [ ] Start model server: `make run-agent`
3. [ ] Try fresh browser tab
4. [ ] Try different browser

**Planning hangs:**
1. [ ] Check internet (web search needs it)
2. [ ] Check model server responsive
3. [ ] Check free disk space
4. [ ] Reduce iterations and try again

**Memory files not created:**
1. [ ] Check memory path: `cat mem-agent-mcp/.memory_path`
2. [ ] Directory readable/writable: `ls -la ~/.../local-memory`
3. [ ] Disk space available
4. [ ] Check terminal for errors

---

## Final Validation

### Success Criteria - ALL MUST BE ✅

```
✅ Browser loads at http://localhost:9000
✅ Chat mode works (responds in 30-120s)
✅ Planning mode works (9 iterations complete)
✅ All emoji render correctly
✅ Memory files created automatically
✅ No errors in browser console
✅ No errors in terminal output
✅ Status shows all ✅ (backend, agent, planning)
✅ Multiple sessions work independently
✅ Can switch modes without issues
✅ Planning results saved to memory
✅ System stable for 20+ minute test
```

### Sign-Off

If all tests pass above, the chatbox implementation is **production-ready** ✅

**Tested By**: _________________
**Date**: _________________
**Notes**:

---

## Post-Verification

### Next Steps
1. [ ] Create first planning iteration (3 iterations)
2. [ ] Review results in memory
3. [ ] Create second planning iteration (9 iterations)
4. [ ] Observe learning improvements
5. [ ] Share with team/users
6. [ ] Gather feedback

### Maintenance
- [ ] Monitor memory directory size
- [ ] Clean old iterations if needed
- [ ] Keep model server running
- [ ] Document any issues

### Future Improvements
- [ ] Add streaming responses
- [ ] Add plan editing UI
- [ ] Add export to PDF
- [ ] Add team collaboration
- [ ] Add authentication

---

**Congratulations! 🎉 Chatbox implementation verified!**

Your autonomous planning system is now ready for production use!
