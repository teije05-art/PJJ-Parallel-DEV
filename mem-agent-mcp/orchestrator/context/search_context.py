"""
Search Context Provider

Handles web search integration for real-world market data.
Single Responsibility: Execute web searches and compile search results.
"""

from typing import Dict
from orchestrator.search_module import SearchModule
from .context_formatter import ContextFormatter


class SearchContextProvider:
    """
    Provides web search context with real-world market data.

    Conducts extensive searches across multiple categories to provide
    current market trends, competitive analysis, and expert insights.
    """

    def __init__(self, agent=None):
        """
        Initialize search context provider

        Args:
            agent: Optional Agent instance for LLM query generation
                   If not provided, will use default Fireworks client
        """
        self.search = SearchModule()
        self.formatter = ContextFormatter()
        self.agent = agent

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

            # Use agent's client if available
            if self.agent:
                messages = [
                    ChatMessage(role=Role.SYSTEM, content=system_prompt),
                    ChatMessage(role=Role.USER, content=user_prompt)
                ]

                response = get_model_response(
                    messages=messages,
                    model=self.agent.model,
                    client=self.agent._client,
                    use_fireworks=self.agent.use_fireworks,
                    use_vllm=self.agent.use_vllm
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
                    client=client,
                    use_fireworks=True
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
        Execute LLM-generated, goal-specific web searches.

        Replaces hardcoded 24 template queries with 8-10 LLM-generated queries
        tailored to the exact planning goal, focusing on concrete data and numbers.

        Dramatically improves plan quality by providing:
        - Goal-specific search queries (not templates)
        - Focused on concrete data, statistics, and numbers
        - Current market trends and company-specific information
        - Real competitive landscape analysis
        - Actual statistics and regulatory information

        Args:
            goal: The exact planning goal
            goal_analysis: Analyzed goal with domain/industry/market

        Returns:
            Organized web search results with citations and links
        """
        try:
            # STEP 1: Generate goal-specific queries using LLM
            print(f"   🔍 Generating goal-specific search queries...")
            search_queries = self._generate_search_queries(goal, goal_analysis)

            if not search_queries:
                print(f"   ⚠️ No queries generated, using fallback")
                search_queries = [goal, f"{goal_analysis.industry} market"]

            # STEP 2: Execute queries
            print(f"   🔍 Executing {len(search_queries)} searches...")
            organized_results = {"Search Results": []}
            total_results = 0

            for query in search_queries:
                print(f"      → {query[:60]}...")
                results = self.search.search(query, num_results=5)

                if results:
                    for result in results:
                        organized_results["Search Results"].append({
                            'title': result.title,
                            'snippet': result.snippet,
                            'url': result.url,
                            'source': result.source,
                            'query': query
                        })
                        total_results += 1

                print(f"      ✓ {len(results)} results")

            # STEP 3: Format and return results
            print(f"   ✓ Web search complete: {total_results} results from {len(search_queries)} queries")

            return self.formatter.format_web_search_results(
                organized_results,
                len(search_queries),
                total_results
            )

        except Exception as e:
            print(f"   ⚠️ Web search unavailable: {e}")
            import traceback
            traceback.print_exc()
            return f"Web search unavailable: {str(e)}"
