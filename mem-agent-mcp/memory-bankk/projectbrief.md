# Project Brief: PDDL-INSTRUCT Learning Orchestrator

## Project Overview
Building a PDDL-INSTRUCT-inspired learning orchestrator integrated into an MCP server with MemAgent. The system uses MemAgent to create, append, and retrieve plain text memory entities (unlimited capacity, no hallucinations—strictly based on user input and stored data). The orchestrator script (~800 lines) implements a learning loop that generates plans with chain-of-thought reasoning, validates them with MemAgent, gets human approval, executes approved plans, and accumulates learning in memory files.

## Core Goal
Create an autonomous planning system that learns from iterations and gets progressively smarter through memory accumulation. The system should be able to process complex consulting projects (like KPMG strategy work) and generate comprehensive deliverables while learning from each interaction.

## Key Requirements
- **Learning System**: Must learn from each iteration and improve over time
- **Memory Integration**: Seamlessly integrate with existing MemAgent memory system
- **Human-in-the-Loop**: Natural language approval/rejection via Claude Desktop
- **Validation**: MemAgent acts as validator checking preconditions and procedures
- **Deliverable Generation**: Create actual work products (reports, analyses, etc.)
- **Two Modes**: Manual (human approval each iteration) and Semi-autonomous (auto-approve with checkpoints)

## Success Criteria
- System gets progressively smarter with each iteration
- Memory accumulation provides rich context for future planning
- Natural language interface works seamlessly
- Generates high-quality consulting deliverables
- Integrates cleanly with existing MCP server infrastructure

## Project Scope
- Integrate orchestrator into existing MCP server
- Implement 6-step learning loop
- Create memory entities for learning accumulation
- Support both manual and autonomous planning modes
- Handle KPMG consulting project context and requirements
