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

    Uses context-aware detection to understand compound phrases and avoid false positives
    (e.g., "coffee startup" is QSR, not technology).
    """

    def __init__(self):
        """Initialize the goal analyzer with context-aware domain detection patterns"""

        # PRIMARY INDUSTRY KEYWORDS - High priority, specific to domain
        # These are strong indicators and should be weighted heavily
        self.primary_industry_patterns = {
            'healthcare': [
                r'healthcare', r'medical(?!ly)', r'clinical', r'hospital', r'pharmaceutical',
                r'biotech(?!nology)', r'health(?!y)', r'medicine', r'patient(?!ly)',
                r'clinical trial', r'FDA', r'regulatory approval', r'medical device',
                r'diagnostic', r'physician', r'doctor', r'nurse', r'drug development'
            ],
            'technology': [
                r'software', r'AI(?!\w)', r'machine learning', r'algorithm', r'neural network',
                r'SaaS', r'cloud computing', r'cyber(?!netic)', r'blockchain', r'IoT',
                r'programming', r'developer(?!s)?', r'code(?!d)?', r'technical(?!ly)',
                r'digital platform', r'web application', r'mobile app', r'infrastructure'
            ],
            'manufacturing': [
                r'manufacturing', r'production(?!ly)', r'factory', r'industrial', r'supply chain',
                r'logistics', r'plant(?!ing)', r'equipment(?!s)?', r'automation', r'assembly',
                r'goods production', r'mass production', r'fabrication', r'forge',
                r'factory setup', r'production line'
            ],
            'retail': [
                r'retail(?!ing)?', r'e-commerce', r'online store', r'consumer(?!s)?', r'brand(?!s)?',
                r'merchandise', r'retail network', r'distribution', r'store(?!d|y)',
                r'shopping', r'customer service', r'inventory management'
            ],
            'financial': [
                r'financial services', r'banking', r'fintech', r'investment(?!s)?', r'fund(?!s)?',
                r'capital(?!s)?', r'venture capital', r'wealth management', r'insurance',
                r'mortgage', r'lending', r'payment', r'cryptocurrency'
            ],
            'qsr': [
                r'restaurant', r'cafe\b', r'café', r'coffee shop', r'coffee(?! machine)',
                r'QSR', r'quick service', r'fast food', r'food service', r'casual dining',
                r'beverage', r'food retail', r'dining', r'bistro', r'bar\b', r'pub\b',
                r'menu', r'cuisine', r'kitchen', r'chef', r'food preparation', r'culinary'
            ]
        }

        # CONTEXTUAL MODIFIERS - Words that provide context for compound phrases
        # Used to disambiguate cases like "coffee startup" vs "tech startup"
        self.contextual_modifiers = {
            'qsr': [r'coffee', r'food', r'beverage', r'dining', r'restaurant', r'cafe', r'café'],
            'technology': [r'AI', r'tech', r'software', r'digital', r'platform', r'app', r'web'],
            'healthcare': [r'medical', r'health', r'pharmaceutical', r'clinical'],
            'manufacturing': [r'industrial', r'factory', r'production', r'supply chain'],
            'retail': [r'e-commerce', r'online', r'brand', r'consumer']
        }

        # PATTERN WEIGHTS - Higher weight = stronger indicator
        self.pattern_weights = {
            'primary': 3.0,        # Primary industry keywords
            'secondary': 1.0,      # Secondary patterns (like "startup" alone)
            'contextual': 2.0      # Context modifiers that clarify meaning
        }

        # BACKWARDS COMPATIBILITY - Keep simple pattern lists for other methods
        self.domain_patterns = {
            'healthcare': [
                r'healthcare', r'medical', r'clinical', r'hospital', r'pharmaceutical',
                r'biotech', r'health', r'medicine', r'patient', r'clinical trial',
                r'FDA', r'regulatory approval', r'medical device', r'diagnostic'
            ],
            'technology': [
                r'software', r'AI', r'ML', r'machine learning',
                r'SaaS', r'platform', r'digital', r'cyber', r'data',
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
                r'dining', r'food service', r'casual dining', r'food retail',
                r'coffee', r'cafe', r'café', r'beverage'
            ]
        }

        self.industry_patterns = {
            'healthcare': ['healthcare', 'medical', 'pharmaceutical', 'biotech', 'clinical'],
            'technology': ['software', 'technology', 'tech', 'AI', 'platform', 'digital'],
            'manufacturing': ['manufacturing', 'industrial', 'production', 'factory'],
            'retail': ['retail', 'e-commerce', 'consumer', 'brand'],
            'financial': ['financial', 'banking', 'fintech', 'investment'],
            'qsr': ['restaurant', 'food service', 'coffee', 'cafe', 'dining', 'beverage']
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

        Uses LLM-powered analysis for better understanding of natural language goals,
        with fallback to keyword matching if LLM is unavailable.

        Args:
            goal: The user's planning goal (e.g., "American healthcare company entering Vietnam")

        Returns:
            GoalAnalysis object with structured analysis
        """
        # STEP 1: Try LLM-powered analysis first (more accurate)
        analysis = self._analyze_goal_with_llm(goal)

        # STEP 2: If LLM analysis succeeded, use it with fallback for missing fields
        if analysis:
            return analysis

        # STEP 3: Fallback to keyword matching if LLM fails
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

    def _analyze_goal_with_llm(self, goal: str) -> Optional[GoalAnalysis]:
        """
        Use Fireworks/Llama LLM to analyze goal for domain, industry, company, market.

        This provides more accurate understanding of natural language goals compared
        to keyword matching. Falls back gracefully if LLM is unavailable.

        Args:
            goal: The user's planning goal

        Returns:
            GoalAnalysis object if successful, None if LLM fails (will use fallback)
        """
        try:
            # Import here to avoid circular dependencies
            from agent.model import get_model_response, create_fireworks_client
            from agent.schemas import ChatMessage, Role

            system_prompt = """You are an expert business analyst. Analyze planning goals to extract:
1. Domain: One of [healthcare, technology, manufacturing, retail, financial, qsr]
2. Industry: Specific industry (e.g., pharmaceutical, e-commerce, QSR)
3. Company: Company name if mentioned
4. Market: Geographic market (e.g., vietnam, southeast_asia, north_america)
5. Company Type: One of [startup, enterprise, sme, nonprofit]
6. Objectives: List of 2-3 key objectives

Return a structured response with clear key-value pairs."""

            user_prompt = f"""Analyze this planning goal and extract the business context:

GOAL: {goal}

Extract and return:
- DOMAIN: [one of: healthcare, technology, manufacturing, retail, financial, qsr, or general]
- INDUSTRY: [specific industry]
- COMPANY: [company name if mentioned, or UNKNOWN]
- MARKET: [one of: vietnam, southeast_asia, asia_pacific, north_america, europe, global]
- COMPANY_TYPE: [one of: startup, enterprise, sme, nonprofit]
- OBJECTIVES: [comma-separated list of 2-3 objectives]

Be precise. Return ONLY the key-value pairs, no explanation."""

            # Create LLM call
            messages = [
                ChatMessage(role=Role.SYSTEM, content=system_prompt),
                ChatMessage(role=Role.USER, content=user_prompt)
            ]

            # Try to use Fireworks client
            try:
                client = create_fireworks_client()
                response = get_model_response(
                    messages=messages,
                    client=client,
                    use_fireworks=True
                )
            except:
                # Fallback to OpenRouter if Fireworks fails
                response = get_model_response(
                    messages=messages,
                    use_fireworks=False
                )

            # Parse the LLM response
            return self._parse_llm_analysis(response)

        except Exception as e:
            print(f"   ℹ️ LLM goal analysis unavailable: {type(e).__name__}")
            return None

    def _parse_llm_analysis(self, response: str) -> Optional[GoalAnalysis]:
        """
        Parse LLM response to extract domain, industry, market, etc.

        Handles various response formats and extracts key information.

        Args:
            response: Raw LLM response text

        Returns:
            GoalAnalysis object if parsing succeeds, None otherwise
        """
        try:
            response_lower = response.lower()

            # Extract DOMAIN
            domain = self._extract_field_value(response, "DOMAIN", [
                'healthcare', 'technology', 'manufacturing', 'retail', 'financial', 'qsr', 'general'
            ]) or 'general'

            # Extract INDUSTRY
            industry = self._extract_field_value(response, "INDUSTRY", [
                'healthcare', 'pharmaceutical', 'technology', 'software', 'manufacturing',
                'retail', 'e-commerce', 'qsr', 'quick_service', 'financial', 'banking'
            ]) or domain

            # Extract MARKET
            market = self._extract_field_value(response, "MARKET", [
                'vietnam', 'southeast_asia', 'asia_pacific', 'north_america', 'europe', 'global'
            ]) or 'global'

            # Extract COMPANY_TYPE
            company_type = self._extract_field_value(response, "COMPANY_TYPE", [
                'startup', 'enterprise', 'sme', 'nonprofit'
            ]) or 'enterprise'

            # Extract OBJECTIVES
            objectives_match = re.search(r'OBJECTIVES?\s*:?\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
            objectives = []
            if objectives_match:
                objectives_text = objectives_match.group(1).strip()
                objectives = [obj.strip() for obj in objectives_text.split(',')]
            if not objectives:
                objectives = ['strategic planning']

            # Extract context entities, methodologies, considerations using detected values
            context_entities = self._determine_context_entities(domain, industry, market)
            methodologies = self._determine_methodologies(domain, industry)
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

        except Exception as e:
            print(f"   ℹ️ LLM response parsing failed: {str(e)}")
            return None

    def _extract_field_value(self, response: str, field_name: str, valid_values: List[str]) -> Optional[str]:
        """
        Extract a field value from LLM response and validate against valid options.

        Args:
            response: LLM response text
            field_name: Field to extract (e.g., "DOMAIN", "MARKET")
            valid_values: List of valid values for this field

        Returns:
            Matched value if found, None otherwise
        """
        # Look for pattern like "DOMAIN: retail" or "DOMAIN=retail"
        pattern = f'{field_name}\\s*[:=]?\\s*([^\\n,]+)'
        match = re.search(pattern, response, re.IGNORECASE)

        if match:
            value = match.group(1).strip().lower()

            # Check if value matches any valid option
            for valid in valid_values:
                if valid in value or value in valid:
                    return valid

        return None

    def _detect_domain(self, goal_lower: str) -> str:
        """
        Detect the primary domain from the goal using context-aware detection.

        This method:
        1. Looks for primary industry keywords (weighted heavily)
        2. Checks contextual modifiers that clarify compound phrases
        3. Falls back to secondary patterns if needed
        4. Avoids false positives from generic terms like "startup"

        Returns the domain with the highest weighted score.
        """
        domain_scores = {}

        # STEP 1: Score primary industry patterns (high weight)
        for domain, patterns in self.primary_industry_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, goal_lower, re.IGNORECASE))
                score += matches * self.pattern_weights['primary']
            domain_scores[domain] = score

        # STEP 2: Check contextual modifiers to clarify meaning
        # Example: "coffee startup" should boost QSR, not technology
        for domain, modifiers in self.contextual_modifiers.items():
            if domain not in domain_scores:
                domain_scores[domain] = 0

            for modifier in modifiers:
                if re.search(modifier, goal_lower, re.IGNORECASE):
                    domain_scores[domain] += self.pattern_weights['contextual']

        # STEP 3: If no primary keywords found, use secondary patterns as fallback
        if max(domain_scores.values()) == 0:
            for domain, patterns in self.domain_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, goal_lower, re.IGNORECASE))
                    score += matches * self.pattern_weights['secondary']
                domain_scores[domain] = score

        # STEP 4: Return domain with highest score
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0:
                return best_domain

        return 'general'
    
    def _detect_industry(self, goal_lower: str) -> str:
        """
        Detect the industry from the goal using context-aware detection.

        Similar to domain detection but focuses on specific industries.
        Also uses primary patterns with higher weights.
        """
        industry_scores = {}

        # STEP 1: Score using primary industry patterns (high weight)
        for industry, patterns in self.primary_industry_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, goal_lower, re.IGNORECASE))
                score += matches * self.pattern_weights['primary']
            industry_scores[industry] = score

        # STEP 2: Add contextual modifier scores
        for domain, modifiers in self.contextual_modifiers.items():
            if domain not in industry_scores:
                industry_scores[domain] = 0

            for modifier in modifiers:
                if re.search(modifier, goal_lower, re.IGNORECASE):
                    industry_scores[domain] += self.pattern_weights['contextual']

        # STEP 3: Fallback to simple patterns if needed
        if max(industry_scores.values()) == 0:
            for industry, patterns in self.industry_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, goal_lower, re.IGNORECASE))
                    score += matches * self.pattern_weights['secondary']
                industry_scores[industry] = score

        # STEP 4: Return industry with highest score
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
        """Return only learning entities - user selections handled by context_manager.

        ISSUE FIXED (Oct 31, 2025):
        Previously returned hardcoded entity names like 'tech_market_analysis', 'startup_ecosystem'
        that often didn't exist in the user's memory, overriding user selections completely.

        Solution: Return only learning entities that are always relevant. User-specific entities
        are selected separately via the frontend proposal flow. The context_manager receives
        the user's actual selections and handles retrieval accordingly.

        Args:
            domain: Detected domain (for context, not entity selection)
            industry: Detected industry (for context, not entity selection)
            market: Detected market (for context, not entity selection)

        Returns:
            List of learning entity names for system improvement tracking
        """
        # Return only learning entities - these track system improvements across planning cycles
        # User-specific entities are selected by the frontend and passed to context_manager
        return ['successful_patterns', 'planning_errors', 'execution_log', 'agent_performance']
    
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
