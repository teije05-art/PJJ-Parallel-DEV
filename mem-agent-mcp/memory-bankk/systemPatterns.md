# System Patterns: Learning Orchestrator Architecture

## System Architecture
The learning orchestrator is integrated into the existing MCP server architecture:

```
Claude Desktop (Frontend)
    ↓ (MCP Protocol)
MCP Server (mcp_server/server.py)
    ├── use_memory_agent (existing)
    ├── start_planning_iteration (new)
    ├── approve_current_plan (new)
    ├── reject_current_plan (new)
    └── view_learning_summary (new)
    ↓
Orchestrator + Llama + MemAgent
    ├── orchestrator/ directory
    ├── Llama 3.3 70B (Fireworks/vLLM)
    └── MemAgent memory system
```

## Key Technical Decisions

### 1. MCP Server Integration
- **Decision**: Add orchestrator tools to existing `mcp_server/server.py`
- **Rationale**: No new infrastructure needed, uses existing Claude connection
- **Implementation**: 4 new MCP tools added to existing server

### 2. Learning Mechanism
- **Decision**: In-context learning via memory accumulation (not fine-tuning)
- **Rationale**: No training phase needed, works immediately, uses existing model
- **Implementation**: Memory files grow with each iteration, providing richer context

### 3. Validation System
- **Decision**: MemAgent acts as validator (like VAL in PDDL-INSTRUCT paper)
- **Rationale**: Leverages existing memory system, provides ground truth checking
- **Implementation**: Checks preconditions, conflicts, and KPMG procedures

### 4. Two Operating Modes
- **Decision**: Manual mode (human approval each iteration) and Semi-autonomous mode
- **Rationale**: Flexibility for different use cases and confidence levels
- **Implementation**: Auto-approve valid plans, checkpoint every N iterations

## Design Patterns in Use

### 1. Learning Loop Pattern
```
Iteration N:
1. Retrieve Context (from memory)
2. Generate Plan (with CoT reasoning)
3. Validate Plan (with MemAgent)
4. Human Approval (or auto-approve)
5. Execute Plan (create deliverables)
6. Write to Memory (LEARNING!)
```

### 2. Memory Accumulation Pattern
- **execution_log.md**: Tracks successful iterations
- **successful_patterns.md**: Records proven approaches
- **planning_errors.md**: Documents mistakes to avoid
- **Context Growth**: Each iteration adds ~400 chars of learned context

### 3. Chain-of-Thought Pattern
- **State-Action-State**: Explicit reasoning with preconditions and effects
- **Structured Planning**: [STATE s0] → [ACTION a1] → [STATE s1] → [ACTION a2] → [STATE s2]
- **Validation Gates**: Each step must satisfy preconditions before proceeding

### 4. Human-in-the-Loop Pattern
- **Natural Language**: User communicates with Claude in plain English
- **Approval Workflow**: Approve/reject/edit with feedback
- **Learning Signal**: Each decision becomes training data for future iterations

## Component Relationships

### Orchestrator ↔ MemAgent
- **Retrieval**: Orchestrator queries MemAgent for context
- **Storage**: Orchestrator writes learning results to MemAgent
- **Validation**: MemAgent validates plans against stored knowledge

### Orchestrator ↔ Llama
- **Planning**: Llama generates plans using chain-of-thought reasoning
- **Context**: Llama receives accumulated context from memory
- **Learning**: Llama uses in-context examples to improve planning

### MCP Server ↔ Claude Desktop
- **Interface**: MCP tools provide natural language interface
- **Workflow**: Claude orchestrates the learning loop
- **Presentation**: Claude formats plans and results for user

## Memory System Patterns

### Entity Structure
```
memory/entities/
├── execution_log.md          # Successful iterations
├── successful_patterns.md    # Proven approaches
├── planning_errors.md        # Mistakes to avoid
├── KPMG_strategyteam_project.md  # Project context
└── [deliverable_entities]    # Generated work products
```

### Learning Accumulation
- **Iteration 1**: ~500 chars context (minimal)
- **Iteration 5**: ~2000 chars context (growing)
- **Iteration 10**: ~4000 chars context (expert level)
- **Iteration 15+**: ~6000+ chars context (mastery)

## Integration Patterns

### Backend Auto-Detection
```python
use_fireworks = sys.platform == "darwin"  # Mac uses Fireworks
use_vllm = sys.platform == "linux"        # H100 uses vLLM
```

### Memory Path Resolution
- **Local Development**: `/Users/teije/Desktop/memagent/local-memory`
- **Production**: Configurable via `.memory_path` file
- **Auto-Detection**: Falls back to default if not specified

### Error Handling
- **Validation Failures**: Pause autonomous mode, request human input
- **Execution Errors**: Log to planning_errors.md, continue learning
- **Memory Errors**: Graceful degradation, continue with available context
