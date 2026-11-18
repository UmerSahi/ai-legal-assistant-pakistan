"""
Automated Test Suite for Day 4: Contract Review, Comparison & Drafting Agents
Khan & Associates AI Legal Assistant
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.clause_classifier import CUADClauseClassifier, run_clause_classification_benchmark
from src.playbook_reviewer import FirmPlaybookReviewer
from src.contract_comparator import ContractComparator, create_sample_contracts_pair
from src.drafting_agent import LegalDraftingAgent
from src.long_context_vs_rag import LongContextVsRAGBenchmark


def test_cuad_clause_classification():
    """Validates clause classification across core CUAD categories."""
    # Test Governing Law
    cat1 = CUADClauseClassifier.classify_llm("This agreement shall be governed by laws of Pakistan.", heading="Governing Law")
    assert cat1 == "Governing Law"

    # Test Dispute Resolution
    cat2 = CUADClauseClassifier.classify_llm("All disputes shall be referred to arbitration in Lahore under Arbitration Act 1940.", heading="Arbitration")
    assert cat2 == "Dispute Resolution / Arbitration"

    # Test Termination
    cat3 = CUADClauseClassifier.classify_llm("Either party may terminate upon 30 days written notice.", heading="Termination")
    assert cat3 == "Termination / Termination for Convenience"

    # Test Classification Benchmark
    bench_res = run_clause_classification_benchmark()
    assert bench_res["total_clauses_evaluated"] >= 10
    assert bench_res["macro_llm_f1"] > 50.0
    assert bench_res["macro_bert_f1"] > 40.0


def test_playbook_clause_evaluation():
    """Validates firm playbook risk badges: PASS, WARN, and FAIL."""
    # 1. Compliant Pakistani governing law -> PASS
    res1 = FirmPlaybookReviewer.evaluate_clause(
        category="Governing Law",
        text="This Agreement shall be governed by the laws of Pakistan and the courts of Lahore.",
        heading="Governing Law"
    )
    assert res1["status"] == "PASS"
    assert res1["penalty"] == 0

    # 2. Foreign English governing law -> FAIL (Unacceptable)
    res2 = FirmPlaybookReviewer.evaluate_clause(
        category="Governing Law",
        text="This Agreement shall be governed by the laws of England and Wales and London courts.",
        heading="Governing Law"
    )
    assert res2["status"] == "FAIL"
    assert res2["penalty"] > 0
    assert "suggested_wording" in res2 and len(res2["suggested_wording"]) > 10

    # 3. Post-termination non-compete (Void under Section 27 Contract Act) -> FAIL
    res3 = FirmPlaybookReviewer.evaluate_clause(
        category="Non-Compete / Restrictive Covenants",
        text="Employee shall not engage in competing business for 2 years post-employment.",
        heading="Non-Compete"
    )
    assert res3["status"] == "FAIL"
    assert "Section 27" in res3["finding"]

    # 4. Immediate termination without cause -> WARN
    res4 = FirmPlaybookReviewer.evaluate_clause(
        category="Termination",
        text="Company may terminate this agreement immediately without cause.",
        heading="Termination"
    )
    assert res4["status"] == "WARN"


def test_playbook_contract_review_and_missing_clauses():
    """Validates full contract review and missing mandatory clause detection."""
    sample_path = "outputs/structured/contracts/CONT_01_employment_agreement_lahore.json"
    assert os.path.exists(sample_path)

    reviewer = FirmPlaybookReviewer()
    review = reviewer.review_contract(sample_path)

    assert "risk_score" in review
    assert 0 <= review["risk_score"] <= 100
    assert "clause_counts" in review
    assert len(review["clause_reviews"]) > 0
    assert isinstance(review["missing_clauses"], list)


def test_word_docx_report_generation(tmp_path):
    """Validates generation of styled Microsoft Word (.docx) review report."""
    sample_path = "outputs/structured/contracts/CONT_01_employment_agreement_lahore.json"
    reviewer = FirmPlaybookReviewer()
    review = reviewer.review_contract(sample_path)

    out_docx = str(tmp_path / "test_report.docx")
    saved_path = reviewer.export_word_report(review, out_docx)

    assert os.path.exists(saved_path)
    assert os.path.getsize(saved_path) > 5000  # valid Word file with content


def test_contract_comparison_diff_and_impact():
    """Validates contract redline diffing and plain-language legal impact analysis."""
    v1, v2 = create_sample_contracts_pair()
    comparator = ContractComparator()
    diff_data = comparator.compare_contracts(v1, v2)

    assert diff_data["total_clauses_reviewed"] == 5
    assert diff_data["modified_clauses_count"] >= 2
    assert diff_data["added_clauses_count"] >= 1
    assert diff_data["high_risk_changes_count"] >= 2

    # Verify plain-language impact for liability cap removal
    mod_items = [d for d in diff_data["clause_comparisons"] if d["change_type"] == "MODIFIED"]
    assert any("liability" in d["impact"].lower() or "damages" in d["impact"].lower() for d in mod_items)


def test_drafting_agent_outputs_and_watermark():
    """Validates drafting agent generates all 3 documents with the mandatory watermark."""
    agent = LegalDraftingAgent()
    drafts = agent.generate_all_drafts()

    for doc_type, file_path in drafts.items():
        assert os.path.exists(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Mandatory watermark requirement
            assert "DRAFT — for lawyer review" in content
            assert len(content) > 500


def test_long_context_vs_rag_benchmark():
    """Validates Long-Context vs RAG benchmark execution across 10 contracts."""
    bench = LongContextVsRAGBenchmark()
    summary = bench.run_benchmark()

    assert summary["contracts_evaluated"] == 10
    assert summary["rag_mean_accuracy"] > summary["long_context_mean_accuracy"]
    assert summary["rag_total_missed"] < summary["long_context_total_missed"]
    assert summary["cost_reduction_factor"] >= 1.0
    assert summary["speedup_factor"] > 1.0
