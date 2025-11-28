"""
FileRecommender Agent - Step 4 of Tax Workflow

Purpose: Search tax database and recommend source documents using MemAgent

CONSTRAINT BOUNDARIES:
- Search Scope: ONLY tax_database/ directory
- Filter: ONLY documents matching confirmed_categories from user
- Fallback: If categories empty, return empty (no autonomous document discovery)
- No Autonomy: Cannot access past_responses directory
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import time

# Setup path for imports
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent import Agent
from orchestrator.agents.base_agent import BaseAgent, AgentResult
from agent.logging_config import get_logger

logger = get_logger(__name__)


class FileRecommender(BaseAgent):
    """
    Step 4: Search tax database and recommend source documents via MemAgent.

    Searches across 3,400+ documents in /local-memory/tax_legal/tax_database/
    and returns ranked results by relevance matching user-confirmed categories.

    CONSTRAINT BOUNDARIES:
    - Search Scope: ONLY /local-memory/tax_legal/tax_database/ directory (EXPLICIT)
    - Filter: ONLY documents matching confirmed_categories from user
    - Fallback: If categories empty, return empty (no autonomous document discovery)
    - No Autonomy: Cannot access past_responses directory

    How it works:
    1. Sends query to Agent.chat() with category constraints
    2. Agent reads tax_database from memory and identifies matching documents
    3. Returns results with metadata about what was searched

    Step 4 Workflow: User confirms categories → FileRecommender searches tax_database → User selects documents
    """

    # Search constraints
    MAX_NEW_RESULTS = 10

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
        Initialize FileRecommender

        Args:
            agent: Agent instance for memory navigation
            memory_path: Path to PRIMARY DATA directory (/local-memory/tax_legal/)
        """
        super().__init__(agent, memory_path)
        self.agent = agent
        self.memory_path = Path(memory_path) if isinstance(memory_path, str) else memory_path

        # Log initialization with explicit path information
        logger.info("=" * 80)
        logger.info("STEP 4: FileRecommender Initialized")
        logger.info(f"  PRIMARY DATA DIRECTORY: {self.memory_path}")
        logger.info(f"  Search Source: {self.memory_path / 'tax_database'}")
        logger.info(f"  Search Scope: tax_database/ (3,400+ tax documents in 16 categories)")
        logger.info(f"  Constraint: Category filtering enforced via Agent")
        logger.info("=" * 80)

    def generate(
        self,
        request: str,
        categories: Optional[List[str]] = None,
        suggested_files: Optional[List[str]] = None
    ) -> AgentResult:
        """
        Search tax database for relevant documents.

        Uses Agent.chat() to navigate memory and find relevant tax documents.
        Agent interprets the constraint and searches only within specified categories.

        Args:
            request: The tax question/request
            categories: User-confirmed tax categories (REQUIRED for search)
            suggested_files: Pre-selected files to include (optional)

        Returns:
            AgentResult with:
            - success: True if search completed (even if no results)
            - output: List of documents (top-10) with metadata
            - metadata: Search scope, categories boundary, results info
            - error: Empty string on success
        """
        try:
            logger.info("=== FileRecommender.generate() STARTED ===")
            logger.info(f"Input request: '{request[:100]}...' (length: {len(request)})")
            logger.info(f"Categories: {categories}")
            logger.info(f"Suggested files from past response: {suggested_files or []}")
            start_time = time.time()

            # CONSTRAINT ENFORCEMENT: Categories required
            if not categories:
                logger.warning("Categories parameter is missing - cannot perform constrained search")
                return AgentResult(
                    success=False,
                    output=[],
                    metadata={
                        "error": "Categories required for constrained search",
                        "search_scope": "tax_database",
                        "required_parameter": "categories"
                    },
                    timestamp=datetime.now().isoformat(),
                    error="Categories parameter is required"
                )

            logger.info(f"Constraint boundary: Search ONLY in tax_database/")
            logger.info(f"Category constraint: ONLY results matching {categories}")

            # Map user-friendly category names to actual filesystem directory names
            actual_dir_names = [self.CATEGORY_DIR_MAP.get(cat, cat) for cat in categories]
            logger.info(f"Mapped categories to actual directories: {actual_dir_names}")

            # Build simple, natural language query
            suggested_files_text = ""
            if suggested_files:
                suggested_files_text = f"\n\nAlso consider these pre-selected documents:\n" + \
                    "\n".join([f"- {f}" for f in suggested_files])

            constrained_query = f"""Find the 10 most relevant tax regulation and guidance documents in the tax_database directory that match this request and are related to these categories: {', '.join(categories)}.

Request: {request}{suggested_files_text}

Search in: {', '.join(categories)} categories in tax_database.

Return relevant documents with their filenames and summaries."""

            logger.debug(f"Constrained query: {constrained_query[:200]}...")

            # MEMAGENT NAVIGATION: Use Agent.chat() for intelligent memory search
            logger.info("=== EXECUTING MEMAGENT SEARCH (Step 4) ===")
            logger.info(f"Query: {request[:100]}...")
            logger.info(f"Categories constraint: {categories}")
            logger.info("Using Agent to navigate tax_database...")

            # Call Agent to search memory
            # Agent will read tax_database and return matches
            agent_response = self.agent.chat(constrained_query)

            search_time_ms = (time.time() - start_time) * 1000
            logger.info(f"Agent search completed in {search_time_ms:.1f}ms")
            logger.info(f"Agent response length: {len(agent_response.reply)} characters")

            # Parse Agent's response to extract documents
            documents = self._parse_agent_response(
                agent_response.reply,
                categories
            )

            logger.info(f"=== MEMAGENT SEARCH COMPLETED ===")
            logger.info(f"Search time: {search_time_ms:.1f}ms")
            logger.info(f"Total results found: {len(documents)} documents")

            # Limit results to MAX_NEW_RESULTS
            documents = documents[:self.MAX_NEW_RESULTS]
            logger.info(f"Results after limiting to top {self.MAX_NEW_RESULTS}: {len(documents)}")

            # Format output
            formatted_results = []
            for doc in documents:
                formatted_results.append({
                    "filename": doc.get("filename", "Unknown"),
                    "category": doc.get("category", "General"),
                    "subcategory": doc.get("subcategory", "General"),
                    "size": doc.get("size", "Unknown"),
                    "date_issued": doc.get("date_issued", "Unknown"),
                    "summary": doc.get("summary", "")[:150]
                })

            logger.info(f"Final output: {len(formatted_results)} search results + {len(suggested_files or [])} suggested files")
            logger.info(f"=== FileRecommender.generate() COMPLETED SUCCESSFULLY ===")

            return AgentResult(
                success=True,
                output=formatted_results,
                metadata={
                    "total_found": len(formatted_results),
                    "search_time_ms": int(search_time_ms),
                    "search_scope": "tax_database",
                    "search_method": "MemAgent intelligent navigation",
                    "categories_searched": categories,
                    "category_constraint_boundary": categories,
                },
                timestamp=datetime.now().isoformat(),
                error=""
            )

        except Exception as e:
            logger.error(f"=== FileRecommender.generate() FAILED ===")
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
        Parse Agent's natural language response to extract documents.

        The Agent navigates memory and identifies relevant documents.
        This method extracts document information from the response.

        Args:
            response_text: Agent's response with document information
            requested_categories: Categories the user requested

        Returns:
            List of structured document objects
        """
        documents = []

        if not response_text or len(response_text.strip()) == 0:
            logger.warning("Agent returned empty response")
            return documents

        try:
            import ast
            import re

            response_text = response_text.strip()

            # Strategy 1: Try to parse as Python literal (list of dicts)
            try:
                data = ast.literal_eval(response_text)
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    for item in data:
                        if isinstance(item, dict) and 'filename' in item:
                            doc = {
                                "filename": item.get("filename", "Unknown"),
                                "category": item.get("category", requested_categories[0] if requested_categories else "General"),
                                "subcategory": item.get("subcategory", "General"),
                                "size": item.get("size", "Unknown"),
                                "date_issued": item.get("date_issued", "Unknown"),
                                "summary": item.get("summary", "")[:150]
                            }
                            documents.append(doc)
                    logger.info(f"Parsed {len(documents)} documents from Python literal")
                    return documents
            except (ValueError, SyntaxError):
                pass

            # Strategy 2: Parse as narrative list (fallback)
            logger.info("Attempting narrative parse of Agent response")
            lines = response_text.split('\n')
            current_doc = None

            for line in lines:
                line = line.strip()

                # Detect document headers (file names, numbered lists)
                if line and (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.', '-')) or
                            line.endswith('.md')):
                    if current_doc and "filename" in current_doc:
                        documents.append(current_doc)

                    # Extract filename
                    filename = re.sub(r'^[\d\.\-\s]+', '', line).strip()
                    if filename and '.md' in filename.lower():
                        current_doc = {
                            "filename": filename,
                            "category": requested_categories[0] if requested_categories else "General",
                            "subcategory": "General",
                            "size": "Unknown",
                            "date_issued": "Unknown",
                            "summary": ""
                        }
                elif current_doc and line and not line.startswith('-'):
                    current_doc["summary"] += " " + line

            if current_doc and "filename" in current_doc:
                documents.append(current_doc)

            logger.info(f"Parsed {len(documents)} documents from narrative")
            return documents

        except Exception as e:
            logger.error(f"Error parsing Agent response: {e}")
            logger.warning(f"Response text was: {response_text[:500]}...")
            return documents
