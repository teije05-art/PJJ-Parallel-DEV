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

    def retrieve_context(self, goal: str, session=None, selected_entities: list = None, selected_plans: list = None) -> Dict[str, str]:
        """
        Main entry point - retrieves all context needed for planning.

        Orchestrates all context providers to gather:
        - Goal analysis information
        - Project status and context
        - Successful patterns and error patterns (CONSTRAINED to selected_plans if provided)
        - Execution history and performance (CONSTRAINED to selected_plans if provided)
        - Real-world web search data
        - Memory segments (Phase 3: SegmentedMemory integration)
        - Selected entities content (Phase 4: User-selected context)

        Args:
            goal: The planning goal
            session: Optional PlanningSession or SegmentedMemory instance (Phase 3)
            selected_entities: Optional list of entity names to include in context (Phase 4)
            selected_plans: Optional list of plan names to constrain memory searches (Phase 4: User boundaries)

        Returns:
            Dictionary with all context data:
            - goal_analysis: Analyzed goal with domain/industry/market
            - current_status: Project status and requirements
            - successful_patterns: Learned successful approaches (constrained to selected_plans)
            - error_patterns: Known error patterns to avoid (constrained to selected_plans)
            - execution_history: Past execution outcomes (constrained to selected_plans)
            - agent_performance: Agent performance metrics (constrained to selected_plans)
            - web_search_results: Current real-world data
            - memory_segments: Previous iteration insights (Phase 3, if available)
            - selected_entities: User-selected entity names (Phase 4)
            - entities_context: Content from selected entity files (Phase 4)
            - selected_plans: User-selected plan names (Phase 4)
        """
        print("\n📚 CONTEXT BUILDER: Retrieving context from all providers...")

        # 1. Analyze goal (determines domain, industry, market)
        goal_analysis = self.goal_provider.analyze_goal(goal)
        print(f"   🎯 Goal Analysis: Domain={goal_analysis.domain}, Industry={goal_analysis.industry}, Market={goal_analysis.market}")

        # 2. Retrieve all context components from providers (with user-selected constraints)
        current_status = self.goal_provider.retrieve_project_status(self.agent, goal_analysis, selected_entities=selected_entities)

        # USER-DEFINED CONSTRAINT BOUNDARIES (Phase 4):
        # All memory searches constrained to selected_plans if provided
        # If no plans selected, return empty (don't search broadly)
        plans_constraint = selected_plans or []

        successful_patterns = self.memory_provider.retrieve_successful_patterns(self.agent, selected_plans=plans_constraint)
        error_patterns = self.memory_provider.retrieve_error_patterns(self.agent, selected_plans=plans_constraint)
        execution_history = self.memory_provider.retrieve_execution_history(self.agent, selected_plans=plans_constraint)
        agent_performance = self.memory_provider.retrieve_agent_performance(self.agent, selected_plans=plans_constraint)

        # 3. Web search for real current data
        web_search_results = self.search_provider.retrieve_web_search_results(goal, goal_analysis)

        # 4. PHASE 3: Retrieve memory segments from SegmentedMemory (if available)
        memory_segments = []
        if session and hasattr(session, 'get_relevant_segments'):
            # session is a SegmentedMemory instance
            try:
                memory_segments = session.get_relevant_segments(query=goal, top_k=3)
                print(f"   ✓ Memory segments retrieved: {len(memory_segments)} segments")
            except Exception as e:
                print(f"   ⚠️ Memory segment retrieval failed: {str(e)}")
                memory_segments = []
        elif session and hasattr(session, 'memory_manager'):
            # session is a PlanningSession instance with memory_manager
            try:
                memory_segments = session.memory_manager.get_relevant_segments(query=goal, top_k=3)
                print(f"   ✓ Memory segments retrieved: {len(memory_segments)} segments")
            except Exception as e:
                print(f"   ⚠️ Memory segment retrieval failed: {str(e)}")
                memory_segments = []
        else:
            if session:
                print(f"   ℹ️ Session provided but no memory_manager found (iteration 1?)")
            else:
                print(f"   ℹ️ No session provided, memory_segments unavailable")

        # 4.5. PHASE 4: Read selected entity files from local-memory/entities/entities/
        entities_context = ""
        selected_entities_list = selected_entities or []
        if selected_entities_list:
            print(f"   🔍 Reading {len(selected_entities_list)} selected entities from local-memory...")
            for entity_name in selected_entities_list:
                entity_path = self.memory_path / "entities" / f"{entity_name}.md"
                try:
                    if entity_path.exists():
                        with open(entity_path, 'r', encoding='utf-8') as f:
                            entity_content = f.read()
                            entities_context += f"\n\n### {entity_name}\n{entity_content}"
                        print(f"      ✓ Read entity: {entity_name} ({len(entity_content)} chars)")
                    else:
                        print(f"      ⚠️ Entity file not found: {entity_path}")
                except Exception as e:
                    print(f"      ⚠️ Error reading entity {entity_name}: {str(e)}")
        else:
            print(f"   ℹ️ No selected entities provided, using default context")

        # 5. Compile all context
        context = {
            "goal_analysis": goal_analysis,
            "current_status": current_status,
            "successful_patterns": successful_patterns,
            "error_patterns": error_patterns,
            "execution_history": execution_history,
            "agent_performance": agent_performance,
            "web_search_results": web_search_results,
            "memory_segments": memory_segments,  # PHASE 3: Add memory segments
            "selected_entities": selected_entities_list,  # PHASE 4: Add selected entity names
            "entities_context": entities_context,  # PHASE 4: Add selected entity content
            "selected_plans": plans_constraint  # PHASE 4: Add selected plan names (for transparency)
        }

        print(f"   ✓ Current status retrieved")
        print(f"   ✓ Successful patterns: {len(successful_patterns)} chars")
        print(f"   ✓ Errors to avoid: {len(error_patterns)} chars")
        print(f"   ✓ Execution history: {len(execution_history)} chars")
        print(f"   ✓ Agent performance: {len(agent_performance)} chars")
        print(f"   ✓ Web search results: {len(web_search_results)} chars")
        print(f"   ✓ Memory segments: {len(memory_segments)} segments")
        print(f"   ✓ Selected entities: {len(selected_entities_list)} entities ({len(entities_context)} chars)")

        return context
