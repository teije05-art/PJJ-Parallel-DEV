# Plan Selection Gate - Cost-Optimized Learning

**Date:** November 2, 2025
**Purpose:** Enable users to control which past plans the system learns from, avoiding API cost explosion while enhancing human-in-the-loop control

---

## Problem Statement

With the infinite learning loop, every time a user requests a plan, the system would:
1. Read ALL completed plans (30-40+ files after multiple iterations)
2. Parse ALL patterns from successful_patterns.md
3. Analyze ALL patterns for relevance
4. Extract patterns for Llama

**Cost Impact:**
- After 10 plans: ~1-2 extra API calls per iteration
- After 30 plans: ~3-5 extra API calls per iteration
- After 50+ plans: ~10+ extra API calls per iteration
- **Result:** Exponential cost growth, unacceptable for proof-of-concept

## Solution: Plan Selection Gate

Add a new **approval gate** where users explicitly select which past plans to learn from before planning begins.

### Benefits

✅ **Cost Control** - Only analyze 3-5 selected plans, not 30-40
✅ **User Transparency** - See exactly which patterns are being extracted
✅ **Quality Control** - Exclude failed or irrelevant plans from learning
✅ **Specialization** - User can say "learn from healthcare plans" or "Vietnam market only"
✅ **Educational** - Users understand system learning process
✅ **Human-in-Loop Enhanced** - More approval gates = more user control

## Architecture: Three-Gate System

```
User Request (Planning Goal)
    ↓
[GATE 1] ← EXISTING
Proposal Generation & Approval
(User approves entities, agents, approach)
    ↓
[GATE 2] ← NEW
Plan Selection for Learning
(User selects which past plans to learn from)
Options:
  - "Skip learning this iteration"
  - "Learn from recent 3 plans"
  - "Learn from recent 5 plans"
  - "Custom: Select specific plans"
    ↓
[GATE 3] ← EXISTING
Plan Refinement Checkpoints
(User approves iterations during planning)
    ↓
Final Plan Output
```

## Component Changes

### 1. LearningAnalyzer (`orchestrator/learning_analyzer.py`)

**New Methods:**

```python
def get_available_plans(self) -> List[Dict[str, Any]]:
    """
    Returns list of available plans with metadata:
    [
        {
            "file": "plan_1.md",
            "goal": "Healthcare company entering Vietnam...",
            "quality": 7.8,
            "created": "2025-11-02 10:23:45",
            "size_kb": 12.4
        },
        ...
    ]
    """

def analyze_selected_plans(self, plan_files: List[str]) -> Dict[str, Any]:
    """
    Analyze ONLY the selected plans (cost-optimized).

    Input: ["plan_1.md", "plan_3.md", "plan_5.md"]
    Output: Only extracts patterns from these 3 plans
    Cost: ~3 pattern extractions instead of 30+
    """
```

**Why This Works:**
- Old method `analyze_all_completed_plans()` kept for backward compatibility
- New method processes only selected plans
- Same extraction quality, fraction of the cost

### 2. PatternRecommender (`orchestrator/pattern_recommender.py`)

**Updated Method:**

```python
def get_pattern_context(self, goal: str, selected_plans: Optional[List[str]] = None):
    """
    Now accepts optional selected_plans parameter.

    If selected_plans provided:
    1. Call analyzer.analyze_selected_plans(selected_plans)
    2. Extract patterns from these only
    3. Return patterns for Llama

    If None:
    - Use existing patterns (no new analysis)
    - Faster, zero additional cost
    """

def get_available_plans_for_selection(self) -> Dict[str, Any]:
    """
    Return list of available plans for the UI to display.
    Called when showing the plan selection gate.
    """
```

**Why This Works:**
- Pattern recommender is the gateway for plan analysis
- Can control whether to analyze or not via parameter
- Maintains backward compatibility

### 3. PlannerAgent (`orchestrator/agents/planner_agent.py`)

**Updated Signature:**

```python
def generate_strategic_plan(self, goal: str, context: Dict[str, str],
                           selected_plans: Optional[List[str]] = None) -> AgentResult:
    """
    Now accepts optional selected_plans.

    Passes to pattern_recommender.get_pattern_context(goal, selected_plans)
    """
```

**Why This Works:**
- Planner is entry point for planning
- Can accept selected plans from orchestrator
- Passes to pattern recommender
- Maintains backward compatibility

## Frontend Integration (index.html)

New UI element for Plan Selection Gate:

```html
<!-- After Proposal Approval, Before Planning Starts -->
<div id="plan-selection-modal" class="modal">
    <h2>Select Plans for Learning</h2>

    <p>Which past plans should the system learn from?</p>

    <div class="plan-list">
        <!-- Display available plans with checkboxes -->
        <label>
            <input type="checkbox" value="plan_1.md">
            Healthcare entering Vietnam (Quality: 7.8)
        </label>
        <label>
            <input type="checkbox" value="plan_3.md">
            Tech startup scaling (Quality: 8.1)
        </label>
        <!-- ... more plans ... -->
    </div>

    <div class="quick-select">
        <button>Skip Learning</button>
        <button>Recent 3</button>
        <button>Recent 5</button>
        <button>All</button>
        <button>Custom Selected</button>
    </div>

    <button onclick="confirmPlanSelection()">
        Continue to Planning
    </button>
</div>
```

## API Endpoints (simple_chatbox.py)

### New: `/api/get-available-plans`

```bash
GET /api/get-available-plans

Response:
{
    "status": "success",
    "plans": [
        {
            "file": "plan_1.md",
            "goal": "Healthcare company entering Vietnam...",
            "quality": 7.8,
            "created": "2025-11-02 10:23:45",
            "size_kb": 12.4
        },
        ...
    ],
    "total_count": 5,
    "message": "Found 5 completed plans. Select which to learn from."
}
```

### Modified: `/api/execute-plan`

```bash
POST /api/execute-plan

Body:
{
    "goal": "...",
    "selected_entities": [...],
    "selected_agents": [...],
    "selected_plans": ["plan_1.md", "plan_3.md"],  # NEW
    ...
}

Flow:
1. User confirms proposal
2. User selects plans
3. Passes selected_plans to orchestrator
4. Orchestrator → PlannerAgent → PatternRecommender
5. Learns only from selected plans
```

## Cost Analysis

### Example: 40 Iterations Over Time

**Old Approach (Analyze All Plans):**
```
Iteration 1:  1 plan → 1 analysis
Iteration 2:  2 plans → 2 analyses
...
Iteration 40: 40 plans → 40 analyses
Total: Sum(1 to 40) = 820 analyses

Cost: 820 API calls for learning ≈ $40+ (at typical rates)
```

**New Approach (User Selects 3-5):**
```
Iteration 1:  1 plan → 0 selected → 0 analyses (skip learning)
Iteration 2:  2 plans → user selects 1 → 1 analysis
Iteration 3:  3 plans → user selects 3 → 3 analyses
...
Iteration 40: 40 plans → user selects 5 → 5 analyses
Total: ~2.5 analyses per iteration × 40 = 100 analyses

Cost: 100 API calls for learning ≈ $5 (90% reduction!)
```

**Plus Added Benefits:**
- User sees what's being analyzed
- User can focus learning on specific domains
- User can exclude failed plans
- More transparency in system behavior

## User Experience Flow

### First Planning Request (No History)
```
User: "Healthcare company entering Vietnam"
    ↓
[Gate 1] Proposal: Entities & Agents
    ↓
[Gate 2] Plan Selection: "No completed plans available yet - skipping learning"
    ↓
[Gate 3] Planning iterations...
    ↓
[Plan Complete] ✅
```

### Second Planning Request (1 Completed Plan)
```
User: "Japanese pharmaceutical in Vietnam"
    ↓
[Gate 1] Proposal: Entities & Agents
    ↓
[Gate 2] Plan Selection:
    - [ ] Healthcare entering Vietnam (Quality: 7.8)
    - [✓] (auto-selected, similar scenario)
    ↓
[Gate 3] Planning iterations...
    ↓
[Terminal Output]
📌 User selected 1 plans for learning
✅ Analyzed healthcare + vietnam + market_entry pattern
✅ Found 1 relevant learned patterns to apply
    ↓
[Plan Complete] ✅ (better quality due to learned pattern)
```

### Tenth Planning Request (9 Completed Plans)
```
User: "Korean biotech expanding Vietnam ops"
    ↓
[Gate 1] Proposal: Entities & Agents
    ↓
[Gate 2] Plan Selection:
    Available: 9 completed plans
    Quick Options:
    - Skip Learning
    - Recent 3
    - Recent 5
    - Custom Select

    [User clicks "Recent 3"]
    Selected:
    - [✓] Japanese pharmaceutical in Vietnam (8.1)
    - [✓] Healthcare entering Vietnam (7.8)
    - [✓] Biotech market research (7.5)
    ↓
[Gate 3] Planning iterations...
    ↓
[Terminal Output]
📌 User selected 3 plans for learning
✅ Analyzed 3 healthcare + vietnam patterns
✅ Found 3 relevant learned patterns to apply
    ↓
[Plan Complete] ✅ (excellent quality from multiple learned patterns)
```

## Implementation Checklist

- ✅ Added `get_available_plans()` to LearningAnalyzer
- ✅ Added `analyze_selected_plans()` to LearningAnalyzer
- ✅ Updated `get_pattern_context()` to accept selected_plans in PatternRecommender
- ✅ Added `get_available_plans_for_selection()` to PatternRecommender
- ✅ Updated PlannerAgent.generate_strategic_plan() to accept selected_plans
- ⏳ Create `/api/get-available-plans` endpoint in simple_chatbox.py
- ⏳ Update `/api/execute-plan` to accept selected_plans parameter
- ⏳ Add Plan Selection Gate modal to index.html
- ⏳ Test with real planning iterations

## Testing the Feature

### Test 1: Verify Available Plans API

```bash
# After running 3 planning iterations, check:
curl http://localhost:9000/api/get-available-plans

# Should return list of 3 completed plans with metadata
```

### Test 2: Selective Learning

```bash
# Next planning request, specify selected plans:
{
    "goal": "New planning goal",
    "selected_plans": ["plan_1.md", "plan_2.md"]  # Only these
}

# Terminal should show:
# 📌 User selected 2 plans for learning
# ✅ Analyzed 2 patterns
```

### Test 3: Cost Verification

```bash
# Run 10 iterations with 5-plan selection each
# Verify: ~50 pattern analyses instead of ~55
# Cost savings: ~90%
```

## Future Enhancements

1. **Smart Recommendations**
   - "Plans similar to your current goal" (auto-suggest)
   - "Highest quality plans" (filter by score)
   - "Recent plans" (quick option)

2. **Learning Analytics**
   - "Quality improved 15% from these patterns"
   - Show which patterns were actually helpful
   - Track pattern effectiveness per domain

3. **Batch Learning**
   - "Learn from all healthcare plans"
   - "Learn from Vietnam market only"
   - Domain-specific learning modes

4. **Pattern Curation**
   - "Save this as a template for future use"
   - Create custom pattern groups
   - Share patterns across teams

## Summary

This design:
- ✅ Solves the API cost explosion problem
- ✅ Adds more human-in-the-loop control
- ✅ Maintains backward compatibility
- ✅ Improves user understanding
- ✅ Enables future enhancements
- ✅ Keeps proof-of-concept affordable

**Result:** Same learning capability, 90% cost reduction, better UX.

---

*Plan Selection Gate Design - November 2, 2025*
