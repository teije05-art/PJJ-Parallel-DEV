#!/usr/bin/env python3
"""Quick test of extraction on small subset - PDF file"""

import sys
sys.path.insert(0, '/Users/teije/Desktop/memagent-modular-fixed')

from extract_tax_documents import TextExtractor
from pathlib import Path

# Test extracting from one specific PDF file
source_path = Path("/Users/teije/Library/Mobile Documents/.Trash/Tax_Legal/General Master Resource Folder/SHUI/CV 3945-300915-Huong dan ve tro cap thoi viec, BHTN, nghi om, tien luong tinh lam them gio bgom phu cap.pdf")

print(f"Testing extraction from: {source_path.name}")
print(f"File exists: {source_path.exists()}")
if source_path.exists():
    print(f"File size: {source_path.stat().st_size} bytes")
else:
    print("File not found, trying alternate...")
    # Find any PDF
    parent = Path("/Users/teije/Library/Mobile Documents/.Trash/Tax_Legal/General Master Resource Folder/SHUI")
    pdfs = list(parent.glob("*.pdf"))
    if pdfs:
        source_path = pdfs[0]
        print(f"Using: {source_path.name}")

print()

text = TextExtractor.extract_text(source_path)
print(f"Extracted {len(text)} characters")
if text:
    print(f"First 300 characters:")
    print(text[:300])
else:
    print("No text extracted")

