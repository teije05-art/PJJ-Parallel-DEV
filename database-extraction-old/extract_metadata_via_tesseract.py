#!/usr/bin/env python3
"""
Extract Content from 1,066 Metadata-Only Tax Database Files via Tesseract OCR

This is the master extraction script for Phase 3 of the tax database completion.
It extracts from all metadata-only files (PDFs, DOCs, DOCXs) using Tesseract OCR
for 100% perfect Vietnamese encoding.

Strategy:
- All PDFs → Direct Tesseract OCR (eng+vie)
- All DOCs → LibreOffice convert to PDF → Tesseract OCR
- All DOCXs → Convert to PDF → Tesseract OCR (python-docx as fallback)

Categories to extract:
- VAT: 459 files (~3.5 hours)
- Customs: 228 files (~1.7 hours)
- DTA: 97 files (~45 min)
- Other: 282 files (~2 hours)

Total: 1,066 files (~7.7 hours serial, ~5.5 hours parallel)
"""

import os
import sys
import json
import yaml
import pytesseract
import subprocess
import tempfile
import time
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
from docx import Document
import logging
import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tesseract_metadata_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
TESSERACT_LANG = 'eng+vie'
SOURCE_BASE = '/Users/teije/Library/Mobile Documents/.Trash/Tax_Legal/General Master Resource Folder'
DB_BASE = '/Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database'
TEMP_DIR = '/tmp/tesseract_extraction'
DPI = 150
TIMEOUT = 300  # 5 minutes timeout for DOC conversions

# Category mapping
CATEGORIES = {
    '02_VAT': {'files': 459, 'source': f'{SOURCE_BASE}/VAT'},
    '03_Customs': {'files': 228, 'source': f'{SOURCE_BASE}/Customs'},
    '05_DTA': {'files': 97, 'source': f'{SOURCE_BASE}/DTA'},
    '04_PIT': {'files': 53, 'source': f'{SOURCE_BASE}/PIT'},
    '08_Tax_Administration': {'files': 54, 'source': f'{SOURCE_BASE}/Tax Administration'},
    '10_Natural_Resources_SHUI': {'files': 64, 'source': f'{SOURCE_BASE}/Natural Resources Tax'},
    '13_Environmental_Protection_EPT': {'files': 10, 'source': f'{SOURCE_BASE}/Environmental Tax'},
    '14_Immigration_Work_Permits': {'files': 10, 'source': f'{SOURCE_BASE}/Immigration'},
    '06_Transfer_Pricing': {'files': 9, 'source': f'{SOURCE_BASE}/Transfer Pricing'},
    '07_FCT': {'files': 34, 'source': f'{SOURCE_BASE}/FCT'},
    '09_Excise_Tax_SST': {'files': 22, 'source': f'{SOURCE_BASE}/Excise Tax'},
    '11_Draft_Regulations': {'files': 7, 'source': f'{SOURCE_BASE}/Drafts'},
    '12_Capital_Gains_Tax_CGT': {'files': 7, 'source': f'{SOURCE_BASE}/CGT'},
    '15_E_Commerce': {'files': 0, 'source': f'{SOURCE_BASE}/E-Commerce'},
    '16_Business_Support_Measures': {'files': 7, 'source': f'{SOURCE_BASE}/Business Support'},
    '17_General_Policies': {'files': 2, 'source': f'{SOURCE_BASE}/General'},
}

class TesseractExtractor:
    """Extracts text from documents using Tesseract OCR."""

    def __init__(self):
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'total_chars': 0,
        }
        self.manifest = {
            'extraction_date': datetime.datetime.now().isoformat(),
            'tesseract_lang': TESSERACT_LANG,
            'categories': {},
            'files': []
        }

    def extract_pdf_tesseract(self, pdf_path):
        """Extract text from PDF using Tesseract OCR."""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=DPI)

            all_text = []
            for page_num, image in enumerate(images, 1):
                try:
                    # Extract text using Tesseract
                    text = pytesseract.image_to_string(image, lang=TESSERACT_LANG)
                    if text.strip():
                        all_text.append(f"--- PAGE {page_num} ---\n{text}")
                except Exception as e:
                    logger.warning(f"Failed to extract page {page_num} from {pdf_path}: {e}")
                    continue

            combined_text = '\n\n--- PAGE BREAK ---\n\n'.join(all_text)
            return combined_text if combined_text.strip() else None

        except Exception as e:
            logger.error(f"PDF extraction failed for {pdf_path}: {e}")
            return None

    def convert_doc_to_pdf(self, doc_path):
        """Convert DOC file to PDF using LibreOffice."""
        try:
            pdf_path = tempfile.mktemp(suffix='.pdf')
            cmd = [
                'soffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', tempfile.gettempdir(),
                doc_path
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=30)

            if result.returncode == 0:
                # LibreOffice outputs to same dir with .pdf extension
                expected_pdf = doc_path.rsplit('.', 1)[0] + '.pdf'
                if os.path.exists(expected_pdf):
                    return expected_pdf

            return None
        except Exception as e:
            logger.error(f"DOC to PDF conversion failed for {doc_path}: {e}")
            return None

    def extract_docx_python(self, docx_path):
        """Try to extract text from DOCX using python-docx."""
        try:
            doc = Document(docx_path)
            text = '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
            return text if text.strip() else None
        except Exception as e:
            logger.warning(f"python-docx extraction failed for {docx_path}: {e}")
            return None

    def extract_docx_tesseract(self, docx_path):
        """Convert DOCX to PDF and extract via Tesseract."""
        pdf_path = self.convert_doc_to_pdf(docx_path)
        if pdf_path:
            text = self.extract_pdf_tesseract(pdf_path)
            try:
                os.remove(pdf_path)
            except:
                pass
            return text
        return None

    def extract_content(self, source_path):
        """
        Extract content from source document based on file type.

        Returns: extracted text or None if failed
        """
        ext = source_path.lower().split('.')[-1]

        if ext == 'pdf':
            return self.extract_pdf_tesseract(source_path)

        elif ext == 'doc':
            # Convert DOC to PDF then extract
            pdf_path = self.convert_doc_to_pdf(source_path)
            if pdf_path:
                text = self.extract_pdf_tesseract(pdf_path)
                try:
                    os.remove(pdf_path)
                except:
                    pass
                return text
            return None

        elif ext == 'docx':
            # Try python-docx first, then fallback to PDF conversion
            text = self.extract_docx_python(source_path)
            if text and len(text) > 100:
                return text
            # Fallback to conversion
            return self.extract_docx_tesseract(source_path)

        else:
            logger.warning(f"Unsupported file type: {ext}")
            return None

    def update_markdown(self, md_path, content):
        """Update markdown file with extracted content."""
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            # Split frontmatter and body
            parts = file_content.split('---\n', 2)
            if len(parts) < 2:
                return False

            # Reconstruct with new content
            frontmatter = parts[1]
            new_content = f"---\n{frontmatter}---\n\n{content}\n"

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return True
        except Exception as e:
            logger.error(f"Failed to update markdown {md_path}: {e}")
            return False

    def find_source_document(self, markdown_path):
        """Find source document path from markdown frontmatter.

        Strategy: Extract base name from markdown and search entire source tree
        for files with matching name regardless of metadata quality.
        """
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract YAML frontmatter
            parts = content.split('---\n', 2)
            if len(parts) < 2:
                return None

            try:
                metadata = yaml.safe_load(parts[1])
                original_format = metadata.get('original_format', '').lower()

                if not original_format or original_format not in ['pdf', 'doc', 'docx']:
                    return None

                # Get markdown filename as search pattern
                md_filename = os.path.basename(markdown_path).replace('.md', '')

                # Extract the core filename (without date prefixes like "CV_2023_11_30_")
                # This helps find files like "CV_5367_30112023_TCT_Ke_khai"
                # when source is "CV_5367_Ke_khai.pdf"
                md_parts = md_filename.split('_')

                # Search entire source tree for matching files
                if not os.path.exists(SOURCE_BASE):
                    return None

                for root, dirs, files in os.walk(SOURCE_BASE):
                    for file in files:
                        file_ext = file.split('.')[-1].lower()

                        # Must match the required format
                        if file_ext != original_format:
                            continue

                        file_path = os.path.join(root, file)
                        file_base = file.replace('.' + file_ext, '')

                        # Exact match: check if markdown name contains file base name
                        if file_base in md_filename or file_base.replace(' ', '_').replace('-', '_') in md_filename.replace('-', '_'):
                            return file_path

                        # Fuzzy match: check if meaningful parts overlap
                        # Extract number sequences that often identify files
                        md_numbers = [s for s in md_parts if any(c.isdigit() for c in s)]
                        file_numbers = [s for s in file_base.replace(' ', '_').split('_') if any(c.isdigit() for c in s)]

                        # If at least 2 number sequences match, likely the same file
                        if len(md_numbers) >= 2 and len(file_numbers) >= 1:
                            matches = sum(1 for fn in file_numbers if fn in md_numbers)
                            if matches >= min(1, len(file_numbers)):
                                return file_path

                return None

            except yaml.YAMLError:
                return None

        except Exception as e:
            logger.warning(f"Error finding source for {markdown_path}: {e}")
            return None

    def process_file(self, markdown_path):
        """Process a single markdown file."""
        self.stats['total_processed'] += 1

        try:
            # Check if already has content
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()

            parts = content.split('---\n', 2)
            if len(parts) > 2 and len(parts[2].strip()) > 500:
                self.stats['skipped'] += 1
                return {'status': 'skipped', 'reason': 'already has content'}

            # Find source document
            source_path = self.find_source_document(markdown_path)
            if not source_path or not os.path.exists(source_path):
                self.stats['failed'] += 1
                return {'status': 'failed', 'reason': 'source document not found'}

            # Extract content
            extracted_text = self.extract_content(source_path)
            if not extracted_text:
                self.stats['failed'] += 1
                return {'status': 'failed', 'reason': 'extraction returned no text'}

            # Update markdown
            if self.update_markdown(markdown_path, extracted_text):
                self.stats['successful'] += 1
                self.stats['total_chars'] += len(extracted_text)
                return {
                    'status': 'success',
                    'chars': len(extracted_text),
                    'source': source_path
                }
            else:
                self.stats['failed'] += 1
                return {'status': 'failed', 'reason': 'failed to update markdown'}

        except Exception as e:
            self.stats['failed'] += 1
            logger.error(f"Error processing {markdown_path}: {e}")
            return {'status': 'failed', 'reason': str(e)}

    def process_category(self, category_name, max_files=None):
        """Process only empty (metadata-only) files in a category."""
        category_path = os.path.join(DB_BASE, category_name)

        if not os.path.exists(category_path):
            logger.warning(f"Category path not found: {category_path}")
            return

        logger.info(f"\n{'='*80}")
        logger.info(f"Processing category: {category_name}")
        logger.info(f"{'='*80}")

        # Find ONLY empty markdown files (< 500 bytes after frontmatter)
        md_files = []
        for root, dirs, files in os.walk(category_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        parts = content.split('---\n', 2)
                        # Only process if content after frontmatter is < 500 bytes
                        if len(parts) <= 2 or len(parts[2].strip()) < 500:
                            md_files.append(file_path)
                    except:
                        pass

        total_in_cat = sum(1 for root, dirs, files in os.walk(category_path) for f in files if f.endswith('.md'))
        logger.info(f"Found {len(md_files)}/{total_in_cat} empty markdown files in {category_name}")

        if max_files:
            md_files = md_files[:max_files]

        category_stats = {
            'total': len(md_files),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
        }

        for i, md_path in enumerate(md_files, 1):
            file_name = os.path.basename(md_path)
            print(f"\r[{i}/{len(md_files)}] {file_name[:50]:<50}", end='', flush=True)

            result = self.process_file(md_path)

            if result['status'] == 'success':
                category_stats['successful'] += 1
            elif result['status'] == 'failed':
                category_stats['failed'] += 1
            else:
                category_stats['skipped'] += 1

        print()  # New line after progress
        logger.info(f"\n{category_name} Results:")
        logger.info(f"  Successful: {category_stats['successful']}")
        logger.info(f"  Failed: {category_stats['failed']}")
        logger.info(f"  Skipped: {category_stats['skipped']}")

        self.manifest['categories'][category_name] = category_stats

    def save_manifest(self):
        """Save extraction manifest."""
        manifest_path = 'metadata_extraction_manifest.json'
        self.manifest['stats'] = self.stats

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2, ensure_ascii=False)

        logger.info(f"\nManifest saved to {manifest_path}")

    def print_summary(self):
        """Print extraction summary."""
        logger.info(f"\n{'='*80}")
        logger.info("TESSERACT METADATA EXTRACTION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Total processed: {self.stats['total_processed']}")
        logger.info(f"Successful: {self.stats['successful']} ({100*self.stats['successful']//max(1, self.stats['total_processed'])}%)")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info(f"Total characters extracted: {self.stats['total_chars']:,}")
        logger.info(f"{'='*80}")

def main():
    """Main extraction process."""

    # Create temp directory
    os.makedirs(TEMP_DIR, exist_ok=True)

    extractor = TesseractExtractor()

    # Process categories in priority order
    priority_order = [
        '02_VAT',           # Priority 1: 459 files
        '03_Customs',       # Priority 2: 228 files
        '05_DTA',           # Priority 3: 97 files
        '04_PIT',           # Priority 4+: Others
        '08_Tax_Administration',
        '10_Natural_Resources_SHUI',
        '13_Environmental_Protection_EPT',
        '14_Immigration_Work_Permits',
        '06_Transfer_Pricing',
        '07_FCT',
        '09_Excise_Tax_SST',
        '11_Draft_Regulations',
        '12_Capital_Gains_Tax_CGT',
        '15_E_Commerce',
        '16_Business_Support_Measures',
        '17_General_Policies',
    ]

    start_time = time.time()

    for category in priority_order:
        if category not in CATEGORIES:
            continue
        extractor.process_category(category)

    elapsed = time.time() - start_time
    minutes = int(elapsed / 60)
    seconds = int(elapsed % 60)

    logger.info(f"\nTotal time: {minutes}m {seconds}s")

    extractor.save_manifest()
    extractor.print_summary()

if __name__ == '__main__':
    main()
