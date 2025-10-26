# 🚀 Chatbox Quick Reference

## One-Liner Startup
```bash
make run-agent  # Terminal 1
make serve-chatbox  # Terminal 2
# Open http://localhost:9000
```

---

## Two Modes

### 💬 Chat Mode (Default)
- Ask questions naturally
- Get memory-based responses
- Interactive conversation

### 🎯 Planning Mode
- Describe goal
- System plans autonomously
- Results in memory files

---

## Planning Workflow

```
Goal Description
  ↓
[9 iterations max]
  ├─ Step 1: Retrieve Context
  ├─ Step 2: Run 4-Agent Workflow
  ├─ Step 3: Store & Learn
  └─ Step 4: Complete
  ↓
Results in: ~/.../local-memory/plans/
```

---

## Key Settings

| Setting | Default | Use | Range |
|---------|---------|-----|-------|
| Max Iterations | 9 | How many times to refine | 1-30 |
| Checkpoint | 3 | Save every N iterations | 1-10 |

---

## File Locations

| File | Purpose |
|------|---------|
| `plans/iteration_NNN_full_details.md` | Full planning output |
| `entities/execution_log.md` | What's been done |
| `entities/successful_patterns.md` | What works |
| `entities/planning_errors.md` | What to avoid |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Connection refused | Start model server: `make run-agent` |
| Port in use | `kill -9 $(lsof -t -i:9000)` |
| Emoji garbled | Refresh browser or try different browser |
| Takes > 5 min | Reduce iterations or restart model server |

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Enter | Send message |
| Shift+Enter | (Chat only) Multi-line |
| Cmd/Ctrl+R | Refresh browser |
| Tab | Switch modes |

---

## Status Indicators

| Icon | Meaning |
|------|---------|
| ✅ | Success/Available |
| ⚠️ | Warning/Attention |
| ❌ | Error/Unavailable |
| 🔄 | Processing |

---

## Terminal Commands

```bash
# Run agent server (REQUIRED)
make run-agent

# Start chatbox
make serve-chatbox

# Interactive CLI (alternative to chatbox)
make chat-cli

# View memory directory
ls ~/.../local-memory/plans/
cat ~/.../local-memory/plans/iteration_001_full_details.md
```

---

## Planning Goal Examples

### Simple (1-3 iterations)
- "Create a bio for our new product"
- "Summarize market trends for healthcare"

### Medium (5-7 iterations)
- "Develop market entry strategy for Vietnam"
- "Create implementation roadmap"

### Complex (9+ iterations)
- "Design comprehensive go-to-market strategy"
- "Analyze competitive landscape and recommend strategy"

---

## Memory Structure

```
local-memory/
├── user.md                    # Profile
├── plans/                     # Planning outputs
│   └── iteration_NNN_full_details.md
├── entities/                  # Knowledge base
│   ├── execution_log.md
│   ├── successful_patterns.md
│   ├── planning_errors.md
│   └── [100+ other entities]
└── deliverables/             # Reports
    └── enhanced_execution_report_*.md
```

---

## Performance Tips

**Faster**: 4-bit precision + 3-5 iterations
**Better**: 8-bit precision + 9-15 iterations
**Balanced**: 4-bit precision + 9 iterations ✅

---

## Browser Compatibility

| Browser | Emoji | Performance | Notes |
|---------|-------|-------------|-------|
| Chrome | ✅ | ✅ Best | Recommended |
| Firefox | ✅ | ✅ Good | Recommended |
| Safari | ✅ | ✅ Good | Works well |
| Edge | ✅ | ✅ Good | Works well |

---

## API Endpoints (Advanced)

```bash
# Get status
curl http://localhost:9000/api/status

# Chat
curl -X POST http://localhost:9000/api/chat \
  -d '{"message":"hello"}'

# Plan
curl -X POST http://localhost:9000/api/plan \
  -d '{"goal":"..","max_iterations":9}'
```

---

## Common Issues

### Q: Why is planning slow?
A: Check if model server running. First iteration usually takes 30-60s.

### Q: Where are my planning results?
A: In `~/.../local-memory/plans/iteration_NNN_full_details.md`

### Q: Can I run multiple sessions?
A: Yes! Each browser tab = separate session, same memory.

### Q: How much storage do I need?
A: ~100MB for 100+ planning iterations (markdown format).

### Q: Can I use Claude Desktop too?
A: Yes! Both chatbox and MCP work with same memory. Use chatbox for planning.

---

## Pro Tips

1. **Use chat first** - Ask "What should I plan?" in chat mode
2. **Review patterns** - Check `successful_patterns.md` between iterations
3. **Learn from errors** - Check `planning_errors.md` to avoid mistakes
4. **Multiple goals** - Run planning for different goals to build knowledge
5. **Combine results** - Use chat mode to synthesize planning outputs

---

## Shortcuts for Power Users

```bash
# Quick start (one command)
make run-agent & sleep 3 && make serve-chatbox

# View latest planning output
tail -f ~/.../local-memory/plans/iteration_*_full_details.md

# Monitor memory growth
watch -n 5 'du -sh ~/.../local-memory'

# Kill everything
pkill -f "make run-agent\|serve-chatbox\|simple_chatbox"
```

---

**Ready to plan? 🎯 Go to http://localhost:9000**
