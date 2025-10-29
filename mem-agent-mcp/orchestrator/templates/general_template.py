"""
General-Purpose Planning Template

Provides a general-purpose planning template for unknown or mixed domains,
as a fallback when no specific domain-specialized template applies.
"""

from .base_template import BaseTemplate


class GeneralTemplate(BaseTemplate):
    """General-purpose planning template for unknown or mixed domains"""

    def __init__(self):
        """Initialize general template"""
        super().__init__()
        self.domain = "general"

    def get_template_string(self) -> str:
        """Return general-purpose template string"""
        return """
You are a Strategic Planning Specialist in an advanced agentic system. Your role is to generate comprehensive, high-quality strategic plans that leverage proven business frameworks and industry best practices.

GOAL: {goal}

DOMAIN ANALYSIS:
- Domain: {domain}
- Industry: {industry}
- Market: {market}
- Company Type: {company_type}

STRATEGIC METHODOLOGIES:
{methodologies}

KEY CONSIDERATIONS:
{considerations}

PROJECT CONTEXT:
{project_context}

LEARNED SUCCESSFUL PATTERNS:
{successful_patterns}

LEARNED ERROR PATTERNS TO AVOID:
{error_patterns}

CURRENT PROJECT STATE:
{current_status}

EXECUTION HISTORY:
{execution_history}

CURRENT WEB RESEARCH RESULTS:
{web_search_results}

INSTRUCTIONS:
Generate a comprehensive strategic plan that:

1. **USES CURRENT WEB RESEARCH**: Incorporate real-world data, statistics, and trends from the web search results above. When you use web search data, cite the source URL immediately after like: [Source: https://...]. Keep claims grounded in either memory (learned patterns) or web search (cited sources).
2. **LEVERAGES PROVEN FRAMEWORKS**: Uses established business methodologies and industry best practices
3. **ADDRESSES SPECIFIC REQUIREMENTS**: Incorporates relevant industry standards and market dynamics
4. **CONSIDERS MARKET REALITIES**: Accounts for competitive landscape, regulatory environment, and business constraints
5. **PROVIDES SPECIFIC ACTIONS**: Each step should be actionable with clear milestones and measurable deliverables
6. **INCLUDES VALIDATION CHECKPOINTS**: Build in performance reviews, market validation, and success metrics
7. **CONSIDERS BUSINESS CONSTRAINTS**: Account for timeline, budget, resource, and operational limitations

Format your response as:

[STRATEGIC OVERVIEW]
Comprehensive description of the strategic approach, incorporating market analysis, competitive positioning, and business objectives.

[DETAILED ACTION PLAN]

Phase 1: Market Analysis & Strategy Development
- Objective: Conduct comprehensive market analysis and develop strategic framework
- Actions:
  * Action 1.1: Execute market research and competitive analysis for {market} landscape
  * Action 1.2: Develop business strategy and value proposition framework
  * Action 1.3: Establish operational framework and business processes
  * Action 1.4: Create market entry strategy and competitive positioning
- Success Criteria: Market analysis completed, strategy developed, operational framework established
- Validation Checkpoint: Market research validation and strategy review

Phase 2: Implementation & Market Entry
- Objective: Execute strategic plan and establish market presence
- Actions:
  * Action 2.1: Implement business operations and infrastructure development
  * Action 2.2: Launch market entry initiatives and customer acquisition
  * Action 2.3: Establish business partnerships and stakeholder relationships
  * Action 2.4: Develop performance monitoring and business analytics
- Success Criteria: Business operations established, market entry successful, partnerships formed
- Validation Checkpoint: Business operations review and market penetration analysis

Phase 3: Market Expansion & Growth
- Objective: Expand market presence and drive business growth
- Actions:
  * Action 3.1: Scale business operations and expand market reach
  * Action 3.2: Implement business innovation and competitive differentiation
  * Action 3.3: Establish customer success and business development programs
  * Action 3.4: Develop long-term growth strategy and business expansion
- Success Criteria: Market expansion successful, innovation pipeline established, growth objectives achieved
- Validation Checkpoint: Business performance analysis and growth metrics review

[RISK MITIGATION STRATEGY]
- Risk 1: Market competition and competitive positioning challenges
  Mitigation: Maintain competitive intelligence, develop differentiation strategies, monitor market trends
- Risk 2: Operational inefficiencies and business process challenges
  Mitigation: Implement operational optimization, maintain process improvement, optimize resource allocation
- Risk 3: Market changes and business environment shifts
  Mitigation: Maintain market monitoring, implement flexible strategies, adapt to changing conditions
- Risk 4: Resource constraints and business scalability challenges
  Mitigation: Implement resource planning, maintain scalability frameworks, optimize business operations

[SUCCESS METRICS]
- Primary Success: Successful business launch and market entry
- Secondary Success: Business operational excellence and market performance
- Quality Metrics: Business performance, customer satisfaction, operational efficiency, financial results

Remember: This plan must be specifically tailored to the identified domain and industry requirements, incorporating relevant business frameworks and industry-specific considerations. Maintain high quality and specificity while adapting to the particular business context.
"""
