# Deployment Guide

Quick guide to get the orchestrator running on both Mac and H100 instance.

## ✅ **What Was Done**

### **Added to Existing MCP Server**

Modified `/Users/teije/Desktop/memagent/mem-agent-mcp/mcp_server/server.py` to include:

1. **Import orchestrator** (lines 25-31)
2. **Global state** for tracking current plan (lines 36-42)
3. **Four new MCP tools**:
   - `start_planning_iteration(goal)` - Start new iteration
   - `approve_current_plan()` - Approve and execute
   - `reject_current_plan(reason)` - Reject with feedback
   - `view_learning_summary()` - See what was learned

**Key Point:** These tools are added to your **existing** MCP server. No new server needed!

---

## 🚀 **Deployment Steps**

### **On Mac (Local Testing)**

#### **1. Verify Orchestrator Module**
```bash
cd /Users/teije/Desktop/memagent/mem-agent-mcp
ls orchestrator/
# Should see: orchestrator.py, __init__.py, etc.
```

#### **2. Restart Your MCP Server**
```bash
# Stop any running instance
pkill -f "mcp_server/server.py"

# Start fresh
make serve-mcp
```

#### **3. Restart Claude Desktop**
```bash
# Quit Claude Desktop completely
# Then reopen it
# New tools are now available!
```

#### **4. Test in Claude**
```
You: What tools do you have?
Claude: [Should list the new orchestrator tools]

You: Start a planning iteration for testing the orchestrator
Claude: [Shows generated plan with CoT reasoning]

You: Approve this plan
Claude: [Executes and updates memory]
```

---

### **On H100 Instance (Production)**

#### **1. Transfer Files**

```bash
# From your Mac
cd /Users/teije/Desktop/memagent

# Transfer orchestrator directory
scp -r mem-agent-mcp/orchestrator/ user@h100-instance:/path/to/mem-agent-mcp/

# Transfer updated server.py
scp mem-agent-mcp/mcp_server/server.py user@h100-instance:/path/to/mem-agent-mcp/mcp_server/
```

#### **2. Restart MCP Server on Instance**

```bash
# SSH into instance
ssh user@h100-instance

# Navigate to project
cd /path/to/mem-agent-mcp

# Restart server
pkill -f "mcp_server/server.py"
make serve-mcp

# Or if using systemd/supervisor, restart that service
```

#### **3. Test**

Same as Mac - restart Claude Desktop and test the tools!

---

## 📝 **File Checklist**

Files that need to be on H100 instance:

```
mem-agent-mcp/
├── mcp_server/
│   ├── server.py          ← UPDATED (has orchestrator tools)
│   └── [other files]      ← Keep existing files
├── orchestrator/          ← NEW DIRECTORY
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── README.md
│   ├── ARCHITECTURE.md
│   ├── CLAUDE_USAGE.md
│   └── [other docs]
├── agent/                 ← Keep existing
├── memory/                ← Keep existing
└── [other directories]    ← Keep existing
```

---

## 🔧 **Verification**

### **Check 1: Orchestrator Import**
```bash
cd /path/to/mem-agent-mcp
python3 -c "from orchestrator.orchestrator import LearningOrchestrator; print('✅ Import successful')"
```

Should print: `✅ Import successful`

### **Check 2: MCP Server Tools**
Start the server and in Claude:
```
You: What tools do you have available?
```

Should see:
- `use_memory_agent` (existing)
- `start_planning_iteration` (new)
- `approve_current_plan` (new)  
- `reject_current_plan` (new)
- `view_learning_summary` (new)

### **Check 3: Backend Detection**
```bash
# On Mac (should use Fireworks)
python3 -c "import sys; print('Platform:', sys.platform)"
# Output: Platform: darwin

# On H100 (should use vLLM)
python3 -c "import sys; print('Platform:', sys.platform)"
# Output: Platform: linux
```

The orchestrator auto-detects and uses the right backend!

---

## 💻 **Resource Usage**

### **Mac:**
- Orchestrator: ~500 MB RAM
- Backend: Fireworks API (0 VRAM)
- **Total extra**: ~500 MB RAM

### **H100:**
- Orchestrator: ~500 MB RAM  
- Backend: Uses existing vLLM (80 GB VRAM)
- Temporary inference: +1-2 GB VRAM per call
- **Peak**: 81-82 GB / 90 GB available ✅

---

## 🎯 **Usage Workflows**

### **Workflow 1: Interactive Planning (Claude)**

```
1. You: "Start planning for [goal]"
2. Claude: [Shows plan with reasoning]
3. You: "Approve" or "Reject because [reason]"
4. Claude: [Executes and learns]
5. Repeat!
```

**Best for:** Non-technical users, conversational approval

### **Workflow 2: Batch Planning (Terminal)**

```bash
python orchestrator/orchestrator.py
# Enter goal
# Review plans in terminal
# Approve/reject with y/n
```

**Best for:** Developers, quick testing, automation

### **Both Work!** Use whichever fits your workflow.

---

## 🐛 **Troubleshooting**

### **Issue: "Orchestrator not available"**

```bash
# Check if orchestrator directory exists
ls mem-agent-mcp/orchestrator/

# Check if Python can import it
python3 -c "from orchestrator.orchestrator import LearningOrchestrator"

# If import fails, check PYTHONPATH
echo $PYTHONPATH
```

**Fix:** Make sure you're in the `mem-agent-mcp` directory when starting the server.

### **Issue: "No plan to approve"**

You need to start an iteration first:
```
You: Start a planning iteration for [goal]
# THEN approve
You: Approve the plan
```

### **Issue: Tools not showing in Claude**

1. Restart Claude Desktop completely
2. Check MCP server is running: `ps aux | grep server.py`
3. Check Claude's connection: Look for 🔌 icon in Claude

### **Issue: High memory usage**

Each inference call uses 1-2 GB temporarily. If you're hitting limits:
- Wait a few seconds between calls
- Check vLLM has enough free memory
- Monitor with: `nvidia-smi`

---

## 📊 **Testing Checklist**

- [ ] Orchestrator imports successfully
- [ ] MCP server starts without errors
- [ ] Claude shows new tools
- [ ] Can start planning iteration
- [ ] Plan shows CoT reasoning
- [ ] Can approve plan
- [ ] Memory files get updated
- [ ] Can reject plan with feedback
- [ ] Can view learning summary
- [ ] Second iteration uses learned context

---

## 🎉 **Success Criteria**

You'll know it's working when:

1. ✅ Claude can start planning iterations
2. ✅ Plans show detailed chain-of-thought reasoning
3. ✅ You can approve/reject naturally in conversation
4. ✅ Memory files accumulate (check `entities/execution_log.md`)
5. ✅ Second iteration shows more context than first
6. ✅ System learns from your feedback

---

## 🔄 **Updating in the Future**

If you modify the orchestrator:

**On Mac:**
```bash
# No need to transfer anything
# Just restart Claude Desktop
```

**On H100:**
```bash
# Transfer only changed files
scp orchestrator/orchestrator.py user@h100:/path/to/mem-agent-mcp/orchestrator/

# Restart server
ssh user@h100 'cd /path/to/mem-agent-mcp && pkill -f server.py && make serve-mcp &'
```

---

## 📚 **Next Steps**

1. **Test on Mac first**
   - Verify tools work in Claude
   - Run a few iterations
   - Check memory accumulation

2. **Transfer to H100**
   - Copy orchestrator directory
   - Copy updated server.py
   - Restart server

3. **Run production iterations**
   - Same interface, different backend
   - Learning accumulates in memory
   - System gets smarter!

---

## 💡 **Key Insight**

**No new server needed!** 

The orchestrator tools are **integrated** into your existing MCP server. Just restart Claude Desktop and you're ready to go!

```
Same server + New tools = Better planning system 🚀
```

