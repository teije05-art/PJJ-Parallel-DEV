# 🚀 Project Jupiter Planner - Chatbox Interface Guide

## Overview

The **Chatbox Interface** is a web-based alternative to Claude Desktop's MCP integration. It provides better support for:
- **Autonomous planning loops** (no broken-pipe errors)
- **Rich emoji and Unicode rendering** (browser-native)
- **Multi-iteration planning** with memory learning
- **Zero MCP protocol overhead**

## Quick Start

### 1. Start the Model Server
```bash
cd mem-agent-mcp
make run-agent
```
Select your preferred precision (4-bit recommended for speed, 8-bit for quality).

### 2. Start the Chatbox
In a **new terminal**:
```bash
cd mem-agent-mcp
make serve-chatbox
```

### 3. Open Browser
Navigate to: **http://localhost:9000**

That's it! You're ready to use the system.

---

## Features

### 💬 Chat Mode
Interactive conversations with your memory agent, just like Claude Desktop:
- Ask questions about your memories
- Get personalized responses based on your memory store
- Session persists across conversations

### 🎯 Planning Mode
Autonomous planning with multiple iterations:
- Describe your planning goal
- System runs up to 9 iterations (configurable)
- Each iteration includes:
  - **Context Retrieval** - Gathers relevant information
  - **4-Agent Workflow** - Planner, Verifier, Executor, Generator work together
  - **Learning** - Flow-GRPO training applied
  - **Memory Storage** - Results saved permanently

---

## How It Works

### Architecture Overview

```
Browser (http://localhost:9000)
    ↓
FastAPI Web Server (Python)
    ↓
├─ Chat Mode: Direct Agent interaction
│
└─ Planning Mode: Orchestrator + 4-Agent System
    ├─ Context Manager (web search, memory retrieval)
    ├─ Workflow Coordinator (4-agent coordination)
    ├─ Memory Manager (storage & learning)
    └─ Learning Manager (Flow-GRPO training)
    ↓
Memory System (local markdown files)
```

### Backend Detection

The chatbox **automatically detects** your platform:
- **macOS**: Uses Fireworks AI (cloud-based LLM)
- **Linux**: Uses vLLM (local H100 GPU)
- **Windows**: Falls back to OpenRouter

No manual configuration needed!

---

## Usage Guide

### Chat Mode

1. **Click "💬 Chat" button** in sidebar (default)
2. **Type your question** in the input field
3. **Press Enter** or click "Send"
4. Agent responds with personalized answer

**Examples:**
- "What have we discussed about market entry strategies?"
- "Tell me about the Japanese hospital project"
- "What are the key lessons learned from previous planning?"

### Planning Mode

1. **Click "🎯 Plan" button** in sidebar
2. **Configure options** (visible on left):
   - Max Iterations: 1-30 (default: 9)
   - Checkpoint Interval: 1-10 (default: 3)
3. **Describe your planning goal** in the input field
4. **Press Enter** or click "Send"
5. System runs autonomous planning loops

**Examples:**
- "Develop a market entry strategy for healthcare in Vietnam"
- "Create a technology implementation roadmap for our company"
- "Analyze competitive landscape and recommend positioning strategy"

#### What Happens During Planning

Each iteration goes through 4 steps:

**[Step 1/4] Context Retrieval**
- System gathers web search results
- Retrieves relevant memory entities
- Analyzes past successful patterns

**[Step 2/4] 4-Agent Workflow**
- 🧭 **Planner Agent** - Creates strategic plan
- ✅ **Verifier Agent** - Validates plan quality
- 🛠️ **Executor Agent** - Plans implementation
- ✍️ **Generator Agent** - Generates detailed outputs

**[Step 3/4] Storage & Learning**
- Results saved to memory files
- Flow-GRPO training signal applied
- Patterns learned for next iteration

**[Step 4/4] Completion**
- Iteration marked complete
- Browser shows summary
- Full details available in memory directory

---

## Accessing Full Results

While the browser shows summaries, **full planning details are stored in memory**:

```
~/.../local-memory/
├── plans/
│   └── iteration_NNN_full_details.md     ← Full planning results
├── entities/
│   ├── execution_log.md                  ← What's been executed
│   ├── successful_patterns.md            ← What works well
│   ├── planning_errors.md                ← What to avoid
│   └── [100+ other entities]             ← Your memory store
└── deliverables/
    └── enhanced_execution_report_*.md    ← Detailed reports
```

Open these files to see:
- Complete planner output
- Detailed verifier validation
- Full executor plan
- Generated deliverables
- All agent reasoning

---

## Configuration

### Max Iterations
- **Min**: 1, **Max**: 30, **Default**: 9
- Higher = more iterations for refinement
- **Recommendation**: 7-9 for quality planning

### Checkpoint Interval
- **Min**: 1, **Max**: 10, **Default**: 3
- How often to save intermediate results
- **Recommendation**: 3 (save after every 3 iterations)

### Backend
Check the sidebar for active backend:
- ✅ Fireworks (macOS)
- ✅ vLLM (Linux)
- ✅ OpenRouter (fallback)

---

## Troubleshooting

### "Connection refused" Error

**Problem**: Browser can't connect to http://localhost:9000

**Solutions**:
1. Check if model server is running: `make run-agent`
2. Verify chatbox started: Check terminal for "Starting server on: http://localhost:9000"
3. Wait 5-10 seconds after starting chatbox
4. Try force-refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows/Linux)

### Port 9000 Already in Use

**Problem**: "Address already in use"

**Solutions**:
```bash
# Find process using port 9000
lsof -i :9000

# Kill the process (replace PID with actual number)
kill -9 <PID>

# Or use killall
killall -9 python
```

Then restart: `make serve-chatbox`

### Planning Takes Too Long

**Problem**: Iteration takes > 5 minutes

**Likely causes**:
1. Web search taking long (network issue)
2. Model server is slow (check with `make run-agent`)
3. Memory file is very large (too many entities)

**Solutions**:
1. Check internet connectivity
2. Reduce `Max Iterations` to 3-5
3. Restart model server: `make run-agent`

### Unicode/Emoji Not Displaying

**Problem**: Emoji showing as boxes or garbled text

**Solutions**:
1. Ensure browser is fully loaded (wait 2 seconds)
2. Try different browser (Chrome/Firefox usually best)
3. Check terminal output to ensure chatbox is responding

### Session Lost After Refresh

**Problem**: Starting new conversation after browser refresh

**Note**: This is normal! Each browser session is independent. The system:
- Stores results in memory files (persistent)
- Browser session ID stored in localStorage (per-device)
- Memory is shared across all sessions

If you want persistent conversation, check memory files!

---

## Performance Tips

### For Faster Planning
1. Use **4-bit precision**: `make run-agent` → choose option 1
2. Reduce **Max Iterations**: Set to 3-5 instead of 9
3. Use **smaller goals**: More specific goals = faster planning

### For Higher Quality
1. Use **8-bit precision**: `make run-agent` → choose option 2
2. Increase **Max Iterations**: Set to 9-15
3. Describe goals with more context

### Memory Management
Keep memory directory organized:
- Archive old planning iterations
- Delete test entities
- Monitor memory usage: `du -sh ./local-memory`

---

## Advanced Usage

### Accessing via Command Line

The chatbox API is also available via curl:

```bash
# Chat
curl -X POST http://localhost:9000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about markets", "session_id": "user123"}'

# Planning
curl -X POST http://localhost:9000/api/plan \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Develop market entry strategy",
    "session_id": "user123",
    "max_iterations": 9,
    "checkpoint_interval": 3
  }'

# System Status
curl http://localhost:9000/api/status
```

### Running Multiple Sessions

You can open **multiple browser tabs** - each gets its own session!
- Same memory, different conversation threads
- Session ID stored in localStorage per-tab
- Useful for parallel planning on different goals

---

## Comparison: Chatbox vs MCP vs CLI

| Feature | Chatbox | MCP (Desktop) | CLI |
|---------|---------|---------------|-----|
| **Interface** | Web browser | Claude Desktop | Terminal |
| **Chat Mode** | ✅ | ✅ | ✅ |
| **Planning** | ✅ Better | ⚠️ Broken pipes | ✅ |
| **Emoji Support** | ✅ Native | ❌ JSON errors | ✅ |
| **Long Iterations** | ✅ Unlimited | ❌ <2 min limit | ✅ |
| **Setup Required** | Minimal | Complex | Minimal |
| **Recommended Use** | **Planning loops** | Ad-hoc chat | Testing |

---

## Common Workflows

### Workflow 1: Interactive Planning Session

```
1. Start chatbox: make serve-chatbox
2. Open http://localhost:9000
3. Chat Mode: Ask "What should we focus on?"
4. Plan Mode: Describe goal based on response
5. View memory: Open ~/...local-memory/plans/
6. Refine: Use feedback for next planning iteration
```

### Workflow 2: Batch Planning

```
1. Prepare list of planning goals in a file
2. Start chatbox and model server
3. For each goal:
   a. Switch to Plan Mode
   b. Paste goal
   c. Run (9-15 iterations)
   d. Check results in memory
4. Compare all iterations for insights
```

### Workflow 3: Memory-Based Learning

```
1. Run planning iterations for Goal A
2. Check entities created: ~/.../entities/
3. Review successful_patterns.md
4. Plan Goal B (system learns from Goal A)
5. Observe improved quality due to learning
```

---

## Memory & Storage

### What Gets Stored

After each planning iteration:
- ✅ Full planning outputs
- ✅ Agent results (all 4 agents)
- ✅ Context retrieved
- ✅ Learning signals
- ✅ Execution logs
- ✅ Learned patterns

### Accessing Results

**Quick Summary** (in browser):
- Iterations completed
- Execution time
- Status (success/partial/error)

**Full Details** (in memory files):
```bash
# View latest plan
cat ~/.../local-memory/plans/iteration_001_full_details.md

# View all execution logs
cat ~/.../local-memory/entities/execution_log.md

# View learned patterns
cat ~/.../local-memory/entities/successful_patterns.md

# Check for errors to avoid
cat ~/.../local-memory/entities/planning_errors.md
```

---

## Support & Feedback

### Reporting Issues

When something goes wrong, check:
1. **Terminal output**: Look for error messages
2. **Memory files**: Check if results were saved
3. **System status**: Click "System Status" in sidebar
4. **Browser console**: F12 → Console tab for JS errors

### Debug Mode

Enable detailed logging:
```bash
cd mem-agent-mcp
FASTMCP_LOG_LEVEL=DEBUG make serve-chatbox
```

---

## Next Steps

- ✅ Master **Chat Mode** for conversation
- ✅ Try **Planning Mode** with small goals (1-3 iterations)
- ✅ Review **memory files** to see full results
- ✅ Increase iterations and complexity gradually
- ✅ Build **knowledge base** through repeated planning

---

## Key Advantages Over MCP

✅ **No Broken Pipes**: Handles long-running planning without errors
✅ **Emoji Support**: All Unicode renders perfectly in browser
✅ **No Protocol Overhead**: Direct Python-to-browser communication
✅ **Unlimited Iterations**: No 2-minute timeout limits
✅ **Better UX**: Sidebar for mode switching and configuration
✅ **Persistent Memory**: Results saved permanently
✅ **Learning Loop**: Flow-GRPO training works perfectly
✅ **Zero Setup**: Just run `make serve-chatbox`

---

**Happy planning! 🎯**
