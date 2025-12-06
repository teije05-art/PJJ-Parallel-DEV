#!/usr/bin/env python3
"""
Process scanned PDFs using local Tesseract OCR.
Works offline, supports Vietnamese, no API limits.
"""

import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import pytesseract
except ImportError:
    print("Installing pytesseract...")
    subprocess.check_call(["python3", "-m", "pip", "install", "pytesseract", "-q"])
    import pytesseract

try:
    from pdf2image import convert_from_path
except ImportError:
    print("Installing pdf2image...")
    subprocess.check_call(["python3", "-m", "pip", "install", "pdf2image", "-q"])
    from pdf2image import convert_from_path

from PIL import Image


class TesseractOCR:
    """Process PDFs using local Tesseract OCR."""

    @staticmethod
    def extract_from_pdf(pdf_path: str, lang: str = "eng+vie") -> Tuple[str, bool]:
        """
        Extract text from PDF using Tesseract OCR.
        Converts PDF to images and runs OCR on each page.

        Args:
            pdf_path: Path to PDF file
            lang: Language for OCR (eng=English, vie=Vietnamese, eng+vie=both)

        Returns:
            (extracted_text, success)
        """
        try:
            print(f"  🔄 Converting PDF to images: {Path(pdf_path).name}...")

            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=150)  # 150 DPI is good balance

            if not images:
                print(f"     ⚠️  No pages extracted from PDF")
                return "", False

            print(f"     📄 {len(images)} pages extracted, running OCR...")

            # Run OCR on each page and combine results
            text_parts = []
            for idx, image in enumerate(images):
                try:
                    # Run Tesseract OCR
                    text = pytesseract.image_to_string(image, lang=lang)

                    if text.strip():
                        text_parts.append(text)
                        print(f"     ✓ Page {idx + 1}: {len(text)} chars")
                    else:
                        print(f"     ✗ Page {idx + 1}: No text found")
                except Exception as e:
                    print(f"     ⚠️  Page {idx + 1} error: {str(e)[:50]}")
                    continue

            full_text = "\n\n--- PAGE BREAK ---\n\n".join(text_parts).strip()

            if full_text:
                print(f"     ✅ Extracted {len(full_text)} characters")
                return full_text, True
            else:
                print(f"     ⚠️  No text extracted from any page")
                return "", False

        except Exception as e:
            print(f"     ❌ Error: {str(e)[:100]}")
            return "", False


class TesseractPipeline:
    """Orchestrate Tesseract OCR processing."""

    def __init__(self, manifest_path: str):
        self.manifest_path = Path(manifest_path)
        with open(manifest_path) as f:
            self.manifest = json.load(f)
        self.stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
            "failed_files": [],
        }

    def process_batch(self, start_idx: int = 0, limit: int = None) -> Dict:
        """
        Process a batch of scanned PDFs with Tesseract.

        Args:
            start_idx: Start from this index
            limit: Process maximum N files (None = all)
        """
        files = self.manifest["files"]
        end_idx = len(files) if limit is None else min(start_idx + limit, len(files))

        print(f"\n{'='*70}")
        print(f"TESSERACT OCR BATCH PROCESSING")
        print(f"{'='*70}")
        print(f"Processing PDFs {start_idx + 1}-{end_idx} of {len(files)} total\n")

        for idx, item in enumerate(files[start_idx:end_idx], start=start_idx + 1):
            source_pdf = item["source_pdf"]
            target_md = item["target_markdown"]
            pdf_name = Path(source_pdf).name

            # Skip if already processed
            if item.get("processed"):
                print(f"[{idx}/{end_idx}] ⏭️  SKIP: {pdf_name} (already processed)")
                self.stats["skipped"] += 1
                continue

            if not Path(source_pdf).exists():
                print(f"[{idx}/{end_idx}] ❌ PDF NOT FOUND: {pdf_name}")
                self.stats["failed"] += 1
                self.stats["failed_files"].append(pdf_name)
                continue

            print(f"[{idx}/{end_idx}] {pdf_name}")

            # Extract with Tesseract
            extracted_text, success = TesseractOCR.extract_from_pdf(source_pdf)
            self.stats["processed"] += 1

            if success and extracted_text and len(extracted_text) > 50:
                # Update markdown
                if self._update_markdown(target_md, extracted_text):
                    self.stats["succeeded"] += 1
                    item["processed"] = True
                    print(f"   📝 Updated markdown\n")
                else:
                    self.stats["failed"] += 1
                    self.stats["failed_files"].append(pdf_name)
                    print(f"   ⚠️  Failed to update markdown\n")
            else:
                self.stats["failed"] += 1
                self.stats["failed_files"].append(pdf_name)
                print(f"   ⚠️  Extraction failed or no text found\n")

        # Save updated manifest
        self._save_manifest()

        return self.stats

    @staticmethod
    def _update_markdown(md_path: str, extracted_text: str) -> bool:
        """Update markdown file with OCR'd text."""
        try:
            md_file = Path(md_path)
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract frontmatter
            match = re.match(r"(---\n.*?\n---\n)", content, re.DOTALL)
            if not match:
                return False

            frontmatter = match.group(1)
            new_content = frontmatter + "\n" + extracted_text

            with open(md_file, "w", encoding="utf-8") as f:
                f.write(new_content)

            return True
        except Exception as e:
            print(f"   ⚠️  Markdown update error: {str(e)[:50]}")
            return False

    def _save_manifest(self):
        """Save updated manifest."""
        with open(self.manifest_path, "w") as f:
            json.dump(self.manifest, f, indent=2)

    def print_summary(self, stats: Dict):
        """Print processing summary."""
        total = self.manifest["total_scanned"]
        processed_count = sum(1 for f in self.manifest["files"] if f.get("processed"))

        print(f"\n{'='*70}")
        print(f"BATCH SUMMARY")
        print(f"{'='*70}")
        print(f"Total scanned PDFs:       {total}")
        print(f"Processed so far:         {processed_count}")
        print(f"")
        print(f"This batch:")
        print(f"  ✅ Succeeded:           {stats['succeeded']}")
        print(f"  ⏭️  Skipped:             {stats['skipped']}")
        print(f"  ⚠️  Failed:              {stats['failed']}")
        print(f"")
        print(f"📊 Overall progress:      {processed_count}/{total} ({100*processed_count//total}%)")

        if stats["failed_files"]:
            print(f"\n⚠️  Failed files in this batch:")
            for f in stats["failed_files"][:5]:
                print(f"   - {f}")
            if len(stats["failed_files"]) > 5:
                print(f"   ... and {len(stats['failed_files']) - 5} more")

        print(f"{'='*70}\n")


def main():
    """Main entry point."""
    import sys

    manifest_path = "/Users/teije/Desktop/memagent-modular-fixed/ocr_manifest.json"

    if not Path(manifest_path).exists():
        print("❌ ocr_manifest.json not found.")
        print("   Run extract_all_documents.py first.")
        return

    # Parse command-line arguments
    start_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10  # Default: 10 at a time

    pipeline = TesseractPipeline(manifest_path)

    print("\n🚀 Starting Tesseract OCR processing...")
    print(f"   (Local OCR - no API limits, supports Vietnamese)\n")

    stats = pipeline.process_batch(start_idx=start_idx, limit=limit)
    pipeline.print_summary(stats)

    # Calculate next batch
    processed_count = sum(1 for f in pipeline.manifest["files"] if f.get("processed"))
    total = pipeline.manifest["total_scanned"]
    remaining = total - processed_count

    if remaining > 0:
        next_start = start_idx + limit
        print(f"\n💡 To continue processing:")
        print(f"   python3 process_tesseract_ocr.py {next_start} 10")
        print(f"   (Process next 10 starting from index {next_start})")
        print(f"\n   Or process all remaining {remaining} at once:")
        print(f"   python3 process_tesseract_ocr.py {next_start} {remaining}")
    else:
        print(f"\n✅ ALL SCANNED PDFs PROCESSED!")


if __name__ == "__main__":
    main()
