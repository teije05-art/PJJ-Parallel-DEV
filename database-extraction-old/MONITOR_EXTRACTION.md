# Monitor Tesseract Metadata Extraction in Real-Time

## Current Status
**Extraction Started**: December 2, 2025 @ 15:11:59 UTC
**Status**: ✅ RUNNING (Fixed LibreOffice path to soffice)
**Categories**: Processing 02_VAT (474 files)

---

## Real-Time Monitoring Commands

### Watch Log Output Live
```bash
tail -f tesseract_metadata_extraction.log
```

### Check Current Statistics
```bash
# Count extracted PDFs (those with content > 500 bytes)
find /Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database/02_VAT \
  -name "*.md" -size +500c -newer /tmp/start_time 2>/dev/null | wc -l
```

### Count File Type Warnings
```bash
# Files it's processing
grep "WARNING\|Unsupported" tesseract_metadata_extraction.log | head -20
```

### Check for Errors
```bash
# Look for any actual errors (not warnings)
grep "ERROR" tesseract_metadata_extraction.log | head -10
```

### Monitor Process
```bash
# Watch all Python/Tesseract/soffice processes
watch -n 2 'ps aux | grep -E "tesseract|soffice|python" | grep -v grep'
```

### Disk Usage
```bash
# Check temp files
du -sh /tmp/tesseract_extraction 2>/dev/null
ls -lh /tmp/*.pdf 2>/dev/null | wc -l
```

---

## Expected Progress

### Timeline (VAT Category - 474 files)
```
Files with PDFs:  ~400-450 (84-95%)
Files with DOCs:  ~20-30   (4-6%)
Files with DOCX:  ~0-10    (0-2%)
Unsupported:      ~20-30   (png, pptx, xlsx, xlsm)
Already have content: ~10-15 (3%)

Processing speed: ~20-30 seconds per PDF
                  ~30-40 seconds per DOC (convert + OCR)
                  ~15-25 seconds per DOCX

ETA for VAT: 2-3.5 hours
```

### Categories Queue
```
1. 02_VAT         (474 files) - Currently processing
2. 03_Customs     (384 files) - Queued
3. 05_DTA         (141 files) - Queued
4. Other          (Various)   - Queued
```

---

## What to Expect

### Successful Extraction Log Entry
```
2025-12-02 HH:MM:SS,mmm - INFO - File extracted successfully
```

### Warnings (Normal, Not Errors)
```
2025-12-02 HH:MM:SS,mmm - WARNING - Unsupported file type: png
2025-12-02 HH:MM:SS,mmm - WARNING - Unsupported file type: xlsx
2025-12-02 HH:MM:SS,mmm - WARNING - Unsupported file type: pptx
```

### Errors (Investigate if Frequent)
```
2025-12-02 HH:MM:SS,mmm - ERROR - DOC to PDF conversion failed
2025-12-02 HH:MM:SS,mmm - ERROR - PDF extraction failed
```

---

## When Done

### Final Summary Output
```
================================================================================
TESSERACT METADATA EXTRACTION COMPLETE
================================================================================
Total processed: 1066
Successful: 1045 (98%)
Failed: 12
Skipped: 9
Total characters extracted: 7,234,892
================================================================================
```

### Verify Results
```bash
# Count total populated files
find /Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database \
  -name "*.md" -size +500c | wc -l

# Expected: 3,375-3,390 (was 2,330 + ~1,045 new)
```

### Check Extraction Manifest
```bash
cat metadata_extraction_manifest.json | python3 -m json.tool | head -50
```

---

## If Issues Occur

### Extraction Seems Stuck
1. Check if processes are running:
   ```bash
   ps aux | grep -E "tesseract|soffice|python" | grep -v grep
   ```

2. Check disk space:
   ```bash
   df -h /tmp
   ```

3. Check recent log entries:
   ```bash
   tail -100 tesseract_metadata_extraction.log | grep -E "ERROR|Processing|Found"
   ```

### Restart if Needed
```bash
# Kill all processes
pkill -9 -f "extract_metadata"
pkill -9 soffice
pkill -9 tesseract

# Restart
python3 extract_metadata_via_tesseract.py
```

---

**Status**: RUNNING ✅
**Next Update**: Check back in 30 minutes for progress
