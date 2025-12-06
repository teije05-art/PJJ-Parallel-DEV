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
    MAX_RESULTS = 15

    # Category to directory mapping (numbered prefixes in actual filesystem)
    CATEGORY_DIR_MAP = {
        "CIT": "01_CIT",
        "VAT": "02_VAT",
        "Customs": "03_Customs",
        "PIT": "04_PIT",
        "DTA": "05_DTA",
        "Transfer Pricing": "06_Transfer_Pricing",
        "FCT": "07_FCT",
        "Tax Administration": "08_Tax_Administration",
        "Excise Tax": "09_Excise_Tax_SST",
        "Natural Resources": "10_Natural_Resources_SHUI",
        "Draft Regulations": "11_Draft_Regulations",
        "Capital Gains": "12_Capital_Gains_Tax_CGT",
        "Environmental Tax": "13_Environmental_Protection_EPT",
        "Immigration": "14_Immigration_Work_Permits",
        "E-Commerce": "15_E_Commerce",
        "Business Support": "16_Business_Support_Measures",
        "General Policies": "17_General_Policies",
        "Miscellaneous": "18_Miscellaneous"
    }

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

            # Map categories to actual directory names
            category_dirs = [f'past_responses/{self.CATEGORY_DIR_MAP.get(cat, cat)}/' for cat in categories]
            logger.info(f"Mapped category directories: {category_dirs}")

            # CRITICAL: Use Python code to navigate directories and read files
            # Agent must write Python code that uses list_files(), read_file(), etc.
            # Use ABSOLUTE paths from the memory directory
            memory_base = self.memory_path
            absolute_category_dirs = [f'{memory_base}/{d}' for d in category_dirs]

            # IMPROVED PROMPT - Requirements as comments, not example code
            # Agent must write its own executable Python code
            constrained_query = f"""You MUST respond with ONLY these sections:

<think>
[Your plan to search these directories for relevant past tax responses]
</think>

<python>
# REQUIREMENTS (write Python code to implement these):
# 1. Create empty 'results' list
# 2. Set category_dirs to: {absolute_category_dirs!r}
# 3. For each dir in category_dirs:
#    - Use os.walk(dir) to recursively traverse ALL subdirectories
#    - For each .md file found:
#      * Use os.chdir(root) to navigate to file's directory
#      * Use read_file(filename) to get content
#      * If len(content) > 50:
#        - Append dict to results with keys: 'source_file', 'content', 'directory'
#        - 'content' should be content[:3000] (first 3000 chars)
#        - 'source_file' should be filename
#        - 'directory' should be root
# 4. Wrap file operations in try/except to handle errors
#
# Write the actual executable Python code below (not comments):
</python>

CRITICAL: Your <python> section must contain ACTUAL executable code that creates the 'results' variable."""

            logger.debug(f"Constrained query: {constrained_query[:200]}...")

            # MEMAGENT NAVIGATION: Use Agent.chat() for intelligent memory search
            logger.info("=== EXECUTING MEMAGENT SEARCH (Step 2) ===")
            logger.info(f"Query: {request[:100]}...")
            logger.info(f"Categories constraint: {categories}")
            logger.info("Using Agent to navigate past_responses...")

            # CRITICAL: Create a FRESH Agent instance to avoid context overflow
            # Each step gets its own clean context window (fresh conversation history)
            # max_tool_turns=1 ensures single execution of template code (no refinement modifications)
            from agent import Agent
            fresh_agent = Agent(memory_path=str(self.memory_path), max_tool_turns=1)
            logger.info("Created fresh Agent instance for this search (max_tool_turns=1)")

            # Call fresh Agent to search memory
            # Agent will read past_responses and return matches
            agent_response = fresh_agent.chat(constrained_query)

            search_time_ms = (time.time() - start_time) * 1000
            logger.info(f"Agent search completed in {search_time_ms:.1f}ms")

            # DEBUG: Show what Python code was executed
            logger.info(f"=== PYTHON CODE EXECUTED ===")
            if agent_response.python_block:
                logger.info(f"{agent_response.python_block[:1000]}")
            else:
                logger.warning("NO PYTHON CODE WAS EXECUTED!")
            logger.info(f"=== END PYTHON CODE ===")

            logger.info(f"Execution results available: {agent_response.execution_results is not None}")
            if agent_response.execution_results:
                logger.info(f"Execution results type: {type(agent_response.execution_results)}")
                logger.info(f"Execution results keys: {list(agent_response.execution_results.keys())}")
                logger.info(f"Number of items in 'results' key: {len(agent_response.execution_results.get('results', []))}")
                if 'results' in agent_response.execution_results:
                    logger.info(f"First result sample: {agent_response.execution_results['results'][0] if agent_response.execution_results['results'] else 'EMPTY LIST'}")
            else:
                logger.error(f"Execution results is EMPTY! Type: {type(agent_response.execution_results)}, Value: {agent_response.execution_results}")

            logger.info(f"Agent reply preview: {agent_response.reply[:500] if agent_response.reply else 'No reply'}")

            # Extract past responses from Agent's execution results
            # The Agent's Python code creates a 'results' variable with extracted content
            past_responses = []
            if agent_response.execution_results and "results" in agent_response.execution_results:
                # Results variable is available from Python code execution
                raw_results = agent_response.execution_results.get("results", [])
                logger.info(f"Found {len(raw_results)} results from Agent execution")

                # Convert Agent's raw results to structured format
                for result in raw_results:
                    if isinstance(result, dict):
                        full_text = result.get("content", "")  # Get the 3000-char content
                        past_responses.append({
                            "filename": result.get("source_file", "Unknown"),
                            "section_title": result.get("section_title", "Section"),
                            "relevance": result.get("relevance", "Relevant"),
                            "content": full_text,  # Full 3000 chars for synthesis
                            "summary": full_text[:250],  # First 250 chars for display
                            "categories": categories,
                            "files_used": [result.get("source_file", "Unknown")],
                            "date_created": "Unknown"
                        })
            else:
                # Fallback: try to parse Agent's reply text (for backward compatibility)
                logger.debug("No execution results found, attempting text parsing fallback")
                past_responses = self._parse_agent_response(
                    agent_response.reply or "",
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
                    "content": result.get("content", ""),  # Full 3000 chars preserved for synthesis
                    "summary": result.get("summary", ""),  # Already 250 chars from line 236
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
        Parse Agent's Python code execution response to extract past responses.

        Agent executes Python code that creates a 'results' variable containing:
        [
            {
                "source_file": "filename.md",
                "section_title": "Section Title",
                "relevance": "Why this is relevant",
                "content": "actual extracted text",
                "directory": "past_responses/XX_Category/"
            },
            ...
        ]

        Args:
            response_text: Agent's response after Python code execution
            requested_categories: Categories the user requested

        Returns:
            List of structured past response objects with full content
        """
        past_responses = []

        if not response_text or len(response_text.strip()) == 0:
            logger.warning("Agent returned empty response - likely no files found in directories")
            return past_responses

        try:
            response_text = response_text.strip()
            logger.debug(f"=== PARSING AGENT RESPONSE ===")
            logger.debug(f"Full response length: {len(response_text)} chars")
            logger.debug(f"Response preview: {response_text[:500]}...")

            # Try to parse as JSON first (Agent may return structured JSON)
            import json
            try:
                # Check if response contains a JSON list
                if '[' in response_text and ']' in response_text:
                    # Extract FIRST complete JSON array from response
                    # This handles cases where JSON is printed multiple times
                    start_idx = response_text.find('[')
                    if start_idx >= 0:
                        # Find the matching closing bracket for this JSON array
                        bracket_count = 0
                        end_idx = start_idx
                        for i in range(start_idx, len(response_text)):
                            if response_text[i] == '[':
                                bracket_count += 1
                            elif response_text[i] == ']':
                                bracket_count -= 1
                                if bracket_count == 0:
                                    end_idx = i + 1
                                    break

                        if end_idx > start_idx:
                            json_str = response_text[start_idx:end_idx]
                            logger.debug(f"Attempting to parse JSON: {json_str[:200]}...")
                            results = json.loads(json_str)

                            if isinstance(results, list):
                                logger.info(f"Parsed {len(results)} results from JSON")
                                for item in results:
                                    if isinstance(item, dict) and "source_file" in item and "content" in item:
                                        response = {
                                            "filename": item.get("source_file", "Unknown"),
                                            "section_title": item.get("section_title", "General"),
                                            "relevance": item.get("relevance", "Matching category"),
                                            "summary": item.get("content", ""),
                                            "categories": requested_categories,
                                            "files_used": [item.get("source_file", "Unknown")],
                                            "date_created": "Unknown"
                                        }
                                        past_responses.append(response)
                                        logger.debug(f"Extracted: {response['filename']} - {response['section_title']}")

                                logger.info(f"Parsed {len(past_responses)} past responses from JSON")
                                if len(past_responses) > 0:
                                    return past_responses
            except (json.JSONDecodeError, Exception) as e:
                logger.debug(f"JSON parsing failed ({str(e)}), trying alternative parsing methods")

            # Parse plain text structured format
            # Look for patterns like "Source File: name.md", "Section Title: title", etc.
            logger.info("Agent likely returned plain text structured response - parsing fields...")

            import re
            sections = re.split(r'\n\s*-{3,}\s*\n|\n\s*\n', response_text)

            for section in sections:
                if not section.strip() or len(section.strip()) < 20:
                    continue

                # Extract structured fields using patterns (case-insensitive)
                source_file_match = re.search(r'(?:Source\s+File|source_file|^\s*File)\s*:\s*([^\n]+\.md)', section, re.IGNORECASE | re.MULTILINE)
                title_match = re.search(r'(?:Section\s+Title|Section|Title)\s*:\s*([^\n]+)', section, re.IGNORECASE)
                relevance_match = re.search(r'(?:Relevance|Relevant|Directory)\s*:\s*([^\n]+)', section, re.IGNORECASE)
                content_match = re.search(r'(?:Content|Section\s+Content)\s*:\s*(.+?)(?:\n(?:\*|Source|Section|Directory|File)|$)', section, re.IGNORECASE | re.DOTALL)

                source_file = source_file_match.group(1).strip() if source_file_match else None
                section_title = title_match.group(1).strip() if title_match else "Extracted Section"
                relevance = relevance_match.group(1).strip() if relevance_match else "Matching query"

                # Get content
                if content_match:
                    content = content_match.group(1).strip()[:3000]
                else:
                    content = section.strip()[:1000]

                if source_file:
                    response = {
                        "filename": source_file,
                        "section_title": section_title,
                        "relevance": relevance,
                        "content": content,  # Full 3000 chars for synthesis
                        "summary": content[:250],  # First 250 chars for display
                        "categories": requested_categories,
                        "files_used": [source_file],
                        "date_created": "Unknown"
                    }
                    past_responses.append(response)
                    logger.debug(f"Extracted: {source_file} - {section_title}")

            if past_responses:
                logger.info(f"Parsed {len(past_responses)} past responses from structured text")
                return past_responses

            # Fallback: look for any .md file mentions
            logger.info("Fallback: searching for .md file mentions...")
            md_pattern = r'([^\s:/\\]+\.md)'
            md_files = re.findall(md_pattern, response_text)

            if md_files:
                logger.info(f"Found {len(set(md_files))} .md file mentions")
                for filename in list(set(md_files))[:self.MAX_RESULTS]:
                    response = {
                        "filename": filename,
                        "section_title": "Extracted Section",
                        "relevance": "Matching query",
                        "summary": response_text[:1000],
                        "categories": requested_categories,
                        "files_used": [filename],
                        "date_created": "Unknown"
                    }
                    past_responses.append(response)

            if not past_responses:
                logger.warning(f"Could not parse any past responses from Agent output")

            logger.info(f"Parsed {len(past_responses)} past responses from Agent response")
            return past_responses

        except Exception as e:
            logger.error(f"Error parsing Agent response: {e}", exc_info=True)
            logger.warning(f"Response text was: {response_text[:500]}...")
            return past_responses
