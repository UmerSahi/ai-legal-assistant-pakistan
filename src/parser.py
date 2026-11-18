"""
Document Parsing & OCR Pipeline Module
Task 2: AI Legal Assistant (Khan & Associates)
Detects digital vs scanned PDFs, extracts structured text and tables via PyMuPDF,
and provides OCR bridge for scanned/rasterized documents.
"""

import os
import re
from typing import Dict, List, Any, Optional, Tuple
import pymupdf


class DocumentParser:
    """Extracts text, tables, and detects digital vs scanned state in legal PDFs."""

    def __init__(self, scanned_char_threshold: int = 60):
        self.scanned_char_threshold = scanned_char_threshold

    def analyze_pdf_nature(self, pdf_path: str) -> Dict[str, Any]:
        """
        Determines whether a PDF is digital (text-layer present) or scanned (image-only).
        Analyzes character count per page, image presence, and font descriptors.
        """
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        page_stats = []

        total_chars = 0
        total_images = 0
        scanned_pages_count = 0

        for page_idx in range(total_pages):
            page = doc[page_idx]
            text = page.get_text() or ""
            chars = len(text.strip())
            images = len(page.get_images(full=True))
            
            total_chars += chars
            total_images += images

            is_page_scanned = (chars < self.scanned_char_threshold and images > 0) or (chars == 0)
            if is_page_scanned:
                scanned_pages_count += 1

            page_stats.append({
                "page_num": page_idx + 1,
                "char_count": chars,
                "image_count": images,
                "is_scanned": is_page_scanned
            })

        doc.close()

        avg_chars_per_page = total_chars / max(total_pages, 1)
        # Document is classified as scanned if > 50% of sampled pages are scanned
        is_scanned_doc = (scanned_pages_count / max(total_pages, 1)) >= 0.5

        return {
            "pdf_path": pdf_path,
            "total_pages": total_pages,
            "total_chars": total_chars,
            "avg_chars_per_page": round(avg_chars_per_page, 2),
            "total_images": total_images,
            "scanned_pages_count": scanned_pages_count,
            "is_scanned": is_scanned_doc,
            "classification": "Scanned / Image-Based PDF" if is_scanned_doc else "Digital Text PDF",
            "page_breakdown": page_stats[:5] # Sample of first 5 pages
        }

    def extract_text_and_tables(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extracts plain text, structural layout blocks, and structured tables from a PDF.
        """
        nature = self.analyze_pdf_nature(pdf_path)
        doc = pymupdf.open(pdf_path)
        
        full_text_pages = []
        extracted_tables = []
        structured_blocks = []

        for page_idx, page in enumerate(doc):
            # 1. Plain text extraction
            page_text = page.get_text() or ""
            full_text_pages.append(page_text)

            # 2. Block layout extraction (bounding boxes, reading order)
            blocks = page.get_text("blocks")
            for b in blocks:
                # b format: (x0, y0, x1, y1, "text", block_no, block_type)
                # block_type: 0 for text, 1 for image
                if b[6] == 0 and b[4].strip():
                    structured_blocks.append({
                        "page": page_idx + 1,
                        "bbox": [round(b[0], 1), round(b[1], 1), round(b[2], 1), round(b[3], 1)],
                        "block_num": b[5],
                        "text": b[4].strip()
                    })

            # 3. Table extraction
            try:
                table_finder = page.find_tables()
                if table_finder and table_finder.tables:
                    for t_idx, table in enumerate(table_finder.tables):
                        extracted_tables.append({
                            "page": page_idx + 1,
                            "table_index": t_idx + 1,
                            "bbox": list(table.bbox),
                            "row_count": table.row_count,
                            "col_count": table.col_count,
                            "header": table.header.names if table.header else [],
                            "rows": table.extract()
                        })
            except Exception:
                pass

        doc.close()

        complete_text = "\n\n--- PAGE BREAK ---\n\n".join(full_text_pages)

        return {
            "pdf_path": pdf_path,
            "is_scanned": nature["is_scanned"],
            "classification": nature["classification"],
            "total_pages": nature["total_pages"],
            "total_chars": len(complete_text),
            "text": complete_text,
            "page_texts": full_text_pages,
            "blocks": structured_blocks,
            "tables": extracted_tables,
            "table_count": len(extracted_tables)
        }

    def render_page_to_image(self, pdf_path: str, page_num: int = 1, dpi: int = 200) -> str:
        """
        Renders a given page of a PDF to a PNG image for OCR processing.
        Returns the saved image path.
        """
        doc = pymupdf.open(pdf_path)
        if page_num < 1 or page_num > len(doc):
            raise ValueError(f"Page {page_num} out of range for doc with {len(doc)} pages.")

        page = doc[page_num - 1]
        pix = page.get_pixmap(dpi=dpi)
        
        output_dir = "outputs/rendered_pages"
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        out_path = os.path.join(output_dir, f"{base_name}_p{page_num}.png")
        pix.save(out_path)
        doc.close()
        return out_path


if __name__ == "__main__":
    parser = DocumentParser()

    print("\n--- Testing Digital vs Scanned Classification ---")
    test_files = [
        "data/data_sources/statutes/contract_act.pdf",
        "data/data_sources/contracts/synthetic/01_employment_agreement_lahore.pdf",
        "data/data_sources/scanned_urdu/01_kiraya_nama_lahore_scanned.pdf",
        "data/data_sources/judgments_sample/Justice Malik Shahzad Ahmad Khan/crl.a._23_q_2020.pdf"
    ]

    for tf in test_files:
        if os.path.exists(tf):
            res = parser.analyze_pdf_nature(tf)
            print(f"File: {os.path.basename(tf):<45} -> {res['classification']} (Avg Chars/Page: {res['avg_chars_per_page']})")

    print("\n--- Testing Table & Text Extraction ---")
    statute_sample = "data/data_sources/statutes/contract_act.pdf"
    if os.path.exists(statute_sample):
        parsed = parser.extract_text_and_tables(statute_sample)
        print(f"Extracted {parsed['total_chars']} chars, {len(parsed['blocks'])} text blocks, {parsed['table_count']} tables.")
