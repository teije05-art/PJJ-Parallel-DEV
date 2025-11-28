# DETAILED PHASE 2 STEP 1: Six Agents Refactor & Implementation

## STEP 1 OVERVIEW

**Goal**: Create 6 specialized agents that handle Steps 1-6 of the tax workflow

**Duration**: Days 1-4 (Implementation), Days 5-6 (Integration)
**Scope**: 6 agent files, each 150-200 lines
**Location**: `orchestrator/tax_workflow/`
**Output**: Working agents that communicate via AgentResult contract

---

## PART 1: AGENT FOUNDATION & ARCHITECTURE

### 1.1 BaseAgent Pattern (Reference)

All tax agents inherit from existing BaseAgent:

```python
# orchestrator/agents/base_agent.py (EXISTING - DO NOT MODIFY)

from dataclasses import dataclass
from typing import Any, Dict
from agent import Agent
from pathlib import Path
from datetime import datetime

@dataclass
class AgentResult:
    """Standard result format for ALL agents"""
    success: bool
    output: Any
    metadata: Dict[str, Any]
    timestamp: str
    error: str = ""
    deliverables: Any = None


class BaseAgent:
    """Base class for all agents"""

    def __init__(self, agent: Agent, memory_path: Path):
        self.agent = agent
        self.memory_path = memory_path

    def generate(self, prompt: str) -> AgentResult:
        """
        Each agent must implement this.
        Must return AgentResult with exact contract.
        """
        raise NotImplementedError("Subclass must implement generate()")
```

### 1.2 Tax Agent Pattern (Template)

All 6 tax agents follow this pattern:

```python
# orchestrator/tax_workflow/tax_example_agent.py

import sys
from pathlib import Path
from datetime import datetime
from typing import Any, List, Dict

# Setup path for imports
REPO_ROOT = Path(__file__).parent.parent.parent  # Goes up 3 levels
sys.path.insert(0, str(REPO_ROOT))

from agent import Agent
from orchestrator.agents.base_agent import BaseAgent, AgentResult


class TaxExampleAgent(BaseAgent):
    """
    Example agent template.

    Input: {...}
    Output: {...}
    Purpose: Description
    """

    def __init__(self, agent: Agent, memory_path: Path):
        super().__init__(agent, memory_path)
        self.agent = agent

    def generate(self, **kwargs) -> AgentResult:
        """
        Main processing method.

        Returns: AgentResult with exact contract
        """
        try:
            # Process input
            # Generate output
            # Return AgentResult

            return AgentResult(
                success=True,
                output={...},  # Agent-specific output
                metadata={...},  # Agent-specific metadata
                timestamp=datetime.now().isoformat(),
                error=""
            )

        except Exception as e:
            return AgentResult(
                success=False,
                output=None,
                metadata={},
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )
```

### 1.3 AgentResult Contract (MUST MATCH EXACTLY)

Every agent returns AgentResult with these exact fields:

```python
@dataclass
class AgentResult:
    success: bool                    # True if processing succeeded
    output: Any                      # Agent-specific output (see agent specs below)
    metadata: Dict[str, Any]         # Agent-specific metadata
    timestamp: str                   # ISO 8601 timestamp
    error: str = ""                  # Error message if failed
    deliverables: Any = None         # Optional extra data
```

---

## PART 1A: MEMAGENT CONSTRAINT BOUNDARIES (CRITICAL PATTERN)

### Constraint Pattern (Applies to ALL Agents)

Based on `User_Constrained_memagent.md` and `truncated_duplicate_memagent.md`:

**Core Principle**: NO autonomous memory scouring. All MemAgent searches must be bounded by user-selected categories (from RequestCategorizer output). If no categories selected, agents must fail gracefully (return empty, don't search broadly).

**Pattern for All Search-Based Agents**:

```python
# CONSTRAINT BOUNDARIES - Add to every agent that searches MemAgent
"""
CONSTRAINT BOUNDARIES:
- Search Scope: ONLY segments [X, Y, Z] (explicitly listed)
- Filter: ONLY by confirmed_categories (user boundary)
- Fallback: If categories empty, return empty results (don't search broadly)
- No Autonomy: Agent cannot search beyond specified segments
"""

def generate(self, request: str, categories: List[str], **kwargs) -> AgentResult:
    # VALIDATION: Check that constraints are present
    if not categories or len(categories) == 0:
        return AgentResult(
            success=False,
            output=[],
            metadata={"error_type": "constraint_violation"},
            timestamp=datetime.now().isoformat(),
            error="Search requires category constraints (user boundary not set)"
        )

    # Build constrained query with explicit CONSTRAINT comment
    query = f"""CONSTRAINT: Analyze ONLY within these user-selected categories:
{', '.join(categories)}

Do NOT search beyond these specified categories.
Search for: {request}"""

    # Search with explicit segment list (prevents autonomous scouring)
    results = self.segmented_memory.search(
        query=query,
        segments=self.ALLOWED_SEGMENTS,  # [X, Y, Z] - EXPLICIT
        search_type="semantic",
        top_k=self.MAX_RESULTS
    )

    # Validate results respect constraints
    filtered = [r for r in results if r.get("category") in categories]

    return AgentResult(
        success=True,
        output=filtered,
        metadata={
            "constraint_boundary": categories,
            "segments_searched": self.ALLOWED_SEGMENTS,
            "results_filtered": len(results) - len(filtered)
        },
        timestamp=datetime.now().isoformat(),
        error=""
    )
```

**Memory Configuration for Tax Workflow**:

**Memory Path** (CRITICAL):
```python
# All agents initialized with tax_legal namespace
memory_path = Path("local-memory/tax_legal")

# Example: RequestCategorizer initialization
agent = RequestCategorizer(
    agent=llama_client,
    memory_path=Path("local-memory/tax_legal")  # ← Isolated namespace
)
```

**Segment Allocation for Tax Workflow**:
- **Segments [0, 1, 2, 3]**: Past responses (read from: `local-memory/tax_legal/entities/`)
- **Segments [4-11]**: Tax database documents (read from: `local-memory/tax_legal/tax_database/`)
- **All 12 segments**: Dedicated to tax/legal workflow only
- **Isolation**: NO access to `local-memory/PJJ-old/` (Project Jupiter data)

**Single Source of Truth for Saving**:
- Only save point: `orchestrator.memory_manager.store_results()` in TaxOrchestrator
- Never save from individual agents
- Never save from multiple locations (causes truncation like old system)

---

## PART 2: AGENT 1 - REQUEST CATEGORIZER

### 2.1 Agent Specification

**Name**: `RequestCategorizer` (was: ProposalAgent)
**File**: `orchestrator/tax_workflow/tax_planner_agent.py`
**Lines of Code**: ~150-180

**Role**: Parse client request, identify tax domains (Step 1)

**Input**:
```python
request: str  # e.g., "Pharmaceutical distributor in Vietnam with Singapore parent..."
```

**Processing**:
- Read request text
- Identify keywords: "pharmaceutical", "distributor", "Singapore", "transfer pricing"
- Map to tax categories: ["CIT", "Transfer Pricing", "VAT"]
- Calculate confidence score

**Output**:
```python
AgentResult(
    success=True,
    output={
        "suggested_categories": ["CIT", "Transfer Pricing", "VAT"],
        "reasoning": "Request mentions...",
        "confidence": 0.92
    },
    metadata={
        "keywords_found": ["pharmaceutical", "distributor", "singapore", "transfer pricing"],
        "llama_prompt_tokens": 45,
        "llama_response_tokens": 120,
        "processing_time_ms": 234
    },
    timestamp="2025-11-25T14:32:15.123456Z",
    error=""
)
```

**Error Handling**:
- If request is empty → error: "Request cannot be empty"
- If request too short (<10 chars) → error: "Request too short, need more detail"
- If Llama call fails → error: "LLM error: ..."

### 2.2 Code Skeleton

```python
# orchestrator/tax_workflow/tax_planner_agent.py

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent import Agent
from orchestrator.agents.base_agent import BaseAgent, AgentResult


class RequestCategorizer(BaseAgent):
    """
    Step 1: Parse client request and suggest tax categories

    Maps business situations to tax domains:
    - CIT (Corporate Income Tax)
    - VAT (Value Added Tax)
    - Transfer Pricing
    - PIT (Personal Income Tax)
    - FCT (Foreign Contractor Tax)
    - etc.

    CONSTRAINT BOUNDARIES:
    - Search Scope: NO MemAgent search (classification only)
    - Output: Suggested categories that become user boundary for downstream agents
    - Critical: Categories suggested here MUST be confirmed by user before use
    - Fallback: If no categories detected, return empty with explanation
    - No Autonomy: This agent initiates the constraint boundary, doesn't search within it
    """

    # Valid tax categories
    VALID_CATEGORIES = [
        "CIT",
        "VAT",
        "Transfer Pricing",
        "PIT",
        "FCT",
        "DTA",
        "Customs",
        "Excise Tax",
        "Environmental Tax",
        "Capital Gains"
    ]

    # Keywords → categories mapping (for quick detection)
    KEYWORD_MAPPING = {
        "transfer pricing": "Transfer Pricing",
        "intercompany": "Transfer Pricing",
        "arm's length": "Transfer Pricing",
        "vat": ["VAT"],
        "gst": ["VAT"],
        "input tax": ["VAT"],
        "cit": ["CIT"],
        "corporate income": ["CIT"],
        "dividend": ["CIT", "PIT"],
        "salary": ["PIT", "FCT"],
        "withholding": ["PIT", "FCT"],
        "transfer": ["Transfer Pricing"],
        "fta": ["Customs"],
        "import": ["Customs", "VAT"],
        "export": ["VAT", "Customs"],
        "foreigner": ["FCT"],
        "foreign contractor": ["FCT"],
    }

    def __init__(self, agent: Agent, memory_path: Path):
        super().__init__(agent, memory_path)
        self.agent = agent

    def generate(self, request: str) -> AgentResult:
        """
        Parse request and suggest categories.

        Args:
            request: Client request text (e.g., "Pharmaceutical distributor...")

        Returns:
            AgentResult with suggested_categories
        """
        try:
            # Validation
            if not request or len(request.strip()) == 0:
                raise ValueError("Request cannot be empty")

            if len(request.strip()) < 10:
                raise ValueError("Request too short, need more detail (minimum 10 chars)")

            # Quick keyword-based detection
            initial_categories = self._detect_from_keywords(request)

            # Llama-based classification for confidence & additional categories
            llama_categories = self._classify_with_llama(request)

            # Merge and rank by confidence
            suggested_categories = self._merge_categories(
                initial_categories,
                llama_categories
            )

            # Build confidence score
            confidence = self._calculate_confidence(request, suggested_categories)

            return AgentResult(
                success=True,
                output={
                    "suggested_categories": suggested_categories,
                    "reasoning": f"Request identified {len(suggested_categories)} relevant tax domains based on keywords and content analysis",
                    "confidence": confidence
                },
                metadata={
                    "keywords_found": self._extract_keywords(request),
                    "llama_model": "llama2-7b",
                    "llama_prompt_tokens": len(request.split()),  # Approximate
                    "processing_time_ms": 234,  # Placeholder
                    "initial_categories_count": len(initial_categories),
                    "final_categories_count": len(suggested_categories)
                },
                timestamp=datetime.now().isoformat(),
                error=""
            )

        except ValueError as e:
            return AgentResult(
                success=False,
                output=None,
                metadata={"error_type": "validation"},
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )

        except Exception as e:
            return AgentResult(
                success=False,
                output=None,
                metadata={"error_type": "processing"},
                timestamp=datetime.now().isoformat(),
                error=f"Categorization error: {str(e)}"
            )

    def _detect_from_keywords(self, request: str) -> List[str]:
        """Quick keyword-based detection"""
        request_lower = request.lower()
        categories = set()

        for keyword, cat in self.KEYWORD_MAPPING.items():
            if keyword in request_lower:
                if isinstance(cat, list):
                    categories.update(cat)
                else:
                    categories.add(cat)

        return list(categories)

    def _classify_with_llama(self, request: str) -> List[str]:
        """Use Llama to classify request"""
        prompt = f"""You are a Vietnamese tax expert. Analyze this client request and identify which tax domains are relevant.

Client Request:
{request}

Select ONLY from these valid categories:
{", ".join(self.VALID_CATEGORIES)}

Return ONLY a JSON list of category names, nothing else.
Example: ["CIT", "Transfer Pricing"]

Response:"""

        try:
            response = self.agent.generate_response(prompt)
            # Parse JSON from response
            categories = json.loads(response)
            # Validate categories
            return [c for c in categories if c in self.VALID_CATEGORIES]
        except:
            # If Llama classification fails, return empty (keyword detection used instead)
            return []

    def _merge_categories(self, keyword_cats: List[str], llama_cats: List[str]) -> List[str]:
        """Merge and deduplicate categories"""
        merged = set(keyword_cats) | set(llama_cats)
        return sorted(list(merged))

    def _extract_keywords(self, request: str) -> List[str]:
        """Extract detected keywords from request"""
        request_lower = request.lower()
        found = []
        for keyword in self.KEYWORD_MAPPING.keys():
            if keyword in request_lower:
                found.append(keyword)
        return found

    def _calculate_confidence(self, request: str, categories: List[str]) -> float:
        """
        Calculate confidence in suggestions.

        Simple heuristic:
        - More keywords found → higher confidence
        - Longer, more detailed request → higher confidence
        """
        keyword_count = len(self._extract_keywords(request))
        request_length = len(request.split())

        # Heuristic: normalize to [0, 1]
        confidence = min(0.95, 0.5 + (keyword_count * 0.1) + (min(request_length, 50) / 50) * 0.2)
        return round(confidence, 2)


# Unit Tests
if __name__ == "__main__":
    from agent import Agent
    from pathlib import Path

    # Create mock Agent for testing
    class MockAgent:
        def generate_response(self, prompt):
            return '["CIT", "Transfer Pricing"]'

    agent = MockAgent()
    memory_path = Path("./local-memory")

    categorizer = RequestCategorizer(agent, memory_path)

    # Test 1: Normal request
    result = categorizer.generate(
        "Pharmaceutical distributor in Vietnam with Singapore parent. Want to understand transfer pricing implications."
    )
    assert result.success, "Should succeed"
    assert len(result.output["suggested_categories"]) > 0, "Should suggest categories"
    print("✓ Test 1 passed: Normal request")

    # Test 2: Empty request
    result = categorizer.generate("")
    assert not result.success, "Should fail on empty request"
    print("✓ Test 2 passed: Empty request validation")

    # Test 3: Short request
    result = categorizer.generate("abc")
    assert not result.success, "Should fail on short request"
    print("✓ Test 3 passed: Short request validation")

    print("\n✓ All RequestCategorizer tests passed")
```

### 2.3 Example Outputs

**Example 1: Pharmaceutical + Transfer Pricing**

```python
Request: "Pharmaceutical distributor in Vietnam with Singapore parent.
           Want to understand transfer pricing implications."

Output:
{
    "suggested_categories": ["CIT", "Transfer Pricing", "VAT"],
    "reasoning": "Request identified 3 relevant tax domains based on keywords and content analysis",
    "confidence": 0.92
}
```

**Example 2: Simple VAT Question**

```python
Request: "Client imported equipment from Japan. What are VAT implications?"

Output:
{
    "suggested_categories": ["VAT", "Customs"],
    "reasoning": "Request identified 2 relevant tax domains based on keywords and content analysis",
    "confidence": 0.87
}
```

### 2.4 Integration Test

```python
def test_request_categorizer_integration():
    """Test RequestCategorizer with real setup"""
    from agent import Agent

    agent = Agent()  # Real MemAgent instance
    categorizer = RequestCategorizer(agent, Path("./local-memory"))

    # Real request
    result = categorizer.generate(
        "Our Vietnam subsidiary earned $2M transfer pricing income this year. "
        "We want to file corrective documentation for OECD comparability."
    )

    assert result.success
    assert "Transfer Pricing" in result.output["suggested_categories"]
    assert "CIT" in result.output["suggested_categories"]
    print(f"✓ Categorized: {result.output['suggested_categories']}")
```

---

## PART 3: AGENT 2 - TAX RESPONSE SEARCHER

### 3.1 Agent Specification

**Name**: `TaxResponseSearcher`
**File**: `orchestrator/tax_workflow/tax_searcher_agent.py`
**Lines of Code**: ~150-180

**Role**: Search past responses library for similar cases (Step 2)

**Input**:
```python
request: str             # e.g., "Pharmaceutical distributor..."
categories: List[str]    # e.g., ["CIT", "Transfer Pricing"]
segmented_memory: SegmentedMemory  # MemAgent instance
```

**Processing**:
- Use MemAgent to search past_responses segment
- Semantic similarity matching
- Rank by relevance
- Return top-5 past responses

**Output**:
```python
AgentResult(
    success=True,
    output=[
        {
            "filename": "past_response_001_pharma_tp.md",
            "similarity_score": 0.92,
            "summary": "Transfer pricing documentation for pharmaceutical distributor...",
            "categories": ["CIT", "Transfer Pricing"],
            "date_created": "2025-10-15",
            "client_type": "Pharmaceutical"
        },
        ...
    ],
    metadata={
        "total_found": 5,
        "search_time_ms": 342,
        "search_scope": "past_responses",
        "filter_applied": "categories match"
    },
    timestamp="2025-11-25T14:32:45.654321Z",
    error=""
)
```

### 3.2 Code Skeleton

```python
# orchestrator/tax_workflow/tax_searcher_agent.py

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import time

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent import Agent
from orchestrator.agents.base_agent import BaseAgent, AgentResult
from orchestrator.memory.memagent_memory import SegmentedMemory


class TaxResponseSearcher(BaseAgent):
    """
    Step 2: Search past responses for similar cases

    Uses MemAgent semantic search to find previous tax advice
    that matches the current request.

    CONSTRAINT BOUNDARIES:
    - Search Scope: ONLY segments [0, 1, 2, 3] (explicitly defined below)
    - Filter: ONLY past responses matching confirmed_categories from user
    - Fallback: If categories empty, return empty (no autonomous search)
    - No Autonomy: Cannot search beyond segments [0-3], cannot search without categories
    """

    # MemAgent segments that contain past responses
    PAST_RESPONSE_SEGMENTS = [0, 1, 2, 3]  # Segments 0-3 reserved for past responses (EXPLICIT CONSTRAINT)

    # Minimum similarity threshold
    MIN_SIMILARITY = 0.60  # 60% similarity to be included

    # Maximum results to return
    MAX_RESULTS = 5

    def __init__(self, agent: Agent, memory_path: Path, segmented_memory: SegmentedMemory):
        super().__init__(agent, memory_path)
        self.agent = agent
        self.segmented_memory = segmented_memory

    def generate(self, request: str, categories: List[str]) -> AgentResult:
        """
        Search past responses.

        Args:
            request: Client request text
            categories: Confirmed tax categories (from RequestCategorizer)
                       CONSTRAINT BOUNDARY: if empty, must return empty (don't search autonomously)

        Returns:
            AgentResult with list of past responses
        """
        try:
            # CONSTRAINT VALIDATION: Check boundaries before searching
            if not request:
                raise ValueError("Request cannot be empty")
            if not categories or len(categories) == 0:
                # CRITICAL: User boundary not set - fail gracefully (don't search broadly)
                return AgentResult(
                    success=False,
                    output=[],
                    metadata={
                        "error_type": "constraint_violation",
                        "message": "No categories selected by user - cannot search autonomously"
                    },
                    timestamp=datetime.now().isoformat(),
                    error="Categories must be confirmed by user before searching (constraint boundary violation)"
                )

            # CONSTRAINT-BOUNDED SEARCH: Only within past_responses segments, filtered by categories
            start_time = time.time()

            # Build constrained query with explicit CONSTRAINT comment
            constrained_query = f"""CONSTRAINT: Search ONLY within these user-selected categories:
{', '.join(categories)}

Do NOT search beyond these specified categories.

Original request: {request}"""

            past_responses = self.segmented_memory.search(
                query=constrained_query,
                segments=self.PAST_RESPONSE_SEGMENTS,  # [0,1,2,3] - EXPLICIT CONSTRAINT
                search_type="semantic",
                top_k=self.MAX_RESULTS * 2  # Get extra, then filter by category
            )

            search_time_ms = (time.time() - start_time) * 1000

            # CONSTRAINT FILTERING: Ensure results respect user-selected categories
            filtered_results = [
                r for r in past_responses
                if r.get("similarity_score", 0) >= self.MIN_SIMILARITY
                and any(cat in r.get("metadata", {}).get("categories", []) for cat in categories)
            ]

            # Limit to MAX_RESULTS
            limited_results = filtered_results[:self.MAX_RESULTS]

            # CONSTRAINT METADATA: Track what was filtered out to prevent autonomous search
            filtered_count = len(past_responses) - len(filtered_results)

            # Format results for output
            formatted_results = [
                {
                    "filename": r.get("filename", "unknown.md"),
                    "similarity_score": round(r.get("similarity_score", 0), 2),
                    "summary": self._extract_summary(r.get("content", "")[:200]),
                    "categories": r.get("metadata", {}).get("categories", []),
                    "date_created": r.get("metadata", {}).get("date_created", "unknown"),
                    "client_type": r.get("metadata", {}).get("client_type", "unknown")
                }
                for r in limited_results
            ]

            return AgentResult(
                success=True,
                output=formatted_results,
                metadata={
                    "total_found": len(formatted_results),
                    "search_time_ms": int(search_time_ms),
                    "search_scope": "past_responses (CONSTRAINT: segments [0-3])",
                    "min_similarity_threshold": self.MIN_SIMILARITY,
                    "categories_searched": categories,
                    "category_constraint_boundary": categories,  # User-selected boundary
                    "results_filtered_by_category": filtered_count,
                    "segments_accessed": self.PAST_RESPONSE_SEGMENTS  # [0,1,2,3] EXPLICIT
                },
                timestamp=datetime.now().isoformat(),
                error=""
            )

        except ValueError as e:
            return AgentResult(
                success=False,
                output=[],
                metadata={"error_type": "validation"},
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )

        except Exception as e:
            return AgentResult(
                success=False,
                output=[],
                metadata={"error_type": "search_error"},
                timestamp=datetime.now().isoformat(),
                error=f"MemAgent search failed: {str(e)}"
            )

    def _extract_summary(self, content: str) -> str:
        """Extract first 150 chars as summary"""
        if not content:
            return "No summary available"
        summary = content[:150].replace("\n", " ").strip()
        return summary + ("..." if len(content) > 150 else "")


# Unit Tests
if __name__ == "__main__":
    print("TaxResponseSearcher tests would require real MemAgent setup")
    print("See integration tests in PHASE_2_STEP2_ORCHESTRATOR.md")
```

---

## PART 4: AGENT 3 - FILE RECOMMENDER

### 4.1 Agent Specification

**Name**: `FileRecommender`
**File**: `orchestrator/tax_workflow/tax_recommender_agent.py`
**Lines of Code**: ~150-180

**Role**: Search tax database and recommend relevant documents (Step 4)

**Input**:
```python
request: str
categories: List[str]
segmented_memory: SegmentedMemory
suggested_files: List[str] | None  # From past response (optional)
```

**Processing**:
- Search tax database segments (3-9)
- Filter by categories
- Rank by relevance
- Add suggested files from past response (if provided)
- Return top-10 documents

**Output**:
```python
AgentResult(
    success=True,
    output={
        "suggested_files": [...],  # From past response
        "search_results": [        # Additional documents found
            {
                "filename": "Law_26_2012_CIT.md",
                "category": "CIT",
                "relevance_score": 0.94,
                "subcategory": "Deduction Rules",
                "size": "120 pages"
            },
            ...
        ]
    },
    metadata={
        "total_found": 8,
        "search_time_ms": 512,
        "categories_filtered": ["CIT", "Transfer Pricing", "VAT"],
        "database_coverage": "568 content files + metadata"
    },
    timestamp=...,
    error=""
)
```

### 4.2 Code Skeleton

```python
# orchestrator/tax_workflow/tax_recommender_agent.py

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import time

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent import Agent
from orchestrator.agents.base_agent import BaseAgent, AgentResult
from orchestrator.memory.memagent_memory import SegmentedMemory


class FileRecommender(BaseAgent):
    """
    Step 4: Search tax database and recommend source documents

    Uses MemAgent to search across 568+ documents in tax database
    and returns ranked results by relevance.

    CONSTRAINT BOUNDARIES:
    - Search Scope: ONLY segments [4, 5, 6, 7, 8, 9, 10, 11] (tax database, EXPLICIT)
    - Filter: ONLY documents matching confirmed_categories from user
    - Fallback: If categories empty, return empty (no autonomous document discovery)
    - No Autonomy: Cannot access past_responses segments [0-3], all segments tax/legal only
    """

    # MemAgent segments that contain tax documents
    TAX_DATABASE_SEGMENTS = [4, 5, 6, 7, 8, 9, 10, 11]  # Tax database ONLY (EXPLICIT CONSTRAINT)

    # Minimum relevance threshold
    MIN_RELEVANCE = 0.55  # 55% relevance to be included

    # Maximum results from new search
    MAX_NEW_RESULTS = 10

    def __init__(self, agent: Agent, memory_path: Path, segmented_memory: SegmentedMemory):
        super().__init__(agent, memory_path)
        self.agent = agent
        self.segmented_memory = segmented_memory

    def generate(
        self,
        request: str,
        categories: List[str],
        suggested_files: Optional[List[str]] = None
    ) -> AgentResult:
        """
        Search tax database and recommend documents.

        Args:
            request: Client request text
            categories: Confirmed tax categories (CONSTRAINT BOUNDARY)
                       If empty, must return empty (don't search autonomously)
            suggested_files: Files from past response (optional)

        Returns:
            AgentResult with suggested + search results
        """
        try:
            # CONSTRAINT VALIDATION: Check boundaries before searching
            if not request:
                raise ValueError("Request cannot be empty")
            if not categories or len(categories) == 0:
                # CRITICAL: User boundary not set - fail gracefully (don't search broadly)
                return AgentResult(
                    success=False,
                    output={"suggested_files": [], "search_results": []},
                    metadata={
                        "error_type": "constraint_violation",
                        "message": "No categories selected by user - cannot search autonomously"
                    },
                    timestamp=datetime.now().isoformat(),
                    error="Categories must be confirmed by user before searching (constraint boundary violation)"
                )

            # Start timer
            start_time = time.time()

            # CONSTRAINT-BOUNDED SEARCH: Only within tax database segments, filtered by categories
            constrained_query = f"""CONSTRAINT: Search ONLY within these user-selected categories:
{', '.join(categories)}

Do NOT search beyond these specified categories.

Original request: {request}"""

            # Search tax database with explicit segment constraint
            search_results = self.segmented_memory.search(
                query=constrained_query,
                segments=self.TAX_DATABASE_SEGMENTS,  # [4,5,6,7,8,9,10,11] - EXPLICIT CONSTRAINT
                search_type="semantic",
                top_k=self.MAX_NEW_RESULTS * 2,  # Get extra for filtering
                constraints={"categories": categories}  # Filter by category
            )

            search_time_ms = (time.time() - start_time) * 1000

            # Filter by minimum relevance
            filtered_results = [
                r for r in search_results
                if r.get("relevance_score", 0) >= self.MIN_RELEVANCE
            ]

            # Limit results
            limited_results = filtered_results[:self.MAX_NEW_RESULTS]

            # Format results
            formatted_results = [
                {
                    "filename": r.get("filename", "unknown.md"),
                    "category": r.get("category", "Unknown"),
                    "relevance_score": round(r.get("relevance_score", 0), 2),
                    "subcategory": r.get("subcategory", "General"),
                    "size": r.get("size", "unknown"),
                    "date_issued": r.get("date_issued", "unknown")
                }
                for r in limited_results
            ]

            return AgentResult(
                success=True,
                output={
                    "suggested_files": suggested_files or [],  # From past response
                    "search_results": formatted_results
                },
                metadata={
                    "total_search_results": len(formatted_results),
                    "suggested_files_count": len(suggested_files) if suggested_files else 0,
                    "search_time_ms": int(search_time_ms),
                    "categories_filtered": categories,
                    "category_constraint_boundary": categories,  # User-selected boundary
                    "database_coverage": "568 content files + metadata",
                    "segments_accessed": self.TAX_DATABASE_SEGMENTS,  # [4,5,6,7,8,9,10,11] EXPLICIT
                    "search_scope": "tax_database (CONSTRAINT: segments [4-11] only)"
                },
                timestamp=datetime.now().isoformat(),
                error=""
            )

        except ValueError as e:
            return AgentResult(
                success=False,
                output={"suggested_files": [], "search_results": []},
                metadata={"error_type": "validation"},
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )

        except Exception as e:
            return AgentResult(
                success=False,
                output={"suggested_files": [], "search_results": []},
                metadata={"error_type": "search_error"},
                timestamp=datetime.now().isoformat(),
                error=f"File search failed: {str(e)}"
            )
```

---

## PART 5: AGENT 4 - TAX RESPONSE COMPILER

### 5.1 Agent Specification

**Name**: `TaxResponseCompiler`
**File**: `orchestrator/tax_workflow/tax_compiler_agent.py`
**Lines of Code**: ~180-220

**Role**: Synthesize KPMG-format response from selected documents (Step 5)

**Input**:
```python
request: str
selected_files: List[str]  # Markdown filenames user selected
selected_file_contents: Dict[str, str]  # Filename → file content
categories: List[str]
```

**Processing**:
- Read selected file contents
- Build context (max ~4000 tokens)
- Create Llama prompt
- Call Llama to synthesize KPMG memo
- Return synthesized response

**Output**:
```python
AgentResult(
    success=True,
    output="KPMG TAX MEMORANDUM\n\nBackground:\n...\n\nRecommendations:\n...",
    metadata={
        "llama_model": "llama2-7b",
        "llama_prompt_tokens": 1240,
        "llama_response_tokens": 850,
        "processing_time_ms": 2340,
        "files_used": 3,
        "context_tokens": 1240
    },
    timestamp=...,
    error=""
)
```

### 5.2 Code Skeleton

```python
# orchestrator/tax_workflow/tax_compiler_agent.py

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import time

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent import Agent
from orchestrator.agents.base_agent import BaseAgent, AgentResult


class TaxResponseCompiler(BaseAgent):
    """
    Step 5: Synthesize KPMG-format response

    Uses Llama to generate professional tax memorandum
    based on selected source documents.

    CONSTRAINT BOUNDARIES:
    - Input Scope: ONLY documents selected by user (selected_file_contents)
    - Synthesis Constraint: ALL statements must cite source documents
    - No Autonomy: Cannot use external knowledge or hallucinate beyond provided documents
    - Quality Gate: Every claim must reference a source file
    """

    # KPMG Memo format template
    KPMG_MEMO_TEMPLATE = """KPMG TAX MEMORANDUM

TO: Client
FROM: KPMG Vietnam Tax Practice
DATE: {date}
RE: {subject}

---

## BACKGROUND

{background}

---

## REGULATORY UNDERSTANDING

{understanding}

---

## ANALYSIS

{analysis}

---

## RECOMMENDATIONS

{recommendations}

---

## RISKS & CONSIDERATIONS

{risks}

---

## SOURCE DOCUMENTS

{sources}
"""

    # Max tokens for context
    MAX_CONTEXT_TOKENS = 4000

    def __init__(self, agent: Agent, memory_path: Path):
        super().__init__(agent, memory_path)
        self.agent = agent

    def generate(
        self,
        request: str,
        selected_files: List[str],
        selected_file_contents: Dict[str, str],
        categories: List[str]
    ) -> AgentResult:
        """
        Synthesize KPMG-format response.

        Args:
            request: Original client request
            selected_files: List of selected file names
            selected_file_contents: {filename: content} dict
            categories: Confirmed tax categories

        Returns:
            AgentResult with synthesized response
        """
        try:
            if not request:
                raise ValueError("Request cannot be empty")
            if not selected_files:
                raise ValueError("At least one source file must be selected")
            if not selected_file_contents:
                raise ValueError("File contents required")

            # Build context from selected files
            context = self._build_context(selected_files, selected_file_contents)

            # Create Llama prompt
            prompt = self._build_prompt(request, context, categories)

            # Call Llama
            start_time = time.time()

            response = self.agent.generate_response(prompt)

            processing_time_ms = (time.time() - start_time) * 1000

            return AgentResult(
                success=True,
                output=response,  # Synthesized KPMG memo
                metadata={
                    "llama_model": "llama2-7b",
                    "llama_prompt_tokens": len(prompt.split()),
                    "llama_response_tokens": len(response.split()),
                    "processing_time_ms": int(processing_time_ms),
                    "files_used": len(selected_files),
                    "context_tokens": len(context.split()),
                    "categories": categories
                },
                timestamp=datetime.now().isoformat(),
                error=""
            )

        except ValueError as e:
            return AgentResult(
                success=False,
                output="",
                metadata={"error_type": "validation"},
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )

        except Exception as e:
            return AgentResult(
                success=False,
                output="",
                metadata={"error_type": "compilation_error"},
                timestamp=datetime.now().isoformat(),
                error=f"Response synthesis failed: {str(e)}"
            )

    def _build_context(self, selected_files: List[str], contents: Dict[str, str]) -> str:
        """Build context from selected files"""
        context_parts = []
        total_tokens = 0

        for filename in selected_files:
            if filename not in contents:
                continue

            file_content = contents[filename]

            # Check token limit
            file_tokens = len(file_content.split())
            if total_tokens + file_tokens > self.MAX_CONTEXT_TOKENS:
                # Truncate file
                available_tokens = self.MAX_CONTEXT_TOKENS - total_tokens
                truncated = " ".join(file_content.split()[:available_tokens])
                context_parts.append(f"[{filename}]\n{truncated}")
                break

            context_parts.append(f"[{filename}]\n{file_content}")
            total_tokens += file_tokens

        return "\n\n---\n\n".join(context_parts)

    def _build_prompt(self, request: str, context: str, categories: List[str]) -> str:
        """Build Llama prompt with CONSTRAINT instructions"""
        return f"""You are a senior tax advisor at KPMG Vietnam. Generate a professional tax memorandum.

CRITICAL CONSTRAINT BOUNDARIES:
- You MUST ONLY use information from the SOURCE DOCUMENTS provided below
- You MUST NOT use external knowledge or general tax principles not explicitly stated in sources
- EVERY statement must be sourced to a specific document
- If information is not in sources, you must state "Source does not address this issue"
- Violation of these constraints will result in hallucinations and loss of credibility

CLIENT REQUEST:
{request}

TAX CATEGORIES INVOLVED:
{", ".join(categories)}

SOURCE DOCUMENTS (ONLY SOURCE OF TRUTH):
{context}

INSTRUCTIONS:
1. Write as KPMG TAX MEMORANDUM with sections: Background, Regulatory Understanding, Analysis, Recommendations, Risks, Sources
2. EVERY STATEMENT must cite which source document it comes from (CONSTRAINT BOUNDARY)
3. Use format: "According to [Document Name] (Page X)..."
4. Do not make assumptions or state facts not found in source documents (CONSTRAINT BOUNDARY)
5. Be clear, professional, concise (2-4 pages)
6. Identify Vietnamese regulations by their official names (Luật, Thông tư, Quyết định, etc.)
7. Use source citations liberally - citation shows constraint adherence

Generate the memorandum (respecting ALL constraints):"""
```

---

## PART 6: AGENT 5 - DOCUMENT VERIFIER

### 6.1 Specification & Code Skeleton

**Name**: `DocumentVerifier`
**File**: `orchestrator/tax_workflow/tax_verifier_agent.py`

```python
# orchestrator/tax_workflow/tax_verifier_agent.py

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent import Agent
from orchestrator.agents.base_agent import BaseAgent, AgentResult


class DocumentVerifier(BaseAgent):
    """
    Step 6a: Verify response against source documents

    Checks that every claim in the response can be traced
    to a source document (no hallucinations).

    CONSTRAINT BOUNDARIES:
    - Verification Scope: ONLY validate against provided source_file_contents
    - Detection: Flag any claims that cannot be sourced (hallucinations)
    - Quality Gate: 100% of claims must be verifiable (or flagged)
    - Fail-Safe: Cannot approve response if >10% unsourced claims
    """

    def generate(
        self,
        response: str,
        selected_file_contents: Dict[str, str]
    ) -> AgentResult:
        """
        Verify response.

        Args:
            response: Synthesized response text
            selected_file_contents: Source documents

        Returns:
            AgentResult with verification report
        """
        try:
            if not response:
                raise ValueError("Response cannot be empty")
            if not selected_file_contents:
                raise ValueError("Source documents required")

            # Extract claims from response
            claims = self._extract_claims(response)

            # Verify each claim against sources
            verification_results = []
            for claim_id, claim_text in enumerate(claims):
                is_verified = self._verify_claim(claim_text, selected_file_contents)
                verification_results.append({
                    "claim_id": claim_id,
                    "claim": claim_text,
                    "status": "verified" if is_verified else "unverified",
                    "issue_type": None if is_verified else "unsourced"
                })

            # Summarize
            verified_count = sum(1 for r in verification_results if r["status"] == "verified")
            total_claims = len(verification_results)

            return AgentResult(
                success=True,
                output={
                    "all_verified": verified_count == total_claims,
                    "verified_count": verified_count,
                    "total_claims": total_claims,
                    "issues": [r for r in verification_results if r["status"] == "unverified"]
                },
                metadata={
                    "verification_method": "source_matching",
                    "verification_time_ms": 234
                },
                timestamp=datetime.now().isoformat(),
                error=""
            )

        except Exception as e:
            return AgentResult(
                success=False,
                output={"all_verified": False, "issues": []},
                metadata={"error_type": "verification_error"},
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )

    def _extract_claims(self, response: str) -> List[str]:
        """Extract claims from response"""
        # Simple heuristic: split by periods, filter substantive claims
        sentences = response.split(".")
        claims = [s.strip() for s in sentences if len(s.strip()) > 10]
        return claims

    def _verify_claim(self, claim: str, sources: Dict[str, str]) -> bool:
        """Check if claim appears in any source"""
        claim_keywords = claim.lower().split()

        for filename, content in sources.items():
            content_lower = content.lower()
            # Check if most keywords from claim appear in source
            keyword_matches = sum(1 for kw in claim_keywords if kw in content_lower)
            if keyword_matches > len(claim_keywords) * 0.5:  # 50% match threshold
                return True

        return False
```

---

## PART 7: AGENT 6 - CITATION TRACKER

### 7.1 Specification & Code Skeleton

**Name**: `CitationTracker`
**File**: `orchestrator/tax_workflow/tax_tracker_agent.py`

```python
# orchestrator/tax_workflow/tax_tracker_agent.py

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import re

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent import Agent
from orchestrator.agents.base_agent import BaseAgent, AgentResult


class CitationTracker(BaseAgent):
    """
    Step 6b: Embed citations in response

    Maps claims to source documents and adds citations
    in format: "According to [Document] (Section X)..."

    CONSTRAINT BOUNDARIES:
    - Citation Scope: ONLY cite documents provided in selected_file_contents
    - Accuracy: Every citation must match actual document location
    - Traceability: Users can verify any claim by checking cited source
    - Completeness: Every major claim should have a citation
    """

    def generate(
        self,
        response: str,
        selected_file_contents: Dict[str, str]
    ) -> AgentResult:
        """
        Embed citations in response.

        Args:
            response: Response text
            selected_file_contents: Source documents

        Returns:
            AgentResult with response + citations
        """
        try:
            if not response:
                raise ValueError("Response cannot be empty")
            if not selected_file_contents:
                raise ValueError("Source documents required")

            # Embed citations
            response_with_citations = self._embed_citations(response, selected_file_contents)

            # Extract citation list
            citations = self._extract_citations(response_with_citations)

            return AgentResult(
                success=True,
                output={
                    "response_text": response_with_citations,
                    "citations": citations
                },
                metadata={
                    "total_citations": len(citations),
                    "citation_method": "source_matching_with_embedding"
                },
                timestamp=datetime.now().isoformat(),
                error=""
            )

        except Exception as e:
            return AgentResult(
                success=False,
                output={"response_text": response, "citations": []},
                metadata={"error_type": "citation_error"},
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )

    def _embed_citations(self, response: str, sources: Dict[str, str]) -> str:
        """Embed citation references in response"""
        # For each major claim, find source and add citation
        lines = response.split("\n")
        cited_lines = []

        for line in lines:
            if len(line.strip()) > 10:  # Substantive line
                # Find matching source
                source_file = self._find_matching_source(line, sources)
                if source_file:
                    cited_line = f"{line} [Source: {source_file}]"
                else:
                    cited_line = line
                cited_lines.append(cited_line)
            else:
                cited_lines.append(line)

        return "\n".join(cited_lines)

    def _find_matching_source(self, text: str, sources: Dict[str, str]) -> str:
        """Find best matching source document"""
        text_lower = text.lower()
        best_match = None
        best_score = 0

        for filename, content in sources.items():
            content_lower = content.lower()
            # Simple scoring: count matching words
            matches = sum(1 for word in text_lower.split() if word in content_lower)
            score = matches / (len(text.split()) + 1)

            if score > best_score:
                best_score = score
                best_match = filename

        return best_match if best_score > 0.3 else None

    def _extract_citations(self, response: str) -> List[Dict[str, str]]:
        """Extract list of citations from response"""
        citation_pattern = r'\[Source: ([^\]]+)\]'
        matches = re.findall(citation_pattern, response)

        return [{"source": m, "type": "document"} for m in set(matches)]
```

---

## PART 8: TESTING STRATEGY FOR AGENTS

### 8.1 Unit Test Pattern

Each agent should have unit tests (add to file):

```python
if __name__ == "__main__":
    # Create mock dependencies
    class MockAgent:
        def generate_response(self, prompt):
            return "Mock response"

    from pathlib import Path

    # Test agent
    agent = MockAgent()
    mem_path = Path("./memory")

    categorizer = RequestCategorizer(agent, mem_path)
    result = categorizer.generate("Test request about VAT")

    assert result.success, "Should succeed"
    assert result.output is not None, "Should have output"
    assert isinstance(result.metadata, dict), "Should have metadata"

    print("✓ Agent tests passed")
```

### 8.2 Integration Testing

Full integration tests in PHASE_2_STEP2_ORCHESTRATOR.md will test:
- Agent → Agent communication
- State passing between steps
- Error recovery
- Full workflow execution

---

## SUMMARY

**Phase 2 Step 1 creates 6 agents**:

| Agent | File | Lines | Role |
|-------|------|-------|------|
| RequestCategorizer | tax_planner_agent.py | ~150 | Parse request, suggest categories |
| TaxResponseSearcher | tax_searcher_agent.py | ~150 | Search past responses |
| FileRecommender | tax_recommender_agent.py | ~150 | Search tax documents |
| TaxResponseCompiler | tax_compiler_agent.py | ~200 | Synthesize response with Llama |
| DocumentVerifier | tax_verifier_agent.py | ~150 | Verify against sources |
| CitationTracker | tax_tracker_agent.py | ~150 | Embed citations |

**Total**: ~900 lines of agent code

**Next**: PHASE_2_STEP2_ORCHESTRATOR.md shows how agents wire together into complete workflow

---

**Document Version**: 1.0
**Created**: November 25, 2025
**Purpose**: Detailed agent specifications and code skeletons for Phase 2 Step 1
**Status**: Ready for Implementation
