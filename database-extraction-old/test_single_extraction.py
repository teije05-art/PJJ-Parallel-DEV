#!/usr/bin/env python3
"""
Debug script to test single file extraction and trace failure points
"""

import os
import sys
import yaml
from pathlib import Path
from extract_metadata_v2 import TesseractExtractorV2

# Configuration
MD_FILE = '/Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database/02_VAT/CV 2023/CV_2023_02_09_CV_19520922023_CT_Binh.md'

# Initialize extractor
extractor = TesseractExtractorV2()

print("=" * 80)
print("SINGLE FILE EXTRACTION DEBUG")
print("=" * 80)
print(f"\nTarget file: {MD_FILE}")
print(f"File exists: {os.path.exists(MD_FILE)}")

# Step 1: Check file content
print("\n[STEP 1] Reading markdown file...")
with open(MD_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

parts = content.split('---\n', 2)
print(f"Parts found: {len(parts)}")
if len(parts) >= 2:
    print(f"Frontmatter length: {len(parts[1])}")
    if len(parts) > 2:
        print(f"Body content length: {len(parts[2].strip())}")
        print(f"Body: {parts[2][:100]}...")

# Step 2: Parse YAML
print("\n[STEP 2] Parsing YAML frontmatter...")
try:
    metadata = yaml.safe_load(parts[1])
    print(f"Original format: {metadata.get('original_format')}")
    print(f"Source folder: {metadata.get('source_folder')}")
except Exception as e:
    print(f"ERROR parsing YAML: {e}")
    sys.exit(1)

# Step 3: Find source document
print("\n[STEP 3] Finding source document...")
source_path = extractor.find_source_document(MD_FILE)
print(f"Source found: {source_path}")
if source_path:
    print(f"Source exists: {os.path.exists(source_path)}")
    print(f"Source size: {os.path.getsize(source_path)} bytes")
else:
    print("ERROR: Source document not found!")
    print("\nDEBUGGING: Searching for similar files...")
    md_filename = os.path.basename(MD_FILE).replace('.md', '')
    print(f"Markdown filename: {md_filename}")

    # Check what's in the index
    print(f"\nAvailable DOC files in index: {len(extractor.source_index['doc'])}")

    # Show some matches
    from difflib import SequenceMatcher
    matches = []
    for source_filename in extractor.source_index['doc'].keys():
        ratio = SequenceMatcher(None, md_filename.lower(), source_filename.lower()).ratio()
        if ratio > 0.3:
            matches.append((ratio, source_filename))

    matches.sort(reverse=True)
    print(f"\nTop 10 potential matches (ratio > 0.3):")
    for ratio, fname in matches[:10]:
        print(f"  {ratio:.2f}: {fname}")

    sys.exit(1)

# Step 4: Extract content
print("\n[STEP 4] Extracting content from source...")
extracted_text = extractor.extract_content(source_path)
if extracted_text:
    print(f"Extracted text length: {len(extracted_text)} bytes")
    print(f"First 200 chars: {extracted_text[:200]}...")
else:
    print("ERROR: Extraction returned no text!")
    sys.exit(1)

# Step 5: Test update markdown
print("\n[STEP 5] Testing markdown update...")

# Make a backup first
backup_file = MD_FILE + '.backup'
with open(MD_FILE, 'r', encoding='utf-8') as f:
    backup_content = f.read()
with open(backup_file, 'w', encoding='utf-8') as f:
    f.write(backup_content)
print(f"Backup created: {backup_file}")

# Try update
success = extractor.update_markdown(MD_FILE, extracted_text)
print(f"Update successful: {success}")

if success:
    print("\n[SUCCESS] File was updated!")
    with open(MD_FILE, 'r', encoding='utf-8') as f:
        new_content = f.read()
    new_parts = new_content.split('---\n', 2)
    if len(new_parts) > 2:
        print(f"New body length: {len(new_parts[2].strip())} bytes")
        print(f"New content preview: {new_parts[2][:200]}...")
else:
    print("\n[FAILURE] File update failed!")
    # Restore backup
    with open(backup_file, 'r', encoding='utf-8') as f:
        backup_content = f.read()
    with open(MD_FILE, 'w', encoding='utf-8') as f:
        f.write(backup_content)
    print("Backup restored")

print("\n" + "=" * 80)
