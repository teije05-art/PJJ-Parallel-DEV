"""
Base Template Framework

This module provides the base class and common functionality for domain-specific templates.
All domain-specific templates inherit from BaseTemplate and implement their domain-specific content.
"""

from typing import Dict
from orchestrator.goal_analyzer import GoalAnalysis


class BaseTemplate:
    """Base class for all domain-specific planning templates

    Provides common template formatting and structure.
    Subclasses implement domain-specific content by overriding get_template_string().
    """

    def __init__(self):
        """Initialize base template"""
        self.domain = self.__class__.__name__.replace('Template', '').lower()

    def get_planning_prompt(self, goal_analysis: GoalAnalysis, context_data: Dict[str, str]) -> str:
        """
        Generate a domain-specific planning prompt based on goal analysis.

        Args:
            goal_analysis: Analyzed goal with domain, industry, market info
            context_data: Retrieved context data from memory

        Returns:
            Formatted planning prompt tailored to the specific domain
        """
        template_string = self.get_template_string()

        # Format the template with actual data
        prompt = template_string.format(
            goal=context_data.get('goal', 'Unknown'),
            domain=goal_analysis.domain.title(),
            industry=goal_analysis.industry.title(),
            market=goal_analysis.market.replace('_', ' ').title(),
            company_type=goal_analysis.company_type.title(),
            methodologies=', '.join(goal_analysis.methodologies),
            considerations='\n'.join([f"- {c}" for c in goal_analysis.considerations]),
            project_context=context_data.get('project_context', 'No specific project context available'),
            successful_patterns=context_data.get('successful_patterns', 'No successful patterns yet'),
            error_patterns=context_data.get('error_patterns', 'No error patterns yet'),
            execution_history=context_data.get('execution_history', 'No execution history yet'),
            current_status=context_data.get('current_status', 'No current status available'),
            web_search_results=context_data.get('web_search_results', 'No web search results available')
        )

        return prompt

    def get_template_string(self) -> str:
        """
        Return the domain-specific template string.

        Override this method in subclasses to provide domain-specific content.
        The string should contain {placeholders} for the following variables:
        - goal
        - domain
        - industry
        - market
        - company_type
        - methodologies
        - considerations
        - project_context
        - successful_patterns
        - error_patterns
        - execution_history
        - current_status
        - web_search_results

        Returns:
            Template string with placeholders
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_template_string()"
        )
