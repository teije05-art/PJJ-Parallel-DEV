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
        NEW: Retrieve current real-world data via web search

        This dramatically improves plan quality by providing:
        - Current market data and statistics
        - Real company examples
        - Industry trends
        - Expert insights

        Args:
            goal: The planning goal
            goal_analysis: Analyzed goal with domain/industry/market

        Returns:
            Formatted web search results with current data
        """
        # Import search module (will be created next)
        try:
            from .search_module import SearchModule
            search = SearchModule()

            # Generate search queries based on goal
            queries = [
                f"{goal_analysis.industry} market analysis 2025",
                f"{goal_analysis.domain} best practices case studies",
                f"{goal} successful examples",
                f"{goal_analysis.industry} trends statistics"
            ]

            all_results = []
            for query in queries:
                results = search.search(query, num_results=3)
                if results:
                    all_results.append(f"\n### Search: {query}")
                    for result in results:
                        all_results.append(f"**{result.title}**")
                        all_results.append(f"{result.snippet}")
                        all_results.append(f"Source: {result.url}\n")

            if all_results:
                return "\n".join(all_results)
            else:
                return "No web search results available"

        except Exception as e:
            print(f"   ⚠️ Web search unavailable: {e}")
            return "Web search not available (module not found or API key missing)"
