# Phase 1 UI Integration Plan

**Date:** October 28, 2025
**Target:** Integrate entity selector + approval gate + function calling into simple_chatbox.py
**Scope:** Modify one file (simple_chatbox.py) to add new UI components and tool execution

---

## Current State

**simple_chatbox.py:**
- 1238 lines
- FastAPI app with HTML UI
- Two modes: chat (/api/chat) and planning (/api/plan)
- Sidebar on left, main chat area on right
- No entity selection
- No approval gates
- Uses SimpleOrchestrator (old rigid system)

**Goal:** Upgrade to use LlamaPlanner + function calling

---

## Integration Strategy: 3 Phases

### Phase 1A: Imports & Setup (Add new modules)
### Phase 1B: UI Components (Add HTML/CSS/JavaScript)
### Phase 1C: Tool Execution & Flow (Add API logic)

---

## Phase 1A: Imports & Setup

### Location: Lines 40-53 (after agent/orchestrator imports)

**Add:**
```python
# Import Llama Planner components
try:
    from llama_planner import LlamaPlanner, PlanningApproach, PlanningOutcome
    LLAMA_PLANNER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import LlamaPlanner: {e}")
    LLAMA_PLANNER_AVAILABLE = False

try:
    from research_agent import ResearchAgent
    RESEARCH_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import ResearchAgent: {e}")
    RESEARCH_AGENT_AVAILABLE = False

try:
    from learning_tracker import LearningTracker
    LEARNING_TRACKER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import LearningTracker: {e}")
    LEARNING_TRACKER_AVAILABLE = False

try:
    from tool_definitions import get_tool_definitions
    FUNCTION_CALLING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import tool definitions: {e}")
    FUNCTION_CALLING_AVAILABLE = False
```

---

## Phase 1B: UI Components

### Location: Lines 614-660 (Sidebar section in HTML)

**Current structure:**
- Mode selector buttons (chat/planning)
- Status info
- (Empty space for new components)

**Add after status-info div:**

#### 1. Entity Selector Component (NEW)

```html
<!-- Entity Selector -->
<div id="entity-selector-panel" class="sidebar-panel" style="display: none;">
    <h3>📚 Select Memory Entities</h3>

    <div class="search-box">
        <input type="text" id="entity-search" placeholder="Search entities..."
               onkeyup="filterEntities(this.value)">
    </div>

    <div id="entity-list" class="entity-list">
        <!-- Populated by JavaScript -->
    </div>

    <div class="entity-controls">
        <button class="btn-small" onclick="saveEntitySelection()">Save</button>
        <button class="btn-small" onclick="clearEntitySelection()">Clear</button>
    </div>

    <div class="selection-summary">
        <small id="selection-count">Selected: 0</small>
    </div>
</div>
```

#### 2. Approval Gate Component (NEW)

```html
<!-- Approval Gate Modal -->
<div id="approval-gate-modal" class="modal" style="display: none;">
    <div class="modal-content">
        <h2>✨ Approve Planning Approach</h2>

        <div class="approval-section">
            <h3>Goal</h3>
            <div id="approval-goal" class="goal-box"></div>
        </div>

        <div class="approval-section">
            <h3>Memory Search</h3>
            <div id="approval-memory" class="info-box"></div>
        </div>

        <div class="approval-section">
            <h3>Proposed Approach</h3>
            <div id="approval-approach" class="info-box"></div>
        </div>

        <div class="approval-controls">
            <button class="btn btn-approve" onclick="approveApproach()">✓ APPROVE</button>
            <button class="btn btn-reject" onclick="rejectApproach()">✗ REJECT</button>
            <button class="btn btn-adjust" onclick="toggleAdjustmentForm()">? ADJUST</button>
        </div>

        <div id="adjustment-form" style="display: none;" class="approval-section">
            <h3>Describe Changes</h3>
            <textarea id="adjustment-text" placeholder="Describe what you'd like to change..."
                      rows="3"></textarea>
            <div class="approval-controls">
                <button class="btn btn-confirm" onclick="submitAdjustment()">Send</button>
                <button class="btn btn-cancel" onclick="toggleAdjustmentForm()">Cancel</button>
            </div>
        </div>
    </div>
</div>
```

#### 3. CSS Additions (In `<style>` section, after existing CSS)

Add these new CSS classes:

```css
/* Entity Selector */
.sidebar-panel {
    margin-bottom: 20px;
}

.sidebar-panel h3 {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 12px;
    color: #333;
}

.search-box {
    margin-bottom: 12px;
}

.search-box input {
    width: 100%;
    padding: 8px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    font-size: 13px;
}

.entity-list {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    margin-bottom: 12px;
}

.entity-item {
    padding: 8px;
    border-bottom: 1px solid #eee;
    cursor: pointer;
    transition: all 0.2s;
}

.entity-item:hover {
    background: #f3f4f6;
}

.entity-item.selected {
    background: #dbeafe;
    border-left: 3px solid #2563eb;
}

.entity-checkbox {
    margin-right: 6px;
}

.entity-controls,
.selection-summary {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    gap: 8px;
}

.entity-controls button {
    flex: 1;
    padding: 6px;
    font-size: 12px;
    border: 1px solid #d1d5db;
    background: white;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.entity-controls button:hover {
    background: #f9fafb;
}

/* Modal */
.modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    background: white;
    border-radius: 8px;
    max-width: 600px;
    max-height: 90vh;
    overflow-y: auto;
    padding: 24px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-content h2 {
    margin-bottom: 20px;
    color: #333;
}

.approval-section {
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #e5e7eb;
}

.approval-section h3 {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 10px;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.goal-box,
.info-box {
    padding: 12px;
    background: #f9fafb;
    border-radius: 4px;
    font-size: 13px;
    line-height: 1.5;
    color: #333;
    border-left: 3px solid #2563eb;
}

.approval-controls {
    display: flex;
    gap: 8px;
    margin-top: 12px;
}

.btn {
    flex: 1;
    padding: 10px;
    border: none;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-approve {
    background: #10b981;
    color: white;
}

.btn-approve:hover {
    background: #059669;
}

.btn-reject {
    background: #ef4444;
    color: white;
}

.btn-reject:hover {
    background: #dc2626;
}

.btn-adjust {
    background: #3b82f6;
    color: white;
}

.btn-adjust:hover {
    background: #2563eb;
}

.btn-confirm {
    background: #10b981;
    color: white;
}

.btn-cancel {
    background: #999;
    color: white;
}

#adjustment-text {
    width: 100%;
    padding: 8px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    font-family: monospace;
    font-size: 12px;
    resize: vertical;
}

.btn-small {
    padding: 6px 10px;
    font-size: 11px;
    border: 1px solid #d1d5db;
    background: white;
    border-radius: 4px;
    cursor: pointer;
}

.btn-small:hover {
    background: #f9fafb;
}
```

#### 4. JavaScript Functions (In `<script>` section at end of HTML)

Add these functions:

```javascript
// ============================================
// ENTITY SELECTOR JAVASCRIPT
// ============================================

let selectedEntities = [];

async function initEntitySelector() {
    // Load entity list from memory directory
    try {
        const response = await fetch('/api/entities');
        const entities = await response.json();

        // Load saved selection from localStorage
        const savedSelection = localStorage.getItem('llama_selected_entities');
        selectedEntities = savedSelection ? JSON.parse(savedSelection) : [];

        // Render entity list
        renderEntityList(entities);

        // Show entity selector when in planning mode
        document.getElementById('entity-selector-panel').style.display = 'block';
    } catch (e) {
        console.error('Failed to init entity selector:', e);
    }
}

function renderEntityList(entities) {
    const list = document.getElementById('entity-list');
    list.innerHTML = entities.map(entity => `
        <div class="entity-item ${selectedEntities.includes(entity.name) ? 'selected' : ''}"
             onclick="toggleEntity('${entity.name}')">
            <input type="checkbox" class="entity-checkbox"
                   ${selectedEntities.includes(entity.name) ? 'checked' : ''}
                   onchange="toggleEntity('${entity.name}')">
            <span>${entity.name}</span>
            <small style="display: block; margin-top: 4px; color: #999;">
                ${entity.description || 'No description'}
            </small>
        </div>
    `).join('');

    updateSelectionSummary();
}

function toggleEntity(name) {
    if (selectedEntities.includes(name)) {
        selectedEntities = selectedEntities.filter(e => e !== name);
    } else {
        selectedEntities.push(name);
    }
    saveEntitySelection();
}

function saveEntitySelection() {
    localStorage.setItem('llama_selected_entities', JSON.stringify(selectedEntities));
    updateSelectionSummary();
}

function clearEntitySelection() {
    selectedEntities = [];
    saveEntitySelection();
}

function filterEntities(query) {
    const items = document.querySelectorAll('.entity-item');
    items.forEach(item => {
        const name = item.textContent.toLowerCase();
        item.style.display = name.includes(query.toLowerCase()) ? 'block' : 'none';
    });
}

function updateSelectionSummary() {
    document.getElementById('selection-count').textContent =
        `Selected: ${selectedEntities.length}`;
}

// ============================================
// APPROVAL GATE JAVASCRIPT
// ============================================

let pendingApproach = null;

function showApprovalGate(goal, memoryResults, approach) {
    pendingApproach = { goal, memoryResults, approach };

    // Populate modal
    document.getElementById('approval-goal').textContent = goal;

    document.getElementById('approval-memory').innerHTML = `
        <strong>Memory Coverage: ${Math.round(memoryResults.coverage * 100)}%</strong>
        <p>Entities searched: ${memoryResults.sources.join(', ')}</p>
        <p>Gaps identified: ${memoryResults.gaps.join(', ')}</p>
    `;

    document.getElementById('approval-approach').innerHTML = `
        <strong>Approach Breakdown</strong>
        <p>Memory: ${Math.round(approach.memory_percentage * 100)}%</p>
        <p>Research: ${Math.round(approach.research_percentage * 100)}%</p>
        <p>Agents: ${approach.agents_to_use.join(' → ')}</p>
    `;

    // Show modal
    document.getElementById('approval-gate-modal').style.display = 'flex';
}

function approveApproach() {
    // Send approval and continue execution
    fetch('/api/approve-approach', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            approach: pendingApproach.approach,
            status: 'approved'
        })
    }).then(() => {
        document.getElementById('approval-gate-modal').style.display = 'none';
    });
}

function rejectApproach() {
    fetch('/api/approve-approach', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            approach: pendingApproach.approach,
            status: 'rejected'
        })
    }).then(() => {
        document.getElementById('approval-gate-modal').style.display = 'none';
    });
}

function toggleAdjustmentForm() {
    const form = document.getElementById('adjustment-form');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

function submitAdjustment() {
    const adjustment = document.getElementById('adjustment-text').value;
    fetch('/api/approve-approach', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            approach: pendingApproach.approach,
            status: 'adjusted',
            adjustment: adjustment
        })
    }).then(() => {
        document.getElementById('approval-gate-modal').style.display = 'none';
    });
}

// Initialize on load
window.addEventListener('load', initEntitySelector);
```

---

## Phase 1C: Tool Execution & Flow

### New API Endpoints to Add

#### 1. GET /api/entities (Before line 239, before status endpoint)

```python
@app.get("/api/entities")
async def get_entities():
    """Return list of memory entities available for selection."""
    try:
        memory_path = get_memory_path()
        entities_dir = Path(memory_path) / "entities"

        entities = []
        if entities_dir.exists():
            for entity_file in entities_dir.glob("*.md"):
                name = entity_file.stem
                # Try to extract description from file
                try:
                    content = entity_file.read_text()
                    lines = content.split('\n')
                    description = lines[0].strip() if lines else ""
                except:
                    description = ""

                entities.append({
                    "name": name,
                    "description": description,
                    "path": str(entity_file.relative_to(memory_path))
                })

        return entities
    except Exception as e:
        return []
```

#### 2. POST /api/approve-approach (After existing endpoints)

```python
class ApprovalRequest(BaseModel):
    approach: dict
    status: str  # approved, rejected, adjusted
    adjustment: Optional[str] = None
    session_id: Optional[str] = None

@app.post("/api/approve-approach")
async def approve_approach(request: ApprovalRequest):
    """Handle user approval of planning approach."""
    session_id, session = get_or_create_session(request.session_id)

    if request.status == "approved":
        # Execute the approved approach
        session["pending_approval"] = None
        session["approach_status"] = "approved"
        return {"status": "approved", "session_id": session_id}

    elif request.status == "rejected":
        session["pending_approval"] = None
        return {"status": "rejected", "session_id": session_id}

    elif request.status == "adjusted":
        # Return adjustment request for Llama to handle
        session["pending_approval"] = None
        session["user_adjustment"] = request.adjustment
        return {"status": "adjusted", "adjustment": request.adjustment, "session_id": session_id}
```

#### 3. POST /api/execute-plan (New planning endpoint with function calling)

This is the core endpoint that:
1. Takes goal + selected entities
2. Initializes LlamaPlanner
3. Makes Fireworks API call with function calling
4. Executes tool calls
5. Shows approval gate
6. Continues execution after approval
7. Logs outcomes for learning

```python
class ExecutePlanRequest(BaseModel):
    goal: str
    selected_entities: List[str]
    session_id: Optional[str] = None

@app.post("/api/execute-plan")
async def execute_plan(request: ExecutePlanRequest):
    """
    Execute planning with Llama as decision maker.

    Flow:
    1. Initialize LlamaPlanner with selected entities
    2. Call Fireworks with function calling
    3. Execute tool calls iteratively
    4. Show approval gate before major execution
    5. Log outcomes for learning
    """

    if not LLAMA_PLANNER_AVAILABLE:
        raise HTTPException(status_code=500, detail="LlamaPlanner not available")

    session_id, session = get_or_create_session(request.session_id)
    agent = session["agent"]
    memory_path = get_memory_path()

    try:
        # Initialize LlamaPlanner
        planner = LlamaPlanner(agent, memory_path)

        # Step 1: Llama analyzes goal and proposes approach
        # Prepare system prompt with function definitions
        tools = get_tool_definitions()

        # Create messages for Fireworks API
        system_prompt = open('/path/to/llama_planner_prompt.txt').read()  # Load prompt

        messages = [
            {"role": "user", "content": f"Goal: {request.goal}\n\nSelected memory entities: {', '.join(request.selected_entities)}"}
        ]

        # Make API call to Fireworks with function calling
        response = await call_fireworks_with_tools(
            messages=messages,
            system_prompt=system_prompt,
            tools=tools,
            agent=agent  # Pass agent for executing tools
        )

        # Response will contain either text (proposal) or tool_calls
        # Continue processing...

        return {
            "status": "success",
            "session_id": session_id,
            "message": "Planning complete"
        }

    except Exception as e:
        return {
            "status": "error",
            "session_id": session_id,
            "error": str(e)
        }
```

---

## Implementation Checklist

### Phase 1A: Imports
- [ ] Add LlamaPlanner imports (line ~45)
- [ ] Add ResearchAgent imports
- [ ] Add LearningTracker imports
- [ ] Add tool_definitions imports

### Phase 1B: UI Components
- [ ] Add entity selector HTML
- [ ] Add approval gate modal HTML
- [ ] Add CSS for entity selector
- [ ] Add CSS for approval gate
- [ ] Add entity selector JavaScript
- [ ] Add approval gate JavaScript

### Phase 1C: Backend
- [ ] Add /api/entities endpoint
- [ ] Add /api/approve-approach endpoint
- [ ] Create tool executor function
- [ ] Create Fireworks API wrapper with function calling
- [ ] Add /api/execute-plan endpoint
- [ ] Wire up flow: goal → memory search → propose → approve → execute

---

## Key Files Involved

### Modified:
- `simple_chatbox.py` - Main file being updated

### New/Unchanged:
- `llama_planner.py` - Already created ✅
- `research_agent.py` - Already created ✅
- `learning_tracker.py` - Already created ✅
- `tool_definitions.py` - Already created ✅
- `llama_planner_prompt.txt` - Already updated ✅

---

## Testing Strategy

After each phase, test:

**Phase 1A:**
- Can import all modules without errors
- Modules show as "available" in /api/status

**Phase 1B:**
- Entity selector renders in sidebar
- Can select/deselect entities
- Selection persists on page refresh
- Approval gate modal shows and hides

**Phase 1C:**
- POST /api/entities returns entity list
- POST /api/approve-approach handles approval
- POST /api/execute-plan runs full flow
- Llama's decisions appear as tool calls
- Tool calls are executed
- Results fed back to Llama
- Outcome logged for learning

---

## Success Criteria

✅ Entity selector works (persistence, filtering)
✅ Approval gate works (show, approve/reject/adjust)
✅ Fireworks function calling works (tools defined, called, executed)
✅ Llama makes intelligent decisions (searches memory first, researches gaps)
✅ Full flow works (goal → approval → execution → learning)
✅ No regressions (old chat/plan modes still work)

---

## Timeline Estimate

- Phase 1A: 30 min (imports)
- Phase 1B: 60 min (UI components)
- Phase 1C: 90 min (backend logic + Fireworks integration)
- Testing: 60 min
- **Total: ~4 hours**

---

This plan provides step-by-step guidance for integrating the new system while minimizing risk and ensuring quality.

