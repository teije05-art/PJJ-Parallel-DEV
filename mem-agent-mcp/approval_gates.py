"""
Approval Gates and Session Management for Planning System

Manages:
1. Planning sessions (user state across requests)
2. Plan storage (generated plans stored in session for chat to access)
3. Control values (iterations, checkpoints synced from proposal → execution)
4. Checkpoint approvals (user decisions at checkpoints)
5. Full checkpoint summaries (1000+ word Llama analyses, not fragments)
6. Planning context (entities, agents, goal info)
"""

import threading
import queue  # FIXED (Oct 31, 2025): Import queue for race-condition-free approval handling
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
import json

from agent.agent import Agent
from orchestrator.memory.memagent_memory import SegmentedMemory  # Phase 1: MemAgent integration


class PlanningSession:
    """A single user planning session with full context."""

    def __init__(self, session_id: str, memory_path: str):
        """Initialize a planning session."""
        self.id = session_id
        self.created_at = datetime.now().isoformat()
        self.memory_path = memory_path

        # Core agent - Uses Fireworks API (consolidated backend)
        print(f"   🔧 Creating Agent with backend: Fireworks (API)")

        self.agent = Agent(memory_path=memory_path)

        # Phase 1: MemAgent-based Segmented Memory (fixed-length, bounded growth)
        self.memory_manager = SegmentedMemory(
            max_segments=12,
            max_tokens_per_segment=2000,
            memagent_client=self.agent  # Use MemAgent client for semantic search
        )

        # Orchestrator for multi-iteration planning
        self.orchestrator = None

        # FIX #1: Store the generated plan so chat can access it later
        self.generated_plan = None
        self.plan_metadata = {
            "goal": None,
            "frameworks_used": [],
            "data_points_count": 0,
            "iterations": 0,
            "checkpoints_reached": 0,
            "created_at": None
        }

        # FIX #2: Store proposal details + control values to ensure sync
        self.proposal_data = {
            "goal": None,
            "proposal_text": None,
            "selected_entities": [],
            "selected_agents": [],
            "max_iterations": 1,
            "checkpoint_interval": 2,
            "approach_summary": None  # What Llama said about approach
        }

        # FIX #3: Store full checkpoint summaries (1000+ words, not 50)
        self.checkpoint_summaries = {}  # checkpoint_num -> full summary text
        self.checkpoint_analyses = {}  # checkpoint_num -> improvements analysis

        # Planning context (used for queries, entity info, etc)
        self.planning_context = {
            "memory_context": {},
            "entity_context": {},
            "research_context": {},
            "formatted_for_agents": {}
        }

        # Checkpoint approval system
        # FIXED (Oct 31, 2025): Use queue instead of Event to prevent race conditions
        # Queue guarantees that if approval is sent before wait() is called, it won't be lost
        self.pending_approvals = {}
        self.checkpoint_approved = False
        self.checkpoint_approval_queue = queue.Queue(maxsize=1)  # Only one approval at a time
        # Keep Event for backward compatibility (can remove after full migration)
        self.checkpoint_approval_event = threading.Event()

        # Track what agents have done at each iteration
        self.iteration_progress = {}  # iteration -> {agents_run, findings, status}

        # FIX #4: Track selected plans for learning from past planning
        self.selected_plans_for_learning = []  # list of plan filenames selected by user

    def __getitem__(self, key: str) -> Any:
        """Support dictionary-style access for backward compatibility with old code."""
        if key == "id":
            return self.id
        elif key == "agent":
            return self.agent
        elif key == "orchestrator":
            return self.orchestrator
        elif key == "pending_approvals":
            return self.pending_approvals
        elif key == "checkpoint_approved":
            return self.checkpoint_approved
        elif key == "checkpoint_approval_event":
            return self.checkpoint_approval_event
        elif key == "selected_plans_for_learning":
            return self.selected_plans_for_learning
        elif key == "execution_state":
            return {}  # Backward compat with old dict-based sessions
        raise KeyError(f"Session has no key '{key}'")

    def __setitem__(self, key: str, value: Any) -> None:
        """Support dictionary-style assignment for backward compatibility."""
        if key == "agent":
            self.agent = value
        elif key == "orchestrator":
            self.orchestrator = value
        elif key == "pending_approvals":
            self.pending_approvals = value
        elif key == "checkpoint_approved":
            self.checkpoint_approved = value
        elif key == "checkpoint_approval_event":
            self.checkpoint_approval_event = value
        elif key == "selected_plans_for_learning":
            self.selected_plans_for_learning = value
        else:
            raise KeyError(f"Cannot set session key '{key}'")


class SessionManager:
    """Manage all planning sessions."""

    def __init__(self):
        """Initialize session manager."""
        self.sessions: Dict[str, PlanningSession] = {}

    def get_or_create(
        self,
        session_id: Optional[str] = None,
        memory_path: str = ""
    ) -> Tuple[str, PlanningSession]:
        """Get existing session or create new one.

        CRITICAL: If session_id is provided, ALWAYS use it (don't generate random ID)
        """
        # Return existing session if it exists
        if session_id and session_id in self.sessions:
            return session_id, self.sessions[session_id]

        # FIX (Nov 2, 2025): Use provided session_id or generate new one
        session_id_to_use = session_id if session_id else str(uuid.uuid4())[:12]
        session = PlanningSession(session_id_to_use, memory_path)
        self.sessions[session_id_to_use] = session

        return session_id_to_use, session

    def get(self, session_id: str) -> Optional[PlanningSession]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def store_proposal(
        self,
        session_id: str,
        goal: str,
        proposal_text: str,
        selected_entities: List[str],
        selected_agents: List[str],
        max_iterations: int,
        checkpoint_interval: int,
        approach_summary: str
    ) -> bool:
        """
        Store proposal details in session.

        FIXES ISSUE #2: Ensures control values are stored before execution,
        so they can't get out of sync.
        """
        session = self.get(session_id)
        if not session:
            return False

        session.proposal_data = {
            "goal": goal,
            "proposal_text": proposal_text,
            "selected_entities": selected_entities,
            "selected_agents": selected_agents,
            "max_iterations": max_iterations,
            "checkpoint_interval": checkpoint_interval,
            "approach_summary": approach_summary
        }

        # Also store in planning context for later reference
        session.planning_context["proposal"] = session.proposal_data

        return True

    def get_proposal(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get stored proposal for this session."""
        session = self.get(session_id)
        if session:
            return session.proposal_data
        return None

    def get_control_values(self, session_id: str) -> Tuple[int, int]:
        """
        Get max_iterations and checkpoint_interval from stored proposal.

        ENSURES CONSISTENCY: Values come from what was approved, not re-requested.
        """
        session = self.get(session_id)
        if session and session.proposal_data:
            return (
                session.proposal_data.get("max_iterations", 1),
                session.proposal_data.get("checkpoint_interval", 2)
            )
        return (1, 2)  # Defaults

    def store_plan(
        self,
        session_id: str,
        plan_content: str,
        frameworks: List[str],
        data_points: int,
        iterations: int,
        checkpoints: int
    ) -> bool:
        """
        Store completed plan in session.

        FIXES ISSUE #1: Plan is stored so chat can access it later.
        """
        session = self.get(session_id)
        if not session:
            return False

        session.generated_plan = plan_content
        session.plan_metadata = {
            "goal": session.proposal_data.get("goal"),
            "frameworks_used": frameworks,
            "data_points_count": data_points,
            "iterations": iterations,
            "checkpoints_reached": checkpoints,
            "created_at": datetime.now().isoformat()
        }

        # Make it accessible to chat
        session.planning_context["completed_plan"] = plan_content
        session.planning_context["plan_metadata"] = session.plan_metadata

        return True

    def get_plan(self, session_id: str) -> Optional[str]:
        """
        Get the stored plan.

        Called by chat endpoint so users can ask about the plan.
        """
        session = self.get(session_id)
        if session:
            return session.generated_plan
        return None

    def get_plan_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get full planning context (plan + metadata).

        Used by chat to answer questions about the planning approach.
        """
        session = self.get(session_id)
        if session:
            return {
                "plan": session.generated_plan,
                "metadata": session.plan_metadata,
                "proposal": session.proposal_data,
                "context": session.planning_context
            }
        return {}

    def store_checkpoint_summary(
        self,
        session_id: str,
        checkpoint_num: int,
        summary_text: str,
        analysis: Dict[str, Any]
    ) -> bool:
        """
        Store full checkpoint summary (1000+ words).

        FIXES ISSUE #3: Stores the real analysis, not a 50-word fragment.
        """
        session = self.get(session_id)
        if not session:
            return False

        session.checkpoint_summaries[checkpoint_num] = summary_text
        session.checkpoint_analyses[checkpoint_num] = analysis

        return True

    def get_checkpoint_summary(self, session_id: str, checkpoint_num: int) -> Optional[str]:
        """Get stored checkpoint summary."""
        session = self.get(session_id)
        if session:
            return session.checkpoint_summaries.get(checkpoint_num)
        return None

    def store_iteration_progress(
        self,
        session_id: str,
        iteration: int,
        agent_name: str,
        status: str,
        findings: str
    ) -> bool:
        """
        Store what's happening during planning.

        FIXES ISSUE #4: Tracks real-time progress for display.
        """
        session = self.get(session_id)
        if not session:
            return False

        if iteration not in session.iteration_progress:
            session.iteration_progress[iteration] = {
                "agents_run": [],
                "findings": {},
                "timeline": []
            }

        progress = session.iteration_progress[iteration]
        if agent_name not in progress["agents_run"]:
            progress["agents_run"].append(agent_name)

        progress["findings"][agent_name] = findings
        progress["timeline"].append({
            "agent": agent_name,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })

        return True

    def get_iteration_progress(self, session_id: str, iteration: int) -> Optional[Dict[str, Any]]:
        """Get progress for a specific iteration."""
        session = self.get(session_id)
        if session:
            return session.iteration_progress.get(iteration)
        return None

    def set_checkpoint_approved(self, session_id: str, checkpoint_num: int, approved: bool = True) -> bool:
        """Mark checkpoint as approved/rejected by user.

        FIXED (Oct 31, 2025): Uses queue instead of Event to prevent race conditions.
        This ensures that if approval is sent before wait() is called, it won't be lost.
        """
        session = self.get(session_id)
        if not session:
            print(f"❌ DEBUG: set_checkpoint_approved - Session {session_id} NOT FOUND")
            return False

        try:
            print(f"📤 DEBUG: set_checkpoint_approved - Putting {approved} in queue for session {session_id}, checkpoint {checkpoint_num}")
            # Put approval decision in queue (non-blocking)
            session.checkpoint_approval_queue.put(approved, block=False)
            print(f"✅ DEBUG: set_checkpoint_approved - Message successfully queued for session {session_id}")
            # Also update the old flag for backward compatibility
            session.checkpoint_approved = approved
            # And set the event for backward compatibility
            session.checkpoint_approval_event.set()
            return True
        except queue.Full:
            print(f"⚠️ Approval message queue FULL for session {session_id}, checkpoint {checkpoint_num}")
            return False
        except Exception as e:
            print(f"❌ DEBUG: set_checkpoint_approved - Exception: {type(e).__name__}: {e}")
            return False

    def wait_for_checkpoint_approval(
        self,
        session_id: str,
        timeout: int = 3600
    ) -> bool:
        """
        Wait for user to approve checkpoint (blocks until approved).

        FIXED (Oct 31, 2025): Uses queue instead of Event to prevent race conditions.
        - If approval is sent BEFORE this is called, it's safely stored in queue
        - If approval is sent AFTER this starts waiting, it's received correctly
        - No race condition where approval gets lost

        Times out after 1 hour by default.
        """
        session = self.get(session_id)
        if not session:
            print(f"❌ DEBUG: wait_for_checkpoint_approval - Session {session_id} NOT FOUND")
            return False

        try:
            print(f"⏳ DEBUG: wait_for_checkpoint_approval - Starting to wait for approval (session {session_id}, timeout {timeout}s)...")
            # Wait for approval message in queue (blocks here, not susceptible to race conditions)
            approval_received = session.checkpoint_approval_queue.get(timeout=timeout)
            print(f"📥 DEBUG: wait_for_checkpoint_approval - Received approval response: {approval_received} (session {session_id})")
            return approval_received  # True = approved, False = rejected

        except queue.Empty:
            # Timeout occurred - user never approved
            print(f"⚠️ Checkpoint approval TIMEOUT ({timeout}s) for session {session_id}")
            return False
        except Exception as e:
            print(f"❌ DEBUG: wait_for_checkpoint_approval - Exception: {type(e).__name__}: {e}")
            return False

    def reset_checkpoint_state(self, session_id: str) -> bool:
        """Reset checkpoint state for next checkpoint."""
        session = self.get(session_id)
        if session:
            session.checkpoint_approved = False
            session.checkpoint_approval_event.clear()
            return True
        return False

    def clear_pending_approval(self, session_id: str, approval_id: str) -> bool:
        """Clear a pending approval after processing."""
        session = self.get(session_id)
        if session:
            session.pending_approvals.pop(approval_id, None)
            return True
        return False

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of session state for debugging."""
        session = self.get(session_id)
        if not session:
            return None

        return {
            "id": session.id,
            "created_at": session.created_at,
            "has_plan": session.generated_plan is not None,
            "plan_metadata": session.plan_metadata,
            "proposal": session.proposal_data,
            "checkpoints_reached": len(session.checkpoint_summaries),
            "iteration_count": len(session.iteration_progress)
        }
