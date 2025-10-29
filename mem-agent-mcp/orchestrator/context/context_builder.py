"""
Context Builder

Main orchestrator for context retrieval.
Combines all context providers (goal, memory, search) into unified context object.
"""

from typing import Dict
from pathlib import Path

from .goal_context import GoalContextProvider
from .memory_context import MemoryContextProvider
from .search_context import SearchContextProvider


class ContextBuilder:
    """
    Orchestrates context retrieval from all providers.

    Main entry point for context gathering. Combines:
    - Goal analysis (domain, industry, market detection)
    - Memory context (patterns, history, performance)
    - Web search context (real-world market data)

    Replaces the monolithic ContextManager with modular providers.
    """

    def __init__(self, agent, memory_path: Path):
        """
        Initialize context builder with dependencies.

        Args:
            agent: The memagent instance (shared across all modules)
            memory_path: Path to memory directory
        """
        self.agent = agent
        self.memory_path = memory_path

        # Initialize all providers
        self.goal_provider = GoalContextProvider()
        self.memory_provider = MemoryContextProvider()
        self.search_provider = SearchContextProvider(agent=agent)

    def retrieve_context(self, goal: str) -> Dict[str, str]:
        """
        Main entry point - retrieves all context needed for planning.

        Orchestrates all context providers to gather:
        - Goal analysis information
        - Project status and context
        - Successful patterns and error patterns
        - Execution history and performance
        - Real-world web search data

        Args:
            goal: The planning goal

        Returns:
            Dictionary with all context data:
            - goal_analysis: Analyzed goal with domain/industry/market
            - current_status: Project status and requirements
            - successful_patterns: Learned successful approaches
            - error_patterns: Known error patterns to avoid
            - execution_history: Past execution outcomes
            - agent_performance: Agent performance metrics
            - web_search_results: Current real-world data
        """
        print("\n📚 CONTEXT BUILDER: Retrieving context from all providers...")

        # 1. Analyze goal (determines domain, industry, market)
        goal_analysis = self.goal_provider.analyze_goal(goal)
        print(f"   🎯 Goal Analysis: Domain={goal_analysis.domain}, Industry={goal_analysis.industry}, Market={goal_analysis.market}")

        # 2. Retrieve all context components from providers
        current_status = self.goal_provider.retrieve_project_status(self.agent, goal_analysis)

        successful_patterns = self.memory_provider.retrieve_successful_patterns(self.agent)
        error_patterns = self.memory_provider.retrieve_error_patterns(self.agent)
        execution_history = self.memory_provider.retrieve_execution_history(self.agent)
        agent_performance = self.memory_provider.retrieve_agent_performance(self.agent)

        # 3. Web search for real current data
        web_search_results = self.search_provider.retrieve_web_search_results(goal, goal_analysis)

        # 4. Compile all context
        context = {
            "goal_analysis": goal_analysis,
            "current_status": current_status,
            "successful_patterns": successful_patterns,
            "error_patterns": error_patterns,
            "execution_history": execution_history,
            "agent_performance": agent_performance,
            "web_search_results": web_search_results
        }

        print(f"   ✓ Current status retrieved")
        print(f"   ✓ Successful patterns: {len(successful_patterns)} chars")
        print(f"   ✓ Errors to avoid: {len(error_patterns)} chars")
        print(f"   ✓ Execution history: {len(execution_history)} chars")
        print(f"   ✓ Agent performance: {len(agent_performance)} chars")
        print(f"   ✓ Web search results: {len(web_search_results)} chars")

        return context
