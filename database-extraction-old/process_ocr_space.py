#!/usr/bin/env python3
"""
Process scanned PDFs via OCR.SPACE free API.
OCR.SPACE allows 25,000 requests/month free (no registration required).
"""

import json
import time
from pathlib import Path
from typing import Dict, List
import subprocess

try:
    import requests
except ImportError:
    print("Installing requests...")
    subprocess.check_call(["python3", "-m", "pip", "install", "requests", "-q"])
    import requests


class OCRSpaceProcessor:
    """Process PDFs using OCR.SPACE API."""

    # Use free API endpoint (no registration needed)
    API_URL = "https://api.ocr.space/parse"

    @staticmethod
    def process_pdf(pdf_path: str, timeout: int = 120) -> str:
        """
        Process a PDF file via OCR.SPACE API (free tier).
        Returns: extracted text
        """
        try:
            with open(pdf_path, "rb") as pdf_file:
                # Free tier endpoint - no API key needed for free usage
                payload = {
                    "isOverlayRequired": False,
                    "language": "eng",  # OCR.SPACE auto-detects, eng is default
                    "isTable": False,
                }

                files = {"filename": pdf_file}

                print(f"  🔄 Sending to OCR.SPACE: {Path(pdf_path).name}...")

                # Use free endpoint with longer timeout
                response = requests.post(
                    OCRSpaceProcessor.API_URL,
                    data=payload,
                    files=files,
                    timeout=timeout,
                )

                if response.status_code not in [200, 201]:
                    error_msg = response.text[:200] if response.text else ""
                    print(f"     ⚠️  HTTP {response.status_code}: {error_msg}")
                    return ""

                try:
                    result = response.json()
                except:
                    print(f"     ⚠️  Invalid JSON response")
                    return ""

                if result.get("IsErroredOnProcessing"):
                    error = result.get("ErrorMessage", "Unknown error")
                    print(f"     ⚠️  OCR Error: {error}")
                    return ""

                text = result.get("ParsedText", "").strip()
                if text:
                    print(f"     ✅ Extracted {len(text)} characters")
                else:
                    print(f"     ⚠️  No text extracted (possibly blank page)")
                return text

        except requests.exceptions.Timeout:
            print(f"     ⚠️  Timeout (PDF too large or slow connection)")
            return ""
        except requests.exceptions.ConnectionError:
            print(f"     ⚠️  Connection error (check internet)")
            return ""
        except Exception as e:
            print(f"     ⚠️  Error: {str(e)[:100]}")
            return ""


class OCRPipeline:
    """Orchestrate OCR processing."""

    def __init__(self, manifest_path: str):
        self.manifest_path = Path(manifest_path)
        with open(manifest_path) as f:
            self.manifest = json.load(f)

    def process_batch(self, start_idx: int = 0, limit: int = None) -> Dict:
        """
        Process a batch of scanned PDFs.

        Args:
            start_idx: Start from this index
            limit: Process maximum N files (None = all)
        """
        files = self.manifest["files"]
        end_idx = len(files) if limit is None else min(start_idx + limit, len(files))

        stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "failed_files": [],
        }

        print(f"\n{'='*70}")
        print(f"OCR.SPACE BATCH PROCESSING")
        print(f"{'='*70}")
        print(f"Processing {end_idx - start_idx} of {len(files)} scanned PDFs\n")

        for idx, item in enumerate(files[start_idx:end_idx], start=start_idx + 1):
            source_pdf = item["source_pdf"]
            target_md = item["target_markdown"]

            if not Path(source_pdf).exists():
                print(f"❌ [{idx}/{end_idx}] PDF not found: {Path(source_pdf).name}")
                stats["failed"] += 1
                stats["failed_files"].append(Path(source_pdf).name)
                continue

            # Process with OCR.SPACE
            extracted_text = OCRSpaceProcessor.process_pdf(source_pdf)

            stats["processed"] += 1

            if extracted_text and len(extracted_text) > 50:
                # Update markdown
                if self._update_markdown(target_md, extracted_text):
                    stats["succeeded"] += 1
                    item["processed"] = True
                    print(f"   📝 Updated: {Path(target_md).name}\n")
                else:
                    stats["failed"] += 1
                    stats["failed_files"].append(Path(source_pdf).name)
                    print(f"   ⚠️  Failed to update markdown\n")
            else:
                stats["failed"] += 1
                stats["failed_files"].append(Path(source_pdf).name)
                print(f"   ⚠️  No text extracted\n")

            # Rate limiting: OCR.SPACE is free so let's be respectful
            if idx < end_idx:
                time.sleep(2)  # 2 second delay between requests

        # Save updated manifest
        self._save_manifest()

        return stats

    @staticmethod
    def _update_markdown(md_path: str, extracted_text: str) -> bool:
        """Update markdown file with OCR'd text."""
        try:
            md_file = Path(md_path)
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract frontmatter
            import re

            match = re.match(r"(---\n.*?\n---\n)", content, re.DOTALL)
            if not match:
                return False

            frontmatter = match.group(1)
            new_content = frontmatter + "\n" + extracted_text

            with open(md_file, "w", encoding="utf-8") as f:
                f.write(new_content)

            return True
        except Exception as e:
            print(f"   ⚠️  Update error: {e}")
            return False

    def _save_manifest(self):
        """Save updated manifest."""
        with open(self.manifest_path, "w") as f:
            json.dump(self.manifest, f, indent=2)
        print(f"📋 Manifest saved: {self.manifest_path}")

    def print_summary(self, stats: Dict):
        """Print processing summary."""
        total = self.manifest["total_scanned"]
        processed_count = sum(1 for f in self.manifest["files"] if f.get("processed"))

        print(f"\n{'='*70}")
        print(f"OCR PROCESSING SUMMARY")
        print(f"{'='*70}")
        print(f"Total scanned PDFs:       {total}")
        print(f"Processed so far:         {processed_count}")
        print(f"")
        print(f"✅ This batch succeeded:  {stats['succeeded']}")
        print(f"⚠️  This batch failed:     {stats['failed']}")
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
    manifest_path = "/Users/teije/Desktop/memagent-modular-fixed/ocr_manifest.json"

    if not Path(manifest_path).exists():
        print("❌ ocr_manifest.json not found.")
        print("   Run extract_all_documents.py first to generate it.")
        return

    pipeline = OCRPipeline(manifest_path)

    # Process first 10 scanned PDFs as a test
    print("\n🚀 Starting OCR.SPACE processing...")
    print("   (Free tier: 25,000 requests/month)")
    print("   Processing first 10 PDFs as a test batch\n")

    stats = pipeline.process_batch(start_idx=0, limit=10)
    pipeline.print_summary(stats)

    print("\n💡 To continue processing more PDFs:")
    print("   - Run: python3 process_ocr_space.py <start_index> <limit>")
    print("   - Example: python3 process_ocr_space.py 10 10  (process next 10)")
    print("   - Example: python3 process_ocr_space.py 0 100  (process 100 from start)")


if __name__ == "__main__":
    main()
