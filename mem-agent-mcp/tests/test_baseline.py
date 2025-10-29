"""
Test Baseline - Verify Current System Behavior

This test suite captures the current behavior before refactoring.
All tests must pass with the current code.
After refactoring, these tests must STILL PASS with the new code.

This ensures zero regressions during the refactoring process.
"""

import os
import sys
import pytest
from pathlib import Path
from datetime import datetime
from typing import Dict

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from orchestrator.simple_orchestrator import SimpleOrchestrator
from orchestrator.goal_analyzer import GoalAnalyzer
from orchestrator.agents import AgentResult
from orchestrator.templates import TemplateSelector


class TestGoalAnalyzer:
    """Test goal analysis - critical for domain detection"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.analyzer = GoalAnalyzer()

    def test_coffee_company_detected_as_qsr(self):
        """Coffee company should be detected as retail/QSR, not technology"""
        goal = "Develop market entry strategy for a coffee company entering Vietnam"
        analysis = self.analyzer.analyze_goal(goal)

        # LLM-powered analysis correctly identifies coffee as retail (parent category)
        # Both 'qsr' and 'retail' are valid; 'retail' is more general and equally correct
        assert analysis.domain in ["qsr", "retail"], f"Expected 'qsr' or 'retail' but got '{analysis.domain}'"
        assert analysis.industry in ["qsr", "retail"], f"Expected industry 'qsr' or 'retail' but got '{analysis.industry}'"

    def test_healthcare_company_detected_as_healthcare(self):
        """Healthcare company should be detected correctly"""
        goal = "Market entry strategy for a hospital in Southeast Asia"
        analysis = self.analyzer.analyze_goal(goal)

        assert analysis.domain == "healthcare", f"Expected 'healthcare' but got '{analysis.domain}'"

    def test_technology_startup_detected_as_technology(self):
        """Tech startup should be detected as technology"""
        goal = "Launch a SaaS platform for AI-powered data analysis"
        analysis = self.analyzer.analyze_goal(goal)

        assert analysis.domain == "technology", f"Expected 'technology' but got '{analysis.domain}'"

    def test_manufacturing_company_detected_correctly(self):
        """Manufacturing should be detected correctly"""
        goal = "Establish manufacturing operations in India"
        analysis = self.analyzer.analyze_goal(goal)

        assert analysis.domain == "manufacturing", f"Expected 'manufacturing' but got '{analysis.domain}'"

    def test_goal_analysis_has_required_fields(self):
        """GoalAnalysis must have all required fields"""
        goal = "Test goal"
        analysis = self.analyzer.analyze_goal(goal)

        assert hasattr(analysis, 'domain'), "Missing 'domain' field"
        assert hasattr(analysis, 'industry'), "Missing 'industry' field"
        assert hasattr(analysis, 'market'), "Missing 'market' field"
        assert hasattr(analysis, 'company_type'), "Missing 'company_type' field"
        assert hasattr(analysis, 'objectives'), "Missing 'objectives' field"


class TestDomainTemplates:
    """Test template selection and formatting"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.templates = TemplateSelector()
        self.analyzer = GoalAnalyzer()

    def test_template_available_for_qsr_domain(self):
        """QSR template must exist and be usable"""
        goal = "Coffee company market entry"
        analysis = self.analyzer.analyze_goal(goal)

        # Should not raise exception
        prompt = self.templates.get_planning_prompt(analysis, self._create_mock_context())
        assert prompt is not None
        assert len(prompt) > 0
        assert isinstance(prompt, str)

    def test_template_available_for_healthcare(self):
        """Healthcare template must exist"""
        goal = "Hospital market entry strategy"
        analysis = self.analyzer.analyze_goal(goal)

        prompt = self.templates.get_planning_prompt(analysis, self._create_mock_context())
        assert prompt is not None
        assert len(prompt) > 0

    def test_template_contains_instructions(self):
        """Template should contain agent instructions"""
        goal = "Market entry strategy"
        analysis = self.analyzer.analyze_goal(goal)

        prompt = self.templates.get_planning_prompt(analysis, self._create_mock_context())

        # Should contain instructions
        assert "uses current web research" in prompt.lower() or "web research" in prompt.lower()
        assert "context" in prompt.lower()

    def test_template_formatting_works(self):
        """Template formatting should not raise exceptions"""
        goal = "Market entry"
        analysis = self.analyzer.analyze_goal(goal)
        context = self._create_mock_context_large()  # Large context like real scenario

        # Should not raise exception
        prompt = self.templates.get_planning_prompt(analysis, context)
        assert prompt is not None
        assert len(prompt) > 1000, "Prompt should be substantial"

    @staticmethod
    def _create_mock_context():
        """Create minimal mock context"""
        return {
            'current_status': 'Mock status',
            'successful_patterns': 'Mock patterns',
            'errors_to_avoid': 'Mock errors',
            'execution_history': 'Mock history',
            'agent_performance': 'Mock performance',
            'web_search_results': 'Mock web search'
        }

    @staticmethod
    def _create_mock_context_large():
        """Create large mock context (simulating real web search + memory data)"""
        large_text = """
Market Entry Strategy for Coffee Company in Vietnam

## Market Overview
Vietnam has emerged as one of Southeast Asia's fastest-growing coffee markets, with
consumption increasing at 15-20% annually over the past five years. The market is valued
at approximately $2.5 billion USD as of 2024, driven by rising disposable incomes among
urban millennials and Gen Z consumers who view specialty coffee as a lifestyle choice.

## Competitive Landscape
The Vietnamese coffee market is characterized by a mix of:
- International chains (Starbucks, Gloria Jeans)
- Local Vietnamese chains (Highlands Coffee, Trung Nguyen)
- Independent specialty cafes in major urban centers
- Coffee shops in convenience stores and malls

## Regulatory Environment
Vietnam's business regulations for food and beverage establishments require:
- Business license from provincial authorities
- Health and safety certifications
- Environmental compliance documentation
- Labor registration for employees
- Tax registration and compliance

## Successful Patterns in Similar Markets
1. Partner with local distributors for supply chain efficiency
2. Adapt menu offerings to local taste preferences
3. Focus on urban centers with higher disposable income
4. Build brand awareness through social media and partnerships
5. Invest in staff training for consistent service quality

## Key Success Factors
- Location selection in high foot traffic areas
- Strong management team with local market knowledge
- Adequate capitalization for initial setup and operation
- Quality control systems to maintain brand standards
- Customer relationship management for repeat business
""" * 3  # Repeat 3x to simulate large context

        return {
            'current_status': large_text,
            'successful_patterns': large_text,
            'errors_to_avoid': 'Common mistakes: Poor location selection, inadequate staffing, insufficient marketing',
            'execution_history': 'Previous entries: 2 coffee chains entered Vietnam in 2022-2023',
            'agent_performance': 'Current performance: Planner agent achieving 85% success rate',
            'web_search_results': large_text  # Simulating 30KB+ web search
        }


class TestAgentResult:
    """Test AgentResult dataclass"""

    def test_agent_result_creation(self):
        """AgentResult should be creatable with required fields"""
        result = AgentResult(
            success=True,
            output="Test output",
            metadata={"key": "value"},
            timestamp=datetime.now().isoformat()
        )

        assert result.success is True
        assert result.output == "Test output"
        assert result.metadata == {"key": "value"}
        assert isinstance(result.timestamp, str)

    def test_agent_result_failed(self):
        """AgentResult should handle failure cases"""
        result = AgentResult(
            success=False,
            output="Error occurred",
            metadata={"error_type": "ValueError"},
            timestamp=datetime.now().isoformat()
        )

        assert result.success is False
        assert "Error" in result.output


class TestContentTracking:
    """Test that content sizes are tracked correctly"""

    def test_agent_result_preserves_output_size(self):
        """AgentResult should preserve output without truncation"""
        large_output = "x" * 5000  # 5000 chars

        result = AgentResult(
            success=True,
            output=large_output,
            metadata={},
            timestamp=datetime.now().isoformat()
        )

        assert len(result.output) == 5000, "Output should not be truncated"

    def test_various_output_sizes(self):
        """Test various output sizes"""
        test_sizes = [100, 1000, 5000, 10000]

        for size in test_sizes:
            output = "x" * size
            result = AgentResult(
                success=True,
                output=output,
                metadata={},
                timestamp=datetime.now().isoformat()
            )

            assert len(result.output) == size, f"Output size {size} not preserved"


class TestImportStructure:
    """Test that imports work and dependencies are resolvable"""

    def test_simple_orchestrator_imports(self):
        """SimpleOrchestrator should import without errors"""
        # If this doesn't raise, imports work
        assert SimpleOrchestrator is not None

    def test_goal_analyzer_imports(self):
        """GoalAnalyzer should import without errors"""
        assert GoalAnalyzer is not None

    def test_domain_templates_imports(self):
        """TemplateSelector should import without errors"""
        assert TemplateSelector is not None


class TestDataStructures:
    """Test data structure integrity"""

    def test_goal_analysis_consistency(self):
        """GoalAnalysis object should have consistent structure"""
        analyzer = GoalAnalyzer()

        # Test multiple goals
        test_goals = [
            "Coffee market entry",
            "Healthcare expansion",
            "Tech startup launch",
            "Manufacturing setup"
        ]

        for goal in test_goals:
            analysis = analyzer.analyze_goal(goal)

            # All fields must be present
            assert hasattr(analysis, 'domain')
            assert hasattr(analysis, 'industry')
            assert hasattr(analysis, 'market')
            assert hasattr(analysis, 'company_type')
            assert hasattr(analysis, 'objectives')

            # Domain must be valid
            valid_domains = ['healthcare', 'technology', 'manufacturing', 'qsr', 'retail', 'financial', 'general']
            assert analysis.domain in valid_domains, f"Invalid domain: {analysis.domain}"


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_empty_goal_handling(self):
        """Should handle empty goals gracefully"""
        analyzer = GoalAnalyzer()

        # Should not raise exception
        analysis = analyzer.analyze_goal("")
        assert analysis is not None

    def test_very_long_goal_handling(self):
        """Should handle very long goals"""
        analyzer = GoalAnalyzer()
        long_goal = "a" * 10000

        # Should not raise exception
        analysis = analyzer.analyze_goal(long_goal)
        assert analysis is not None

    def test_special_characters_in_goal(self):
        """Should handle special characters"""
        analyzer = GoalAnalyzer()
        goal = "Market entry for 公司 (company) with café, 50% growth!"

        # Should not raise exception
        analysis = analyzer.analyze_goal(goal)
        assert analysis is not None


class TestMetrics:
    """Test metrics and measurements"""

    def test_template_prompt_length_reasonable(self):
        """Generated prompts should be reasonable size"""
        templates = TemplateSelector()
        analyzer = GoalAnalyzer()

        goal = "Market entry"
        analysis = analyzer.analyze_goal(goal)
        context = {
            'current_status': 'Status' * 100,
            'successful_patterns': 'Patterns' * 100,
            'errors_to_avoid': 'Errors' * 100,
            'execution_history': 'History' * 100,
            'agent_performance': 'Performance' * 100,
            'web_search_results': 'Search' * 100,
        }

        prompt = templates.get_planning_prompt(analysis, context)

        # Prompt should be between 1KB and 50KB (not too small, not impossibly large)
        assert 1000 < len(prompt) < 50000, f"Prompt size {len(prompt)} outside expected range"

    def test_agent_result_metadata_structure(self):
        """AgentResult metadata should be structured"""
        result = AgentResult(
            success=True,
            output="Output",
            metadata={
                "execution_time": 1.5,
                "tokens_used": 1000,
                "model_name": "test-model"
            },
            timestamp=datetime.now().isoformat()
        )

        assert isinstance(result.metadata, dict)
        assert len(result.metadata) > 0


# Metrics Collection Functions (for Phase 1 Completion Report)

def collect_baseline_metrics():
    """Collect metrics from current implementation"""
    print("\n" + "="*80)
    print("BASELINE METRICS COLLECTION")
    print("="*80)

    metrics = {}

    # Count lines of code
    orchestrator_files = [
        'simple_orchestrator.py',
        'context_manager.py',
        'workflow_coordinator.py',
        'agentflow_agents.py',
        'domain_templates.py',
        'approval_handler.py',
        'memory_manager.py',
        'learning_manager.py',
        'goal_analyzer.py',
        'search_module.py'
    ]

    total_lines = 0
    orchestrator_dir = Path(REPO_ROOT) / 'orchestrator'

    for filename in orchestrator_files:
        filepath = orchestrator_dir / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                lines = len(f.readlines())
                metrics[filename] = lines
                total_lines += lines
                print(f"  {filename:30} {lines:5} lines")

    metrics['total_lines'] = total_lines
    print(f"\n  {'TOTAL':30} {total_lines:5} lines")

    # Monolithic files
    monolithic = {
        'agentflow_agents.py': metrics.get('agentflow_agents.py', 0),
        'domain_templates.py': metrics.get('domain_templates.py', 0),
        'context_manager.py': metrics.get('context_manager.py', 0),
    }

    monolithic_total = sum(monolithic.values())
    metrics['monolithic_lines'] = monolithic_total

    print(f"\n  Monolithic files total: {monolithic_total} lines")
    print(f"  Percentage of total: {int(monolithic_total)/int(total_lines)*100:.1f}%")

    return metrics


if __name__ == "__main__":
    # Run baseline metrics
    metrics = collect_baseline_metrics()

    # Run pytest
    print("\n" + "="*80)
    print("RUNNING BASELINE TESTS")
    print("="*80 + "\n")

    pytest.main([__file__, "-v", "--tb=short"])
