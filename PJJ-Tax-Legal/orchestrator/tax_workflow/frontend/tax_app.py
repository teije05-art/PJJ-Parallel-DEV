"""
KPMG Tax Workflow System - Streamlit UI
Phase 2 Step 3: Tax/Legal Request Analysis and Response Generation

This is a separate Streamlit application (tax_app.py) for the tax/legal workflow.
It works alongside (but independent from) the Project Jupiter planning system (app.py).

Run with:
  From PJJ-Tax-Legal directory:
    streamlit run orchestrator/tax_workflow/frontend/tax_app.py

  From repository root:
    streamlit run PJJ-Tax-Legal/orchestrator/tax_workflow/frontend/tax_app.py

  Or navigate to the frontend directory and run:
    cd PJJ-Tax-Legal/orchestrator/tax_workflow/frontend
    streamlit run tax_app.py
"""

import streamlit as st
from pathlib import Path
import uuid
import json
import sys
from datetime import datetime

# Add repo to path for imports
# Use relative path from this file's location for cross-platform compatibility
REPO_ROOT = Path(__file__).parent.parent.parent.parent

# Debug: show what we're doing
# print(f"REPO_ROOT: {REPO_ROOT}")
# print(f"REPO_ROOT exists: {REPO_ROOT.exists()}")

if str(REPO_ROOT) not in sys.path:
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
    st.error(f"sys.path: {sys.path}")
    st.stop()

# Initialize logging system
setup_logging()
logger = get_logger(__name__)

# NEW: Initialize Agent with knowledge base path
MEMORY_PATH = REPO_ROOT.parent / "local-memory" / "tax_legal"
try:
    agent = Agent(memory_path=str(MEMORY_PATH))
    logger.info("Agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Agent: {e}")
    st.error(f"Failed to initialize Agent: {e}")
    st.stop()

# NEW: Initialize TaxOrchestrator
try:
    orchestrator = TaxOrchestrator(agent, MEMORY_PATH)
    logger.info("TaxOrchestrator initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize TaxOrchestrator: {e}")
    st.error(f"Failed to initialize TaxOrchestrator: {e}")
    st.stop()


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
# SESSION STATE INITIALIZATION
# ============================================================================

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "workflow_stage" not in st.session_state:
    st.session_state.workflow_stage = "step_1_request"

if "request_text" not in st.session_state:
    st.session_state.request_text = ""

if "suggested_categories" not in st.session_state:
    st.session_state.suggested_categories = []

if "confirmed_categories" not in st.session_state:
    st.session_state.confirmed_categories = []

if "past_responses" not in st.session_state:
    st.session_state.past_responses = []

if "selected_past_responses" not in st.session_state:
    st.session_state.selected_past_responses = []

if "recommended_files" not in st.session_state:
    st.session_state.recommended_files = []

if "selected_files" not in st.session_state:
    st.session_state.selected_files = []

if "compiled_response" not in st.session_state:
    st.session_state.compiled_response = ""

if "verification_report" not in st.session_state:
    st.session_state.verification_report = {}

if "cited_response" not in st.session_state:
    st.session_state.cited_response = ""

# ============================================================================
# TITLE
# ============================================================================

col1, col2 = st.columns([1, 4])
with col1:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/KPMG.svg/1200px-KPMG.svg.png", width=80)
with col2:
    st.title("Tax Workflow System")
    st.markdown("*Intelligent tax analysis and response generation*")

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.header("⚙️ System Control")
    
    # Session info
    st.markdown(f"**Session ID**: `{st.session_state.session_id[:8]}...`")
    st.markdown(f"**Current Stage**: {st.session_state.workflow_stage}")
    
    # Clear session
    if st.button("🔄 Reset Workflow"):
        for key in st.session_state.keys():
            if key != "session_id":
                del st.session_state[key]
        st.rerun()
    
    # View logs
    st.markdown("---")
    if st.checkbox("📊 Show Logs"):
        log_file = REPO_ROOT / "orchestrator" / "tax_workflow" / "frontend" / "streamlit_instance_info" / "logs" / "tax_app.log"
        if log_file.exists():
            try:
                recent_logs = tail_log_file(str(log_file), lines=20)
                st.markdown("**Recent Logs**:")
                st.code(recent_logs, language="text")
            except Exception as e:
                st.warning(f"Could not load logs: {e}")

# ============================================================================
# STEP 1: REQUEST SUBMISSION & CATEGORIZATION
# ============================================================================

if st.session_state.workflow_stage in ["step_1_request", "start"]:
    st.markdown("## Step 1: Submit Tax Request & Get Categories")
    st.markdown("""
    <div class="user-boundary">
    <strong>User Input Needed:</strong> Submit your tax question or request. The system will analyze it and suggest relevant tax domains.
    </div>
    """, unsafe_allow_html=True)
    
    request_input = st.text_area(
        "Enter your tax request:",
        value=st.session_state.request_text,
        height=150,
        placeholder="E.g., 'We have a Vietnam subsidiary that imports pharmaceutical products. What are the key transfer pricing considerations...'"
    )
    
    if st.button("📝 Submit Request & Analyze", key="btn_step1"):
        if not request_input.strip():
            st.error("Please enter a tax request")
        else:
            with st.spinner("Analyzing request..."):
                try:
                    # Initialize orchestrator                    
                    # Step 1: Categorize request
                    logger.info(f"Step 1: Categorizing request (length: {len(request_input)})")
                    categorization_result = orchestrator.run_workflow(request_input, st.session_state.session_id, 'user', step=1)
                    
                    if categorization_result.get('success'):
                        st.session_state.request_text = request_input
                        st.session_state.suggested_categories = categorization_result.get('output').get("suggested_categories", [])
                        st.session_state.workflow_stage = "step_1_review"
                        st.success("✓ Request categorized successfully")
                        st.rerun()
                    else:
                        st.error(f"Categorization failed: {categorization_result.get('error', '')}")
                        logger.error(f"Categorization error: {categorization_result.get('error', '')}")
                
                except Exception as e:
                    st.error(f"Error during categorization: {str(e)}")
                    logger.error(f"Exception: {str(e)}", exc_info=True)

# ============================================================================
# STEP 1: CATEGORY REVIEW & CONFIRMATION
# ============================================================================

if st.session_state.workflow_stage == "step_1_review":
    st.markdown("## Step 1: Review Suggested Categories")
    st.markdown("""
    <div class="user-boundary">
    <strong>User Review Needed:</strong> The system has identified these relevant tax categories. Confirm the ones you want to search with.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("**Suggested Categories:**")
    for cat in st.session_state.suggested_categories:
        st.markdown(f"<span class='category-pill'>{cat}</span>", unsafe_allow_html=True)
    
    confirmed = st.multiselect(
        "Select categories to use (or leave empty to use suggestions):",
        options=st.session_state.suggested_categories,
        default=st.session_state.suggested_categories,
        key="category_multiselect"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm Categories", key="btn_confirm_cats"):
            if not confirmed and not st.session_state.suggested_categories:
                st.error("No categories selected")
            else:
                final_cats = confirmed if confirmed else st.session_state.suggested_categories
                st.session_state.confirmed_categories = final_cats
                st.session_state.workflow_stage = "step_2_search"
                st.rerun()
    
    with col2:
        if st.button("← Back", key="btn_back_to_request"):
            st.session_state.workflow_stage = "step_1_request"
            st.rerun()

# ============================================================================
# STEP 2: PAST RESPONSE SEARCH
# ============================================================================

if st.session_state.workflow_stage == "step_2_search":
    st.markdown("## Step 2: Search Past Tax Responses")
    st.markdown("""
    <div class="user-boundary">
    <strong>Automatic Search:</strong> The system is searching for similar past tax advice cases in your approved categories.
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Searching past responses..."):
        try:            
            search_result = orchestrator.run_workflow(st.session_state.request_text, st.session_state.session_id, 'user', step=2, confirmed_categories=st.session_state.confirmed_categories)

            if search_result.get('success'):
                st.session_state.past_responses = search_result.get('output', {}).get('past_responses', [])
                st.success(f"✓ Found {len(st.session_state.past_responses)} past responses")
                st.session_state.workflow_stage = "step_2_review"
                st.rerun()
            else:
                st.warning(f"No past responses found: {search_result.get('error', '')}")
                st.session_state.past_responses = []
                st.session_state.workflow_stage = "step_4_recommend"
                st.rerun()
        
        except Exception as e:
            st.error(f"Error searching past responses: {str(e)}")
            logger.error(f"Search error: {str(e)}", exc_info=True)

# ============================================================================
# STEP 2/3: PAST RESPONSE REVIEW & SELECTION
# ============================================================================

if st.session_state.workflow_stage == "step_2_review":
    st.markdown("## Step 2/3: Review Past Responses")
    st.markdown("""
    <div class="user-boundary">
    <strong>User Review Needed:</strong> Select which past responses to use as reference for the current request.
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.past_responses:
        # === CONTENT PREVIEW SECTION ===
        st.markdown("### 📄 Past Response Previews")
        st.markdown("*Preview the content of each past response before selecting*")

        for i, r in enumerate(st.session_state.past_responses):
            filename = r.get("filename", f"Response {i}")
            with st.expander(f"📄 {filename}", expanded=False):
                # Show clean text content (summary field = 250 chars)
                content = r.get("summary", "No content available")
                st.markdown("**Content Preview (first 250 characters):**")
                st.text(content)  # Clean text display, not JSON

                # Show metadata
                st.markdown("---")
                st.markdown(f"**Categories:** {', '.join(r.get('categories', []))}")
                st.markdown(f"**Date Created:** {r.get('date_created', 'Unknown')}")
                st.markdown(f"**Files Used:** {', '.join(r.get('files_used', []))}")

        st.markdown("---")
        # === END CONTENT PREVIEW SECTION ===

        selected = st.multiselect(
            "Select past responses to use:",
            options=[r.get("filename", f"Response {i}") for i, r in enumerate(st.session_state.past_responses)],
            key="past_responses_select"
        )
        
        st.session_state.selected_past_responses = [
            st.session_state.past_responses[i]
            for i, r in enumerate(st.session_state.past_responses)
            if r.get("filename") in selected
        ]
    else:
        st.info("No past responses to select from")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("→ Continue to Document Search", key="btn_next_to_docs"):
            st.session_state.workflow_stage = "step_4_recommend"
            st.rerun()
    with col2:
        if st.button("← Back", key="btn_back_to_cats"):
            st.session_state.workflow_stage = "step_1_review"
            st.rerun()

# ============================================================================
# STEP 4: TAX DATABASE SEARCH & RECOMMENDATION
# ============================================================================

if st.session_state.workflow_stage == "step_4_recommend":
    st.markdown("## Step 4: Search Tax Database for Regulations")
    st.markdown("""
    <div class="user-boundary">
    <strong>Automatic Search:</strong> The system is searching for relevant tax regulations and source documents.
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Searching tax database..."):
        try:            
            # Pass selected past response filenames as suggested files
            suggested_files = [r.get("filename") for r in st.session_state.selected_past_responses] if st.session_state.selected_past_responses else None
            
            recommend_result = orchestrator.run_workflow(st.session_state.request_text, st.session_state.session_id, 'user', step=4, confirmed_categories=st.session_state.confirmed_categories)

            if recommend_result.get('success'):
                st.session_state.recommended_files = recommend_result.get('output', {}).get('search_results', [])
                st.success(f"✓ Found {len(st.session_state.recommended_files)} recommended documents")
                st.session_state.workflow_stage = "step_4_review"
                st.rerun()
            else:
                st.error(f"Document search failed: {recommend_result.get('error', '')}")
        
        except Exception as e:
            st.error(f"Error searching documents: {str(e)}")
            logger.error(f"Recommend error: {str(e)}", exc_info=True)

# ============================================================================
# STEP 4/5: DOCUMENT REVIEW & SELECTION
# ============================================================================

if st.session_state.workflow_stage == "step_4_review":
    st.markdown("## Step 4/5: Select Source Documents")
    st.markdown("""
    <div class="user-boundary">
    <strong>User Selection Needed:</strong> Select which documents to use for synthesizing the response.
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.recommended_files:
        # === CONTENT PREVIEW SECTION ===
        st.markdown("### 📋 Document Previews")
        st.markdown("*Preview the content of each document before selecting*")

        for i, d in enumerate(st.session_state.recommended_files):
            filename = d.get("filename", f"Document {i}")
            with st.expander(f"📋 {filename}", expanded=False):
                # Show clean text content (summary field = 250 chars)
                content = d.get("summary", "No content available")
                st.markdown("**Content Preview (first 250 characters):**")
                st.text(content)  # Clean text display, not JSON

                # Show metadata
                st.markdown("---")
                st.markdown(f"**Category:** {d.get('category', 'Unknown')}")
                st.markdown(f"**Date Issued:** {d.get('date_issued', 'Unknown')}")

        st.markdown("---")
        # === END CONTENT PREVIEW SECTION ===

        selected_docs = st.multiselect(
            "Select documents to use:",
            options=[d.get("filename", f"Document {i}") for i, d in enumerate(st.session_state.recommended_files)],
            key="docs_select"
        )
        
        st.session_state.selected_files = [
            st.session_state.recommended_files[i]
            for i, d in enumerate(st.session_state.recommended_files)
            if d.get("filename") in selected_docs
        ]
    else:
        st.warning("No documents found")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("→ Synthesize Response", key="btn_synthesize"):
            if not st.session_state.selected_files:
                st.error("Please select at least one document")
            else:
                st.session_state.workflow_stage = "step_5_compile"
                st.rerun()
    with col2:
        if st.button("← Back", key="btn_back_to_search"):
            st.session_state.workflow_stage = "step_4_recommend"
            st.rerun()

# ============================================================================
# STEP 5: RESPONSE COMPILATION
# ============================================================================

if st.session_state.workflow_stage == "step_5_compile":
    st.markdown("## Step 5: Synthesize KPMG Response")
    st.markdown("""
    <div class="user-boundary">
    <strong>Automatic Synthesis:</strong> The system is generating a professional tax memorandum based on your selected documents.
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Synthesizing response..."):
        try:
            # Build file contents dict
            file_contents = {}
            for doc in st.session_state.selected_files:
                filename = doc.get("filename")
                # Use full content (3000 chars) for synthesis, not summary
                file_contents[filename] = doc.get("content", "")
            
            compile_result = orchestrator.run_workflow(st.session_state.request_text, st.session_state.session_id, 'user', step=6, confirmed_categories=st.session_state.confirmed_categories, selected_documents=[d.get('filename') for d in st.session_state.selected_files], selected_file_contents=file_contents)

            if compile_result.get('success'):
                st.session_state.compiled_response = compile_result.get('output', {}).get('response', '')
                st.success("✓ Response synthesized and verified successfully")
                st.session_state.workflow_stage = "step_6_verify"
                st.rerun()
            else:
                st.error(f"Response compilation failed: {compile_result.get('error', '')}")
        
        except Exception as e:
            st.error(f"Error synthesizing response: {str(e)}")
            logger.error(f"Compile error: {str(e)}", exc_info=True)

# ============================================================================
# STEP 6a: VERIFICATION
# ============================================================================

if st.session_state.workflow_stage == "step_6_verify":
    st.markdown("## Step 6a: Verify Response Against Sources")
    st.markdown("""
    <div class="user-boundary">
    <strong>Quality Gate:</strong> The system is verifying that all claims are sourced to your provided documents.
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Verifying claims..."):
        try:
            # Build file contents
            file_contents = {}
            for doc in st.session_state.selected_files:
                filename = doc.get("filename")
                # Use full content (3000 chars) for verification, not summary
                file_contents[filename] = doc.get("content", "")
            
            verify_result = orchestrator.run_workflow(st.session_state.request_text, st.session_state.session_id, 'user', step=6, confirmed_categories=st.session_state.confirmed_categories, selected_documents=[d.get('filename') for d in st.session_state.selected_files], selected_file_contents=file_contents)
            
            st.session_state.verification_report = verify_result.get('output', {})
            st.success("✓ Verification complete")
            st.session_state.workflow_stage = "step_6_cite"
            st.rerun()
        
        except Exception as e:
            st.error(f"Error verifying response: {str(e)}")
            logger.error(f"Verify error: {str(e)}", exc_info=True)

# ============================================================================
# STEP 6b: CITATION TRACKING
# ============================================================================

if st.session_state.workflow_stage == "step_6_cite":
    st.markdown("## Step 6b: Embed Citations")
    st.markdown("""
    <div class="user-boundary">
    <strong>Final Step:</strong> The system is adding source citations to the response.
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Embedding citations..."):
        try:
            file_contents = {}
            for doc in st.session_state.selected_files:
                filename = doc.get("filename")
                # Use full content (3000 chars) for citations, not summary
                file_contents[filename] = doc.get("content", "")
            
            cite_result = orchestrator.run_workflow(st.session_state.request_text, st.session_state.session_id, 'user', step=6, confirmed_categories=st.session_state.confirmed_categories, selected_documents=[d.get('filename') for d in st.session_state.selected_files], selected_file_contents=file_contents)
            
            st.session_state.cited_response = cite_result.get('output', {}).get("response_text", st.session_state.compiled_response)
            st.success("✓ Citations embedded successfully")
            st.session_state.workflow_stage = "complete"
            st.rerun()
        
        except Exception as e:
            st.error(f"Error embedding citations: {str(e)}")
            logger.error(f"Citation error: {str(e)}", exc_info=True)

# ============================================================================
# FINAL RESPONSE
# ============================================================================

if st.session_state.workflow_stage == "complete":
    st.markdown("## ✅ Tax Analysis Complete")
    
    # Show compiled response
    with st.expander("📄 Final Response", expanded=True):
        st.markdown(st.session_state.cited_response)
    
    # Show verification report
    if st.session_state.verification_report:
        with st.expander("✓ Verification Report"):
            st.json(st.session_state.verification_report)
    
    # Export options
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Copy to Clipboard"):
            st.write("Response copied to clipboard")
    
    with col2:
        if st.button("🔄 Start New Analysis"):
            for key in st.session_state.keys():
                if key != "session_id":
                    del st.session_state[key]
            st.rerun()

