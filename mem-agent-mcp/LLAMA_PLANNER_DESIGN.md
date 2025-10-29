# Llama Planner System Design

**Date:** October 28, 2025
**Phase:** 1 - Foundation
**Status:** Design Document (Implementation Follows)

---

## Overview

This document defines the new Llama Planner system, replacing the rigid orchestrator with intelligent decision-making. Llama becomes the primary decision maker while orchestrator agents become tools that Llama calls as needed.

---

## Core Principles

1. **Llama Decides** - What to search, which agents to call, how to approach the goal
2. **Memory First** - Always search selected entities before going online
3. **Iterative Research** - Web search adapts based on previous results
4. **Approval Before Execution** - Propose approach, get human approval, then execute
5. **Dynamic Agents** - Call agents only when needed, not mandatory sequence
6. **Learn from Outcomes** - Track what approaches work, improve next iteration

---

## System Architecture

### Tools Available to Llama

Llama has access to 6 tools:

#### 1. **Memory Search** (MemAgent)
```
Tool: search_memory(entities: list[str], queries: list[str]) -> dict
Purpose: Search selected entities for relevant information
Returns: {
  "results": str,           # Found content
  "coverage": float,        # 0.0-1.0 (how complete the info is)
  "entities_searched": int, # Number of entities searched
  "gaps": list[str]        # What's missing
}
```

**When Llama uses it:**
- Always FIRST, before any other tool
- Pass selected entities + specific queries about the goal
- Analyze coverage to decide next step

#### 2. **Research Agent** (Iterative Web Search)
```
Tool: research(gaps: list[str], max_iterations: int = 3) -> dict
Purpose: Search online for gaps found in memory, iteratively refines
Returns: {
  "summary": str,           # Research summary
  "sources": list[str],     # URLs found
  "iterations": int,        # How many search iterations completed
  "data_points": list[str]  # Key data/numbers found
}
```

**When Llama uses it:**
- ONLY after memory search
- Pass specific gaps/questions, not generic topics
- ResearchAgent handles iteration internally
- Optimized for finding KEY DATA and NUMBERS

#### 3. **Planner Agent** (Strategic Planning)
```
Tool: call_planner(goal: str, context: str, approach: str) -> dict
Purpose: Generate strategic plan using context and approach
Returns: {
  "plan": str,              # The actual plan
  "methodology": str,       # Approach used
  "key_actions": list[str], # Steps to take
  "dependencies": list[str] # What must happen first
}
```

**When Llama uses it:**
- After gathering memory + research (if needed)
- Pass: goal + collected context + Llama's approach
- e.g., "Create structured plan, use agile methodology"

#### 4. **Verifier Agent** (Plan Validation)
```
Tool: call_verifier(plan: str, context: str, criteria: str) -> dict
Purpose: Validate plan quality and feasibility
Returns: {
  "is_valid": bool,         # Plan is viable
  "quality_score": float,   # 0.0-1.0
  "issues": list[str],      # What needs improvement
  "recommendations": str    # How to improve
}
```

**When Llama uses it:**
- Optional, only if Llama decides plan needs validation
- Pass generated plan + validation criteria

#### 5. **Executor Agent** (Implementation)
```
Tool: call_executor(plan: str, context: str, resources: str) -> dict
Purpose: Implement/execute plan, generate detailed steps
Returns: {
  "implementation": str,    # Detailed execution steps
  "timeline": str,          # How long it takes
  "resources_needed": str,  # What's required
  "success_metrics": str    # How to measure success
}
```

**When Llama uses it:**
- After planning (verified or not, depending on Llama's judgment)
- Pass plan + available resources

#### 6. **Generator Agent** (Synthesis)
```
Tool: call_generator(data: dict, format: str = "summary") -> dict
Purpose: Synthesize results into final output
Returns: {
  "output": str,            # Final synthesized result
  "sources_cited": str,     # Where data came from
  "confidence": float       # 0.0-1.0
}
```

**When Llama uses it:**
- At the end, to synthesize all gathered data
- Optional, only if outputs need synthesis

---

## Workflow: The Planning Loop

### Step 1: Analyze Goal (No Tool Required)

**Llama's internal reasoning:**
```
Read user goal carefully:
  "Create a growth strategy for my SaaS startup for Q1 2025"

Analyze:
  - What is the goal REALLY about? (Growth strategy, SaaS, startup, Q1)
  - What information would be USEFUL? (Market data, competition, past performance, resources)
  - What should come from MEMORY? (Past goals, company data, resources, market analysis)
  - What should come from ONLINE? (Current market trends, competitor analysis, new frameworks)
  - Which AGENTS should help? (Planner for strategy, maybe Verifier, maybe Executor)

NO domain bucketing, NO forcing into categories
Just: What does this goal NEED?
```

### Step 2: Search Memory (Memory Search Tool)

**Llama proposes to itself:**
```
I will search these selected entities:
  - my_startup.md (company info, past goals, resources)
  - market_analysis.md (previous market research)
  - q4_2024_results.md (past performance)

Looking for:
  - Current company metrics (ARR, MRR, customer count)
  - Past growth strategies (what worked, what didn't)
  - Available resources (team, budget)
  - Market position (competitors, market size)
```

**Tool call:**
```python
memory_results = search_memory(
  entities=["my_startup", "market_analysis", "q4_2024_results"],
  queries=[
    "Current ARR, MRR, customer metrics",
    "Past growth strategies and results",
    "Available budget and team resources",
    "Current market position and competitors"
  ]
)
```

**Analyze results:**
```
Found:
  - ✅ Company metrics (ARR $250K, 50 customers)
  - ✅ Past strategy (tried cold outreach, 2% conversion)
  - ✅ Available budget ($50K for Q1)
  - ❌ Current competitor analysis (outdated, from Q3 2024)
  - ❌ Market trends (no recent data)

Coverage: 60% - Good foundation, need online research for competition + trends
```

### Step 3: Propose Approach (To Human)

**Llama generates approach proposal:**

```
Based on my analysis, here's how I'll help with your growth strategy:

PROPOSED APPROACH:
─────────────────

Memory Foundation (60%):
  • Starting metrics: ARR $250K, 50 customers
  • What worked: Inbound marketing performed better than cold outreach
  • Available: $50K budget + 1 marketing person + 1 engineer

Research Gaps (40%):
  • Current competitor analysis (last data was Sept 2024)
  • New market trends in SaaS growth (Q4 2024 - Q1 2025)
  • Latest growth frameworks (PLG, hybrid sales/product)

AGENTS I'LL USE:
  1. Research Agent → Iteratively find competitor data + market trends
  2. Planner Agent → Create strategic growth plan for Q1
  3. Verifier Agent → Validate plan against your constraints
  4. Generator Agent → Synthesize final strategy

ESTIMATED RESOURCE COST:
  • API calls: ~5-8 web searches (iterative)
  • Processing time: ~2-3 minutes
  • Token usage: ~15K tokens

APPROVAL REQUEST:
  ✓ Approve this approach
  ✗ Reject and propose different approach
  ? Adjust (specify what to change)
```

**User approves, rejects, or adjusts.**

### Step 4: Execute Approved Approach

**If approved, Llama executes:**

```
Step 1: Iterative Research
  - Search: "SaaS growth trends Q1 2025"
    → Find: Product-led growth rising, AI-powered sales trending
    → Generate next search: "PLG strategies for B2B SaaS"
  - Search: "Top SaaS competitors in [category] 2025"
    → Find: Competitor X using PLG, Competitor Y with AI
    → Generate next search: "PLG SaaS case studies Q1 2025"
  - Research complete: Found key trends + competitor moves

Step 2: Call Planner Agent
  context = {
    memory: {
      current_metrics: "ARR $250K, 50 customers",
      past_strategy: "Inbound worked better (12% vs 2%)",
      budget: "$50K",
      team: "1 marketing, 1 engineer"
    },
    research: {
      trends: "PLG is rising, AI-powered sales emerging",
      competitors: "Competitor X: PLG model, Competitor Y: AI sales"
    }
  }

  plan = call_planner(
    goal="Create growth strategy for Q1 2025",
    context=json.dumps(context),
    approach="Hybrid PLG + inbound (focus on PLG since it's trending)"
  )

Step 3: Call Verifier Agent
  verification = call_verifier(
    plan=plan,
    context=context,
    criteria="Realistic with $50K budget, 1 marketing person"
  )

  If not valid, suggest improvements, replan if needed

Step 4: Call Generator Agent
  final_strategy = call_generator(
    data={
      plan: plan,
      verification: verification,
      memory: context,
      research: research_results
    },
    format="executive_summary"
  )

  → Returns: Final growth strategy document

Step 5: Save to Memory
  - Update my_startup.md with new strategy
  - Create q1_2025_growth_strategy.md with full plan
  - Log approach used + feedback for learning
```

### Step 5: Learning & Feedback

**After plan is delivered:**

```
LEARNING CAPTURE:
  Goal: "Create growth strategy for Q1 2025"
  Approach Used:
    - Memory: 60% (company data, past strategies)
    - Research: 40% (market trends, competitor analysis)
    - Agents: Planner → Verifier → Generator

  User Feedback: (1-5 stars)
    Rating: ⭐⭐⭐⭐ (4 stars)
    Why: "Great competitive analysis, budget seems realistic"

  Outcome: "Success - Strategy approved and moving to implementation"

PATTERN LEARNED:
  For goal_type="growth_strategy":
    - Effective approach: 60% memory + 40% research
    - Best agents: Planner → Verifier → Generator
    - Typical quality: 4-4.5 stars

  Next time similar goal appears:
    → Use same approach ratio + agent sequence
    → Skip agents if not needed
```

---

## Entity Selection UI Integration

**In simple_chatbox.py:**

```
┌─────────────────────────────────────────┐
│ Entity Selector (Checkbox List)         │
├─────────────────────────────────────────┤
│ ☑ my_startup.md                        │
│ ☑ market_analysis.md                   │
│ ☑ q4_2024_results.md                   │
│ ☐ customer_feedback.md                 │
│ ☐ team_members.md                      │
│ ☐ competitor_analysis.md (outdated)    │
│                                         │
│ [Save Selection] [Clear] [View All]   │
└─────────────────────────────────────────┘

User: "Create growth strategy for Q1 2025"

[Selected entities shown above search ↑]

Llama response:
  "I'll search the selected entities you chose..."
```

**Persistent selection:**
- User selects entities once
- Stays selected for multiple goals
- Can be changed anytime

---

## Approval Gate UI Integration

**In simple_chatbox.py:**

```
┌──────────────────────────────────────────┐
│ LLAMA'S PROPOSED APPROACH                │
├──────────────────────────────────────────┤
│                                          │
│ Memory Foundation (60%):                 │
│  • Company metrics: ✓ Found              │
│  • Growth history: ✓ Found               │
│  • Resources: ✓ Found                    │
│                                          │
│ Research Gaps (40%):                     │
│  • Competitor analysis: Needs search     │
│  • Market trends: Needs search           │
│                                          │
│ AGENTS TO USE:                           │
│  1. ResearchAgent (iterative search)     │
│  2. PlannerAgent (create strategy)       │
│  3. VerifierAgent (validate plan)        │
│  4. GeneratorAgent (synthesize)          │
│                                          │
│ RESOURCE COST:                           │
│  • API calls: ~5-8 web searches         │
│  • Time estimate: 2-3 minutes            │
│  • Tokens: ~15K                          │
│                                          │
│ [✓ APPROVE] [✗ REJECT] [? ADJUST]      │
│                                          │
│ If adjusting, specify:                   │
│ ┌──────────────────────────────────────┐ │
│ │ e.g., "Skip web search, use only     │ │
│ │ memory" or "Add customer feedback    │ │
│ │ entity to search"                    │ │
│ └──────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

---

## System Prompt for Llama (The Core)

This is what Llama will be given:

```
You are Llama 3.3 70B, a strategic planning agent.

YOUR ROLE:
You analyze user goals and create detailed plans. You have access to:
  1. Memory (selected entities)
  2. Web search (iterative, for specific data)
  3. Planning agents (Planner, Verifier, Executor, Generator)

YOUR WORKFLOW:
1. Read the goal carefully
2. Analyze: What information exists in memory? What's missing?
3. Search memory (the selected entities)
4. Evaluate: Is memory sufficient (>70%)? Or do you need research?
5. Propose approach to human:
   - Breakdown: X% memory + Y% research
   - Agents you'll use
   - Resource cost estimate
   - Ask for approval
6. Execute approved approach:
   - Iteratively search for missing data
   - Call planning agents as needed
   - Synthesize results
7. Learn: Capture outcome and feedback

KEY PRINCIPLES:
- ALWAYS search selected memory entities FIRST
- Don't force goals into categories or domains
- Call agents only when you need them (not all 4 every time)
- Iterative web search: each search informs the next
- Approval gates prevent wasted resources
- Learn from what works

AVAILABLE TOOLS:
- search_memory(entities, queries) - Search selected entities
- research(gaps, max_iterations) - Iterative web search
- call_planner(goal, context, approach) - Strategic planning
- call_verifier(plan, context, criteria) - Plan validation
- call_executor(plan, context, resources) - Implementation details
- call_generator(data, format) - Synthesize results

CRITICAL GUIDELINES:
- You must propose your approach and wait for approval before using research/agents
- Specify which entities you're searching and what you're looking for
- Be specific with web search queries (look for data/numbers, not generic info)
- Only call agents Llama determines necessary
- Track coverage: what % of goal is covered by memory vs research
- Always ask: "Do I need all 4 agents, or just some?"

RESPONSE FORMAT:
When analyzing a goal:
  1. <analyze>
     - What is this goal really asking?
     - What info exists in memory?
     - What gaps exist?
     - Which agents will help?
     </analyze>

  2. <propose>
     - Breakdown: X% memory + Y% research
     - Entities I'll search
     - Web search focus (if needed)
     - Agents I'll use + order
     - Resource estimate
     - Awaiting approval...
     </propose>

  After approval, execute and return results.
```

---

## File Changes Summary

**Create (New Files):**
- `llama_planner.py` - Core planner orchestration
- `research_agent.py` - Iterative web search agent
- `learning_tracker.py` - Learning/feedback logging
- `llama_planner_prompt.txt` - System prompt above

**Modify:**
- `simple_chatbox.py` - Add entity selector + approval UI
- `agent/agent.py` - Expose search_memory interface for Llama

**Keep (Unchanged):**
- `orchestrator/agents/*.py` - Planner, Verifier, Executor, Generator
- All existing agent logic

**Delete (Later, after Phase 1 validation):**
- `orchestrator/simple_orchestrator.py`
- `orchestrator/workflow_coordinator.py`
- `orchestrator/domain_templates.py`
- `orchestrator/context_manager.py`

---

## Implementation Checklist - Phase 1

- [ ] Create `llama_planner_prompt.txt` with detailed system prompt
- [ ] Create `research_agent.py` for iterative web search
- [ ] Create `llama_planner.py` orchestration logic
- [ ] Create `learning_tracker.py` for logging approaches + outcomes
- [ ] Modify `simple_chatbox.py` with entity selector UI
- [ ] Modify `simple_chatbox.py` with approval gate UI
- [ ] Add `search_memory()` interface to agent
- [ ] Test Phase 1 end-to-end (goal → proposal → approval → execution)
- [ ] Validate learning tracker captures correct data
- [ ] Document approval workflow for users

---

## Success Criteria (Phase 1)

✅ Llama proposes approach before execution (not automatic)
✅ Approval gate prevents wasted resources
✅ Entity selection works persistently
✅ Iterative web search finds relevant data
✅ Learning tracker captures approach + outcome
✅ System demonstrates more specific/targeted plans than before
✅ All existing agents still work when called
✅ No regression in core memory functionality

