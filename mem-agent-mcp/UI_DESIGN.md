# UI Design - Entity Selector & Approval Gate

**Phase 1 Integration Guide for simple_chatbox.py**

---

## Part 1: Entity Selector UI

### Purpose
Allow users to select which memory entities they want Llama to search. This selection persists across multiple goals in a session.

### Visual Design

```
┌─────────────────────────────────────────────────────────────┐
│  📚 SELECT MEMORY ENTITIES TO SEARCH                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Search entity names...]                                  │
│                                                             │
│  ☑ my_startup                  Last updated: Oct 27       │
│    Company metrics, roadmap, resources                     │
│                                                             │
│  ☑ q4_2024_results             Last updated: Oct 25       │
│    Performance data, metrics from last quarter             │
│                                                             │
│  ☑ past_strategies             Last updated: Oct 20       │
│    Historical approaches and results                       │
│                                                             │
│  ☐ market_analysis             Last updated: Sep 15       │
│    Market data, trends, competitor info                   │
│                                                             │
│  ☐ team_members                Last updated: Aug 30       │
│    Team structure, capabilities                           │
│                                                             │
│  ☐ product_roadmap             Last updated: Oct 26       │
│    Q1, Q2, Q3 planned features                            │
│                                                             │
│  [✓ Save Selection] [Clear All] [View All Entities]       │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Selected: 3 entities
Last saved: Today 2:45 PM
```

### Technical Implementation

#### 1. Entity Discovery (On Load)
```javascript
// In simple_chatbox.py or separate module
function discoverEntities() {
  // Read local-memory/entities/ directory
  // Return list of .md files with metadata

  return [
    {
      name: "my_startup",
      path: "entities/my_startup.md",
      description: "Company metrics, roadmap, resources",
      last_updated: "2025-10-27",
      size_bytes: 2048
    },
    {
      name: "q4_2024_results",
      path: "entities/q4_2024_results.md",
      description: "Performance data, metrics from last quarter",
      last_updated: "2025-10-25",
      size_bytes: 1524
    },
    // ... more entities
  ]
}
```

#### 2. Entity Selection Storage
```javascript
// LocalStorage for persistence across refresh
const ENTITY_SELECTION_KEY = "llama_planner_selected_entities";

function saveEntitySelection(selectedEntities) {
  localStorage.setItem(
    ENTITY_SELECTION_KEY,
    JSON.stringify({
      selected: selectedEntities,
      saved_at: new Date().toISOString()
    })
  );
}

function loadEntitySelection() {
  const stored = localStorage.getItem(ENTITY_SELECTION_KEY);
  if (stored) {
    return JSON.parse(stored).selected;
  }
  return [];  // Default: empty
}
```

#### 3. UI Component (HTML/CSS/JavaScript)
```html
<div id="entity-selector" class="sidebar-panel">
  <div class="panel-header">
    <h3>📚 Select Entities to Search</h3>
  </div>

  <div class="search-box">
    <input
      type="text"
      id="entity-search"
      placeholder="Search entity names..."
      onkeyup="filterEntities(this.value)"
    >
  </div>

  <div id="entity-list" class="entity-list">
    <!-- Populated by JavaScript -->
  </div>

  <div class="selection-controls">
    <button onclick="saveSelection()">✓ Save Selection</button>
    <button onclick="clearSelection()">Clear All</button>
    <button onclick="showAllEntities()">View All</button>
  </div>

  <div class="selection-summary">
    <small id="selection-count">Selected: 0 entities</small>
    <small id="selection-saved">Last saved: Never</small>
  </div>
</div>

<style>
.entity-list {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 8px;
}

.entity-item {
  padding: 12px;
  margin: 4px 0;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background: #f9f9f9;
  cursor: pointer;
  transition: all 0.2s;
}

.entity-item:hover {
  background: #f0f0f0;
  border-color: #999;
}

.entity-item.selected {
  background: #e3f2fd;
  border-color: #2196F3;
}

.entity-checkbox {
  margin-right: 8px;
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.entity-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.entity-description {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.entity-meta {
  font-size: 11px;
  color: #999;
}

.selection-controls {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.selection-summary {
  margin-top: 12px;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}
</style>

<script>
async function initEntitySelector() {
  const entities = await discoverEntities();
  const selected = loadEntitySelection();
  renderEntityList(entities, selected);
}

function renderEntityList(entities, selected) {
  const list = document.getElementById("entity-list");
  list.innerHTML = entities.map(entity => `
    <div class="entity-item ${selected.includes(entity.name) ? 'selected' : ''}"
         onclick="toggleEntity('${entity.name}')">
      <input type="checkbox" class="entity-checkbox"
             ${selected.includes(entity.name) ? 'checked' : ''}
             onchange="toggleEntity('${entity.name}')">
      <div class="entity-name">${entity.name}</div>
      <div class="entity-description">${entity.description}</div>
      <div class="entity-meta">
        Updated: ${entity.last_updated} • Size: ${(entity.size_bytes/1024).toFixed(1)}KB
      </div>
    </div>
  `).join('');

  updateSelectionSummary(selected);
}

function toggleEntity(name) {
  let selected = loadEntitySelection();
  if (selected.includes(name)) {
    selected = selected.filter(e => e !== name);
  } else {
    selected.push(name);
  }
  saveEntitySelection(selected);
  initEntitySelector();  // Re-render
}

function clearSelection() {
  localStorage.removeItem(ENTITY_SELECTION_KEY);
  initEntitySelector();
}

function saveSelection() {
  // Save happens automatically on toggle, but show confirmation
  showNotification("Entity selection saved");
}

function updateSelectionSummary(selected) {
  document.getElementById("selection-count").innerText =
    `Selected: ${selected.length} entities`;
  document.getElementById("selection-saved").innerText =
    `Last saved: ${new Date().toLocaleTimeString()}`;
}
</script>
```

---

## Part 2: Approval Gate UI

### Purpose
Show Llama's proposed approach before execution. User can approve, reject, or adjust.

### Visual Design

```
┌──────────────────────────────────────────────────────────────┐
│  ✨ LLAMA'S APPROACH PROPOSAL                               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  GOAL:                                                       │
│  "Create growth strategy for Q1 2025"                       │
│                                                              │
│  ─────────────────────────────────────────────────────────   │
│  MEMORY SEARCH RESULTS:                                      │
│  ───────────────────────                                     │
│  Entities to search: my_startup, q4_2024_results            │
│
│  Coverage from memory: 60% ✓                                │
│    ✓ Company metrics (ARR $250K, 50 customers)             │
│    ✓ Past growth strategies (tried cold outreach + inbound) │
│    ✓ Available resources ($50K budget, 1 marketer)         │
│                                                              │
│  ─────────────────────────────────────────────────────────   │
│  IDENTIFIED GAPS (40%):                                      │
│  ──────────────────────                                      │
│    • Current competitor analysis (outdated from Sept 2024)  │
│    • Market trends for Q1 2025 (need latest data)           │
│                                                              │
│  ─────────────────────────────────────────────────────────   │
│  PROPOSED APPROACH:                                          │
│  ──────────────────                                          │
│
│  📊 DATA BREAKDOWN:                                          │
│     Memory:     60% ████████░░ (company context)           │
│     Research:   40% ██████░░░░ (market trends)             │
│                                                              │
│  🔍 RESEARCH FOCUS:                                          │
│     1. SaaS growth trends Q1 2025 (frameworks, PLG)         │
│     2. Competitor market moves (based on findings)          │
│     3. Best practices for bootstrapped startups            │
│                                                              │
│  🤖 AGENTS I'LL USE (in order):                             │
│     1. ResearchAgent → Find current market data            │
│     2. PlannerAgent → Create growth strategy               │
│     3. VerifierAgent → Validate plan feasibility           │
│                                                              │
│  📈 ESTIMATED RESOURCES:                                     │
│     • Web searches: ~3-4 (iterative)                       │
│     • Processing time: ~2 minutes                          │
│     • Token usage: ~12K tokens                             │
│                                                              │
│  ─────────────────────────────────────────────────────────   │
│  YOUR DECISION:                                              │
│  ────────────────                                            │
│
│  [✓ APPROVE] [✗ REJECT] [? ADJUST]                        │
│                                                              │
│  If adjusting, describe changes:                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ e.g., "Skip research, just use memory" or              │ │
│  │ "Add 'customer_feedback' entity to search"             │ │
│  │ "Focus on 50% research instead of 40%"                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  [Send Feedback]                                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Technical Implementation

#### 1. Approval State Management
```python
# In llama_planner.py or separate approval_handler.py

@dataclass
class ApprovalState:
    approach: PlanningApproach
    memory_results: Dict
    status: str = "pending"  # pending, approved, rejected, adjusted
    user_adjustment: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
```

#### 2. UI Component (HTML/CSS/JavaScript)
```html
<div id="approval-gate" class="modal-overlay" style="display: none;">
  <div class="approval-modal">
    <div class="modal-header">
      <h2>✨ Llama's Approach Proposal</h2>
    </div>

    <div class="modal-body">
      <!-- Goal Section -->
      <div class="section">
        <h3>Goal</h3>
        <div class="goal-display" id="goal-display"></div>
      </div>

      <!-- Memory Results -->
      <div class="section">
        <h3>Memory Search Results</h3>
        <div class="memory-info">
          <div id="entities-searched"></div>
          <div class="coverage-bar">
            <div class="coverage-fill" id="memory-coverage"></div>
          </div>
          <div id="memory-findings"></div>
        </div>
      </div>

      <!-- Gaps Identified -->
      <div class="section">
        <h3>Identified Gaps</h3>
        <ul id="gaps-list"></ul>
      </div>

      <!-- Proposed Approach -->
      <div class="section">
        <h3>Proposed Approach</h3>

        <div class="approach-subsection">
          <h4>Data Breakdown</h4>
          <div class="breakdown-bars">
            <div class="breakdown-item">
              <label>Memory:</label>
              <div class="bar-container">
                <div class="bar memory-bar" id="memory-bar"></div>
              </div>
              <span id="memory-percent"></span>
            </div>
            <div class="breakdown-item">
              <label>Research:</label>
              <div class="bar-container">
                <div class="bar research-bar" id="research-bar"></div>
              </div>
              <span id="research-percent"></span>
            </div>
          </div>
        </div>

        <div class="approach-subsection">
          <h4>Research Focus</h4>
          <ul id="research-focus-list"></ul>
        </div>

        <div class="approach-subsection">
          <h4>Agents I'll Use</h4>
          <div id="agents-list"></div>
        </div>
      </div>

      <!-- Resource Estimate -->
      <div class="section">
        <h3>Estimated Resources</h3>
        <ul id="resource-estimate"></ul>
      </div>

      <!-- Approval Controls -->
      <div class="section approval-controls">
        <h3>Your Decision</h3>
        <div class="button-group">
          <button class="btn btn-approve" onclick="approveApproach()">
            ✓ APPROVE
          </button>
          <button class="btn btn-reject" onclick="rejectApproach()">
            ✗ REJECT
          </button>
          <button class="btn btn-adjust" onclick="toggleAdjustmentForm()">
            ? ADJUST
          </button>
        </div>
      </div>

      <!-- Adjustment Form (Hidden by default) -->
      <div id="adjustment-form" style="display: none;" class="section">
        <h3>Describe Your Adjustments</h3>
        <p class="help-text">
          What would you like to change? Examples:
          <br/>• "Skip web research, use only memory"
          <br/>• "Add 'customer_feedback' entity to search"
          <br/>• "Use different agent sequence"
        </p>
        <textarea
          id="adjustment-text"
          placeholder="Describe your adjustment..."
          rows="4"
        ></textarea>
        <div class="button-group">
          <button class="btn btn-confirm" onclick="submitAdjustment()">
            Send Adjustment
          </button>
          <button class="btn btn-cancel" onclick="toggleAdjustmentForm()">
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
.modal-overlay {
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

.approval-modal {
  background: white;
  border-radius: 8px;
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  background: #f5f5f5;
}

.modal-body {
  padding: 20px;
}

.section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.section h3 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.goal-display {
  padding: 12px;
  background: #f9f9f9;
  border-left: 4px solid #2196F3;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.coverage-bar {
  height: 20px;
  background: #e0e0e0;
  border-radius: 10px;
  overflow: hidden;
  margin: 8px 0;
}

.coverage-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #8BC34A);
  border-radius: 10px;
  transition: width 0.3s ease;
}

.approach-subsection {
  margin: 12px 0;
  padding: 12px;
  background: #fafafa;
  border-radius: 4px;
}

.approach-subsection h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.breakdown-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.breakdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.breakdown-item label {
  min-width: 70px;
  font-weight: 600;
  color: #333;
}

.bar-container {
  flex: 1;
  height: 24px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.bar {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: 600;
  transition: width 0.3s ease;
}

.memory-bar {
  background: linear-gradient(90deg, #2196F3, #1976D2);
}

.research-bar {
  background: linear-gradient(90deg, #FF9800, #F57C00);
}

.breakdown-item span {
  min-width: 45px;
  text-align: right;
  font-weight: 600;
  color: #333;
}

#research-focus-list,
#agents-list,
#resource-estimate,
#gaps-list,
#memory-findings {
  margin: 8px 0;
  padding-left: 16px;
}

#research-focus-list li,
#agents-list li,
#resource-estimate li,
#gaps-list li {
  margin: 6px 0;
  color: #555;
  font-size: 14px;
  line-height: 1.4;
}

.approval-controls {
  border-bottom: none;
}

.button-group {
  display: flex;
  gap: 8px;
}

.btn {
  flex: 1;
  padding: 12px 16px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.btn-approve {
  background: #4CAF50;
  color: white;
}

.btn-approve:hover {
  background: #45a049;
}

.btn-reject {
  background: #f44336;
  color: white;
}

.btn-reject:hover {
  background: #da190b;
}

.btn-adjust {
  background: #2196F3;
  color: white;
}

.btn-adjust:hover {
  background: #0b7dda;
}

.btn-confirm {
  background: #4CAF50;
  color: white;
}

.btn-cancel {
  background: #999;
  color: white;
}

#adjustment-form {
  background: #fafafa;
  padding: 12px;
  border-radius: 4px;
}

#adjustment-text {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  resize: vertical;
}

.help-text {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}
</style>

<script>
function showApprovalGate(approach, memoryResults) {
  const modal = document.getElementById("approval-gate");

  // Populate content
  document.getElementById("goal-display").innerText = approach.goal;
  document.getElementById("entities-searched").innerText =
    `Entities to search: ${approach.memory_entities.join(", ")}`;

  // Coverage bar
  const coverage = memoryResults.coverage;
  const coveragePercent = Math.round(coverage * 100);
  const fill = document.getElementById("memory-coverage");
  fill.style.width = `${coveragePercent}%`;

  // Memory findings
  document.getElementById("memory-findings").innerHTML =
    `Coverage from memory: ${coveragePercent}% ✓`;

  // Gaps
  document.getElementById("gaps-list").innerHTML =
    memoryResults.gaps.map(g => `<li>${g}</li>`).join('');

  // Data breakdown
  const memoryBar = document.getElementById("memory-bar");
  const researchBar = document.getElementById("research-bar");
  memoryBar.style.width = `${approach.memory_percentage * 100}%`;
  researchBar.style.width = `${approach.research_percentage * 100}%`;
  document.getElementById("memory-percent").innerText =
    `${Math.round(approach.memory_percentage * 100)}%`;
  document.getElementById("research-percent").innerText =
    `${Math.round(approach.research_percentage * 100)}%`;

  // Research focus
  document.getElementById("research-focus-list").innerHTML =
    approach.research_focus.map(f => `<li>${f}</li>`).join('');

  // Agents
  document.getElementById("agents-list").innerHTML =
    approach.agents_to_use.map(a => `<li>${a}</li>`).join('');

  // Resources
  document.getElementById("resource-estimate").innerHTML =
    Object.entries(approach.resource_estimate)
      .map(([k, v]) => `<li>${k}: ${v}</li>`)
      .join('');

  modal.style.display = "flex";
}

function approveApproach() {
  // Send approval signal and close modal
  window.parent.postMessage({
    type: "approach_approved",
    timestamp: new Date().toISOString()
  }, "*");

  document.getElementById("approval-gate").style.display = "none";
}

function rejectApproach() {
  window.parent.postMessage({
    type: "approach_rejected",
    timestamp: new Date().toISOString()
  }, "*");

  document.getElementById("approval-gate").style.display = "none";
}

function toggleAdjustmentForm() {
  const form = document.getElementById("adjustment-form");
  form.style.display = form.style.display === "none" ? "block" : "none";
}

function submitAdjustment() {
  const adjustment = document.getElementById("adjustment-text").value;
  window.parent.postMessage({
    type: "approach_adjusted",
    adjustment: adjustment,
    timestamp: new Date().toISOString()
  }, "*");

  document.getElementById("approval-gate").style.display = "none";
}
</script>
```

---

## Integration Points with simple_chatbox.py

### 1. On Application Load
```python
# Initialize entity selector
selected_entities = load_entity_selection()
render_entity_selector(all_entities)
```

### 2. When User Submits Goal
```python
# Get selected entities from UI
selected_entities = get_selected_entities()

# Pass to Llama planner
memory_results = llama_planner.search_memory(
  entities=selected_entities,
  queries=extract_queries_from_goal(user_goal)
)

# Get Llama's approach proposal
approach = llama_planner.propose_approach(
  goal=user_goal,
  memory_results=memory_results,
  approach_plan=...  # Llama's decision
)

# Show approval UI
show_approval_gate(approach, memory_results)
```

### 3. On User Approval
```python
# Wait for approval signal from UI
# Then execute the approved approach
results = execute_approved_approach(approach)
```

### 4. After Planning Complete
```python
# Capture user feedback
rating = capture_user_rating()
feedback = capture_user_feedback()

# Log outcome for learning
outcome = PlanningOutcome(
  goal=user_goal,
  approach=approach,
  ...
)
llama_planner.log_outcome(outcome)
llama_planner.capture_user_rating(outcome, rating, feedback)
```

---

## State Flow

```
Application Starts
  ↓
Load Entity Selection (from localStorage)
Render Entity Selector UI
  ↓
User Selects Entities & Confirms
Selection saved to localStorage
  ↓
User Enters Goal
  ↓
Search Memory (selected entities)
  ↓
Llama Proposes Approach
  ↓
Show Approval Gate Modal
  ↓
User: Approve / Reject / Adjust
  ↓
[Approved] → Execute Plan → Capture Feedback → Log Outcome
[Rejected/Adjusted] → Return to goal entry
  ↓
Results shown in chat
```

---

## Success Criteria

✅ Entity selector shows all available entities
✅ Selection persists across page refresh
✅ User can change selection anytime
✅ Approval gate shows complete breakdown
✅ User can approve, reject, or adjust
✅ Adjustments are understood and implemented
✅ Feedback is captured after each planning iteration
✅ Learning log is populated with outcomes

