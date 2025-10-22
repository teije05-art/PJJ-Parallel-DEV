# System Patterns: Learning Orchestrator Architecture

## System Architecture
The learning orchestrator is integrated into the existing MCP server architecture with enhanced domain-agnostic capabilities:

```
Claude Desktop (Frontend)
    ↓ (MCP Protocol)
MCP Server (mcp_server/server.py)
    ├── use_memory_agent (existing)
    ├── start_planning_iteration (new)
    ├── approve_current_plan (new)
    ├── reject_current_plan (new)
    ├── view_learning_summary (new)
    └── list_entities (new)
    ↓
Enhanced Orchestrator + Llama + MemAgent
    ├── orchestrator/ directory
    │   ├── goal_analyzer.py (domain detection)
    │   ├── domain_templates.py (7 domain templates)
    │   ├── agentflow_agents.py (4-agent coordination)
    │   ├── orchestrator.py (main orchestrator)
    │   └── legacy_orchestrator.py (legacy orchestrator)
    ├── Llama 3.3 70B (Fireworks/vLLM)
    └── MemAgent memory system
```

## Key Technical Decisions

### 1. MCP Server Integration
- **Decision**: Add orchestrator tools to existing `mcp_server/server.py`
- **Rationale**: No new infrastructure needed, uses existing Claude connection
- **Implementation**: 5 new MCP tools added to existing server (including list_entities for entity discovery)

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

### 1. Enhanced Learning Loop Pattern
```
Iteration N:
1. Analyze Goal (domain detection)
2. Retrieve Context (dynamic entity selection)
3. Generate Plan (domain-specific CoT reasoning)
4. Coordinate Agents (4-agent workflow)
5. Validate Plan (with MemAgent)
6. Human Approval (or auto-approve)
7. Execute Plan (create deliverables)
8. Apply Flow-GRPO Training (LEARNING!)
9. Write to Memory (accumulate context)
```

### 2. Enhanced Memory Accumulation Pattern
- **execution_log.md**: Tracks successful iterations across all domains
- **successful_patterns.md**: Records proven approaches by domain
- **planning_errors.md**: Documents mistakes to avoid by domain
- **agent_coordination.md**: Tracks 4-agent workflow coordination
- **planner_training_log.md**: Records Flow-GRPO training signals
- **agent_performance.md**: Tracks performance metrics for each agent
- **Context Growth**: Each iteration adds ~400 chars of learned context

### 3. Chain-of-Thought Pattern
- **State-Action-State**: Explicit reasoning with preconditions and effects
- **Structured Planning**: [STATE s0] → [ACTION a1] → [STATE s1] → [ACTION a2] → [STATE s2]
- **Validation Gates**: Each step must satisfy preconditions before proceeding

### 4. Enhanced Human-in-the-Loop Pattern
- **Natural Language**: User communicates with Claude in plain English
- **Domain-Agnostic**: System adapts to any domain (healthcare, tech, manufacturing, etc.)
- **Approval Workflow**: Approve/reject/edit with feedback
- **Learning Signal**: Each decision becomes training data for future iterations
- **Flow-GRPO Training**: Real-time learning optimization based on outcomes

## Component Relationships

### Enhanced Orchestrator ↔ MemAgent
- **Dynamic Retrieval**: Goal analyzer determines relevant entities to retrieve
- **Domain-Specific Storage**: Writes learning results by domain
- **Validation**: MemAgent validates plans against domain-specific knowledge
- **Context Selection**: Dynamically selects context based on goal analysis

### Enhanced Orchestrator ↔ Llama
- **Domain-Specific Planning**: Llama generates plans using domain-specific templates
- **Rich Context**: Llama receives accumulated context from multiple domains
- **Flow-GRPO Learning**: Llama learns from Flow-GRPO training signals
- **Multi-Agent Coordination**: Llama coordinates with 4 specialized agents

### MCP Server ↔ Claude Desktop
- **Interface**: MCP tools provide natural language interface
- **Workflow**: Claude orchestrates the enhanced learning loop
- **Presentation**: Claude formats domain-specific plans and results for user
- **Domain Adaptation**: Claude adapts interface based on detected domain

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
