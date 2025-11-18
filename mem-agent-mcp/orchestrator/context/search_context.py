"""
Search Context Provider

Handles web search integration for real-world market data using goal-aware ResearchAgent.
Single Responsibility: Execute goal-specific web research and compile search results.
"""

from typing import Dict
from research_agent import ResearchAgent
from .context_formatter import ContextFormatter


class SearchContextProvider:
    """
    Provides web search context with goal-aware research using ResearchAgent.

    Conducts intelligent, iterative searches focused on the specific planning goal,
    providing current market trends, competitive analysis, and expert insights.
    """

    def __init__(self, agent=None):
        """
        Initialize search context provider

        Args:
            agent: Optional Agent instance (kept for compatibility)
        """
        self.formatter = ContextFormatter()
        self.agent = agent
        # Note: ResearchAgent will be initialized per research call with goal-specific parameters

    def _generate_search_queries(self, goal: str, goal_analysis) -> list[str]:
        """
        Generate 8-10 goal-specific search queries using Fireworks/Llama.

        Instead of 24 hardcoded template queries, asks LLM to create
        specific queries tailored to the exact planning goal, focusing on
        concrete data, numbers, and statistics.

        Args:
            goal: The exact planning goal from user
            goal_analysis: Analyzed goal with domain/industry/market

        Returns:
            List of 8-10 specific search queries
        """
        system_prompt = """You are an expert research query generator.
Your job is to create specific, focused web search queries that will find
concrete data, statistics, numbers, and key market information."""

        user_prompt = f"""Given this planning goal, generate 8-10 specific web search queries
that will find real data, numbers, statistics, and concrete details:

PLANNING GOAL: {goal}

CONTEXT:
- Domain: {goal_analysis.domain}
- Industry: {goal_analysis.industry}
- Market: {goal_analysis.market}

Focus on finding:
- Specific numbers (market size, growth rates, percentages)
- Current data (2024-2025 statistics)
- Key details (regulations, requirements, competitive info)
- Company/industry specific information

Return ONLY the queries, one per line, no numbering or explanation."""

        try:
            # Import here to avoid circular dependencies
            from agent.model import get_model_response, create_fireworks_client
            from agent.schemas import ChatMessage, Role

            # Use agent's client if available, otherwise create Fireworks client
            if self.agent:
                messages = [
                    ChatMessage(role=Role.SYSTEM, content=system_prompt),
                    ChatMessage(role=Role.USER, content=user_prompt)
                ]

                response = get_model_response(
                    messages=messages,
                    client=self.agent._client
                )
            else:
                # Fallback to default Fireworks client
                client = create_fireworks_client()
                messages = [
                    ChatMessage(role=Role.SYSTEM, content=system_prompt),
                    ChatMessage(role=Role.USER, content=user_prompt)
                ]
                response = get_model_response(
                    messages=messages,
                    client=client
                )

            # Parse queries from response
            queries = [q.strip() for q in response.strip().split('\n') if q.strip()]
            queries = queries[:10]  # Limit to 10

            print(f"   Generated {len(queries)} goal-specific search queries")
            return queries

        except Exception as e:
            print(f"   ⚠️ LLM query generation failed: {e}")
            # Fallback to basic queries
            return [goal, f"{goal_analysis.industry} market"]

    def retrieve_web_search_results(self, goal: str, goal_analysis) -> str:
        """
        Execute goal-aware, intelligent web research using ResearchAgent.

        Uses ResearchAgent for iterative, goal-focused research that provides:
        - Goal-aware research (identifies what data matters for THIS goal)
        - Semantic search with Jina.ai/Reader (finds relevant sources)
        - Iterative refinement (multiple search passes with gap validation)
        - Rich data extraction (regex + LLM-based semantic extraction)
        - Coverage validation (ensures critical data categories are addressed)

        Args:
            goal: The exact planning goal
            goal_analysis: Analyzed goal with domain/industry/market

        Returns:
            Formatted web search results with citations and key data
        """
        try:
            print(f"   🔍 Starting goal-aware research using ResearchAgent...")

            # Convert goal_analysis object to dict for ResearchAgent
            goal_analysis_dict = {
                "domain": getattr(goal_analysis, "domain", ""),
                "industry": getattr(goal_analysis, "industry", ""),
                "market": getattr(goal_analysis, "market", ""),
            }

            # Initialize ResearchAgent with goal-awareness
            try:
                research_agent = ResearchAgent(
                    verbose=False,
                    goal=goal,
                    goal_analysis=goal_analysis_dict
                )
            except ValueError as e:
                if "JINA_API_KEY" in str(e):
                    print(f"   ⚠️ Jina API key not configured: {e}")
                    return "Research unavailable: JINA_API_KEY not set. Get a free key at https://jina.ai"
                raise

            # Run goal-aware research (4-5 iterations for context phase)
            print(f"   🔍 Executing goal-aware research (max 4 iterations)...")
            research_result = research_agent.research(
                goal=goal,
                goal_analysis=goal_analysis_dict,
                max_iterations=4
            )

            # Format results for downstream consumption
            print(f"   ✓ Research complete: {len(research_result.sources)} sources, "
                  f"{len(research_result.key_data_points)} data points, "
                  f"Coverage: {research_result.coverage:.0%}")

            formatted_results = self._format_research_results(research_result)

            return formatted_results

        except Exception as e:
            print(f"   ⚠️ Research unavailable: {e}")
            import traceback
            traceback.print_exc()
            return f"Research unavailable: {str(e)}"

    def _format_research_results(self, research_result) -> str:
        """
        Format ResearchResult into readable string for context consumption.

        Maintains compatibility with downstream agents expecting web_search_results format.

        Args:
            research_result: ResearchResult object from ResearchAgent

        Returns:
            Formatted string with sources, data points, and summary
        """
        formatted = []

        # Add summary
        if research_result.summary:
            formatted.append("# Research Summary\n")
            formatted.append(research_result.summary)
            formatted.append("")

        # Add sources
        if research_result.sources:
            formatted.append("## Sources Consulted")
            for i, source in enumerate(research_result.sources[:10], 1):
                formatted.append(f"{i}. {source}")
            formatted.append("")

        # Add coverage metrics
        formatted.append("## Research Coverage")
        formatted.append(f"- Coverage: {research_result.coverage:.0%}")
        formatted.append(f"- Gaps Filled: {len(research_result.gaps_filled)}/{len(research_result.gaps_filled) + len(research_result.gaps_remaining)}")
        formatted.append(f"- Iterations Used: {research_result.iterations_used}")
        formatted.append("")

        # Add key data points
        if research_result.key_data_points:
            formatted.append("## Key Data Points")
            for point in research_result.key_data_points[:20]:  # Top 20 points
                formatted.append(f"- {point}")

        return "\n".join(formatted)
