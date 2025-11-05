"""
Executor Agent - Implementation Specialist

Responsibilities:
- Execute plans by implementing actions
- Create deliverables
- Track execution progress

PHASE 1 (Nov 5, 2025): Creates in-memory Deliverable objects from planner text
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from agent.model import get_model_response
from .base_agent import BaseAgent, AgentResult


@dataclass
class Deliverable:
    """In-memory deliverable object (Phase 1 - Nov 5, 2025)

    NOT a file, NOT a MemAgent entity - just a Python object passed between agents
    Lives in RAM during planning session only
    """
    title: str                          # e.g., "Market Analysis"
    content: str                        # The actual completed deliverable text
    citations: List[str]                # Web sources used (extracted from content)
    domain: str                         # e.g., "manufacturing"
    iteration: int                      # Which iteration created this
    metrics: Optional[Dict] = None      # Key metrics extracted (optional)
    source_data: Optional[Dict] = None  # Raw data used (optional)


# Helper Functions for Phase 1

def extract_deliverables_from_plan(plan_text: str) -> List[str]:
    """Parse planner text to identify what deliverables are needed

    Examples of deliverables mentioned in plans:
    - Market analysis, market research
    - Competitive analysis, competitive landscape
    - Implementation plan, execution roadmap
    - Risk assessment, mitigation strategy
    - Timeline, project schedule
    - Budget analysis, financial projections
    - Resource allocation
    - Quality assurance plan

    Args:
        plan_text: The planner's strategic plan text

    Returns:
        List of deliverable titles to create
    """
    deliverable_keywords = {
        # Key deliverable types commonly in plans
        "market analysis": "Market Analysis",
        "market research": "Market Analysis",
        "competitive analysis": "Competitive Landscape Analysis",
        "competitive landscape": "Competitive Landscape Analysis",
        "competitive intelligence": "Competitive Landscape Analysis",
        "implementation plan": "Implementation Plan",
        "execution roadmap": "Implementation Plan",
        "implementation approach": "Implementation Plan",
        "risk assessment": "Risk Assessment & Mitigation",
        "risk mitigation": "Risk Assessment & Mitigation",
        "timeline": "Project Timeline",
        "project schedule": "Project Timeline",
        "budget analysis": "Financial Projections",
        "financial projections": "Financial Projections",
        "resource allocation": "Resource Allocation Plan",
        "quality assurance": "Quality Assurance Framework",
        "qa plan": "Quality Assurance Framework",
        "success metrics": "Success Metrics & KPIs",
        "kpi": "Success Metrics & KPIs",
    }

    found_deliverables = set()
    plan_lower = plan_text.lower()

    for keyword, deliverable_name in deliverable_keywords.items():
        if keyword in plan_lower:
            found_deliverables.add(deliverable_name)

    # If none found, use generic defaults
    if not found_deliverables:
        found_deliverables = {
            "Strategic Overview",
            "Implementation Roadmap",
            "Success Metrics"
        }

    return sorted(list(found_deliverables))


def extract_citations(text: str) -> List[str]:
    """Extract citation references from deliverable text

    Looks for patterns like:
    - "According to X article"
    - "[Source: X]"
    - "X reported that"
    - URL patterns

    Args:
        text: The deliverable content text

    Returns:
        List of citation references found
    """
    citations = []

    # Look for explicit source citations
    source_patterns = [
        r"source:?\s*([^,\n]+)",
        r"according to\s+([^,\n]+)",
        r"from\s+([^,\n]+)",
        r"\[([^]]*(?:article|study|report|research)[^]]*)\]",
    ]

    for pattern in source_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        citations.extend(matches)

    # Look for URLs
    url_pattern = r"https?://[^\s]+"
    urls = re.findall(url_pattern, text)
    citations.extend(urls)

    # Remove duplicates and clean up
    citations = list(set(c.strip() for c in citations if c.strip()))

    return citations[:5]  # Return top 5 citations


def extract_metrics(text: str) -> Dict:
    """Extract key metrics/numbers from deliverable text

    Looks for patterns like:
    - Numbers with units: "$5B", "12%", "100K units"
    - Growth rates: "CAGR", "growth"
    - Key metrics: "ROI", "revenue", "market size"

    Args:
        text: The deliverable content text

    Returns:
        Dict of extracted metrics
    """
    metrics = {}

    # Look for monetary values
    money_pattern = r"\$[\d,]+(?:\.\d+)?(?:\s*(?:billion|million|thousand|B|M|K))?"
    money_values = re.findall(money_pattern, text, re.IGNORECASE)
    if money_values:
        metrics["monetary_values"] = money_values[:3]

    # Look for percentages
    percent_pattern = r"(\d+(?:\.\d+)?)\s*%"
    percent_values = re.findall(percent_pattern, text)
    if percent_values:
        metrics["percentages"] = percent_values[:3]

    # Look for growth rates
    if "cagr" in text.lower() or "growth rate" in text.lower():
        metrics["has_growth_rate"] = True

    # Look for years/timeline
    year_pattern = r"20\d{2}|Q[1-4]\s*20\d{2}"
    years = re.findall(year_pattern, text)
    if years:
        metrics["timeline"] = years[:3]

    return metrics if metrics else None


class ExecutorAgent(BaseAgent):
    """🛠️ Executor Agent - The implementation specialist

    Responsibilities:
    - Execute plans by calling appropriate tools
    - Implement actions and create deliverables
    - Coordinate with MemAgent for execution tracking
    - Provide detailed execution feedback
    """

    def execute_plan(self, plan: str, goal: str, context: Dict = None) -> AgentResult:
        """Execute a strategic plan by creating in-memory Deliverable objects (Phase 1)

        PHASE 1 (Nov 5, 2025): Creates actual Deliverable objects from planner text
        - Parses what deliverables are needed
        - For each deliverable, creates actual content using web search data + memory context
        - Returns list of Deliverable objects (not files, not text)

        Args:
            plan: The strategic plan to execute (from planner agent)
            goal: The original planning goal
            context: Context dict with web_search_results, memory_segments, domain, iteration_number

        Returns:
            AgentResult with list of Deliverable objects in output field
        """

        context = context or {}
        iteration_num = context.get('iteration_number', 1)
        max_iterations = context.get('max_iterations', 1)

        if context.get('iteration_mode'):
            print(f"\n🛠️ EXECUTOR AGENT: Executing iteration {iteration_num}/{max_iterations}...")
        else:
            print(f"\n🛠️ EXECUTOR AGENT: Executing strategic plan...")

        try:
            # STEP 1: Parse planner text to extract deliverables needed
            deliverables_needed = extract_deliverables_from_plan(plan)
            print(f"   📋 Identified {len(deliverables_needed)} deliverables to create")

            # STEP 2: For each deliverable, ACTUALLY CREATE it
            created_deliverables: List[Deliverable] = []

            for deliverable_type in deliverables_needed:
                print(f"   🔄 Creating: {deliverable_type}...")

                # Get web search data for this deliverable
                web_search_data = context.get('web_search_results', 'No web search data available')[:2000]

                # PHASE 3: Get memory context from SegmentedMemory (previous iterations)
                memory_segments = context.get('memory_segments', [])
                memory_text = ""
                if memory_segments:
                    memory_text = f"\n\nLessons from previous iterations (MemAgent SegmentedMemory):\n"
                    if isinstance(memory_segments, list):
                        for i, segment in enumerate(memory_segments[:3], 1):  # Top 3 segments
                            # Handle both MemorySegment objects and tuples from get_relevant_segments
                            if isinstance(segment, tuple) and len(segment) >= 2:
                                # Result from get_relevant_segments: (idx, MemorySegment, relevance)
                                segment_obj = segment[1]
                                content = segment_obj.content if hasattr(segment_obj, 'content') else str(segment_obj)
                                source = segment_obj.source if hasattr(segment_obj, 'source') else 'previous'
                            elif hasattr(segment, 'content'):
                                # Direct MemorySegment object
                                content = segment.content
                                source = segment.source if hasattr(segment, 'source') else 'previous'
                            elif isinstance(segment, dict):
                                # Dictionary representation
                                content = segment.get('content', '')
                                source = segment.get('source', 'previous')
                            else:
                                # Fallback for other types
                                content = str(segment)[:300]
                                source = 'previous'

                            # Truncate content if too long
                            content_preview = content[:250] if len(content) > 250 else content
                            memory_text += f"  {i}. [{source}] {content_preview}...\n"

                # Create prompt to actually build this deliverable
                memory_emphasis = ""
                if memory_text:
                    memory_emphasis = "\n6. **IMPORTANT FOR ITERATION 2+**: Learn from and build upon the previous iteration's insights shown above\n"
                    memory_emphasis += "   - Reference what worked before\n"
                    memory_emphasis += "   - Avoid repeating what didn't work\n"
                    memory_emphasis += "   - Go deeper and more specific than iteration 1\n"

                creation_prompt = f"""
You are creating a detailed {deliverable_type} as part of a strategic planning process.

GOAL: {goal}
ITERATION: {iteration_num} of {max_iterations}

DELIVERABLE TO CREATE: {deliverable_type}

AVAILABLE DATA:
{web_search_data}
{memory_text}

YOUR TASK:
Create a comprehensive {deliverable_type} that:
1. Uses specific data, metrics, and numbers from the web search data provided
2. Cites sources when using data (e.g., "According to [source]" or "[Source: X]")
3. Includes concrete details, not generic placeholder text
4. Is suitable for iteration {iteration_num} of the planning process
5. Builds on previous insights if this is iteration 2+{memory_emphasis}

Make this a real, data-driven document with substance.
"""

                # Get LLM response (actual content for this deliverable)
                try:
                    deliverable_content = get_model_response(
                        message=creation_prompt,
                        client=self.agent._client
                    )
                except Exception as prompt_error:
                    print(f"   ⚠️ Failed to create {deliverable_type}: {str(prompt_error)}")
                    deliverable_content = f"[Unable to create {deliverable_type}: {str(prompt_error)}]"

                # Extract citations and metrics from the generated content
                citations = extract_citations(deliverable_content)
                metrics = extract_metrics(deliverable_content)

                # Create in-memory Deliverable object
                deliverable = Deliverable(
                    title=deliverable_type,
                    content=deliverable_content,
                    citations=citations,
                    domain=context.get('domain', 'general'),
                    iteration=iteration_num,
                    metrics=metrics,
                    source_data={"web_search_used": bool(web_search_data)}
                )

                created_deliverables.append(deliverable)
                print(f"      ✅ Created {deliverable_type} ({len(deliverable_content)} chars)")

            # STEP 3: Return Deliverable objects in result
            print(f"   ✅ Created {len(created_deliverables)} total deliverables")

            execution_metadata = {
                "goal": goal,
                "iteration": iteration_num,
                "deliverables_created": len(created_deliverables),
                "deliverable_types": [d.title for d in created_deliverables],
                "total_content_chars": sum(len(d.content) for d in created_deliverables),
                "phase": "1_executor_objects"
            }

            result = self._wrap_result(
                success=True,
                output=created_deliverables,  # List of Deliverable objects!
                metadata=execution_metadata
            )

            # PHASE 1 (Nov 5): Also set deliverables field for clean access by generator
            result.deliverables = created_deliverables

            # Log the execution action
            self._log_agent_action("execute_plan", result)

            return result

        except Exception as e:
            return self._handle_error("Execution", e)
