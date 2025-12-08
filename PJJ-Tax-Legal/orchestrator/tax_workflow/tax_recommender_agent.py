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
    MAX_NEW_RESULTS = 20

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

            # Build directory list for Agent
            category_dirs = [str(Path("tax_database") / dir_name) for dir_name in actual_dir_names]

            # Build suggested files text if provided
            suggested_files_text = ""
            if suggested_files:
                suggested_files_text = f"\n\nAlso consider these pre-selected documents:\n" + \
                    "\n".join([f"- {f}" for f in suggested_files])

            # CRITICAL: Use Python code to navigate directories and read files
            # Agent must write Python code that uses list_files(), read_file(), etc.
            # Use ABSOLUTE paths from the memory directory
            memory_base = self.memory_path
            absolute_category_dirs = [f'{memory_base}/{d}' for d in category_dirs]

            # IMPROVED PROMPT - Requirements as comments, not example code
            # Agent must write its own executable Python code
            constrained_query = f"""You MUST respond with ONLY these sections:

<think>
[Your plan to search these directories for relevant tax regulations]
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
#        - Append dict to results with keys: 'source_file', 'category', 'content', 'directory'
#        - 'content' should be content[:3000] (first 3000 chars)
#        - 'category' should be dir_path.split('/')[-1]
#        - 'source_file' should be filename
#        - 'directory' should be root
# 4. Wrap file operations in try/except to handle errors
#
# Write the actual executable Python code below (not comments):
</python>

CRITICAL: Your <python> section must contain ACTUAL executable code that creates the 'results' variable."""

            logger.debug(f"Constrained query: {constrained_query[:200]}...")

            # MEMAGENT NAVIGATION: Use Agent.chat() for intelligent memory search
            logger.info("=== EXECUTING MEMAGENT SEARCH (Step 4) ===")
            logger.info(f"Query: {request[:100]}...")
            logger.info(f"Categories constraint: {categories}")
            logger.info("Using Agent to navigate tax_database...")

            # CRITICAL: Create a FRESH Agent instance to avoid context overflow
            # Each step gets its own clean context window (fresh conversation history)
            # max_tool_turns=1 ensures single execution of template code (no refinement modifications)
            from agent import Agent
            fresh_agent = Agent(memory_path=str(self.memory_path), max_tool_turns=1)
            logger.info("Created fresh Agent instance for this search (max_tool_turns=1)")

            # Call fresh Agent to search memory
            # Agent will read tax_database and return matches
            agent_response = fresh_agent.chat(constrained_query)

            search_time_ms = (time.time() - start_time) * 1000
            logger.info(f"Agent search completed in {search_time_ms:.1f}ms")
            logger.info(f"Execution results available: {agent_response.execution_results is not None}")

            # Extract documents from Agent's execution results
            # The Agent's Python code creates a 'results' variable with extracted content
            documents = []
            if agent_response.execution_results and "results" in agent_response.execution_results:
                # Results variable is available from Python code execution
                raw_results = agent_response.execution_results.get("results", [])
                logger.info(f"Found {len(raw_results)} results from Agent execution")

                # Convert Agent's raw results to structured format
                for result in raw_results:
                    if isinstance(result, dict):
                        full_text = result.get("content", "")  # Get the 3000-char content
                        documents.append({
                            "filename": result.get("source_file", "Unknown"),
                            "category": result.get("category", "Unknown"),
                            "section_title": result.get("section_title", "Section"),
                            "application": result.get("application", "Relevant"),
                            "content": full_text,  # Full 3000 chars for synthesis
                            "summary": full_text[:250],  # First 250 chars for display
                            "categories": categories,
                            "files_used": [result.get("source_file", "Unknown")],
                            "date_created": "Unknown"
                        })
            else:
                # Fallback: try to parse Agent's reply text (for backward compatibility)
                logger.debug("No execution results found, attempting text parsing fallback")
                documents = self._parse_agent_response(
                    agent_response.reply or "",
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
                    "content": doc.get("content", ""),  # Full 3000 chars preserved for synthesis
                    "summary": doc.get("summary", "")  # Already 250 chars from line 242
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
        Parse Agent's Python code execution response to extract documents.

        Agent executes Python code that creates a 'results' variable containing:
        [
            {
                "source_file": "filename.md",
                "category": "Category Name",
                "section_title": "Section Title",
                "application": "How this applies",
                "content": "actual regulatory text",
                "directory": "tax_database/XX_Category/"
            },
            ...
        ]

        Args:
            response_text: Agent's response after Python code execution
            requested_categories: Categories the user requested

        Returns:
            List of structured document objects with full content
        """
        documents = []

        if not response_text or len(response_text.strip()) == 0:
            logger.warning("Agent returned empty response - likely no files found in directories")
            return documents

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
                    # Extract JSON array from response
                    start_idx = response_text.find('[')
                    end_idx = response_text.rfind(']') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx]
                        results = json.loads(json_str)

                        if isinstance(results, list):
                            logger.info(f"Parsed {len(results)} results from JSON")
                            for item in results:
                                if isinstance(item, dict) and "source_file" in item and "content" in item:
                                    doc = {
                                        "filename": item.get("source_file", "Unknown"),
                                        "category": item.get("category", requested_categories[0] if requested_categories else "General"),
                                        "section_title": item.get("section_title", "General"),
                                        "application": item.get("application", "Matching category"),
                                        "size": "Unknown",
                                        "date_issued": "Unknown",
                                        "summary": item.get("content", "")
                                    }
                                    documents.append(doc)
                                    logger.debug(f"Extracted: {doc['filename']} - {doc['section_title']}")

                            logger.info(f"Parsed {len(documents)} documents from JSON")
                            return documents
            except json.JSONDecodeError:
                logger.debug("Response is not JSON, trying alternative parsing methods")

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
                category_match = re.search(r'(?:Category|Directory)\s*:\s*([^\n]+)', section, re.IGNORECASE)
                title_match = re.search(r'(?:Section\s+Title|Section|Title)\s*:\s*([^\n]+)', section, re.IGNORECASE)
                application_match = re.search(r'(?:Application|Relevance)\s*:\s*([^\n]+)', section, re.IGNORECASE)
                content_match = re.search(r'(?:Content|Section\s+Content)\s*:\s*(.+?)(?:\n(?:\*|Source|Section|Category|Directory|File)|$)', section, re.IGNORECASE | re.DOTALL)

                source_file = source_file_match.group(1).strip() if source_file_match else None
                category = category_match.group(1).strip() if category_match else (requested_categories[0] if requested_categories else "General")
                section_title = title_match.group(1).strip() if title_match else "Extracted Section"
                application = application_match.group(1).strip() if application_match else "Matching query"

                # Get content
                if content_match:
                    content = content_match.group(1).strip()[:2000]
                else:
                    content = section.strip()[:1000]

                if source_file:
                    doc = {
                        "filename": source_file,
                        "category": category,
                        "section_title": section_title,
                        "application": application,
                        "size": "Unknown",
                        "date_issued": "Unknown",
                        "content": content,  # Full 3000 chars for synthesis
                        "summary": content[:250]  # First 250 chars for display
                    }
                    documents.append(doc)
                    logger.debug(f"Extracted: {source_file} - {section_title}")

            if documents:
                logger.info(f"Parsed {len(documents)} documents from structured text")
                return documents

            # Fallback: look for any .md file mentions
            logger.info("Fallback: searching for .md file mentions...")
            md_pattern = r'([^\s:/\\]+\.md)'
            md_files = re.findall(md_pattern, response_text)

            if md_files:
                logger.info(f"Found {len(set(md_files))} .md file mentions")
                for filename in list(set(md_files))[:self.MAX_NEW_RESULTS]:
                    doc = {
                        "filename": filename,
                        "category": requested_categories[0] if requested_categories else "General",
                        "section_title": "Extracted Section",
                        "application": "Matching query",
                        "size": "Unknown",
                        "date_issued": "Unknown",
                        "summary": response_text[:1000]
                    }
                    documents.append(doc)

            if not documents:
                logger.warning(f"Could not parse any documents from Agent output")

            logger.info(f"Parsed {len(documents)} documents from Agent response")
            return documents

        except Exception as e:
            logger.error(f"Error parsing Agent response: {e}", exc_info=True)
            logger.warning(f"Response text was: {response_text[:500]}...")
            return documents
