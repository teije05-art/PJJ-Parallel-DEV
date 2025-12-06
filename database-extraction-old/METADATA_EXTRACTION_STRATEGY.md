# Extraction Strategy for 1,066 Metadata-Only Files

**Generated**: December 2, 2025
**Total Files to Extract**: 1,066
**Estimated Time**: 4-6 hours

---

## Overview

This document outlines the strategy for extracting content from 1,066 metadata-only markdown files in the tax database. These files currently contain only YAML frontmatter with no body content.

---

## Priority-Based Extraction Plan

### Phase 3a: VAT Category (Priority 1)
**Files**: 459 metadata-only files
**Estimated Time**: 2 hours
**Current Status**: 0% extracted

| Metric | Value |
|--------|-------|
| Total in category | 474 |
| Already populated | 15 (3%) |
| Need extraction | 459 (97%) |
| Success factor | HIGH (most critical for tax system) |

**Extraction Approach**:
1. Source location: `/Users/teije/Library/Mobile Documents/.Trash/Tax_Legal/General Master Resource Folder/VAT/`
2. Expected file types: PDFs, DOCs, DOCXs
3. Smart routing:
   - PDF (text-based) → pdfplumber extraction
   - PDF (scanned) → Tesseract OCR (if pdfplumber fails)
   - DOC → LibreOffice conversion to PDF → Tesseract
   - DOCX → python-docx extraction, fallback to PDF conversion

### Phase 3b: Customs Category (Priority 2)
**Files**: 228 metadata-only files
**Estimated Time**: 1 hour
**Current Status**: 0% extracted

| Metric | Value |
|--------|-------|
| Total in category | 384 |
| Already populated | 156 (41%) |
| Need extraction | 228 (59%) |
| Success factor | MEDIUM-HIGH |

**Extraction Approach**: Same as VAT

### Phase 3c: DTA Category (Priority 3)
**Files**: 97 metadata-only files
**Estimated Time**: 30 minutes
**Current Status**: 0% extracted

| Metric | Value |
|--------|-------|
| Total in category | 141 |
| Already populated | 44 (31%) |
| Need extraction | 97 (69%) |
| Success factor | MEDIUM |

**Extraction Approach**: Same as VAT

### Phase 3d: Other Categories (Priority 4)
**Files**: 282 metadata-only files
**Estimated Time**: 1 hour
**Current Status**: 0% extracted

**Breakdown**:
| Category | Need Extraction |
|----------|-----------------|
| 04_PIT | 53 |
| 08_Tax_Administration | 54 |
| 10_Natural_Resources_SHUI | 64 |
| 05_DTA_subset | 97 |
| 13_Environmental_Protection_EPT | 10 |
| 14_Immigration | 10 |
| Others | ~82 |

---

## Extraction Logic & Routing

### Smart File Type Detection
Each script will:
1. Read markdown frontmatter to find source document path
2. Detect file type (PDF, DOC, DOCX, etc.)
3. Route to Tesseract-based extraction:
   - PDFs → Direct Tesseract OCR
   - DOCs → LibreOffice convert to PDF → Tesseract OCR
   - DOCXs → Convert to PDF → Tesseract OCR (python-docx as fallback only)
4. Extract content via Tesseract (eng+vie languages)
5. Update markdown body with extracted text
6. Log success/failure and source method

### Extraction Methods by File Type

**PRIMARY METHOD FOR ALL**: Tesseract OCR (proven 100% success rate + perfect Vietnamese)

#### PDF (All Types - Text-Based or Scanned)
```python
# Method: Tesseract OCR (PRIMARY)
- Uses Tesseract with eng+vie languages
- Works on both text-based and scanned PDFs
- 100% success rate (proven on 422 PDFs)
- Perfect Vietnamese diacritical preservation
- Takes ~24-30 seconds per PDF average
- Converts PDF pages to images (150 DPI) then OCR

# Why Tesseract instead of pdfplumber:
- pdfplumber caused encoding corruption (79 files with "TONG CUC THU6")
- Tesseract handles Vietnamese perfectly
- Tesseract is reliable and consistent
```

#### DOC (Old Word Format)
```python
# Method: LibreOffice Conversion + Tesseract OCR
- Step 1: LibreOffice: doc → pdf
- Step 2: Tesseract OCR on PDF (eng+vie)
- Always use Tesseract for consistent Vietnamese quality
- Takes ~30-40 seconds per file
```

#### DOCX (Modern Word Format)
```python
# Method 1: Tesseract OCR (PRIMARY)
- Convert DOCX → PDF
- Extract via Tesseract (eng+vie)
- Consistent with all other file types
- 100% reliable for Vietnamese

# Method 2: python-docx (FALLBACK ONLY)
- Only try if file appears to be pure text-based
- Limited Vietnamese support
- Fall back to Method 1 if fails
```

---

## Quality Assurance Checkpoints

### During Extraction
- ✅ Verify content extracted > 0 bytes
- ✅ Check for Vietnamese text (should contain diacritics)
- ✅ Ensure markdown format correct
- ✅ Log all successes/failures

### After Each Phase
- Count files with content > 500 bytes
- Spot-check 5 random files for quality
- Verify Vietnamese diacritics present
- Log completion percentage

### Final Verification
- Total files extracted: 1,066
- Final coverage: 97% (3,396 of 3,408)
- Metadata-only remaining: ~12 (unfound files)
- 100% of extracted files have Vietnamese perfect

---

## Resource Requirements

### Tools Already Installed
- ✅ Tesseract 5.5.1
- ✅ Poppler 25.11.0
- ✅ pdfplumber
- ✅ python-docx
- ✅ LibreOffice (for DOC conversion)

### Python Dependencies
```python
import pdfplumber
import pytesseract
from docx import Document
import subprocess  # for LibreOffice
import os
import json
import yaml
```

### Disk Space Required
- Current database: ~500 MB
- Estimated additional: ~200-300 MB
- Temp files: ~50 MB (cleaned up)

---

## Expected Success Metrics

### File Type Success Rates (Tesseract-Based)
| File Type | Expected Success | Notes |
|-----------|-----------------|-------|
| PDF (via Tesseract) | 100% | Proven on 422 scanned PDFs |
| DOC → PDF → Tesseract | 95%+ | Some DOC format variations may fail |
| DOCX → PDF → Tesseract | 98%+ | Tesseract highly reliable for modern formats |
| Fallback (python-docx for pure text DOCX) | 90%+ | Limited Vietnamese support |

### Overall Metrics (All Tesseract-Based)
- Total files extracted: 1,066
- Expected success: 98%+ (1,045+)
- Failed/unfound: ~2% (21 files max)
- Final coverage: 98-99% (3,375-3,390 files with content)
- **Key advantage**: 100% perfect Vietnamese encoding on all extracted files

---

## Timeline Breakdown (Tesseract-Based)

```
Tesseract processing time: ~24-30 seconds per file average
(Proven on 422 PDFs: 2.5 files/minute)

Phase 3a (VAT):      459 files × 27 sec = ~206 min (~3.5 hours)
Phase 3b (Customs):  228 files × 27 sec = ~102 min (~1.7 hours)
Phase 3c (DTA):      97 files × 27 sec = ~44 min (~45 min)
Phase 3d (Other):    282 files × 27 sec = ~127 min (~2 hours)

Total extraction: ~7.7 hours (serial processing)

Parallel processing options:
- Run VAT and Customs in parallel: ~3.5 hours
- Then DTA and Other: ~2 hours
- Total parallel: ~5.5 hours

Plus:
- Setup & script creation: 1 hour
- Verification & cleanup: 30 min
- MemAgent re-indexing: 30 min

GRAND TOTAL: ~7-8 hours (serial) or ~6.5-7 hours (parallel)
```

**Note**: Tesseract processing is reliable and consistent, with proven 100% success rate on Vietnamese text.

---

## Execution Order

### Pre-Extraction Preparation (30 min)
1. ✅ Verify Phase 2 complete (Tesseract 422 PDFs)
2. ✅ Clean 12 Word-corrupted files
3. ✅ Create `extract_metadata_strategy.py` - route files
4. Create progress tracking manifest

### Phase 3a: VAT Extraction (2 hours)
- Create `extract_vat_files.py`
- Execute extraction
- Log results

### Phase 3b: Customs Extraction (1 hour)
- Create `extract_customs_files.py`
- Execute extraction
- Log results

### Phase 3c: DTA Extraction (30 min)
- Create `extract_dta_files.py`
- Execute extraction
- Log results

### Phase 3d: Other Extraction (1 hour)
- Create `extract_other_files.py`
- Execute extraction
- Log results

### Post-Extraction Verification (30 min)
- Count total files with content
- Spot-check samples
- Generate statistics

### MemAgent Re-Indexing (30 min)
- Update tax_legal/tax_database indices
- Re-build search indices
- Test search functionality

---

## Risk Mitigation

### Risk: Source documents not found
- **Mitigation**: Check `/Users/teije/Library/Mobile Documents/.Trash/Tax_Legal/` paths
- **Fallback**: Mark as "source not found" in metadata

### Risk: LibreOffice conversion fails
- **Mitigation**: Tesseract fallback available
- **Fallback**: Mark file as "conversion failed" but attempt Tesseract

### Risk: Tesseract times out on large PDFs
- **Mitigation**: Set timeout to 60 seconds
- **Fallback**: Split into pages or mark as partial

### Risk: Corrupted extraction format
- **Mitigation**: Validate markdown syntax before save
- **Fallback**: Keep backup of original frontmatter

---

## Success Definition

✅ **Complete success when**:
- 1,066 metadata-only files extracted
- 95%+ extraction rate (1,010+ files)
- All extracted content has Vietnamese diacritics preserved
- Final database: 3,300+ files with content (97% coverage)
- All scripts complete without fatal errors
- MemAgent re-indexed and functional

---

**Status**: Ready for execution
**Start Date**: December 2, 2025
**Estimated Completion**: December 2, 2025 (same day, 5-7 hours)
