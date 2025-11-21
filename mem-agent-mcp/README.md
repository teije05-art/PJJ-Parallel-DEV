# Project Jupiter - Streamlit Frontend

Complete Streamlit frontend with full feature parity to the HTML chatbox.

## Features

✅ **Complete Feature Parity:**
- Goal input and configuration
- Entity selection (user-constrained)
- Plan selection (user-constrained)
- Real-time planning execution
- Checkpoint approval with 5 tabs
- MemAgent chat interface
- Planning history

✅ **Connected to Complete Backend:**
- IntegratedOrchestrator integration
- All Evolution Paths active (Flow-GRPO, PDDL, Agent Coordination)
- User-constrained memory and learning
- Multi-user support

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
cd /home/user/PJJ-Parallel-MAXDEV/mem-agent-mcp/streamlit_frontend
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### 1. Configure Planning

**Sidebar:**
- Enter your planning goal
- Select memory scope (private/shared/both)
- Choose entities to use (user-constrained)
- Choose past plans to learn from (user-constrained)
- Set iterations and checkpoint interval

### 2. Generate Plan

Click "🚀 Generate Plan" to start planning.

The system will:
- Only read selected entities (human-in-the-loop)
- Only learn from selected plans (cost control)
- Apply Flow-GRPO training
- Run PDDL verification
- Track agent coordination

### 3. Review at Checkpoints

When checkpoints appear, review 5 tabs:
- **Summary**: Overview and metrics
- **Entity Utilization**: Which memory was used
- **Plan Alignment**: Goal alignment analysis
- **Reasoning**: PDDL reasoning chains
- **Verification**: Verification results

Approve or request changes.

### 4. Chat with Plan

Use the Chat tab to:
- Ask questions about the plan
- Request clarifications
- Refine specific sections

Powered by MemAgent semantic search.

### 5. View History

See all past plans in the History tab.
Load previous plans to chat or review.

## Architecture

```
app.py (main entry point)
    ↓
IntegratedOrchestrator (backend)
    ↓
All Systems:
    ✅ User-constrained memory/plans
    ✅ Flow-GRPO training
    ✅ PDDL verification
    ✅ Agent coordination
    ✅ Multi-user isolation
    ✅ MemAgent chat
```

## Configuration

### Multi-User Support

Change the User ID in the sidebar to switch users.
Each user gets isolated private memory.

### Memory Scope

- **Private**: Only your memory
- **Shared**: Organizational memory
- **Both**: Combined (private first, then shared)

## Features by Tab

### Planning Tab
- Configure and execute planning
- View generated plans
- Download plans as markdown
- See detailed metadata

### Chat Tab
- Natural language Q&A about plans
- MemAgent semantic search
- Conversation history
- Context-aware responses

### History Tab
- All past plans
- Load previous plans
- Metrics and metadata
- Chronological view

## Technical Details

**Frontend:** Streamlit (Python)
**Backend:** IntegratedOrchestrator
**Memory:** local-memory/
**LLM:** Fireworks (heavy reasoning) + MemAgent (semantic search)

**Lines of Code:** ~450 lines
**Dependencies:** streamlit, pathlib
**Time to Start:** <5 seconds

## Production Ready

✅ Error handling
✅ User feedback
✅ Progress indicators
✅ Graceful degradation
✅ Session management
✅ Multi-user support

## Next Steps

1. Run `streamlit run app.py`
2. Generate your first plan
3. Test all features
4. Customize as needed

Enjoy your complete Project Jupiter planning system! 🪐
