# Planning System Architecture Issue Analysis

## Executive Summary

The planning system has a **critical architectural flaw** that prevents it from being a general-purpose planner. Despite fixing all technical bugs, the system is hard-coded to only work with KPMG QSR projects, making it unsuitable for other domains.

## The Problem

### What's Happening
When users request planning for any domain (healthcare, tech, manufacturing, etc.), the system consistently generates QSR/Casual Dining plans because it's hard-coded to retrieve KPMG Jardine Pacific context.

### Evidence from Screenshots
- **User Request**: "American healthcare company looking to do business in Vietnam"
- **System Output**: "QSR and Casual Dining sectors" with "KPMG frameworks and methodologies"
- **Result**: Completely irrelevant plan for healthcare company

## Root Cause Analysis

### 1. Hard-coded Context Retrieval
**Location**: `/orchestrator/agentflow_agents.py` lines 207-209

```python
def _retrieve_project_context(self) -> str:
    response = self.agent.chat("""
        OPERATION: RETRIEVE
        ENTITY: KPMG_strategyteam_project  # ← HARD-CODED!
        CONTEXT: Comprehensive project context for strategic planning
```

### 2. KPMG-Specific Planning Prompts
**Location**: `/orchestrator/agentflow_agents.py` lines 116, 133, 152

```python
# Line 116: "LEVERAGES SPECIFIC PROJECT CONTEXT": Reference actual KPMG project requirements
# Line 133: "Specific action with KPMG methodology"
# Line 152: "Specific mitigation strategy using KPMG protocols"
```

### 3. No Goal Analysis
The system never analyzes the user's goal to determine relevant context. It always assumes KPMG QSR projects.

## Impact Assessment

### Affected Scenarios
- ✅ **KPMG QSR Projects**: Works perfectly
- ❌ **Healthcare Companies**: Gets QSR plans
- ❌ **Tech Startups**: Gets QSR plans
- ❌ **Manufacturing**: Gets QSR plans
- ❌ **Any Non-QSR Domain**: Gets QSR plans

### Business Impact
- **System Unusable**: Cannot be deployed as general-purpose planner
- **User Frustration**: Irrelevant plans for all non-QSR requests
- **Limited Scope**: Only works for one specific project type

## Proposed Solution Architecture

### Phase 1: Goal Analysis Module
```
USER GOAL → GOAL ANALYZER → DOMAIN DETECTOR → CONTEXT SELECTOR
```

### Phase 2: Dynamic Context Retrieval
```
Domain: Healthcare → Retrieve healthcare entities
Domain: Technology → Retrieve tech entities  
Domain: Manufacturing → Retrieve manufacturing entities
Domain: QSR → Retrieve KPMG QSR entities (current behavior)
```

### Phase 3: Generic Planning Templates
- Remove KPMG-specific language from prompts
- Create domain-agnostic planning templates
- Add domain-specific adaptation logic

## Required Changes

### 1. Core Architecture Changes
- [ ] Create GoalAnalyzer class
- [ ] Implement dynamic context selection
- [ ] Remove hard-coded entity retrieval
- [ ] Add domain detection logic

### 2. Planning Prompt Refactoring
- [ ] Remove KPMG-specific references
- [ ] Create generic planning templates
- [ ] Add domain adaptation mechanisms
- [ ] Implement fallback for unknown domains

### 3. Context Management
- [ ] Create domain-specific entity categories
- [ ] Implement context relevance scoring
- [ ] Add multi-entity retrieval support
- [ ] Create context combination logic

## Files Requiring Changes

1. **`/orchestrator/agentflow_agents.py`**
   - PlannerAgent._retrieve_project_context()
   - Planning prompt templates
   - Add GoalAnalyzer integration

2. **`/orchestrator/enhanced_orchestrator.py`**
   - Context retrieval logic
   - Add domain detection

3. **New Files Needed**
   - `goal_analyzer.py` - Goal analysis and domain detection
   - `context_selector.py` - Dynamic context selection
   - `domain_templates.py` - Domain-specific planning templates

## Implementation Priority

### High Priority (Critical)
1. Fix hard-coded entity retrieval
2. Add goal analysis capability
3. Create generic planning prompts

### Medium Priority
1. Implement domain-specific templates
2. Add context relevance scoring
3. Create fallback mechanisms

### Low Priority
1. Advanced domain detection
2. Multi-domain planning support
3. Context optimization

## Success Criteria

### Technical Success
- [ ] System works for healthcare companies
- [ ] System works for tech startups
- [ ] System works for manufacturing
- [ ] System still works for KPMG QSR projects

### User Success
- [ ] Relevant plans for all domains
- [ ] No more QSR plans for healthcare requests
- [ ] Appropriate methodologies per domain
- [ ] Scalable to new domains

## Conclusion

The planning system requires **major architectural refactoring** to become a true general-purpose planner. The current implementation is essentially a specialized KPMG QSR tool that cannot adapt to other domains.

**Recommendation**: Implement the proposed solution architecture to transform the system from a specialized tool into a flexible, domain-agnostic planning system.
