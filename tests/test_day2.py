"""
Automated Unit Tests for Day 2: Advanced RAG & Citation-Grounded Legal Research
AI Legal Assistant (Khan & Associates)
"""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.eval_set import create_evaluation_dataset, save_evaluation_dataset
from src.advanced_rag import LegalQueryRewriter, LegalHyDE, AdvancedLegalRetriever
from src.citation_verifier import CitationVerifier
from src.answer_generator import LegalAnswerGenerator


def test_evaluation_dataset_structure():
    dataset = create_evaluation_dataset()
    assert len(dataset) == 100, f"Expected 100 questions, got {len(dataset)}"

    statute_count = sum(1 for q in dataset if q["category"] == "statute")
    caselaw_count = sum(1 for q in dataset if q["category"] == "case_law")
    unans_count = sum(1 for q in dataset if q["category"] == "unanswerable")

    assert statute_count == 50, f"Expected 50 statute questions, got {statute_count}"
    assert caselaw_count == 30, f"Expected 30 case law questions, got {caselaw_count}"
    assert unans_count == 20, f"Expected 20 unanswerable questions, got {unans_count}"

    for q in dataset:
        assert "id" in q
        assert "query" in q and len(q["query"]) > 5
        assert "category" in q
        assert "is_answerable" in q


def test_query_rewriter_bilingual():
    roman_urdu_q = "Agar consideration unlawful ho to kya contract void hai?"
    rewritten = LegalQueryRewriter.rewrite(roman_urdu_q)
    assert "section 23" in rewritten.lower() or "unlawful consideration" in rewritten.lower()
    assert "Contract Act" in rewritten or "agreement" in rewritten

    acronym_q = "What is the penalty for murder under PPC?"
    rewritten_acronym = LegalQueryRewriter.rewrite(acronym_q)
    assert "Pakistan Penal Code" in rewritten_acronym


def test_hyde_hypothetical_generation():
    query = "Agar consideration unlawful ho to kya contract void hai?"
    hyde_doc = LegalHyDE.generate_hypothetical_document(query)
    assert "SECTION 23" in hyde_doc
    assert "THE CONTRACT ACT" in hyde_doc
    assert "void" in hyde_doc.lower()


def test_answer_generator_scenario_query():
    generator = LegalAnswerGenerator()
    query = "Agar consideration unlawful ho to kya contract void hai?"
    ans = generator.generate_answer(query)

    assert ans["status"] == "answered"
    assert "void" in ans["short_answer"].lower()
    assert "Section 23" in ans["exact_citations"][0]["section_or_para"]
    assert ans["exact_citations"][0]["doc_id"] == "STAT_contract_act"
    assert len(ans["quoted_source_text"]) > 10

    # Verification must be 100% verified with 0 fabrication
    v = ans["verification"]
    assert v["fabrication_detected"] is False
    assert v["is_grounded"] is True
    assert v["status"] == "verified"


def test_answer_generator_unanswerable_query():
    generator = LegalAnswerGenerator()
    unans_query = "What is the patent subject matter eligibility standard under 35 U.S. Code § 101?"
    ans = generator.generate_answer(unans_query)

    assert ans["short_answer"] == "No sufficient source found"
    assert len(ans["exact_citations"]) == 0
    assert ans["quoted_source_text"] == ""

    v = ans["verification"]
    assert v["fabrication_detected"] is False
    assert v["status"] == "valid_unanswerable"


def test_citation_verifier_catches_fabrication():
    verifier = CitationVerifier()

    # Intentionally fabricated citation
    fabricated_answer = {
        "short_answer": "Under Section 9999 of the Pakistan Penal Code, 1860, theft has no punishment.",
        "explanation": "Fabricated text.",
        "exact_citations": [
            {
                "act_or_case": "The Pakistan Penal Code, 1860",
                "section_or_para": "Section 9999",
                "doc_id": "STAT_Penal_code_pakistan"
            }
        ],
        "quoted_source_text": "Whoever steals shall receive no punishment under Section 9999",
        "status": "answered"
    }

    result = verifier.verify_answer(fabricated_answer)
    assert result["fabrication_detected"] is True
    assert result["is_grounded"] is False
    assert result["status"] == "verification_failed"
