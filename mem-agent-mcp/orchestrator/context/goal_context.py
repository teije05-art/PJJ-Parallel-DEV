"""
Goal Context Provider

Handles goal analysis and project status context retrieval.
Single Responsibility: Analyze goals and retrieve project status information.
"""

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

    def retrieve_project_status(self, agent, goal_analysis) -> str:
        """
        Retrieve project status using dynamic entity selection.

        Uses analyzed goal to select relevant context entities and
        retrieves project-specific information from memory.

        Args:
            agent: The memagent instance for memory retrieval
            goal_analysis: Analyzed goal with context entities

        Returns:
            Project status and context information as formatted string
        """
        try:
            context_parts = []

            # Try to retrieve context from relevant entities
            for entity in goal_analysis.context_entities:
                try:
                    response = agent.chat(f"""
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
