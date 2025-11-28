"""
Domain-Specific Planning Templates Module

This module provides domain-specialized planning templates that maintain high quality
and specificity while being tailored to different industries and markets.

Each template is implemented as a separate class, enabling:
- Independent maintenance and testing
- Clear separation of domain-specific logic
- Easy extension for new domains
- Single Responsibility Principle
"""

from .base_template import BaseTemplate
from .healthcare_template import HealthcareTemplate
from .technology_template import TechnologyTemplate
from .manufacturing_template import ManufacturingTemplate
from .qsr_template import QSRTemplate
from .retail_template import RetailTemplate
from .financial_template import FinancialTemplate
from .general_template import GeneralTemplate
from .template_selector import TemplateSelector

__all__ = [
    'BaseTemplate',
    'HealthcareTemplate',
    'TechnologyTemplate',
    'ManufacturingTemplate',
    'QSRTemplate',
    'RetailTemplate',
    'FinancialTemplate',
    'GeneralTemplate',
    'TemplateSelector'
]
