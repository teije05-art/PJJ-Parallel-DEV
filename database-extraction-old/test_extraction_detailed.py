#!/usr/bin/env python3
"""
Detailed extraction debugging - trace DOC conversion and Tesseract
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

# Configuration
DOC_FILE = '/Users/teije/Library/Mobile Documents/.Trash/Tax_Legal/General Master Resource Folder/VAT/CV 2023/CV 1952-09.2.2023_CT Binh Duong_Ben ban tu huy hoa don thi hoa don bat hop phap.doc'
TESSERACT_LANG = 'eng+vie'
DPI = 150
TIMEOUT = 600

print("=" * 80)
print("DETAILED EXTRACTION DEBUG")
print("=" * 80)

# Step 1: Check source file
print(f"\n[STEP 1] Source file check")
print(f"File: {DOC_FILE}")
print(f"Exists: {os.path.exists(DOC_FILE)}")
print(f"Size: {os.path.getsize(DOC_FILE):,} bytes")

# Step 2: Convert DOC to PDF
print(f"\n[STEP 2] Converting DOC to PDF via LibreOffice...")
try:
    pdf_path = tempfile.mktemp(suffix='.pdf')
    print(f"Output PDF: {pdf_path}")

    cmd = [
        'soffice',
        '--headless',
        '--convert-to', 'pdf',
        '--outdir', tempfile.gettempdir(),
        DOC_FILE
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, timeout=TIMEOUT, text=True)

    print(f"Return code: {result.returncode}")
    if result.stdout:
        print(f"Stdout: {result.stdout[:200]}")
    if result.stderr:
        print(f"Stderr: {result.stderr[:200]}")

    # Check expected output location
    expected_pdf = DOC_FILE.rsplit('.', 1)[0] + '.pdf'
    print(f"\nExpected PDF path: {expected_pdf}")
    print(f"Expected PDF exists: {os.path.exists(expected_pdf)}")

    if os.path.exists(expected_pdf):
        pdf_size = os.path.getsize(expected_pdf)
        print(f"PDF size: {pdf_size:,} bytes")
        pdf_path = expected_pdf
    else:
        print("ERROR: Expected PDF not found!")
        sys.exit(1)

except subprocess.TimeoutExpired:
    print("ERROR: Conversion timed out!")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

# Step 3: Convert PDF to images
print(f"\n[STEP 3] Converting PDF to images...")
try:
    images = convert_from_path(pdf_path, dpi=DPI)
    print(f"Pages extracted: {len(images)}")
    if images:
        print(f"First image size: {images[0].size}")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

# Step 4: Extract text from first few pages
print(f"\n[STEP 4] Extracting text via Tesseract...")
try:
    all_text = []
    for page_num, image in enumerate(images[:3], 1):  # Test first 3 pages
        try:
            text = pytesseract.image_to_string(image, lang=TESSERACT_LANG)
            text_len = len(text.strip())
            print(f"Page {page_num}: {text_len} characters")
            if text.strip():
                all_text.append(f"--- PAGE {page_num} ---\n{text}")
                print(f"  Preview: {text[:100]}...")
            else:
                print(f"  (empty page)")
        except Exception as e:
            print(f"Page {page_num}: ERROR - {e}")

    if all_text:
        combined = '\n\n--- PAGE BREAK ---\n\n'.join(all_text)
        print(f"\nTotal extracted: {len(combined)} characters")
        print(f"Preview:\n{combined[:300]}...")
    else:
        print("\nERROR: No text extracted from any page!")

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

# Cleanup
print(f"\n[CLEANUP]")
try:
    os.remove(pdf_path)
    print(f"Removed temp PDF")
except:
    pass

print("\n" + "=" * 80)
