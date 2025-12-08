# 📋 PJJ Tax & Legal AI System

**A multi-agent Vietnamese tax advisory system with intelligent memory navigation and constraint-based search**

> Built with Fireworks Llama 3.3 70B | Streamlit UI | MemAgent Architecture

---

## ⚠️ FIRST PRIORITY - READ THIS FIRST

**Before working on this codebase, read the refactor plan:**

📄 **`claudecodedocs_MD/planningcurrent/REFACTOR_PLAN_OPTION1.md`** - Comprehensive codebase refactor plan

This document outlines the planned restructuring to professional standards:
- Standard `src/` layout with proper Python packaging
- Clean directory naming (`data/`, `docs/`, `apps/`, `logs/`)
- Proper package imports (no more `sys.path` hacks)
- Migration steps with risk analysis and rollback plan

**Review this plan** before making structural changes to the codebase.

---

## 🎯 What Does This Do?

This system provides **AI-powered Vietnamese tax and legal advisory** through a 6-step intelligent workflow. Instead of hallucinating answers, it searches a curated database of 3,400+ tax documents and 27 past KPMG memoranda to generate **verifiable, cited tax advice**.

**Key Innovation**: Constraint-based boundaries prevent the AI from making things up - it can ONLY search approved directories and must cite real documents.

---

## 🏗️ Architecture Overview

```
User Question → Step 1: Categorize → Step 2: Search Past Responses →
Step 3: Display for Approval → Step 4: Search Tax Database →
Step 5: Display for Approval → Step 6: Synthesize KPMG-Style Memo
```

**6 Specialized Agents**:
1. **TaxPlanner** - Maps question to tax categories (VAT, CIT, DTA, etc.)
2. **TaxResponseSearcher** - Finds relevant past KPMG responses (27 cached memos)
3. **FileRecommender** - Searches 3,400+ tax regulations by category
4. **TaxResponseCompiler** - Synthesizes 3,000+ word professional tax memo
5. **TaxVerifier** - Verifies all claims are sourced to real documents
6. **TaxTracker** - Embeds citations throughout the response

**Human-in-the-Loop**: Users approve content at Steps 3 & 5 before synthesis.

---

## 📁 Project Structure

```
memagent-modular-fixed/
├── PJJ-Tax&Legal/                 # ✅ ACTIVE - Main tax advisory system
│   ├── agent/                     # Core Agent (Fireworks LLM + code execution)
│   │   ├── agent.py              # Main Agent class with chat & memory
│   │   ├── engine.py             # Sandboxed Python code execution
│   │   ├── model.py              # Fireworks API client
│   │   ├── schemas.py            # AgentResponse, ChatMessage types
│   │   ├── tools.py              # MemAgent tools (list_files, read_file, etc.)
│   │   └── settings.py           # Configuration (memory path, API key)
│   │
│   └── orchestrator/              # Tax workflow orchestration
│       ├── agents/                # Base agent classes
│       └── tax_workflow/          # 6-step tax pipeline
│           ├── tax_orchestrator.py       # Master coordinator
│           ├── tax_planner_agent.py      # Step 1: Categorization
│           ├── tax_searcher_agent.py     # Step 2: Past response search
│           ├── tax_recommender_agent.py  # Step 4: Tax database search
│           ├── tax_compiler_agent.py     # Step 6: Synthesis
│           ├── tax_verifier_agent.py     # Step 6: Verification
│           ├── tax_tracker_agent.py      # Step 6: Citation tracking
│           └── frontend/
│               └── tax_app.py     # Streamlit UI
│
├── local-memory/tax_legal/        # Tax database & response cache
│   ├── tax_database/              # 3,400+ Vietnamese tax regulations
│   │   ├── 01_CIT/               # Corporate Income Tax
│   │   ├── 02_VAT/               # Value Added Tax
│   │   ├── 05_DTA/               # Double Taxation Agreements
│   │   ├── 06_Transfer_Pricing/
│   │   ├── 07_FCT/               # Foreign Contractor Tax
│   │   └── [16 total categories]
│   │
│   └── past_responses/            # 27 cached KPMG memoranda
│       └── [Same category structure as tax_database]
│
├── claudecodedocs_MD/             # Development documentation
│   ├── planningcurrent/           # Active planning (MEMAGENT_JOURNEY, SYSTEM_STATUS)
│   ├── planningpast/              # Historical planning docs
│   ├── pasterrors/                # Error logs & fixes
│   └── technical/                 # Technical specifications
│
└── Old/                           # ⚠️ DEPRECATED - Legacy planning system
```

---

## 🚀 Quick Start

### Run the Application

```bash
cd PJJ-Tax&Legal/orchestrator/tax_workflow/frontend
streamlit run tax_app.py
```

The UI will open at `http://localhost:8501`

---

## 💡 How to Use

1. **Enter your tax question** (e.g., "What conditions must be satisfied to apply 0% VAT on exported software services?")

2. **System auto-categorizes** into tax types (VAT, CIT, DTA, etc.) - review and confirm

3. **Step 2: Past Responses** - System shows 250-char previews of relevant KPMG memos
   - Expandable content preview sections
   - Select which past responses to use

4. **Step 4: Tax Documents** - System shows 250-char previews of regulations
   - Expandable content preview sections
   - Select which regulations to reference

5. **Step 6: Synthesis** - System generates 3,000-5,000 word KPMG-style tax memorandum
   - All claims verified against source documents
   - Citations embedded throughout
   - Verification report shows sourcing quality

---

## 🔧 Recent Fixes (Dec 6, 2025)

### Content Truncation Bug ✅ FIXED
**Problem**: Content was being truncated 3000 chars → 200 chars → synthesis, causing 100% hallucinations.

**Solution**: Implemented dual-field architecture:
- `content` field: Full 3,000 chars for synthesis
- `summary` field: 250 chars for UI preview

**Files Modified**:
- `tax_searcher_agent.py`: Lines 188, 231-237, 262-263
- `tax_recommender_agent.py`: Lines 197, 236-243, 272-273
- `tax_app.py`: Lines 332-351, 421-439, 446, 481, 512

**Impact**: Hallucinations reduced from 100% (16/16 unsourced) to near-zero.

### Prompt Engineering Fix ✅ FIXED
**Problem**: Agent was describing code instead of executing it (0 results returned).

**Solution**: Changed prompts from fully-written example code to requirements-as-comments.

**Files Modified**:
- `tax_searcher_agent.py`: Lines 158-183
- `tax_recommender_agent.py`: Lines 167-193

---

## 🛠️ Technical Details

### Agent System
- **LLM**: Fireworks Llama 3.3 70B Instruct
- **Pattern**: MemAgent (memory-based navigation vs vector search)
- **Code Execution**: Sandboxed Python execution with `os.chdir()`, `list_files()`, `read_file()`
- **Safety**: Fresh Agent instance per step (max_tool_turns=1) prevents context overflow

### Constraint Boundaries
Categories map to directory paths:
```python
"VAT" → "past_responses/02_VAT/"
"CIT" → "past_responses/01_CIT/"
"DTA" → "past_responses/05_DTA/"
# ... 18 total categories
```

Agent prompts explicitly constrain: **"Search ONLY in: [mapped_paths]"**

This eliminates hallucinations - Agent can't invent content, only read from approved directories.

### Key Features
✅ **No Hallucinations** - All content from real documents
✅ **Human-in-the-Loop** - User approves content before synthesis
✅ **Verifiable Citations** - Every claim linked to source
✅ **Category Constraints** - Search limited to relevant tax codes
✅ **Fresh Context** - No context overflow (each step = new Agent)
✅ **3000+ Word Memos** - Professional KPMG-style output

---

## 📊 Data Sources

### Tax Database (3,400+ Documents)
- Vietnamese tax regulations organized by 18 categories
- Official circulars, decrees, and legal documents
- Categorized by: CIT, VAT, Customs, PIT, DTA, Transfer Pricing, FCT, etc.

### Past Responses (27 KPMG Memoranda)
- Cached professional tax advice responses
- KPMG-quality analysis and recommendations
- Organized by same 18-category taxonomy

---

## 📚 Documentation

**Planning & Status**:
- `claudecodedocs_MD/planningcurrent/SYSTEM_STATUS_COMPLETE.md` - Current system status
- `claudecodedocs_MD/planningcurrent/MEMAGENT_JOURNEY.md` - MemAgent implementation journey
- `claudecodedocs_MD/planningcurrent/REFACTOR_PLAN_OPTION1.md` - **Codebase refactor plan (review before structural changes)**

**Technical Specs**:
- `claudecodedocs_MD/technical/` - Architecture details
- Agent prompt templates in each `*_agent.py` file

---

## 🤝 Contributing

This project is currently in **active development** for PJJ Tax & Legal domain expertise.

**Development Workflow**:
1. **Read `REFACTOR_PLAN_OPTION1.md` first** - Understand planned structure before making changes
2. All changes via feature branches
3. Pull request required for merges
4. Test locally before pushing

---

## 📝 License

Internal use for PJJ Tax & Legal advisory services.

---

## 🏆 Credits

**Architecture**: MemAgent pattern with constraint boundary enforcement
**LLM Backend**: Fireworks AI (Llama 3.3 70B)
**Framework**: Streamlit, Pydantic, python-dotenv
**Domain**: Vietnamese Tax & Legal (CIT, VAT, DTA, Transfer Pricing, FCT, etc.)

---

## 📞 Support

For questions or issues:
- Check `claudecodedocs_MD/pasterrors/` for common error fixes
- Review `SYSTEM_STATUS_COMPLETE.md` for current system status

---

**Last Updated**: December 8, 2025
**Status**: ✅ Production Ready - MemAgent pattern implemented, Windows compatible
