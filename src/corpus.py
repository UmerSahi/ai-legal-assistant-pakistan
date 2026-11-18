"""
Corpus Collection & Inventory Module
Task 1: AI Legal Assistant (Khan & Associates)
Audits, validates, and indexes all 290+ legal documents across Pakistani statutes,
Supreme Court judgments, CUAD & synthetic contracts, and scanned Urdu records.
"""

import os
import re
import json
import csv
from typing import List, Dict, Any
import pymupdf


class CorpusInventory:
    """Manages document inventory, metadata extraction, and collection audit."""

    def __init__(self, base_data_dir: str = "data/data_sources"):
        self.base_data_dir = base_data_dir

    @staticmethod
    def detect_language(text_sample: str, default_lang: str = "English") -> str:
        """Heuristic language detection based on Arabic/Urdu Unicode ranges."""
        if not text_sample or not text_sample.strip():
            return default_lang
        # Check for Arabic / Urdu Unicode blocks (\u0600-\u06FF, \u0750-\u077F, \uFB50-\uFDFF, \uFE70-\uFEFF)
        urdu_chars = len(re.findall(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]", text_sample))
        latin_chars = len(re.findall(r"[a-zA-Z]", text_sample))
        
        total = urdu_chars + latin_chars
        if total == 0:
            return default_lang
        if urdu_chars / total > 0.4 and latin_chars / total > 0.1:
            return "Bilingual"
        elif urdu_chars / total > 0.3:
            return "Urdu"
        else:
            return "English"

    def scan_documents(self) -> List[Dict[str, Any]]:
        """Scans the entire corpus directory and extracts structured document metadata."""
        records = []
        doc_counter = 1

        # Configuration mapping for directory scanning
        configs = [
            {
                "subpath": "statutes",
                "doc_type": "statute",
                "category": "Statute",
                "default_lang": "English",
                "source": "Pakistan Code / Ministry of Law & Justice",
                "recursive": False
            },
            {
                "subpath": "judgments_sample",
                "doc_type": "judgment",
                "category": "Judgment",
                "default_lang": "English",
                "source": "Supreme Court of Pakistan",
                "recursive": True
            },
            {
                "subpath": "contracts/cuad",
                "doc_type": "contract_cuad",
                "category": "Contract",
                "default_lang": "English",
                "source": "Atticus Project CUAD Dataset",
                "recursive": False
            },
            {
                "subpath": "contracts/synthetic",
                "doc_type": "contract_synthetic",
                "category": "Contract",
                "default_lang": "English",
                "source": "Khan & Associates Synthetic Generator",
                "recursive": False
            },
            {
                "subpath": "scanned_urdu",
                "doc_type": "scanned_urdu",
                "category": "Scanned/Urdu",
                "default_lang": "Urdu",
                "source": "Khan & Associates Litigation Records",
                "recursive": False
            }
        ]

        for cfg in configs:
            target_dir = os.path.join(self.base_data_dir, cfg["subpath"])
            if not os.path.exists(target_dir):
                continue

            if cfg["recursive"]:
                walker = os.walk(target_dir)
            else:
                files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]
                walker = [(target_dir, [], files)]

            for root, _, filenames in walker:
                for fname in sorted(filenames):
                    if not fname.lower().endswith(".pdf"):
                        continue

                    full_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(full_path, start=".")
                    file_size = os.path.getsize(full_path)

                    pages = 0
                    is_scanned = False
                    detected_lang = cfg["default_lang"]

                    try:
                        doc = pymupdf.open(full_path)
                        pages = len(doc)
                        total_text_len = 0
                        sample_text = ""
                        sample_pages = min(pages, 3)

                        for p_idx in range(sample_pages):
                            p_txt = doc[p_idx].get_text() or ""
                            total_text_len += len(p_txt.strip())
                            sample_text += " " + p_txt

                        doc.close()

                        # If text per page is negligible, it's a scanned document
                        avg_text = total_text_len / max(sample_pages, 1)
                        if avg_text < 60:
                            is_scanned = True

                        if not is_scanned and sample_text.strip():
                            detected_lang = self.detect_language(sample_text, cfg["default_lang"])
                        elif cfg["doc_type"] == "scanned_urdu":
                            detected_lang = "Urdu"
                            is_scanned = True

                    except Exception as e:
                        pages = 1
                        is_scanned = (cfg["doc_type"] == "scanned_urdu")

                    # Extra metadata: Justice name for judgments
                    extra_meta = {}
                    if cfg["doc_type"] == "judgment":
                        rel_sub = os.path.relpath(root, target_dir)
                        if rel_sub and rel_sub != ".":
                            extra_meta["author_justice"] = rel_sub

                    records.append({
                        "doc_id": f"DOC_{doc_counter:04d}",
                        "filename": fname,
                        "relative_path": rel_path.replace("\\", "/"),
                        "doc_type": cfg["doc_type"],
                        "category": cfg["category"],
                        "language": detected_lang,
                        "pages": pages,
                        "file_size_kb": round(file_size / 1024, 2),
                        "is_scanned": is_scanned,
                        "source": cfg["source"],
                        **extra_meta
                    })
                    doc_counter += 1

        return records

    def export_inventory(self, records: List[Dict[str, Any]], csv_path: str = "outputs/inventory.csv", json_path: str = "outputs/inventory.json") -> None:
        """Exports scanned records to CSV and JSON formats."""
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        os.makedirs(os.path.dirname(json_path), exist_ok=True)

        # JSON Export
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        # CSV Export
        if records:
            keys = ["doc_id", "filename", "doc_type", "category", "language", "pages", "file_size_kb", "is_scanned", "source", "author_justice", "relative_path"]
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
                writer.writeheader()
                for r in records:
                    writer.writerow(r)

    def generate_audit_summary(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validates all assignment collection requirements and produces audit statistics."""
        summary = {
            "total_documents": len(records),
            "total_pages": sum(r["pages"] for r in records),
            "by_type": {},
            "by_language": {},
            "by_scan_status": {"digital": 0, "scanned": 0},
            "requirements_audit": {}
        }

        for r in records:
            dt = r["doc_type"]
            summary["by_type"][dt] = summary["by_type"].get(dt, 0) + 1

            lang = r["language"]
            summary["by_language"][lang] = summary["by_language"].get(lang, 0) + 1

            if r["is_scanned"]:
                summary["by_scan_status"]["scanned"] += 1
            else:
                summary["by_scan_status"]["digital"] += 1

        # Check assignment targets:
        # Statutes >= 10
        # Judgments >= 200
        # Contracts >= 50 (CUAD + 20 synthetic)
        # Scanned/Urdu >= 30
        statutes_count = summary["by_type"].get("statute", 0)
        judgments_count = summary["by_type"].get("judgment", 0)
        cuad_count = summary["by_type"].get("contract_cuad", 0)
        synth_count = summary["by_type"].get("contract_synthetic", 0)
        contracts_total = cuad_count + synth_count
        scanned_count = summary["by_type"].get("scanned_urdu", 0)

        summary["requirements_audit"] = {
            "statutes": {"target": 10, "found": statutes_count, "satisfied": statutes_count >= 10},
            "judgments": {"target": 200, "found": judgments_count, "satisfied": judgments_count >= 200},
            "contracts_total": {"target": 50, "found": contracts_total, "satisfied": contracts_total >= 50},
            "contracts_cuad": {"target": 30, "found": cuad_count, "satisfied": cuad_count >= 30},
            "contracts_synthetic": {"target": 20, "found": synth_count, "satisfied": synth_count >= 20},
            "scanned_urdu": {"target": 30, "found": scanned_count, "satisfied": scanned_count >= 30},
            "all_satisfied": (
                statutes_count >= 10 and
                judgments_count >= 200 and
                contracts_total >= 50 and
                cuad_count >= 30 and
                synth_count >= 20 and
                scanned_count >= 30
            )
        }

        return summary


if __name__ == "__main__":
    inventory = CorpusInventory()
    docs = inventory.scan_documents()
    inventory.export_inventory(docs)
    summary = inventory.generate_audit_summary(docs)
    print("\n" + "="*60)
    print(" CORPUS COLLECTION AUDIT & INVENTORY SUMMARY")
    print("="*60)
    print(f"Total Documents: {summary['total_documents']}")
    print(f"Total Pages:     {summary['total_pages']}")
    print("\nBreakdown by Type:")
    for k, v in summary["by_type"].items():
        print(f"  - {k:<22}: {v}")
    print("\nBreakdown by Language:")
    for k, v in summary["by_language"].items():
        print(f"  - {k:<22}: {v}")
    print("\nFormat Classification:")
    for k, v in summary["by_scan_status"].items():
        print(f"  - {k:<22}: {v}")
    print("\nRequirements Audit:")
    for req, stat in summary["requirements_audit"].items():
        if req == "all_satisfied":
            continue
        status_flag = "PASS" if stat["satisfied"] else "FAIL"
        print(f"  [{status_flag}] {req:<20}: Found {stat['found']} / Target {stat['target']}")
    print(f"\nAll Targets Met: {summary['requirements_audit']['all_satisfied']}")
    print("="*60)
