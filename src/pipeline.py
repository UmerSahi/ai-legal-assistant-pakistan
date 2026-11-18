"""
End-to-End Ingestion & Processing Pipeline
Task 1-5: AI Legal Assistant (Khan & Associates)
Orchestrates:
1. Corpus Collection & Inventory Audit
2. PDF Parsing, Digital vs Scanned Classification & Table Extraction
3. Urdu OCR Benchmarking (CER/WER evaluation)
4. Domain Structure Extraction into JSON
5. Legal-Aware Chunking (Fixed, Section, Parent-Child)
6. Dual Vector DB (ChromaDB) + BM25 Indexing & Hybrid Retrieval
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any

from src.corpus import CorpusInventory
from src.parser import DocumentParser
from src.extractor import LegalStructureExtractor
from src.chunker import FixedSizeChunker, SectionLevelChunker, ParentChildChunker, ChunkingBenchmark, LegalChunk
from src.indexer import LegalIndexer


class LegalIngestionPipeline:
    """Master pipeline orchestrator for Khan & Associates AI Legal Assistant."""

    def __init__(self, data_dir: str = "data/data_sources", output_dir: str = "outputs"):
        self.data_dir = data_dir
        self.output_dir = output_dir

        self.inventory_manager = CorpusInventory(base_data_dir=data_dir)
        self.parser = DocumentParser()
        self.extractor = LegalStructureExtractor(parser=self.parser)
        self.indexer = LegalIndexer(
            chroma_persist_dir=os.path.join(output_dir, "indices", "chromadb"),
            bm25_persist_path=os.path.join(output_dir, "indices", "bm25_index.pkl")
        )

    # -------------------------------------------------------------------------
    # STEP 1: Corpus Collection & Inventory
    # -------------------------------------------------------------------------
    def run_inventory_step(self) -> Dict[str, Any]:
        print("\n" + "="*70)
        print(" [TASK 1] CORPUS COLLECTION & INVENTORY AUDIT")
        print("="*70)
        docs = self.inventory_manager.scan_documents()
        csv_path = os.path.join(self.output_dir, "inventory.csv")
        json_path = os.path.join(self.output_dir, "inventory.json")
        self.inventory_manager.export_inventory(docs, csv_path=csv_path, json_path=json_path)
        summary = self.inventory_manager.generate_audit_summary(docs)

        print(f"Total Legal Documents Audited: {summary['total_documents']}")
        print(f"Total Pages Across Corpus:     {summary['total_pages']}")
        print("Category Breakdown:")
        for k, v in summary["by_type"].items():
            print(f"  * {k:<22}: {v}")
        print("Requirements Compliance:")
        for req, stat in summary["requirements_audit"].items():
            if req == "all_satisfied":
                continue
            mark = "PASS" if stat["satisfied"] else "FAIL"
            print(f"  [{mark}] {req:<20}: Found {stat['found']} / Target {stat['target']}")
        print(f"All Ingestion Requirements Met: {summary['requirements_audit']['all_satisfied']}")
        return summary

    # -------------------------------------------------------------------------
    # STEP 2: Parsing & Document Nature Analysis
    # -------------------------------------------------------------------------
    def run_parsing_step(self, sample_limit: int = 5) -> Dict[str, Any]:
        print("\n" + "="*70)
        print(" [TASK 2A] DIGITAL VS SCANNED PARSING & TABLE EXTRACTION")
        print("="*70)
        sample_files = [
            "statutes/contract_act.pdf",
            "statutes/anti-money-laundering.pdf",
            "contracts/synthetic/01_employment_agreement_lahore.pdf",
            "scanned_urdu/01_kiraya_nama_lahore_scanned.pdf",
            "scanned_urdu/02_fir_report_karachi_scanned.pdf"
        ]

        parsing_results = []
        for sf in sample_files:
            full_path = os.path.join(self.data_dir, sf)
            if not os.path.exists(full_path):
                continue
            res = self.parser.analyze_pdf_nature(full_path)
            tables_res = self.parser.extract_text_and_tables(full_path)
            print(f"Document: {os.path.basename(sf):<42} -> {res['classification']} | Avg Chars: {res['avg_chars_per_page']} | Tables: {tables_res['table_count']}")
            parsing_results.append({
                "file": sf,
                "classification": res["classification"],
                "avg_chars": res["avg_chars_per_page"],
                "tables": tables_res["table_count"]
            })
        return {"parsed_samples": parsing_results}

    # -------------------------------------------------------------------------
    # STEP 3: Legal Structure Extraction
    # -------------------------------------------------------------------------
    def run_extraction_step(self) -> Dict[str, Any]:
        print("\n" + "="*70)
        print(" [TASK 3] DOMAIN-SPECIFIC LEGAL STRUCTURE EXTRACTION TO JSON")
        print("="*70)
        structured_counts = {"statutes": 0, "judgments": 0, "contracts": 0, "scanned_urdu": 0}

        # 1. Statutes
        statutes_dir = os.path.join(self.data_dir, "statutes")
        if os.path.exists(statutes_dir):
            for fname in sorted(os.listdir(statutes_dir)):
                if fname.endswith(".pdf"):
                    p = os.path.join(statutes_dir, fname)
                    data = self.extractor.extract_statute(p)
                    out_path = os.path.join(self.output_dir, "structured", "statutes", f"{data['doc_id']}.json")
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    structured_counts["statutes"] += 1
            print(f"[Extractor] Extracted and saved {structured_counts['statutes']} Pakistani statutes to JSON.")

        # 2. Judgments (Representative cross-bench extraction)
        judg_dir = os.path.join(self.data_dir, "judgments_sample")
        if os.path.exists(judg_dir):
            for root, _, files in os.walk(judg_dir):
                for fname in sorted(files):
                    if fname.endswith(".pdf"):
                        p = os.path.join(root, fname)
                        author = os.path.basename(root)
                        data = self.extractor.extract_judgment(p, author_justice=author)
                        out_path = os.path.join(self.output_dir, "structured", "judgments", f"{data['doc_id']}.json")
                        with open(out_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        structured_counts["judgments"] += 1
                        if structured_counts["judgments"] >= 25: # Sample batch for rapid structural index
                            break
                if structured_counts["judgments"] >= 25:
                    break
            print(f"[Extractor] Extracted and saved {structured_counts['judgments']} Supreme Court judgments to JSON.")

        # 3. Contracts (CUAD + Synthetic)
        for sub in ["contracts/synthetic", "contracts/cuad"]:
            cdir = os.path.join(self.data_dir, sub)
            if os.path.exists(cdir):
                for fname in sorted(os.listdir(cdir)):
                    if fname.lower().endswith(".pdf"):
                        p = os.path.join(cdir, fname)
                        data = self.extractor.extract_contract(p, contract_subtype=sub)
                        out_path = os.path.join(self.output_dir, "structured", "contracts", f"{data['doc_id']}.json")
                        with open(out_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        structured_counts["contracts"] += 1
            print(f"[Extractor] Extracted and saved {structured_counts['contracts']} commercial contracts to JSON.")

        # 4. Scanned Urdu Documents
        urdu_dir = os.path.join(self.data_dir, "scanned_urdu")
        if os.path.exists(urdu_dir):
            for fname in sorted(os.listdir(urdu_dir)):
                if fname.endswith(".pdf"):
                    p = os.path.join(urdu_dir, fname)
                    data = self.extractor.extract_scanned_urdu(p)
                    out_path = os.path.join(self.output_dir, "structured", "scanned_urdu", f"{data['doc_id']}.json")
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    structured_counts["scanned_urdu"] += 1
            print(f"[Extractor] Extracted and saved {structured_counts['scanned_urdu']} scanned Urdu records to JSON.")

        return structured_counts

    # -------------------------------------------------------------------------
    # STEP 4: Legal-Aware Chunking & Comparison
    # -------------------------------------------------------------------------
    def run_chunking_step(self) -> List[LegalChunk]:
        print("\n" + "="*70)
        print(" [TASK 4] LEGAL-AWARE CHUNKING BENCHMARK & COMPARISON")
        print("="*70)
        benchmark = ChunkingBenchmark()
        section_chunker = SectionLevelChunker()
        pc_chunker = ParentChildChunker()

        # Load extracted sample data
        stat_path = os.path.join(self.output_dir, "structured", "statutes")
        cont_path = os.path.join(self.output_dir, "structured", "contracts")
        judg_path = os.path.join(self.output_dir, "structured", "judgments")

        sample_stat = {}
        sample_cont = {}
        sample_judg = {}

        if os.path.exists(stat_path) and os.listdir(stat_path):
            with open(os.path.join(stat_path, os.listdir(stat_path)[0]), "r", encoding="utf-8") as f:
                sample_stat = json.load(f)
        if os.path.exists(cont_path) and os.listdir(cont_path):
            with open(os.path.join(cont_path, os.listdir(cont_path)[0]), "r", encoding="utf-8") as f:
                sample_cont = json.load(f)
        if os.path.exists(judg_path) and os.listdir(judg_path):
            with open(os.path.join(judg_path, os.listdir(judg_path)[0]), "r", encoding="utf-8") as f:
                sample_judg = json.load(f)

        raw_sample_text = (
            "Section 1. Short title, extent and commencement. This Act may be called the Contract Act, 1872. "
            "It extends to the whole of Pakistan; and it shall come into force on the first day of September, 1872. "
            "Section 2. In this Act the following words and expressions are used in the following senses, unless a contrary intention appears: "
            "(a) When one person signifies to another his willingness to do or to abstain from doing anything, with a view to obtaining the assent of that other to such act or abstinence, he is said to make a proposal. "
            "(b) When the person to whom the proposal is made signifies his assent thereto, the proposal is said to be accepted. A proposal, when accepted, becomes a promise. "
            "Clause 5. Indemnification. The Tenant covenants to indemnify Khan & Associates against all losses, damages, liabilities, costs, charges, and expenses resulting from any breach of this lease deed. "
            "IN THE SUPREME COURT OF PAKISTAN. Civil Appeal No. 470 of 2022. Having heard the learned ASC for the appellant and DPG for the State, we are of the considered opinion that the prosecution has proved the guilt of the accused beyond any shadow of reasonable doubt. Appeal dismissed."
        ) * 15

        metrics = benchmark.run_comparison(sample_stat, sample_cont, sample_judg, raw_sample_text)
        benchmark.export_comparison(metrics)

        print("\nChunking Strategy Comparison Summary:")
        for m in metrics:
            print(f"  * {m['strategy']:<40} | Chunks: {m['total_chunks']:<3} | Avg Len: {m['mean_char_length']:<5} | Boundary: {m['boundary_integrity_pct']}% | Meta: {m['metadata_richness_pct']}%")

        # Collect full production chunks for indexing
        all_chunks = []

        # 1. Chunks from Statutes
        if os.path.exists(stat_path):
            for jf in sorted(os.listdir(stat_path)):
                with open(os.path.join(stat_path, jf), "r", encoding="utf-8") as f:
                    s_data = json.load(f)
                all_chunks.extend(section_chunker.chunk_statute(s_data))

        # 2. Chunks from Contracts
        if os.path.exists(cont_path):
            for jf in sorted(os.listdir(cont_path)):
                with open(os.path.join(cont_path, jf), "r", encoding="utf-8") as f:
                    c_data = json.load(f)
                all_chunks.extend(section_chunker.chunk_contract(c_data))

        # 3. Chunks from Judgments
        if os.path.exists(judg_path):
            for jf in sorted(os.listdir(judg_path)):
                with open(os.path.join(judg_path, jf), "r", encoding="utf-8") as f:
                    j_data = json.load(f)
                all_chunks.extend(section_chunker.chunk_judgment(j_data))

        print(f"[Chunker] Prepared {len(all_chunks)} legal-aware production chunks with domain metadata.")
        return all_chunks

    # -------------------------------------------------------------------------
    # STEP 5: Vector DB & BM25 Indexing + Retrieval Demo
    # -------------------------------------------------------------------------
    def run_indexing_step(self, chunks: List[LegalChunk]) -> Dict[str, Any]:
        print("\n" + "="*70)
        print(" [TASK 5] DUAL VECTOR DB (CHROMADB) & BM25 DUAL INDEXING")
        print("="*70)
        res = self.indexer.index_chunks(chunks)
        print(f"Indexing Complete! Indexed {res['indexed_count']} chunks into ChromaDB & BM25.")

        print("\n--- Demonstration Retrieval across Legal Corpus ---")
        demo_queries = [
            ("murder penalty qatl-i-amd life imprisonment", "Statutory Penal Provision"),
            ("appeal preliminary decree disputing correctness", "Civil Procedure Code CPC"),
            ("tenant indemnity hold harmless damages", "Commercial Contract Risk"),
            ("cancellation of bail criminal procedure", "Supreme Court Jurisprudence")
        ]

        retrieval_log = []
        for q, label in demo_queries:
            print(f"\n[Query: '{q}'] ({label})")
            hybrid_results = self.indexer.search_hybrid(q, top_k=2)
            for r in hybrid_results:
                act_sec = f"{r['metadata'].get('act', '')} § {r['metadata'].get('section', '')}".strip()
                print(f"  -> [RRF: {r['rrf_score']:.4f}] {r['chunk_id']} | {act_sec} | {r['text'][:90]}...")
            retrieval_log.append({"query": q, "label": label, "results": hybrid_results})

        return {"index_status": res, "demo_retrievals": retrieval_log}


if __name__ == "__main__":
    pipeline = LegalIngestionPipeline()
    print("AI Legal Assistant Ingestion Pipeline initialized.")
