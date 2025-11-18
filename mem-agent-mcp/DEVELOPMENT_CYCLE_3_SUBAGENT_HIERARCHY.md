# DEVELOPMENT CYCLE 3: SUBAGENT HIERARCHY - REPLACE 4-AGENT PIPELINE
**Version:** 1.0
**Created:** November 14, 2025
**Duration:** ~1 day
**Scope:** Replace 4-agent pipeline with hierarchical structure; implement 6 specialized subagents
**Depends On:** DEVELOPMENT_CYCLE_1 (Clean Architecture) + DEVELOPMENT_CYCLE_2 (Multi-User Memory) ← Both must be complete
**Status:** Ready for Execution

---

## 1. STRATEGIC PURPOSE

### What is Being Developed?

A fundamental redesign of the agent system:
- **Current:** Fixed 4-agent pipeline (Planner → Verifier → Executor → Generator)
- **Future:** Hierarchical agent system where specialized subagents handle specific analysis tasks
- **6 Initial Subagent Types:**
  1. **Domain Analyzer** - Analyzes domain-specific context and market realities
  2. **Risk Assessor** - Identifies and quantifies risks
  3. **Opportunity Finder** - Surfaces opportunities and advantages
  4. **Hypothesis Generator** - Creates and tests hypotheses
  5. **Frameworks Discoverer** - Identifies applicable frameworks and patterns
  6. **Implications Analyzer** - Works out consequences and dependencies
- **Pluggable:** New subagent types can be added without redesigning orchestrator

### Why Does This Matter?

**Current Limitation:** 4 agents do general planning. Hard to add specialized analysis without modifying agent code.

**What This Enables:**
- **Agent Coordination (Path 7):** Orchestrator dynamically selects which subagents to spawn
- **Specialized Analysis:** Each subagent is expert in its domain (risk, opportunity, frameworks)
- **Scalability:** Adding new analysis types doesn't require rewriting orchestrator
- **Multi-Agent Reasoning (Section 2):** Agents can debate internally, present options to user
- **Complex Planning:** More sophisticated problems get more subagents; simple problems stay lean

### Success Criteria

✅ Hierarchical agent system replaces 4-agent pipeline
✅ 6 initial subagent types implemented and working
✅ Orchestrator dynamically selects appropriate subagents
✅ Subagents can be spawned on-demand during planning
✅ Planning output quality equals or exceeds current system
✅ New subagent types can be added without changes to orchestrator
✅ All tests passing
✅ Zero behavioral regressions

---

## 2. EXTERNAL REFERENCES ANALYZED

### Source 1: CrewAI Hierarchical Structure
**URL:** `https://github.com/crewAIInc/crewAI`

**Key Patterns:**
- **Agent Base Class:** Common interface all agents implement
- **Task-Driven:** Agents take tasks, return outputs
- **Tool Availability:** Each agent can have specific tools/capabilities
- **Hierarchical Spawning:** Agent can spawn sub-agents for complex tasks
- **Information Flow:** Output of one agent becomes input to another
- **Memory:** Agents can recall context from previous work

**How It Applies:**
Your current agents will become first level in hierarchy. Specialized subagents spawn from orchestrator for specific needs.

### Source 2: AutoGen Multi-Agent Conversation Framework Paper
**URL:** `https://arxiv.org/abs/2308.08155`

**Key Concepts:**
- **Agent Conversation:** Agents communicate with each other, not just sequentially
- **Debate/Consensus:** Multiple agents analyze problem, present their perspectives
- **Hierarchical Roles:** Senior agents direct junior agents
- **Task Decomposition:** Complex tasks split across multiple agents
- **Human in Loop:** Humans review agent conclusions before proceeding

**How It Applies:**
Your orchestrator can collect analyses from multiple subagents, synthesize, present to user for approval.

---

## 3. CURRENT 4-AGENT PIPELINE ASSESSMENT

### Current Architecture

```
Planner Agent
    ↓ (creates plan)
Verifier Agent
    ↓ (checks logic)
Executor Agent
    ↓ (executes steps)
Generator Agent
    ↓ (generates output/learning)
```

**What Each Does:**
- **Planner:** Takes goal, generates planning steps
- **Verifier:** Checks planner's logic, identifies gaps
- **Executor:** Simulates execution, identifies blockers
- **Generator:** Creates output documents, extracts learning

### Current Limitations

1. **Fixed Sequence:** Always runs in same order; can't skip irrelevant agents
2. **General Purpose:** Each agent tries to do multiple things (Planner = goal analysis + step generation)
3. **Hard to Add Analysis:** Want domain analysis? Modify Planner. Want risk analysis? Modify Executor.
4. **No Parallelization:** Must wait for Planner before Verifier starts
5. **No Specialization:** No agent expert in specific domain (healthcare, finance, etc.)

### What Will Be Preserved

- ✅ All four agents still exist, but as coordinators
- ✅ Planning pipeline produces equivalent outputs
- ✅ User approval gates remain
- ✅ All learning still captured

---

## 4. TARGET HIERARCHICAL ARCHITECTURE

### New Agent System

```
┌─────────────────────────────────────┐
│   ORCHESTRATOR                      │
│   (Routes tasks to appropriate      │
│    agent teams based on goal)       │
└────┬────────────────────────────────┘
     │
     ├─→ PRIMARY PIPELINE
     │   ├─ Planner Agent (updated for hierarchy)
     │   ├─ Verifier Agent
     │   ├─ Executor Agent
     │   └─ Generator Agent
     │
     └─→ SPAWNS SUBAGENTS AS NEEDED
         ├─ Domain Analyzer (analyzes market, industry, context)
         ├─ Risk Assessor (identifies risks and quantifies)
         ├─ Opportunity Finder (surfaces advantages, opportunities)
         ├─ Hypothesis Generator (creates hypotheses, tests them)
         ├─ Frameworks Discoverer (finds applicable frameworks, patterns)
         └─ Implications Analyzer (works out consequences, dependencies)
```

### Agent Hierarchy Levels

**Level 1: Coordinators (Current Agents, Enhanced)**
- Planner: Now routes to subagents, synthesizes analyses
- Verifier: Checks not just logic, but risk assessments, opportunity coverage
- Executor: Incorporates risk and implication analyses
- Generator: Incorporates learnings from all subagents

**Level 2: Specialists (New Subagents)**
- Domain Analyzer: Expert in domain-specific context
- Risk Assessor: Expert in identifying, quantifying risks
- Opportunity Finder: Expert in finding advantages
- Hypothesis Generator: Expert in creating testable hypotheses
- Frameworks Discoverer: Expert in pattern/framework matching
- Implications Analyzer: Expert in consequence analysis

### Communication Pattern

```
Orchestrator decides:
  "This is a healthcare market entry problem"
  "Complexity: High"
  "Required analyses: Domain, Risk, Opportunity, Frameworks"

Spawns subagents:
  Domain Analyzer: Analyzes healthcare regulations, timelines, stakeholders
  Risk Assessor: Identifies regulatory, competitive, financial risks
  Opportunity Finder: Surfaces healthcare-specific advantages
  Frameworks Discoverer: Finds applicable healthcare frameworks

Subagents return:
  [Domain Analysis] + [Risk Assessment] + [Opportunities] + [Frameworks]

Planner uses all analyses:
  Creates plan that accounts for domain context, risks, opportunities, frameworks

Verifier validates:
  All subagent analyses incorporated? ✓
  Risks addressed in plan? ✓
  Opportunities leveraged? ✓

Executor simulates:
  Using domain analysis + risk/opportunity insights

Generator outputs:
  Comprehensive plan + learning from all subagents
```

---

## 5. SIX SUBAGENT TYPES (Detailed)

### Subagent 1: Domain Analyzer

**Purpose:** Understand domain-specific context, regulations, timelines, stakeholders

**What It Analyzes:**
- Domain-specific regulations and compliance requirements
- Industry-specific timelines and best practices
- Key stakeholders and decision-makers
- Domain-specific risks and opportunities
- Cultural and contextual factors

**Input:**
- Goal (e.g., "Market entry into Japanese healthcare")
- Domain classification (healthcare, finance, manufacturing, etc.)
- Memory access: shared frameworks for domain

**Output:**
```json
{
  "domain_analysis": {
    "domain": "healthcare",
    "regulatory_requirements": ["FDA approval", "Clinical trials"],
    "typical_timeline": "18-24 months",
    "key_stakeholders": ["Hospital Networks", "Regulatory Bodies"],
    "cultural_factors": ["Risk-averse in medical", "High liability concerns"],
    "confidence": 0.88
  }
}
```

### Subagent 2: Risk Assessor

**Purpose:** Identify, categorize, and quantify risks

**What It Analyzes:**
- Strategic risks (market, competitive)
- Operational risks (execution, resources)
- Financial risks (capital, ROI)
- Regulatory risks (compliance, approval)
- Organizational risks (capability gaps)

**Input:**
- Goal
- Domain context
- Memory access: patterns of past risk assessments

**Output:**
```json
{
  "risk_assessment": {
    "top_risks": [
      {
        "risk": "Regulatory approval delays",
        "probability": 0.6,
        "impact": "high",
        "mitigation": "Early regulatory engagement"
      },
      {
        "risk": "Competitive response",
        "probability": 0.8,
        "impact": "medium",
        "mitigation": "Differentiated positioning"
      }
    ],
    "overall_risk_score": 6.5,
    "confidence": 0.82
  }
}
```

### Subagent 3: Opportunity Finder

**Purpose:** Surface opportunities, advantages, unique positioning

**What It Analyzes:**
- Market gaps and unmet needs
- Competitive advantages available
- Timing opportunities
- Partnership opportunities
- Technology/capability advantages

**Input:**
- Goal
- Domain context
- Risk assessment (to find risk-adjusted opportunities)
- Memory access: patterns of successful strategies

**Output:**
```json
{
  "opportunities": {
    "market_gaps": [
      "Rural healthcare access gap",
      "Preventive care underserved"
    ],
    "competitive_advantages": [
      "Superior mobile technology",
      "Price 30% lower than competitors"
    ],
    "timing_opportunities": [
      "Government digital health initiative launching Q2",
      "Competitor distracted by EU expansion"
    ],
    "partnership_opportunities": [
      "Local hospital network seeking digital solution"
    ],
    "confidence": 0.75
  }
}
```

### Subagent 4: Hypothesis Generator

**Purpose:** Create and test hypotheses about what will work

**What It Analyzes:**
- Hypothesis formulation (what success looks like)
- Hypothesis testing (what evidence would confirm/disprove)
- Alternative hypotheses
- Critical assumptions

**Input:**
- Goal
- Domain analysis
- Risk assessment
- Opportunities
- Memory access: past hypotheses and test results

**Output:**
```json
{
  "hypotheses": [
    {
      "hypothesis": "Rural healthcare market will adopt solution within 18 months",
      "assumptions": ["Price sensitivity", "Mobile first preference"],
      "test_plan": "Run pilot in 3 districts, measure adoption",
      "evidence_needed": ["X% pilot adoption", "Y% retention after 3 months"],
      "confidence": 0.72
    }
  ]
}
```

### Subagent 5: Frameworks Discoverer

**Purpose:** Identify applicable frameworks, patterns, proven strategies

**What It Analyzes:**
- Domain-specific frameworks (healthcare regulations, finance compliance)
- Market entry frameworks (timing, sequencing, stakeholder engagement)
- Successful patterns from history (what worked before in similar situations)
- Applicable templates

**Input:**
- Goal
- Domain context
- Memory access: shared frameworks + successful patterns

**Output:**
```json
{
  "frameworks": {
    "applicable_frameworks": [
      {
        "name": "Healthcare Market Entry Framework",
        "source": "shared",
        "key_phases": ["Regulatory", "Clinical validation", "Market launch"],
        "estimated_timeline": "18-24 months",
        "confidence": 0.85
      }
    ],
    "patterns_that_worked": [
      "Early regulatory engagement with health ministry",
      "Pilot with leading hospital chain",
      "Training before rollout"
    ]
  }
}
```

### Subagent 6: Implications Analyzer

**Purpose:** Work out consequences, dependencies, and dependencies

**What It Analyzes:**
- Consequence chains (if A then B then C)
- Dependencies (what must happen before what)
- Resource implications
- Timeline implications
- Organizational capability implications

**Input:**
- Goal
- All previous analyses
- Memory access: past plans and their execution outcomes

**Output:**
```json
{
  "implications": {
    "consequence_chains": [
      "Regulatory approval → Clinical trials → Market readiness → Launch timing"
    ],
    "dependencies": [
      "Clinical trials depend on regulatory approval",
      "Market launch depends on trials completion"
    ],
    "resource_implications": {
      "capital": "$5-10M",
      "team": "15-20 people",
      "timeline": "24 months"
    },
    "capability_gaps": [
      "Healthcare regulatory expertise",
      "Clinical trial management"
    ]
  }
}
```

---

## 6. IMPLEMENTATION PLAN

### PHASE 1: Base Agent Class Hierarchy (2 hours)

#### Step 1.1: Define Agent Interface

```python
# orchestrator/domain/entities/agent.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AgentTask:
    """Task given to agent"""
    task_id: str
    goal: str
    domain: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    required_analyses: Optional[List[str]] = None  # Which subagents to spawn

@dataclass
class AgentAnalysis:
    """Output from agent"""
    agent_type: str
    task_id: str
    analysis: Dict[str, Any]
    confidence: float
    created_at: datetime

class Agent(ABC):
    """Base agent class - all agents inherit from this"""

    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.memory_access = None  # Injected

    @abstractmethod
    def execute(self, task: AgentTask) -> AgentAnalysis:
        """Execute task and return analysis"""
        pass

    @abstractmethod
    def can_handle(self, domain: str) -> bool:
        """Check if this agent can handle domain"""
        pass

    def get_confidence(self) -> float:
        """Get agent's overall confidence score"""
        # Overridden in subclasses
        return 0.75

    def spawn_subagent(
        self,
        subagent_type: str,
        task: AgentTask
    ) -> AgentAnalysis:
        """Request orchestrator to spawn subagent"""
        # This goes back to orchestrator for spawning
        pass
```

#### Step 1.2: Update Existing Agents to Use Base Class

```python
# orchestrator/agents/planner_agent.py

from orchestrator.domain.entities.agent import Agent, AgentTask, AgentAnalysis

class PlannerAgent(Agent):
    """Updated Planner - now uses subagent analyses"""

    def __init__(self):
        super().__init__(agent_type='planner')
        self.domain_analyzer = None  # Will be injected by orchestrator
        self.risk_assessor = None
        self.opportunity_finder = None
        self.frameworks_discoverer = None

    def execute(self, task: AgentTask) -> AgentAnalysis:
        """
        Create plan using subagent analyses
        """

        # Request subagent analyses
        domain_analysis = self.domain_analyzer.execute(task)
        risk_analysis = self.risk_assessor.execute(task)
        opportunities = self.opportunity_finder.execute(task)
        frameworks = self.frameworks_discoverer.execute(task)

        # Synthesize into plan
        plan = self._synthesize_plan(
            domain_analysis=domain_analysis,
            risk_analysis=risk_analysis,
            opportunities=opportunities,
            frameworks=frameworks
        )

        return AgentAnalysis(
            agent_type='planner',
            task_id=task.task_id,
            analysis=plan,
            confidence=0.82,
            created_at=datetime.now()
        )

    def _synthesize_plan(self, **analyses) -> Dict[str, Any]:
        """Create plan incorporating all analyses"""
        # Logic that creates plan steps
        # Uses domain context, addresses risks, leverages opportunities,
        # follows frameworks
        pass

    def can_handle(self, domain: str) -> bool:
        return True  # Planner can handle any domain
```

---

### PHASE 2: Implement 6 Subagent Types (3 hours)

#### Step 2.1: Domain Analyzer Subagent

```python
# orchestrator/agents/domain_analyzer_subagent.py

from orchestrator.domain.entities.agent import Agent, AgentTask, AgentAnalysis
from datetime import datetime
from typing import Dict, Any

class DomainAnalyzerSubagent(Agent):
    """Analyzes domain-specific context"""

    def __init__(self, memory_service):
        super().__init__(agent_type='domain_analyzer')
        self.memory_service = memory_service
        self.domain_expertise = {
            'healthcare': self._analyze_healthcare,
            'finance': self._analyze_finance,
            'manufacturing': self._analyze_manufacturing,
            # Can add more domains
        }

    def execute(self, task: AgentTask) -> AgentAnalysis:
        """Analyze domain-specific context"""

        domain = task.domain or self._detect_domain(task.goal)

        if domain in self.domain_expertise:
            analysis = self.domain_expertise[domain](task)
        else:
            analysis = self._analyze_generic_domain(task, domain)

        return AgentAnalysis(
            agent_type='domain_analyzer',
            task_id=task.task_id,
            analysis=analysis,
            confidence=self._calculate_confidence(domain),
            created_at=datetime.now()
        )

    def _analyze_healthcare(self, task: AgentTask) -> Dict[str, Any]:
        """Healthcare-specific analysis"""

        # Search for healthcare frameworks in memory
        frameworks = self.memory_service.search_memory(
            query="healthcare regulations frameworks",
            scope_type='shared'
        )

        return {
            'domain': 'healthcare',
            'regulatory_bodies': ['FDA', 'Health Ministry'],
            'approval_timeline_months': 18,
            'key_stakeholders': ['Hospital networks', 'Clinicians', 'Patients'],
            'frameworks_found': len(frameworks),
            'notes': 'Healthcare highly regulated, slow approval cycle'
        }

    def _analyze_finance(self, task: AgentTask) -> Dict[str, Any]:
        """Finance-specific analysis"""
        # Similar pattern for finance
        pass

    def _analyze_manufacturing(self, task: AgentTask) -> Dict[str, Any]:
        """Manufacturing-specific analysis"""
        # Similar pattern for manufacturing
        pass

    def _analyze_generic_domain(
        self,
        task: AgentTask,
        domain: str
    ) -> Dict[str, Any]:
        """Generic domain analysis for unknown domains"""

        frameworks = self.memory_service.search_memory(
            query=f"{domain} domain analysis",
            scope_type='both'
        )

        return {
            'domain': domain,
            'frameworks_found': len(frameworks),
            'confidence': 'moderate',
            'notes': f'Generic analysis for {domain}'
        }

    def _detect_domain(self, goal: str) -> str:
        """Detect domain from goal"""
        # Simple domain detection
        if 'healthcare' in goal.lower():
            return 'healthcare'
        elif 'finance' in goal.lower():
            return 'finance'
        return 'generic'

    def _calculate_confidence(self, domain: str) -> float:
        """Confidence depends on domain expertise"""
        if domain in self.domain_expertise:
            return 0.85  # High confidence for known domains
        return 0.60  # Lower confidence for unknown

    def can_handle(self, domain: str) -> bool:
        return True  # Domain analyzer can handle any domain
```

#### Step 2.2-2.6: Other Subagents (Similar Pattern)

```python
# orchestrator/agents/risk_assessor_subagent.py
class RiskAssessorSubagent(Agent):
    """Identifies and quantifies risks"""
    # Similar structure

# orchestrator/agents/opportunity_finder_subagent.py
class OpportunityFinderSubagent(Agent):
    """Finds opportunities and advantages"""
    # Similar structure

# orchestrator/agents/hypothesis_generator_subagent.py
class HypothesisGeneratorSubagent(Agent):
    """Generates and tests hypotheses"""
    # Similar structure

# orchestrator/agents/frameworks_discoverer_subagent.py
class FrameworksDiscovererSubagent(Agent):
    """Finds applicable frameworks and patterns"""
    # Similar structure

# orchestrator/agents/implications_analyzer_subagent.py
class ImplicationsAnalyzerSubagent(Agent):
    """Works out consequences and dependencies"""
    # Similar structure
```

---

### PHASE 3: Update Orchestrator for Hierarchical Agent System (3 hours)

#### Step 3.1: Agent Factory & Registry

```python
# orchestrator/application/services/agent_factory.py

from typing import Dict, Type
from orchestrator.domain.entities.agent import Agent
from orchestrator.agents import (
    PlannerAgent,
    VerifierAgent,
    ExecutorAgent,
    GeneratorAgent,
    DomainAnalyzerSubagent,
    RiskAssessorSubagent,
    OpportunityFinderSubagent,
    HypothesisGeneratorSubagent,
    FrameworksDiscovererSubagent,
    ImplicationsAnalyzerSubagent
)

class AgentFactory:
    """Factory for creating agents"""

    def __init__(self, dependencies):
        self.dependencies = dependencies

        # Agent registry
        self.agent_classes: Dict[str, Type[Agent]] = {
            'planner': PlannerAgent,
            'verifier': VerifierAgent,
            'executor': ExecutorAgent,
            'generator': GeneratorAgent,
            # Subagents
            'domain_analyzer': DomainAnalyzerSubagent,
            'risk_assessor': RiskAssessorSubagent,
            'opportunity_finder': OpportunityFinderSubagent,
            'hypothesis_generator': HypothesisGeneratorSubagent,
            'frameworks_discoverer': FrameworksDiscovererSubagent,
            'implications_analyzer': ImplicationsAnalyzerSubagent,
        }

    def create_agent(self, agent_type: str) -> Agent:
        """Create and return agent instance"""

        if agent_type not in self.agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")

        agent_class = self.agent_classes[agent_type]
        agent = agent_class(self.dependencies.get(agent_type))
        return agent

    def register_agent(self, agent_type: str, agent_class: Type[Agent]) -> None:
        """Register new agent type (for extensibility)"""
        self.agent_classes[agent_type] = agent_class
```

#### Step 3.2: Updated Orchestrator with Agent Spawning

```python
# orchestrator/application/services/hierarchical_orchestrator.py

from typing import Dict, List
from orchestrator.domain.entities.agent import AgentTask, AgentAnalysis
from orchestrator.application.services.agent_factory import AgentFactory

class HierarchicalOrchestrator:
    """Orchestrator for hierarchical agent system"""

    def __init__(self, agent_factory: AgentFactory):
        self.agent_factory = agent_factory
        self.primary_agents = {
            'planner': self.agent_factory.create_agent('planner'),
            'verifier': self.agent_factory.create_agent('verifier'),
            'executor': self.agent_factory.create_agent('executor'),
            'generator': self.agent_factory.create_agent('generator'),
        }
        self.subagents = {}  # Dynamically spawned

    def execute_planning(self, goal: str, domain: str = None) -> Dict:
        """Execute planning with hierarchical agent system"""

        # Create task
        task = AgentTask(
            task_id=generate_task_id(),
            goal=goal,
            domain=domain,
            context={},
            required_analyses=[
                'domain_analyzer',
                'risk_assessor',
                'opportunity_finder',
                'frameworks_discoverer'
            ]
        )

        # Planner may request subagents
        # This happens within PlannerAgent.execute()
        # Planner has references to subagent factories

        # Execute primary pipeline
        planner_output = self.primary_agents['planner'].execute(task)
        verifier_output = self.primary_agents['verifier'].execute(task)
        executor_output = self.primary_agents['executor'].execute(task)
        generator_output = self.primary_agents['generator'].execute(task)

        return {
            'planning': planner_output.analysis,
            'verification': verifier_output.analysis,
            'execution': executor_output.analysis,
            'output': generator_output.analysis,
        }

    def spawn_subagent(self, subagent_type: str) -> Agent:
        """Spawn subagent on demand"""

        if subagent_type not in self.subagents:
            self.subagents[subagent_type] = self.agent_factory.create_agent(
                subagent_type
            )

        return self.subagents[subagent_type]
```

---

### PHASE 4: Update API & Integration (1 hour)

#### Step 4.1: Update Planning Route

```python
# orchestrator/interfaces/api/routes/planning_routes.py

from orchestrator.application.services.hierarchical_orchestrator import HierarchicalOrchestrator

def create_planning_routes(orchestrator: HierarchicalOrchestrator):
    """Routes using hierarchical orchestrator"""

    bp = Blueprint('planning', __name__, url_prefix='/api/plans')

    @bp.route('', methods=['POST'])
    def create_plan():
        data = request.json
        goal = data['goal']
        domain = data.get('domain')  # Optional domain hint

        result = orchestrator.execute_planning(goal, domain)

        return jsonify({
            'plan': result['planning'],
            'verification': result['verification'],
            'execution_simulation': result['execution'],
            'final_output': result['output']
        }), 201

    return bp
```

---

## 7. INTEGRATION VERIFICATION

### Verification Checklist

#### 1. Agent Hierarchy Created
```bash
# Verify all agent classes exist
ls -la orchestrator/agents/*subagent.py
# Should show 6 files

# Verify inheritance
grep -r "class.*Subagent(Agent)" orchestrator/agents/
# Should show 6 matches
```

#### 2. Subagents Spawn Successfully
```python
def test_subagent_spawning():
    """Test orchestrator can spawn subagents"""

    orchestrator = HierarchicalOrchestrator(agent_factory)

    # Spawn each type
    for subagent_type in [
        'domain_analyzer',
        'risk_assessor',
        'opportunity_finder',
        'hypothesis_generator',
        'frameworks_discoverer',
        'implications_analyzer'
    ]:
        subagent = orchestrator.spawn_subagent(subagent_type)
        assert subagent is not None
        assert subagent.agent_type == subagent_type
```

#### 3. Planning Output Quality
```python
def test_planning_with_subagents():
    """Test planning output incorporates subagent analyses"""

    result = orchestrator.execute_planning(
        goal="Market entry into Japanese healthcare",
        domain="healthcare"
    )

    # Verify all analyses included
    assert 'domain_analysis' in str(result['planning'])
    assert 'risk' in str(result['planning'])
    assert 'opportunity' in str(result['planning'])
```

#### 4. Backward Compatibility
```bash
# Run existing tests - all should still pass
pytest tests/e2e/test_planning_iteration.py -v
# Should show: PASSED

# Run on existing plans - should work identically
# No behavior changes, just new agent structure
```

---

## 8. RISK/ISSUE SECTIONS

### Risk 1: Circular Subagent Dependencies

**Problem:** Subagent A calls Subagent B, B calls A → infinite loop

**Prevention:**
- No subagent should spawn other subagents
- Only orchestrator spawns subagents
- Subagents get results from other subagents, not spawn them

**Detection:**
```bash
# Check for spawn calls in subagents
grep -r "spawn_subagent" orchestrator/agents/*subagent.py
# Should return 0 results (no spawning in subagents)
```

---

### Risk 2: Subagent Creates Low-Quality Analysis

**Problem:** A subagent gives bad analysis that breaks planning

**Mitigation:**
- Verifier agent checks all analyses
- Tests validate output quality
- Confidence scores track uncertainty

**Solution:**
```python
# Check confidence scores
if subagent_output.confidence < 0.6:
    # Log warning, consider this analysis unreliable
    logger.warning(f"Low confidence from {subagent_type}: {confidence}")
```

---

### Risk 3: Memory Access Failures in Subagents

**Problem:** Subagent tries to search memory, memory service unavailable

**Prevention:**
- Mock memory service in tests
- Graceful fallback if search fails
- Return empty results rather than crash

**Code:**
```python
def _analyze_with_memory(self, query: str):
    try:
        results = self.memory_service.search_memory(query, scope_type='shared')
        return results
    except Exception as e:
        logger.warning(f"Memory search failed: {e}")
        return []  # Graceful fallback
```

---

## 9. DECISION TREES

### Decision 1: Should I Create a New Subagent Type?

```
"I have a specialized analysis need. Should I create new subagent?"

IF analysis fits existing 6 types:
  → Extend that subagent (add method)
  → Example: Add "competitor analysis" to Opportunity Finder

ELSE IF analysis is fundamentally different from existing types:
  → Create new subagent type
  → Register with AgentFactory
  → Example: "Capability Gap Analyzer"

ELSE IF analysis is one-off/temporary:
  → Don't create subagent, add logic to orchestrator
  → Example: Temporary workaround for Q4 planning
```

---

### Decision 2: How to Handle Subagent Disagreement?

```
"Two subagents disagree (one says high risk, one says opportunity). What do I do?"

IF disagreement is about the same analysis:
  → Verifier agent resolves
  → Return both perspectives to user

ELSE IF disagreement is valid (different lenses):
  → Present both to user
  → Let user decide

ELSE IF one subagent is clearly wrong:
  → Adjust subagent logic
  → Retrain/recalibrate
  → Flag for review
```

---

## 10. TESTING STRATEGY

### Unit Tests

```python
# tests/unit/agents/test_domain_analyzer_subagent.py

def test_domain_analyzer_healthcare():
    """Domain analyzer correctly analyzes healthcare domain"""

    subagent = DomainAnalyzerSubagent(mock_memory_service)
    task = AgentTask(goal="Healthcare market entry", domain="healthcare")

    analysis = subagent.execute(task)

    assert analysis.agent_type == 'domain_analyzer'
    assert 'healthcare' in str(analysis.analysis).lower()
    assert analysis.confidence > 0.7

def test_domain_analyzer_unknown_domain():
    """Domain analyzer handles unknown domains gracefully"""

    subagent = DomainAnalyzerSubagent(mock_memory_service)
    task = AgentTask(goal="Unknown domain task", domain="unknown_domain")

    analysis = subagent.execute(task)

    assert analysis.agent_type == 'domain_analyzer'
    # Confidence lower for unknown domain
    assert analysis.confidence < 0.75
```

### Integration Tests

```python
# tests/integration/test_hierarchical_orchestrator.py

def test_orchestrator_spawns_subagents():
    """Orchestrator correctly spawns subagents"""

    orchestrator = HierarchicalOrchestrator(agent_factory)

    result = orchestrator.execute_planning(
        goal="Healthcare market entry",
        domain="healthcare"
    )

    # Should have analyses from multiple subagents
    assert 'planning' in result
    assert 'verification' in result
    # All required subagents should have contributed

def test_subagent_analyses_incorporated():
    """Planning output incorporates subagent analyses"""

    result = orchestrator.execute_planning(goal="Healthcare market entry")

    # Verify planning uses domain analysis
    planning_output = result['planning']
    assert len(planning_output.get('steps', [])) > 0
```

---

## 11. COMPLETION CHECKLIST

- [ ] Agent base class defined
- [ ] 4 main agents updated to use base class
- [ ] 6 subagent types implemented
- [ ] Agent factory created and tested
- [ ] Hierarchical orchestrator created
- [ ] Subagent spawning works
- [ ] Planning output quality equals current system
- [ ] All tests passing (100%)
- [ ] No behavioral regressions
- [ ] Documentation updated

---

## NEXT STEPS

After completing DEVELOPMENT_CYCLE_3:
1. Verify all subagents spawn correctly
2. Confirm planning output quality
3. Validate integration with memory and cleanup
4. Mark Goal 3 as COMPLETE
5. Move to DEVELOPMENT_CYCLE_4 (Enhanced Chat)

**Estimated Timeline:** ~1 day

---

**Document Status:** Complete & Ready for Execution
**Last Updated:** November 14, 2025
**Next Document:** DEVELOPMENT_CYCLE_4_ENHANCED_CHAT.md
