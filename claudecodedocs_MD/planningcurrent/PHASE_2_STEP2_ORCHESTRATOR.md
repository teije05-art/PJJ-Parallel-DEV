# DETAILED PHASE 2 STEP 2: Orchestrator Implementation

## STEP 2 OVERVIEW

**Goal**: Create TaxOrchestrator that wires all 6 agents into coordinated 6-step workflow

**Duration**: Days 5-6 (Implementation)
**Scope**: 1 orchestrator file (200-250 lines)
**Location**: `orchestrator/tax_workflow/tax_orchestrator.py`
**Output**: Complete working tax workflow (Steps 1-6)

---

## PART 1: MEMAGENT SEGMENT ALLOCATION & CONSTRAINTS

### 1.0 Memory Segment Allocation (Critical for Constraint Boundaries)

```
MemAgent has 12 fixed segments (2,000 tokens each, all for tax/legal workflow):

TAX/LEGAL WORKFLOW SEGMENTS:
├─ Segment 0: Past responses - Tier 1 (newest approved responses)
├─ Segment 1: Past responses - Tier 2 (older approved responses)
├─ Segment 2: Past responses - Tier 3 (archive of successful responses)
├─ Segment 3: Past responses - Tier 4 (overflow if > 3 segments used)
├─ Segment 4: Tax database - VAT documents, circulars, recent guidance
├─ Segment 5: Tax database - CIT documents, deduction rules, rates
├─ Segment 6: Tax database - Transfer Pricing rules, comparability studies
├─ Segment 7: Tax database - PIT, FCT, DTA documents
├─ Segment 8: Tax database - Special categories, customs, excise
├─ Segment 9: Tax database - Environmental tax, capital gains
├─ Segment 10: Tax database - Emerging guidance, regulatory updates
├─ Segment 11: Tax database - Overflow / category-specific documents

CONSTRAINT ENFORCEMENT:
- Tax agents search ONLY segments [0-3] for past responses
- Tax agents search ONLY segments [4-11] for tax documents
- All 12 segments dedicated to tax/legal workflow only
- Cross-contamination prevented by explicit segment lists in each agent
```

### 1.1 TaxOrchestrator Overview (Single Source of Truth)

**File**: `orchestrator/tax_workflow/tax_orchestrator.py`
**Lines**: ~200-250
**Responsibility**: Wire 6 agents into 6-step workflow, manage state, handle errors, trigger learning

**Memory Configuration** (CRITICAL):
```python
# TaxOrchestrator MUST use tax_legal namespace
memory_path = Path("local-memory/tax_legal")  # ← Isolated from PJJ-old

orchestrator = TaxOrchestrator(
    agent=llama_client,
    memory_path=memory_path,  # ← Passes to all agents
    segmented_memory=SegmentedMemory(
        memory_path=memory_path,  # ← MemAgent reads/writes to tax_legal/
        max_segments=12,
        segment_allocation={
            'response_segments': [0, 1, 2, 3],
            'document_segments': [4, 5, 6, 7, 8, 9, 10, 11]
        }
    ),
    learning_manager=learning_manager,
    approval_gates=approval_gates
)

# All agents inherit memory_path:
# - TaxResponseSearcher reads: local-memory/tax_legal/entities/
# - FileRecommender reads: local-memory/tax_legal/tax_database/
# - TaxResponseCompiler writes: local-memory/tax_legal/entities/
```

**Single Source of Truth for Saving** (prevents truncation like old system):
- ONLY save point: `orchestrator.memory_manager.store_results()` (called after approval)
- NEVER save from individual agents
- NEVER save from multiple locations
- Agents return AgentResult only (data contract, no side effects)
- All saves use constraint metadata from agents to track boundary violations

**Constructor**:
```python
class TaxOrchestrator(BaseAgent):
    def __init__(
        self,
        agent: Agent,
        memory_path: Path,
        segmented_memory: SegmentedMemory,
        learning_manager: LearningManager,
        approval_gates: SessionManager
    ):
        super().__init__(agent, memory_path)
        self.segmented_memory = segmented_memory
        self.learning_manager = learning_manager
        self.approval_gates = approval_gates

        # Initialize all 6 agents
        self.request_categorizer = RequestCategorizer(agent, memory_path)
        self.response_searcher = TaxResponseSearcher(agent, memory_path, segmented_memory)
        self.file_recommender = FileRecommender(agent, memory_path, segmented_memory)
        self.response_compiler = TaxResponseCompiler(agent, memory_path)
        self.document_verifier = DocumentVerifier(agent, memory_path)
        self.citation_tracker = CitationTracker(agent, memory_path)
```

**Main Entry Point**:
```python
def run(
    self,
    request: str,
    session_id: str,
    user_id: str,
    tax_domain: str = "income"
) -> Dict[str, Any]:
    """
    Execute complete 6-step tax workflow.

    Returns:
        {
            "success": bool,
            "response": str,
            "citations": List[Dict],
            "metadata": {
                "steps_completed": int,
                "processing_time_ms": int,
                "approval_status": str
            }
        }
    """
    pass
```

### 1.2 6-Step Execution Flow

```
STEP 1: REQUEST CATEGORIZATION
  Input: request_text → RequestCategorizer
  Output: suggested_categories
  State: Store in session.suggested_categories
  ↓

STEP 2: PAST RESPONSE SEARCH
  Input: request_text, categories → TaxResponseSearcher
  Output: past_responses (top-5)
  State: Store in session.past_responses_found
  ↓

STEP 3: USER SELECTION (Streamlit handles)
  Input: User clicks "Accept past response" or "Search new"
  State: session.selected_past_response (or None)
  ↓

STEP 4: DOCUMENT SEARCH
  Input: request_text, categories, suggested_files → FileRecommender
  Output: search_results
  State: Store in session.documents_found
  ↓

STEP 5: USER REFINEMENT (Streamlit handles)
  Input: User selects which documents to use
  State: session.selected_documents (List[str])
  ↓

STEP 6a: RESPONSE SYNTHESIS
  Input: request_text, selected_documents, file_contents → TaxResponseCompiler
  Output: synthesized_response
  State: Store in session.synthesized_response
  ↓

STEP 6b: VERIFICATION
  Input: response, file_contents → DocumentVerifier
  Output: verification_report
  State: Store in session.verification_report
  ↓

STEP 6c: CITATION
  Input: response, file_contents → CitationTracker
  Output: response_with_citations, citations
  State: Store in session.response_with_citations, session.citations
  ↓

STEP 6d: APPROVAL GATE (Streamlit handles)
  Input: User clicks "Approve" or "Reject"
  State: session.approval_status = "approved" | "rejected"
  ↓

IF APPROVED:
  → Save response to past_responses/
  → Record learning signals
  → Flow-GRPO training
  → Update MemAgent memory

IF REJECTED:
  → Go back to Step 5 (refine files)
```

---

## PART 2: STATE MANAGEMENT

### 2.1 TaxPlanningSession (Extension of PlanningSession)

```python
# In approval_gates.py (extend existing)
class TaxPlanningSession(PlanningSession):
    """Extended session for tax workflow"""

    # Base (inherited from PlanningSession)
    session_id: str
    user_id: str
    memory_manager: SegmentedMemory
    checkpoint_summaries: Dict[str, str]
    iteration_progress: Dict[str, Any]

    # Tax-specific additions
    tax_domain: str                      # e.g., "income", "transfer_pricing"
    original_request: str                # User's exact request
    suggested_categories: List[str]      # From RequestCategorizer
    confirmed_categories: List[str]      # After user confirmation
    past_responses_found: List[Dict]     # From TaxResponseSearcher
    selected_past_response: Dict | None  # User choice (optional)
    documents_found: List[Dict]          # From FileRecommender
    selected_documents: List[str]        # User selected filenames
    selected_file_contents: Dict[str, str]  # {filename: content}
    synthesized_response: str            # From TaxResponseCompiler
    verification_report: Dict            # From DocumentVerifier
    response_with_citations: str         # From CitationTracker
    citations: List[Dict]                # List of citations used
    approval_status: str                 # "pending", "approved", "rejected"
    current_step: int                    # 1-6
    iteration_history: List[Dict]        # Track user decisions
```

### 2.2 State Transitions & Persistence

**State Saved to Disk** (for recovery if Streamlit session lost):

```python
# In orchestrator, after each step:
session_file = memory_path / f"users/{user_id}/sessions/{session_id}.json"

session_data = {
    "current_step": session.current_step,
    "original_request": session.original_request,
    "suggested_categories": session.suggested_categories,
    "confirmed_categories": session.confirmed_categories,
    "past_responses_found": session.past_responses_found,
    "selected_past_response": session.selected_past_response,
    "documents_found": session.documents_found,
    "selected_documents": session.selected_documents,
    "approval_status": session.approval_status,
    "timestamp": datetime.now().isoformat()
}

# Save to file
with open(session_file, 'w') as f:
    json.dump(session_data, f)
```

**State Recovery** (if Streamlit refreshes):

```python
def load_session(session_id: str, user_id: str) -> TaxPlanningSession:
    """Restore session from disk"""
    session_file = memory_path / f"users/{user_id}/sessions/{session_id}.json"

    if session_file.exists():
        with open(session_file, 'r') as f:
            data = json.load(f)
        # Restore session object from data
        session = TaxPlanningSession(...)
        session.current_step = data["current_step"]
        # ... restore all fields
        return session
    else:
        # New session
        return TaxPlanningSession(session_id, user_id, ...)
```

---

## PART 3: COMPLETE ORCHESTRATOR CODE SKELETON

```python
# orchestrator/tax_workflow/tax_orchestrator.py

import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import time

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent import Agent
from orchestrator.agents.base_agent import BaseAgent, AgentResult
from orchestrator.memory.memagent_memory import SegmentedMemory
from orchestrator.learning.learning_manager import LearningManager
from approval_gates import SessionManager, TaxPlanningSession

# Import all 6 agents
from .tax_planner_agent import RequestCategorizer
from .tax_searcher_agent import TaxResponseSearcher
from .tax_recommender_agent import FileRecommender
from .tax_compiler_agent import TaxResponseCompiler
from .tax_verifier_agent import DocumentVerifier
from .tax_tracker_agent import CitationTracker


class TaxOrchestrator(BaseAgent):
    """
    Main orchestrator for tax workflow (Steps 1-6).

    Coordinates all 6 agents, manages session state,
    handles errors, and triggers learning signals.
    """

    def __init__(
        self,
        agent: Agent,
        memory_path: Path,
        segmented_memory: SegmentedMemory,
        learning_manager: LearningManager,
        session_manager: SessionManager
    ):
        super().__init__(agent, memory_path)
        self.agent = agent
        self.segmented_memory = segmented_memory
        self.learning_manager = learning_manager
        self.session_manager = session_manager
        self.memory_path = memory_path

        # Initialize all 6 agents
        self.request_categorizer = RequestCategorizer(agent, memory_path)
        self.response_searcher = TaxResponseSearcher(agent, memory_path, segmented_memory)
        self.file_recommender = FileRecommender(agent, memory_path, segmented_memory)
        self.response_compiler = TaxResponseCompiler(agent, memory_path)
        self.document_verifier = DocumentVerifier(agent, memory_path)
        self.citation_tracker = CitationTracker(agent, memory_path)

    def run(
        self,
        request: str,
        session_id: str,
        user_id: str,
        tax_domain: str = "income"
    ) -> Dict[str, Any]:
        """
        Execute complete 6-step workflow.

        Args:
            request: Client request text
            session_id: Unique session ID
            user_id: User identifier
            tax_domain: Tax domain (for later use)

        Returns:
            {
                "success": bool,
                "current_step": int,
                "response": str or None,
                "metadata": {...}
            }
        """
        start_time = time.time()

        try:
            # Get or create session
            session = self.session_manager.get_or_create_tax_session(
                session_id, user_id, self.memory_path
            )
            session.tax_domain = tax_domain
            session.original_request = request

            # ============================================================================
            # STEP 1: REQUEST CATEGORIZATION
            # ============================================================================
            # CONSTRAINT: RequestCategorizer suggests categories that will become
            # the boundary for all downstream searches. These are the user's control point.

            if session.current_step <= 1:
                step_1_result = self._execute_step_1_categorization(session, request)

                if not step_1_result["success"]:
                    return {
                        "success": False,
                        "current_step": 1,
                        "error": step_1_result["error"],
                        "metadata": {"error_time_ms": int((time.time() - start_time) * 1000)}
                    }

                session.suggested_categories = step_1_result["suggested_categories"]
                session.current_step = 1
                self._save_session(session)

                return {
                    "success": True,
                    "current_step": 1,
                    "action_required": "confirm_categories",
                    "suggested_categories": session.suggested_categories,
                    "metadata": {
                        "step": "categorization",
                        "status": "awaiting user confirmation"
                    }
                }

            # ============================================================================
            # STEP 2: PAST RESPONSE SEARCH
            # ============================================================================
            # CONSTRAINT: TaxResponseSearcher uses confirmed_categories as boundary.
            # Searches ONLY segments [0,1,2,3]. If categories empty, returns empty (no autonomous search).

            if session.current_step <= 2 and session.confirmed_categories:
                step_2_result = self._execute_step_2_search(session, request)

                if not step_2_result["success"]:
                    return {
                        "success": False,
                        "current_step": 2,
                        "error": step_2_result["error"]
                    }

                session.past_responses_found = step_2_result["past_responses"]
                session.current_step = 2
                self._save_session(session)

                return {
                    "success": True,
                    "current_step": 2,
                    "action_required": "select_past_response",
                    "past_responses": session.past_responses_found,
                    "metadata": {
                        "step": "past response search",
                        "found": len(session.past_responses_found)
                    }
                }

            # ============================================================================
            # STEP 3: USER SELECTION (Streamlit handles)
            # ============================================================================

            # No processing here - Streamlit captures user selection
            # When user decides to continue to Step 4, call run() again

            # ============================================================================
            # STEP 4: DOCUMENT SEARCH
            # ============================================================================
            # CONSTRAINT: FileRecommender searches tax database for documents matching confirmed_categories.
            # Searches ONLY segments [4-11]. If categories empty, returns empty (no autonomous search).
            # Results filtered to ensure only category-matching documents are returned.

            if session.current_step <= 4:
                suggested_files = []
                if session.selected_past_response:
                    suggested_files = session.selected_past_response.get("files_used", [])

                step_4_result = self._execute_step_4_search(
                    session, request, suggested_files
                )

                if not step_4_result["success"]:
                    return {
                        "success": False,
                        "current_step": 4,
                        "error": step_4_result["error"]
                    }

                session.documents_found = step_4_result["documents"]
                session.current_step = 4
                self._save_session(session)

                return {
                    "success": True,
                    "current_step": 4,
                    "action_required": "select_documents",
                    "suggested_files": suggested_files,
                    "search_results": session.documents_found,
                    "metadata": {
                        "step": "document search",
                        "total_found": len(session.documents_found)
                    }
                }

            # ============================================================================
            # STEP 5: RESPONSE SYNTHESIS
            # ============================================================================
            # CONSTRAINT: TaxResponseCompiler uses ONLY selected documents as source of truth.
            # Llama is prompted to cite every statement. No external knowledge allowed.

            if session.current_step <= 5 and session.selected_documents:
                # Load file contents
                step_5_result = self._execute_step_5_synthesis(session)

                if not step_5_result["success"]:
                    return {
                        "success": False,
                        "current_step": 5,
                        "error": step_5_result["error"]
                    }

                session.synthesized_response = step_5_result["response"]
                session.current_step = 5
                self._save_session(session)

                return {
                    "success": True,
                    "current_step": 5,
                    "action_required": "verify_and_approve",
                    "response": session.synthesized_response,
                    "metadata": {
                        "step": "response synthesis",
                        "files_used": len(session.selected_documents)
                    }
                }

            # ============================================================================
            # STEP 6: VERIFICATION + CITATION
            # ============================================================================
            # CONSTRAINT: DocumentVerifier checks response against selected_documents only (no external sources).
            # CitationTracker embeds citations from selected_documents only.
            # Quality Gate: If >10% of claims unsourced, flag for revision.

            if session.current_step <= 6:
                step_6_result = self._execute_step_6_verification_and_citation(session)

                if not step_6_result["success"]:
                    return {
                        "success": False,
                        "current_step": 6,
                        "error": step_6_result["error"]
                    }

                session.verification_report = step_6_result["verification"]
                session.response_with_citations = step_6_result["response_with_citations"]
                session.citations = step_6_result["citations"]
                session.current_step = 6
                session.approval_status = "pending"
                self._save_session(session)

                return {
                    "success": True,
                    "current_step": 6,
                    "action_required": "partner_approval",
                    "response": session.response_with_citations,
                    "verification_report": session.verification_report,
                    "citations": session.citations,
                    "metadata": {
                        "step": "verification and citation",
                        "verified": session.verification_report.get("all_verified", False)
                    }
                }

            # If we get here, all steps completed but not approved yet
            return {
                "success": True,
                "current_step": 6,
                "status": "awaiting approval",
                "metadata": {}
            }

        except Exception as e:
            return {
                "success": False,
                "current_step": session.current_step if 'session' in locals() else 0,
                "error": f"Workflow error: {str(e)}",
                "metadata": {
                    "error_type": type(e).__name__,
                    "total_time_ms": int((time.time() - start_time) * 1000)
                }
            }

    # ============================================================================
    # STEP IMPLEMENTATIONS
    # ============================================================================

    def _execute_step_1_categorization(
        self,
        session: TaxPlanningSession,
        request: str
    ) -> Dict[str, Any]:
        """Execute Step 1: Request Categorization"""
        try:
            result = self.request_categorizer.generate(request)

            if not result.success:
                return {
                    "success": False,
                    "error": result.error
                }

            return {
                "success": True,
                "suggested_categories": result.output.get("suggested_categories", []),
                "confidence": result.output.get("confidence", 0)
            }

        except Exception as e:
            return {"success": False, "error": f"Categorization failed: {str(e)}"}

    def _execute_step_2_search(
        self,
        session: TaxPlanningSession,
        request: str
    ) -> Dict[str, Any]:
        """Execute Step 2: Past Response Search"""
        try:
            result = self.response_searcher.generate(
                request=request,
                categories=session.confirmed_categories
            )

            if not result.success:
                return {
                    "success": False,
                    "error": result.error
                }

            return {
                "success": True,
                "past_responses": result.output
            }

        except Exception as e:
            return {"success": False, "error": f"Past response search failed: {str(e)}"}

    def _execute_step_4_search(
        self,
        session: TaxPlanningSession,
        request: str,
        suggested_files: List[str]
    ) -> Dict[str, Any]:
        """Execute Step 4: Document Search"""
        try:
            result = self.file_recommender.generate(
                request=request,
                categories=session.confirmed_categories,
                suggested_files=suggested_files if suggested_files else None
            )

            if not result.success:
                return {
                    "success": False,
                    "error": result.error
                }

            return {
                "success": True,
                "documents": result.output.get("search_results", [])
            }

        except Exception as e:
            return {"success": False, "error": f"Document search failed: {str(e)}"}

    def _execute_step_5_synthesis(self, session: TaxPlanningSession) -> Dict[str, Any]:
        """Execute Step 5: Response Synthesis"""
        try:
            # Load file contents from disk
            selected_file_contents = self._load_file_contents(session.selected_documents)

            result = self.response_compiler.generate(
                request=session.original_request,
                selected_files=session.selected_documents,
                selected_file_contents=selected_file_contents,
                categories=session.confirmed_categories
            )

            if not result.success:
                return {
                    "success": False,
                    "error": result.error
                }

            return {
                "success": True,
                "response": result.output
            }

        except Exception as e:
            return {"success": False, "error": f"Response synthesis failed: {str(e)}"}

    def _execute_step_6_verification_and_citation(
        self,
        session: TaxPlanningSession
    ) -> Dict[str, Any]:
        """Execute Step 6: Verification + Citation"""
        try:
            selected_file_contents = self._load_file_contents(session.selected_documents)

            # Verification
            verify_result = self.document_verifier.generate(
                response=session.synthesized_response,
                selected_file_contents=selected_file_contents
            )

            if not verify_result.success:
                return {
                    "success": False,
                    "error": verify_result.error
                }

            # Citation
            cite_result = self.citation_tracker.generate(
                response=session.synthesized_response,
                selected_file_contents=selected_file_contents
            )

            if not cite_result.success:
                return {
                    "success": False,
                    "error": cite_result.error
                }

            return {
                "success": True,
                "verification": verify_result.output,
                "response_with_citations": cite_result.output.get("response_text", session.synthesized_response),
                "citations": cite_result.output.get("citations", [])
            }

        except Exception as e:
            return {"success": False, "error": f"Verification/citation failed: {str(e)}"}

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def _load_file_contents(self, filenames: List[str]) -> Dict[str, str]:
        """Load file contents from tax-database"""
        contents = {}
        tax_db_path = self.memory_path / "tax-database"

        for filename in filenames:
            # Search for file in tax database
            for category_dir in tax_db_path.iterdir():
                file_path = category_dir / filename
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            contents[filename] = f.read()
                        break
                    except:
                        contents[filename] = ""
                        break

        return contents

    def _save_session(self, session: TaxPlanningSession):
        """Save session state to disk"""
        session_dir = self.memory_path / f"users/{session.user_id}/sessions"
        session_dir.mkdir(parents=True, exist_ok=True)

        session_file = session_dir / f"{session.session_id}.json"

        session_data = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "tax_domain": session.tax_domain,
            "current_step": session.current_step,
            "original_request": session.original_request,
            "suggested_categories": session.suggested_categories,
            "confirmed_categories": session.confirmed_categories,
            "past_responses_found": session.past_responses_found,
            "selected_past_response": session.selected_past_response,
            "documents_found": session.documents_found,
            "selected_documents": session.selected_documents,
            "approval_status": session.approval_status,
            "timestamp": datetime.now().isoformat()
        }

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)

    def handle_approval(
        self,
        session: TaxPlanningSession,
        approved: bool
    ) -> Dict[str, Any]:
        """
        Handle approval gate result.

        If approved: Save response + learning signals
        If rejected: Return to Step 5 (refine files)
        """
        if approved:
            return self._save_approved_response(session)
        else:
            # Reset to Step 5 for refinement
            session.current_step = 5
            session.approval_status = "rejected"
            self._save_session(session)
            return {
                "success": True,
                "action": "return_to_step_5",
                "message": "Go back to file selection to refine"
            }

    def _save_approved_response(self, session: TaxPlanningSession) -> Dict[str, Any]:
        """
        Save approved response and trigger learning.

        CRITICAL: This is the ONLY save point for approved responses (single source of truth).
        - Never save from agents (they only return AgentResult)
        - Never save from multiple locations (prevents truncation)
        - Saves include constraint metadata to track boundary adherence
        """
        try:
            # Save response to past_responses
            response_filename = f"past_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session.user_id}.md"
            response_path = self.memory_path / "past-responses" / response_filename

            response_path.parent.mkdir(parents=True, exist_ok=True)

            with open(response_path, 'w', encoding='utf-8') as f:
                f.write(f"# Tax Advice\n\n")
                f.write(f"**Original Request**: {session.original_request}\n\n")
                f.write(f"**Categories**: {', '.join(session.confirmed_categories)}\n\n")
                f.write(f"**Date Created**: {datetime.now().isoformat()}\n\n")
                f.write(f"---\n\n")
                f.write(session.response_with_citations)
                f.write(f"\n\n---\n\n")
                f.write(f"**Files Used**: {', '.join(session.selected_documents)}\n\n")
                f.write(f"**Citations**: {len(session.citations)} sources\n\n")

            # Update MemAgent memory
            self.segmented_memory.add_to_segment(
                segment_id=0,  # Past responses segment
                content=session.response_with_citations,
                metadata={
                    "categories": session.confirmed_categories,
                    "files_used": session.selected_documents,
                    "approval_date": datetime.now().isoformat(),
                    "client_type": "Tax",
                    "citations_count": len(session.citations)
                }
            )

            # Record learning signals with constraint metadata
            # This helps Flow-GRPO learn which agent sequences work within category boundaries
            self.learning_manager.apply_learning(
                agent_results=[],  # Agents already executed
                feedback={
                    "approved": True,
                    "categories": session.confirmed_categories,  # CONSTRAINT BOUNDARY that worked
                    "files_used": session.selected_documents,
                    "verification_passed": session.verification_report.get("all_verified", False),
                    "constraint_boundary": {
                        "past_responses_segments": [0, 1, 2, 3],
                        "tax_database_segments": [4, 5, 6, 7, 8, 9, 10, 11],
                        "category_filter": session.confirmed_categories,
                        "document_source_only": True
                    }
                },
                success=True
            )

            session.approval_status = "approved"
            self._save_session(session)

            return {
                "success": True,
                "action": "save_and_learn",
                "response_id": response_filename,
                "message": "Response saved and learning signals recorded"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save approved response: {str(e)}"
            }

    def generate(self, **kwargs) -> AgentResult:
        """
        Implement BaseAgent.generate() method (required by interface).

        In tax workflow, use run() instead.
        """
        raise NotImplementedError("Use run() method instead of generate()")
```

---

## PART 4: INTEGRATION WITH APPROVAL GATES

### 4.1 SessionManager Extension

```python
# In approval_gates.py (add method)

class SessionManager:
    # ... existing methods ...

    def get_or_create_tax_session(
        self,
        session_id: str,
        user_id: str,
        memory_path: Path
    ) -> TaxPlanningSession:
        """Create or restore TaxPlanningSession"""

        # Try to load from disk
        session_file = memory_path / f"users/{user_id}/sessions/{session_id}.json"

        if session_file.exists():
            with open(session_file, 'r') as f:
                data = json.load(f)

            session = TaxPlanningSession(
                session_id=session_id,
                user_id=user_id,
                memory_path=memory_path
            )
            # Restore state from data
            session.current_step = data.get("current_step", 0)
            session.original_request = data.get("original_request", "")
            # ... restore all fields

            return session
        else:
            # New session
            session = TaxPlanningSession(
                session_id=session_id,
                user_id=user_id,
                memory_path=memory_path
            )
            session.current_step = 0
            session.approval_status = "pending"

            return session
```

---

## PART 5: ERROR HANDLING & RECOVERY

### 5.1 Error Types & Recovery

```python
class TaxWorkflowError(Exception):
    """Base class for tax workflow errors"""
    pass

class CategorizationError(TaxWorkflowError):
    """Step 1 error"""
    recovery = "Restart from Step 1"

class SearchError(TaxWorkflowError):
    """Step 2/4 error"""
    recovery = "Retry search or continue without past responses"

class SynthesisError(TaxWorkflowError):
    """Step 5 error"""
    recovery = "Return to file selection and try different files"

class VerificationError(TaxWorkflowError):
    """Step 6 error"""
    recovery = "Return to file selection, may have hallucinations"
```

### 5.2 Graceful Degradation

```python
# In orchestrator step methods:

def _execute_step_2_search(...):
    try:
        result = self.response_searcher.generate(...)
    except SearchError:
        # Graceful fallback: continue without past responses
        return {
            "success": True,
            "past_responses": [],
            "message": "No past responses found, continuing to document search"
        }
```

---

## PART 6: TESTING STRATEGY

### 6.1 Unit Test (Orchestrator alone)

```python
if __name__ == "__main__":
    # Mock all dependencies
    class MockAgent:
        def generate_response(self, prompt):
            return "Mock response"

    class MockMemory:
        def search(self, **kwargs):
            return []

    class MockLearningManager:
        def apply_learning(self, **kwargs):
            pass

    class MockSessionManager:
        def get_or_create_tax_session(self, *args):
            return TaxPlanningSession("test", "user1", Path("./memory"))

    # Test Step 1
    orchestrator = TaxOrchestrator(
        agent=MockAgent(),
        memory_path=Path("./memory"),
        segmented_memory=MockMemory(),
        learning_manager=MockLearningManager(),
        session_manager=MockSessionManager()
    )

    result = orchestrator.run(
        request="Test pharmaceutical distributor question",
        session_id="test_session_1",
        user_id="user1"
    )

    assert result["success"] == True
    assert result["current_step"] == 1
    assert "suggested_categories" in result
    print("✓ Orchestrator tests passed")
```

### 6.2 Integration Test (Full Workflow)

Complete integration test will be in test suite:
- Create real agents
- Step-by-step execution
- Verify state transitions
- Verify learning signals recorded

---

## SUMMARY

**Orchestrator wires 6 agents**:

```
Step 1: RequestCategorizer.generate() → categories
Step 2: TaxResponseSearcher.generate() → past responses
Step 3: [User selects]
Step 4: FileRecommender.generate() → documents
Step 5: [User selects]
Step 6a: TaxResponseCompiler.generate() → response
Step 6b: DocumentVerifier.generate() → verification
Step 6c: CitationTracker.generate() → citations
Step 6d: [Partner approves]
→ Save + Learning signals
```

**State**: Persisted to disk after each step (recoverable)

**Errors**: Gracefully handled with recovery paths

**Learning**: Flow-GRPO signals recorded on approval

**Next**: PHASE_2_STEP3_UI.md shows Streamlit UI for user interactions

---

## ✅ IMPLEMENTATION COMPLETE (NOVEMBER 25, 2025)

### Results Delivered

**TaxOrchestrator Implementation**: ✅ COMPLETE
- **File**: `mem-agent-mcp/orchestrator/tax_workflow/tax_orchestrator.py`
- **Lines of Code**: 710 (actual) vs 200-250 (original estimate)
- **Reason for size**: Comprehensive session management + full constraint tracking

**Key Classes Delivered**:
1. **TaxPlanningSession** (95 lines)
   - Single source of truth for all user boundaries
   - Persistent fields for all 6 steps
   - Serializable for disk persistence

2. **TaxOrchestrator** (615 lines)
   - `run_workflow()`: Main entry point (step-by-step execution)
   - `_execute_step_*()`: Methods for steps 1, 2, 4, 6
   - `save_approved_response()`: Single save point
   - `_load_or_create_session()`: Disk-based session recovery
   - `_save_session()`: Session persistence after each step

**Unit Tests**: 7/7 PASSING ✅
1. ✅ Step 1 categorization
2. ✅ Step 2 past response search (with constraint boundary)
3. ✅ Step 3 user selection wait
4. ✅ Step 4 document search (with constraint boundary)
5. ✅ Step 6 full synthesis/verification/citation (source-only constraint)
6. ✅ Constraint enforcement (rejects missing categories)
7. ✅ Session persistence (save and load state)

### Verification Results

**Constraint Boundary Passing**: ✅ VERIFIED
- Confirmed categories flow from Step 1 → Step 2 & 4
- Selected documents flow from Step 5 → Step 6
- No selections lost mid-workflow
- Every agent receives explicit parameters

**MemAgent Integration**: ✅ VERIFIED
- TaxResponseSearcher uses segments [0-3] only
- FileRecommender uses segments [4-11] only
- Explicit segment lists in every search
- Category constraints enforced at MemAgent query level

**Past Failure Prevention**: ✅ IMPLEMENTED
- Single save point: `_save_approved_response()` only
- Explicit parameter passing: All agents receive boundaries
- Constraint enforcement: Every stage validates
- Session persistence: Disk saves after each step
- Metadata tracking: Complete audit trail

**Architecture Guarantees**: ✅ ENFORCED
- Memory namespace isolation (tax_legal/ separate from PJJ-old/)
- No autonomous MemAgent searches (categories required)
- Source-only constraint in synthesis
- Hallucination detection with >10% threshold
- Citation tracking for all claims

### Current Status

**Phase 2 Progress**: 55% complete (Days 1-6)
- Days 1-4: 6 agents implemented ✅
- Days 5-6: Orchestrator implemented ✅
- Days 7-10: Streamlit UI (NEXT)
- Days 11+: Integration testing

**Ready for Next Phase**: YES
- Backend fully functional
- All constraint boundaries enforced
- Session management complete
- Single save point working
- Ready for UI implementation

### Connection to Overall Goal

This Phase 2 Step 2 implementation delivers:
- **Foundation for learning**: Approved responses saved with constraint metadata
- **Audit trail**: Complete tracking of what constraints were enforced
- **Flow-GRPO readiness**: Metadata enables training signals in Phase 4
- **Translation-ready**: Session state can be extended for Vietnamese support in Phase 5

---

**Document Version**: 2.0
**Updated**: November 25, 2025
**Previous Version**: 1.0 (implementation spec)
**Current Status**: ✅ IMPLEMENTATION COMPLETE & VERIFIED
