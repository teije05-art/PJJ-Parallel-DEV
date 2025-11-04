"""
Planning Coordinator - Main Iteration Loop with Real-Time Progress

Manages:
1. Multi-iteration planning execution
2. Real-time progress events (FIX #4 - shows what agents are doing)
3. Detailed checkpoint summaries via context_manager
4. Session storage of all progress
5. Plan generation and synthesis
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator

from approval_gates import SessionManager, PlanningSession
from context_manager import generate_detailed_checkpoint_summary, analyze_iteration_improvements
from llama_planner import LlamaPlanner
from orchestrator.simple_orchestrator import SimpleOrchestrator
# Phase 1: MemAgent integration
from orchestrator.integration import IntegratedPlanningLoop
from orchestrator.learning import FlowGRPOTrainer, AgentCoordination
from orchestrator.reasoning import VerificationFeedback


async def execute_planning_iterations(
    session: PlanningSession,
    session_manager: SessionManager,
    goal: str,
    proposal_data: Dict[str, Any],
    max_iterations: int = 1,
    checkpoint_interval: int = 2,
    debug: bool = False
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Execute multi-iteration planning with real-time progress updates.

    FIXES:
    - FIX #1: Plan stored in session for chat access
    - FIX #3: Detailed 1000+ word checkpoint summaries
    - FIX #4: Real-time progress events

    Yields:
    - planning_started: Multi-iteration planning begins
    - iteration_started: Each iteration starts
    - agent_progress: Real-time status of agent execution
    - checkpoint_reached: At checkpoint intervals (with full summary)
    - checkpoint_approved: User approved checkpoint
    - final_plan: Planning complete
    - error: If anything fails
    - complete: Stream end marker
    """
    try:
        memory_path = session.memory_path
        agent = session.agent

        if debug:
            print(f"🎯 Starting {max_iterations} iteration planning...")

        # Emit planning_started event
        yield {
            "type": "planning_started",
            "goal": goal,
            "max_iterations": max_iterations,
            "checkpoint_interval": checkpoint_interval
        }

        if max_iterations == 1:
            # ============= SINGLE ITERATION (NO CHECKPOINTS) =============
            yield {
                "type": "iteration_started",
                "iteration": 1,
                "max": 1
            }

            # Initialize orchestrator with memory enrichment (Phase 1.2)
            orchestrator = SimpleOrchestrator(
                memory_path=memory_path,
                max_iterations=1,
                segmented_memory=session.memory_manager  # FIX #2 - Enrich context with memory
            )

            # Run single iteration
            for result in orchestrator.run_iterative_planning(
                goal=goal,
                proposal=proposal_data.get("proposal_text", ""),
                max_iterations=1,
                checkpoint_interval=checkpoint_interval,
                llama_planner=LlamaPlanner(agent, memory_path)
            ):
                if isinstance(result, dict):
                    if result.get("type") == "final_plan":
                        # Store plan in session (FIX #1)
                        session_manager.store_plan(
                            session.id,
                            result.get("plan_content", ""),
                            result.get("frameworks", []),
                            result.get("data_points", 0),
                            iterations=1,
                            checkpoints=0
                        )

                        # Emit final plan
                        yield {
                            "type": "final_plan",
                            "plan": result.get("plan_content", ""),
                            "frameworks": result.get("frameworks", []),
                            "data_points": result.get("data_points", 0),
                            "iterations": 1,
                            "checkpoints": 0
                        }
        else:
            # ============= MULTI-ITERATION WITH CHECKPOINTS =============
            orchestrator = SimpleOrchestrator(
                memory_path=memory_path,
                max_iterations=max_iterations,
                segmented_memory=session.memory_manager  # FIX #2 - Enrich context with memory
            )

            llama_planner = LlamaPlanner(agent, memory_path)
            checkpoint_count = 0
            final_plan = ""
            all_frameworks = []
            all_data_points = 0
            previous_iteration_result = None

            # Run iteration generator
            for item in orchestrator.run_iterative_planning(
                goal=goal,
                proposal=proposal_data.get("proposal_text", ""),
                max_iterations=max_iterations,
                checkpoint_interval=checkpoint_interval,
                llama_planner=llama_planner
            ):
                if isinstance(item, dict):
                    # ===== CHECKPOINT REACHED =====
                    if item.get("type") == "checkpoint":
                        checkpoint_count += 1
                        current_iteration = item.get("iteration", checkpoint_count * checkpoint_interval)

                        if debug:
                            print(f"   ✓ Checkpoint {checkpoint_count} at iteration {current_iteration}")

                        # FIX #3: Generate DETAILED checkpoint summary (1000+ words)
                        detailed_summary = await generate_detailed_checkpoint_summary(
                            agent=agent,
                            goal=goal,
                            iteration_number=current_iteration,
                            current_result=item,
                            previous_result=previous_iteration_result,
                            debug=debug
                        )

                        # Store detailed summary in session
                        session_manager.store_checkpoint_summary(
                            session.id,
                            checkpoint_count,
                            detailed_summary,
                            {}  # Analysis data
                        )

                        # Get improvements analysis for JSON
                        improvement_analysis = await analyze_iteration_improvements(
                            agent=agent,
                            goal=goal,
                            iteration_number=current_iteration,
                            current_result=item,
                            previous_result=previous_iteration_result,
                            debug=debug
                        )

                        # Emit checkpoint event WITH FULL SUMMARY
                        yield {
                            "type": "checkpoint_reached",
                            "iteration": current_iteration,
                            "checkpoint_number": checkpoint_count,
                            "summary": detailed_summary,  # Full 1000+ word summary
                            "frameworks_so_far": item.get("frameworks_used", []),
                            "data_points_so_far": item.get("data_points_count", 0),
                            "improvements": improvement_analysis
                        }

                        # Block until user approves checkpoint
                        if debug:
                            print(f"   ⏳ Waiting for checkpoint {checkpoint_count} approval...")

                        checkpoint_approved = session_manager.wait_for_checkpoint_approval(session.id)

                        # Phase 1: Record flow score after user approval
                        # Phase 7: Record deferred flow score now that user has approved
                        if checkpoint_approved:
                            flow_score_metrics = item.get('flow_score_metrics', {})
                            if flow_score_metrics and hasattr(session, 'orchestrator'):
                                try:
                                    orchestrator = session.orchestrator
                                    if hasattr(orchestrator, 'flow_grpo_trainer'):
                                        orchestrator.flow_grpo_trainer.record_iteration_signal(
                                            iteration=flow_score_metrics.get('iteration', 0),
                                            agent_name=flow_score_metrics.get('agent_name', 'planner'),
                                            verification_quality=flow_score_metrics.get('verification_quality', 0.75),
                                            user_approved=True,  # Now we can record with actual approval
                                            reasoning_quality=flow_score_metrics.get('reasoning_quality', 0.7)
                                        )
                                        # Update agent selection weights based on approved flow score
                                        orchestrator.flow_grpo_trainer.update_agent_weights()
                                        if debug:
                                            print(f"   📊 Flow score recorded after user approval: {flow_score_metrics.get('flow_score', 0):.3f}")
                                except Exception as e:
                                    if debug:
                                        print(f"   ⚠️  Could not record deferred flow score: {e}")

                        # Phase 1: Update memory on approval
                        if checkpoint_approved:
                            if debug:
                                print(f"   ✅ Checkpoint {checkpoint_count} APPROVED - Updating memory...")

                            # Add checkpoint summary to memory
                            session.memory_manager.add_segment(
                                content=detailed_summary,
                                source=f"checkpoint_{checkpoint_count}_approved",
                                importance_score=0.85,
                                semantic_tags=["checkpoint", "approved", "iteration", str(current_iteration)]
                            )

                            # Phase 4: Store learned pattern effectiveness in memory
                            # Extract pattern effectiveness information if available
                            patterns_metadata = item.get('patterns_metadata', {})
                            if patterns_metadata:
                                try:
                                    pattern_effectiveness_content = f"""# Learned Pattern Effectiveness - Iteration {current_iteration}

**Timestamp:** {datetime.now().isoformat()}

## Patterns Applied in This Iteration

"""
                                    for pattern_name, pattern_info in patterns_metadata.items():
                                        effectiveness = pattern_info.get('effectiveness', 0.5)
                                        flow_score = pattern_info.get('flow_score', 0.0)
                                        pattern_effectiveness_content += f"\n### {pattern_name}\n"
                                        pattern_effectiveness_content += f"- Effectiveness: {effectiveness:.2f}\n"
                                        pattern_effectiveness_content += f"- Flow Score: {flow_score:.3f}\n"
                                        pattern_effectiveness_content += f"- User Approved: ✅\n"

                                    session.memory_manager.add_segment(
                                        content=pattern_effectiveness_content,
                                        source=f"pattern_effectiveness_iteration_{current_iteration}",
                                        importance_score=0.8,
                                        semantic_tags=["pattern", "effectiveness", "learning", str(current_iteration)]
                                    )
                                    if debug:
                                        print(f"   📚 Stored pattern effectiveness data in memory")
                                except Exception as e:
                                    if debug:
                                        print(f"   ⚠️  Could not store pattern effectiveness: {e}")

                            # Train memory overwrite scores based on approval
                            session.memory_manager.train_overwrite_scores(
                                plan_result={
                                    'user_approved': True,
                                    'quality_score': item.get('quality_score', 0.75),
                                    'iteration': current_iteration,
                                    'frameworks_used': item.get('frameworks_used', []),
                                    'patterns_applied': list(patterns_metadata.keys()) if patterns_metadata else []
                                },
                                user_approved=True
                            )

                            if debug:
                                memory_summary = session.memory_manager.get_memory_summary()
                                print(f"   📊 Memory: {memory_summary['segment_count']}/{memory_summary['max_segments']} segments")

                        # Phase 3.A: FIX #2 - Add rejection learning path
                        else:
                            if debug:
                                print(f"   ❌ Checkpoint {checkpoint_count} REJECTED - Recording negative learning signals...")

                            # Record negative flow score for learning
                            flow_score_metrics = item.get('flow_score_metrics', {})
                            if flow_score_metrics and hasattr(session, 'orchestrator'):
                                try:
                                    orchestrator = session.orchestrator
                                    if hasattr(orchestrator, 'flow_grpo_trainer'):
                                        # Record with user_approved=False (negative signal)
                                        orchestrator.flow_grpo_trainer.record_iteration_signal(
                                            iteration=flow_score_metrics.get('iteration', 0),
                                            agent_name=flow_score_metrics.get('agent_name', 'planner'),
                                            verification_quality=flow_score_metrics.get('verification_quality', 0.75) * 0.3,  # Penalty
                                            user_approved=False,  # CRITICAL: Negative signal
                                            reasoning_quality=flow_score_metrics.get('reasoning_quality', 0.7) * 0.3  # Penalty
                                        )
                                        # Update agent selection weights with negative signals
                                        orchestrator.flow_grpo_trainer.update_agent_weights()
                                        if debug:
                                            print(f"   📊 Negative flow score recorded: {flow_score_metrics.get('flow_score', 0) * 0.3:.3f}")
                                            print(f"   🧠 Agent weights updated to discourage similar patterns")
                                except Exception as e:
                                    if debug:
                                        print(f"   ⚠️  Could not record rejection signal: {e}")

                            # Phase 3.A: FIX #3 - Log rejection to planning_errors entity
                            try:
                                errors_file = session.memory_manager.memory_path / "entities" / "planning_errors.md"
                                rejection_entry = f"""
## Rejected Checkpoint - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Checkpoint:** {checkpoint_count}
**Iteration:** {current_iteration}
**Goal:** {item.get('goal', 'Unknown')}
**Reason:** User rejected during checkpoint approval gate

**Rejected Content Summary:**
{item.get('summary', '')[:500]}...

**Patterns Applied (Now marked low-effectiveness):**
{', '.join(list(item.get('patterns_metadata', {}).keys())) if item.get('patterns_metadata') else 'None'}

**Impact:** System will learn to avoid similar approaches in future iterations

---
"""
                                if errors_file.exists():
                                    with open(errors_file, 'a') as f:
                                        f.write(rejection_entry)
                                    if debug:
                                        print(f"   📚 Rejection logged to planning_errors entity")
                            except Exception as e:
                                if debug:
                                    print(f"   ⚠️  Could not log rejection: {e}")

                        # Phase 3.A: FIX #4 - Emit correct event and reset conditionally
                        if checkpoint_approved:
                            # User approved - emit confirmation and prepare for next checkpoint
                            yield {
                                "type": "checkpoint_approved",
                                "checkpoint": checkpoint_count
                            }
                            # Reset for next checkpoint (only if continuing)
                            session_manager.reset_checkpoint_state(session.id)
                        else:
                            # User rejected - emit rejection and stop planning
                            yield {
                                "type": "checkpoint_rejected",
                                "checkpoint": checkpoint_count,
                                "message": "Planning halted - user rejected checkpoint"
                            }
                            # Don't reset state on rejection - planning is stopped
                            if debug:
                                print(f"   🛑 Planning halted. Session state preserved for review.")
                        previous_iteration_result = item

                    # ===== FINAL PLAN =====
                    elif item.get("type") == "final_plan":
                        final_plan = item.get("plan_content", "")
                        all_frameworks = item.get("frameworks", [])
                        all_data_points = item.get("data_points", 0)

                        # Store plan in session (FIX #1)
                        session_manager.store_plan(
                            session.id,
                            final_plan,
                            all_frameworks,
                            all_data_points,
                            iterations=max_iterations,
                            checkpoints=checkpoint_count
                        )

                        # Emit final plan
                        yield {
                            "type": "final_plan",
                            "plan": final_plan,
                            "frameworks": all_frameworks,
                            "data_points": all_data_points,
                            "iterations": max_iterations,
                            "checkpoints": checkpoint_count
                        }

        # Stream complete
        yield {
            "type": "complete"
        }

    except Exception as e:
        if debug:
            print(f"❌ Planning error: {e}")
        yield {
            "type": "error",
            "error": str(e)
        }


async def format_sse_event(event_data: Dict[str, Any]) -> str:
    """Format event data as SSE line."""
    return f"data: {json.dumps(event_data)}\n\n"


async def generate_proposal_with_context(
    goal: str,
    selected_entities: Optional[list],
    selected_agents: Optional[list],
    llama_planner: Any,
    max_iterations: int = 1,
    checkpoint_interval: int = 2,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Generate planning proposal that includes full context.

    Returns proposal data ready to store in session.
    """
    from context_manager import generate_goal_specific_queries

    try:
        queries = generate_goal_specific_queries(goal)

        # Propose approach using Llama
        approach_plan = {
            "memory_percentage": 0.6,
            "research_percentage": 0.4,
            "research_focus": queries[:5],
            "agents_to_use": selected_agents or ["PlannerAgent", "VerifierAgent"],
            "resource_estimate": {
                "estimated_time_minutes": max_iterations * 5,
                "memory_searches": len(queries),
                "web_searches": 10,
                "agents_to_call": len(selected_agents or [])
            }
        }

        proposal_text = f"""# Planning Proposal

**Goal:** {goal}

## Approach
- **Iterations:** {max_iterations}
- **Checkpoint Interval:** {checkpoint_interval}
- **Memory Coverage:** 60%
- **Research Coverage:** 40%

## What We'll Search
{chr(10).join([f"- {q}" for q in queries[:5]])}

## Expected Output
- Comprehensive strategic plan (3000-5000+ words)
- Key insights and recommendations
- Implementation timeline
- Success metrics and KPIs

## Ready to proceed?
Click "Approve" to start planning."""

        return {
            "goal": goal,
            "proposal_text": proposal_text,
            "selected_entities": selected_entities or [],
            "selected_agents": selected_agents or [],
            "max_iterations": max_iterations,
            "checkpoint_interval": checkpoint_interval,
            "approach_plan": approach_plan,
            "queries": queries
        }

    except Exception as e:
        return {
            "error": str(e),
            "goal": goal
        }
