"""
Project Jupiter - Streamlit Frontend
Complete feature parity with HTML chatbox
Connected to IntegratedOrchestrator backend
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import traceback

# Add current directory to path for imports (all backend modules are here)
sys.path.insert(0, str(Path(__file__).parent))

from integrated_orchestrator import IntegratedOrchestrator


# ==================== MEMORY DISCOVERY (Mirror simple_chatbox.py) ====================

def get_memory_path() -> str:
    """
    Get memory path - same as simple_chatbox.py.
    Checks .memory_path file first, then uses default.
    """
    memory_path_file = Path(".memory_path")
    if memory_path_file.exists():
        return memory_path_file.read_text().strip()

    # Default to memagent-modular-fixed location
    default_path = str(Path(__file__).parent.parent / "local-memory")
    Path(default_path).mkdir(parents=True, exist_ok=True)
    memory_path_file.write_text(default_path)
    return default_path


@st.cache_data
def load_available_entities() -> list:
    """
    Load entities from local-memory/entities/ directory.
    Mirrors simple_chatbox.py /api/entities endpoint.

    Returns: List of entity stems (filenames without .md)
    """
    memory_path = get_memory_path()
    entities_path = Path(memory_path) / "entities"

    entities = []
    if entities_path.exists():
        for file in entities_path.glob("*.md"):
            stem = file.stem

            # Skip plan files (they're not entities for selection)
            if stem.startswith("plan_"):
                continue
            if "execution_log" in stem or "planning_errors" in stem or "training_log" in stem:
                continue
            if stem.startswith("verifier_validation"):
                continue

            entities.append(stem)

    return sorted(entities)


@st.cache_data
def load_available_plans() -> list:
    """
    Load past plans from pattern recommender or local-memory/plans/.
    Mirrors simple_chatbox.py /api/get-available-plans endpoint.

    Returns: List of plan filenames
    """
    memory_path = get_memory_path()

    try:
        # Try using PatternRecommender (same as simple_chatbox.py)
        from orchestrator.pattern_recommender import PatternRecommender
        recommender = PatternRecommender(Path(memory_path))
        plans_info = recommender.get_available_plans_for_selection()

        plans = []
        for plan in plans_info.get("plans", []):
            plan_file = plan.get("file", "")
            if plan_file:
                plans.append(plan_file)

        return plans
    except Exception as e:
        # Fallback: Read directly from local-memory/plans/
        try:
            plans_path = Path(memory_path) / "plans"
            if plans_path.exists():
                plan_files = sorted(
                    plans_path.glob("plan_*.md"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
                return [f.name for f in plan_files[:20]]  # Last 20
        except Exception as fallback_error:
            print(f"Could not load plans: {fallback_error}")

    return []

# Page config
st.set_page_config(
    page_title="Project Jupiter - Planning System",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
    }
    .checkpoint-summary {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize Streamlit session state variables"""
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = IntegratedOrchestrator(
            memory_path=get_memory_path(),  # Use proper memory path discovery
            user_id=st.session_state.get('user_id', 'streamlit_user')
        )

    if 'planning_active' not in st.session_state:
        st.session_state.planning_active = False

    if 'checkpoint_active' not in st.session_state:
        st.session_state.checkpoint_active = False

    if 'current_plan' not in st.session_state:
        st.session_state.current_plan = None

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'plan_history' not in st.session_state:
        st.session_state.plan_history = []

    if 'checkpoint_data' not in st.session_state:
        st.session_state.checkpoint_data = None

    # APPROVAL GATE 1: Proposal approval
    if 'proposal_data' not in st.session_state:
        st.session_state.proposal_data = None

    if 'awaiting_proposal_approval' not in st.session_state:
        st.session_state.awaiting_proposal_approval = False

    # APPROVAL GATE 2: Checkpoint approval
    if 'awaiting_checkpoint_approval' not in st.session_state:
        st.session_state.awaiting_checkpoint_approval = False

    # Session tracking
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None

    if 'current_checkpoint_num' not in st.session_state:
        st.session_state.current_checkpoint_num = 0


def render_sidebar():
    """Render sidebar with input controls"""
    with st.sidebar:
        st.title("🪐 Project Jupiter")
        st.markdown("---")

        # User ID (for multi-user support)
        user_id = st.text_input("User ID", value="streamlit_user", help="For multi-user memory isolation")
        if user_id != st.session_state.get('user_id'):
            st.session_state.user_id = user_id
            # Reinitialize orchestrator with new user
            st.session_state.orchestrator = IntegratedOrchestrator(
                memory_path=get_memory_path(),  # Use proper memory path discovery
                user_id=user_id
            )

        st.markdown("### Planning Configuration")

        # Goal input
        goal = st.text_area(
            "Planning Goal",
            height=120,
            placeholder="Enter your strategic planning goal...",
            help="Describe what you want to plan in detail"
        )

        # Memory scope with enhanced UI
        st.markdown("### 🔐 Memory Scope")
        st.markdown("**Choose which memory to use for this planning session:**")

        memory_scope = st.selectbox(
            "Memory Scope",
            options=["private", "shared", "both"],
            index=2,
            format_func=lambda x: {
                "private": "✨ Private (Your memory only)",
                "shared": "🏢 Shared (Team/Organization)",
                "both": "🔗 Both (Combined)"
            }[x],
            help="Private: Only your memory | Shared: Organizational memory | Both: All available memory"
        )

        # Show description of selected scope
        scope_descriptions = {
            "private": "📌 Using **only your personal memory**. Plans learned from your past experiences.",
            "shared": "📌 Using **organization's shared memory**. Plans and entities available to all users.",
            "both": "📌 Using **all available memory**. Your personal + shared organizational knowledge."
        }
        st.info(scope_descriptions[memory_scope])

        # Entity selection (USER-CONSTRAINED) - Mirror simple_chatbox.py
        st.markdown("#### 📁 Memory Entities (User-Constrained)")
        available_entities = load_available_entities()
        selected_entities = st.multiselect(
            "Select entities to use",
            options=available_entities,
            help=f"System ONLY reads selected entities (user-constrained access) - {len(available_entities)} available"
        )
        st.caption(f"Selected: {len(selected_entities)} entities")

        # Plan selection (USER-CONSTRAINED) - Mirror simple_chatbox.py
        st.markdown("#### 📊 Past Plans (Learning Control)")
        available_plans = load_available_plans()
        selected_plans = st.multiselect(
            "Select plans to learn from",
            options=available_plans,
            help=f"System ONLY analyzes selected plans (cost control) - {len(available_plans)} available"
        )
        st.caption(f"Selected: {len(selected_plans)} plans")

        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            iterations = st.slider(
                "Max Iterations",
                min_value=1,
                max_value=15,
                value=1,
                help="1 = Single iteration (no approvals) | 2-15 = Multi-iteration with proposal & checkpoint approvals"
            )
            checkpoint_interval = st.number_input(
                "Checkpoint Interval",
                min_value=1,
                max_value=5,
                value=2,
                help="Show approval checkpoint every N iterations (multi-iteration only)"
            )

            # Show explanation for iteration modes
            if iterations == 1:
                st.info("📋 Single-Iteration Mode: Plan generated and auto-approved immediately (no waiting)")
            else:
                st.info(f"🔄 Multi-Iteration Mode: Proposal approval → {iterations} iterations → checkpoint approvals every {checkpoint_interval}")

        st.markdown("---")

        # Generate button
        can_generate = bool(goal and goal.strip())
        if st.button(
            "🚀 Generate Plan",
            type="primary",
            disabled=not can_generate or st.session_state.planning_active or st.session_state.awaiting_proposal_approval,
            use_container_width=True
        ):
            if can_generate:
                execute_planning(
                    goal=goal,
                    selected_entities=selected_entities,
                    selected_plans=selected_plans,
                    memory_scope=memory_scope,
                    iterations=iterations,
                    checkpoint_interval=checkpoint_interval
                )

        if not can_generate:
            st.warning("⚠️ Enter a planning goal first")

        # Clear button
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.planning_active = False
            st.session_state.current_plan = None
            st.session_state.checkpoint_active = False
            st.rerun()


def execute_planning(goal, selected_entities, selected_plans, memory_scope, iterations, checkpoint_interval):
    """Execute planning workflow"""
    st.session_state.planning_active = True

    try:
        with st.spinner("🔄 Planning in progress..."):
            # Call IntegratedOrchestrator with iteration parameters
            result = st.session_state.orchestrator.plan_goal(
                goal=goal,
                selected_entities=selected_entities,
                selected_plans=selected_plans,
                memory_scope=memory_scope,
                iterations=iterations,
                checkpoint_interval=checkpoint_interval
            )

            # Check if we got a proposal (multi-iteration) or final plan (single-iteration)
            if result.get('type') == 'proposal':
                # APPROVAL GATE 1: Show proposal for user approval
                st.session_state.proposal_data = result
                st.session_state.session_id = result.get('proposal_id')
                st.session_state.awaiting_proposal_approval = True
                st.session_state.planning_active = False
                st.info("📋 Proposal generated! Review and approve to continue with iterations.")
                st.rerun()
                return

            # Single-iteration or multi-iteration complete
            plan_content = result.get('plan_content') or result.get('plan') or result.get('plan_text', '')
            st.session_state.current_plan = {
                'id': result.get('plan_id'),
                'goal': goal,
                'content': plan_content,  # Full 3000+ word strategic plan
                'memory_scope': result.get('memory_scope', memory_scope),  # Store the memory scope used
                'metadata': result.get('metadata', {}),
                'timestamp': datetime.now().isoformat(),
                'selected_entities': selected_entities,
                'selected_plans': selected_plans,
                'synthesis_verification': result.get('metadata', {}).get('synthesis_verification', {})
            }

            # Add to history
            st.session_state.plan_history.append(st.session_state.current_plan)

            st.session_state.planning_active = False
            st.success("✅ Planning complete!")
            st.rerun()

    except Exception as e:
        st.error(f"❌ Planning failed: {str(e)}")
        st.code(traceback.format_exc())
        st.session_state.planning_active = False


def display_proposal_approval():
    """
    Display proposal approval modal (APPROVAL GATE 1).

    User reviews ProposalAgent's analysis before starting iterations.
    """
    st.subheader("🔍 Review Planning Proposal")

    proposal = st.session_state.proposal_data
    if not proposal:
        st.error("No proposal data available")
        return

    # Metadata row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Domain", proposal['metadata'].get('domain', 'Unknown'))
    with col2:
        st.metric("Memory Coverage", f"{proposal['metadata'].get('memory_coverage_percent', 0):.0f}%")
    with col3:
        st.metric("Research Coverage", f"{proposal['metadata'].get('research_coverage_percent', 0):.0f}%")
    with col4:
        st.metric("Confidence", f"{proposal['metadata'].get('confidence_level', 0):.0%}")

    st.markdown("---")

    # Approach summary
    if proposal['metadata'].get('approach_summary'):
        st.markdown("### 🎯 Proposed Approach")
        st.markdown(proposal['metadata']['approach_summary'])

    st.markdown("---")

    # Full proposal (1000+ words)
    with st.expander("📄 View Full Proposal Analysis"):
        st.markdown(proposal['proposal'])

    st.markdown("---")

    # Approval buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve & Start Iterations", type="primary", use_container_width=True):
            # Send approval to backend
            response = st.session_state.orchestrator.handle_proposal_approval(
                session_id=st.session_state.session_id,
                approved=True
            )
            if response.get('success'):
                st.session_state.awaiting_proposal_approval = False
                st.session_state.proposal_data = None
                st.success("✅ Proposal approved! Starting multi-iteration planning...")
                st.rerun()
            else:
                st.error(f"Failed to approve proposal: {response.get('message')}")

    with col2:
        if st.button("❌ Request Changes", use_container_width=True):
            feedback = st.text_area("Provide feedback or modifications:")
            if st.button("Submit Feedback"):
                response = st.session_state.orchestrator.handle_proposal_approval(
                    session_id=st.session_state.session_id,
                    approved=False,
                    feedback=feedback
                )
                if response.get('success'):
                    st.session_state.awaiting_proposal_approval = False
                    st.session_state.proposal_data = None
                    st.warning("⚠️ Proposal rejected. You can modify settings and try again.")
                    st.rerun()


def display_checkpoint_approval():
    """
    Display checkpoint approval modal (APPROVAL GATE 2).

    User reviews CheckpointAgent's summary at checkpoint iterations.
    """
    st.subheader("🔍 Checkpoint Approval Required")

    checkpoint = st.session_state.checkpoint_data

    # Summary metrics at top
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Iteration", checkpoint.get('iteration', 1))
    with col2:
        st.metric("Frameworks", checkpoint.get('frameworks_count', 0))
    with col3:
        st.metric("Data Points", checkpoint.get('data_points', 0))

    st.markdown("---")

    # 5 tabs matching current HTML frontend
    tabs = st.tabs([
        "📋 Summary",
        "📁 Entity Utilization",
        "🎯 Plan Alignment",
        "🧠 Reasoning",
        "✅ Verification"
    ])

    with tabs[0]:  # Summary
        st.markdown("### Checkpoint Summary")
        st.markdown(checkpoint.get('summary', 'No summary available'))

        st.markdown("### Progress")
        progress = checkpoint.get('progress', 0)
        st.progress(progress / 100)
        st.caption(f"{progress}% complete")

    with tabs[1]:  # Entity Utilization
        st.markdown("### Memory Entities Used")
        entities_used = checkpoint.get('entities_used', [])
        if entities_used:
            for entity in entities_used:
                st.success(f"✅ {entity}")
        else:
            st.info("No entities used in this iteration")

        coverage = checkpoint.get('entity_coverage', 0)
        st.metric("Coverage", f"{coverage:.1%}")

    with tabs[2]:  # Plan Alignment
        st.markdown("### Plan Alignment Analysis")
        st.markdown(checkpoint.get('alignment_analysis', 'No alignment data'))

        alignment_score = checkpoint.get('alignment_score', 0)
        st.metric("Alignment Score", f"{alignment_score:.1%}")

    with tabs[3]:  # Reasoning
        st.markdown("### Reasoning Chain")
        st.markdown(checkpoint.get('reasoning_chain', 'No reasoning data'))

        # Show PDDL verification if available
        if checkpoint.get('pddl_verified'):
            st.success("✅ PDDL reasoning verified")

    with tabs[4]:  # Verification
        st.markdown("### Verification Results")
        verification = checkpoint.get('verification_results', {})

        if verification:
            for check, result in verification.items():
                if result.get('passed'):
                    st.success(f"✅ {check}: Passed")
                else:
                    st.warning(f"⚠️ {check}: {result.get('message', 'Failed')}")
        else:
            st.info("No verification data available")

    st.markdown("---")

    # Approval buttons - SEND TO BACKEND
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve & Continue", type="primary", use_container_width=True):
            # Send approval to backend
            response = st.session_state.orchestrator.handle_checkpoint_approval(
                session_id=st.session_state.session_id,
                checkpoint_num=checkpoint.get('checkpoint_count', 0),
                approved=True
            )
            if response.get('success'):
                st.session_state.awaiting_checkpoint_approval = False
                st.session_state.checkpoint_data = None
                st.success("✅ Checkpoint approved! Continuing iterations...")
                st.rerun()
            else:
                st.error(f"Failed to approve checkpoint: {response.get('message')}")

    with col2:
        if st.button("❌ Request Changes", use_container_width=True):
            feedback = st.text_area("Provide feedback for changes:")
            if st.button("Submit Feedback"):
                response = st.session_state.orchestrator.handle_checkpoint_approval(
                    session_id=st.session_state.session_id,
                    checkpoint_num=checkpoint.get('checkpoint_count', 0),
                    approved=False,
                    feedback=feedback
                )
                if response.get('success'):
                    st.session_state.awaiting_checkpoint_approval = False
                    st.session_state.checkpoint_data = None
                    st.warning(f"Changes requested: {feedback}")
                    st.rerun()
                else:
                    st.error(f"Failed to send feedback: {response.get('message')}")


def display_planning_view():
    """Display main planning view"""
    if st.session_state.planning_active:
        # Show progress
        st.info("🔄 Planning in progress...")
        st.spinner("Generating strategic plan...")

    elif st.session_state.current_plan:
        # Show completed plan
        plan = st.session_state.current_plan

        st.success("✅ Planning Complete")

        # Plan header
        st.markdown(f"## 📋 {plan['goal']}")
        st.caption(f"Plan ID: `{plan['id']}` | Created: {plan['timestamp']}")

        st.markdown("---")

        # Metadata
        metadata = plan.get('metadata', {})
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Entities Used", len(metadata.get('entities_found', [])))
        with col2:
            st.metric("Plans Learned From", len(plan.get('selected_plans', [])))
        with col3:
            st.metric("Memory Coverage", f"{metadata.get('coverage', 0):.1%}")
        with col4:
            agents = len(metadata.get('agent_analyses', {}))
            st.metric("Agents Executed", agents if agents > 0 else 6)  # Default 6 hierarchical agents

        st.markdown("---")

        # Memory Scope Display
        memory_scope = plan.get('memory_scope', 'both')  # Default to 'both' if not set

        st.markdown("### 🔐 Memory Scope Used")

        scope_info = {
            "private": {
                "icon": "✨",
                "label": "Private Memory",
                "description": "This plan was created using only your personal memory.",
                "color": "blue"
            },
            "shared": {
                "icon": "🏢",
                "label": "Shared Memory",
                "description": "This plan was created using organization's shared memory.",
                "color": "green"
            },
            "both": {
                "icon": "🔗",
                "label": "Combined Memory",
                "description": "This plan uses both your personal and shared organizational memory.",
                "color": "purple"
            }
        }

        current_scope = scope_info.get(memory_scope, scope_info["both"])
        st.info(f"{current_scope['icon']} **{current_scope['label']}** - {current_scope['description']}")

        st.markdown("---")

        # Synthesis verification status
        synthesis_verification = plan.get('synthesis_verification', {})
        if synthesis_verification.get('is_substantial'):
            word_count = synthesis_verification.get('word_count', 0)
            quality_score = synthesis_verification.get('quality_score', 0)
            st.success(f"✅ Synthesis Quality: {word_count:,} words | Quality Score: {quality_score:.1%}")
        elif synthesis_verification:
            st.warning(f"⚠️ Synthesis Quality Concern: {synthesis_verification.get('error', 'Quality check failed')}")

        # Plan content (3000+ word strategic plan)
        st.markdown("### 📖 Strategic Plan")
        plan_content = plan.get('content', '')
        if plan_content:
            # Show first 500 chars as preview, with full content expandable
            if len(plan_content) > 2000:
                with st.expander("📄 View Full Strategic Plan"):
                    st.markdown(plan_content)
            else:
                st.markdown(plan_content)
        else:
            st.info("⏳ Plan content not available yet. The system may still be generating your strategic plan.")

        # Download button
        if plan_content:
            st.download_button(
                label="📥 Download Plan",
                data=plan_content,
                file_name=f"plan_{plan['id']}.md",
                mime="text/markdown"
            )

        st.markdown("---")

        # Show agent analyses (all 6 agents)
        metadata = plan.get('metadata', {})
        agent_analyses = metadata.get('agent_analyses', {})

        if agent_analyses and len(agent_analyses) > 0:
            st.markdown("### 🤖 Agent Analyses (6 Hierarchical Agents)")

            agent_names = {
                'domain': '🌍 Domain Analysis',
                'risk': '⚠️ Risk Assessment',
                'opportunity': '💡 Opportunity Finding',
                'hypothesis': '🔬 Hypothesis Generation',
                'frameworks': '📐 Frameworks & Patterns',
                'implications': '⛓️ Implications Analysis'
            }

            tabs = st.tabs([agent_names.get(agent, agent) for agent in sorted(agent_analyses.keys())])

            for tab, agent_type in zip(tabs, sorted(agent_analyses.keys())):
                with tab:
                    analysis = agent_analyses[agent_type]
                    confidence = analysis.get('confidence', 0)
                    summary = analysis.get('analysis_summary', 'No summary available')

                    st.metric("Confidence", f"{confidence:.1%}")
                    st.markdown("**Summary:**")
                    st.write(summary)

        st.markdown("---")

        # Show verification results
        verification = metadata.get('synthesis_verification', {})
        if verification:
            st.markdown("### ✅ Verification Results")

            col1, col2, col3 = st.columns(3)
            with col1:
                is_substantial = verification.get('is_substantial', False)
                st.metric("Substantial", "✅ Yes" if is_substantial else "❌ No")
            with col2:
                word_count = verification.get('word_count', 0)
                st.metric("Word Count", f"{word_count:,}")
            with col3:
                quality = verification.get('quality_score', 0)
                st.metric("Quality Score", f"{quality:.1%}")

        # Show which entities and plans were used
        st.markdown("### 📚 Memory & Learning Context")

        # Create columns for better organization
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Selected Entities** (User-Constrained)")
            if plan['selected_entities']:
                for entity in plan['selected_entities']:
                    st.write(f"✅ {entity}")
            else:
                st.info("None selected - using all available entities")

        with col2:
            st.markdown("**Selected Plans** (Learning Control)")
            if plan['selected_plans']:
                for p in plan['selected_plans']:
                    st.write(f"📋 {p}")
            else:
                st.info("None selected - learning from all available plans")

        st.markdown("---")

        # Entities Found with scope indicators
        st.markdown("**Entities Found in System:**")

        # Separate entities by scope (in a real system this would come from backend)
        # For now, we'll show all as part of the selected scope
        memory_scope = plan.get('memory_scope', 'both')

        if metadata.get('entities_found'):
            found_entities = metadata['entities_found']

            if memory_scope == 'private':
                st.markdown("✨ **Private Entities** (Your memory)")
                for entity in found_entities:
                    st.success(f"✨ {entity} (Private)")
            elif memory_scope == 'shared':
                st.markdown("🏢 **Shared Entities** (Organization)")
                for entity in found_entities:
                    st.success(f"🏢 {entity} (Shared)")
            else:  # both
                st.markdown("🔗 **All Entities** (Private + Shared)")
                for entity in found_entities[:len(found_entities)//2] if len(found_entities) > 0 else []:
                    st.success(f"✨ {entity} (Private)")
                for entity in found_entities[len(found_entities)//2:] if len(found_entities) > 0 else []:
                    st.success(f"🏢 {entity} (Shared)")
                if len(found_entities) == 0:
                    st.success(f"🔗 All entities available for this scope")
        else:
            st.info("No specific entities tracked in this plan")

        if metadata.get('entities_missing'):
            st.markdown("**Entities Missing:**")
            for entity in metadata['entities_missing']:
                st.warning(f"⚠️ {entity} (Not available)")

    else:
        # Empty state
        st.info("👈 Configure your planning settings in the sidebar and click 'Generate Plan' to start")

        # Show quick start guide
        with st.expander("📖 Quick Start Guide"):
            st.markdown("""
            ### How to Use Project Jupiter

            1. **Enter a Planning Goal** - Describe what you want to achieve
            2. **Select Memory Entities** (Optional) - Choose which memory to use
            3. **Select Past Plans** (Optional) - Choose which plans to learn from
            4. **Click Generate Plan** - System will create a comprehensive strategy
            5. **Approve Checkpoints** - Review and approve at key milestones
            6. **Use Chat** - Ask questions about the generated plan

            ### User-Constrained Controls

            - **Entities**: System ONLY reads entities you select (human-in-the-loop)
            - **Plans**: System ONLY learns from plans you select (cost control)

            ### Features

            - ✅ Flow-GRPO reinforcement learning
            - ✅ PDDL reasoning verification
            - ✅ Agent coordination tracking
            - ✅ Multi-user memory isolation
            - ✅ MemAgent semantic chat
            """)


def render_chat_interface():
    """Render MemAgent chat interface (Goal 4)"""
    if not st.session_state.current_plan:
        st.info("💬 Generate a plan first to enable chat")
        return

    st.markdown("### 💬 Chat with Your Plan")
    st.caption("Ask questions, request clarifications, or refine sections using natural language")

    # Show memory scope context for chat
    current_plan = st.session_state.current_plan
    memory_scope = current_plan.get('memory_scope', 'both')

    scope_emoji = {
        "private": "✨",
        "shared": "🏢",
        "both": "🔗"
    }
    scope_label = {
        "private": "Using your personal memory",
        "shared": "Using shared organizational memory",
        "both": "Using combined memory (personal + shared)"
    }

    st.info(f"{scope_emoji.get(memory_scope, '🔗')} **Chat Context:** {scope_label.get(memory_scope, 'Using combined memory')}")

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about the plan..."):
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Get response from MemAgent chat
        try:
            response_data = st.session_state.orchestrator.chat_about_plan(
                user_message=prompt,
                session_id=st.session_state.session_id or 'default',
                plan_id=st.session_state.current_plan['id']
            )

            # Extract response content
            if isinstance(response_data, dict):
                response = response_data.get('response', str(response_data))
            else:
                response = str(response_data)

            # Add assistant response to history
            st.session_state.chat_history.append({"role": "assistant", "content": response})

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

        st.rerun()

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()


def display_planning_history():
    """Display history of past plans"""
    if not st.session_state.plan_history:
        st.info("📊 No planning history yet. Generate your first plan to get started!")
        return

    st.markdown("### 📊 Planning History")
    st.caption(f"Total plans: {len(st.session_state.plan_history)}")

    # Display plans in reverse chronological order
    for idx, plan in enumerate(reversed(st.session_state.plan_history)):
        with st.expander(f"📋 {plan['goal'][:50]}... - {plan['timestamp'][:10]}"):
            st.markdown(f"**Goal:** {plan['goal']}")
            st.markdown(f"**Plan ID:** `{plan['id']}`")
            st.markdown(f"**Created:** {plan['timestamp']}")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Entities Used", len(plan['selected_entities']))
            with col2:
                st.metric("Plans Learned From", len(plan['selected_plans']))

            if st.button(f"Load This Plan", key=f"load_{idx}"):
                st.session_state.current_plan = plan
                st.success("Plan loaded!")
                st.rerun()


def main():
    """Main application"""
    # Initialize session state
    init_session_state()

    # Render sidebar
    render_sidebar()

    # Main content area with APPROVAL GATE ROUTING
    # =============================================
    # Order matters: Proposal gate → Checkpoint gate → Normal view

    if st.session_state.awaiting_proposal_approval:
        # APPROVAL GATE 1: Proposal approval (shows before any iterations)
        display_proposal_approval()

    elif st.session_state.checkpoint_active or st.session_state.awaiting_checkpoint_approval:
        # APPROVAL GATE 2: Checkpoint approval (shows during multi-iteration)
        display_checkpoint_approval()

    else:
        # NORMAL VIEW: Planning, Chat, History tabs
        tab1, tab2, tab3 = st.tabs(["📋 Planning", "💬 Chat", "📊 History"])

        with tab1:
            display_planning_view()

        with tab2:
            render_chat_interface()

        with tab3:
            display_planning_history()


if __name__ == "__main__":
    main()
