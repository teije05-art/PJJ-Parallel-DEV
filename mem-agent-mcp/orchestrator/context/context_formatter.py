"""
Context Formatting Utilities

Provides formatting functions for context data.
Simple utility module with no external dependencies.
"""

from typing import Dict
from datetime import datetime


class ContextFormatter:
    """Utilities for formatting context data"""

    @staticmethod
    def format_web_search_results(organized_results: Dict, total_searches: int, total_results: int) -> str:
        """
        Format web search results for agent consumption.

        Args:
            organized_results: Dictionary of results organized by category
            total_searches: Total number of search queries executed
            total_results: Total number of results found

        Returns:
            Formatted string with citations and URLs
        """
        if total_results == 0:
            return "No web search results available - internet may be unavailable"

        # Build comprehensive formatted output with citations
        formatted_output = f"""# 🌐 EXTENSIVE WEB RESEARCH DATA
*Comprehensive real-world data collection with {total_results} sources across {len(organized_results)} categories*

---

"""

        for category, results in organized_results.items():
            if results:
                formatted_output += f"\n## 📊 {category}\n"
                formatted_output += f"*{len(results)} sources identified*\n\n"

                for idx, result in enumerate(results, 1):
                    # Format with clear citations and clickable URLs
                    formatted_output += f"""### [{idx}] {result['title']}

**Source:** {result['source']}
**URL:** {result['url']}

{result['snippet']}

---

"""

        # Add research methodology note
        formatted_output += f"""
## 📈 Research Methodology

- **Total Sources Analyzed:** {total_results}
- **Search Categories:** {len(organized_results)}
- **Queries Executed:** {total_searches}
- **Search Method:** DuckDuckGo (Real-time web search)
- **Results Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### How to Use These Sources
1. Agents can reference specific sources by number [1], [2], etc.
2. URLs can be verified for accuracy and current information
3. Snippets provide context from each source
4. Sources are organized by research category for easy navigation

### Citation Format for Agents
When using these sources, agents should cite as:
- "[Title] [Source - URL]" or
- "According to [Source]: [finding]"

This ensures all planning decisions are grounded in real, verifiable information.

---
"""

        return formatted_output
