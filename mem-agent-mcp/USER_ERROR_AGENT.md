# UserErrorAgent - Alternative Problem-Solving from User Perspective

**Purpose:** When stuck in error loops, provide alternative hypotheses and solutions aligned with user's intuition and project knowledge rather than following assumed debugging patterns.

**Trigger:** User invokes this explicitly when feeling that Claude's investigation direction is missing something or contradicting user's own insights.

---

## Learned Error Patterns

### Pattern 1: Frontend-Backend Data Flow Issues (Oct 29, 2025)

**Context:**
- User was debugging why multi-iteration planning wasn't executing
- System was stuck executing single-iteration (OPTION C) despite fixes

**User's Intuition:**
- "it is still not running multiple iterations/loops... there are still errors"
- User suspected: **Frontend is not sending parameters to backend**

**Claude's Initial Response:**
- ❌ Investigated string division errors in Python code
- ❌ Fixed Path object issues in agent initialization
- ❌ Analyzed backend routing logic (which was actually correct)
- ❌ Concluded: "System is executing OPTION C (single iteration)" but didn't immediately identify root cause
- ❌ When asked to "Use CodebaseAgent, ErrorAgent, ArchitectureAgent", finally discovered the real issue

**Root Cause (Found on 2nd Deep Analysis):**
- **JavaScript frontend was NOT sending `max_iterations` and `checkpoint_interval` to `/api/execute-plan`**
- Backend had perfect routing: `if request.max_iterations > 1: route_to_multi_iteration()`
- But request.max_iterations was never set, so defaulted to 1
- Result: `1 > 1` = False, always executed single-iteration

**Lesson Learned:**
When debugging data flow between frontend and backend, **check the actual HTTP request body being sent** before investigating backend logic. The frontend JavaScript is often the culprit when parameters mysteriously disappear.

**How to Avoid This Pattern:**
1. When user suspects frontend-backend communication issues, **believe them** - they often have intuition about their codebase
2. Before analyzing backend routing/logic, verify:
   - Does the HTTP request body include the parameter?
   - Is the JavaScript actually sending it?
   - Is it being stored in the right variable?
   - Is it being passed to fetch() call?
3. Add console.log or network inspector analysis FIRST, not last

---

## How to Use This Agent

### When to Call It:
- Error loop detected (same error appearing multiple times)
- Claude's debugging direction feels off
- User has intuition that contradicts Claude's analysis
- Multiple layers of investigation haven't found root cause

### Example Call:
```
Use UserErrorAgent to identify if there's an alternative explanation
for why multi-iteration isn't triggering. What would the user suspect
that Claude might have missed?
```

### What It Should Do:
1. Surface user's original intuition ("I think it's frontend-backend")
2. Check if that intuition was dismissed too quickly
3. Provide alternative hypotheses that align with user's thinking
4. Look for simple explanations before complex ones
5. Consider the user's project knowledge as a valuable signal

---

## Future Pattern Recognition

This agent should grow with each issue where user intuition proved correct:
- [ ] Frontend-backend data flow issues (DOCUMENTED)
- [ ] (Future patterns to be added)

