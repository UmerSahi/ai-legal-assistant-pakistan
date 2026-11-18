"""
AI Legal Assistant - Command Line Interface (CLI)
Khan & Associates - Day 1 & Day 2 Deliverables
"""

import sys
import argparse
from src.pipeline import LegalIngestionPipeline
from src.ocr_benchmark import UrduOCRBenchmark


def parse_args():
    parser = argparse.ArgumentParser(
        description="Khan & Associates AI Legal Assistant: Ingestion, Advanced RAG & Citation Grounding"
    )
    parser.add_argument(
        "--step",
        choices=["all", "inventory", "parse", "ocr", "extract", "chunk", "index", "search", "day2_eval", "answer"],
        default="all",
        help="Specify the pipeline step to execute (default: all)"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="Agar consideration unlawful ho to kya contract void hai?",
        help="Query to search or answer when --step search or --step answer is selected"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/data_sources",
        help="Base directory containing legal documents"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Output directory for structured data, reports, and indices"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("\n" + "#"*70)
    print(" KHAN & ASSOCIATES - AI LEGAL ASSISTANT PLATFORM")
    print(" Day 1: Document Ingestion | Day 2: Advanced Grounded RAG")
    print("#"*70)

    if args.step == "day2_eval":
        from src.advanced_rag import AdvancedLegalRAG
        print("\n[CLI] Running Day 2 Advanced RAG Ablation Benchmark on 100 questions...")
        rag = AdvancedLegalRAG(output_dir=args.output_dir)
        results = rag.run_ablation_benchmark()
        rag.export_ablation_report(results)
        return

    if args.step == "answer":
        from src.answer_generator import LegalAnswerGenerator
        print(f"\n[CLI] Generating Citation-Grounded Answer for:\n>>> {args.query}\n")
        gen = LegalAnswerGenerator()
        ans = gen.generate_answer(args.query)
        print("="*60)
        print(f"SHORT ANSWER: {ans['short_answer']}")
        print(f"\nEXPLANATION: {ans['explanation']}")
        print("\nEXACT CITATIONS:")
        for c in ans.get("exact_citations", []):
            print(f"  - {c.get('act_or_case', '')} -> {c.get('section_or_para', '')} ({c.get('doc_id', '')})")
        print("\nQUOTED SOURCE TEXT:")
        quote_text = ans.get("quoted_source_text", "")
        if quote_text:
            print(f"  > \"{quote_text}\"")
        else:
            print("  (None)")
        print("\nVERIFICATION STATUS:")
        v = ans.get("verification", {})
        print(f"  - Status: {v.get('status', 'unknown')}")
        print(f"  - Is Grounded: {v.get('is_grounded', False)}")
        print(f"  - Fabrication Detected: {v.get('fabrication_detected', False)}")
        print(f"  - Quote Matched: {v.get('quote_match', False)}")
        print(f"  - Summary: {v.get('summary', '')}")
        print("="*60)
        return

    pipeline = LegalIngestionPipeline(data_dir=args.data_dir, output_dir=args.output_dir)

    if args.step in ["all", "inventory"]:
        pipeline.run_inventory_step()

    if args.step in ["all", "parse"]:
        pipeline.run_parsing_step()

    if args.step == "ocr":
        print("\n[CLI] Running dedicated Urdu OCR Benchmark on 10 legal pages...")
        bench = UrduOCRBenchmark()
        results = bench.run_benchmark()
        bench.export_results(results)

    if args.step in ["all", "extract"]:
        pipeline.run_extraction_step()

    if args.step in ["all", "chunk"]:
        chunks = pipeline.run_chunking_step()

    if args.step in ["all", "index"]:
        if "chunks" not in locals():
            chunks = pipeline.run_chunking_step()
        pipeline.run_indexing_step(chunks)

    if args.step == "search":
        print(f"\n[CLI] Searching legal index for query: '{args.query}'")
        results = pipeline.indexer.search_hybrid(args.query, top_k=5)
        print("\nSearch Results (Reciprocal Rank Fusion Hybrid):")
        for i, r in enumerate(results, 1):
            act_sec = f"{r['metadata'].get('act', '')} § {r['metadata'].get('section', '')}".strip()
            print(f" {i}. [{r['rrf_score']:.4f}] {r['chunk_id']} | {act_sec}")
            print(f"    Text: {r['text'][:150]}...\n")

    print("\n" + "#"*70)
    print(" PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print(f" Artifacts, structured JSONs, and indices available in: {args.output_dir}/")
    print("#"*70 + "\n")


if __name__ == "__main__":
    main()
