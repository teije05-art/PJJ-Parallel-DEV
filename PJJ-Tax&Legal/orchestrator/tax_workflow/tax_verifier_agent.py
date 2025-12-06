"""
DocumentVerifier Agent - Step 6a of Tax Workflow

Purpose: Verification gate with hallucination detection

CONSTRAINT BOUNDARIES:
- Verification Scope: ONLY validate against provided source_file_contents
- Detection: Flag any claims that cannot be sourced (hallucinations)
- Quality Gate: 100% of claims must be verifiable (or flagged)
- Fail-Safe: Cannot approve response if >10% unsourced claims
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import re
import time

# Setup path for imports
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent import Agent
from orchestrator.agents.base_agent import BaseAgent, AgentResult
from agent.logging_config import get_logger

logger = get_logger(__name__)


class DocumentVerifier(BaseAgent):
    """
    Step 6a: Verify response against source documents

    Checks that every claim in the response can be traced
    to a source document (no hallucinations).

    CONSTRAINT BOUNDARIES:
    - Verification Scope: ONLY validate against provided source_file_contents
    - Detection: Flag any claims that cannot be sourced (hallucinations)
    - Quality Gate: 100% of claims must be verifiable (or flagged)
    - Fail-Safe: Cannot approve response if >10% unsourced claims
    """

    # Hallucination threshold: max percentage of unsourced claims allowed
    MAX_UNSOURCED_PERCENTAGE = 10  # 10% tolerance

    def __init__(self, agent: Agent, memory_path: Path):
        super().__init__(agent, memory_path)
        self.agent = agent

    def generate(
        self,
        response: str,
        selected_file_contents: Dict[str, str]
    ) -> AgentResult:
        """
        Verify response against source documents.

        Args:
            response: Synthesized response text
            selected_file_contents: Source documents {filename: content}

        Returns:
            AgentResult with verification report
        """
        try:
            logger.info("=== DocumentVerifier.generate() STARTED ===")
            logger.info(f"Response length: {len(response)} characters")
            logger.info(f"Source documents provided: {len(selected_file_contents)}")
            logger.info(f"Source filenames: {list(selected_file_contents.keys())}")
            start_time = time.time()

            # Validate inputs
            if not response:
                logger.error("Response is empty")
                raise ValueError("Response cannot be empty")
            if not selected_file_contents:
                logger.error("No source documents provided")
                raise ValueError("Source documents required for verification")

            logger.info("Input validation passed")

            # Extract claims from response
            logger.info("Extracting claims from response...")
            claims = self._extract_claims(response)
            logger.info(f"Extracted {len(claims)} claims from response")

            if not claims:
                # No claims to verify (empty response)
                logger.warning("No claims extracted from response")
                return AgentResult(
                    success=True,
                    output={
                        "all_verified": True,
                        "verified_count": 0,
                        "total_claims": 0,
                        "issues": [],
                        "can_approve": True,
                        "approval_status": "NO_CLAIMS_FOUND"
                    },
                    metadata={
                        "verification_method": "source_matching",
                        "verification_time_ms": 0,
                        "claim_extraction_method": "sentence_splitting"
                    },
                    timestamp=datetime.now().isoformat(),
                    error=""
                )

            # Verify each claim against sources using Llama
            logger.info(f"Verifying {len(claims)} claims against {len(selected_file_contents)} source documents...")
            logger.info("Using Llama for semantic verification (not just keyword matching)...")
            verification_results = []
            for claim_id, claim_text in enumerate(claims):
                is_verified = self._verify_claim_with_llama(claim_text, selected_file_contents)
                verification_results.append({
                    "claim_id": claim_id,
                    "claim": claim_text[:100],  # Truncate for display
                    "status": "verified" if is_verified else "unverified",
                    "issue_type": None if is_verified else "unsourced_claim"
                })
                if is_verified:
                    logger.debug(f"Claim {claim_id}: VERIFIED by Llama")
                else:
                    logger.debug(f"Claim {claim_id}: UNVERIFIED by Llama (potential hallucination)")

            # Summarize verification
            verified_count = sum(1 for r in verification_results if r["status"] == "verified")
            total_claims = len(verification_results)
            unsourced_count = total_claims - verified_count
            unsourced_percentage = (unsourced_count / total_claims * 100) if total_claims > 0 else 0

            logger.info(f"Verification complete: {verified_count}/{total_claims} claims verified")
            logger.info(f"Unsourced claims: {unsourced_count} ({unsourced_percentage:.1f}%)")

            # Determine if response can be approved
            can_approve = unsourced_percentage <= self.MAX_UNSOURCED_PERCENTAGE
            logger.info(f"Hallucination threshold: {self.MAX_UNSOURCED_PERCENTAGE}% (unsourced: {unsourced_percentage:.1f}%)")
            logger.info(f"Approval decision: {'APPROVED' if can_approve else 'REJECTED (too many hallucinations)'}")

            issues = [r for r in verification_results if r["status"] == "unverified"]

            processing_time_ms = (time.time() - start_time) * 1000
            logger.info(f"=== DocumentVerifier.generate() COMPLETED SUCCESSFULLY in {processing_time_ms:.1f}ms ===")

            return AgentResult(
                success=True,
                output={
                    "all_verified": verified_count == total_claims,
                    "verified_count": verified_count,
                    "total_claims": total_claims,
                    "unsourced_count": unsourced_count,
                    "unsourced_percentage": round(unsourced_percentage, 1),
                    "issues": issues,
                    "can_approve": can_approve,
                    "approval_status": "APPROVED" if can_approve else "REJECTED_TOO_MANY_HALLUCINATIONS"
                },
                metadata={
                    "verification_method": "source_matching",
                    "hallucination_detection": "enabled",
                    "max_unsourced_allowed_percentage": self.MAX_UNSOURCED_PERCENTAGE,
                    "claim_count": total_claims,
                    "unsourced_claim_count": unsourced_count,
                    "verification_passed": can_approve
                },
                timestamp=datetime.now().isoformat(),
                error=""
            )

        except ValueError as e:
            logger.error(f"ValueError in DocumentVerifier: {str(e)}")
            return AgentResult(
                success=False,
                output={"all_verified": False, "issues": [], "can_approve": False},
                metadata={"error_type": "validation"},
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )

        except Exception as e:
            logger.error(f"=== DocumentVerifier.generate() FAILED ===")
            logger.error(f"Exception: {str(e)}", exc_info=True)
            return AgentResult(
                success=False,
                output={"all_verified": False, "issues": [], "can_approve": False},
                metadata={"error_type": "verification_error"},
                timestamp=datetime.now().isoformat(),
                error=f"Verification failed: {str(e)}"
            )

    def _extract_claims(self, response: str) -> List[str]:
        """Extract substantive claims from response"""
        # Split by sentence (period, question mark, exclamation)
        sentences = re.split(r'[.!?]+', response)

        # Filter substantive claims (length > 10 chars, not headers)
        claims = []
        for sentence in sentences:
            cleaned = sentence.strip()
            # Exclude short lines, headers, and formatting
            if (len(cleaned) > 10 and
                not cleaned.isupper() and
                not cleaned.startswith("#") and
                not cleaned.startswith("---") and
                ":" not in cleaned[:20]):  # Exclude section headers like "BACKGROUND:"
                claims.append(cleaned)

        return claims

    def _verify_claim_with_llama(self, claim: str, sources: Dict[str, str]) -> bool:
        """
        Verify claim semantically using Llama.

        Asks Llama to determine if the claim is supported by the provided source documents.
        Uses semantic understanding rather than simple keyword matching.

        Args:
            claim: The claim to verify
            sources: Dict of {filename: content} source documents

        Returns:
            True if Llama confirms claim is sourced, False otherwise
        """
        try:
            # Build source context
            sources_text = "\n---\n".join(
                f"[Source: {filename}]\n{content[:1000]}"  # First 1000 chars per source
                for filename, content in sources.items()
            )

            # Ask Llama to verify the claim
            prompt = f"""Verify this claim based on the provided source documents.

CLAIM TO VERIFY:
{claim}

SOURCE DOCUMENTS:
{sources_text}

Is this claim supported by the source documents?
Answer with ONLY "YES" or "NO" on the first line, then briefly explain why.

Example:
YES - This is stated in Source 2, line 5
OR
NO - No source document mentions this"""

            logger.debug(f"Verifying claim: '{claim[:80]}...'")
            response = self.agent.generate_response(prompt)

            if not response:
                logger.warning(f"Llama returned empty response for claim: {claim[:80]}")
                return False

            # Parse response: should start with YES or NO
            response_upper = response.strip().upper()
            is_verified = response_upper.startswith("YES")

            logger.debug(f"Llama verification: {is_verified} - Response: {response[:100]}")
            return is_verified

        except Exception as e:
            logger.error(f"Error verifying claim with Llama: {e}")
            logger.error(f"Claim was: {claim[:100]}")
            # On error, assume unverified (conservative approach)
            return False


# ============================================================================
# UNIT TESTS
# ============================================================================

