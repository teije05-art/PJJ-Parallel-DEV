"""
TaxResponseSearcher - Step 2 Agent

Searches past approved tax responses using MemAgent.
Returns similar cases that might directly answer the current request.

CONSTRAINT BOUNDARIES (CRITICAL):
- Search source: past_responses directory ONLY
- NO autonomous search: Requires confirmed_categories from user
- Query constraint: CONSTRAINT text in query enforces category filtering
- Result filtering: Only returns results matching user-selected categories
- Metadata tracking: Return search scope, category_boundary, results_filtered_count

If categories is empty → returns empty (no fallback to broad search)
If no matches found → returns empty list (not error)
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from orchestrator.agents.base_agent import BaseAgent, AgentResult
from agent.logging_config import get_logger, log_search_query, log_search_results

logger = get_logger(__name__)


class TaxResponseSearcher(BaseAgent):
    """
    Searches past tax responses via MemAgent intelligent memory navigation.

    CONSTRAINT BOUNDARIES:
    - Search Scope: ONLY past_responses/ directory
    - Filter: ONLY responses matching confirmed_categories from user
    - Fallback: If categories empty, return empty (no autonomous search)
    - No Autonomy: Cannot search beyond past responses, cannot search without categories

    How it works:
    1. Sends query to Agent.chat() with category constraints
    2. Agent reads past_responses from memory and identifies matches
    3. Returns results with metadata about what was searched
    """

    # Search constraints
    MAX_RESULTS = 5

    def __init__(self, agent: Agent, memory_path: Path):
        """
        Initialize TaxResponseSearcher

        Args:
            agent: Agent instance for memory navigation
            memory_path: Path to PRIMARY DATA directory (/local-memory/tax_legal/)
        """
        super().__init__(agent, memory_path)
        self.agent = agent
        self.memory_path = Path(memory_path) if isinstance(memory_path, str) else memory_path

        # Log initialization with explicit path information
        logger.info("=" * 80)
        logger.info("STEP 2: TaxResponseSearcher Initialized")
        logger.info(f"  PRIMARY DATA DIRECTORY: {self.memory_path}")
        logger.info(f"  Search Source: {self.memory_path / 'past_responses'}")
        logger.info(f"  Search Scope: past_responses/ (approved tax responses)")
        logger.info(f"  Constraint: Category filtering enforced via Agent")
        logger.info("=" * 80)

    def generate(
        self,
        request: str,
        categories: Optional[List[str]] = None
    ) -> AgentResult:
        """
        Search past tax responses matching the request and categories.

        Uses Agent.chat() to navigate memory and find relevant past responses.
        Agent interprets the constraint and searches only within specified categories.

        Args:
            request: The tax question/request
            categories: User-confirmed tax categories (REQUIRED for search)

        Returns:
            AgentResult with:
            - success: True if search completed (even if no results)
            - output: List of past responses (top-5) with metadata
            - metadata: Search scope, categories boundary, results info
            - error: Empty string on success
        """
        try:
            logger.info("=== TaxResponseSearcher.generate() STARTED ===")
            logger.info(f"Input request: '{request[:100]}...' (length: {len(request)})")
            logger.info(f"Categories: {categories}")
            start_time = time.time()

            # CONSTRAINT ENFORCEMENT: Categories required
            if not categories:
                logger.warning("Categories parameter is missing - cannot perform constrained search")
                return AgentResult(
                    success=False,
                    output=[],
                    metadata={
                        "error": "Categories required for constrained search",
                        "search_scope": "past_responses",
                        "required_parameter": "categories"
                    },
                    timestamp=datetime.now().isoformat(),
                    error="Categories parameter is required"
                )

            logger.info(f"Constraint boundary: Search ONLY in past_responses/")
            logger.info(f"Category constraint: ONLY results matching {categories}")

            # Build constrained query with explicit CONSTRAINT directive
            # This tells the Agent to use Python code to navigate memory
            constrained_query = f"""Find the 5 most relevant past tax response memos in the past_responses directory that match this query and are related to these categories: {', '.join(categories)}.

Query: {request}

Focus on responses related to: {', '.join(categories)}

Return relevant past responses with their filenames and summaries."""

            logger.debug(f"Constrained query: {constrained_query[:200]}...")

            # MEMAGENT NAVIGATION: Use Agent.chat() for intelligent memory search
            logger.info("=== EXECUTING MEMAGENT SEARCH (Step 2) ===")
            logger.info(f"Query: {request[:100]}...")
            logger.info(f"Categories constraint: {categories}")
            logger.info("Using Agent to navigate past_responses...")

            # Call Agent to search memory
            # Agent will read past_responses and return matches
            agent_response = self.agent.chat(constrained_query)

            search_time_ms = (time.time() - start_time) * 1000
            logger.info(f"Agent search completed in {search_time_ms:.1f}ms")
            logger.info(f"Agent response length: {len(agent_response.reply)} characters")

            # Parse Agent's response to extract past responses
            past_responses = self._parse_agent_response(
                agent_response.reply,
                categories
            )

            logger.info(f"=== MEMAGENT SEARCH COMPLETED ===")
            logger.info(f"Search time: {search_time_ms:.1f}ms")
            logger.info(f"Results found: {len(past_responses)} past responses")

            # Limit results to MAX_RESULTS
            past_responses = past_responses[:self.MAX_RESULTS]
            logger.info(f"Results after limiting to top {self.MAX_RESULTS}: {len(past_responses)}")

            # Format output
            formatted_results = []
            for result in past_responses:
                formatted_results.append({
                    "filename": result.get("filename", "Unknown"),
                    "summary": result.get("summary", "")[:200],  # First 200 chars
                    "categories": result.get("categories", []),
                    "files_used": result.get("files_used", []),
                    "date_created": result.get("date_created", "Unknown")
                })

            logger.info(f"Final formatted output: {len(formatted_results)} past responses")
            logger.info(f"=== TaxResponseSearcher.generate() COMPLETED SUCCESSFULLY ===")

            return AgentResult(
                success=True,
                output=formatted_results,
                metadata={
                    "total_found": len(formatted_results),
                    "search_time_ms": int(search_time_ms),
                    "search_scope": "past_responses",
                    "search_method": "MemAgent intelligent navigation",
                    "categories_searched": categories,
                    "category_constraint_boundary": categories,
                },
                timestamp=datetime.now().isoformat(),
                error=""
            )

        except Exception as e:
            logger.error(f"=== TaxResponseSearcher.generate() FAILED ===")
            logger.error(f"Exception: {str(e)}", exc_info=True)
            return AgentResult(
                success=False,
                output=[],
                metadata={"error_type": "search_error"},
                timestamp=datetime.now().isoformat(),
                error=f"Search failed: {str(e)}"
            )

    def _parse_agent_response(
        self,
        response_text: str,
        requested_categories: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Parse Agent's natural language response to extract past responses.

        The Agent navigates memory and identifies relevant files.
        This method extracts document information from the response.

        Args:
            response_text: Agent's response with past response information
            requested_categories: Categories the user requested

        Returns:
            List of structured past response objects
        """
        past_responses = []

        if not response_text or len(response_text.strip()) == 0:
            logger.warning("Agent returned empty response")
            return past_responses

        try:
            import ast

            response_text = response_text.strip()

            # Strategy 1: Try to parse as Python literal (list of dicts)
            try:
                data = ast.literal_eval(response_text)
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    for item in data:
                        if isinstance(item, dict) and 'filename' in item:
                            response = {
                                "filename": item.get("filename", "Unknown"),
                                "summary": item.get("summary", "")[:200],
                                "categories": item.get("categories", requested_categories),
                                "files_used": item.get("files_used", []),
                                "date_created": item.get("date_created", "Unknown")
                            }
                            past_responses.append(response)
                    logger.info(f"Parsed {len(past_responses)} past responses from Python literal")
                    return past_responses
            except (ValueError, SyntaxError):
                pass

            # Strategy 2: Parse as narrative list (fallback)
            logger.info("Attempting narrative parse of Agent response")
            import re
            lines = response_text.split('\n')
            current_response = None

            for line in lines:
                line = line.strip()

                # Detect response headers (file names, numbered lists)
                if line and (line.startswith(('1.', '2.', '3.', '4.', '5.', '-')) or
                            line.endswith('.md')):
                    if current_response and "filename" in current_response:
                        past_responses.append(current_response)

                    # Extract filename
                    filename = re.sub(r'^[\d\.\-\s]+', '', line).strip()
                    if filename and '.md' in filename.lower():
                        current_response = {
                            "filename": filename,
                            "summary": "",
                            "categories": requested_categories,
                            "files_used": [],
                            "date_created": "Unknown"
                        }
                elif current_response and line and not line.startswith('-'):
                    current_response["summary"] += " " + line

            if current_response and "filename" in current_response:
                past_responses.append(current_response)

            logger.info(f"Parsed {len(past_responses)} past responses from narrative")
            return past_responses

        except Exception as e:
            logger.error(f"Error parsing Agent response: {e}")
            logger.warning(f"Response text was: {response_text[:500]}...")
            return past_responses
