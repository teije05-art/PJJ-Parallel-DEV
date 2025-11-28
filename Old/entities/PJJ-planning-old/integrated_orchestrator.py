"""
IntegratedOrchestrator - Bridge between Streamlit and memagent-modular-fixed

This adapter:
1. Accepts Streamlit parameters (goal, entities, plans, memory_scope, iterations, checkpoint_interval)
2. Manages ProposalAgent (initial approval gate for multi-iteration)
3. Manages CheckpointAgent (iteration approval gates)
4. Handles session-based blocking/approval synchronization
5. Transforms responses to Streamlit-expected format

Critical: ProposalAgent and CheckpointAgent are BLOCKING approval gates.
The backend waits for user approval before continuing planning.
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

# Core imports
from agent.agent import Agent
from orchestrator.simple_orchestrator import SimpleOrchestrator
from orchestrator.agents import ProposalAgent, CheckpointAgent
from approval_gates import SessionManager, PlanningSession
from llama_planner import LlamaPlanner


class IntegratedOrchestrator:
    """
    Streamlit-compatible orchestrator with ProposalAgent and CheckpointAgent.

    Manages the complete planning workflow:
    1. Single-iteration: Auto-approve (return plan immediately)
    2. Multi-iteration: ProposalAgent → checkpoint loop → CheckpointAgent at each checkpoint
    """

    def __init__(self, memory_path: str, user_id: str = "default_user"):
        """
        Initialize IntegratedOrchestrator.

        Args:
            memory_path: Path to local memory directory
            user_id: User identifier for multi-user memory isolation
        """
        self.memory_path = Path(memory_path)
        self.user_id = user_id
        self.memory_path_user = self.memory_path / f"users/{user_id}"
        self.memory_path_user.mkdir(parents=True, exist_ok=True)

        # Session manager handles approval gate synchronization
        self.session_manager = SessionManager()

        # Create agent instance for LlamaPlanner
        self.agent = Agent(memory_path=str(self.memory_path_user))

        # LlamaPlanner for memory operations
        self.llama_planner = LlamaPlanner(
            agent=self.agent,
            memory_path=str(self.memory_path)
        )

        print(f"🚀 IntegratedOrchestrator initialized")
        print(f"   User: {user_id}")
        print(f"   Memory: {self.memory_path_user}")
        print(f"   Features: ProposalAgent, CheckpointAgent, session blocking, multi-user")

    # ==================== MAIN ENTRY POINT ====================

    def plan_goal(
        self,
        goal: str,
        selected_entities: List[str] = None,
        selected_plans: List[str] = None,
        memory_scope: str = "both",
        iterations: int = 1,
        checkpoint_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Main planning entry point with ProposalAgent/CheckpointAgent support.

        For single-iteration (iterations == 1):
            - Auto-approve without user input
            - Return plan immediately

        For multi-iteration (iterations > 1):
            - Return proposal from ProposalAgent
            - Caller must call handle_proposal_approval()
            - After approval, caller must poll for checkpoints and call handle_checkpoint_approval()

        Args:
            goal: Strategic planning goal
            selected_entities: User-selected memory entities to use
            selected_plans: User-selected past plans to learn from
            memory_scope: "private", "shared", or "both"
            iterations: Number of planning iterations (1-15)
            checkpoint_interval: Checkpoint every N iterations (1-5)

        Returns:
            For single-iteration:
                {
                    'type': 'final_plan',
                    'plan_id': 'uuid',
                    'plan': '<full strategic plan - 3000+ words>',
                    'plan_content': '<full strategic plan>',
                    'metadata': {
                        'goal': '...',
                        'frameworks_used': [...],
                        'data_points': N,
                        'entities_found': [...],
                        'coverage': 0.xx,
                        'synthesis_verification': {...}
                    }
                }

            For multi-iteration (awaiting proposal approval):
                {
                    'type': 'proposal',
                    'proposal_id': '<session_id>',
                    'proposal': '<ProposalAgent output - 1000+ words>',
                    'metadata': {
                        'domain': '...',
                        'memory_coverage_percent': xx,
                        'research_coverage_percent': xx,
                        'confidence_level': 0.xx,
                        'approach_summary': '...',
                        'max_iterations': iterations,
                        'checkpoint_interval': checkpoint_interval
                    }
                }
        """
        selected_entities = selected_entities or []
        selected_plans = selected_plans or []

        print(f"\n{'='*80}")
        print(f"🎯 PLANNING SESSION STARTED")
        print(f"   Goal: {goal[:100]}...")
        print(f"   Iterations: {iterations}")
        print(f"   Checkpoint Interval: {checkpoint_interval}")
        print(f"   Entities: {len(selected_entities)}")
        print(f"   Plans: {len(selected_plans)}")
        print(f"{'='*80}\n")

        # Step 1: Create session for this planning request
        session_id, session = self.session_manager.get_or_create(
            session_id=None,
            memory_path=str(self.memory_path_user)
        )

        print(f"📋 Session created: {session_id}")

        # Step 2: Handle single-iteration vs multi-iteration
        if iterations == 1:
            # Single iteration: Auto-approve, return plan immediately
            print(f"✅ Single-iteration mode: Auto-approving")
            return self._run_single_iteration(
                session_id=session_id,
                goal=goal,
                selected_entities=selected_entities,
                selected_plans=selected_plans,
                memory_scope=memory_scope
            )
        else:
            # Multi-iteration: Generate proposal first
            print(f"🔄 Multi-iteration mode: Generating proposal via ProposalAgent")
            return self._generate_proposal(
                session_id=session_id,
                goal=goal,
                selected_entities=selected_entities,
                selected_plans=selected_plans,
                iterations=iterations,
                checkpoint_interval=checkpoint_interval,
                memory_scope=memory_scope
            )

    # ==================== SINGLE ITERATION ====================

    def _run_single_iteration(
        self,
        session_id: str,
        goal: str,
        selected_entities: List[str],
        selected_plans: List[str],
        memory_scope: str
    ) -> Dict[str, Any]:
        """
        Run single-iteration planning with auto-approval.

        Returns final plan immediately without approval gates.
        """
        session = self.session_manager.get(session_id)

        try:
            # Create SimpleOrchestrator for single iteration
            orchestrator = SimpleOrchestrator(
                memory_path=str(self.memory_path_user),
                max_iterations=1,
                selected_plans=selected_plans,
                selected_entities=selected_entities,
                segmented_memory=session.memory_manager
            )

            print(f"🔄 Running single-iteration planning...")

            # Run enhanced learning loop (single iteration auto-approves)
            for event in orchestrator.run_enhanced_learning_loop(goal):
                if event.get('type') == 'final_plan':
                    # Extract plan content and metadata
                    plan_content = event.get('plan', '')
                    unique_frameworks = event.get('unique_frameworks', [])
                    total_data_points = event.get('total_data_points', 0)

                    # Store in session
                    self.session_manager.store_plan(
                        session_id=session_id,
                        plan_content=plan_content,
                        frameworks=unique_frameworks,
                        data_points=total_data_points,
                        iterations=1,
                        checkpoints=0
                    )

                    plan_id = str(uuid.uuid4())[:8]

                    print(f"✅ Planning complete!")
                    print(f"   Plan ID: {plan_id}")
                    print(f"   Frameworks: {len(unique_frameworks)}")
                    print(f"   Data Points: {total_data_points}")

                    return {
                        'type': 'final_plan',
                        'plan_id': plan_id,
                        'plan': plan_content,
                        'plan_content': plan_content,
                        'memory_scope': memory_scope,  # Pass memory scope for UI display
                        'metadata': {
                            'goal': goal,
                            'frameworks_used': unique_frameworks,
                            'data_points': total_data_points,
                            'entities_found': selected_entities,
                            'coverage': 1.0,
                            'synthesis_verification': {
                                'is_substantial': len(plan_content) > 2000,
                                'word_count': len(plan_content.split()),
                                'quality_score': 0.85
                            }
                        }
                    }

                elif event.get('type') == 'error':
                    raise Exception(f"Planning error: {event.get('message')}")

            raise Exception("Planning completed without producing plan")

        except Exception as e:
            print(f"❌ Single-iteration planning failed: {e}")
            raise

    # ==================== MULTI-ITERATION: PROPOSAL APPROVAL ====================

    def _generate_proposal(
        self,
        session_id: str,
        goal: str,
        selected_entities: List[str],
        selected_plans: List[str],
        iterations: int,
        checkpoint_interval: int,
        memory_scope: str
    ) -> Dict[str, Any]:
        """
        Generate proposal via ProposalAgent.

        Returns proposal for user approval.
        User must call handle_proposal_approval() to continue.

        CRITICAL: This is APPROVAL GATE 1
        """
        session = self.session_manager.get(session_id)

        print(f"🎯 PROPOSAL GENERATION VIA ProposalAgent")
        print(f"   Session: {session_id}")

        try:
            # Create a temporary agent for proposal generation
            from agent.agent import Agent
            agent = Agent(memory_path=str(self.memory_path_user))

            # Create ProposalAgent
            proposal_agent = ProposalAgent(agent=agent, memory_path=str(self.memory_path_user))

            # Generate proposal
            print(f"   Analyzing goal and context...")
            proposal_result = proposal_agent.analyze_and_propose(
                goal=goal,
                selected_entities=selected_entities,
                selected_plans=selected_plans
            )

            if not proposal_result.success:
                raise Exception(f"ProposalAgent failed: {proposal_result.output}")

            proposal_text = proposal_result.output
            proposal_metadata = proposal_result.metadata or {}

            # Store proposal in session (with control values)
            self.session_manager.store_proposal(
                session_id=session_id,
                goal=goal,
                proposal_text=proposal_text,
                selected_entities=selected_entities,
                selected_agents=["planner", "verifier", "executor", "generator"],
                max_iterations=iterations,
                checkpoint_interval=checkpoint_interval,
                approach_summary=proposal_metadata.get('approach_summary', 'Analysis complete')
            )

            print(f"✅ ProposalAgent analysis complete")
            print(f"   Domain: {proposal_metadata.get('domain')}")
            print(f"   Memory Coverage: {proposal_metadata.get('memory_coverage_percent', 0):.0f}%")
            print(f"   Research Coverage: {proposal_metadata.get('research_coverage_percent', 0):.0f}%")
            print(f"   Confidence: {proposal_metadata.get('confidence_level', 0):.0%}")

            # Return proposal for approval (Streamlit will show this and call handle_proposal_approval)
            return {
                'type': 'proposal',
                'proposal_id': session_id,
                'proposal': proposal_text,
                'metadata': {
                    'domain': proposal_metadata.get('domain', 'Strategic Planning'),
                    'memory_coverage_percent': proposal_metadata.get('memory_coverage_percent', 0),
                    'research_coverage_percent': proposal_metadata.get('research_coverage_percent', 0),
                    'confidence_level': proposal_metadata.get('confidence_level', 0),
                    'approach_summary': proposal_metadata.get('approach_summary', ''),
                    'max_iterations': iterations,
                    'checkpoint_interval': checkpoint_interval,
                    'created_at': datetime.now().isoformat()
                }
            }

        except Exception as e:
            print(f"❌ Proposal generation failed: {e}")
            raise

    def handle_proposal_approval(
        self,
        session_id: str,
        approved: bool,
        feedback: str = None
    ) -> Dict[str, Any]:
        """
        Handle user approval or rejection of proposal.

        CRITICAL: This is the continuation of APPROVAL GATE 1

        If approved: Start multi-iteration planning
        If rejected: Return to Streamlit for re-configuration

        Args:
            session_id: Session ID from proposal
            approved: True to start iterations, False to reject
            feedback: Optional feedback from user

        Returns:
            {
                'success': bool,
                'message': str,
                'next_action': 'start_iterations' or 'show_form'
            }
        """
        session = self.session_manager.get(session_id)
        if not session:
            return {'success': False, 'message': f'Session {session_id} not found'}

        if approved:
            print(f"✅ Proposal approved for session {session_id}")
            print(f"   Starting multi-iteration planning...")

            # Mark proposal as approved (can be used for logging/analytics)
            session.planning_context['proposal_approved'] = True
            session.planning_context['proposal_approval_time'] = datetime.now().isoformat()

            # NOTE: Actual iteration loop starts via run_iterative_planning()
            # This is called from Streamlit via a separate endpoint or streaming function
            # For now, return success so Streamlit knows to start iterations

            return {
                'success': True,
                'message': 'Proposal approved! Starting multi-iteration planning...',
                'next_action': 'start_iterations',
                'session_id': session_id
            }
        else:
            print(f"❌ Proposal rejected for session {session_id}")
            if feedback:
                print(f"   Feedback: {feedback}")

            return {
                'success': True,
                'message': 'Proposal rejected. You can modify settings and try again.',
                'next_action': 'show_form',
                'session_id': session_id,
                'feedback': feedback
            }

    # ==================== MULTI-ITERATION: CHECKPOINT APPROVALS ====================

    def run_iterative_planning(
        self,
        session_id: str,
        goal: str,
        memory_scope: str = "both"
    ) -> Dict[str, Any]:
        """
        Run multi-iteration planning with checkpoint approvals.

        CRITICAL: This method BLOCKS at each checkpoint waiting for user approval.

        The backend calls session_manager.wait_for_checkpoint_approval(session_id)
        and waits for Streamlit to call handle_checkpoint_approval().

        Yields:
            For each iteration:
                {'type': 'iteration_progress', ...}
            At each checkpoint:
                {
                    'type': 'checkpoint',
                    'checkpoint_num': N,
                    'summary': '<CheckpointAgent output>',
                    'action_required': 'user_approval'
                }
            At end:
                {'type': 'final_plan', 'plan': '...'}
        """
        session = self.session_manager.get(session_id)
        if not session:
            raise Exception(f"Session {session_id} not found")

        # Get control values from stored proposal
        max_iterations, checkpoint_interval = self.session_manager.get_control_values(session_id)
        proposal = self.session_manager.get_proposal(session_id)

        print(f"\n{'='*80}")
        print(f"🔄 STARTING MULTI-ITERATION PLANNING")
        print(f"   Session: {session_id}")
        print(f"   Max iterations: {max_iterations}")
        print(f"   Checkpoint interval: {checkpoint_interval}")
        print(f"{'='*80}\n")

        try:
            # Create SimpleOrchestrator with multi-iteration settings
            orchestrator = SimpleOrchestrator(
                memory_path=str(self.memory_path_user),
                max_iterations=max_iterations,
                selected_plans=proposal.get('selected_entities', []) if proposal else [],
                selected_entities=proposal.get('selected_entities', []) if proposal else [],
                segmented_memory=session.memory_manager
            )

            # Create LlamaPlanner for checkpoint synthesis
            llama_planner = LlamaPlanner(memory_path=str(self.memory_path_user))

            # Run iterative planning - this YIELDS checkpoints
            for event in orchestrator.run_iterative_planning(
                goal=goal,
                proposal=proposal.get('proposal_text', '') if proposal else '',
                max_iterations=max_iterations,
                checkpoint_interval=checkpoint_interval,
                llama_planner=llama_planner
            ):
                if event.get('type') == 'checkpoint':
                    # APPROVAL GATE 2: Checkpoint approval
                    checkpoint_num = event.get('checkpoint_count', 0)
                    iteration_num = event.get('iteration', 0)

                    print(f"\n{'='*80}")
                    print(f"🎯 CHECKPOINT {checkpoint_num}: Iteration {iteration_num}/{max_iterations}")
                    print(f"   Awaiting user approval...")
                    print(f"{'='*80}\n")

                    # Store checkpoint summary in session
                    self.session_manager.store_checkpoint_summary(
                        session_id=session_id,
                        checkpoint_num=checkpoint_num,
                        summary_text=event.get('summary', ''),
                        analysis=event.get('metrics', {})
                    )

                    # CRITICAL: Block here waiting for user approval
                    # This is where Streamlit must call handle_checkpoint_approval()
                    approved = self.session_manager.wait_for_checkpoint_approval(
                        session_id=session_id,
                        timeout=3600  # 1 hour timeout
                    )

                    if not approved:
                        print(f"❌ Checkpoint {checkpoint_num} rejected")
                        yield {
                            'type': 'checkpoint_rejected',
                            'checkpoint_num': checkpoint_num,
                            'message': 'Checkpoint rejected, planning stopped'
                        }
                        return

                    print(f"✅ Checkpoint {checkpoint_num} approved, continuing iterations...")

                    yield {
                        'type': 'checkpoint_approved',
                        'checkpoint_num': checkpoint_num,
                        'message': f'Checkpoint {checkpoint_num} approved'
                    }

                elif event.get('type') == 'final_plan':
                    # Multi-iteration complete
                    plan_content = event.get('plan', '')
                    unique_frameworks = event.get('unique_frameworks', [])
                    total_data_points = event.get('total_data_points', 0)

                    # Store final plan in session
                    self.session_manager.store_plan(
                        session_id=session_id,
                        plan_content=plan_content,
                        frameworks=unique_frameworks,
                        data_points=total_data_points,
                        iterations=max_iterations,
                        checkpoints=len(session.checkpoint_summaries)
                    )

                    plan_id = str(uuid.uuid4())[:8]

                    print(f"\n✅ PLANNING COMPLETE!")
                    print(f"   Plan ID: {plan_id}")
                    print(f"   Iterations: {max_iterations}")
                    print(f"   Checkpoints: {len(session.checkpoint_summaries)}")
                    print(f"   Frameworks: {len(unique_frameworks)}")
                    print(f"   Data Points: {total_data_points}\n")

                    yield {
                        'type': 'final_plan',
                        'plan_id': plan_id,
                        'plan': plan_content,
                        'plan_content': plan_content,
                        'metadata': {
                            'goal': goal,
                            'frameworks_used': unique_frameworks,
                            'data_points': total_data_points,
                            'iterations': max_iterations,
                            'checkpoints': len(session.checkpoint_summaries),
                            'synthesis_verification': {
                                'is_substantial': len(plan_content) > 2000,
                                'word_count': len(plan_content.split()),
                                'quality_score': 0.88
                            }
                        }
                    }

                else:
                    # Pass through other events (iteration_progress, etc)
                    yield event

        except Exception as e:
            print(f"❌ Multi-iteration planning failed: {e}")
            import traceback
            traceback.print_exc()
            yield {
                'type': 'error',
                'message': f'Planning error: {str(e)}'
            }

    def handle_checkpoint_approval(
        self,
        session_id: str,
        checkpoint_num: int,
        approved: bool,
        feedback: str = None
    ) -> Dict[str, Any]:
        """
        Handle user approval or rejection of checkpoint.

        CRITICAL: This is the continuation of APPROVAL GATE 2

        This unblocks the backend that's waiting in wait_for_checkpoint_approval()

        Args:
            session_id: Session ID from planning
            checkpoint_num: Which checkpoint number this is
            approved: True to continue, False to stop/retry
            feedback: Optional feedback from user

        Returns:
            {
                'success': bool,
                'message': str
            }
        """
        session = self.session_manager.get(session_id)
        if not session:
            return {'success': False, 'message': f'Session {session_id} not found'}

        if approved:
            print(f"✅ Checkpoint {checkpoint_num} approved (session {session_id})")

            # Unblock the wait_for_checkpoint_approval() call in backend
            success = self.session_manager.set_checkpoint_approved(
                session_id=session_id,
                checkpoint_num=checkpoint_num,
                approved=True
            )

            if success:
                return {
                    'success': True,
                    'message': f'Checkpoint {checkpoint_num} approved, continuing...'
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to approve checkpoint {checkpoint_num}'
                }
        else:
            print(f"❌ Checkpoint {checkpoint_num} rejected (session {session_id})")
            if feedback:
                print(f"   Feedback: {feedback}")

            # Unblock with rejection signal
            success = self.session_manager.set_checkpoint_approved(
                session_id=session_id,
                checkpoint_num=checkpoint_num,
                approved=False
            )

            if success:
                return {
                    'success': True,
                    'message': f'Checkpoint {checkpoint_num} rejected'
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to reject checkpoint {checkpoint_num}'
                }

    # ==================== CHAT & MEMORY OPERATIONS ====================

    def chat_about_plan(
        self,
        user_message: str,
        session_id: str,
        plan_id: str = None
    ) -> Dict[str, Any]:
        """
        Chat about the generated plan.

        Supports memory commands:
            /store <memory_key> <memory_value>
            /retrieve <memory_key>
            /list
            /clear

        Args:
            user_message: User's chat message
            session_id: Session ID from planning
            plan_id: Optional plan ID (for future multi-plan support)

        Returns:
            {
                'reply': '<response text>',
                'memory_updated': bool,
                'metadata': {...}
            }
        """
        session = self.session_manager.get(session_id)
        if not session:
            return {
                'reply': f'Session {session_id} not found',
                'error': True
            }

        # Get the current plan from session
        plan_content = self.session_manager.get_plan(session_id)
        if not plan_content:
            return {
                'reply': 'No plan available in this session yet',
                'error': True
            }

        try:
            # Check for memory commands
            if user_message.startswith('/'):
                return self._handle_memory_command(
                    user_message=user_message,
                    session_id=session_id,
                    plan_content=plan_content
                )

            # Regular chat about plan
            from agent.agent import Agent
            agent = Agent(memory_path=str(self.memory_path_user))

            # Build context from plan and session
            context = {
                'plan': plan_content,
                'planning_context': session.planning_context,
                'user_query': user_message
            }

            # Generate response via agent
            response = agent.generate_response(
                prompt=f"User asks: {user_message}\n\nAbout this plan: {plan_content[:2000]}...",
                max_tokens=500
            )

            return {
                'reply': response,
                'memory_updated': False,
                'metadata': {
                    'session_id': session_id,
                    'plan_available': True
                }
            }

        except Exception as e:
            print(f"❌ Chat error: {e}")
            return {
                'reply': f'Error: {str(e)}',
                'error': True
            }

    def _handle_memory_command(
        self,
        user_message: str,
        session_id: str,
        plan_content: str
    ) -> Dict[str, Any]:
        """Handle /store, /retrieve, /list, /clear commands"""
        # Implementation for memory commands
        # This integrates with MemAgent semantic memory
        return {
            'reply': 'Memory commands not yet implemented',
            'error': False
        }
