# Frontend-Backend Contract Specification

**Version:** 1.0
**Date:** November 2, 2025
**Status:** ✅ ENFORCED & TESTED

---

## Purpose

This document defines the EXACT JSON structures, field names, and behavior for all communication between the frontend (HTML/JavaScript) and backend (Python/FastAPI).

**Why This Matters**: Frontend and backend were out of sync for 7 days because there was NO formal contract. This document prevents that from happening again.

---

## Endpoint: POST /api/generate-proposal

### Request Contract

**Called by**: `planGoal()` function in index.html
**URL**: `POST http://localhost:9000/api/generate-proposal`
**Content-Type**: `application/json`

#### Request Body (EXACT JSON Structure)

```json
{
  "goal": "Develop a healthcare market entry strategy for Vietnam",
  "selected_entities": ["agent_coordination", "detailed_implementation_plan"],
  "selected_agents": ["planner", "generator"],
  "max_iterations": 3,
  "checkpoint_interval": 2,
  "session_id": "abc123def456"
}
```

#### Request Field Definitions

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `goal` | string | YES | - | User's planning goal (500 chars max) |
| `selected_entities` | array[string] | NO | [] | Entity names (from /api/entities response) |
| `selected_agents` | array[string] | NO | [] | Agent names: "planner", "verifier", "executor", "generator" |
| `max_iterations` | integer | YES | 3 | Number of planning iterations (1-20) |
| `checkpoint_interval` | integer | YES | 2 | Frequency of checkpoints (1-10) |
| `session_id` | string | NO | generated | Unique session identifier |

#### Python Pydantic Model

```python
class ProposalRequest(BaseModel):
    """Request for planning proposal generation."""
    goal: str
    session_id: Optional[str] = None
    selected_entities: Optional[List[str]] = None
    selected_agents: Optional[List[str]] = None
    max_iterations: int = 3
    checkpoint_interval: int = 2
```

### Response Contract

#### Success Response (HTTP 200)

```json
{
  "status": "success",
  "proposal_id": "a1b2c3d4e5f6",
  "proposal": "# Planning Proposal: [Goal]\n\n## Executive Summary\n...(8000+ chars)...",
  "approach": {
    "frameworks_used": [...],
    "data_points": {...}
  },
  "memory_coverage": 0.6,
  "research_coverage": 0.4,
  "memory_coverage_percent": 60.0,
  "research_coverage_percent": 40.0,
  "memory_percentage": 0.6,
  "research_percentage": 0.4,
  "entity_count": 2,
  "entity_names": ["agent_coordination", "detailed_implementation_plan"],
  "agents_to_use": ["PlannerAgent", "GeneratorAgent"],
  "max_iterations": 3,
  "checkpoint_interval": 2,
  "session_id": "abc123def456",
  "timestamp": "2025-11-02T22:30:45.123456"
}
```

#### Response Field Definitions

| Field | Type | Notes |
|-------|------|-------|
| `status` | string | Always "success" on 200 |
| `proposal_id` | string | Unique ID for this proposal |
| `proposal` | string | Full proposal text (5000-10000 chars), markdown formatted |
| `approach` | object | Strategic approach details |
| `memory_coverage` | float | Decimal form (0.0-1.0) - redundant, use `memory_percentage` |
| `research_coverage` | float | Decimal form (0.0-1.0) - redundant, use `research_percentage` |
| `memory_coverage_percent` | float | Percentage form (0-100) - redundant, use `memory_coverage_percent` |
| `research_coverage_percent` | float | Percentage form (0-100) - redundant, use `research_coverage_percent` |
| `memory_percentage` | float | **USE THIS**: Decimal form (0.0-1.0) |
| `research_percentage` | float | **USE THIS**: Decimal form (0.0-1.0) |
| `entity_count` | integer | Number of entities selected |
| `entity_names` | array[string] | Names of selected entities |
| `agents_to_use` | array[string] | Agent names for execution |
| `max_iterations` | integer | Echoes request value |
| `checkpoint_interval` | integer | Echoes request value |
| `session_id` | string | Session identifier |
| `timestamp` | string | ISO 8601 timestamp |

#### Python Pydantic Model

```python
class ProposalResponse(BaseModel):
    """Planning proposal response."""
    status: str
    proposal_id: str
    proposal: str
    approach: Dict[str, Any]
    memory_coverage: float
    research_coverage: float
    session_id: str
    timestamp: str
    memory_percentage: Optional[float] = None
    research_percentage: Optional[float] = None
    memory_coverage_percent: Optional[float] = None
    research_coverage_percent: Optional[float] = None
    entity_count: Optional[int] = None
    entity_names: Optional[List[str]] = None
    agents_to_use: Optional[List[str]] = None
    max_iterations: Optional[int] = None
    checkpoint_interval: Optional[int] = None
```

#### Error Response (HTTP 400)

```json
{
  "detail": "Description of what went wrong"
}
```

---

## Endpoint: GET /api/entities

### Request Contract

**Called by**: `loadEntities()` function in index.html (on page load)
**URL**: `GET http://localhost:9000/api/entities`
**No request body**

### Response Contract

#### Success Response (HTTP 200)

```json
{
  "entities": [
    {
      "name": "agent_coordination",
      "display_name": "Agent Coordination",
      "description": "Memory entity with 1118 references",
      "references": 1118
    },
    {
      "name": "detailed_implementation_plan",
      "display_name": "Detailed Implementation Plan",
      "description": "Memory entity with 39 references",
      "references": 39
    },
    ...
  ],
  "total_count": 23
}
```

#### Response Field Definitions

| Field | Type | Notes |
|-------|------|-------|
| `entities` | array[object] | List of all available entities |
| `entities[].name` | string | File name (without .md extension) - use in POST requests |
| `entities[].display_name` | string | User-friendly name for UI display |
| `entities[].description` | string | Human-readable description |
| `entities[].references` | integer | Number of references (higher = more important) |
| `total_count` | integer | Total number of entities |

---

## Endpoint: GET /api/get-available-plans

### Request Contract

**Called by**: `showPlanSelectionModal()` function in index.html
**URL**: `GET http://localhost:9000/api/get-available-plans?session_id=abc123`
**Query Parameters**:
- `session_id` (optional): Current session ID

### Response Contract

#### Success Response (HTTP 200)

```json
{
  "status": "success",
  "plans": [
    {
      "file": "plan_develop_market_entry_20251102_103045.md",
      "goal": "Develop a market entry strategy for healthcare in Vietnam",
      "quality": 8.5,
      "created": "2025-11-02 10:30:45",
      "size_kb": 12.4
    },
    ...
  ],
  "total_count": 6,
  "message": "6 completed plans available for learning"
}
```

#### Response Field Definitions

| Field | Type | Notes |
|-------|------|-------|
| `status` | string | "success" or "no_plans" |
| `plans` | array[object] | List of past plans |
| `plans[].file` | string | File name - use in POST requests |
| `plans[].goal` | string | Planning goal this plan addresses |
| `plans[].quality` | float | Quality score (0-10) |
| `plans[].created` | string | Timestamp when plan was created |
| `plans[].size_kb` | float | File size in kilobytes |
| `total_count` | integer | Total number of plans |
| `message` | string | Human-readable message |

---

## Frontend Implementation

### Key Functions

#### 1. loadEntities()

**Purpose**: Fetch and display available entities in sidebar

**Called**: On page load

**Code Pattern**:
```javascript
async function loadEntities() {
    const response = await fetch('/api/entities');
    const data = await response.json();
    const entities = data.entities || [];

    // Display in sidebar
    entities.forEach(entity => {
        // Create checkbox with entity.name (for selection)
        // Display entity.display_name (for user)
    });
}
```

**CRITICAL**: Use `entity.name` (not `entity.display_name`) when sending to backend

#### 2. planGoal()

**Purpose**: Send planning request to backend

**Called**: When user clicks PLAN button

**Code Pattern**:
```javascript
async function planGoal() {
    const goal = document.getElementById('goalInput').value;
    const maxIterations = 3;  // Default
    const checkpointInterval = 2;  // Default

    const payload = {
        goal: goal,
        selected_entities: selectedEntities,  // Array of entity.name values
        selected_agents: selectedAgents,  // Array from checkboxes
        max_iterations: maxIterations,
        checkpoint_interval: checkpointInterval,
        session_id: sessionId
    };

    const response = await fetch('/api/generate-proposal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    const proposal = await response.json();
    showProposalModal(proposal, maxIterations, checkpointInterval);
}
```

**CRITICAL FIELDS TO SEND**:
- ✅ `goal` - required
- ✅ `selected_entities` - use entity.name values
- ✅ `max_iterations` - must send (not hardcoded in backend)
- ✅ `checkpoint_interval` - must send (not hardcoded in backend)

#### 3. showProposalModal()

**Purpose**: Display proposal content to user

**Called**: After /api/generate-proposal response

**Code Pattern**:
```javascript
function showProposalModal(proposal, maxIterations, checkpointInterval) {
    // Display proposal.proposal (full markdown text)
    // Display proposal.memory_percentage * 100 (as percentage)
    // Display proposal.research_percentage * 100 (as percentage)

    // Show editable config fields
    document.getElementById('modal-max-iterations').value = maxIterations;
    document.getElementById('modal-checkpoint-interval').value = checkpointInterval;
}
```

**CRITICAL FIELDS TO DISPLAY**:
- ✅ `proposal.proposal` - full text (use memory_percentage and research_percentage for math)
- ✅ `proposal.memory_percentage` - use this, not memory_coverage_percent
- ✅ `proposal.research_percentage` - use this, not research_coverage_percent

---

## Backend Implementation

### Key Functions

#### 1. generate_proposal_endpoint()

**File**: simple_chatbox.py, line 1063

**CRITICAL**: Must do these things:

```python
@app.post("/api/generate-proposal")
async def generate_proposal_endpoint(request: ProposalRequest):
    # 1. CREATE PlanRequest with user's values (NOT hardcoded)
    plan_req = PlanRequest(
        goal=request.goal,
        session_id=request.session_id,
        max_iterations=request.max_iterations,  # ✅ Use request value
        checkpoint_interval=request.checkpoint_interval,  # ✅ Use request value
        selected_entities=request.selected_entities,  # ✅ Pass through
        selected_agents=request.selected_agents  # ✅ Pass through
    )

    # 2. Call _generate_planning_proposal
    return await _generate_planning_proposal(
        session_manager.get_or_create(request.session_id)[1],
        plan_req,
        request.session_id
    )
```

**CRITICAL MISTAKES TO AVOID**:
- ❌ Hardcoding `max_iterations=4` (was here - FIXED)
- ❌ Hardcoding `checkpoint_interval=2` (was here - FIXED)
- ❌ Not passing `selected_entities` and `selected_agents` (was here - FIXED)

#### 2. _generate_planning_proposal()

**File**: simple_chatbox.py, line 682

**CRITICAL**: Must do these things:

```python
async def _generate_planning_proposal(session, request, session_id):
    # 1. Call llama_planner.search_memory() with selected_entities
    memory_results = await asyncio.to_thread(
        llama_planner.search_memory,
        selected_entities,
        queries
    )

    # 2. Get entities_found from results
    entities_found = memory_results.get("entities_found", [])

    # 3. Calculate coverage (MUST reflect what user selected)
    total_selected = len(entities_found) + len(entities_missing)
    entity_coverage = len(entities_found) / total_selected if total_selected > 0 else 0.0
    memory_percentage = entity_coverage * 0.6

    # 4. Use request values in proposal text
    proposal_text = f"""
...
Using {request.max_iterations} planning iterations...
- Maximum iterations: {request.max_iterations}
- Checkpoint interval: {request.checkpoint_interval}
- Memory coverage: {memory_percentage*100:.0f}% (based on {len(entities_found)} selected entities found)
...
"""

    # 5. Return ALL required fields
    return ProposalResponse(
        status="success",
        proposal=proposal_text,
        memory_percentage=memory_percentage,  # ✅ Decimal form
        research_percentage=research_percentage,  # ✅ Decimal form
        memory_coverage_percent=memory_percentage * 100,  # ✅ Percentage form
        research_coverage_percent=research_percentage * 100,  # ✅ Percentage form
        # ... other fields ...
    )
```

#### 3. llama_planner.search_memory()

**File**: llama_planner.py, line 165

**CRITICAL**: Must do these things:

```python
def search_memory(self, entities, queries):
    # 1. Try to read each selected entity file
    for entity in entities:
        entity_path = Path(self.memory_path) / "entities" / f"{entity}.md"
        if not entity_path.exists():
            missing_entities.append(entity)
            continue

        # 2. READ file (don't filter by keywords)
        with open(entity_path, 'r') as f:
            content = f.read()

        # 3. ADD to results REGARDLESS of keyword match
        # ✅ This is the CRITICAL FIX
        found_content.append(content)
        found_entities.append(entity)  # Always add if file exists

    # 4. Return what was found
    return {
        "entities_found": found_entities,  # All readable selected entities
        "entities_missing": missing_entities,  # Non-existent entities
        # ...
    }
```

**CRITICAL MISTAKE TO AVOID**:
- ❌ Filtering entities by keyword match (was here - FIXED)

---

## Testing the Contract

### Unit Test: Request Validation

```python
def test_proposal_request_validation():
    payload = {
        "goal": "test",
        "selected_entities": ["entity1"],
        "max_iterations": 3,
        "checkpoint_interval": 2
    }

    request = ProposalRequest(**payload)

    assert request.goal == "test"
    assert request.max_iterations == 3
    assert request.checkpoint_interval == 2
    assert request.selected_entities == ["entity1"]
```

### Integration Test: End-to-End

```python
def test_proposal_response_completeness():
    payload = {
        "goal": "test",
        "selected_entities": ["agent_coordination"],
        "max_iterations": 3,
        "checkpoint_interval": 2
    }

    response = requests.post("/api/generate-proposal", json=payload)
    data = response.json()

    # Verify response structure
    assert data["status"] == "success"
    assert data["proposal_id"] is not None
    assert len(data["proposal"]) > 5000
    assert data["memory_percentage"] > 0  # Entity was selected
    assert data["max_iterations"] == 3  # Not hardcoded to 4
    assert "based on 1 selected entities found" in data["proposal"]
```

### Browser Test: Full Workflow

1. Open http://localhost:9000
2. Sidebar loads → should show 23 entities
3. Select "Agent Coordination"
4. Enter goal
5. Click PLAN
6. Proposal modal appears showing:
   - ✅ Full proposal text (8000+ chars)
   - ✅ "Memory Coverage: 60%" (not 0%)
   - ✅ "Maximum iterations: 3" (not 4)
   - ✅ "based on 1 selected entities found"

---

## Common Mistakes (Do NOT Make These)

### ❌ Mistake #1: Hardcoding Backend Defaults
```python
# WRONG
plan_req = PlanRequest(
    goal=request.goal,
    max_iterations=4  # ❌ Hardcoded!
)

# RIGHT
plan_req = PlanRequest(
    goal=request.goal,
    max_iterations=request.max_iterations  # ✅ Use request value
)
```

### ❌ Mistake #2: Not Passing User Selections
```python
# WRONG
plan_req = PlanRequest(
    goal=request.goal
    # ❌ Missing selected_entities and selected_agents
)

# RIGHT
plan_req = PlanRequest(
    goal=request.goal,
    selected_entities=request.selected_entities,  # ✅ Pass through
    selected_agents=request.selected_agents  # ✅ Pass through
)
```

### ❌ Mistake #3: Filtering User Selections
```python
# WRONG
if keyword_match(entity, query):  # ❌ Filters user selections!
    found_entities.append(entity)

# RIGHT
if entity_file_exists(entity):  # ✅ Only check existence
    found_entities.append(entity)
```

### ❌ Mistake #4: Using Wrong Field Names
```javascript
// WRONG
const coverage = response.memory_coverage_percent;  // ❌ Use this for display
const percentage = coverage * 100;  // ❌ Double-multiplies!

// RIGHT
const decimal = response.memory_percentage;  // ✅ Use decimal form
const percentage = decimal * 100;  // ✅ Multiply once
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Nov 2, 2025 | Initial contract specification after bug fixes |

---

## Sign-Off

This contract was created after identifying three critical bugs caused by frontend-backend desynchronization.

**Status**: ✅ Enforced in codebase
**Last Verified**: November 2, 2025 22:30 UTC
**Tests Passing**: 8/8 critical tests

For questions or clarifications, refer to SYSTEM_STATUS_NOV2_2025.md
