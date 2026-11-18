"""
AI Legal Assistant - Command Line Interface (CLI)
Khan & Associates - Day 1, Day 2 & Day 3 Deliverables
"""

import sys
import argparse
from src.pipeline import LegalIngestionPipeline
from src.ocr_benchmark import UrduOCRBenchmark


def parse_args():
    parser = argparse.ArgumentParser(
        description="Khan & Associates AI Legal Assistant: Ingestion, Advanced RAG, and Knowledge GraphRAG"
    )
    parser.add_argument(
        "--step",
        choices=[
            "all", "inventory", "parse", "ocr", "extract", "chunk", "index", "search",
            "day2_eval", "answer",
            "graph", "graph_eval", "graphrag", "multihop_eval", "route"
        ],
        default="all",
        help="Specify the pipeline step to execute (default: all)"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="Which Supreme Court judgments interpreted Section 23 of the Contract Act, and were any of them later overruled?",
        help="Query to search, answer, or route"
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
    print(" Day 1: Document Ingestion | Day 2: Grounded RAG | Day 3: Knowledge GraphRAG")
    print("#"*70)

    # -----------------------------------------------------------------
    # Day 3: Knowledge Graph & GraphRAG Steps
    # -----------------------------------------------------------------
    if args.step == "graph":
        from src.graph_extractor import LegalGraphExtractor
        from src.neo4j_graph import LegalNeo4jGraph
        print("\n[CLI] Extracting Legal Knowledge Graph from structured corpus...")
        extractor = LegalGraphExtractor(structured_dir=f"{args.output_dir}/structured")
        graph = LegalNeo4jGraph(output_dir=args.output_dir)
        graph.load_from_extractor(extractor)
        print("\n[CLI] Graph Knowledge Base Successfully Built & Exported:")
        print(f"  - Cypher DDL Script: {args.output_dir}/neo4j_export.cypher")
        print(f"  - Interactive PyVis Visualization: {args.output_dir}/graph_visualization.html")
        return

    if args.step == "graph_eval":
        from src.graph_extractor import evaluate_extraction_on_20_judgments
        print("\n[CLI] Running Entity and Relationship Extraction Evaluation on 20 Judgments...")
        evaluate_extraction_on_20_judgments(
            structured_dir=f"{args.output_dir}/structured/judgments",
            output_dir=args.output_dir
        )
        return

    if args.step == "graphrag":
        from src.graph_rag import LegalGraphRAG
        print(f"\n[CLI] Executing Legal GraphRAG for:\n>>> {args.query}\n")
        grag = LegalGraphRAG()
        ans = grag.answer_question(args.query)
        print("="*65)
        print(f"INTENT: {ans.get('intent', 'general')}")
        print(f"\nGENERATED CYPHER QUERY:\n{ans.get('cypher_query')}")
        print(f"\nSHORT ANSWER:\n{ans.get('short_answer')}")
        print(f"\nEXPLANATION:\n{ans.get('explanation')}")
        print("\nRELATIONAL FACTS TRAVERSED:")
        for fact in ans.get("relational_facts", []):
            print(f"  - {fact}")
        warnings = ans.get("overruled_warnings", [])
        if warnings:
            print("\nCRITICAL OVERRULED / BAD LAW WARNINGS:")
            for w in warnings:
                print(f"  [!] {w.get('warning')}")
        else:
            print("\nCITATION SAFETY: 100% Good Law (No Overruled Cases Found)")
        print("="*65)
        return

    if args.step == "multihop_eval":
        from src.rag_router import MultiHopRAGEvaluator
        print("\n[CLI] Running 30-Question Multi-Hop Benchmark (Vector vs Graph vs Hybrid)...")
        evaluator = MultiHopRAGEvaluator(output_dir=args.output_dir)
        res = evaluator.run_comparison_benchmark()
        print("\nBenchmark Summary Results:")
        for eng, m in res["aggregate_metrics"].items():
            print(f"  [{eng}] Completeness: {m['completeness']}% | Precision: {m['path_precision']}% | Bad Law Rate: {m['bad_law_rate']}% | Latency: {m['latency_ms']}ms")
        return

    if args.step == "route":
        from src.rag_router import LegalQueryRouter
        print(f"\n[CLI] Routing Legal Query:\n>>> {args.query}\n")
        decision = LegalQueryRouter.route_query(args.query)
        print("="*65)
        print(f"RECOMMENDED ENGINE: {decision['selected_engine']} (Confidence: {decision['confidence']})")
        print(f"REASONING: {decision['reasoning']}")
        print(f"FEATURE SCORES: {decision['feature_scores']}")
        print("="*65)
        return

    # -----------------------------------------------------------------
    # Day 2: Advanced RAG Steps
    # -----------------------------------------------------------------
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

    # -----------------------------------------------------------------
    # Day 1: Document Ingestion Steps
    # -----------------------------------------------------------------
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
