"""
ResearchAgent - Iterative Web Search Specialist

Handles intelligent, iterative web search:
1. Analyze gaps/questions
2. Perform initial search with specific queries
3. Analyze results for key data/numbers
4. Generate next search query based on findings
5. Iterate until gaps filled or max iterations reached
6. Return structured results with sources and data points

Key Feature: Focuses on finding KEY DATA and NUMBERS, not generic information
"""

import json
import os
import requests
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from fireworks.client import Fireworks
import re


@dataclass
class ResearchResult:
    """Structured research result"""
    summary: str
    sources: List[str]
    key_data_points: List[str]
    iterations_used: int
    coverage: float  # 0.0-1.0 estimated completeness
    gaps_filled: List[str]
    gaps_remaining: List[str]


# Goal Type Mapping - defines required data categories for different goal types
GOAL_TYPE_DATA_CATEGORIES = {
    # Market & Expansion
    "market_expansion": [
        "market_size", "market_growth_rate", "competitor_landscape",
        "regulatory_environment", "target_demographics", "distribution_channels",
        "pricing_trends", "customer_pain_points", "market_entry_barriers"
    ],
    "market_analysis": [
        "total_addressable_market", "competitive_positioning", "market_segments",
        "customer_preferences", "industry_trends", "supply_chain_dynamics"
    ],
    "competitive_analysis": [
        "competitor_strengths", "competitor_weaknesses", "market_share_distribution",
        "competitive_advantages", "pricing_strategy_comparison", "feature_comparison"
    ],

    # Product & Development
    "product_development": [
        "market_need_validation", "technology_requirements", "competitive_features",
        "development_timeline", "resource_requirements", "customer_feedback",
        "market_adoption_rates", "technology_maturity"
    ],
    "product_improvement": [
        "user_feedback", "feature_requests", "usage_metrics", "pain_points",
        "competitor_feature_analysis", "industry_best_practices"
    ],
    "product_launch": [
        "market_readiness", "go_to_market_strategy", "pricing_models",
        "customer_acquisition_costs", "distribution_partnerships", "regulatory_approvals"
    ],

    # Cost & Operations
    "cost_optimization": [
        "cost_drivers", "industry_benchmarks", "process_improvement_opportunities",
        "vendor_alternatives", "automation_possibilities", "economies_of_scale",
        "supply_chain_efficiency", "labor_market_trends"
    ],
    "operational_improvement": [
        "process_efficiency_metrics", "industry_standards", "technology_solutions",
        "best_practices", "risk_management_strategies", "quality_metrics"
    ],
    "supply_chain_optimization": [
        "supplier_options", "logistics_costs", "inventory_management_strategies",
        "supplier_reliability", "regional_sourcing_opportunities", "sustainability_options"
    ],

    # Strategy & Planning
    "business_strategy": [
        "market_trends", "emerging_opportunities", "strategic_threats",
        "stakeholder_interests", "regulatory_landscape", "competitive_positioning",
        "financial_metrics", "growth_opportunities"
    ],
    "diversification": [
        "adjacent_markets", "customer_overlap", "technology_transferability",
        "new_market_regulations", "competitive_intensity", "profitability_potential"
    ],
    "partnership_strategy": [
        "potential_partners", "partnership_benefits", "market_dynamics",
        "partner_track_records", "integration_complexity", "revenue_sharing_models"
    ],

    # Financial & Risk
    "financial_analysis": [
        "revenue_models", "profitability_metrics", "cost_structures",
        "financial_benchmarks", "funding_landscape", "valuation_trends"
    ],
    "risk_management": [
        "industry_risks", "competitive_threats", "regulatory_risks",
        "market_volatility", "operational_vulnerabilities", "mitigation_strategies"
    ],
    "investment_evaluation": [
        "market_potential", "competitive_landscape", "management_track_record",
        "financial_projections", "exit_opportunities", "industry_growth_rates"
    ],

    # Organization & People
    "organizational_restructuring": [
        "role_requirements", "talent_market_availability", "industry_salary_benchmarks",
        "organizational_best_practices", "change_management_strategies", "skill_gaps"
    ],
    "talent_acquisition": [
        "talent_availability", "skill_requirements", "compensation_benchmarks",
        "recruitment_strategies", "industry_talent_distribution", "competitor_compensation"
    ],
    "training_development": [
        "skill_gaps", "training_methodologies", "industry_best_practices",
        "technology_platforms", "learning_outcomes_data", "cost_comparisons"
    ],

    # Technology & Digital
    "technology_implementation": [
        "technology_options", "implementation_requirements", "vendor_reputation",
        "deployment_timelines", "integration_complexity", "total_cost_of_ownership",
        "industry_benchmarks", "success_rates"
    ],
    "digital_transformation": [
        "market_capabilities", "technology_trends", "implementation_roadmaps",
        "change_management_approaches", "roi_benchmarks", "industry_case_studies"
    ],
    "cybersecurity_strategy": [
        "threat_landscape", "industry_compliance_requirements", "security_solutions",
        "risk_assessment_frameworks", "incident_response_best_practices"
    ],

    # Default/Fallback
    "general_research": [
        "market_data", "competitive_information", "industry_trends",
        "regulatory_information", "financial_metrics", "best_practices"
    ]
}


class ResearchAgent:
    """
    Performs iterative web research focused on finding specific data and numbers.

    Example usage:
        agent = ResearchAgent()
        result = agent.research(
            gaps=[
                "SaaS growth trends Q1 2025",
                "Competitor market moves",
                "PLG methodology effectiveness"
            ],
            max_iterations=3
        )
    """

    def __init__(self, verbose: bool = False, goal: str = None, goal_analysis: dict = None):
        self.verbose = verbose
        self.goal = goal
        self.goal_analysis = goal_analysis or {}
        self.search_history: List[Dict] = []

        # Validate JINA_API_KEY exists
        self.jina_api_key = os.getenv('JINA_API_KEY')
        if not self.jina_api_key:
            raise ValueError(
                "JINA_API_KEY environment variable not set. "
                "Get a free key at https://jina.ai (no credit card needed). "
                "Set it as: export JINA_API_KEY=sk_..."
            )

        # Initialize Fireworks client for LLM operations
        try:
            self.fireworks_client = Fireworks()
        except Exception as e:
            if self.verbose:
                print(f"Warning: Fireworks client initialization failed: {e}")
            self.fireworks_client = None

    def research(
        self,
        goal: str = None,
        gaps: List[str] = None,
        max_iterations: int = 10,  # INCREASED from 3 to 10 for extensive research
        results_per_search: int = 8,  # INCREASED from 5 to 8 for more results per search
        goal_analysis: dict = None
    ) -> ResearchResult:
        """
        Perform EXTENSIVE iterative research to fill identified gaps or achieve a goal.

        Supports two modes:
        1. Goal-aware mode: Research guided by goal type and required data categories
        2. Gap-based mode: Traditional mode targeting specific knowledge gaps (backward compatible)

        Searches from multiple angles:
        1. Market size and growth trends
        2. Industry-specific metrics and KPIs
        3. Competitive landscape analysis
        4. Economic indicators (macro/micro)
        5. Healthcare trends (if applicable)
        6. Demographic data
        7. Adoption rates and penetration
        8. Forward-looking forecasts

        Args:
            goal: The planning goal/objective (activates goal-aware research)
            gaps: List of specific gaps/questions to research (backward compatible)
            max_iterations: Maximum number of search iterations (default 10 for extensive coverage)
            results_per_search: Number of results per search query
            goal_analysis: Optional analysis of the goal (domain, industry, market info)

        Returns:
            ResearchResult with summary, sources, and key data points
        """
        # Use provided parameters or fall back to instance attributes
        goal = goal or self.goal
        goal_analysis = goal_analysis or self.goal_analysis
        gaps = gaps or []

        if self.verbose:
            print(f"\n🔍 ResearchAgent Starting (EXTENSIVE MODE)")
            print(f"   Gaps to fill: {gaps}")
            print(f"   Max iterations: {max_iterations} (extensive search)")
            print(f"   Results per search: {results_per_search}\n")

        # Track what we've found and what we still need
        remaining_gaps = set(gaps)
        all_sources = set()  # Use set to prevent duplicates
        all_data_points = []
        search_queries = []
        iteration = 0
        data_point_count_last_iteration = 0

        # Generate MULTI-ANGLE search queries from gaps
        initial_queries = self._generate_comprehensive_queries(gaps)
        query_queue = list(initial_queries)

        # Iterative search loop - continues until gaps filled OR max iterations
        while query_queue and iteration < max_iterations:
            iteration += 1
            current_query = query_queue.pop(0)

            if self.verbose:
                print(f"📍 Iteration {iteration}/{max_iterations}")
                print(f"   Query: {current_query}")

            # Perform search
            try:
                results = self._search_and_extract(current_query, results_per_search)
                search_queries.append(current_query)
                all_sources.update(results.get("sources", []))  # Use update for set
                data_points = results.get("data_points", [])
                all_data_points.extend(data_points)

                if self.verbose:
                    print(f"   Found {len(data_points)} data points from this query")
                    if data_points:
                        print(f"   Examples: {data_points[:2]}")

                # If we found good data, analyze and generate deeper queries
                if data_points:
                    # Mark gaps as making progress (we found relevant data)
                    gaps_filled_this_iteration = self._analyze_findings_with_data(
                        current_query,
                        data_points,
                        remaining_gaps
                    )

                    # Update remaining gaps
                    for gap in gaps_filled_this_iteration:
                        remaining_gaps.discard(gap)

                    # Generate follow-up queries to drill deeper
                    if remaining_gaps and iteration < max_iterations:
                        follow_ups = self._generate_deep_follow_ups(
                            current_query,
                            data_points,
                            remaining_gaps,
                            all_data_points
                        )
                        query_queue.extend(follow_ups)
                        if self.verbose and follow_ups:
                            print(f"   → {len(follow_ups)} follow-up queries queued")
                else:
                    # No data found with this query, try alternative search angles
                    if remaining_gaps and iteration < max_iterations:
                        alternative_queries = self._generate_alternative_angles(
                            current_query,
                            list(remaining_gaps)[0],
                            all_data_points
                        )
                        query_queue.extend(alternative_queries)
                        if self.verbose:
                            print(f"   No data found. Trying {len(alternative_queries)} alternative angles...")

                # Check for progress stagnation - if no new data in last 2 iterations, try new angle
                if len(all_data_points) == data_point_count_last_iteration and iteration % 2 == 0:
                    if remaining_gaps:
                        stagnation_queries = self._generate_breakthrough_queries(
                            list(remaining_gaps)[:2]  # Focus on first 2 gaps
                        )
                        query_queue.extend(stagnation_queries)
                        if self.verbose:
                            print(f"   No progress detected. Injecting {len(stagnation_queries)} breakthrough queries...")

                data_point_count_last_iteration = len(all_data_points)

            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️  Search error: {str(e)}")
                continue

        # Compile results
        summary = self._synthesize_summary(
            search_queries,
            all_data_points,
            list(all_sources)
        )

        # Calculate coverage based on ACTUAL DATA FOUND + gaps filled
        # Coverage = (data_point_count / expected_data_points) + (gaps_filled / total_gaps)
        coverage = self._estimate_coverage_extensive(gaps, remaining_gaps, all_data_points)

        if self.verbose:
            print(f"\n✅ Research Complete (EXTENSIVE MODE)")
            print(f"   Iterations used: {iteration}")
            print(f"   Coverage: {coverage:.0%}")
            print(f"   Data points found: {len(all_data_points)}")
            print(f"   Unique sources: {len(all_sources)}")
            print(f"   Gaps filled: {len(gaps) - len(remaining_gaps)}/{len(gaps)}")
            print(f"   Remaining gaps: {remaining_gaps}\n")

        return ResearchResult(
            summary=summary,
            sources=list(all_sources),  # Already deduplicated (was set)
            key_data_points=all_data_points,
            iterations_used=iteration,
            coverage=coverage,
            gaps_filled=list(set(gaps) - remaining_gaps),
            gaps_remaining=list(remaining_gaps)
        )

    def _classify_goal_type(self) -> str:
        """
        Use LLM to classify the goal into one of the predefined goal types.
        Prevents hallucination by constraining to known categories.

        Returns:
            Goal type string from GOAL_TYPE_DATA_CATEGORIES keys, or "general_research"
        """
        if not self.goal or not self.fireworks_client:
            return "general_research"

        try:
            goal_types_list = ", ".join(GOAL_TYPE_DATA_CATEGORIES.keys())

            prompt = f"""
Classify this planning goal into ONE of these goal types:
{goal_types_list}

Goal: {self.goal}

Additional context: {self.goal_analysis}

Respond with ONLY the goal type name (no explanation, no markdown).
If none fit exactly, choose the closest match.
If unsure, respond with: general_research
"""

            response = self.fireworks_client.chat.completions.create(
                model="accounts/fireworks/models/llama-v3p3-70b-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=50
            )

            classified_type = response.choices[0].message.content.strip().lower()

            # Validate the response is in our known types
            if classified_type in GOAL_TYPE_DATA_CATEGORIES:
                if self.verbose:
                    print(f"   Goal classified as: {classified_type}")
                return classified_type
            else:
                if self.verbose:
                    print(f"   Classification '{classified_type}' not recognized, using general_research")
                return "general_research"

        except Exception as e:
            if self.verbose:
                print(f"   Goal classification failed: {e}, using general_research")
            return "general_research"

    def _get_required_data_categories(self, goal_type: str) -> List[str]:
        """
        Get the required data categories for a specific goal type.

        Supports mixed approach: hardcoded defaults + configuration-driven overrides

        Args:
            goal_type: One of the keys in GOAL_TYPE_DATA_CATEGORIES

        Returns:
            List of required data categories for this goal type
        """
        # Return hardcoded list for goal type, or general_research as fallback
        return GOAL_TYPE_DATA_CATEGORIES.get(goal_type, GOAL_TYPE_DATA_CATEGORIES["general_research"])

    def _generate_comprehensive_queries(self, gaps: List[str]) -> List[str]:
        """
        Generate COMPREHENSIVE multi-angle queries from gaps.

        For each gap, generate 3-4 queries from different angles:
        1. Market size and growth
        2. Industry metrics and KPIs
        3. Competitive/comparative analysis
        4. Demographic and trend data (if healthcare/consumer topic)
        """
        queries = []

        for gap in gaps:
            gap_lower = gap.lower()

            # ANGLE 1: Market Size & Growth Trends
            queries.append(f"{gap} market size growth rate 2024 2025")
            queries.append(f"{gap} market value CAGR forecast")

            # ANGLE 2: Industry Metrics & KPIs
            queries.append(f"{gap} industry metrics statistics data")
            queries.append(f"{gap} key performance indicators benchmarks")

            # ANGLE 3: Competitive Analysis
            queries.append(f"{gap} competitive analysis market share")
            queries.append(f"{gap} competitor comparison landscape")

            # ANGLE 4: Healthcare-specific (if applicable)
            if any(term in gap_lower for term in ["health", "medical", "disease", "patient", "treatment", "diagnostic", "drug", "therapy"]):
                queries.append(f"{gap} patient adoption rates penetration")
                queries.append(f"{gap} clinical efficacy effectiveness outcomes")
                queries.append(f"{gap} healthcare spending adoption metrics")
                queries.append(f"{gap} demographic prevalence epidemiology")
                queries.append(f"{gap} regulatory approval status guidelines")

            # ANGLE 5: Economic Indicators (for market/business gaps)
            if any(term in gap_lower for term in ["market", "growth", "business", "revenue", "sales", "economic", "financial"]):
                queries.append(f"{gap} economic impact ROI financial metrics")
                queries.append(f"{gap} spending distribution consumer behavior")
                queries.append(f"{gap} pricing trends unit economics")

            # ANGLE 6: Demographic Data
            queries.append(f"{gap} demographic breakdown user adoption")
            queries.append(f"{gap} penetration rate by segment region")

            # ANGLE 7: Forward-looking research
            queries.append(f"{gap} forecast predictions trends 2025 2026")
            queries.append(f"{gap} emerging trends future outlook")

        return queries

    def _generate_queries_from_gaps(self, gaps: List[str]) -> List[str]:
        """Convert gaps into specific, searchable queries. [LEGACY - use _generate_comprehensive_queries]"""
        queries = []

        for gap in gaps:
            # Make gaps into specific search queries
            # Remove generic words, add specificity

            if "trend" in gap.lower() or "what's" in gap.lower():
                # Trends → Add "2024" or "2025"
                if "2024" not in gap and "2025" not in gap:
                    query = f"{gap} 2024 2025"
                else:
                    query = gap
            elif "competitor" in gap.lower() or "how" in gap.lower():
                # Competitor/how → Add "best practices" or "case study"
                query = f"{gap} case study best practices"
            elif "effectiveness" in gap.lower() or "work" in gap.lower():
                # Effectiveness → Add "metrics" or "results"
                query = f"{gap} metrics results data"
            else:
                # Default: add context
                query = f"{gap} data statistics metrics"

            queries.append(query)

        return queries

    def _search_jina(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search using Jina.ai/Reader endpoint - semantic search with AI-extracted content.

        Endpoint: https://s.jina.ai/
        Returns: List of results with title, url, and cleaned content

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of dicts with title, url, content, source
        """
        endpoint = "https://s.jina.ai/"

        headers = {
            "Authorization": f"Bearer {self.jina_api_key}",
            "Accept": "application/json"
        }

        params = {
            "q": query,
            "limit": max_results
        }

        try:
            response = requests.post(endpoint, headers=headers, json=params, timeout=30)
            response.raise_for_status()

            results = []
            response_data = response.json()

            # Parse Jina response structure
            for item in response_data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),  # AI-extracted clean text from Jina
                    "source": item.get("source", "unknown")
                })

            return results

        except requests.exceptions.RequestException as e:
            if self.verbose:
                print(f"   Jina API error for query '{query}': {e}")
            return []

    def _search_and_extract(
        self,
        query: str,
        num_results: int = 5
    ) -> Dict:
        """
        Perform web search using Jina and extract key data/numbers.

        Returns dict with:
            - sources: list of URLs
            - data_points: list of key data/numbers found
            - raw_results: raw search results for analysis
        """

        try:
            # Perform search using Jina
            results = self._search_jina(query, max_results=num_results)

            sources = []
            data_points = []

            for result in results:
                url = result.get("url", "")
                title = result.get("title", "")
                content = result.get("content", "")  # Jina returns extracted content

                if url:
                    sources.append(url)

                # Extract data points (numbers, percentages, stats)
                extracted = self._extract_data_points(title, content)
                data_points.extend(extracted)

            return {
                "sources": sources,
                "data_points": data_points,
                "raw_results": results
            }

        except Exception as e:
            if self.verbose:
                print(f"   Search and extract error: {e}")
            return {
                "sources": [],
                "data_points": [],
                "raw_results": [],
                "error": str(e)
            }

    def _extract_data_points(self, title: str, body: str) -> List[str]:
        """
        Extract COMPREHENSIVE data points and numbers from search results.

        Looks for:
        - Percentages and rates
        - Numbers with units and context
        - Financial metrics (revenue, spending, funding)
        - Healthcare metrics (patient numbers, adoption rates, clinical outcomes)
        - Demographic data
        - Market/competitive data
        - Economic indicators
        - Time-based trends
        - Key statistics and benchmarks
        """

        data_points = []
        combined_text = f"{title}. {body}"

        # Pattern 1: Percentages (23%, 45.6%, -15%)
        percentage_matches = re.findall(r'[-]?\d+\.?\d*%', combined_text)
        for match in percentage_matches:
            idx = combined_text.find(match)
            context = combined_text[max(0, idx-40):min(len(combined_text), idx+40)]
            data_points.append(f"{match} {context.strip()}")

        # Pattern 2: Growth/decline patterns
        growth_pattern = r'(?:grew|increased|decreased|growth|decline|growth rate|CAGR)\s+(?:by|of|at|to)?\s+(\d+\.?\d*)\s*(%|\$)?'
        growth_matches = re.findall(growth_pattern, combined_text, re.IGNORECASE)
        for match in growth_matches:
            data_points.append(f"Growth: {match[0]}{match[1] if match[1] else '%'}")

        # Pattern 3: Dollar amounts and financial metrics
        dollar_pattern = r'\$\d+\.?\d*\s*(?:billion|million|thousand|B|M|K)?'
        dollar_matches = re.findall(dollar_pattern, combined_text)
        for match in set(dollar_matches):
            data_points.append(f"Value: {match}")

        # Pattern 4: Business metrics (ARR, MRR, CAC, LTV, CLTV, etc.)
        metric_pattern = r'(ARR|MRR|CAC|LTV|CLTV|ROI|margin|market share|reach|penetration)\s+(?:is|of|at|=|:)?\s*([^\.\,;]{1,40})'
        metric_matches = re.findall(metric_pattern, combined_text, re.IGNORECASE)
        for match in metric_matches:
            data_points.append(f"{match[0]}: {match[1].strip()}")

        # Pattern 5: Healthcare-specific metrics
        healthcare_metrics = r'(adoption rate|patient|patients|mortality|morbidity|prevalence|incidence|efficacy|effectiveness|clinical|diagnostic|treatment|diagnosis rate|cure rate|disease rate|infection rate|complication rate|hospitalization|emergency|bed occupancy)\s*(?:is|=|of|at|:)?\s*([^\.\,;]{1,50})'
        healthcare_matches = re.findall(healthcare_metrics, combined_text, re.IGNORECASE)
        for match in healthcare_matches:
            data_points.append(f"{match[0]}: {match[1].strip()}")

        # Pattern 6: Demographic data
        demographic_pattern = r'(age|population|demographic|gender|income|education|rural|urban|region|country|segment|cohort|user|consumer|customer)\s+(?:is|=|of|at|:|was)\s+([^\.\,;]{1,50})'
        demographic_matches = re.findall(demographic_pattern, combined_text, re.IGNORECASE)
        for match in demographic_matches:
            data_points.append(f"{match[0]}: {match[1].strip()}")

        # Pattern 7: Numeric measurements with units (e.g., 5 million people, 500 patients)
        numeric_units = r'(\d+\.?\d*)\s*(million|thousand|billion|thousand|hundred|patients|people|users|customers|companies|hospitals|clinics|doctors|nurses)'
        numeric_matches = re.findall(numeric_units, combined_text, re.IGNORECASE)
        for match in numeric_matches:
            data_points.append(f"Count: {match[0]} {match[1]}")

        # Pattern 8: Market/competitive data
        market_pattern = r'(market size|market value|market share|competitor|rank|position|leader|market leader|market growth|market penetration)\s*(?:is|=|:)?\s*([^\.\,;]{1,50})'
        market_matches = re.findall(market_pattern, combined_text, re.IGNORECASE)
        for match in market_matches:
            data_points.append(f"Market: {match[0]} = {match[1].strip()}")

        # Pattern 9: Time-based references (data from specific years)
        time_pattern = r'(2024|2025|2023|2022|2021|Q[1-4]\s+\d{4}|in \d{4}|by \d{4}|since \d{4})\s+([^\.\,;]{1,50})'
        time_matches = re.findall(time_pattern, combined_text, re.IGNORECASE)
        for match in time_matches:
            data_points.append(f"{match[0]}: {match[1].strip()}")

        # Pattern 10: Rankings and comparisons
        ranking_pattern = r'(?:ranked|top|#|number|position|leader)\s+(\d+)(?:st|nd|rd|th)?(?:\s+(?:in|among|out of)\s+([^\.\,;]{1,40}))?'
        ranking_matches = re.findall(ranking_pattern, combined_text, re.IGNORECASE)
        for match in ranking_matches:
            if match[1]:
                data_points.append(f"Rank: #{match[0]} {match[1].strip()}")
            else:
                data_points.append(f"Rank: #{match[0]}")

        # Pattern 11: Forecast and projections
        forecast_pattern = r'(forecast|projection|expected|projected|anticipated)\s+(?:to|be|of|is)?\s+([^\.\,;]{1,60})'
        forecast_matches = re.findall(forecast_pattern, combined_text, re.IGNORECASE)
        for match in forecast_matches:
            data_points.append(f"Forecast: {match[1].strip()}")

        # Clean up and deduplicate
        cleaned_points = []
        for point in data_points:
            # Remove very short or obviously incomplete extractions
            if len(point) > 10:
                cleaned_points.append(point.strip())

        return list(set(cleaned_points))  # Deduplicate

    def _extract_with_llm(self, content: str, goal_type: str, required_categories: List[str]) -> Dict:
        """
        Use LLM to semantically extract relevant information based on goal type.
        Complements regex extraction with context-aware data.

        Args:
            content: The text content to extract from
            goal_type: The classified goal type
            required_categories: List of data categories to focus on

        Returns:
            Dict with extracted_data
        """
        if not self.fireworks_client or not content:
            return {}

        try:
            # Limit content to avoid token overrun
            content_preview = content[:2000]

            prompt = f"""
Extract relevant information from this content for a {goal_type} goal.

Focus on these data categories:
{', '.join(required_categories)}

Content:
{content_preview}

Return valid JSON only (no markdown, no explanation):
{{"extracted_data": {{"category1": "value", "category2": "value"}}}}

Only include data you can directly extract. Leave categories empty if not found.
Use specific numbers, percentages, and metrics when available.
"""

            response = self.fireworks_client.chat.completions.create(
                model="accounts/fireworks/models/llama-v3p3-70b-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )

            try:
                parsed = json.loads(response.choices[0].message.content)
                return parsed.get("extracted_data", {})
            except json.JSONDecodeError:
                return {}

        except Exception as e:
            if self.verbose:
                print(f"   LLM extraction error: {e}")
            return {}

    def _combine_extractions(self, regex_results: Dict, llm_results: Dict) -> Dict:
        """
        Combine regex and LLM extraction results.

        Regex results take precedence (more reliable), LLM adds semantic context.

        Args:
            regex_results: Results from regex pattern matching
            llm_results: Results from LLM semantic extraction

        Returns:
            Combined extraction results
        """
        combined = dict(regex_results)

        # Add LLM results where regex didn't find data
        for key, value in llm_results.items():
            if key not in combined:
                combined[key] = value

        return combined

    def _validate_extraction_coverage(self, extracted_data: Dict, required_categories: List[str]) -> bool:
        """
        Check if extracted data covers required categories.

        If missing critical categories, return False to trigger additional research.

        Args:
            extracted_data: The extracted data dictionary
            required_categories: Required data categories for this goal

        Returns:
            True if coverage is sufficient, False if more research needed
        """
        if not extracted_data or not required_categories:
            return False

        # Check what % of required categories we found
        found_categories = set(extracted_data.keys())
        required_set = set(required_categories)

        coverage_ratio = len(found_categories.intersection(required_set)) / len(required_set)

        # Require at least 50% coverage to consider research sufficient
        return coverage_ratio >= 0.5

    def _analyze_findings(
        self,
        query: str,
        data_points: List[str],
        remaining_gaps: set
    ) -> List[str]:
        """
        Analyze what gaps were filled by this search. [LEGACY]

        Returns list of gaps that are now satisfied.
        """

        gaps_filled = []

        for gap in remaining_gaps:
            # Simple heuristic: if gap terms appear in data points, we've made progress
            gap_terms = gap.lower().split()

            if any(term in ' '.join(data_points).lower() for term in gap_terms):
                gaps_filled.append(gap)

        return gaps_filled

    def _analyze_findings_with_data(
        self,
        query: str,
        data_points: List[str],
        remaining_gaps: set
    ) -> List[str]:
        """
        Improved gap analysis: mark gaps as filled when we find ACTUAL DATA.

        Since we found data points, this indicates we're making progress on the gaps
        that prompted this query.
        """
        gaps_filled = []

        if not data_points:
            return gaps_filled

        # If we found data points, mark gaps related to this query as partially filled
        combined_data = ' '.join(data_points).lower()

        for gap in remaining_gaps:
            gap_lower = gap.lower()
            gap_terms = gap_lower.split()

            # Check if gap terms appear in extracted data
            if any(term in combined_data for term in gap_terms):
                gaps_filled.append(gap)

        return gaps_filled

    def _generate_follow_up_query(
        self,
        previous_query: str,
        data_points: List[str],
        remaining_gaps: List
    ) -> Optional[str]:
        """
        Generate next search query based on findings and remaining gaps. [LEGACY]

        Intelligent follow-up:
        - If found partial info, drill deeper
        - If found nothing, try different angle
        - Focus on first remaining gap
        """

        if not remaining_gaps:
            return None

        # Focus on first remaining gap
        next_gap = list(remaining_gaps)[0]

        if data_points:
            # We found something - drill deeper
            # Add specificity based on what we found

            if any("%" in str(p) for p in data_points):
                # Found percentages - dig for absolute numbers
                return f"{next_gap} actual numbers absolute values"
            elif any("$" in str(p) for p in data_points):
                # Found dollar amounts - dig for context
                return f"{next_gap} market size growth rate"
            else:
                # Found something else - explore differently
                return f"{next_gap} metrics data statistics"
        else:
            # Found nothing - try different search angle
            return f"{next_gap} case study example"

    def _generate_deep_follow_ups(
        self,
        current_query: str,
        data_points: List[str],
        remaining_gaps: set,
        all_data_points: List[str]
    ) -> List[str]:
        """
        Generate DEEP follow-up queries to drill into found data.

        Based on what we found, generate 2-3 follow-ups to:
        1. Get absolute numbers if we found percentages
        2. Get percentages if we found absolute numbers
        3. Dive deeper into specific metrics found
        4. Explore related gaps
        """
        follow_ups = []

        if not remaining_gaps:
            return follow_ups

        first_gap = list(remaining_gaps)[0]
        combined_data = ' '.join(data_points).lower()

        # Follow-up 1: If percentages found, ask for absolute numbers
        if any("%" in str(p) for p in data_points):
            follow_ups.append(f"{first_gap} actual numbers absolute values millions thousands")

        # Follow-up 2: If financial data found, ask for growth/trends
        if any("value:" in str(p).lower() or "$" in str(p) for p in data_points):
            follow_ups.append(f"{first_gap} growth rate CAGR year-over-year trend")

        # Follow-up 3: If any data found, ask for more specific metrics
        if any("count:" in str(p).lower() or "metric:" in str(p).lower() for p in data_points):
            follow_ups.append(f"{first_gap} detailed metrics breakdown segment analysis")

        # Follow-up 4: Explore related gaps if available
        if len(remaining_gaps) > 1:
            second_gap = list(remaining_gaps)[1]
            follow_ups.append(f"{second_gap} statistics data 2024 2025")

        return follow_ups

    def _generate_alternative_angles(
        self,
        failed_query: str,
        gap: str,
        all_data_points: List[str]
    ) -> List[str]:
        """
        Generate ALTERNATIVE search angles when a query finds sources but no data.

        Try different search strategies:
        1. Industry reports and whitepapers
        2. News and press releases
        3. Academic/research studies
        4. Government statistics
        5. Company earnings reports
        """
        alternatives = []

        # Angle 1: Industry reports
        alternatives.append(f"{gap} industry report whitepaper analysis")

        # Angle 2: News and current events
        alternatives.append(f"{gap} news report latest 2024 2025")

        # Angle 3: Research and studies
        alternatives.append(f"{gap} research study data findings")

        # Angle 4: Government/regulatory data
        alternatives.append(f"{gap} government statistics regulatory data")

        # Angle 5: Company/financial data
        alternatives.append(f"{gap} company earnings report financial data")

        return alternatives

    def _generate_breakthrough_queries(
        self,
        gaps: List[str]
    ) -> List[str]:
        """
        Generate BREAKTHROUGH queries when progress stagnates.

        When we're not finding new data, try radical variations:
        1. Broaden the search (remove specificity)
        2. Add related keywords
        3. Target specific data types
        4. Search for benchmarks and comparisons
        """
        breakthrough = []

        for gap in gaps:
            # Strategy 1: Broaden
            breakthrough.append(f"{gap} overview summary report")

            # Strategy 2: Add industry context
            breakthrough.append(f"{gap} industry analysis trends market")

            # Strategy 3: Seek specific numbers
            breakthrough.append(f"{gap} statistics numbers percentages figures")

            # Strategy 4: Benchmarking
            breakthrough.append(f"{gap} benchmark comparison ranking leading")

        return breakthrough

    def _synthesize_summary(
        self,
        queries: List[str],
        data_points: List[str],
        sources: List[str]
    ) -> str:
        """Create a structured summary of research findings."""

        summary = []
        summary.append("# Research Findings\n")

        if queries:
            summary.append("## Search Queries Used")
            for i, q in enumerate(queries, 1):
                summary.append(f"{i}. {q}")
            summary.append("")

        if data_points:
            summary.append("## Key Data Points Found")
            # Group by type
            percentages = [d for d in data_points if "%" in d]
            growth = [d for d in data_points if "growth" in d.lower()]
            amounts = [d for d in data_points if "amount" in d.lower()]
            metrics = [d for d in data_points if any(m in d.upper() for m in ["ARR", "MRR", "CAC", "LTV"])]
            other = [d for d in data_points if d not in percentages + growth + amounts + metrics]

            if percentages:
                summary.append("### Percentages & Rates")
                for p in percentages[:5]:  # Top 5
                    summary.append(f"- {p}")

            if growth:
                summary.append("### Growth Indicators")
                for g in growth[:5]:
                    summary.append(f"- {g}")

            if amounts:
                summary.append("### Financial Figures")
                for a in amounts[:5]:
                    summary.append(f"- {a}")

            if metrics:
                summary.append("### Key Metrics")
                for m in metrics[:5]:
                    summary.append(f"- {m}")

            if other:
                summary.append("### Other Findings")
                for o in other[:5]:
                    summary.append(f"- {o}")

            summary.append("")

        if sources:
            summary.append("## Sources Consulted")
            for i, src in enumerate(sources[:5], 1):  # Top 5 sources
                summary.append(f"{i}. {src}")

        return "\n".join(summary)

    def _estimate_coverage(self, original_gaps: List[str], remaining_gaps: set) -> float:
        """Estimate what % of gaps were filled. [LEGACY]"""

        if not original_gaps:
            return 1.0

        filled = len(original_gaps) - len(remaining_gaps)
        return filled / len(original_gaps)

    def _estimate_coverage_extensive(
        self,
        original_gaps: List[str],
        remaining_gaps: set,
        all_data_points: List[str]
    ) -> float:
        """
        Estimate coverage based on BOTH gaps filled AND actual data found.

        Coverage = (0.5 * gap_fill_rate) + (0.5 * data_density)

        This encourages finding actual data, not just gap-filling.
        """

        if not original_gaps:
            return 0.0 if not all_data_points else 1.0

        # Component 1: Gap fill rate (0-1)
        # How many of the original gaps did we address?
        gap_fill_rate = (len(original_gaps) - len(remaining_gaps)) / len(original_gaps)

        # Component 2: Data density (0-1)
        # How many data points did we extract?
        # Normalize to: 0 points = 0%, 10+ points = 100%
        data_point_count = len(all_data_points)
        data_density = min(1.0, data_point_count / 10.0)

        # Composite coverage (weighted)
        # If we found data but no gaps filled, coverage can still be 50%
        # If we filled all gaps but found no data, coverage is only 50%
        coverage = (0.5 * gap_fill_rate) + (0.5 * data_density)

        return min(1.0, coverage)  # Cap at 100%


if __name__ == "__main__":
    # Example usage
    agent = ResearchAgent(verbose=True)

    result = agent.research(
        gaps=[
            "SaaS growth trends Q1 2025",
            "Product-led growth effectiveness",
            "Competitor market moves"
        ],
        max_iterations=3
    )

    print("\n" + "="*60)
    print("RESEARCH RESULTS")
    print("="*60)
    print(f"Coverage: {result.coverage:.0%}")
    print(f"Iterations: {result.iterations_used}")
    print(f"\nSummary:\n{result.summary}")
    print(f"\nGaps Filled: {result.gaps_filled}")
    print(f"Remaining: {result.gaps_remaining}")
