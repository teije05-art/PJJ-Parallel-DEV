# MCP Planning Tool Timeout - Debugging Report

## Problem Statement

When calling `start_planning_iteration` in Claude Desktop, you receive the error:
```
No result received from client-side tool execution.
```

The tool actually completes successfully (as seen in server logs taking 3-4+ minutes), but Claude Desktop times out waiting for the response.

## Root Cause Analysis

### Issue 1: Web Search Overhead (10-20 seconds)

**Location**: `orchestrator/context_manager.py`, lines 214-229

The context retrieval makes **4 sequential web search requests**:

```python
queries = [
    f"{goal_analysis.industry} market analysis 2025",
    f"{goal_analysis.domain} best practices case studies",
    f"{goal} successful examples",
    f"{goal_analysis.industry} trends statistics"
]

for query in queries:
    results = search.search(query, num_results=3)  # Each ~2-5 seconds
```

**Impact**: Each web search can take 2-5 seconds, totaling 10-20 seconds just for context retrieval.

### Issue 2: Synchronous Agent.chat() Calls (30-90 seconds)

**Location**: Multiple files in `orchestrator/`

The system makes 10+ sequential `agent.chat()` calls that are **fully synchronous and blocking**:

1. **Context Retrieval** (5 calls):
   - Line 104-112: `_retrieve_project_status()`
   - Line 130-139: `_retrieve_successful_patterns()`
   - Line 146-155: `_retrieve_error_patterns()`
   - Line 161-170: `_retrieve_execution_history()`
   - Line 176-189: `_retrieve_agent_performance()`

2. **Agent Workflow** (5+ calls per agent):
   - Planner Agent: generates_strategic_plan() makes 3+ calls
   - Verifier Agent: verify_plan() makes 2+ calls
   - Executor Agent: execute_plan() makes 2+ calls
   - Generator Agent: synthesize_results() makes 2+ calls

Each `agent.chat()` call blocks until MemAgent responds, which can take 5-30 seconds depending on the LLM backend (Fireworks AI on macOS).

**Impact**: 10+ calls × 5-10 seconds = 50-100+ seconds minimum execution time.

## Current Fix Applied

### 1. Disabled Web Search (Temporary)

**File**: `orchestrator/context_manager.py`, lines 191-209

Added an early return that bypasses all web search:

```python
def _retrieve_web_search_results(self, goal: str, goal_analysis) -> str:
    # TEMPORARY FIX: Return early to skip web search while debugging
    print(f"   ⚠️ Web search temporarily disabled for debugging")
    return "Web search disabled (debugging MCP timeout issue)"
```

**Effect**: Removes 10-20 seconds of delay.

### 2. Added Detailed Timing Logs

**File**: `mcp_server/server.py`, lines 308-421

Added timing measurements for each major step:

```python
[STEP 0] start_planning_iteration called...
[STEP 1a] Orchestrator initialized (X.XXs)...
[STEP 1b] Calling _retrieve_enhanced_context...
[STEP 1c] Context retrieved: XXXX chars (X.XXs)
[STEP 2a] Starting 4-agent workflow...
[STEP 2b] 4-agent workflow completed (X.XXs)
...
[COMPLETE] Total time: X.XXs
```

**Effect**: You can now see exactly where the time is being spent by checking the MCP logs.

### 3. Improved Error Handling

**File**: `mcp_server/server.py`, lines 416-421

Added full exception tracing to help diagnose any actual failures:

```python
except Exception as exc:
    import traceback
    print(f"[ERROR] Exception after {total_time:.2f}s: {type(exc).__name__}: {exc}")
    traceback.print_exc()
```

## Testing the Fix

### Step 1: Verify the Changes

The changes have been applied to:
- `/Users/teije/Desktop/memagent-modular-fixed/mem-agent-mcp/orchestrator/context_manager.py`
- `/Users/teije/Desktop/memagent-modular-fixed/mem-agent-mcp/mcp_server/server.py`

### Step 2: Restart Claude Desktop

Close and reopen Claude Desktop to pick up the new MCP server code.

### Step 3: Test the Planning Tool

In Claude Desktop, try:
```
Start a planning iteration for developing a market entry strategy for gleneagles hospital into vietnam
```

### Step 4: Check Logs

Monitor the progress in:
```bash
tail -f ~/Library/Logs/Claude/mcp.log
```

Look for the `[STEP X]` messages and timing information to understand where the time is spent.

## Expected Results After Fix

- **With web search disabled**: 30-60 seconds execution time (should complete)
- **Without fix**: 3-4+ minutes (Claude Desktop times out)
- **Time breakdown** (approximate):
  - Orchestrator init: 2-5 seconds
  - Context retrieval: 5-15 seconds (without web search)
  - 4-agent workflow: 20-40 seconds
  - Output formatting: 1-2 seconds

## Next Steps for Permanent Solution

### Option 1: Keep Web Search Disabled
- Simple fix, fast execution
- Trade-off: Plans won't have current market data
- Easy to implement now, add web search later with timeout

### Option 2: Add Async Web Search
- Properly implement async/await for web search calls
- Add timeout (e.g., 5 seconds per query, skip if timeout)
- Run web search in parallel instead of sequential
- **Recommended**: This gives you fast execution + current data

### Option 3: Add "Fast Mode" Parameter
- Add `use_web_search=False` parameter to `start_planning_iteration`
- Let user choose between speed and data freshness
- Best flexibility

### Option 4: Proper Async/Await Architecture
- Make agent.chat() calls async if possible
- Parallelize context retrieval where safe
- Add proper timeout handling throughout
- **Most complex but most robust**

## Recommended Quick Wins

1. **Test current fix** - Confirm it works with web search disabled
2. **Re-enable web search with timeout** - Add 5-second timeout per query with fallback
3. **Parallelize web searches** - Run 4 queries concurrently instead of sequentially
4. **Cache results** - Cache web search results for repeated goals

## Files Modified

1. `/Users/teije/Desktop/memagent-modular-fixed/mem-agent-mcp/orchestrator/context_manager.py`
   - Disabled `_retrieve_web_search_results()` method

2. `/Users/teije/Desktop/memagent-modular-fixed/mem-agent-mcp/mcp_server/server.py`
   - Added timing measurements
   - Added detailed [STEP X] logging
   - Improved error handling and tracebacks

## How to Re-enable Web Search (Later)

When ready to add web search back, edit `context_manager.py` line 191-209 and uncomment the original code:

```python
def _retrieve_web_search_results(self, goal: str, goal_analysis) -> str:
    try:
        from .search_module import SearchModule
        search = SearchModule()
        # ... rest of original code
    except Exception as e:
        return "Web search failed"
```

Then add timeout handling using `concurrent.futures` or `asyncio` for parallel execution.

## Questions?

If the tool still times out after this fix:
1. Check the [STEP X] logs to see where it gets stuck
2. Share the logs from `~/Library/Logs/Claude/mcp.log`
3. Note the total time reported in [COMPLETE] message

The detailed logging will help us identify if there are other bottlenecks.
