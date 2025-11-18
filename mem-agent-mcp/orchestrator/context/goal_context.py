"""
Goal Context Provider

Handles goal analysis and project status context retrieval.
Single Responsibility: Analyze goals and retrieve project status information from CONSTRAINED user-selected entities.
"""

from typing import Optional, List
from orchestrator.goal_analyzer import GoalAnalyzer


class GoalContextProvider:
    """
    Provides goal analysis and project status context.

    Wraps GoalAnalyzer and retrieves project status based on analyzed goal.
    """

    def __init__(self):
        """Initialize goal context provider"""
        self.goal_analyzer = GoalAnalyzer()

    def analyze_goal(self, goal: str):
        """
        Analyze a planning goal to extract domain, industry, market info.

        Args:
            goal: The planning goal to analyze

        Returns:
            GoalAnalysis object with domain, industry, market, etc.
        """
        return self.goal_analyzer.analyze_goal(goal)

    def retrieve_project_status(self, agent, goal_analysis, selected_entities: Optional[List[str]] = None) -> str:
        """
        Retrieve project status from user-selected entities (constrained search)

        CONSTRAINT: Only retrieves status from entities explicitly selected by user.
        Does NOT autonomously search all entities or fall back to unbounded searches.

        Args:
            agent: The memagent instance for memory retrieval
            goal_analysis: Analyzed goal with context entities (NOT USED for constraint)
            selected_entities: User-selected entity names to search within (REQUIRED for constraint enforcement)

        Returns:
            Project status and context information from selected entities only, or empty string if no selections
        """
        try:
            # CONSTRAINT ENFORCEMENT: If user didn't select entities, return empty
            if not selected_entities:
                return ""

            context_parts = []

            # Retrieve context from ONLY user-selected entities (constrained)
            for entity in selected_entities:
                try:
                    response = agent.chat(f"""
                        OPERATION: RETRIEVE
                        ENTITY: {entity}
                        CONSTRAINT: Analyze ONLY WITHIN this user-selected entity.
                        This entity was explicitly selected by the user for status retrieval.
                        Do NOT search for other entities.

                        For entity: {entity}

                        What information is available about the current project?
                        What methodologies, frameworks, or best practices are relevant?
                        What specific requirements, constraints, or considerations apply?
                    """)
                    if response.reply and response.reply.strip():
                        context_parts.append(f"=== {entity.upper()} ===\n{response.reply}")
                except:
                    continue

            # Return what we found within constraints (no fallback to unbounded search)
            if context_parts:
                return "\n\n".join(context_parts)
            else:
                # STRICT CONSTRAINT: No fallback to generic/unbounded context
                return ""

        except Exception as e:
            return f"Context retrieval failed: {str(e)}"
