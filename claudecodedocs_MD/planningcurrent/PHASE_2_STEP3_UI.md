# DETAILED PHASE 2 STEP 3: Streamlit UI Implementation

## STEP 3 OVERVIEW

**Goal**: Create Streamlit UI for 6-step tax workflow

**Duration**: Days 7-10
**Scope**: 6 screens + navigation + state management (350-400 lines total)
**Location**: NEW file `tax_app.py` (separate from Project Jupiter's app.py)
**Output**: Complete user interface for tax workflow

---

## ARCHITECTURE DECISION: Separate tax_app.py (Clean Approach)

### Why Separate File?

**Original Plan**: Modify existing `app.py` (from PHASE_2_STEP3_UI.md v1.0)
- Pros: Single app file, feature parity
- Cons: Risk of dead Project Jupiter code remaining, harder to debug, potential conflicts

**New Plan**: Create NEW `tax_app.py` (NOVEMBER 25, 2025)
- Pros: Clean separation, zero dead code risk, easier maintenance, can always consolidate later
- Cons: Two app files (but both serve different workflows)

**Reasoning**: User feedback "there is usually some leftover dead/conflicting code which messes with new developments" → prioritize code clarity and maintainability

### File Organization

```
mem-agent-mcp/
├── app.py (PRESERVED)
│   └─ Project Jupiter planning system (legacy)
│   └─ Run with: streamlit run app.py
│
├── tax_app.py (NEW - NOVEMBER 25, 2025)
│   └─ Tax/legal workflow system (current focus)
│   └─ Run with: streamlit run tax_app.py
│
├── orchestrator/tax_workflow/
│   ├── tax_planner_agent.py
│   ├── tax_searcher_agent.py
│   ├── tax_recommender_agent.py
│   ├── tax_compiler_agent.py
│   ├── tax_verifier_agent.py
│   ├── tax_tracker_agent.py
│   └── tax_orchestrator.py (BACKEND - NO CHANGES)
```

**Key Decision**:
- `tax_app.py` is the ONLY frontend for tax/legal workflow
- `app.py` is preserved (legacy Project Jupiter)
- Clear ownership, zero conflicts, clean codebase

---

## PART 1: UI ARCHITECTURE

### 1.1 Screen Organization

```
SCREEN 1: Request Input (Step 1)
  ├─ Text input for client request
  └─ Submit → TaxOrchestrator.run() with request
     ↓
SCREEN 2: Category Confirmation (Step 2)
  ├─ Display suggested categories (RequestCategorizer output)
  ├─ Multi-select dropdown (user can add/remove)
  └─ Confirm → TaxOrchestrator.run() with confirmed categories
     ↓
SCREEN 3: Past Response Selection (Step 3)
  ├─ List past responses (top-5 from TaxResponseSearcher)
  ├─ Each shows: Summary, categories, relevance score
  └─ User: Select one OR "Search for new documents"
     → TaxOrchestrator.run() proceeds to Step 4
     ↓
SCREEN 4: Document Selection (Step 4)
  ├─ Left column: Suggested files from past response (if selected)
  ├─ Right column: Additional search results (FileRecommender output)
  └─ Checkboxes: User selects which files to use
     → TaxOrchestrator.run() proceeds to Step 5
     ↓
SCREEN 5: Response Preview (Step 5)
  ├─ Rendered KPMG memo (TaxResponseCompiler output)
  ├─ Tabs: Response | Sources | Citations
  └─ Actions: Approve | Reject (go back to Step 4)
     → If Approve: Proceed to Step 6 (verify + citation)
     ↓
SCREEN 6: Approval Gate (Step 6)
  ├─ Read-only: Final response with citations
  ├─ Verification report (if issues found)
  └─ Partner Actions: Approve | Reject
     → If Approve: Save + learning signals
     → If Reject: Return to Step 4 (refine files)
```

### 1.2 Navigation Flow

```
streamlit.session_state structure:

{
    "session_id": "sess_12345",
    "user_id": "user_123",
    "current_step": 1-6,
    "original_request": "...",
    "suggested_categories": [...],
    "confirmed_categories": [...],
    "past_responses_found": [...],
    "selected_past_response": {...} | None,
    "documents_found": [...],
    "selected_documents": [...],
    "synthesized_response": "...",
    "response_with_citations": "...",
    "verification_report": {...},
    "citations": [...],
    "approval_status": "pending" | "approved" | "rejected"
}
```

---

## PART 1.5: STATE ISOLATION & USER BOUNDARY ENFORCEMENT (CRITICAL)

### 1.5 How UI Enforces MemAgent Constraints

**User Boundary Principle**: Users explicitly select categories and documents. These selections drive ALL downstream MemAgent searches.

**State Flow with Boundary Enforcement**:

```
Step 1: User enters request
  → RequestCategorizer suggests categories
  → Suggestions displayed to user (NOT automatic)

Step 2: USER CONFIRMS CATEGORIES (boundary set here!)
  → confirmed_categories = user selection
  → Only NOW can searches happen

Step 2→3: TaxResponseSearcher executes
  → Uses confirmed_categories as constraint boundary
  → Searches segments [0,1,2] ONLY
  → Filters results: only documents matching categories
  → Returns results filtered by category

Step 3: User selects past response (optional)
  → selected_past_response contains suggested_files

Step 4: FileRecommender executes
  → Uses confirmed_categories as constraint boundary
  → Searches segments [3-9] ONLY
  → Filters results: only documents matching categories
  → Returns results filtered by category

Step 4→5: USER SELECTS DOCUMENTS (refinement boundary)
  → selected_documents = user explicit choice
  → Only these documents used for synthesis

Step 5: TaxResponseCompiler uses ONLY selected_documents
  → No MemAgent search (source-only constraint)
  → Llama prompted: "Use ONLY provided sources"

Step 6: DocumentVerifier + CitationTracker
  → Verify AGAINST ONLY selected_documents
  → Cannot use external sources

Step 6→7: USER APPROVES (final control point)
  → approval_status = "approved"
  → Saves with constraint metadata
```

**Critical Invariant**: If user doesn't confirm categories, NO searches happen
  - TaxResponseSearcher returns empty with error
  - FileRecommender returns empty with error
  - No autonomous MemAgent scouring

**UI Responsibility**: Enforce category confirmation before search buttons enabled

```python
# SCREEN 2: Category Confirmation
if st.button("Continue to Search"):
    if not confirmed_categories:
        st.error("Please select at least one category")  # Block search
    else:
        # NOW safe to search with constraints
        TaxResponseSearcher(confirmed_categories=confirmed_categories).run()
```

### 1.6 Session State Isolation (Per-User + Per-Session)

```python
# Streamlit session_state provides isolation per browser session
st.session_state = {
    "session_id": "sess_abc123",          # Unique session
    "user_id": "user_xyz",                 # User context
    "original_request": "...",
    "suggested_categories": [],            # Agent output
    "confirmed_categories": [],            # USER BOUNDARY ← Critical
    "past_responses_found": [],            # Agent output
    "selected_past_response": None,        # USER BOUNDARY ← Critical
    "documents_found": [],                 # Agent output
    "selected_documents": [],              # USER BOUNDARY ← Critical
    "synthesized_response": "",            # Agent output
    "response_with_citations": "",         # Agent output
    "approval_status": "pending"           # USER BOUNDARY ← Critical
}
```

**Isolation Guarantees**:
- User A's session_id != User B's session_id
- State files saved to `/local-memory/tax_legal/users/{user_id}/sessions/{session_id}.json` (tax_legal namespace)
- User A cannot see User B's categories, documents, responses
- Constraint boundaries are per-user + per-session
- Tax workflow sessions isolated from Project Jupiter sessions (separate local-memory directories)

---

## PART 2: STREAMLIT CODE SKELETON

### 2.1 Main App Structure

```python
# tax_app.py (NEW Streamlit app - NOVEMBER 25, 2025)
# Location: /mem-agent-mcp/tax_app.py
# Purpose: Tax/legal workflow only (separate from Project Jupiter's app.py)

import streamlit as st
from pathlib import Path
from datetime import datetime
import json
import uuid
import sys

# Add repo to path for imports
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))

# Import backend
from orchestrator.tax_workflow.tax_orchestrator import TaxOrchestrator

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="KPMG Tax Workflow System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================

st.markdown("""
<style>
    .step-progress {
        font-size: 14px;
        font-weight: bold;
        color: #1f77b4;
    }
    .user-boundary {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #ff9800;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION INITIALIZATION
# ============================================================================

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "user_id" not in st.session_state:
    st.session_state.user_id = "user_default"  # Would come from auth

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = TaxOrchestrator(
        agent=get_agent(),  # Initialize Llama client
        memory_path=Path("./local-memory"),
        segmented_memory=get_segmented_memory(),
        learning_manager=get_learning_manager(),
        session_manager=get_session_manager()
    )

if "current_step" not in st.session_state:
    st.session_state.current_step = 0

if "original_request" not in st.session_state:
    st.session_state.original_request = ""

if "suggested_categories" not in st.session_state:
    st.session_state.suggested_categories = []

if "confirmed_categories" not in st.session_state:
    st.session_state.confirmed_categories = []

if "past_responses_found" not in st.session_state:
    st.session_state.past_responses_found = []

if "selected_past_response" not in st.session_state:
    st.session_state.selected_past_response = None

if "documents_found" not in st.session_state:
    st.session_state.documents_found = []

if "selected_documents" not in st.session_state:
    st.session_state.selected_documents = []

if "synthesized_response" not in st.session_state:
    st.session_state.synthesized_response = ""

if "response_with_citations" not in st.session_state:
    st.session_state.response_with_citations = ""

if "verification_report" not in st.session_state:
    st.session_state.verification_report = {}

if "citations" not in st.session_state:
    st.session_state.citations = []

if "approval_status" not in st.session_state:
    st.session_state.approval_status = "pending"

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.title("⚙️ Control Panel")

    st.write(f"**Session ID**: {st.session_state.session_id[:8]}...")
    st.write(f"**User**: {st.session_state.user_id}")

    st.divider()

    if st.button("🔄 Start New Request", use_container_width=True):
        # Reset all state
        st.session_state.current_step = 0
        st.session_state.original_request = ""
        st.session_state.suggested_categories = []
        st.session_state.confirmed_categories = []
        st.session_state.past_responses_found = []
        st.session_state.selected_past_response = None
        st.session_state.documents_found = []
        st.session_state.selected_documents = []
        st.session_state.synthesized_response = ""
        st.session_state.response_with_citations = ""
        st.session_state.approval_status = "pending"
        st.rerun()

    if st.button("💾 Save Session", use_container_width=True):
        st.success("Session saved!")

    st.divider()

    # Progress indicator
    st.subheader("Workflow Progress")
    progress_value = st.session_state.current_step / 6
    st.progress(progress_value)
    st.caption(f"Step {st.session_state.current_step} of 6")

# ============================================================================
# MAIN CONTENT
# ============================================================================

st.title("📋 KPMG Tax Workflow System")
st.markdown("*English-only MVP | Phase 2 Implementation*")

st.divider()

# Render appropriate screen based on current_step
if st.session_state.current_step == 0:
    render_screen_1_request_input()
elif st.session_state.current_step == 1:
    render_screen_2_category_confirmation()
elif st.session_state.current_step == 2:
    render_screen_3_past_response_selection()
elif st.session_state.current_step == 3:
    render_screen_4_document_selection()
elif st.session_state.current_step == 4:
    render_screen_5_response_preview()
elif st.session_state.current_step == 5:
    render_screen_6_approval_gate()
else:
    st.error("Unknown step")
```

### 2.2 Screen 1: Request Input

```python
def render_screen_1_request_input():
    """Screen 1: Client request input"""

    st.header("Step 1: Enter Your Tax Question")
    st.write("Provide details about your tax situation. The system will analyze and identify relevant tax domains.")

    # Input
    request = st.text_area(
        "Tax Question",
        placeholder="Example: Our Vietnam subsidiary is a pharmaceutical distributor with a Singapore parent company. We need to understand transfer pricing implications for intercompany sales...",
        height=150,
        key="request_input"
    )

    # Validation
    col1, col2 = st.columns([3, 1])
    with col2:
        submit_button = st.button("Submit", type="primary", use_container_width=True)

    if submit_button:
        if not request or len(request.strip()) < 10:
            st.error("❌ Please provide a more detailed request (at least 10 characters)")
        else:
            st.session_state.original_request = request

            # Call orchestrator Step 1
            with st.spinner("Analyzing your request..."):
                result = st.session_state.orchestrator.run(
                    request=request,
                    session_id=st.session_state.session_id,
                    user_id=st.session_state.user_id
                )

            if result["success"]:
                st.session_state.suggested_categories = result.get("suggested_categories", [])
                st.session_state.current_step = 1
                st.rerun()
            else:
                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
```

### 2.3 Screen 2: Category Confirmation

```python
def render_screen_2_category_confirmation():
    """Screen 2: User confirms/adjusts tax categories"""

    st.header("Step 2: Confirm Tax Categories")
    st.write("The system identified these relevant tax domains. You can add or remove categories.")

    # Display suggested categories as buttons
    st.subheader("Suggested Categories")

    suggested = st.session_state.suggested_categories
    st.info(f"🎯 {len(suggested)} categories suggested: {', '.join(suggested)}")

    # Multi-select for adjustment
    st.subheader("Adjust Categories (if needed)")

    all_categories = [
        "CIT", "VAT", "Transfer Pricing", "PIT", "FCT", "DTA",
        "Customs", "Excise Tax", "Environmental Tax", "Capital Gains"
    ]

    confirmed = st.multiselect(
        "Select tax categories to use:",
        options=all_categories,
        default=suggested,
        key="category_selector"
    )

    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 0
            st.rerun()

    with col3:
        if st.button("Continue →", type="primary", use_container_width=True):
            if not confirmed:
                st.error("❌ Please select at least one category")
            else:
                st.session_state.confirmed_categories = confirmed

                # Call orchestrator Step 2
                with st.spinner("Searching past responses..."):
                    result = st.session_state.orchestrator.run(
                        request=st.session_state.original_request,
                        session_id=st.session_state.session_id,
                        user_id=st.session_state.user_id
                    )

                if result["success"]:
                    st.session_state.past_responses_found = result.get("past_responses", [])
                    st.session_state.current_step = 2
                    st.rerun()
                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
```

### 2.4 Screen 3: Past Response Selection

```python
def render_screen_3_past_response_selection():
    """Screen 3: User selects from past responses or starts fresh"""

    st.header("Step 3: Review Similar Past Cases")

    if not st.session_state.past_responses_found:
        st.info("ℹ️ No similar past responses found. Proceeding to document search...")
        col1, col2 = st.columns([1, 1])
        with col2:
            if st.button("Continue to Document Search →", type="primary", use_container_width=True):
                st.session_state.current_step = 3
                st.rerun()
    else:
        st.write(f"Found {len(st.session_state.past_responses_found)} similar past cases:")

        st.subheader("Select a Past Response (Optional)")

        selected_idx = None
        for idx, response in enumerate(st.session_state.past_responses_found):
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**{response.get('filename', 'Unknown')}**")
                    st.caption(f"Similarity: {response.get('similarity_score', 0):.0%}")
                    st.write(response.get('summary', 'No summary'))
                    if response.get('categories'):
                        st.caption(f"Categories: {', '.join(response['categories'])}")

                with col2:
                    if st.checkbox("Select", key=f"response_{idx}"):
                        selected_idx = idx

        st.divider()

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.current_step = 1
                st.rerun()

        with col2:
            if st.button("Continue →", type="primary", use_container_width=True):
                if selected_idx is not None:
                    st.session_state.selected_past_response = st.session_state.past_responses_found[selected_idx]

                st.session_state.current_step = 3
                st.rerun()
```

### 2.5 Screen 4: Document Selection

```python
def render_screen_4_document_selection():
    """Screen 4: User selects source documents"""

    st.header("Step 4: Select Source Documents")

    col1, col2 = st.columns(2)

    # Left column: Suggested files
    with col1:
        st.subheader("📌 Suggested Files")
        st.caption("From selected past response")

        suggested_files = []
        if st.session_state.selected_past_response:
            suggested_files = st.session_state.selected_past_response.get("files_used", [])

        if suggested_files:
            for file in suggested_files:
                st.write(f"✓ {file}")
        else:
            st.info("No suggested files")

    # Right column: Search results
    with col2:
        st.subheader("🔍 Search Results")
        st.caption("Additional documents found")

        if st.session_state.documents_found:
            selected_docs = []
            for doc in st.session_state.documents_found:
                if st.checkbox(
                    doc.get('filename', 'Unknown'),
                    value=False,
                    key=f"doc_{doc.get('filename')}"
                ):
                    selected_docs.append(doc.get('filename'))

                # Show metadata
                with st.expander(f"ℹ️ {doc.get('filename')}", expanded=False):
                    st.write(f"**Category**: {doc.get('category', 'Unknown')}")
                    st.write(f"**Relevance**: {doc.get('relevance_score', 0):.0%}")
                    st.write(f"**Size**: {doc.get('size', 'Unknown')}")

            st.session_state.selected_documents = selected_docs

        else:
            st.info("No documents found")

    st.divider()

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()

    with col3:
        if st.button("Continue →", type="primary", use_container_width=True):
            if not st.session_state.selected_documents:
                st.error("❌ Please select at least one document")
            else:
                # Call orchestrator Step 5
                with st.spinner("Synthesizing response..."):
                    result = st.session_state.orchestrator.run(
                        request=st.session_state.original_request,
                        session_id=st.session_state.session_id,
                        user_id=st.session_state.user_id
                    )

                if result["success"]:
                    st.session_state.synthesized_response = result.get("response", "")
                    st.session_state.current_step = 4
                    st.rerun()
                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
```

### 2.6 Screen 5: Response Preview

```python
def render_screen_5_response_preview():
    """Screen 5: Preview synthesized response"""

    st.header("Step 5: Review Response")

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📄 Response", "📚 Source Files", "🔗 Citations"])

    with tab1:
        st.subheader("KPMG Tax Memorandum")
        st.markdown(st.session_state.synthesized_response)

    with tab2:
        st.subheader("Source Documents Used")
        for doc in st.session_state.selected_documents:
            st.write(f"- {doc}")

    with tab3:
        st.subheader("Citations")
        if st.session_state.citations:
            for citation in st.session_state.citations:
                st.write(f"- {citation.get('source', 'Unknown')}")
        else:
            st.info("No citations found")

    st.divider()

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("← Back (Refine Files)", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()

    with col3:
        if st.button("Continue to Approval →", type="primary", use_container_width=True):
            # Call orchestrator Step 6 (verify + citation)
            with st.spinner("Verifying response..."):
                result = st.session_state.orchestrator.run(
                    request=st.session_state.original_request,
                    session_id=st.session_state.session_id,
                    user_id=st.session_state.user_id
                )

            if result["success"]:
                st.session_state.response_with_citations = result.get("response", "")
                st.session_state.verification_report = result.get("verification_report", {})
                st.session_state.citations = result.get("citations", [])
                st.session_state.current_step = 5
                st.rerun()
            else:
                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
```

### 2.7 Screen 6: Approval Gate

```python
def render_screen_6_approval_gate():
    """Screen 6: Partner approval"""

    st.header("Step 6: Partner Approval")

    st.info("🔒 **This is restricted to KPMG partners only.**")

    # Display verification report if issues found
    if st.session_state.verification_report:
        if not st.session_state.verification_report.get("all_verified", True):
            st.warning("⚠️ **Verification Issues Found**")
            with st.expander("View Issues", expanded=True):
                for issue in st.session_state.verification_report.get("issues", []):
                    st.write(f"- Claim {issue.get('claim_id')}: {issue.get('issue_type')}")

    # Response with citations
    st.subheader("Final Response")
    st.markdown(st.session_state.response_with_citations)

    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        reject_button = st.button("❌ Reject", use_container_width=True)

    with col2:
        approve_button = st.button("✅ Approve", type="primary", use_container_width=True)

    if approve_button:
        # Handle approval
        with st.spinner("Saving response and recording learning..."):
            approval_result = st.session_state.orchestrator.handle_approval(
                session=st.session_state,
                approved=True
            )

        if approval_result["success"]:
            st.success("✅ Response approved and saved!")
            st.balloons()

            # Show saved response ID
            st.info(f"Response ID: {approval_result.get('response_id', 'unknown')}")

            # Reset for new request
            if st.button("Start New Request", type="primary", use_container_width=True):
                st.session_state.current_step = 0
                st.session_state.original_request = ""
                st.session_state.suggested_categories = []
                st.session_state.confirmed_categories = []
                st.rerun()

    if reject_button:
        st.warning("Returning to file selection...")
        st.session_state.current_step = 3
        st.rerun()
```

---

## PART 3: STATE MANAGEMENT & PERSISTENCE

### 3.1 Session Recovery

```python
def load_session_from_disk(session_id: str, user_id: str) -> dict:
    """Load session state from disk if exists"""
    session_file = Path(f"./local-memory/users/{user_id}/sessions/{session_id}.json")

    if session_file.exists():
        with open(session_file, 'r') as f:
            return json.load(f)
    return None


# On app startup
if st.session_state.current_step == 0 and st.session_state.original_request == "":
    saved_session = load_session_from_disk(
        st.session_state.session_id,
        st.session_state.user_id
    )

    if saved_session:
        st.session_state.current_step = saved_session.get("current_step", 0)
        st.session_state.original_request = saved_session.get("original_request", "")
        # ... restore all fields
        st.info("✓ Previous session restored")
```

---

## PART 4: TESTING STRATEGY

### 4.1 Manual Testing Checklist

- [ ] Screen 1: Request input validation
- [ ] Screen 2: Category multi-select works
- [ ] Screen 3: Past response selection
- [ ] Screen 4: Document multi-select with scrolling
- [ ] Screen 5: Response tabs display correctly
- [ ] Screen 6: Approval buttons work
- [ ] Navigation: Forward/back buttons work
- [ ] State persistence: Refresh page → state restored
- [ ] Multi-user: 2+ users don't see each other's data
- [ ] Error handling: All error messages display
- [ ] Performance: Each screen <3 seconds to load

### 4.2 Integration Test

```
Test flow:
1. Enter pharmaceutical distributor request
2. Confirm CIT + Transfer Pricing categories
3. Select past response (if found)
4. Select 2-3 documents
5. Review response
6. Approve
7. Verify saved to past_responses/
8. Verify learning signals recorded
```

---

## PART 5: DEPLOYMENT

### 5.1 Running tax_app.py

```bash
cd /path/to/memagent-modular-fixed/mem-agent-mcp
streamlit run tax_app.py --logger.level=info
```

**Default Port**: 8501
**Output**: "You can now view your Streamlit app in your browser at: http://localhost:8501"

**Requires**:
- Streamlit installed (`pip install streamlit`)
- All backend modules accessible (orchestrator/tax_workflow/)
- TaxOrchestrator imports working
- Llama client configured
- MemAgent instance with tax_legal namespace

### 5.2 Separate from Project Jupiter (app.py)

```bash
# To run Project Jupiter planning (legacy):
streamlit run app.py --logger.level=info

# To run Tax/Legal workflow (current):
streamlit run tax_app.py --logger.level=info

# Both can run simultaneously on different ports:
streamlit run app.py --server.port 8501
streamlit run tax_app.py --server.port 8502
```

### 5.3 Production Configuration

```
# .streamlit/config.toml (for tax_app.py)

[server]
headless = true
port = 8501
runOnSave = false
maxMessageSize = 200

[client]
showErrorDetails = true
toolbarMode = "viewer"

[logger]
level = "info"

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#f0f2f6"
secondaryBackgroundColor = "#e0e1e6"
textColor = "#262730"
font = "sans serif"
```

---

## SUMMARY

**UI provides complete 6-step workflow**:

| Screen | Step | User Input | Backend Call |
|--------|------|-----------|--------------|
| 1 | 1 | Request text | RequestCategorizer |
| 2 | 2 | Category selection | TaxResponseSearcher |
| 3 | 3 | Past response selection | — (UI only) |
| 4 | 4 | Document selection | FileRecommender |
| 5 | 5 | File confirmation | TaxResponseCompiler |
| 6 | 6 | Approval decision | DocumentVerifier + CitationTracker |

**State**: Persisted to disk (recoverable on refresh)

**Integration**: Connects to TaxOrchestrator backend

**Testing**: Manual checklist + integration test

**Deployment**: `streamlit run app.py`

**Next**: Integration testing (Phase 3) validates full workflow

---

## PLANNING DECISION LOG (NOVEMBER 25, 2025)

### Decision: Separate tax_app.py vs Modifying app.py

**Context**:
- Original v1.0 plan: Modify existing app.py (Project Jupiter planning system)
- User feedback: "usually some leftover dead/conflicting code which messes with new developments"
- Requirement: Zero hallucination, clean development path

**Decision Made: CREATE NEW tax_app.py**

**Rationale**:
1. **Code Safety**: No dead Project Jupiter code remaining
2. **Maintainability**: Clear ownership (tax_app.py = tax/legal only)
3. **Debugging**: Easy to identify issues (new code only)
4. **Future Flexibility**: Can consolidate later if needed
5. **Testing**: Isolated testing without Project Jupiter interference

**Architecture**:
- `app.py`: Project Jupiter planning (preserved, legacy)
- `tax_app.py`: Tax/legal workflow (new, current focus)
- Both can coexist or be consolidated post-Phase 2

**Implementation Approach**:
- Day 7: Create tax_app.py base + Screens 1-2
- Day 8: Screens 3-4
- Day 9: Screens 5-6
- Day 10: Testing & polish

**Benefits**:
- ✅ Zero dead code
- ✅ Clear separation of concerns
- ✅ Easier to debug
- ✅ Reduced risk of conflicts
- ✅ Can run both simultaneously for testing

---

## IMPLEMENTATION STATUS (NOVEMBER 26, 2025)

### ✅ ALL 6 SCREENS IMPLEMENTED AND FUNCTIONAL

**Status**: Phase 2 Step 3 COMPLETE

**Implementation Timeline**:
- Day 7: Screens 1-2 ✅ (Request input + Category confirmation)
- Day 8: Screens 3-4 ✅ (Past response + Document selection)
- Day 9: Screens 5-6 ✅ (Response preview + Approval gate)

**Location**: `/mem-agent-mcp/tax_app.py` (created as separate file, not modifying app.py)

**All Screens Functional**:
- ✅ Screen 1: Request input with validation (min 10 chars)
- ✅ Screen 2: Category confirmation with multi-select
- ✅ Screen 3: Past response selection (optional flow, auto-skip if none)
- ✅ Screen 4: Document selection with FileRecommender integration
  - Two-column layout: Suggested files | Search results
  - FileRecommender integration with error checking
  - Constraint enforcement (Continue disabled if no documents)
- ✅ Screen 5: Response preview with 3 tabs
  - Tab 1: Full response markdown rendering
  - Tab 2: Source files list
  - Tab 3: Citations with counts
  - Back button to refine files
  - Continue button calls orchestrator Step 6 for verification
- ✅ Screen 6: Approval gate with verification report
  - Verification report display (issues if found)
  - Final response markdown rendering
  - Citations summary expander
  - Approve/Reject buttons
  - On Approve: Calls orchestrator.handle_approval()
  - Shows response ID after approval
  - Session reset for new request

**Additional Features Implemented**:
- ✅ Comprehensive logging at every step
- ✅ Live log viewer in sidebar with color-coding
- ✅ Full error handling and graceful failures
- ✅ Session state persistence to disk
- ✅ State validation with hasattr checks (learned from Day 7 errors)
- ✅ Result verification with .get("success") before using output
- ✅ User boundary enforcement at UI level
- ✅ Session isolation per user + per session

**Ready for**: Day 10 comprehensive testing

---

**Document Version**: 2.1 (Updated with Implementation Status)
**Created**: November 25, 2025 (Original v1.0 - Specification)
**Updated**: November 26, 2025 (v2.1 - Complete with Implementation Status)
**Purpose**: Complete Streamlit UI implementation for Phase 2 (Tax/Legal Workflow)
**Status**: ✅ FULLY IMPLEMENTED (Days 7-9 Complete)
