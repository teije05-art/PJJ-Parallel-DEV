"""
Context Manager Module

Single Responsibility: Retrieve and prepare context for planning

This module handles all context retrieval operations:
- Goal analysis
- Entity selection
- Pattern loading
- Execution history retrieval
- Web search integration (NEW!)

No dependencies on: Agent execution, workflow coordination, memory writing
"""

import os
import sys
from typing import Dict, Optional
from pathlib import Path

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from .goal_analyzer import GoalAnalyzer


class ContextManager:
    """Manages all context retrieval for planning"""

    def __init__(self, agent: Agent, memory_path: Path):
        """
        Initialize context manager

        Args:
            agent: The memagent instance (shared across all modules)
            memory_path: Path to memory directory
        """
        self.agent = agent
        self.memory_path = memory_path
        self.goal_analyzer = GoalAnalyzer()

    def retrieve_context(self, goal: str) -> Dict[str, str]:
        """
        Main entry point - retrieves all context needed for planning

        Args:
            goal: The planning goal

        Returns:
            Dictionary with all context data:
            - current_status: Project status and requirements
            - successful_patterns: Learned successful approaches
            - errors_to_avoid: Known error patterns
            - execution_history: Past executions
            - agent_performance: Agent performance metrics
            - web_search_results: Current real-world data (NEW!)
        """
        print("\n📚 CONTEXT MANAGER: Retrieving context from memory...")

        # Analyze goal
        goal_analysis = self.goal_analyzer.analyze_goal(goal)
        print(f"   🎯 Goal Analysis: Domain={goal_analysis.domain}, Industry={goal_analysis.industry}, Market={goal_analysis.market}")

        # Retrieve all context components
        current_status = self._retrieve_project_status(goal_analysis)
        successful_patterns = self._retrieve_successful_patterns()
        errors_to_avoid = self._retrieve_error_patterns()
        execution_history = self._retrieve_execution_history()
        agent_performance = self._retrieve_agent_performance()

        # NEW: Web search for real current data
        web_search_results = self._retrieve_web_search_results(goal, goal_analysis)

        context = {
            "goal_analysis": goal_analysis,
            "current_status": current_status,
            "successful_patterns": successful_patterns,
            "errors_to_avoid": errors_to_avoid,
            "execution_history": execution_history,
            "agent_performance": agent_performance,
            "web_search_results": web_search_results
        }

        print(f"   ✓ Current status retrieved")
        print(f"   ✓ Successful patterns: {len(successful_patterns)} chars")
        print(f"   ✓ Errors to avoid: {len(errors_to_avoid)} chars")
        print(f"   ✓ Execution history: {len(execution_history)} chars")
        print(f"   ✓ Agent performance: {len(agent_performance)} chars")
        print(f"   ✓ Web search results: {len(web_search_results)} chars")

        return context

    def _retrieve_project_status(self, goal_analysis) -> str:
        """Retrieve project status using dynamic entity selection"""
        try:
            context_parts = []

            # Try to retrieve context from relevant entities
            for entity in goal_analysis.context_entities:
                try:
                    response = self.agent.chat(f"""
                        OPERATION: RETRIEVE
                        ENTITY: {entity}
                        CONTEXT: Current project status and requirements

                        What information is available about the current project?
                        What methodologies, frameworks, or best practices are relevant?
                        What specific requirements, constraints, or considerations apply?
                    """)
                    if response.reply and response.reply.strip():
                        context_parts.append(f"=== {entity.upper()} ===\n{response.reply}")
                except:
                    continue

            if context_parts:
                return "\n\n".join(context_parts)
            else:
                # Fallback to generic context
                return "No specific project context available"

        except Exception as e:
            return f"Context retrieval failed: {str(e)}"

    def _retrieve_successful_patterns(self) -> str:
        """Retrieve successful patterns from memory"""
        try:
            response = self.agent.chat("""
                OPERATION: RETRIEVE
                ENTITY: successful_patterns
                CONTEXT: Review successful planning approaches across all agents

                What planning patterns have worked well across all 4 agents?
                What approaches led to successful workflow outcomes?
                What agent coordination strategies proved effective?
            """)
            return response.reply or "No successful patterns yet (first iteration)"
        except:
            return "Pattern retrieval failed"

    def _retrieve_error_patterns(self) -> str:
        """Retrieve error patterns from memory"""
        try:
            response = self.agent.chat("""
                OPERATION: RETRIEVE
                ENTITY: planning_errors
                CONTEXT: Review planning mistakes across all agents

                What planning approaches have been rejected across all agents?
                What common mistakes should be avoided in agent coordination?
                What workflow patterns led to failures?
            """)
            return response.reply or "No errors yet (no failures)"
        except:
            return "Error pattern retrieval failed"

    def _retrieve_execution_history(self) -> str:
        """Retrieve execution history from memory"""
        try:
            response = self.agent.chat("""
                OPERATION: RETRIEVE
                ENTITY: execution_log
                CONTEXT: Review past enhanced iterations and workflows

                What enhanced workflows have been successfully executed?
                How many iterations have completed with agent coordination?
                What were the outcomes of previous agentic workflows?
            """)
            return response.reply or "No history yet (first iteration)"
        except:
            return "Execution history retrieval failed"

    def _retrieve_agent_performance(self) -> str:
        """Retrieve agent performance metrics from memory"""
        try:
            response = self.agent.chat("""
                OPERATION: RETRIEVE
                ENTITY: agent_performance
                CONTEXT: Review agent performance and learning progress

                What are the current performance metrics for each agent?
                How has Flow-GRPO training improved planning over time?
                What agent-specific improvements have been observed?
            """)
            return response.reply or "No performance data yet (first iteration)"
        except:
            return "Performance data retrieval failed"

    def _retrieve_web_search_results(self, goal: str, goal_analysis) -> str:
        """
        EXTENSIVE Web Search - Comprehensive real-world data collection

        This dramatically improves plan quality by providing:
        - Current market data and statistics (with links)
        - Real company examples and case studies
        - Industry trends and forecasts
        - Expert insights and research
        - Regulatory and compliance information
        - Competitive landscape analysis

        Returns formatted search results with FULL URLs for reference and citation.

        Args:
            goal: The planning goal
            goal_analysis: Analyzed goal with domain/industry/market

        Returns:
            Organized web search results with comprehensive citations and links
        """
        try:
            from .search_module import SearchModule
            search = SearchModule()
            from datetime import datetime

            # EXTENSIVE search queries - multiple angles for comprehensive coverage
            search_queries = {
                "Market Analysis": [
                    f"{goal_analysis.industry} market size 2025",
                    f"{goal_analysis.industry} market growth forecast",
                    f"{goal_analysis.market} market research report",
                    f"{goal_analysis.industry} industry analysis 2025"
                ],
                "Competitive Landscape": [
                    f"{goal_analysis.industry} competitors analysis",
                    f"{goal_analysis.industry} market leaders",
                    f"{goal_analysis.industry} competitive advantage",
                    f"{goal} competitive analysis"
                ],
                "Case Studies & Examples": [
                    f"{goal_analysis.industry} successful companies",
                    f"{goal_analysis.domain} case studies",
                    f"{goal} successful implementation",
                    f"{goal_analysis.industry} best practices examples"
                ],
                "Trends & Innovations": [
                    f"{goal_analysis.industry} trends 2025",
                    f"{goal_analysis.industry} innovations",
                    f"{goal_analysis.domain} emerging trends",
                    f"{goal_analysis.industry} future outlook"
                ],
                "Regulatory & Compliance": [
                    f"{goal_analysis.industry} regulations",
                    f"{goal_analysis.market} regulatory requirements",
                    f"{goal_analysis.industry} compliance requirements",
                    f"{goal_analysis.domain} legal requirements"
                ],
                "Expert Insights": [
                    f"{goal_analysis.industry} expert analysis",
                    f"{goal_analysis.domain} thought leaders",
                    f"{goal_analysis.industry} research papers",
                    f"{goal_analysis.domain} best practices guide"
                ]
            }

            # Collect results organized by category
            organized_results = {}
            total_searches = 0
            total_results = 0

            print(f"   🔍 Starting extensive web search ({len(search_queries)} categories)...")

            for category, queries in search_queries.items():
                print(f"      → Searching: {category}...")
                organized_results[category] = []

                for query in queries:
                    # Get 5-10 results per query for comprehensive coverage
                    results = search.search(query, num_results=8)
                    total_searches += 1

                    if results:
                        for idx, result in enumerate(results, 1):
                            organized_results[category].append({
                                'title': result.title,
                                'snippet': result.snippet,
                                'url': result.url,
                                'source': result.source,
                                'query': query
                            })
                            total_results += 1

                print(f"      ✓ {category}: {len(organized_results[category])} results found")

            # Format results for agents to use with proper citations
            print(f"   ✓ Web search complete: {total_results} results from {total_searches} queries")

            if total_results == 0:
                return "No web search results available - internet may be unavailable"

            # Build comprehensive formatted output with citations
            formatted_output = f"""# 🌐 EXTENSIVE WEB RESEARCH DATA
*Comprehensive real-world data collection with {total_results} sources across {len(search_queries)} categories*

---

"""

            for category, results in organized_results.items():
                if results:
                    formatted_output += f"\n## 📊 {category}\n"
                    formatted_output += f"*{len(results)} sources identified*\n\n"

                    for idx, result in enumerate(results, 1):
                        # Format with clear citations and clickable URLs
                        formatted_output += f"""### [{idx}] {result['title']}

**Source:** {result['source']}
**URL:** {result['url']}

{result['snippet']}

---

"""

            # Add research methodology note
            formatted_output += f"""
## 📈 Research Methodology

- **Total Sources Analyzed:** {total_results}
- **Search Categories:** {len(search_queries)}
- **Queries Executed:** {total_searches}
- **Search Method:** DuckDuckGo (Real-time web search)
- **Results Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### How to Use These Sources
1. Agents can reference specific sources by number [1], [2], etc.
2. URLs can be verified for accuracy and current information
3. Snippets provide context from each source
4. Sources are organized by research category for easy navigation

### Citation Format for Agents
When using these sources, agents should cite as:
- "[Title] [Source - URL]" or
- "According to [Source]: [finding]"

This ensures all planning decisions are grounded in real, verifiable information.

---
"""

            return formatted_output

        except Exception as e:
            print(f"   ⚠️ Web search unavailable: {e}")
            import traceback
            traceback.print_exc()
            return f"Web search unavailable: {str(e)}"
