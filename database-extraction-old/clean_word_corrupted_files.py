#!/usr/bin/env python3
"""
Clean Word 97-2003 Binary Markers from Tax Database Files

This script removes Word binary markers and formatting codes from 12 corrupted
markdown files in the CIT category, while preserving the actual Vietnamese text content.

Affected Files: 12 files with 'bjbjzXzX' markers in 01_CIT category
Processing: Extract readable text, preserve Vietnamese encoding
Result: Clean markdown files with proper format
"""

import os
import re
import yaml
from pathlib import Path

# List of files to clean
CORRUPTED_FILES = [
    "/Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database/01_CIT/CIT_Deductions_Depreciation/CV_1037_0375_01_01_CV_1037519914_Trich_lap.md",
    "/Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database/01_CIT/CIT_Deductions_Depreciation/CV_1256_2568_01_01_CV_12568090915BTCKhong_trich_lap.md",
    "/Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database/01_CIT/CIT_Miscellaneous/CV_1028_0287_01_01_CV_10287_CTTTHT290915Uu_dai_theo.md",
    "/Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database/01_CIT/CIT_Miscellaneous/CV_2402_0711_01_12_CV_2402120711TCTChi_phi_thue.md",
    "/Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database/01_CIT/CIT_Miscellaneous/CV_2405_2012_07_09_CV_2405_09072012TCTChi_phi_thanh.md",
    "/Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database/01_CIT/CIT_Miscellaneous/CV_3677_0814_01_29_CV_3677290814TCTKhong_an_dinh.md",
    "/Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database/01_CIT/CIT_Miscellaneous/CV_3677_0814_01_29_CV_3677290814TCTKhong_an_dinh_v1.md",
    "/Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database/01_CIT/CIT_Miscellaneous/CV_9294_2015_10_13_CV_929413102015CTHCMChi_mua_bao.md",
    "/Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database/01_CIT/CIT_Miscellaneous/CV_9607_2015_10_23_CV_960723102015CTHCMKhoan_chi_bao.md",
    "/Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database/01_CIT/CIT_Miscellaneous/Doc_2465_Undated_QD_2465_DinhchinhTT96_2015.md",
    "/Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database/01_CIT/CIT_Miscellaneous/ND_12_Undated_ND_122015CPHuong_dan_luat.md",
    "/Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database/01_CIT/CIT_Miscellaneous/TT_212_Undated_TT_2122015BTCUu_dai_thue.md",
]

def extract_text_from_corrupted(content):
    """
    Extract readable Vietnamese text from corrupted Word-formatted content.

    Removes:
    - Word binary markers (bjbjzXzX, etc.)
    - Word formatting codes (rtf-style codes)
    - Excessive whitespace and control characters
    - XML/formatting tags

    Preserves:
    - Vietnamese text with diacritics
    - Line breaks between meaningful sections
    """

    # Remove Word binary markers
    text = re.sub(r'bjbjzXzX.*?(?=\n|$)', '', content, flags=re.DOTALL)

    # Remove Word document structure markers
    text = re.sub(r'<\?xml.*?\?>', '', text)
    text = re.sub(r'<w:.*?>', '', text)
    text = re.sub(r'<\w+:.*?>', '', text)

    # Remove RTF-style formatting codes
    text = re.sub(r'\{\\[a-z]+\d*\s*[^}]*\}', '', text)
    text = re.sub(r'\\[a-z]+\d*\s+', '', text)

    # Remove multiple spaces (but preserve some line structure)
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        # Remove excessive spaces within lines
        line = re.sub(r' {2,}', ' ', line)
        # Remove control characters and formatting markers
        line = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', line)
        # Remove standalone formatting codes
        line = re.sub(r'[_\*\~\^\`]{1,3}', '', line)
        # Clean up Word formatting artifacts
        line = re.sub(r'(?<=[a-z])\s+(?=[A-Z])', ' ', line)

        # Keep non-empty lines or lines with Vietnamese characters
        if line.strip() and (any(ord(c) > 127 for c in line) or any(c.isalnum() for c in line)):
            cleaned_lines.append(line.strip())

    # Remove excessive blank lines
    result = '\n'.join(cleaned_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)

    return result.strip()

def clean_file(file_path):
    """
    Clean a single corrupted file.

    Process:
    1. Parse YAML frontmatter
    2. Extract text from corrupted body
    3. Recombine with proper markdown format
    4. Save backup and update original
    """

    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split on first --- delimiter to separate frontmatter from body
        parts = content.split('---\n', 2)

        if len(parts) < 3:
            return False, f"Invalid frontmatter format in {file_path}"

        # Extract YAML frontmatter
        yaml_header = parts[1]
        corrupted_body = parts[2] if len(parts) > 2 else ''

        # Parse YAML to verify it's valid
        try:
            metadata = yaml.safe_load(yaml_header)
        except yaml.YAMLError as e:
            return False, f"YAML parse error: {str(e)}"

        # Extract readable text from corrupted body
        cleaned_text = extract_text_from_corrupted(corrupted_body)

        # Only update if we extracted meaningful content
        if not cleaned_text or len(cleaned_text) < 50:
            return False, f"Insufficient content extracted (only {len(cleaned_text)} chars)"

        # Reconstruct the markdown file
        reconstructed = f"---\n{yaml_header}---\n\n{cleaned_text}\n"

        # Save backup
        backup_path = file_path + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Write cleaned version
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(reconstructed)

        return True, f"Cleaned - extracted {len(cleaned_text)} characters"

    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main cleanup process."""

    print("=" * 80)
    print("WORD BINARY MARKER CLEANUP - TAX DATABASE")
    print("=" * 80)
    print(f"\nProcessing {len(CORRUPTED_FILES)} corrupted files...\n")

    successful = 0
    failed = 0
    results = []

    for i, file_path in enumerate(CORRUPTED_FILES, 1):
        file_name = os.path.basename(file_path)
        print(f"[{i}/{len(CORRUPTED_FILES)}] Processing {file_name}...")

        success, message = clean_file(file_path)

        if success:
            successful += 1
            status = "✅ SUCCESS"
            print(f"  {status}: {message}")
        else:
            failed += 1
            status = "❌ FAILED"
            print(f"  {status}: {message}")

        results.append({
            'file': file_name,
            'path': file_path,
            'status': status,
            'message': message
        })

    # Print summary
    print("\n" + "=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print(f"Total files processed: {len(CORRUPTED_FILES)}")
    print(f"Successful: {successful} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success rate: {100*successful//len(CORRUPTED_FILES)}%")
    print("\n" + "=" * 80)

    # Detailed results
    print("\nDETAILED RESULTS:")
    print("-" * 80)
    for result in results:
        print(f"\n{result['status']} {result['file']}")
        print(f"  Path: {result['path']}")
        print(f"  Status: {result['message']}")

    print("\n" + "=" * 80)
    print("BACKUPS CREATED")
    print("=" * 80)
    print("All original files backed up with .backup extension")
    print("Location: Same directory as original files")
    print("To restore: mv file.md.backup file.md")

    return successful == len(CORRUPTED_FILES)

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
