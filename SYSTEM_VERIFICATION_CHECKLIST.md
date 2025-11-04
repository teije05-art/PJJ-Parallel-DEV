# System Verification Checklist

**Date:** November 2, 2025
**Purpose:** Complete verification that system is ready for multi-iteration planning

---

## Critical Bug Fixed

**BUG:** PlanningSession was not using Fireworks API
- **File:** `approval_gates.py` line 33
- **Issue:** `Agent(memory_path=memory_path)` was missing Fireworks flag
- **Fix:** Now properly initializes with `use_fireworks=True` on macOS
- **Status:** ✅ FIXED

---

## Pre-Flight Checklist

### 1. Environment Configuration

```bash
# Check Fireworks API key is set
echo $FIREWORKS_API_KEY

# Should output your Fireworks API key (not empty)
# If empty, set it:
export FIREWORKS_API_KEY="your_api_key_here"
```

**Required:** FIREWORKS_API_KEY must be set before starting chatbox

---

### 2. Package Installation

```bash
# Verify fireworks-ai is installed
python -c "import fireworks; print(fireworks.__version__)"

# Should output version number
# If not installed:
pip install --upgrade fireworks-ai
```

**Required:** fireworks-ai package must be installed

---

### 3. Model Configuration

Expected model: `accounts/fireworks/models/llama-v3p3-70b-instruct`

**Verification:**
- Check in `agent/settings.py` line 14
- Should match Fireworks model name
- ✅ Confirmed correct

---

## System Architecture Verification

### Backend Components

#### 1. Agent Initialization (approval_gates.py)
- ✅ Now uses `use_fireworks=True` on macOS
- ✅ Will use `use_vllm=True` on Linux
- ✅ Properly detects platform via `sys.platform`

#### 2. SimpleOrchestrator (simple_orchestrator.py)
- ✅ Creates Agent with Fireworks enabled
- ✅ Passes `selected_plans` through context
- ✅ Supports Plan Selection Gate

#### 3. PlannerAgent (planner_agent.py)
- ✅ Accepts `selected_plans` parameter
- ✅ Passes to PatternRecommender
- ✅ Integration complete

#### 4. Pattern Components
- ✅ LearningAnalyzer: get_available_plans(), analyze_selected_plans()
- ✅ PatternRecommender: get_pattern_context(selected_plans)
- ✅ Cost-optimized learning activated

#### 5. API Endpoints
- ✅ `/api/get-available-plans` - Fetch available plans
- ✅ `/api/execute-plan` - Execute with selected_plans parameter
- ✅ `/api/chat` - Regular chat (fixed Fireworks)
- ✅ `/api/generate-proposal` - Proposal generation (fixed missing field)

### Frontend Components

#### 1. Plan Selection Modal (index.html)
- ✅ HTML modal created
- ✅ JavaScript handlers implemented
- ✅ Integrated into workflow

#### 2. Workflow Integration
- ✅ approveProposal() shows Plan Selection Gate
- ✅ executePlan() accepts selectedPlans parameter
- ✅ Selected plans passed to backend as URL parameter

---

## Testing Sequence

### Test 1: Verify Fireworks Connection

```bash
# Start fresh terminal
cd /Users/teije/Desktop/memagent-modular-fixed/mem-agent-mcp

# Set Fireworks API key
export FIREWORKS_API_KEY="your_key_here"

# Start chatbox
make serve-chatbox
```

**Expected Output:**
```
✅ MemAgent Chatbox Starting
✅ Application startup complete
✅ Uvicorn running on http://0.0.0.0:9000
```

---

### Test 2: Simple Chat (verifies Fireworks)

**In Browser:**
1. Open http://localhost:9000
2. Type: "hello"
3. Press Enter

**Expected Output:**
- ✅ No "Connection refused" error
- ✅ No "Connection error" in logs
- ✅ Bot responds with greeting

**If this fails:**
- ❌ Check FIREWORKS_API_KEY is set: `echo $FIREWORKS_API_KEY`
- ❌ Check fireworks-ai installed: `pip list | grep fireworks`
- ❌ Check internet connection to api.fireworks.ai

---

### Test 3: Proposal Generation

**In Browser:**
1. Type: "create a healthcare market entry strategy for japan in vietnam"
2. Click "Generate Proposal"

**Expected Output:**
```
✅ Proposal generation for multi-iteration planning...
✅ Memory entities found
✅ Research focus identified
✅ Agents to use selected
✅ Proposal modal displayed
```

**If error occurs:**
- Check terminal output for specific error message
- Verify Agent is initialized with Fireworks (approved_gates.py line 36)
- Verify selected_agents field exists in PlanRequest model

---

### Test 4: Plan Selection Gate

**In Browser:**
1. Continue from proposal modal
2. Click "Approve & Execute"

**Expected Output:**
```
✅ Plan Selection Modal appears
✅ Available plans fetched from /api/get-available-plans
✅ Plans listed with quality scores
✅ Quick select buttons working
```

**If error occurs:**
- Check /api/get-available-plans endpoint response
- Verify LearningAnalyzer.get_available_plans() exists
- Check local-memory/plans/ directory exists

---

### Test 5: Planning with Learning

**In Browser:**
1. Continue from Plan Selection Gate
2. Select "Recent 3" or custom plans
3. Click "Continue to Planning"

**Expected Output:**
```
✅ Planning started
✅ Terminal shows: "📌 User selected N plans for learning"
✅ Terminal shows: "✅ Analyzed N patterns from selected plans"
✅ Planning iterations begin
✅ Checkpoints appear
✅ Final plan generated
```

**Terminal Output Should Show:**
```
🧭 PLANNER AGENT: Generating strategic plan...
🎯 PATTERN RECOMMENDER: Finding learned patterns...
📌 User selected 3 plans for learning
✅ Analyzed 3 patterns from selected plans
✅ Found N relevant learned patterns to apply
```

---

## Verification Checklist

### Before Running Tests

- [ ] FIREWORKS_API_KEY is set in environment
- [ ] fireworks-ai package is installed
- [ ] Python 3.11+ is active
- [ ] Port 9000 is available
- [ ] Memagent service running on MacBook
- [ ] Internet connection available

### After Starting Chatbox

- [ ] Server starts on http://localhost:9000
- [ ] Web interface loads
- [ ] API status returns 200 OK
- [ ] Entities list loads

### During First Chat

- [ ] "hello" message gets response (not Connection error)
- [ ] Response comes from Llama 3.3 70B
- [ ] No "Connection refused" errors

### During Proposal Generation

- [ ] Proposal modal appears
- [ ] Modal shows entities, agents, configuration
- [ ] No "selected_agents" errors
- [ ] Approve button works

### During Plan Selection

- [ ] Plan Selection Modal appears
- [ ] Available plans are listed
- [ ] Quick select buttons work
- [ ] Continue button passes selected plans

### During Planning Execution

- [ ] Planning starts without errors
- [ ] Terminal shows pattern analysis
- [ ] Planning iterations complete
- [ ] Checkpoints appear
- [ ] Final plan is generated with learned patterns

---

## Success Criteria

✅ **System is ready for multi-iteration planning when:**

1. Chat works without "Connection error"
2. Proposal generation completes without errors
3. Plan Selection Gate modal appears and functions
4. Planning starts with selected plans
5. Terminal shows pattern learning occurring
6. Planning completes with final plan
7. No exceptions or error traces

---

## What Each Component Does Now

### Agent (approval_gates.py line 36)
- ✅ Detects platform (macOS → Fireworks)
- ✅ Creates Fireworks client with API key
- ✅ Handles all chat requests through Fireworks

### Orchestrator (simple_orchestrator.py)
- ✅ Initializes with Fireworks support
- ✅ Accepts selected_plans from frontend
- ✅ Passes selected_plans through context layers

### PlannerAgent (planner_agent.py)
- ✅ Receives context with selected_plans
- ✅ Passes to PatternRecommender
- ✅ PatternRecommender analyzes only selected plans
- ✅ Patterns used in Llama's planning prompt

### LearningAnalyzer (learning_analyzer.py)
- ✅ analyze_selected_plans() - Analyzes ONLY selected plans (cost-optimized)
- ✅ get_available_plans() - Returns list for frontend
- ✅ get_patterns_for_goal() - Finds relevant patterns

### Frontend (index.html)
- ✅ showPlanSelectionModal() - Fetches and displays plans
- ✅ confirmPlanSelection() - Captures user selections
- ✅ executePlan() - Passes selected_plans to backend

---

## Common Issues & Solutions

### Issue: "Connection refused" or "Connection error"
**Cause:** Fireworks API key not set or service not responding
**Solution:**
```bash
export FIREWORKS_API_KEY="your_key_here"
# Then restart chatbox
make serve-chatbox
```

### Issue: "'PlanRequest' object has no attribute 'selected_agents'"
**Cause:** Fixed by adding selected_agents to PlanRequest model
**Solution:** ✅ Already fixed in this update

### Issue: Plan Selection Modal doesn't appear
**Cause:** /api/get-available-plans endpoint error
**Solution:**
```bash
# Check endpoint manually
curl http://localhost:9000/api/get-available-plans

# Check for errors in terminal output
```

### Issue: "No completed plans found"
**Cause:** First iteration - no past plans to select
**Solution:** This is normal for first iteration. System will skip selection and start planning.

---

## Next: Run Tests

Once you've verified the checklist above, proceed with:

1. **Test 1:** Chat with "hello"
2. **Test 2:** Generate proposal
3. **Test 3:** Approve proposal → See Plan Selection Gate
4. **Test 4:** Select plans
5. **Test 5:** Watch planning execute with learned patterns

Each test should complete without errors.

---

*System Verification Checklist - November 2, 2025*
