"""
RequestCategorizer - Step 1 Agent

Analyzes client tax requests and suggests relevant tax domains/categories.
Used to establish user-selected constraint boundary for downstream searches.

CONSTRAINT BOUNDARIES:
- NO MemAgent search (classification only, uses keyword detection + Llama)
- Input: request string (minimum 10 characters)
- Output: suggested_categories list with confidence scores
- User confirms these categories before any MemAgent searches happen

This agent does NOT access memory. It only performs request classification.
Output categories become the user boundary for Steps 2 and 4 searches.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from orchestrator.agents.base_agent import BaseAgent, AgentResult
from agent.logging_config import get_logger, log_agent_call, log_agent_response, log_agent_error, log_json_parsing

logger = get_logger(__name__)


class RequestCategorizer(BaseAgent):
    """
    Categorizes incoming tax requests into relevant tax domains.

    Uses keyword-based detection + Llama classification to suggest
    tax categories that the user will confirm before searches.

    CONSTRAINT BOUNDARIES:
    - NO MemAgent search (classification only)
    - Input validation: request must be >= 10 characters
    - Output: suggested_categories list with confidence
    - Output becomes user boundary for downstream searches

    Categories Available:
    - CIT: Corporate Income Tax
    - VAT: Value Added Tax
    - Transfer Pricing: Intercompany pricing
    - PIT: Personal Income Tax
    - FCT: Foreign Contractor Tax
    - DTA: Double Taxation Agreements
    - Customs: Import/Export duties
    - Excise Tax: Special goods taxation
    - Environmental Tax: Pollution/resource taxes
    - Capital Gains: Investment income
    """

    # Tax domain keywords for initial classification
    DOMAIN_KEYWORDS = {
        "CIT": ["corporate", "company", "cit", "profit", "business", "income", "enterprise", "corporation"],
        "VAT": ["vat", "value added", "tax invoice", "output tax", "input tax", "gst", "iva"],
        "Transfer Pricing": ["transfer pricing", "tp", "arm's length", "intercompany", "related party", "pricing", "comparable"],
        "PIT": ["personal income", "pit", "individual", "salary", "wage", "freelancer", "self-employed"],
        "FCT": ["foreign contractor", "fct", "service provider", "expatriate", "foreign worker", "withholding"],
        "DTA": ["double taxation", "dta", "tax treaty", "treaty", "vietnam treaty", "agreement"],
        "Customs": ["customs", "import", "export", "tariff", "duty", "border", "clearance"],
        "Excise Tax": ["excise", "special excise", "alcohol", "tobacco", "petrol", "fuel"],
        "Environmental Tax": ["environmental", "eco tax", "water", "waste", "forest", "environment"],
        "Capital Gains": ["capital gains", "investment", "stock", "capital", "asset sale", "profit on sale"]
    }

    def __init__(self, agent: Agent, memory_path: Path):
        """
        Initialize RequestCategorizer

        Args:
            agent: MemAgent instance (used for Llama, not for memory search)
            memory_path: Path to memory directory
        """
        super().__init__(agent, memory_path)
        self.agent = agent
        self.memory_path = Path(memory_path) if isinstance(memory_path, str) else memory_path

    def generate(self, request: str) -> AgentResult:
        """
        Classify tax request and suggest relevant categories

        Args:
            request: The client's tax question/request

        Returns:
            AgentResult with:
            - success: True if classification succeeded
            - output: {"suggested_categories": [...], "confidence": float}
            - metadata: Classification details
            - error: Empty string on success
        """
        try:
            logger.info(f"=== RequestCategorizer.generate() STARTED ===")
            logger.info(f"Input request: '{request[:100]}...' (length: {len(request)})")

            # Validate input
            if not request or len(request.strip()) < 10:
                logger.warning(f"Input validation failed: request too short (length: {len(request) if request else 0})")
                return AgentResult(
                    success=False,
                    output={},
                    metadata={
                        "error": "Request too short",
                        "min_length": 10,
                        "actual_length": len(request) if request else 0
                    },
                    timestamp=datetime.now().isoformat(),
                    error="Request must be at least 10 characters"
                )

            logger.info("Input validation passed")

            # Step 1: Keyword-based detection
            logger.info("Step 1: Running keyword-based classification...")
            request_lower = request.lower()
            keyword_scores = self._keyword_classification(request_lower)
            logger.debug(f"Keyword classification results: {keyword_scores}")

            # Step 2: Llama-based classification (for verification/nuance)
            logger.info("Step 2: Running Llama-based classification...")
            llama_scores = self._llama_classification(request)
            logger.debug(f"Llama classification results: {llama_scores}")

            # Step 3: Combine scores (weighted average)
            logger.info("Step 3: Combining keyword and Llama scores...")
            combined_scores = self._combine_scores(keyword_scores, llama_scores)
            logger.debug(f"Combined scores: {combined_scores}")

            # Step 4: Select top categories (threshold: >0.3)
            logger.info("Step 4: Selecting top categories (threshold > 0.3)...")
            suggested_categories = [
                cat for cat, score in combined_scores.items()
                if score > 0.3
            ]
            logger.info(f"Found {len(suggested_categories)} categories above threshold: {suggested_categories}")

            # If no categories found, return all with lower confidence
            if not suggested_categories:
                logger.warning("No categories above threshold, selecting top 3 by score...")
                suggested_categories = sorted(
                    combined_scores.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]  # Return top 3
                suggested_categories = [cat for cat, _ in suggested_categories]
                logger.info(f"Selected fallback categories: {suggested_categories}")

            # Calculate overall confidence
            scores = [combined_scores.get(cat, 0) for cat in suggested_categories]
            avg_confidence = sum(scores) / len(scores) if scores else 0.5
            logger.info(f"Overall confidence score: {round(avg_confidence, 2)}")

            # Sort by confidence (highest first)
            suggested_categories.sort(
                key=lambda x: combined_scores.get(x, 0),
                reverse=True
            )
            logger.debug(f"Categories sorted by confidence: {suggested_categories}")

            # Format output
            output = {
                "suggested_categories": suggested_categories,
                "confidence": round(avg_confidence, 2),
                "confidence_by_category": {
                    cat: round(combined_scores.get(cat, 0), 2)
                    for cat in suggested_categories
                }
            }

            # Metadata for audit trail
            metadata = {
                "classification_method": "keyword + Llama (weighted)",
                "keyword_matches": {
                    cat: score for cat, score in keyword_scores.items()
                    if score > 0
                },
                "llama_scores": llama_scores,
                "combined_scores": {
                    cat: round(score, 2)
                    for cat, score in combined_scores.items()
                },
                "threshold": 0.3,
                "request_length": len(request),
                "categories_count": len(suggested_categories)
            }

            logger.info(f"=== RequestCategorizer.generate() COMPLETED SUCCESSFULLY ===")
            logger.info(f"Final output: {output}")
            logger.debug(f"Metadata: {metadata}")

            return AgentResult(
                success=True,
                output=output,
                metadata=metadata,
                timestamp=datetime.now().isoformat(),
                error=""
            )

        except Exception as e:
            logger.error(f"=== RequestCategorizer.generate() FAILED ===")
            log_agent_error(logger, "RequestCategorizer", "generate", e)
            return self._handle_error("RequestCategorizer classification", e)

    def _keyword_classification(self, request_lower: str) -> Dict[str, float]:
        """
        Classify request using keyword matching

        Args:
            request_lower: Request text in lowercase

        Returns:
            Dict mapping domain -> confidence score (0-1)
        """
        scores = {}

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            # Count keyword matches
            matches = sum(
                request_lower.count(keyword)
                for keyword in keywords
            )

            # Normalize to 0-1 range (cap at 5 matches = score 1.0)
            score = min(matches / 5, 1.0)
            scores[domain] = score

        return scores

    def _llama_classification(self, request: str) -> Dict[str, float]:
        """
        Use Llama to classify request for additional context

        Args:
            request: Original request text

        Returns:
            Dict mapping domain -> confidence score (0-1)
        """
        try:
            prompt = f"""Analyze this tax request and rate its relevance to each tax domain (0-1 scale).

Tax Domains:
- CIT: Corporate Income Tax
- VAT: Value Added Tax
- Transfer Pricing: Intercompany pricing
- PIT: Personal Income Tax
- FCT: Foreign Contractor Tax
- DTA: Double Taxation Agreements
- Customs: Import/Export duties
- Excise Tax: Special goods taxation
- Environmental Tax: Pollution/resource taxes
- Capital Gains: Investment income

Request: "{request}"

Respond ONLY with JSON format:
{{
  "CIT": 0.0-1.0,
  "VAT": 0.0-1.0,
  "Transfer Pricing": 0.0-1.0,
  "PIT": 0.0-1.0,
  "FCT": 0.0-1.0,
  "DTA": 0.0-1.0,
  "Customs": 0.0-1.0,
  "Excise Tax": 0.0-1.0,
  "Environmental Tax": 0.0-1.0,
  "Capital Gains": 0.0-1.0
}}"""

            logger.debug(f"Sending prompt to Agent.generate_response()")
            response = self.agent.generate_response(prompt)
            logger.debug(f"Received response from Agent (length: {len(response)})")

            # Check if response is empty
            if not response:
                logger.error("CRITICAL: Agent.generate_response() returned EMPTY response")
                logger.warning("Using fallback neutral scores due to empty response")
                return {domain: 0.5 for domain in self.DOMAIN_KEYWORDS}

            logger.debug(f"Raw response (first 500 chars): {response[:500]}...")

            # Try to parse JSON from response
            try:
                # Look for JSON in response
                import json
                json_start = response.find('{')
                json_end = response.rfind('}') + 1

                if json_start < 0 or json_end <= json_start:
                    logger.error(f"CRITICAL: No JSON found in response (searched {len(response)} chars)")
                    logger.error(f"Response content: {response[:300]}...")
                    logger.warning("Using fallback neutral scores due to missing JSON")
                    return {domain: 0.5 for domain in self.DOMAIN_KEYWORDS}

                json_str = response[json_start:json_end]
                logger.debug(f"Extracted JSON substring ({len(json_str)} chars): {json_str[:200]}...")

                scores = json.loads(json_str)
                logger.debug(f"Successfully parsed JSON with {len(scores)} keys: {list(scores.keys())[:3]}...")

                # Validate and normalize scores
                normalized = {}
                for domain in self.DOMAIN_KEYWORDS.keys():
                    score = scores.get(domain, 0)
                    normalized[domain] = max(0, min(float(score), 1.0))

                logger.debug(f"Normalized scores: {normalized}")
                logger.info(f"Llama classification SUCCEEDED with scores: {normalized}")
                return normalized
            except json.JSONDecodeError as parse_error:
                logger.error(f"CRITICAL: JSON parsing failed: {parse_error}")
                logger.error(f"Failed response was: {response[:500]}...")
                logger.warning("Using fallback neutral scores due to JSON parsing error")
                return {domain: 0.5 for domain in self.DOMAIN_KEYWORDS}
            except (ValueError, KeyError, TypeError) as parse_error:
                logger.error(f"CRITICAL: Response validation failed: {parse_error}")
                logger.error(f"Failed response was: {response[:500]}...")
                logger.warning("Using fallback neutral scores due to response validation error")
                return {domain: 0.5 for domain in self.DOMAIN_KEYWORDS}

        except Exception as e:
            logger.error(f"CRITICAL: Llama classification error: {e}", exc_info=True)
            logger.warning("Using fallback neutral scores due to exception")
            # Return neutral scores on error
            return {domain: 0.5 for domain in self.DOMAIN_KEYWORDS}

    def _combine_scores(
        self,
        keyword_scores: Dict[str, float],
        llama_scores: Dict[str, float],
        keyword_weight: float = 0.6,
        llama_weight: float = 0.4
    ) -> Dict[str, float]:
        """
        Combine keyword and Llama scores using weighted average

        Args:
            keyword_scores: Scores from keyword matching
            llama_scores: Scores from Llama classification
            keyword_weight: Weight for keyword scores (default 0.6)
            llama_weight: Weight for Llama scores (default 0.4)

        Returns:
            Dict mapping domain -> combined confidence score
        """
        combined = {}

        for domain in self.DOMAIN_KEYWORDS.keys():
            kw_score = keyword_scores.get(domain, 0)
            llama_score = llama_scores.get(domain, 0.5)

            # Weighted average
            combined_score = (kw_score * keyword_weight) + (llama_score * llama_weight)
            combined[domain] = max(0, min(combined_score, 1.0))

        return combined
