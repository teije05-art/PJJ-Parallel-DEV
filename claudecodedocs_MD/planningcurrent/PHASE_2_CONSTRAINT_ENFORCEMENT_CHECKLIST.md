# PHASE 2 CONSTRAINT ENFORCEMENT CHECKLIST

**Document Purpose**: Comprehensive checklist of ALL constraint validation points in Phase 2 tax workflow implementation.

**Critical Intent**: Prevent recreation of old system's MemAgent search autonomy issues.

---

## SEGMENT 1: AGENT-LEVEL CONSTRAINTS

### RequestCategorizer (Step 1) - CATEGORIZATION AGENT

- [ ] **Input validation**: Request must be ≥10 characters
- [ ] **Output validation**: Must return suggested_categories list
- [ ] **Error handling**: Return empty list if request too short
- [ ] **No MemAgent search**: Agent does not access memory (no constraint segments)
- [ ] **Metadata**: Returns {"confidence": float, "reasoning": str}
- [ ] **Docstring**: Documents that output becomes user boundary for downstream

### TaxResponseSearcher (Step 2) - PAST RESPONSE SEARCH

- [ ] **Constraint 1 - Categories Required**: Check `if not categories: return error`
- [ ] **Constraint 2 - Explicit Segments**: Use ONLY `segments=[0, 1, 2, 3]` (no other)
- [ ] **Constraint 3 - Segment Immutability**: Add comment `# [0,1,2,3] - EXPLICIT CONSTRAINT`
- [ ] **Constraint 4 - Query Decoration**: Include CONSTRAINT comment in query
  - [ ] Query string starts with: "CONSTRAINT: Search ONLY within these user-selected categories:"
  - [ ] Lists confirmed categories
  - [ ] Includes: "Do NOT search beyond these specified categories"
- [ ] **Constraint 5 - Result Filtering**: Filter results by user categories
  - [ ] `filtered = [r for r in results if r["category"] in categories]`
- [ ] **Constraint 6 - Metadata Tracking**: Return constraint metadata
  - [ ] `"category_constraint_boundary": categories`
  - [ ] `"segments_accessed": [0, 1, 2]`
  - [ ] `"results_filtered_by_category": count`
- [ ] **Error Cases**: Return AgentResult(success=False) with error message
- [ ] **Minimum Similarity**: Apply threshold (0.60) before returning

### FileRecommender (Step 4) - TAX DATABASE SEARCH

- [ ] **Constraint 1 - Categories Required**: Check `if not categories: return error`
- [ ] **Constraint 2 - Explicit Segments**: Use ONLY `segments=[4, 5, 6, 7, 8, 9, 10, 11]` (no other)
- [ ] **Constraint 3 - Segment Immutability**: Add comment `# [4-11] - EXPLICIT CONSTRAINT`
- [ ] **Constraint 4 - Query Decoration**: Include CONSTRAINT comment in query
  - [ ] Query string starts with: "CONSTRAINT: Search ONLY within these user-selected categories:"
  - [ ] Lists confirmed categories
  - [ ] Includes: "Do NOT search beyond these specified categories"
- [ ] **Constraint 5 - Result Filtering**: Filter results by user categories
  - [ ] `filtered = [r for r in results if any(cat in r["metadata"]["categories"] for cat in categories)]`
- [ ] **Constraint 6 - Metadata Tracking**: Return constraint metadata
  - [ ] `"category_constraint_boundary": categories`
  - [ ] `"segments_accessed": [3, 4, 5, 6, 7, 8, 9]`
  - [ ] `"search_scope": "tax_database (CONSTRAINT: segments [3-9] only)"`
- [ ] **Error Cases**: Return AgentResult(success=False) with error message
- [ ] **Minimum Relevance**: Apply threshold (0.55) before returning

### TaxResponseCompiler (Step 5) - RESPONSE SYNTHESIS

- [ ] **Constraint 1 - Source-Only Enforcement**: Prompt includes CRITICAL CONSTRAINT section
  - [ ] "MUST ONLY use information from SOURCE DOCUMENTS provided below"
  - [ ] "MUST NOT use external knowledge"
  - [ ] "EVERY statement must be sourced to a specific document"
  - [ ] "If information is not in sources, state 'Source does not address this issue'"
  - [ ] "Violation of these constraints will result in hallucinations"
- [ ] **Constraint 2 - Citation Requirement**: Prompt includes citation instructions
  - [ ] Use format: "According to [Document Name] (Page X)..."
  - [ ] "Use source citations liberally - citation shows constraint adherence"
- [ ] **Metadata**: Return token counts and files_used count
- [ ] **Error Handling**: Return error if no files provided

### DocumentVerifier (Step 6a) - VERIFICATION GATE

- [ ] **Constraint 1 - Source Verification Only**: Verify AGAINST provided_documents only
- [ ] **Constraint 2 - Hallucination Detection**: Flag unsourced claims
- [ ] **Constraint 3 - Quality Threshold**: Report percentage of unverified claims
- [ ] **Constraint 4 - Explicit Sources**: Compare against exact provided files only
- [ ] **Metadata**: Return verification_report with issues list
- [ ] **Error Cases**: Never approve if verification fails

### CitationTracker (Step 6b) - CITATION EMBEDDING

- [ ] **Constraint 1 - Source Citation Only**: Cite ONLY provided documents
- [ ] **Constraint 2 - Accuracy**: Every citation must reference actual document
- [ ] **Constraint 3 - Completeness**: Major claims should have citations
- [ ] **Metadata**: Return citation list with source + location
- [ ] **Error Handling**: Return error if citation matching fails

---

## SEGMENT 2: ORCHESTRATOR-LEVEL CONSTRAINTS

### TaxOrchestrator Memory Management

- [ ] **Single Save Point Enforcement**:
  - [ ] ONLY `_save_approved_response()` saves responses
  - [ ] NO individual agents call save()
  - [ ] NO Streamlit UI calls save()
  - [ ] NO multiple save locations
- [ ] **Save Method Comment**: Documents "ONLY save point" principle

### TaxOrchestrator Step Execution

- [ ] **Step 1 Comment**: Documents categories become boundary
- [ ] **Step 2 Comment**: Documents "Searches ONLY segments [0,1,2], filters by category"
- [ ] **Step 3 Comment**: Documents user selection boundary
- [ ] **Step 4 Comment**: Documents "Searches ONLY segments [3-9], filters by category"
- [ ] **Step 5 Comment**: Documents source-only constraint
- [ ] **Step 6 Comment**: Documents verification + source-only constraint

### TaxOrchestrator Constraint Passing

- [ ] **Step 2 Execution**: Passes `categories=session.confirmed_categories`
- [ ] **Step 4 Execution**: Passes `categories=session.confirmed_categories`
- [ ] **Step 5 Execution**: Passes `selected_file_contents` only (no MemAgent search)
- [ ] **Step 6 Execution**: Passes `selected_file_contents` only
- [ ] **Error Handling**: All steps validate constraints before execution

### TaxOrchestrator Learning Integration

- [ ] **Learning Metadata Includes**:
  - [ ] `"categories": confirmed_categories`
  - [ ] `"constraint_boundary": {...}` object with all boundaries
  - [ ] `"past_responses_segments": [0, 1, 2, 3]`
  - [ ] `"tax_database_segments": [4, 5, 6, 7, 8, 9, 10, 11]`
  - [ ] `"category_filter": confirmed_categories`
  - [ ] `"document_source_only": True`

---

## SEGMENT 3: UI-LEVEL CONSTRAINTS

### Streamlit Session State

- [ ] **State Variables Defined**:
  - [ ] `"session_id"` - Unique per session
  - [ ] `"user_id"` - Unique per user
  - [ ] `"confirmed_categories"` - USER BOUNDARY (marked in code)
  - [ ] `"selected_documents"` - USER BOUNDARY (marked in code)
  - [ ] `"approval_status"` - USER BOUNDARY (marked in code)
  - [ ] All other variables marked as "Agent output" (not user boundary)
- [ ] **Isolation**: Per-user + per-session files saved to `/local-memory/users/{user_id}/sessions/{session_id}.json`

### Screen 2: Category Confirmation

- [ ] **Button Guard**: `if not confirmed_categories: st.error("Please select...")`
- [ ] **Search Block**: Search buttons disabled until categories confirmed
- [ ] **Docstring**: Documents that user confirmation is REQUIRED before searches

### Screen 4: Document Selection

- [ ] **Selection Enforcement**: User MUST select documents before synthesis
- [ ] **Button Guard**: `if not selected_documents: st.error("Please select...")`
- [ ] **Error Handling**: Prevents proceeding without explicit user selection

### Screen 6: Approval Gate

- [ ] **Final Boundary**: Only partner can approve
- [ ] **Read-Only Display**: Response displayed read-only (no editing)
- [ ] **Verification Report**: Shows issues (if any)
- [ ] **Single Choice**: Approve or Reject (no other options)

---

## SEGMENT 4: MEMAGENT MEMORY CONSTRAINTS

### Segment Allocation Enforcement

- [ ] **Segment [0-3] Locked** (Past Responses - Read-Only + Write on Approval):
  - [ ] ONLY TaxResponseSearcher searches these
  - [ ] ONLY TaxOrchestrator writes to segment 0
- [ ] **Segment [4-11] Locked** (Tax Database - Read-Only):
  - [ ] ONLY FileRecommender searches these
  - [ ] NO writing during workflow
  - [ ] Populated at system startup only
- [ ] **All 12 Segments Dedicated** (Tax/Legal Workflow Only):
  - [ ] Tax agents use segments [0-3] for past responses
  - [ ] Tax agents use segments [4-11] for tax documents
  - [ ] Enforcement: Explicit segment lists in agent code

### Cross-Contamination Prevention

- [ ] **Segment Lists Explicit**: No dynamic segment selection
  - [ ] TaxResponseSearcher: `segments=[0, 1, 2, 3]` (hardcoded)
  - [ ] FileRecommender: `segments=[4, 5, 6, 7, 8, 9, 10, 11]` (hardcoded)
- [ ] **Constraint Comments**: Every search includes segment list comment
- [ ] **Error Handling**: If segment list missing, code fails (no fallback)

### Learning Signal Isolation

- [ ] **Tax Workflow Metadata**: Captured with constraints
- [ ] **All Segments Tax/Legal**: No separate planning workflows
- [ ] **Flow-GRPO Training**: Uses constraint metadata to learn boundaries within tax workflow

---

## SEGMENT 5: ERROR HANDLING & FALLBACKS

### Constraint Violation Handling

- [ ] **Missing Categories** → Return error, don't search
- [ ] **Missing Documents** → Return error, don't synthesize
- [ ] **Missing Confirmation** → Block button, show error message
- [ ] **Unsourced Claims** → Flag as hallucination, don't auto-approve
- [ ] **No matches found** → Return empty list (not broad search)

### Graceful Degradation

- [ ] **Step 2 fails** → Continue to Step 4 without past responses (graceful)
- [ ] **Step 4 finds nothing** → Allow user to proceed with manual input (graceful)
- [ ] **Step 6 finds issues** → Display issues, ask user to refine (user-controlled)

### Audit Trail

- [ ] **Every agent logs**: Constraint boundary used
- [ ] **Every agent logs**: Segments accessed
- [ ] **Every agent logs**: Results filtered count
- [ ] **Orchestrator aggregates**: Summary of all constraints applied

---

## SEGMENT 6: TESTING REQUIREMENTS

### Unit Test Checklist (Per Agent)

- [ ] **Test 1 - Missing Categories**: Agent returns error
- [ ] **Test 2 - Valid Input**: Agent returns correct output
- [ ] **Test 3 - Empty Results**: Agent returns empty (not error)
- [ ] **Test 4 - Metadata**: Constraint metadata included

### Integration Test Checklist

- [ ] **Test 1 - Full Workflow**: Request → Categories → Past Responses → Documents → Response → Verification → Approval
- [ ] **Test 2 - Rejection Path**: User can reject and return to Step 4
- [ ] **Test 3 - No Categories**: Searches fail gracefully (don't execute)
- [ ] **Test 4 - Learning**: Approved response saved with constraint metadata
- [ ] **Test 5 - Multi-User**: User A categories don't interfere with User B
- [ ] **Test 6 - Segment Isolation**: Verify segments [0-2] + [3-9] used, [10-11] untouched

### Code Review Checklist

- [ ] **Segment Lists**: All hardcoded (not dynamic)
- [ ] **Constraint Comments**: Present in all MemAgent search calls
- [ ] **Save Points**: Only ONE location saves approved responses
- [ ] **Metadata**: All agents return constraint boundary in metadata
- [ ] **Error Handling**: All agents validate constraints before search
- [ ] **Documentation**: All constraint boundaries documented in docstrings

---

## SEGMENT 7: IMPLEMENTATION SIGN-OFF

### Pre-Implementation

- [ ] Read all constraint files (User_Constrained_memagent.md, truncated_duplicate_memagent.md)
- [ ] Review checklist items
- [ ] Understand segment allocation diagram
- [ ] Understand single save point principle

### During Implementation

- [ ] Follow agent skeletons from PHASE_2_STEP1_AGENTS_REFACTOR.md
- [ ] Include CONSTRAINT BOUNDARIES comments
- [ ] Implement constraint validation (check categories before search)
- [ ] Use explicit segment lists (no fallback to broad search)
- [ ] Return constraint metadata
- [ ] **Memory Path Configuration (NEW)**:
  - [ ] All agents initialized with `memory_path=Path("local-memory/tax_legal")`
  - [ ] TaxOrchestrator passes tax_legal path to all agents
  - [ ] SegmentedMemory initialized with `memory_path=Path("local-memory/tax_legal")`
  - [ ] Session state saved to: `local-memory/tax_legal/users/{user_id}/sessions/{session_id}.json`

### Post-Implementation Code Review

- [ ] All checklist items marked complete
- [ ] All agents follow constraint pattern
- [ ] All searches include segment lists + constraint comments
- [ ] All saves happen in single location only
- [ ] All error cases handled gracefully
- [ ] All unit tests pass
- [ ] All integration tests pass

### Pre-Phase 3 Verification

- [ ] No MemAgent autonomous searches (user boundaries enforced)
- [ ] No truncated response files (single save point enforced)
- [ ] No cross-contamination (segment isolation enforced)
- [ ] All approved responses include constraint metadata
- [ ] Multi-user sessions properly isolated
- [ ] **Memory Namespace Verification (NEW)**:
  - [ ] Verify `local-memory/PJJ-old/` exists and contains archived Jupiter data
  - [ ] Verify `local-memory/tax_legal/` exists and is separate from PJJ-old/
  - [ ] Verify tax agents read ONLY from `local-memory/tax_legal/` (not PJJ-old/)
  - [ ] Verify Project Jupiter agents do NOT access `local-memory/tax_legal/`
  - [ ] Verify session files saved to: `local-memory/tax_legal/users/{user_id}/sessions/`
  - [ ] Verify no symlinks create cross-contamination between workflows

---

## SIGN-OFF

**Document**: PHASE_2_CONSTRAINT_ENFORCEMENT_CHECKLIST.md
**Created**: November 25, 2025
**Purpose**: Prevent recreation of old system MemAgent search autonomy issues
**Status**: Ready for Implementation Review

**Critical Principles Enforced**:
1. ✅ NO autonomous MemAgent searches (user confirms categories first)
2. ✅ EXPLICIT segment lists (no fallback to broad search)
3. ✅ SINGLE save point (no truncation)
4. ✅ SOURCE-ONLY constraints (no hallucinations)
5. ✅ AUDIT trails (constraint metadata tracked)

---

**Total Validation Points**: 150+
**Categories**: 7 (Agents, Orchestrator, UI, Memory, Error Handling, Testing, Sign-Off)
**Use For**: Code implementation, code review, testing verification
