"""
KPMG Tax Workflow System - Streamlit UI
Phase 2 Step 3: Tax/Legal Request Analysis and Response Generation

This is a separate Streamlit application (tax_app.py) for the tax/legal workflow.
It works alongside (but independent from) the Project Jupiter planning system (app.py).

Run with: streamlit run tax_app.py
"""

import streamlit as st
from pathlib import Path
import uuid
import json
import sys
from datetime import datetime

# Add repo to path for imports
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))

# ============================================================================
# IMPORTS
# ============================================================================

try:
    from agent import Agent
    from orchestrator.tax_workflow.tax_orchestrator import TaxOrchestrator
    from agent.logging_config import setup_logging, get_logger, tail_log_file, get_log_statistics, clear_logs
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.stop()

# Initialize logging system
setup_logging()
logger = get_logger(__name__)

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
    .step-header {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 20px;
    }

    .user-boundary {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #ff9800;
        margin: 10px 0;
    }

    .category-pill {
        display: inline-block;
        padding: 8px 12px;
        margin: 5px;
        border-radius: 20px;
        background-color: #e8f4f8;
        border: 1px solid #1f77b4;
        font-weight: 500;
    }

    .error-box {
        background-color: #ffebee;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #f44336;
    }

    .success-box {
        background-color: #e8f5e9;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize all session variables if not already set"""
    defaults = {
        # Session tracking
        "session_id": str(uuid.uuid4()),
        "user_id": st.query_params.get("user_id", "default_user") if hasattr(st, "query_params") else "default_user",
        "current_step": 0,

        # Step 1: Request Input
        "original_request": "",

        # Step 1→2: RequestCategorizer Output
        "suggested_categories": [],
        "category_confidence": {},

        # USER BOUNDARY #1: Category Confirmation
        "confirmed_categories": [],

        # Step 2→3: TaxResponseSearcher Output
        "past_responses_found": [],

        # USER BOUNDARY #2: Past Response Selection
        "selected_past_response": None,
        "past_response_files": [],

        # Step 4: FileRecommender Output
        "documents_found": [],

        # USER BOUNDARY #3: Document Selection
        "selected_documents": [],
        "selected_file_contents": {},

        # Step 5: TaxResponseCompiler Output
        "synthesized_response": "",

        # Step 6a: DocumentVerifier Output
        "verification_report": {},
        "can_approve": False,

        # Step 6b: CitationTracker Output
        "response_with_citations": "",
        "citations": [],

        # USER BOUNDARY #4: Approval
        "approval_status": "pending",

        # Error handling
        "last_error": None,

        # Orchestrator caching
        "orchestrator": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================================================
# ORCHESTRATOR INITIALIZATION
# ============================================================================

@st.cache_resource
def get_orchestrator():
    """Initialize TaxOrchestrator (cached for performance)"""
    try:
        # PRIMARY DATA DIRECTORY - Use .resolve() to ensure absolute path
        # Located at: /Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/
        script_dir = Path(__file__).parent.resolve()  # /mem-agent-mcp (absolute)
        memagent_root = script_dir.parent.resolve()   # /memagent-modular-fixed (absolute)

        # PRIMARY: Data directory (contains actual tax documents and past responses)
        memory_path = (memagent_root / "local-memory" / "tax_legal").resolve()

        # Verify PRIMARY data directory exists with actual data
        if not memory_path.exists():
            raise FileNotFoundError(
                f"PRIMARY DATA DIRECTORY NOT FOUND:\n"
                f"  Resolved Path: {memory_path}\n"
                f"  Script Dir: {script_dir}\n"
                f"  Memagent Root: {memagent_root}\n"
                f"Expected: /Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/\n"
                f"Contains: past_responses/ and tax_database/ with all MD files"
            )

        # Step 2: Past responses search path (PRIMARY DATA)
        past_responses_path = memory_path / "past_responses"
        if not past_responses_path.exists():
            logger.warning(f"Step 2 past_responses directory not found: {past_responses_path}")

        # Step 4: Tax database file search path (PRIMARY DATA)
        tax_database_path = memory_path / "tax_database"
        if not tax_database_path.exists():
            logger.warning(f"Step 4 tax_database directory not found: {tax_database_path}")

        # SECONDARY: Runtime info directory (sessions, logs, user metadata)
        # This is SEPARATE from PRIMARY data - renamed to streamlit_instance_info
        runtime_info_dir = (memagent_root / "streamlit_instance_info").resolve()
        runtime_info_dir.mkdir(parents=True, exist_ok=True)
        (runtime_info_dir / "users").mkdir(parents=True, exist_ok=True)
        (runtime_info_dir / "logs").mkdir(parents=True, exist_ok=True)
        (runtime_info_dir / "entities").mkdir(parents=True, exist_ok=True)

        logger.info(f"PRIMARY DATA DIRECTORY: {memory_path}")
        logger.info(f"  - past_responses: {past_responses_path}")
        logger.info(f"  - tax_database: {tax_database_path}")
        logger.info(f"RUNTIME INFO DIRECTORY: {runtime_info_dir}")

        # Initialize Agent instance for the orchestrator (uses PRIMARY data dir)
        agent = Agent(memory_path=str(memory_path))

        # Create orchestrator with BOTH paths:
        # - memory_path: PRIMARY data directory (read-only for searches)
        # - runtime_info_dir: SECONDARY runtime directory (write for sessions/logs)
        # Uses vanilla MemAgent pattern: Agent.chat() for intelligent memory navigation
        orchestrator = TaxOrchestrator(
            agent=agent,
            memory_path=memory_path,  # PRIMARY: /local-memory/tax_legal/
            runtime_path=runtime_info_dir  # SECONDARY: /streamlit_instance_info/
        )
        return orchestrator
    except Exception as e:
        st.error(f"Failed to initialize TaxOrchestrator: {e}")
        return None

# Get orchestrator
if st.session_state.orchestrator is None:
    st.session_state.orchestrator = get_orchestrator()

orchestrator = st.session_state.orchestrator

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def show_error(message: str, details: str = None):
    """Display error message"""
    st.error(f"❌ {message}")
    if details:
        with st.expander("Technical Details"):
            st.code(details)
    st.session_state.last_error = message

def show_success(message: str):
    """Display success message"""
    st.success(f"✅ {message}")

def show_info(message: str):
    """Display info message"""
    st.info(f"ℹ️ {message}")

def go_to_step(step: int):
    """Navigate to a specific step"""
    st.session_state.current_step = step
    st.rerun()

def show_transparency_info(metadata: dict):
    """Show constraint boundary info (transparency)"""
    if not metadata:
        return

    with st.expander("🔍 Search Details (Transparency)"):
        cols = st.columns(3)

        if "search_time_ms" in metadata:
            cols[0].metric("Search Time", f"{metadata['search_time_ms']}ms")
        if "total_found" in metadata:
            cols[1].metric("Results Found", metadata['total_found'])
        if "min_similarity_threshold" in metadata:
            cols[2].metric("Threshold", f"{metadata['min_similarity_threshold']:.0%}")

        if "category_constraint_boundary" in metadata:
            st.write("**Categories Used:**", ", ".join(metadata["category_constraint_boundary"]))
        if "segments_accessed" in metadata:
            st.write("**Segments Accessed:**", str(metadata["segments_accessed"]))
        if "search_scope" in metadata:
            st.write("**Search Scope:**", metadata["search_scope"])

def save_session_to_disk():
    """Save session state to disk for recovery"""
    try:
        # Save to SECONDARY runtime directory, not PRIMARY data directory
        script_dir = Path(__file__).parent.resolve()
        memagent_root = script_dir.parent.resolve()
        session_dir = (memagent_root / "streamlit_instance_info" / "users" / st.session_state.user_id / "sessions").resolve()
        session_dir.mkdir(parents=True, exist_ok=True)

        session_file = session_dir / f"{st.session_state.session_id}.json"

        # Prepare session data (exclude non-serializable objects)
        session_data = {
            "session_id": st.session_state.session_id,
            "user_id": st.session_state.user_id,
            "current_step": st.session_state.current_step,
            "original_request": st.session_state.original_request,
            "suggested_categories": st.session_state.suggested_categories,
            "category_confidence": st.session_state.category_confidence,
            "confirmed_categories": st.session_state.confirmed_categories,
            "past_responses_found": st.session_state.past_responses_found,
            "selected_past_response": st.session_state.selected_past_response,
            "past_response_files": st.session_state.past_response_files,
            "documents_found": st.session_state.documents_found,
            "selected_documents": st.session_state.selected_documents,
            "selected_file_contents": st.session_state.selected_file_contents,
            "synthesized_response": st.session_state.synthesized_response,
            "verification_report": st.session_state.verification_report,
            "can_approve": st.session_state.can_approve,
            "response_with_citations": st.session_state.response_with_citations,
            "citations": st.session_state.citations,
            "approval_status": st.session_state.approval_status,
        }

        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
    except Exception as e:
        # Don't crash if save fails, just log it
        pass

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.title("⚙️ Control Panel")

    # Session info
    st.write(f"**Session ID**: `{st.session_state.session_id[:8]}...`")
    st.write(f"**User**: {st.session_state.user_id}")

    st.divider()

    # New request button
    if st.button("🔄 Start New Request", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.current_step = 0
        st.session_state.original_request = ""
        st.session_state.suggested_categories = []
        st.session_state.category_confidence = {}
        st.session_state.confirmed_categories = []
        st.session_state.past_responses_found = []
        st.session_state.selected_past_response = None
        st.session_state.past_response_files = []
        st.session_state.documents_found = []
        st.session_state.selected_documents = []
        st.session_state.selected_file_contents = {}
        st.session_state.synthesized_response = ""
        st.session_state.verification_report = {}
        st.session_state.can_approve = False
        st.session_state.response_with_citations = ""
        st.session_state.citations = []
        st.session_state.approval_status = "pending"
        st.rerun()

    st.divider()

    # Progress indicator
    st.subheader("📊 Workflow Progress")
    progress_value = st.session_state.current_step / 6
    st.progress(progress_value)
    step_text = f"Step {st.session_state.current_step} of 6"
    if st.session_state.current_step == 0:
        step_text = "Ready to start"
    st.caption(step_text)

    st.divider()

    # Status badges
    st.subheader("✓ Status")
    if st.session_state.original_request:
        st.caption("✓ Request entered")
    if st.session_state.confirmed_categories:
        st.caption(f"✓ {len(st.session_state.confirmed_categories)} categories confirmed")
    if st.session_state.past_responses_found:
        st.caption(f"✓ {len(st.session_state.past_responses_found)} past responses found")
    if st.session_state.selected_documents:
        st.caption(f"✓ {len(st.session_state.selected_documents)} documents selected")

    st.divider()

    # Live Logs Viewer
    st.subheader("🔍 Live Logs")

    # Get recent logs
    recent_logs = tail_log_file(lines=50)
    log_stats = get_log_statistics()

    # Display log statistics
    if log_stats.get("exists"):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Log File Size", f"{log_stats.get('size_mb', 0):.2f} MB")
        with col2:
            st.metric("Last Updated", log_stats.get("modified", "N/A"))

    # Display logs in a container
    with st.container(border=True):
        # Color-coded log display
        for log_line in recent_logs:
            if "[ERROR]" in log_line:
                st.markdown(f"<span style='color:red'>{log_line}</span>", unsafe_allow_html=True)
            elif "[WARNING]" in log_line:
                st.markdown(f"<span style='color:orange'>{log_line}</span>", unsafe_allow_html=True)
            elif "[INFO]" in log_line:
                st.markdown(f"<span style='color:blue'>{log_line}</span>", unsafe_allow_html=True)
            else:
                st.caption(log_line)

    # Log controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Download Logs", use_container_width=True):
            if log_stats.get("exists"):
                with open(log_stats.get("path"), "r") as f:
                    log_content = f.read()
                st.download_button(
                    label="Download",
                    data=log_content,
                    file_name=f"tax_app_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                    mime="text/plain"
                )

    with col2:
        if st.button("🗑️ Clear Logs", use_container_width=True):
            clear_logs()
            st.info("Logs cleared (page will refresh)")
            st.rerun()

# ============================================================================
# SCREEN 1: REQUEST INPUT
# ============================================================================

def render_screen_1_request_input():
    """Screen 1: User enters tax question"""

    st.header("📝 Step 1 of 6: Enter Your Tax Question")
    st.markdown("Provide details about your tax situation. The system will analyze and identify relevant tax domains.")

    # Input
    request = st.text_area(
        "Tax Question",
        placeholder="Example: Our Vietnam subsidiary is a pharmaceutical distributor with a Singapore parent company. We need to understand transfer pricing implications for intercompany sales...",
        height=150,
        key="request_input_1"
    )

    # Display character count
    col1, col2 = st.columns([3, 1])
    with col2:
        st.caption(f"{len(request)} characters")

    # Validation & Submit
    col1, col2 = st.columns([3, 1])
    with col2:
        submit_button = st.button("Submit", type="primary", use_container_width=True)

    if submit_button:
        if not request or len(request.strip()) < 10:
            show_error("Request too short", "Please provide a more detailed request (at least 10 characters)")
        else:
            st.session_state.original_request = request

            # Call orchestrator Step 1
            with st.spinner("🤔 Analyzing your request..."):
                try:
                    if orchestrator is None:
                        show_error("Orchestrator not initialized", "Failed to initialize TaxOrchestrator")
                        return

                    result = orchestrator.run_workflow(
                        request=request,
                        session_id=st.session_state.session_id,
                        user_id=st.session_state.user_id,
                        step=1
                    )

                    if result.get("success"):
                        # Extract output
                        output = result.get("output", {})
                        st.session_state.suggested_categories = output.get("suggested_categories", [])
                        st.session_state.category_confidence = output.get("confidence_by_category", {})
                        st.session_state.current_step = 1

                        # Save session
                        save_session_to_disk()

                        show_success("Request analyzed successfully!")
                        st.rerun()
                    else:
                        error_msg = result.get("error", "Unknown error analyzing request")
                        error_details = str(result.get("metadata", {}))
                        show_error(error_msg, error_details)

                except Exception as e:
                    show_error(f"Error analyzing request: {str(e)}", str(e))

# ============================================================================
# SCREEN 2: CATEGORY CONFIRMATION
# ============================================================================

def render_screen_2_category_confirmation():
    """Screen 2: User confirms/adjusts tax categories"""

    st.header("🏷️ Step 2 of 6: Confirm Tax Categories")
    st.markdown("The system identified these relevant tax domains. You can adjust the selection.")

    # Display suggested categories as pills
    st.subheader("Suggested Categories")
    suggested = st.session_state.suggested_categories

    if suggested:
        st.info(f"🎯 {len(suggested)} categories suggested")

        # Display as colored pills with confidence
        cols = st.columns(3)
        for idx, category in enumerate(suggested):
            col_idx = idx % 3
            with cols[col_idx]:
                confidence = st.session_state.category_confidence.get(category, 0)
                st.metric(category, f"{confidence:.0%}")
    else:
        show_error("No categories suggested", "Failed to identify relevant tax categories")
        return

    # Multi-select for confirmation/adjustment
    st.subheader("Confirm Categories")
    st.markdown("**USER BOUNDARY**: Select which categories to use for document search (required)")

    all_categories = [
        "CIT", "VAT", "Transfer Pricing", "PIT", "FCT", "DTA",
        "Customs", "Excise Tax", "Environmental Tax", "Capital Gains", "Other"
    ]

    confirmed = st.multiselect(
        "Select tax categories to use:",
        options=all_categories,
        default=suggested,
        key="category_selector"
    )

    # Show user boundary enforcement
    if not confirmed:
        st.markdown("""
        <div class="user-boundary">
        <strong>⚠️ User Boundary</strong><br/>
        Please select at least one category to proceed.
        </div>
        """, unsafe_allow_html=True)

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("← Back", use_container_width=True):
            go_to_step(0)

    with col3:
        if st.button("Continue →", type="primary", use_container_width=True, disabled=not confirmed):
            if not confirmed:
                show_error("Categories required", "Please select at least one category")
            else:
                st.session_state.confirmed_categories = confirmed

                # Call orchestrator Step 2
                with st.spinner("🔍 Searching past responses..."):
                    try:
                        if orchestrator is None:
                            show_error("Orchestrator not initialized")
                            return

                        result = orchestrator.run_workflow(
                            request=st.session_state.original_request,
                            session_id=st.session_state.session_id,
                            user_id=st.session_state.user_id,
                            step=2,
                            confirmed_categories=confirmed
                        )

                        if result.get("success"):
                            output = result.get("output", {})
                            st.session_state.past_responses_found = output.get("past_responses", [])
                            st.session_state.current_step = 2

                            # Show transparency info
                            metadata = result.get("metadata", {})
                            show_transparency_info(metadata)

                            # Save session
                            save_session_to_disk()

                            show_success("Past responses searched successfully!")
                            st.rerun()
                        else:
                            error_msg = result.get("error", "Unknown error searching past responses")
                            error_details = str(result.get("metadata", {}))
                            show_error(error_msg, error_details)

                    except Exception as e:
                        show_error(f"Error searching: {str(e)}", str(e))

# ============================================================================
# SCREEN 3: PAST RESPONSE SELECTION
# ============================================================================

def render_screen_3_past_response_selection():
    """Screen 3: User selects from past responses or starts fresh"""

    st.header("📜 Step 3 of 6: Review Similar Past Cases")
    st.markdown("Explore similar tax questions we've solved before.")

    # CRITICAL: Check state is populated (learned from Day 7)
    if not hasattr(st.session_state, 'past_responses_found'):
        show_error("Internal error: past_responses not available")
        st.info("Please go back and run category confirmation first")
        if st.button("← Back"):
            go_to_step(1)
        return

    past_responses = st.session_state.past_responses_found

    # Logic: If empty, skip to next screen
    if not past_responses:
        st.info("ℹ️ No similar past responses found. Proceeding to fresh document search...")
        st.session_state.selected_past_response = None
        st.session_state.past_response_files = []

        # Import logger for logging
        from agent.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info(f"Screen 3: No past responses found, auto-skipping to Screen 4")

        if st.button("Continue to Document Search →", type="primary", use_container_width=True):
            st.session_state.current_step = 3
            save_session_to_disk()
            st.rerun()
    else:
        st.write(f"Found {len(past_responses)} similar past cases:")

        # Display past responses
        st.subheader("Select a Past Response (Optional)")
        st.markdown("*You can use a past response as a starting point, or skip to search for documents*")

        selected_idx = None
        for idx, response in enumerate(past_responses):
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.write(f"**{response.get('filename', 'Unknown')}**")
                    st.caption(f"Similarity: {response.get('similarity_score', 0):.0%}")
                    st.write(response.get('summary', 'No summary available')[:200])
                    if response.get('categories'):
                        st.caption(f"Categories: {', '.join(response['categories'])}")
                    if response.get('date_created'):
                        st.caption(f"Created: {response['date_created']}")

                with col2:
                    if st.checkbox("Select", key=f"response_{idx}"):
                        selected_idx = idx

        st.divider()

        # Navigation buttons
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("← Back", use_container_width=True):
                go_to_step(1)

        with col2:
            if st.button("Continue →", type="primary", use_container_width=True):
                # Extract files_used if selected, otherwise empty list
                if selected_idx is not None:
                    st.session_state.selected_past_response = past_responses[selected_idx]
                    st.session_state.past_response_files = past_responses[selected_idx].get("files_used", [])

                    from agent.logging_config import get_logger
                    logger = get_logger(__name__)
                    logger.info(f"Screen 3: User selected past response: {past_responses[selected_idx].get('filename')}")
                    logger.info(f"Screen 3: Extracted files_used: {st.session_state.past_response_files}")
                else:
                    st.session_state.selected_past_response = None
                    st.session_state.past_response_files = []

                    from agent.logging_config import get_logger
                    logger = get_logger(__name__)
                    logger.info("Screen 3: User skipped past response selection")

                st.session_state.current_step = 3
                save_session_to_disk()
                st.rerun()

# ============================================================================
# SCREEN 4: DOCUMENT SELECTION
# ============================================================================

def render_screen_4_document_selection():
    """Screen 4: User selects source documents"""

    st.header("📄 Step 4 of 6: Select Source Documents")
    st.markdown("Choose which tax documents to use for analysis. You must select at least one.")

    from agent.logging_config import get_logger
    logger = get_logger(__name__)

    # CRITICAL: Verify confirmed_categories exist (constraint validation)
    if not hasattr(st.session_state, 'confirmed_categories') or not st.session_state.confirmed_categories:
        show_error("❌ Constraint violation: Categories not confirmed")
        st.info("Please go back to Step 2 and confirm categories")
        if st.button("← Back to Categories"):
            go_to_step(1)
        return

    logger.info(f"Screen 4: Rendering with confirmed categories={st.session_state.confirmed_categories}")

    # Get suggested files from Screen 3 (may be empty)
    suggested_files = st.session_state.past_response_files or []
    logger.info(f"Screen 4: Suggested files from past response: {len(suggested_files)}")

    # TWO COLUMNS
    col_left, col_right = st.columns(2)

    # ====== LEFT COLUMN: Suggested Files ======
    with col_left:
        st.subheader("📌 Suggested Files")
        if suggested_files:
            st.caption(f"From selected past response ({len(suggested_files)} files)")
        else:
            st.caption("None selected from past response")

        # Display as checkboxes (pre-checked if from past response)
        selected_suggested = []
        for file in suggested_files:
            if st.checkbox(f"✓ {file}", value=True, key=f"suggested_{file}"):
                selected_suggested.append(file)

    # ====== RIGHT COLUMN: Search Results ======
    with col_right:
        st.subheader("🔍 Search Results")
        st.caption("Additional documents found")

        # CRITICAL: Call FileRecommender if not already called
        if not st.session_state.documents_found:
            with st.spinner("🔍 Searching for documents..."):
                try:
                    logger.info(f"Screen 4: FileRecommender called with categories={st.session_state.confirmed_categories}")

                    if orchestrator is None:
                        show_error("Orchestrator not initialized")
                        logger.error("Screen 4: Orchestrator is None")
                        return

                    result = orchestrator.run_workflow(
                        request=st.session_state.original_request,
                        session_id=st.session_state.session_id,
                        user_id=st.session_state.user_id,
                        step=4,
                        confirmed_categories=st.session_state.confirmed_categories
                    )

                    # CHECK RESULT (learned from Day 7 - verify agent worked)
                    if not result.get("success"):
                        error_msg = result.get("error", "Unknown error")
                        logger.error(f"Screen 4: FileRecommender failed: {error_msg}")
                        show_error(f"❌ FileRecommender failed: {error_msg}")
                        st.info("Please check the Live Logs sidebar for details")
                        return

                    # SUCCESS: Populate documents_found
                    output = result.get("output", {})
                    st.session_state.documents_found = output.get("search_results", [])
                    logger.info(f"Screen 4: FileRecommender returned {len(st.session_state.documents_found)} documents")

                    # Show transparency info
                    metadata = result.get("metadata", {})
                    show_transparency_info(metadata)

                except Exception as e:
                    logger.error(f"Screen 4: Exception calling FileRecommender: {str(e)}", exc_info=True)
                    show_error(f"Error searching documents: {str(e)}", str(e))
                    return

        # Display search results as checkboxes
        if st.session_state.documents_found:
            selected_search = []
            for doc in st.session_state.documents_found:
                col_doc, col_info = st.columns([3, 1])

                with col_doc:
                    if st.checkbox(
                        doc.get('filename', 'Unknown'),
                        value=False,
                        key=f"search_{doc.get('filename')}"
                    ):
                        selected_search.append(doc.get('filename'))

                with col_info:
                    with st.expander(f"ℹ️ {doc.get('relevance_score', 0):.0%}"):
                        st.write(f"**Category**: {doc.get('category', 'Unknown')}")
                        st.write(f"**Size**: {doc.get('size', 'Unknown')}")
                        if doc.get('date_issued'):
                            st.write(f"**Date**: {doc['date_issued']}")
        else:
            st.warning("⚠️ No documents found matching your categories")
            selected_search = []

    # COMBINE: Suggested + Search results
    all_selected = list(set(selected_suggested + selected_search))
    st.session_state.selected_documents = all_selected

    logger.info(f"Screen 4: User selected {len(all_selected)} documents total")

    # CRITICAL CONSTRAINT: Block navigation if empty
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 2
            save_session_to_disk()
            st.rerun()

    with col3:
        continue_disabled = len(all_selected) == 0

        if st.button("Continue →", type="primary", use_container_width=True, disabled=continue_disabled):
            if not all_selected:
                show_error("❌ Please select at least one document to proceed")
                logger.warning("User tried to proceed without selecting documents")
                return

            # LOAD FILE CONTENTS before proceeding
            try:
                logger.info(f"Screen 4: Loading file contents for {len(all_selected)} files...")

                st.session_state.selected_file_contents = {}
                # Resolve memory directory using absolute path
                script_dir = Path(__file__).parent
                memory_dir = script_dir.parent / "local-memory" / "tax_legal"

                for doc in all_selected:
                    # Try loading from tax_database directory (files returned from FileRecommender)
                    tax_db_path = memory_dir / "tax_database" / doc

                    if tax_db_path.exists():
                        try:
                            with open(tax_db_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                st.session_state.selected_file_contents[doc] = content
                                logger.info(f"Screen 4: Loaded {doc} ({len(content)} bytes from tax_database)")
                        except Exception as e:
                            logger.warning(f"Screen 4: Failed to load {doc}: {str(e)}")
                            st.session_state.selected_file_contents[doc] = f"[Unable to load {doc}]"
                    else:
                        logger.warning(f"Screen 4: File not found in tax_database: {tax_db_path}")
                        st.session_state.selected_file_contents[doc] = f"[File not found: {doc}]"

                total_bytes = sum(len(content) for content in st.session_state.selected_file_contents.values())
                logger.info(f"Screen 4: File loading complete. Total content: {total_bytes} bytes")

                st.session_state.current_step = 4
                save_session_to_disk()

                logger.info("Screen 4: Advancing to Screen 5")
                show_success("Documents selected successfully!")
                st.rerun()

            except Exception as e:
                logger.error(f"Screen 4: File loading failed: {str(e)}", exc_info=True)
                show_error(f"❌ Failed to load files: {str(e)}")
                st.info("Check the Live Logs sidebar for technical details")
                return

# ============================================================================
# SCREEN 5: RESPONSE PREVIEW
# ============================================================================

def render_screen_5_response_preview():
    """Screen 5: Preview synthesized response with verification"""

    logger.info("Screen 5: Response Preview - STARTED")

    st.header("Step 5: Review Response")
    st.write("Review the synthesized KPMG tax memorandum before approval.")

    try:
        # Generate response if not already available
        if not hasattr(st.session_state, 'synthesized_response') or not st.session_state.synthesized_response:
            logger.info("Screen 5: Generating synthesized response (Step 5)...")

            with st.spinner("🔄 Synthesizing KPMG tax memorandum..."):
                try:
                    if not hasattr(st.session_state, 'selected_file_contents') or not st.session_state.selected_file_contents:
                        logger.error("Screen 5: No selected file contents available")
                        show_error("❌ No source documents available. Please go back and select documents.")
                        if st.button("← Back"):
                            go_to_step(3)
                        return

                    # Call orchestrator Step 5: TaxResponseCompiler
                    result = orchestrator.run_workflow(
                        request=st.session_state.original_request,
                        session_id=st.session_state.session_id,
                        user_id=st.session_state.user_id,
                        step=5,
                        selected_documents=st.session_state.selected_documents,
                        selected_file_contents=st.session_state.selected_file_contents,
                        confirmed_categories=st.session_state.confirmed_categories
                    )

                    logger.info(f"Screen 5: TaxResponseCompiler result - success={result.get('success')}")

                    if result.get("success"):
                        output = result.get("output", {})
                        st.session_state.synthesized_response = output.get("response_text", "")
                        st.session_state.sources_cited = output.get("sources_cited", [])

                        if not st.session_state.synthesized_response:
                            logger.error("Screen 5: TaxResponseCompiler returned empty response")
                            show_error("❌ Failed to generate response. Response text is empty.")
                            logger.info("Screen 5: Returning to document selection")
                            if st.button("← Back"):
                                go_to_step(3)
                            return

                        logger.info(f"Screen 5: Response generated successfully ({len(st.session_state.synthesized_response)} chars)")
                        save_session_to_disk()
                    else:
                        error_msg = result.get("error", "Unknown error")
                        logger.error(f"Screen 5: TaxResponseCompiler failed - {error_msg}")
                        show_error(f"❌ Failed to generate response: {error_msg}")
                        st.info("Check the Live Logs sidebar for technical details")
                        if st.button("← Back"):
                            go_to_step(3)
                        return

                except Exception as e:
                    logger.error(f"Screen 5: Exception during response generation: {str(e)}", exc_info=True)
                    show_error(f"❌ Error generating response: {str(e)}")
                    st.info("Check the Live Logs sidebar for technical details")
                    if st.button("← Back"):
                        go_to_step(3)
                    return

        logger.info(f"Screen 5: Response length: {len(st.session_state.synthesized_response)} chars")

        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📄 Response", "📚 Source Files", "🔗 Citations"])

        with tab1:
            st.subheader("KPMG Tax Memorandum")
            st.markdown(st.session_state.synthesized_response)
            logger.debug("Screen 5: Response tab rendered")

        with tab2:
            st.subheader("Source Documents Used")
            if hasattr(st.session_state, 'selected_documents') and st.session_state.selected_documents:
                for i, doc in enumerate(st.session_state.selected_documents, 1):
                    st.write(f"{i}. {doc}")
                logger.info(f"Screen 5: Displayed {len(st.session_state.selected_documents)} source documents")
            else:
                st.info("No source documents found")
                logger.warning("Screen 5: No selected documents in session state")

        with tab3:
            st.subheader("Citations")
            if hasattr(st.session_state, 'citations') and st.session_state.citations:
                for citation in st.session_state.citations:
                    st.write(f"- {citation.get('source', 'Unknown')} (cited {citation.get('citations_count', 1)} times)")
                logger.info(f"Screen 5: Displayed {len(st.session_state.citations)} citations")
            else:
                st.info("No citations extracted yet (will be generated on approval)")
                logger.debug("Screen 5: No citations yet - will be generated in Screen 6")

        st.divider()

        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("← Back (Refine Files)", use_container_width=True):
                logger.info("Screen 5: User chose to go back to document selection")
                go_to_step(3)

        with col3:
            if st.button("Continue to Approval →", type="primary", use_container_width=True):
                logger.info("Screen 5: User confirmed response, proceeding to verification")

                try:
                    # Call orchestrator Step 6 (verify + citation)
                    logger.info("Screen 5: Calling orchestrator for verification (Step 6)")
                    with st.spinner("Verifying response against sources..."):
                        result = orchestrator.run_workflow(
                            step=6,
                            synthesized_response=st.session_state.synthesized_response,
                            selected_file_contents=st.session_state.selected_file_contents
                        )

                    logger.info(f"Screen 5: Orchestrator result - success={result.get('success')}")

                    if result.get("success"):
                        # Extract verification results
                        st.session_state.response_with_citations = result.get("response_text", st.session_state.synthesized_response)
                        st.session_state.verification_report = result.get("verification_report", {})
                        st.session_state.citations = result.get("citations", [])

                        logger.info(f"Screen 5: Verification complete - {len(st.session_state.citations)} citations extracted")
                        logger.info(f"Screen 5: Verification report - all_verified={st.session_state.verification_report.get('all_verified', False)}")

                        st.session_state.current_step = 5
                        save_session_to_disk()
                        logger.info("Screen 5: Advancing to Screen 6 (Approval Gate)")
                        show_success("Response verified successfully!")
                        st.rerun()
                    else:
                        logger.error(f"Screen 5: Verification failed - {result.get('error', 'Unknown error')}")
                        show_error(f"❌ Verification failed: {result.get('error', 'Unknown error')}")
                        st.info("Check the Live Logs sidebar for technical details")

                except Exception as e:
                    logger.error(f"Screen 5: Verification process failed: {str(e)}", exc_info=True)
                    show_error(f"❌ Failed to verify response: {str(e)}")
                    st.info("Check the Live Logs sidebar for technical details")

        logger.info("Screen 5: Response Preview - COMPLETED")

    except Exception as e:
        logger.error(f"Screen 5: Unexpected error: {str(e)}", exc_info=True)
        show_error(f"❌ An unexpected error occurred: {str(e)}")
        st.info("Check the Live Logs sidebar for technical details")


# ============================================================================
# SCREEN 6: APPROVAL GATE
# ============================================================================

def render_screen_6_approval_gate():
    """Screen 6: Partner approval of final response"""

    logger.info("Screen 6: Approval Gate - STARTED")

    st.header("Step 6: Partner Approval")
    st.info("🔒 **This is restricted to KPMG partners only.**")

    try:
        # Check if response is available
        if not hasattr(st.session_state, 'response_with_citations') or not st.session_state.response_with_citations:
            logger.error("Screen 6: No response with citations available")
            show_error("❌ No response available. Please go back and try again.")
            if st.button("← Back"):
                go_to_step(4)
            return

        logger.info(f"Screen 6: Response length: {len(st.session_state.response_with_citations)} chars")

        # Display verification report if issues found
        if hasattr(st.session_state, 'verification_report') and st.session_state.verification_report:
            verification = st.session_state.verification_report

            logger.info(f"Screen 6: Verification report available - all_verified={verification.get('all_verified', False)}")

            if not verification.get("all_verified", True):
                st.warning("⚠️ **Verification Issues Found**")
                logger.warning(f"Screen 6: Verification issues detected - {len(verification.get('issues', []))} issues")

                with st.expander("View Issues", expanded=True):
                    issues = verification.get("issues", [])
                    if issues:
                        for i, issue in enumerate(issues, 1):
                            st.write(f"**Issue {i}**: {issue.get('issue_type', 'Unknown')} - Claim: {issue.get('claim', 'Unknown')}")
                        logger.debug(f"Screen 6: Displayed {len(issues)} verification issues")
                    else:
                        st.info("No specific issues listed")
            else:
                st.success("✅ **All claims verified against source documents**")
                logger.info("Screen 6: All verification checks passed")
        else:
            logger.debug("Screen 6: No verification report available")

        # Response with citations
        st.subheader("Final Response")
        st.markdown(st.session_state.response_with_citations)
        logger.debug("Screen 6: Final response displayed")

        # Display citations summary
        if hasattr(st.session_state, 'citations') and st.session_state.citations:
            with st.expander("📚 Citations Summary"):
                st.write(f"Total unique sources cited: {len(st.session_state.citations)}")
                for citation in st.session_state.citations:
                    st.write(f"- **{citation.get('source', 'Unknown')}**: {citation.get('citations_count', 1)} citation(s)")
                logger.debug(f"Screen 6: Displayed citations summary - {len(st.session_state.citations)} sources")

        st.divider()

        # Approval/Rejection buttons
        col1, col2 = st.columns([1, 1])

        reject_button = None
        approve_button = None

        with col1:
            reject_button = st.button("❌ Reject", use_container_width=True)

        with col2:
            approve_button = st.button("✅ Approve", type="primary", use_container_width=True)

        # Handle approval
        if approve_button:
            logger.info("Screen 6: User approved response")

            try:
                with st.spinner("Saving response and recording learning signals..."):
                    logger.info("Screen 6: Calling orchestrator.handle_approval()")

                    approval_result = orchestrator.handle_approval(
                        session_id=st.session_state.session_id,
                        user_id=st.session_state.user_id,
                        approved=True,
                        response_text=st.session_state.response_with_citations,
                        verification_report=st.session_state.verification_report,
                        citations=st.session_state.citations,
                        confirmed_categories=st.session_state.confirmed_categories,
                        selected_documents=st.session_state.selected_documents
                    )

                logger.info(f"Screen 6: Approval result - success={approval_result.get('success')}")

                if approval_result.get("success"):
                    logger.info(f"Screen 6: Response saved with ID: {approval_result.get('response_id')}")

                    show_success("✅ Response approved and saved!")
                    st.balloons()

                    # Show saved response ID
                    st.info(f"📋 Response ID: `{approval_result.get('response_id', 'unknown')}`")
                    st.caption("This ID can be used to retrieve this response later")

                    # Reset for new request
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col2:
                        if st.button("🔄 Start New Request", type="primary", use_container_width=True):
                            logger.info("Screen 6: User starting new request")
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
                            st.session_state.verification_report = {}
                            st.session_state.citations = []
                            st.session_state.approval_status = "pending"
                            st.session_state.selected_file_contents = {}
                            save_session_to_disk()
                            logger.info("Screen 6: Session reset for new request")
                            st.rerun()
                else:
                    logger.error(f"Screen 6: Approval failed - {approval_result.get('error', 'Unknown error')}")
                    show_error(f"❌ Approval failed: {approval_result.get('error', 'Unknown error')}")
                    st.info("Check the Live Logs sidebar for technical details")

            except Exception as e:
                logger.error(f"Screen 6: Approval process failed: {str(e)}", exc_info=True)
                show_error(f"❌ Failed to save response: {str(e)}")
                st.info("Check the Live Logs sidebar for technical details")

        # Handle rejection
        if reject_button:
            logger.info("Screen 6: User rejected response - returning to document selection")
            show_warning("Response rejected. Returning to document selection...")
            st.session_state.current_step = 3
            save_session_to_disk()
            st.rerun()

        logger.info("Screen 6: Approval Gate - COMPLETED")

    except Exception as e:
        logger.error(f"Screen 6: Unexpected error: {str(e)}", exc_info=True)
        show_error(f"❌ An unexpected error occurred: {str(e)}")
        st.info("Check the Live Logs sidebar for technical details")


# ============================================================================
# MAIN ROUTER
# ============================================================================

def main():
    """Main app router"""

    st.title("📋 KPMG Tax Workflow System")
    st.markdown("*English-only MVP | Phase 2 Step 3 Implementation*")
    st.divider()

    # Route based on current step
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

if __name__ == "__main__":
    main()
