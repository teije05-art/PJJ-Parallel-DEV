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
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
import json

from agent.agent import Agent


class PlanningSession:
    """A single user planning session with full context."""

    def __init__(self, session_id: str, memory_path: str):
        """Initialize a planning session."""
        self.id = session_id
        self.created_at = datetime.now().isoformat()
        self.memory_path = memory_path

        # Core agent
        self.agent = Agent(memory_path=memory_path)

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
        self.pending_approvals = {}
        self.checkpoint_approved = False
        self.checkpoint_approval_event = threading.Event()

        # Track what agents have done at each iteration
        self.iteration_progress = {}  # iteration -> {agents_run, findings, status}

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
        """Get existing session or create new one."""
        # Return existing session if valid
        if session_id and session_id in self.sessions:
            return session_id, self.sessions[session_id]

        # Create new session
        new_id = str(uuid.uuid4())[:12]
        session = PlanningSession(new_id, memory_path)
        self.sessions[new_id] = session

        return new_id, session

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

    def set_checkpoint_approved(self, session_id: str, checkpoint_num: int) -> bool:
        """Mark checkpoint as approved by user."""
        session = self.get(session_id)
        if session:
            session.checkpoint_approved = True
            session.checkpoint_approval_event.set()
            return True
        return False

    def wait_for_checkpoint_approval(
        self,
        session_id: str,
        timeout: int = 3600
    ) -> bool:
        """
        Wait for user to approve checkpoint (blocks until approved).

        Times out after 1 hour by default.
        """
        session = self.get(session_id)
        if not session:
            return False

        # Reset event for next checkpoint
        session.checkpoint_approval_event.clear()
        session.checkpoint_approved = False

        # Wait for approval (blocks here)
        session.checkpoint_approval_event.wait(timeout=timeout)

        return session.checkpoint_approved

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
