# Planning System Flowchart - Current Issues Analysis

## Current Planning System Process

```
USER INPUT: "Start planning iteration for American healthcare company in Vietnam"
    ↓
1. start_planning_iteration(goal="American healthcare company in Vietnam")
    ↓
2. EnhancedLearningOrchestrator._retrieve_enhanced_context()
    ↓
3. AgentCoordinator.coordinate_agentic_workflow(goal, context)
    ↓
4. PlannerAgent.generate_strategic_plan(goal, context)
    ↓
5. _retrieve_project_context() - **PROBLEM HERE**
    ↓
6. Hard-coded query: "OPERATION: RETRIEVE ENTITY: KPMG_strategyteam_project"
    ↓
7. MemAgent returns KPMG/Jardine Pacific QSR context
    ↓
8. Planning prompt includes KPMG context regardless of user goal
    ↓
9. Generated plan defaults to QSR/Casual Dining framework
    ↓
10. User gets irrelevant plan about QSR instead of healthcare
```

## The Core Problem

**ISSUE**: The PlannerAgent._retrieve_project_context() method is hard-coded to always retrieve "KPMG_strategyteam_project" regardless of the user's actual goal.

**LOCATION**: `/orchestrator/agentflow_agents.py` lines 207-209

**CODE**:
```python
response = self.agent.chat("""
    OPERATION: RETRIEVE
    ENTITY: KPMG_strategyteam_project  # ← HARD-CODED!
    CONTEXT: Comprehensive project context for strategic planning
```

## Why This Happens

1. **Hard-coded Entity**: The planner always looks for "KPMG_strategyteam_project" 
2. **No Goal-Based Context**: The system doesn't analyze the user's goal to determine relevant context
3. **KPMG Bias**: The planning prompt is specifically designed for KPMG projects
4. **No Domain Adaptation**: The system can't adapt to different industries (healthcare, tech, etc.)

## Impact

- **American Healthcare Company** → Gets QSR/Casual Dining plan
- **Tech Startup** → Gets QSR/Casual Dining plan  
- **Manufacturing Company** → Gets QSR/Casual Dining plan
- **Any Non-QSR Goal** → Gets QSR/Casual Dining plan

## Root Cause Analysis

The planning system was designed specifically for the KPMG Jardine Pacific QSR project and never made generic. It's essentially a specialized tool masquerading as a general-purpose planner.

## Required Fixes

1. **Dynamic Context Retrieval**: Make context retrieval based on user goal analysis
2. **Goal-Based Entity Selection**: Analyze goal to determine relevant entities
3. **Generic Planning Prompts**: Remove KPMG-specific language from prompts
4. **Domain Adaptation**: Add logic to adapt planning approach to different industries
5. **Fallback Mechanisms**: Handle cases where no specific context exists

## Proposed Solution Architecture

```
USER GOAL → GOAL ANALYZER → RELEVANT CONTEXT SELECTOR → DOMAIN-SPECIFIC PLANNER
    ↓              ↓                    ↓                        ↓
"Healthcare"   "Healthcare"      Healthcare entities      Healthcare-specific
"in Vietnam"   "Vietnam market"  Vietnam context         planning approach
```

## Files That Need Changes

1. `/orchestrator/agentflow_agents.py` - PlannerAgent._retrieve_project_context()
2. `/orchestrator/agentflow_agents.py` - Planning prompt template
3. `/orchestrator/enhanced_orchestrator.py` - Context retrieval logic
4. Add new goal analysis module for dynamic context selection
