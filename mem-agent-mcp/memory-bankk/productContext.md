# Product Context: Learning Orchestrator for Consulting

## Why This Project Exists
Cursor AI agents have limited context windows and don't remember past errors, successes, or project goals across sessions. This creates inefficiency and repetition. The learning orchestrator solves this by:

1. **Persistent Learning**: Accumulates knowledge in memory files that persist across sessions
2. **Progressive Improvement**: Each iteration builds on previous successes and learns from failures
3. **Context Preservation**: Maintains project context and goals throughout development
4. **Error Prevention**: Learns from past mistakes to avoid repeating them

## Problems It Solves
- **Context Loss**: AI agents forget previous work and decisions
- **Repeated Mistakes**: Same errors occur across different sessions
- **Goal Drift**: Project objectives get lost or misaligned over time
- **Inefficient Planning**: Each session starts from scratch without learned context
- **Manual Documentation**: Requires constant manual updates to maintain context

## How It Should Work
1. **Natural Interface**: User talks to Claude Desktop in natural language
2. **Learning Loop**: System generates plans, validates them, gets approval, executes, and learns
3. **Memory Accumulation**: Each iteration adds to memory files (execution_log.md, successful_patterns.md, planning_errors.md)
4. **Progressive Intelligence**: System gets smarter with each iteration through accumulated context
5. **Deliverable Creation**: Actually creates work products, not just plans

## User Experience Goals
- **Seamless Integration**: Works within existing Claude Desktop workflow
- **Natural Language**: No technical commands, just conversation
- **Learning Transparency**: User can see what the system has learned
- **Quality Output**: Generates high-quality consulting deliverables
- **Efficiency**: Reduces repetitive work and improves over time

## Target Use Cases
- **KPMG Consulting**: Complex strategy projects with multiple deliverables
- **Market Analysis**: Vietnam QSR market study with 10 key research questions
- **Competitive Intelligence**: Analysis of market landscape and trends
- **Risk Assessment**: Evaluation of market risks and opportunities
- **Strategic Planning**: Long-term planning with iterative improvement

## Success Metrics
- **Learning Rate**: System improves plan quality over iterations
- **Context Retention**: Maintains project context across sessions
- **Error Reduction**: Fewer repeated mistakes over time
- **Deliverable Quality**: High-quality outputs that meet consulting standards
- **User Efficiency**: Less time spent on repetitive tasks
