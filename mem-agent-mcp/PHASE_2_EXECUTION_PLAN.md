# Phase 2: Fireworks Function Calling & Full Planning Execution

**Date:** October 28, 2025
**Objective:** Implement Fireworks API integration to enable Llama's intelligent decision-making through function calling

---

## Phase 2 Overview

Phase 1 gave us the UI and basic endpoints. Phase 2 connects everything by:

1. **Calling Fireworks API** with Llama's system prompt and function definitions
2. **Handling Llama's function calls** (search_memory, research, call_planner, etc.)
3. **Executing tools** and returning results to Llama
4. **Showing approval gate** when Llama proposes an approach
5. **Continuing execution** after user approval
6. **Logging outcomes** for the learning system

---

## How Fireworks Function Calling Works

### Request Flow
```
Client sends:
  • messages (conversation history)
  • system prompt (role definition)
  • tools (list of available functions)
  • tool_choice: "auto" (let Llama decide)
        ↓
Fireworks/Llama processes:
  • Analyzes user message
  • Decides which tool to call (if any)
  • Generates tool_calls array
        ↓
Response contains:
  • Either: text response (no tool call)
  • Or: tool_calls array with function name + arguments
```

### Response Structure
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "I will search your memory for...",
      "tool_calls": [
        {
          "id": "call_123",
          "type": "function",
          "function": {
            "name": "search_memory",
            "arguments": "{\"entities\": [\"company_metrics\"], \"queries\": [\"current ARR\"]}"
          }
        }
      ]
    }
  }]
}
```

### Tool Call Execution Loop
```
1. Call Fireworks with function calling enabled
2. Get response with potential tool_calls
3. For each tool_call:
   a. Parse function name and arguments
   b. Execute the tool (search_memory, research, etc.)
   c. Get result
   d. Add to messages: {"role": "tool", "tool_call_id": "...", "content": result}
4. Call Fireworks again with updated messages
5. Repeat until Llama says "I'm done" (no more tool calls)
```

---

## Phase 2 Components to Build

### A. Fireworks API Wrapper (`fireworks_wrapper.py`)

**Purpose:** Encapsulate Fireworks API communication with function calling support

**Key Functions:**
```python
async def call_fireworks_with_tools(
    messages: List[Dict],
    system_prompt: str,
    tools: List[Dict],
    max_turns: int = 5
) -> Dict:
    """
    Call Fireworks API with function calling.

    Returns:
    - final_text: Last text response from Llama
    - tool_calls_made: List of all tool calls executed
    - results: Results from each tool call
    - iterations: Number of API calls made
    """
```

**What It Does:**
1. Makes HTTP POST to Fireworks API
2. Handles authentication (API key from env)
3. Processes tool_calls from response
4. Routes to tool executor
5. Feeds results back to Llama
6. Continues loop until Llama is done
7. Returns comprehensive execution summary

**Error Handling:**
- Graceful Fireworks API failures
- Timeout handling
- Invalid function names
- Argument parsing errors
- Max iterations exceeded

---

### B. Tool Executor (`tool_executor.py`)

**Purpose:** Execute tools that Llama calls via function calling

**Functions to Implement:**
```python
async def execute_tool(tool_name: str, arguments: Dict, context: Dict) -> str:
    """
    Execute a tool and return result as string.

    tool_name: One of: search_memory, research, call_planner,
                       call_verifier, call_executor, call_generator
    arguments: JSON-parsed arguments from Llama
    context: {agent, memory_path, planner, selected_entities, ...}

    Returns: JSON string with result
    """
```

**Tools to Implement:**

1. **search_memory(entities, queries)**
   - Calls planner.search_memory(selected_entities, queries)
   - Returns: {coverage: %, content: "...", gaps: [...]}

2. **research(gaps, max_iterations)**
   - Calls research_agent.research(gaps, max_iterations)
   - Returns: {summary: "...", sources: [...], data_points: [...], coverage: %}

3. **call_planner(goal, context, approach)**
   - Calls PlannerAgent with goal + context
   - Returns: {plan: "...", reasoning: "..."}

4. **call_verifier(plan, context, criteria)**
   - Calls VerifierAgent to validate plan
   - Returns: {is_feasible: bool, feedback: "..."}

5. **call_executor(plan, context, resources)**
   - Calls ExecutorAgent for implementation details
   - Returns: {steps: [...], timeline: "..."}

6. **call_generator(data, format)**
   - Calls GeneratorAgent to synthesize results
   - Returns: {output: "...", format: str}

---

### C. Approval Gate Handler

**Purpose:** Pause execution, show approval UI, handle user decision

**Flow:**
```python
# When Llama proposes an approach, pause and wait for approval
if message_contains("I propose..."):
    # Extract approach details
    approach = parse_approach_from_message(llama_response)

    # Return to frontend asking to show approval gate
    return {
        "status": "awaiting_approval",
        "approach": approach,
        "goal": goal,
        "memory_results": memory_results
    }

# Frontend shows approval gate modal
# User clicks approve/reject/adjust

# Backend receives decision via /api/approve-approach
if approval_status == "approved":
    continue_execution()  # Resume from where we paused
elif approval_status == "rejected":
    return error_message()
elif approval_status == "adjusted":
    feed_adjustment_back_to_llama()
```

---

### D. Main `/api/execute-plan` Endpoint

**Purpose:** Orchestrate the entire planning flow

**Flow:**
```python
@app.post("/api/execute-plan")
async def execute_plan(request: ExecutePlanRequest):
    """
    Execute planning with Llama decision-making.

    Flow:
    1. Initialize LlamaPlanner
    2. Load system prompt
    3. Call Fireworks with function calling
    4. Execute tool calls in loop
    5. When approach is proposed, pause for approval
    6. Continue after user approval
    7. Log final outcome
    8. Return comprehensive results
    """

    session_id, session = get_or_create_session(request.session_id)
    agent = session["agent"]

    # Initialize planner
    planner = LlamaPlanner(agent, get_memory_path())

    # Load system prompt
    system_prompt = load_system_prompt()  # From llama_planner_prompt.txt

    # Get tools definitions
    tools = get_tool_definitions()

    # Initial message to Llama
    messages = [
        {"role": "user", "content": f"""
        Goal: {request.goal}
        Selected memory entities: {', '.join(request.selected_entities)}

        Please analyze this goal and propose your approach.
        """}
    ]

    # Call Fireworks with function calling
    try:
        response = await call_fireworks_with_tools(
            messages=messages,
            system_prompt=system_prompt,
            tools=tools,
            agent=agent,
            planner=planner,
            selected_entities=request.selected_entities
        )

        # Extract proposal from response
        approach = extract_approach(response)
        memory_results = response.get("memory_results", {})

        # Return for approval gate
        return {
            "status": "awaiting_approval",
            "session_id": session_id,
            "goal": request.goal,
            "approach": approach,
            "memory_results": memory_results
        }

    except Exception as e:
        return {
            "status": "error",
            "session_id": session_id,
            "error": str(e)
        }
```

---

## Implementation Steps

### Step 1: Create `fireworks_wrapper.py` (90 min)

**Structure:**
```python
import os
import asyncio
import httpx
from typing import List, Dict, Optional, Any

class FireworksClient:
    """Wrapper for Fireworks API with function calling support."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FIREWORKS_API_KEY")
        self.base_url = "https://api.fireworks.ai/inference/v1"
        self.model = "accounts/fireworks/models/llama-v3p3-70b-instruct"

    async def call_with_tools(
        self,
        messages: List[Dict],
        system_prompt: str,
        tools: List[Dict],
        max_turns: int = 5
    ) -> Dict:
        """
        Call Fireworks with function calling.

        Returns:
        {
            "final_text": str,
            "tool_calls_executed": int,
            "all_results": List[Dict],
            "messages": List[Dict],  # Full conversation
            "status": "success" | "error"
        }
        """

        # Prepare initial conversation
        conversation = []
        conversation.append({"role": "system", "content": system_prompt})
        conversation.extend(messages)

        results = []
        turn = 0

        while turn < max_turns:
            # Make API call
            response = await self._call_fireworks(
                messages=conversation,
                tools=tools
            )

            # Check for tool calls
            if response.get("tool_calls"):
                # Execute tools and add to conversation
                for tool_call in response["tool_calls"]:
                    result = await execute_tool(
                        tool_call["function"]["name"],
                        json.loads(tool_call["function"]["arguments"])
                    )
                    results.append({
                        "tool": tool_call["function"]["name"],
                        "result": result
                    })

                    # Add assistant message with tool calls
                    conversation.append({
                        "role": "assistant",
                        "content": response["text"],
                        "tool_calls": response["tool_calls"]
                    })

                    # Add tool result
                    conversation.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result
                    })
            else:
                # Llama is done with tools
                return {
                    "final_text": response["text"],
                    "tool_calls_executed": len(results),
                    "all_results": results,
                    "messages": conversation,
                    "status": "success"
                }

            turn += 1

        return {
            "final_text": conversation[-1].get("content", ""),
            "tool_calls_executed": len(results),
            "all_results": results,
            "messages": conversation,
            "status": "max_turns_exceeded"
        }

    async def _call_fireworks(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """Make actual API call to Fireworks."""
        # Implementation details...
```

### Step 2: Create `tool_executor.py` (60 min)

**Structure:**
```python
async def execute_tool(
    tool_name: str,
    arguments: Dict,
    context: Dict  # {agent, planner, selected_entities, memory_path}
) -> str:
    """Route to appropriate tool handler."""

    if tool_name == "search_memory":
        return await handle_search_memory(arguments, context)
    elif tool_name == "research":
        return await handle_research(arguments, context)
    elif tool_name == "call_planner":
        return await handle_call_planner(arguments, context)
    # ... etc
    else:
        raise ValueError(f"Unknown tool: {tool_name}")

async def handle_search_memory(args: Dict, context: Dict) -> str:
    """Execute search_memory tool."""
    planner = context["planner"]
    entities = args.get("entities", [])
    queries = args.get("queries", [])

    results = planner.search_memory(entities, queries)

    return json.dumps({
        "coverage": results.get("coverage", 0),
        "content": results.get("content", ""),
        "gaps": results.get("gaps", []),
        "sources": results.get("sources", [])
    })

async def handle_research(args: Dict, context: Dict) -> str:
    """Execute research tool."""
    # Call ResearchAgent...

async def handle_call_planner(args: Dict, context: Dict) -> str:
    """Execute call_planner tool."""
    # Call PlannerAgent...
```

### Step 3: Modify `/api/execute-plan` (120 min)

**Add to simple_chatbox.py after `/api/approve-approach` endpoint**

**Key aspects:**
1. Initialize LlamaPlanner with agent and memory_path
2. Load llama_planner_prompt.txt as system prompt
3. Get tool definitions
4. Create initial message with goal + selected entities
5. Call Fireworks with function calling
6. Parse response for approval gate data
7. Return with status "awaiting_approval"

**After user approves:**
1. Resume conversation at approval point
2. Continue calling Fireworks for additional tool calls
3. Collect all results
4. Call LearningTracker to log outcome
5. Return final plan to frontend

### Step 4: Continuation Endpoint (30 min)

**New endpoint: POST `/api/continue-plan`**

Purpose: Handle post-approval execution continuation

```python
@app.post("/api/continue-plan")
async def continue_plan(request: ContinuePlanRequest):
    """
    Continue planning after user approval.

    Resume the conversation and execute remaining steps.
    """
    # Get session
    # Restore conversation state
    # Resume Fireworks calls
    # Execute remaining tools
    # Log final outcome
    # Return results
```

---

## Key Design Decisions

### 1. Async/Await Pattern
- All Fireworks API calls are async
- Tool execution is async-compatible
- Prevents blocking during network I/O

### 2. Message Format
- Follow OpenAI format (compatible with Fireworks)
- System prompt + user message + assistant response
- Tool calls embedded in messages
- Tool results as {"role": "tool", ...}

### 3. Approval Gate Timing
- Pause BEFORE execution begins
- Show Llama's proposed approach to user
- Continue from exact point after approval
- Preserve full conversation context

### 4. Error Handling
- Fireworks API errors caught and reported
- Tool execution errors converted to tool results
- Max iterations prevents infinite loops
- Graceful degradation

### 5. Learning Integration
- Every execution logs to LearningTracker
- Tracks: goal_type, approach_ratio, agents_used, rating
- Enables future recommendations

---

## Testing Strategy

### Unit Tests
- [ ] Fireworks wrapper initialization
- [ ] Message formatting for function calling
- [ ] Tool call parsing
- [ ] Tool executor routing

### Integration Tests
- [ ] Full flow: goal → Fireworks → tools → completion
- [ ] Approval gate pause/resume
- [ ] Memory search execution
- [ ] Research execution
- [ ] Agent calls

### End-to-End Tests
- [ ] User selects entities
- [ ] User enters goal
- [ ] Approval gate shows correct data
- [ ] User approves
- [ ] Plan execution completes
- [ ] Results displayed
- [ ] Outcome logged

### Edge Cases
- [ ] No entities selected
- [ ] Goal with no gaps (all from memory)
- [ ] Goal requiring research
- [ ] Fireworks API timeout
- [ ] Tool execution failure
- [ ] User rejection

---

## Success Criteria

✅ Fireworks function calling integration works
✅ Llama makes intelligent tool decisions
✅ Tools execute and return results
✅ Approval gate pauses/resumes execution
✅ Memory-first pattern followed
✅ Results fed back to Llama correctly
✅ Outcomes logged for learning
✅ No regressions to Phase 1
✅ Error handling comprehensive
✅ Full end-to-end flow works

---

## Files to Create/Modify

### New Files:
- `fireworks_wrapper.py` (200+ lines)
- `tool_executor.py` (250+ lines)
- `PHASE_2_EXECUTION_PLAN.md` (this file)

### Modified Files:
- `simple_chatbox.py` (add `/api/execute-plan` and `/api/continue-plan`)

### No Changes Needed:
- Phase 1 files remain unchanged
- Existing endpoints unchanged
- llama_planner.py, research_agent.py, learning_tracker.py unchanged

---

## Timeline Estimate

- **Design & Planning:** 30 min ✅ (This document)
- **Fireworks Wrapper:** 90 min
- **Tool Executor:** 60 min
- **Execute-Plan Endpoint:** 120 min
- **Continue-Plan Endpoint:** 30 min
- **Testing:** 90 min
- **Bug Fixes & Polish:** 60 min
- **Total: ~7.5 hours**

---

## Next: Implementation

Ready to start Phase 2A - Create Fireworks API wrapper?

