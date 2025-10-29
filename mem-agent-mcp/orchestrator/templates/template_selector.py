"""
Template Selector

Routes domain-specific goal analyses to appropriate domain templates.
Selects the correct template class based on the identified domain.
"""

from typing import Dict
from orchestrator.goal_analyzer import GoalAnalysis
from .base_template import BaseTemplate
from .healthcare_template import HealthcareTemplate
from .technology_template import TechnologyTemplate
from .manufacturing_template import ManufacturingTemplate
from .qsr_template import QSRTemplate
from .retail_template import RetailTemplate
from .financial_template import FinancialTemplate
from .general_template import GeneralTemplate


class TemplateSelector:
    """
    Selects and manages domain-specific planning templates.

    Routes goal analyses to the appropriate domain template based on
    the identified domain from goal analysis.
    """

    def __init__(self):
        """Initialize template selector with all available templates"""
        self.templates: Dict[str, BaseTemplate] = {
            'healthcare': HealthcareTemplate(),
            'technology': TechnologyTemplate(),
            'manufacturing': ManufacturingTemplate(),
            'qsr': QSRTemplate(),
            'retail': RetailTemplate(),
            'financial': FinancialTemplate(),
            'general': GeneralTemplate()
        }

    def get_template(self, domain: str) -> BaseTemplate:
        """
        Get the template for a specific domain.

        Args:
            domain: The domain identifier (healthcare, technology, etc.)

        Returns:
            BaseTemplate instance for the domain, or GeneralTemplate if unknown
        """
        return self.templates.get(domain, self.templates['general'])

    def get_planning_prompt(self, goal_analysis: GoalAnalysis, context_data: Dict[str, str]) -> str:
        """
        Generate a domain-specific planning prompt based on goal analysis.

        Args:
            goal_analysis: Analyzed goal with domain, industry, market info
            context_data: Retrieved context data from memory and web search

        Returns:
            Formatted planning prompt tailored to the specific domain
        """
        domain = goal_analysis.domain
        template = self.get_template(domain)

        # Use the template's get_planning_prompt method
        return template.get_planning_prompt(goal_analysis, context_data)
