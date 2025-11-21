# COMPREHENSIVE PLAN: Tax & Legal Jupiter Restructure + MemAgent Integration

## OVERVIEW

Transform Jupiter from consultant-centric planning into tax/legal document-centric workflow, powered by MemAgent semantic search (not vectors/RAG). Focus: past response discovery → source document identification → cited response synthesis.

**Architectural Foundation**:
- **MemAgent**: All memory/search tasks (past responses, source documents)
- **Llama**: Reasoning, synthesis, PDDL-INSTRUCT verification
- **No FAISS/vectors**: Uses MemAgent's bounded, learnable semantic search

---

## PART 1: TAX DATABASE CONVERSION & ORGANIZATION

### 1.1 Convert 3,015 Tax Files to Markdown (Collaborative: You + Claude Code)

**Timeline**: ~1 week (collaborative parallel processing)

**Process**:
```
Collaborative approach - You mount/provide access to Tax database files:
1. Claude Code reads each PDF/DOC/DOCX/Excel file
2. Extract text and preserve original filename (better for MemAgent search)
3. Organize in optimal folder structure:
   local-memory/tax-database/
   ├── CIT/
   │   ├── Interest_Expenses_EBITDA_Cap/
   │   │   ├── Circular_111_2013_TT-BTC.md
   │   │   ├── Law_26_2012_QH13_CIT.md
   │   │   └── [etc.]
   │   ├── Provision_Expenses/
   │   └── [other CIT subtopics]
   ├── VAT/
   ├── PIT/
   └── [etc. - all 23 main categories]

4. Add metadata footer to each .md file:
   ---
   # Document Metadata
   - **Source Type**: Circular | Law | Ruling | Advice | Guidance
   - **Category**: CIT | VAT | PIT | etc.
   - **Regulatory Body**: Ministry of Finance | Tax Authority | Court
   - **Date Issued**: [YYYY-MM-DD]
   - **Keywords**: [comma-separated tags for search]
   - **Scope**: [High-level description]
   ---
```

**Rationale**:
- MemAgent searches better with organized structure + clear metadata
- Filename preservation helps MemAgent identify documents by reference
- Metadata tags improve semantic matching without vectors

### 1.2 Create Document Index

**Location**: `local-memory/tax-database-index.json`

**Structure**:
```json
{
  "documents": [
    {
      "filename": "Circular_111_2013_TT-BTC.md",
      "path": "CIT/Interest_Expenses_EBITDA_Cap/",
      "document_type": "Circular",
      "category": "CIT",
      "issued_by": "Ministry of Finance",
      "date_issued": "2013-12-20",
      "keywords": ["interest expense", "EBITDA", "cap", "deduction"],
      "size_bytes": 45230,
      "extracted_timestamp": "2025-11-21"
    },
    // ... 3,014 more entries
  ],
  "total_files": 3015,
  "total_size_gb": 5.5,
  "categories": {
    "CIT": 512,
    "VAT": 287,
    // ... all categories with counts
  },
  "last_updated": "2025-11-21"
}
```

---

## PART 2: JUPITER WORKFLOW RESTRUCTURE

### 2.1 New Tax-Specific Workflow (5 Steps)

**Step 1: Request Input & Categorization**
```
User: "Client is a pharmaceutical distributor in Vietnam with a Singapore parent company.
      They have a distribution agreement and want to understand the tax implications,
      especially around transfer pricing and contract structure."

System:
├─ Suggest topic categories: [CIT] [Transfer Pricing] [VAT]
├─ User confirms/adjusts
└─ Categories locked in for search
```

**Step 2: Past Response Search (MemAgent)**
```
MemAgent searches: local-memory/past-responses/

Query: "Pharmaceutical distribution agreement + transfer pricing + contract structure"

Returns (ranked by semantic similarity):
├─ Response_20251115_001: "Pharmaceutical-Memo on contract review"
│  └─ Similarity: 95% | Files used: 3 | Status: Approved
├─ Response_20251110_045: "Distribution agreement analysis for medical devices"
│  └─ Similarity: 87% | Files used: 4 | Status: Approved
└─ Response_20251105_023: "Transfer pricing fundamentals for multinational service providers"
   └─ Similarity: 72% | Files used: 5 | Status: Approved
```

**Step 3: User Review & Acceptance**

User sees top 3-5 past responses with:
- Original client question/situation
- Advice given
- Files that were used for that response
- User: "Accept Response #1" OR "Reject, search differently" OR "Accept + modify"

**If Accepted**: System shows "Files from accepted response:"
```
Files used in Pharmaceutical-Memo response:
├─ Circular_103_2014_TT-BTC_Contract_Review.md
├─ Law_05_2014_QH13_Transfer_Pricing.md
└─ Past_Advice_Pharmaceutical_2022.md
```

**Step 4: Source Document Search (MemAgent)**

If user accepts past response:
```
MemAgent searches: local-memory/tax-database/

Query: "More docs on pharmaceutical + distribution + transfer pricing + contract"
(Constrained to categories: [CIT], [Transfer_Pricing], [VAT])

Returns (ranked by relevance to this request):
├─ Circular_111_2013_TT-BTC_CIT_Guidance.md (95% match)
├─ Law_26_2012_QH13_CIT.md (92% match)
├─ OECD_Transfer_Pricing_Guidelines_Vietnam_Version.md (85% match)
├─ VAT_Treatment_Import_Distribution.md (78% match)
└─ [others...]
```

**Step 5: File Selection, Response Synthesis, Approval**

User sees recommended documents from past response + additional search results.

User can:
- ✅ Accept all suggested files
- ❌ Reject some files
- ➕ Add additional files from search results
- 🔍 Run new keyword search within category
- 🎯 Mark files as "Critical", "Supporting", "Reference"

**Once files selected**:

**Llama synthesizes response in KPMG format:**
```
PHARMACEUTICAL DISTRIBUTION AGREEMENT ANALYSIS

BACKGROUND
[From client request + files]

UNDERSTANDING OF KEY TERMS
├─ Distribution scope (from Circular_103_2014_TT-BTC.md, Section 2.3)
├─ Pricing terms (from Law_26_2012_QH13_CIT.md, Article 5.2)
├─ Marketing obligations (from VAT_Treatment_Import_Distribution.md, pp. 12-15)
└─ Termination & renewal (from Past_Advice_Pharmaceutical_2022.md, Section "Termination Risks")

DETAILED TAX ANALYSIS
├─ 1. CIT IMPLICATIONS
│  - Base Erosion Risk: Based on interest expense cap (Circular_111_2013_TT-BTC_CIT_Guidance.md, Section 3.1)
│    Current analysis: [reasoning from files]
│    Recommendation: [citation: Circular_111_2013, clause 2.5]
│
├─ 2. TRANSFER PRICING CONSIDERATIONS
│  - Comparability: [analysis from OECD_Transfer_Pricing_Guidelines_Vietnam_Version.md]
│    Recommendation: [specific guidance]
│
├─ 3. VAT TREATMENT
│  - Import VAT: [from VAT_Treatment_Import_Distribution.md, pp. 12-15]
│  - Allocation: [from Law_26_2012_QH13_CIT.md, Article 5.2]
│  - Recommendation: [citation and practical guidance]
│
└─ 4. CONTRACT STRUCTURE RISKS
   [Similar breakdown with citations]

KPMG RECOMMENDATION
[Synthesis of above, telling client what to do]

RISK ASSESSMENT
- Compliance Risk: High (citation: Circular_103_2014_TT-BTC, Section 7)
- Operational Risk: Medium
- Financial Impact: [estimated exposure based on contract terms]

SOURCE DOCUMENTATION
├─ Circular_103_2014_TT-BTC_Contract_Review.md (pp. 5-8, 12-14)
├─ Law_26_2012_QH13_CIT.md (Article 5.2, Section 3.1)
├─ VAT_Treatment_Import_Distribution.md (pp. 12-15)
├─ Past_Advice_Pharmaceutical_2022.md (Section "Termination Risks")
└─ [others with exact citations]
```

**Approval Gate**:
- Partner reviews (visual inspection, cites match sources, recommendations sound)
- ✅ Approve → Save as new past response + update learning patterns
- ❌ Reject → Go back to file selection OR restart search

---

## PART 3: AGENT ARCHITECTURE FOR TAX WORKFLOW

### 3.1 Agent Changes (Remove/Add/Refactor)

**Remove**:
- ❌ PlannerAgent (not needed for tax)
- ❌ ExecutorAgent (web search not central)
- ❌ GeneratorAgent (response generation now Llama-based, not agent-based)

**Refactor**:
- **ProposalAgent** → **RequestCategorizer**
  - Input: Client request text
  - Output: Suggested topic categories (dropdown list)
  - Uses: Llama to classify request into tax topics

- **VerifierAgent** → **DocumentVerifier**
  - Input: Synthesized response + source files
  - Output: Verification report (does response match sources? Any hallucinations?)
  - Uses: PDDL-INSTRUCT to verify preconditions/effects

**New**:
- **TaxResponseSearcher** (uses MemAgent)
  - Searches past responses for similar client situations
  - Returns top-5 past responses with metadata (files used, approval status)

- **FileRecommender** (uses MemAgent)
  - Takes accepted past response
  - Returns source files that were used in that response
  - Also performs additional semantic search for supplementary docs

- **TaxResponseCompiler** (uses Llama)
  - Takes selected files
  - Generates KPMG memo with full citations
  - Ensures every claim points to a source document

- **CitationTracker** (new utility)
  - Maps response text back to source documents
  - Validates: "This statement comes from [Filename, page X]"
  - Ensures citation consistency

### 3.2 New Orchestrator Logic (SimpleOrchestrator modifications)

```python
class TaxOrchestrator:
    def run(self, client_request: str):
        # Step 1: Categorize
        categories = RequestCategorizer(client_request)
        user_confirm_categories()  # User approves or adjusts

        # Step 2: Search past responses (MemAgent)
        past_responses = TaxResponseSearcher.search(
            query=client_request,
            constrained_to=categories
        )
        user_selects_response(past_responses)  # User picks one or none

        # Step 3: Get source files from selected response
        if user_accepted_response:
            suggested_files = FileRecommender.get_files_from_response(
                response=selected_response
            )
            additional_files = FileRecommender.search_additional(
                query=client_request,
                constrained_to=categories
            )
        else:
            # Direct search for files
            suggested_files = FileRecommender.search_additional(
                query=client_request,
                constrained_to=categories
            )

        # Step 4: User selects/refines files
        final_files = user_refines_file_selection(suggested_files)

        # Step 5: Synthesize response (Llama)
        response = TaxResponseCompiler.compile(
            files=final_files,
            request=client_request,
            categories=categories,
            past_response=selected_response if accepted else None
        )

        # Step 6: Verify citations (PDDL-INSTRUCT)
        verification = DocumentVerifier.verify(
            response=response,
            files=final_files
        )

        # Step 7: Approval gate
        approved = ApprovalGate.wait_for_approval(
            response=response,
            verification=verification
        )

        if approved:
            # Save as new past response
            save_as_past_response(response, final_files, client_request)
            # Update learning patterns
            update_learning_patterns(final_files, categories)
            return response
        else:
            return "Rejected - restart"
```

---

## PART 4: MEMAGENT INTEGRATION STRATEGY

### 4.1 How MemAgent Handles Tax Database Search

**Current MemAgent in Jupiter**:
- Bounded memory (12 segments, ~24K tokens)
- Semantic search within segments
- RL-trained compression
- Constrained retrieval (user selects what to search)

**For Tax System**:

**Segment Allocation** (initial):
```
MemAgent Memory (12 segments total):
├─ Segment 0-2: Past responses corpus (3-4K most relevant responses)
│  └─ Organized by: CIT | VAT | PIT | Transfer Pricing | Other
│
├─ Segment 3-6: High-frequency tax documents (most-searched circulars/laws)
│  └─ Circulars 103, 111, 123 / Laws 05, 26, 47 etc.
│
├─ Segment 7-9: Category-specific regulations (loaded based on user's category selection)
│  └─ CIT specialists → CIT segment emphasis
│  └─ TP specialists → TP segment emphasis
│
├─ Segment 10-11: Current request context + selected files
│  └─ Session-specific: What user searched for, what files selected
│
└─ Overflow: Compression strategy
   └─ Low-importance segments compressed when memory full
   └─ RL learns: "Response approved? Keep those segments high-priority"
```

**Search Process** (both steps):

**Step 2: Past Response Search**
```
MemAgent.search(
  query="Pharmaceutical distribution agreement transfer pricing",
  memory_segments=[0, 1, 2],  # Past responses only
  search_type="semantic",      # MemAgent semantic, not keyword
  return_top_k=5,
  constraints={"categories": ["CIT", "Transfer_Pricing"]},
)

Output: [Past_Response_1, Past_Response_2, ...]
├─ Each includes: original_request, files_used, approval_status
└─ Ranked by semantic similarity to new request
```

**Step 4: Source Document Search**
```
MemAgent.search(
  query="More regulations on pharmaceutical distribution transfer pricing",
  memory_segments=[3, 4, 5, 6, 7, 8, 9],  # Tax documents
  search_type="semantic",
  return_top_k=10,
  constraints={
    "categories": ["CIT", "Transfer_Pricing", "VAT"],
    "exclude": [files_already_used]  # Don't repeat suggestions
  },
)

Output: [File_1, File_2, File_3, ...]
├─ Each includes: filename, path, content, metadata
└─ Ranked by relevance to request + selected past response
```

### 4.2 MemAgent Learning Integration

**Learning Signal** (from approval):
```
After user approves response:

Learning input:
├─ Request: "Pharmaceutical distribution..."
├─ Files_selected: [File_A, File_B, File_C]
├─ Categories_used: [CIT, Transfer_Pricing, VAT]
├─ Approval_status: "Approved"
└─ Partner_feedback: [if user provided notes]

MemAgent learns:
1. "These files are important for pharmaceutical + transfer pricing queries"
   → Increase segment importance score for [File_A, File_B, File_C]

2. "These categories co-occur"
   → Pattern: Pharmaceutical cases need CIT + TP + VAT

3. "This file combination leads to approved outcomes"
   → Next time similar request: prioritize this combo

4. Compression decision:
   → If memory full: Don't compress files used in approved responses
   → Compress: Files not yet used in approved cases
```

---

## PART 5: CITATION ARCHITECTURE (CRITICAL)

### 5.1 Citation Requirement

**MUST HAVE**: Every statement in response cites source

**Format Examples**:
- "According to Circular 111/2013/TT-BTC (Section 2.3)..."
- "Per Law 26/2012/QH13 Article 5.2..."
- "As noted in KPMG's Past Advice [2022]..."
- "Based on OECD Transfer Pricing Guidelines..."

### 5.2 Citation Tracking System

**CitationTracker Component**:
```python
class CitationTracker:
    def track_response_generation(self,
        response_text: str,
        source_files: List[str],
        llama_generation_log: str
    ):
        """Map every claim in response back to source"""

        for section in response_text.sections:
            for claim in section.extract_claims():
                # Verify: This claim appears in at least one source file
                source_found = self.find_source_for_claim(
                    claim,
                    source_files
                )

                if not source_found:
                    flag_hallucination(claim)

                # Extract exact citation
                citation = self.extract_citation(source_found, claim)
                response.add_citation(claim, citation)

        return response_with_citations
```

**Output Example**:
```
Claim: "The interest expense deduction is capped at EBITDA"
Source: Circular_111_2013_TT-BTC.md, Section 3.1, Page 5
Citation: "Circular 111/2013/TT-BTC, Section 3.1"
Verification: ✓ Confirmed in source

Claim: "Marketing expenses must be substantiated with contracts"
Source: Law_26_2012_QH13_CIT.md, Article 5.2
Citation: "Law 26/2012/QH13, Article 5.2"
Verification: ✓ Confirmed in source
```

---

## PART 6: MULTI-USER ARCHITECTURE (VASTAI)

### 6.1 Multi-User Data Organization

```
VastAI Shared Storage:

local-memory/
├─ tax-database/                    [SHARED - all users]
│  ├─ CIT/
│  ├─ VAT/
│  ├─ [23 main categories]
│  └─ tax-database-index.json
│
├─ past-responses/                  [SHARED - all users see history]
│  ├─ response_20251121_001_[pharma].md
│  ├─ response_20251120_002_[banking].md
│  └─ [growing library of approved responses]
│
├─ users/                           [SEPARATE per user]
│  ├─ [user1]/
│  │  ├─ current-draft.md           [Private work]
│  │  ├─ search-history.json
│  │  └─ preferences.json
│  ├─ [user2]/
│  └─ [user3]/
│
├─ audit-logs/                      [SHARED - centralized tracking]
│  ├─ 2025-11-21_searches.log
│  ├─ 2025-11-21_approvals.log
│  └─ 2025-11-21_responses.log
│
└─ learning-patterns.json           [SHARED - system learns from all approvals]
   ├─ Pattern: "Pharma + Distribution" → [Files A, B, C]
   ├─ Pattern: "Transfer Pricing + Multinational" → [Files D, E]
   └─ [grows over time]
```

### 6.2 User Roles & Access

**Roles** (confirmed with KPMG):
- [ ] **Partner**: Create requests, approve responses, see all history
- [ ] **Senior Staff**: Create requests, see past responses, suggest files, can't approve
- [ ] **Junior Staff**: View only, learn from system, no creation/approval

(Exact roles TBD with KPMG team)

### 6.3 VastAI Instance Setup

```
VastAI Instance:
├─ Streamlit app.py (multi-user session management)
├─ MemAgent instance (memory search engine)
├─ Llama model (response synthesis)
├─ FastAPI backend (if needed for heavy lifting)
└─ SQLite user/audit database
```

---

## PART 7: IMPLEMENTATION ROADMAP

### Phase 1: Database Conversion (Week 1) - COLLABORATIVE: You + Claude Code
**Duration**: ~1 week
**Approach**: Collaborative parallel processing

**Process**:
- [ ] You mount/provide access to Tax and Legal database (5.5GB, 3,015 files)
- [ ] Claude Code reads each file and converts to markdown:
  - [ ] Extract text from PDF/DOC/DOCX/Excel files
  - [ ] Preserve original filenames (better for MemAgent search)
  - [ ] Organize into folder structure (mirroring original: CIT/, VAT/, PIT/, etc.)
  - [ ] Add metadata footer to each .md file (source type, date, regulatory body, keywords)
- [ ] You validate sample conversions for quality
- [ ] Create tax-database-index.json (metadata for all 3,015 files)
- [ ] Final validation: Spot-check 50 files, ensure metadata accuracy

**Why Collaborative**:
- Claude Code can read binary files (PDF/DOC) and convert efficiently
- Working in parallel reduces timeline from 2-3 weeks to ~1 week
- You can validate/adjust structure as we go
- Ensures optimal MemAgent-friendly organization

**Deliverable**: 3,015 markdown files in local-memory/tax-database/, fully indexed, ready for MemAgent search

---

### Phase 2: Workflow Refactor (Weeks 3-4)
**Duration**: 2-3 weeks
**Builds on**: Phase 1 complete

**Update Agents**:
- [ ] Refactor ProposalAgent → RequestCategorizer
- [ ] Refactor VerifierAgent → DocumentVerifier
- [ ] Create TaxResponseSearcher (MemAgent-based)
- [ ] Create FileRecommender (MemAgent-based)
- [ ] Create TaxResponseCompiler (Llama-based)
- [ ] Create CitationTracker (citation validation)

**Update Orchestrator**:
- [ ] Rewrite SimpleOrchestrator for tax workflow (5-step process above)
- [ ] Integrate approval gates at Step 6
- [ ] Implement learning pattern update on approval

**Update Streamlit Frontend**:
- [ ] New UI flow: Request → Categorize → Past responses → Files → Synthesize → Approve
- [ ] Past response display (shows files used, approval status)
- [ ] File selection interface (accept/reject/search/refine)
- [ ] Citation preview (shows where each claim comes from)

**Deliverable**: Local Jupiter system runs new tax workflow

---

### Phase 3: MemAgent Integration & Testing (Weeks 5-6)
**Duration**: 2-3 weeks
**Builds on**: Phases 1-2 complete

- [ ] Test MemAgent semantic search on tax database
- [ ] Validate: Can MemAgent find similar past responses? (yes/no)
- [ ] Validate: Can MemAgent find relevant source documents? (yes/no)
- [ ] Test citation accuracy (does response cite correct sources?)
- [ ] Test with 10-15 real KPMG questions (quality validation)
- [ ] Measure performance: time per request, accuracy, citation coverage
- [ ] Get KPMG feedback on response quality + format
- [ ] Fix issues identified

**Deliverable**: Validated, working system on local machine

---

### Phase 4: Multi-User & VastAI Deployment (Weeks 7-8)
**Duration**: 1-2 weeks
**Builds on**: Phases 1-3 complete

- [ ] Set up VastAI instance with appropriate specs
- [ ] Mount shared storage (tax database, past responses)
- [ ] Implement multi-user session management
- [ ] Implement role-based access control (Partner/Senior/Junior)
- [ ] Set up audit logging (all searches, approvals, responses)
- [ ] Deploy Streamlit + backend to VastAI
- [ ] Test concurrent multi-user usage
- [ ] Validate file access/isolation (users see shared data, private drafts isolated)

**Deliverable**: Multi-user system running on vastAI

---

### Phase 5: Team Training & Launch (OPTIONAL - 3-5 days if desired)
**Duration**: 3-5 days (completely optional based on your preference)
**Builds on**: Phase 4 complete

**This phase is optional.** After Phase 4 deployment, you can choose to:
- [ ] Create user guide + video walkthrough (optional)
- [ ] Train KPMG team members (optional)
- [ ] Formalize documentation (optional)
- [ ] Go live with structured training (optional)

Or skip directly to organic rollout with minimal formal documentation.

**Deliverable** (if executed): KPMG team fully trained with documentation

---

## PART 8: MINIMUM VIABLE PRODUCT (MVP)

**For launch, system must have**:

### Core Workflow ✅
- [ ] Client request input interface
- [ ] Automatic topic categorization (dropdown, multi-select)
- [ ] MemAgent search past responses (top 5 results)
- [ ] User accept/reject past response selection
- [ ] File recommendation + manual search
- [ ] Llama-based response synthesis
- [ ] Full citation tracking (every claim cited)
- [ ] Approval gate (partner review before delivery)
- [ ] Save approved response as past response
- [ ] Multi-user access on VastAI

### Search Quality ✅
- [ ] MemAgent returns relevant past responses (>80% of top 3 are relevant)
- [ ] MemAgent returns correct source files from selected past response
- [ ] Supplementary document search finds additional relevant docs
- [ ] Search completes in <10 seconds per query

### Response Quality ✅
- [ ] KPMG memo format (Background, Understanding, Analysis, Recommendations, Risks, Sources)
- [ ] Every claim traced to source document
- [ ] No hallucinations (verified via CitationTracker)
- [ ] Professional tone and structure
- [ ] 2-5 page responses (appropriate length)

### Usability ✅
- [ ] Clear flow (5-step workflow is obvious)
- [ ] Easy file selection (accept/reject/search interface is intuitive)
- [ ] Citation preview (user can see where claims come from)
- [ ] Functional (not beautiful, but works)

### What's NOT in MVP
- ❌ UI polish/design refinement (add Phase 2)
- ❌ Keyboard shortcuts / advanced features
- ❌ Mobile responsive
- ❌ Real-time regulatory updates
- ❌ Predictive pattern co-evolution
- ❌ Feature 1: Natural conversation chat (defer to Phase 2)

---

## PART 9: RISK MITIGATION

| Risk | Severity | Mitigation |
|------|----------|-----------|
| MemAgent doesn't find past responses effectively | High | Early testing in Phase 3 with real KPMG questions; pivot search strategy if needed |
| Citation accuracy drops (hallucinations appear) | Critical | CitationTracker validation; partner review gate catches issues; iterate with Llama |
| File extraction quality is poor for some PDFs | Medium | Sample extraction early (Week 1); fall back to manual copy-paste for problematic docs |
| VastAI instance performance is slow | Medium | Generous instance sizing; performance monitoring; optimize MemAgent queries if needed |
| KPMG team finds response quality inadequate | High | Iterate quickly in Phase 3; get feedback early; adjust templates/reasoning if needed |
| Multi-user data isolation fails | High | Thorough testing in Phase 4; implement audit trail to catch data leaks |

---

## PART 10: SUCCESS METRICS

**Launch Success**:
- System finds relevant past response for 12/15 test cases (80%+ success)
- Response generation includes proper citations for 100% of claims
- KPMG team can operate system without engineer support
- At least 3 team members trained and actively using
- No critical bugs reported in first week
- Time per response: Target 15-30 minutes (vs. current 90-150 min)

**Long-term Success**:
- Time reduction: Actual 90-150 min → 20-40 min (50-70% improvement, realistic vs. 87-90% promised)
- Team adoption: 80%+ of requests use Jupiter
- Response quality: Consistent across team members (learning patterns working)
- Past responses reused: 30-40% of new requests leveraging past work
- System learning: Quality of recommendations improves over time (MemAgent compression prioritizes useful patterns)

---

## SUMMARY

This plan transforms Jupiter into a **tax/legal resource-discovery system** using MemAgent's bounded, learnable semantic search (NOT vectors/RAG), integrated with Llama for reasoning and synthesis.

**Key Architecture Changes**:
1. **MemAgent handles**: Past response search + source document search (both semantic, bounded memory)
2. **Llama handles**: Request classification, response synthesis, logical verification
3. **No vectors**: Uses MemAgent's native memory-based semantic search with RL compression
4. **Two-phase search**: Find similar past responses → Extract files used → Offer additional docs
5. **Citation-critical**: Every claim must point to source document (KPMG compliance requirement)
6. **Multi-user**: VastAI deployment with shared tax DB + shared past responses + private drafts

**Realistic Timeline**: 6-8 weeks for core system (Phases 1-4) + optional Phase 5
- Phase 1: Database conversion (1 week) - Collaborative you + Claude Code
- Phase 2: Workflow refactor (2-3 weeks)
- Phase 3: Testing + validation (2-3 weeks)
- Phase 4: Multi-user deployment (1-2 weeks)
- Phase 5: Training & Launch (OPTIONAL - 3-5 days if you want it)

**MVP Scope**: Core workflow, search quality, response quality, basic usability (NOT UI polish)

**Team Size**: You (solo) + Claude Code for Phase 1 extraction; You solo for Phases 2-5
