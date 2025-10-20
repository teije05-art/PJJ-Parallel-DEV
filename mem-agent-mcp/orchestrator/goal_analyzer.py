"""
Goal Analysis Module for Dynamic Context Selection

This module analyzes user goals to determine relevant domains, industries, and context requirements.
It enables the planning system to select appropriate entities and methodologies based on the
specific goal rather than defaulting to hard-coded KPMG QSR context.
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class GoalAnalysis:
    """Structured analysis of a user's planning goal"""
    domain: str
    industry: str
    market: str
    company_type: str
    objectives: List[str]
    context_entities: List[str]
    methodologies: List[str]
    considerations: List[str]


class GoalAnalyzer:
    """
    Analyzes user goals to determine relevant domains and context requirements.
    
    This enables dynamic context selection and domain-specific planning approaches
    instead of defaulting to KPMG QSR context for all requests.
    """
    
    def __init__(self):
        """Initialize the goal analyzer with domain detection patterns"""
        self.domain_patterns = {
            'healthcare': [
                r'healthcare', r'medical', r'clinical', r'hospital', r'pharmaceutical',
                r'biotech', r'health', r'medicine', r'patient', r'clinical trial',
                r'FDA', r'regulatory approval', r'medical device', r'diagnostic'
            ],
            'technology': [
                r'tech', r'technology', r'software', r'AI', r'ML', r'machine learning',
                r'startup', r'SaaS', r'platform', r'digital', r'cyber', r'data',
                r'cloud', r'API', r'app', r'application', r'development'
            ],
            'manufacturing': [
                r'manufacturing', r'production', r'factory', r'industrial', r'supply chain',
                r'logistics', r'operations', r'plant', r'equipment', r'automation'
            ],
            'retail': [
                r'retail', r'e-commerce', r'online store', r'consumer', r'brand',
                r'marketing', r'sales', r'distribution', r'merchandise'
            ],
            'financial': [
                r'financial', r'banking', r'fintech', r'investment', r'funding',
                r'capital', r'venture', r'private equity', r'wealth management'
            ],
            'qsr': [
                r'QSR', r'quick service restaurant', r'fast food', r'restaurant',
                r'dining', r'food service', r'casual dining', r'food retail'
            ]
        }
        
        self.industry_patterns = {
            'healthcare': ['healthcare', 'medical', 'pharmaceutical', 'biotech'],
            'technology': ['technology', 'software', 'tech', 'AI', 'startup'],
            'manufacturing': ['manufacturing', 'industrial', 'production'],
            'retail': ['retail', 'e-commerce', 'consumer'],
            'financial': ['financial', 'banking', 'fintech'],
            'qsr': ['QSR', 'restaurant', 'food service']
        }
        
        self.market_patterns = {
            'vietnam': [r'vietnam', r'vietnamese'],
            'southeast_asia': [r'southeast asia', r'SEA', r'singapore', r'thailand', r'indonesia', r'malaysia', r'philippines'],
            'asia_pacific': [r'asia pacific', r'APAC', r'china', r'japan', r'south korea'],
            'north_america': [r'north america', r'USA', r'United States', r'canada'],
            'europe': [r'europe', r'EU', r'germany', r'france', r'UK', r'united kingdom'],
            'global': [r'global', r'international', r'worldwide']
        }
        
        self.company_type_patterns = {
            'startup': [r'startup', r'early stage', r'emerging', r'new company'],
            'enterprise': [r'enterprise', r'large company', r'corporation', r'multinational'],
            'sme': [r'SME', r'small business', r'medium business', r'local company'],
            'nonprofit': [r'nonprofit', r'NGO', r'non-profit', r'charity']
        }
    
    def analyze_goal(self, goal: str) -> GoalAnalysis:
        """
        Analyze a user goal to determine relevant domains, industries, and context.
        
        Args:
            goal: The user's planning goal (e.g., "American healthcare company entering Vietnam")
            
        Returns:
            GoalAnalysis object with structured analysis
        """
        goal_lower = goal.lower()
        
        # Detect domain
        domain = self._detect_domain(goal_lower)
        
        # Detect industry
        industry = self._detect_industry(goal_lower)
        
        # Detect market
        market = self._detect_market(goal_lower)
        
        # Detect company type
        company_type = self._detect_company_type(goal_lower)
        
        # Extract objectives
        objectives = self._extract_objectives(goal)
        
        # Determine context entities
        context_entities = self._determine_context_entities(domain, industry, market)
        
        # Determine methodologies
        methodologies = self._determine_methodologies(domain, industry)
        
        # Determine considerations
        considerations = self._determine_considerations(domain, industry, market)
        
        return GoalAnalysis(
            domain=domain,
            industry=industry,
            market=market,
            company_type=company_type,
            objectives=objectives,
            context_entities=context_entities,
            methodologies=methodologies,
            considerations=considerations
        )
    
    def _detect_domain(self, goal_lower: str) -> str:
        """Detect the primary domain from the goal"""
        domain_scores = {}
        
        for domain, patterns in self.domain_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, goal_lower))
                score += matches
            domain_scores[domain] = score
        
        # Return domain with highest score, default to 'general' if no clear match
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0:
                return best_domain
        
        return 'general'
    
    def _detect_industry(self, goal_lower: str) -> str:
        """Detect the industry from the goal"""
        industry_scores = {}
        
        for industry, patterns in self.industry_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, goal_lower))
                score += matches
            industry_scores[industry] = score
        
        if industry_scores:
            best_industry = max(industry_scores, key=industry_scores.get)
            if industry_scores[best_industry] > 0:
                return best_industry
        
        return 'general'
    
    def _detect_market(self, goal_lower: str) -> str:
        """Detect the target market from the goal"""
        market_scores = {}
        
        for market, patterns in self.market_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, goal_lower))
                score += matches
            market_scores[market] = score
        
        if market_scores:
            best_market = max(market_scores, key=market_scores.get)
            if market_scores[best_market] > 0:
                return best_market
        
        return 'global'
    
    def _detect_company_type(self, goal_lower: str) -> str:
        """Detect the company type from the goal"""
        company_type_scores = {}
        
        for company_type, patterns in self.company_type_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, goal_lower))
                score += matches
            company_type_scores[company_type] = score
        
        if company_type_scores:
            best_type = max(company_type_scores, key=company_type_scores.get)
            if company_type_scores[best_type] > 0:
                return best_type
        
        return 'enterprise'
    
    def _extract_objectives(self, goal: str) -> List[str]:
        """Extract specific objectives from the goal"""
        objectives = []
        
        # Common objective patterns
        objective_patterns = [
            r'entering\s+(\w+)',  # "entering Vietnam"
            r'expanding\s+to\s+(\w+)',  # "expanding to Asia"
            r'launching\s+in\s+(\w+)',  # "launching in Vietnam"
            r'market entry',  # market entry
            r'growth strategy',  # growth strategy
            r'business development',  # business development
        ]
        
        for pattern in objective_patterns:
            matches = re.findall(pattern, goal, re.IGNORECASE)
            objectives.extend(matches)
        
        # If no specific objectives found, infer from context
        if not objectives:
            if 'entry' in goal.lower() or 'entering' in goal.lower():
                objectives.append('market entry')
            if 'expansion' in goal.lower() or 'expanding' in goal.lower():
                objectives.append('market expansion')
            if 'launch' in goal.lower() or 'launching' in goal.lower():
                objectives.append('product/service launch')
            if 'strategy' in goal.lower():
                objectives.append('strategic planning')
        
        return objectives if objectives else ['strategic planning']
    
    def _determine_context_entities(self, domain: str, industry: str, market: str) -> List[str]:
        """Determine which entities to retrieve based on domain, industry, and market"""
        entities = []
        
        # Domain-specific entities
        if domain == 'healthcare':
            entities.extend(['healthcare_regulations', 'medical_market_analysis', 'clinical_protocols'])
        elif domain == 'technology':
            entities.extend(['tech_market_analysis', 'startup_ecosystem', 'digital_transformation'])
        elif domain == 'manufacturing':
            entities.extend(['manufacturing_processes', 'supply_chain_analysis', 'industrial_standards'])
        elif domain == 'qsr':
            entities.extend(['KPMG_strategyteam_project'])  # Maintain backward compatibility
        
        # Market-specific entities
        if market == 'vietnam':
            entities.extend(['vietnam_market_analysis', 'vietnamese_regulations'])
        elif market == 'southeast_asia':
            entities.extend(['sea_market_analysis', 'asean_regulations'])
        
        # Always include learning entities
        entities.extend(['successful_patterns', 'planning_errors', 'execution_log'])
        
        return entities
    
    def _determine_methodologies(self, domain: str, industry: str) -> List[str]:
        """Determine appropriate methodologies based on domain and industry"""
        methodologies = []
        
        if domain == 'healthcare':
            methodologies.extend([
                'Clinical Development Framework',
                'Regulatory Compliance Methodology',
                'Healthcare Market Entry Protocol',
                'Medical Device Approval Process'
            ])
        elif domain == 'technology':
            methodologies.extend([
                'Agile Development Framework',
                'Lean Startup Methodology',
                'Product-Market Fit Analysis',
                'Technology Adoption Lifecycle'
            ])
        elif domain == 'manufacturing':
            methodologies.extend([
                'Lean Manufacturing Principles',
                'Six Sigma Methodology',
                'Supply Chain Optimization',
                'Quality Management Systems'
            ])
        elif domain == 'qsr':
            methodologies.extend([
                'KPMG Market Entry Framework',
                'QSR Market Analysis Protocol',
                'Franchise Development Methodology'
            ])
        else:
            methodologies.extend([
                'Strategic Planning Framework',
                'Market Entry Methodology',
                'Risk Assessment Protocol',
                'Competitive Analysis Framework'
            ])
        
        return methodologies
    
    def _determine_considerations(self, domain: str, industry: str, market: str) -> List[str]:
        """Determine key considerations based on domain, industry, and market"""
        considerations = []
        
        # Domain-specific considerations
        if domain == 'healthcare':
            considerations.extend([
                'Regulatory approval requirements',
                'Clinical trial protocols',
                'Patient safety standards',
                'Medical device regulations',
                'Healthcare data privacy'
            ])
        elif domain == 'technology':
            considerations.extend([
                'Technology infrastructure requirements',
                'Data security and privacy',
                'Scalability and performance',
                'User experience design',
                'API and integration capabilities'
            ])
        elif domain == 'manufacturing':
            considerations.extend([
                'Supply chain logistics',
                'Quality control standards',
                'Environmental regulations',
                'Labor and workforce requirements',
                'Equipment and facility needs'
            ])
        
        # Market-specific considerations
        if market == 'vietnam':
            considerations.extend([
                'Vietnamese regulatory environment',
                'Local partnership requirements',
                'Cultural and language considerations',
                'Economic and political stability'
            ])
        elif market == 'southeast_asia':
            considerations.extend([
                'ASEAN regulatory harmonization',
                'Regional trade agreements',
                'Cultural diversity across markets',
                'Infrastructure and logistics'
            ])
        
        return considerations


# Example usage and testing
if __name__ == "__main__":
    analyzer = GoalAnalyzer()
    
    # Test cases
    test_goals = [
        "American healthcare company looking to do business in Vietnam",
        "Tech startup expanding to Southeast Asia",
        "Manufacturing company entering Vietnam market",
        "QSR chain looking to expand to Vietnam"
    ]
    
    for goal in test_goals:
        analysis = analyzer.analyze_goal(goal)
        print(f"\nGoal: {goal}")
        print(f"Domain: {analysis.domain}")
        print(f"Industry: {analysis.industry}")
        print(f"Market: {analysis.market}")
        print(f"Company Type: {analysis.company_type}")
        print(f"Objectives: {analysis.objectives}")
        print(f"Context Entities: {analysis.context_entities}")
        print(f"Methodologies: {analysis.methodologies}")
        print(f"Considerations: {analysis.considerations}")
