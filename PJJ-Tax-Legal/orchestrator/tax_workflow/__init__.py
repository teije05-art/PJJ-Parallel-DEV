"""
Tax/Legal Workflow Module - Project Jupiter Phase 2

Specialized agents for tax advice workflow using Vanilla MemAgent Pattern:
- RequestCategorizer: Classify tax requests into domains using Llama
- TaxResponseSearcher: Search past approved responses via MemAgent
- FileRecommender: Search tax database documents via MemAgent
- TaxResponseCompiler: Synthesize KPMG-format responses using Llama
- CitationTracker: Embed and track citations
(DocumentVerifier removed - human does manual verification)

DUAL-LLM ARCHITECTURE:
- MemAgent (via Agent.chat()): Navigates filesystem and reads memory
  - Performs intelligent LLM-driven file discovery
  - Accesses past_responses/ and tax_database/ directories
  - Returns natural language descriptions of findings
- Llama (via Fireworks API): Performs reasoning and synthesis
  - Takes MemAgent findings and synthesizes responses
  - Applies domain expertise for tax/legal advice
  - Enforces constraint boundaries

CONSTRAINT ENFORCEMENT:
- User-confirmed categories (RequestCategorizer validates user selection)
- Natural language queries (no JSON forcing)
- Single save point (only TaxOrchestrator saves approved responses)
- Source-only constraints (no hallucinations, all findings from memory)
- Audit trails (complete logging of each agent's decision)

MEMORY NAVIGATION:
- MemAgent uses natural language queries to navigate filesystem
- No semantic similarity scoring (vanilla MemAgent pattern)
- Reads files directly from filesystem for intelligent relevance assessment
- Returns natural descriptions that are parsed to extract results
"""

__version__ = "1.0.0"

from .tax_planner_agent import RequestCategorizer
from .tax_searcher_agent import TaxResponseSearcher
from .tax_recommender_agent import FileRecommender
from .tax_compiler_agent import TaxResponseCompiler
# DocumentVerifier removed - human does manual verification
from .tax_tracker_agent import CitationTracker
from .tax_orchestrator import TaxOrchestrator

__all__ = [
    "RequestCategorizer",
    "TaxResponseSearcher",
    "FileRecommender",
    "TaxResponseCompiler",
    # DocumentVerifier removed
    "CitationTracker",
    "TaxOrchestrator"
]
