"""
AI Legal Assistant - Command Line Interface (CLI)
Task 1-5 Deliverable: Khan & Associates
"""

import sys
import argparse
from src.pipeline import LegalIngestionPipeline
from src.ocr_benchmark import UrduOCRBenchmark


def parse_args():
    parser = argparse.ArgumentParser(
        description="Khan & Associates AI Legal Assistant: Document Ingestion & Understanding Engine"
    )
    parser.add_argument(
        "--step",
        choices=["all", "inventory", "parse", "ocr", "extract", "chunk", "index", "search"],
        default="all",
        help="Specify the pipeline step to execute (default: all)"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="punishment for murder qatl-i-amd",
        help="Query to search when --step search is selected"
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
    pipeline = LegalIngestionPipeline(data_dir=args.data_dir, output_dir=args.output_dir)

    print("\n" + "#"*70)
    print(" KHAN & ASSOCIATES - AI LEGAL ASSISTANT PIPELINE")
    print(" Day 1: Legal Document Ingestion & Understanding Engine")
    print("#"*70)

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
