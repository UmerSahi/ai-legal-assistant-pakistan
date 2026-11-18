"""
Unit and Integration Tests for AI Legal Assistant Ingestion Pipeline
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.corpus import CorpusInventory
from src.parser import DocumentParser
from src.extractor import LegalStructureExtractor
from src.chunker import FixedSizeChunker, SectionLevelChunker, ParentChildChunker, ChunkingBenchmark, LegalChunk
from src.indexer import LegalIndexer


@pytest.fixture
def base_data_dir():
    return "data/data_sources"


def test_corpus_inventory_audit(base_data_dir):
    inventory = CorpusInventory(base_data_dir=base_data_dir)
    docs = inventory.scan_documents()
    assert len(docs) >= 290, f"Expected at least 290 documents, found {len(docs)}"

    summary = inventory.generate_audit_summary(docs)
    audit = summary["requirements_audit"]
    assert audit["statutes"]["satisfied"], f"Statutes requirement failed: {audit['statutes']}"
    assert audit["judgments"]["satisfied"], f"Judgments requirement failed: {audit['judgments']}"
    assert audit["contracts_total"]["satisfied"], f"Contracts requirement failed: {audit['contracts_total']}"
    assert audit["contracts_cuad"]["satisfied"], f"CUAD contracts requirement failed: {audit['contracts_cuad']}"
    assert audit["contracts_synthetic"]["satisfied"], f"Synthetic contracts requirement failed: {audit['contracts_synthetic']}"
    assert audit["scanned_urdu"]["satisfied"], f"Scanned Urdu requirement failed: {audit['scanned_urdu']}"
    assert audit["all_satisfied"] is True


def test_pdf_digital_vs_scanned_detection(base_data_dir):
    parser = DocumentParser()

    # Digital statute
    statute_path = os.path.join(base_data_dir, "statutes", "contract_act.pdf")
    if os.path.exists(statute_path):
        res = parser.analyze_pdf_nature(statute_path)
        assert res["is_scanned"] is False
        assert "Digital" in res["classification"]

    # Scanned Urdu document
    scanned_path = os.path.join(base_data_dir, "scanned_urdu", "01_kiraya_nama_lahore_scanned.pdf")
    if os.path.exists(scanned_path):
        res = parser.analyze_pdf_nature(scanned_path)
        assert res["is_scanned"] is True
        assert "Scanned" in res["classification"]


def test_statute_structure_extraction(base_data_dir):
    extractor = LegalStructureExtractor()
    statute_path = os.path.join(base_data_dir, "statutes", "contract_act.pdf")
    if os.path.exists(statute_path):
        data = extractor.extract_statute(statute_path)
        assert "act_title" in data
        assert "sections" in data
        assert len(data["sections"]) > 0
        assert data["document_type"] == "statute"


def test_judgment_structure_extraction(base_data_dir):
    extractor = LegalStructureExtractor()
    judg_path = os.path.join(base_data_dir, "judgments_sample", "Justice Aqeel Ahmed Abbasi", "c.a._470_2022.pdf")
    if os.path.exists(judg_path):
        data = extractor.extract_judgment(judg_path, author_justice="Justice Aqeel Ahmed Abbasi")
        assert "court" in data
        assert "case_number" in data
        assert "holding" in data
        assert "parties" in data


def test_contract_structure_extraction(base_data_dir):
    extractor = LegalStructureExtractor()
    cont_path = os.path.join(base_data_dir, "contracts", "synthetic", "01_employment_agreement_lahore.pdf")
    if os.path.exists(cont_path):
        data = extractor.extract_contract(cont_path, contract_subtype="synthetic")
        assert "title" in data
        assert "clauses" in data
        assert len(data["clauses"]) > 0
        assert "parties" in data


def test_chunking_strategies():
    statute_mock = {
        "doc_id": "TEST_STAT",
        "act_title": "Test Penal Code",
        "year": 1860,
        "sections": [
            {
                "section_number": "302",
                "section_title": "Punishment of qatl-i-amd",
                "section_text": "Whoever commits qatl-i-amd shall be punished with death, or imprisonment for life.",
                "subsections": ["(a) with death as qisas", "(b) with imprisonment for life"]
            }
        ]
    }

    # Section Chunker
    s_chunker = SectionLevelChunker()
    s_chunks = s_chunker.chunk_statute(statute_mock)
    assert len(s_chunks) == 1
    assert s_chunks[0].section == "302"
    assert s_chunks[0].chunk_type == "atomic"

    # Parent-Child Chunker
    pc_chunker = ParentChildChunker()
    parents, children = pc_chunker.chunk_statute(statute_mock)
    assert len(parents) == 1
    assert len(children) == 2
    assert children[0].parent_id == parents[0].chunk_id


def test_indexer_and_retrieval(tmp_path):
    chroma_dir = str(tmp_path / "chromadb")
    bm25_file = str(tmp_path / "bm25.pkl")

    indexer = LegalIndexer(
        chroma_persist_dir=chroma_dir,
        bm25_persist_path=bm25_file,
        collection_name="test_legal_collection"
    )

    chunks = [
        LegalChunk(
            chunk_id="TEST_SEC_302",
            doc_id="STAT_PPC",
            text="Section 302: Punishment of murder and qatl-i-amd with capital death sentence.",
            strategy="section_level",
            doc_type="statute",
            act="Pakistan Penal Code",
            section="302",
            year=1860
        ),
        LegalChunk(
            chunk_id="TEST_SEC_97",
            doc_id="STAT_CPC",
            text="Section 97: Appeal from preliminary decree in civil court suits.",
            strategy="section_level",
            doc_type="statute",
            act="Code of Civil Procedure",
            section="97",
            year=1908
        ),
        LegalChunk(
            chunk_id="TEST_CONT_LEASE",
            doc_id="CONT_LEASE",
            text="Clause 4: Commercial lease monthly rent and security deposit payment terms.",
            strategy="section_level",
            doc_type="contract",
            act="Commercial Lease Deed",
            section="4",
            year=2024
        ),
        LegalChunk(
            chunk_id="TEST_JUDG_BAIL",
            doc_id="JUDG_BAIL",
            text="High Court Order: Grant of pre-arrest protective bail in criminal proceedings.",
            strategy="section_level",
            doc_type="judgment",
            court="Supreme Court of Pakistan",
            year=2023
        )
    ]

    res = indexer.index_chunks(chunks)
    assert res["status"] == "success"

    # Vector search
    v_res = indexer.search_vector("death penalty murder", top_k=1)
    assert len(v_res) == 1
    assert v_res[0]["chunk_id"] == "TEST_SEC_302"

    # BM25 search
    b_res = indexer.search_bm25("preliminary decree section 97", top_k=1)
    assert len(b_res) == 1
    assert b_res[0]["chunk_id"] == "TEST_SEC_97"

    # Hybrid RRF search
    h_res = indexer.search_hybrid("preliminary decree appeal", top_k=1)
    assert len(h_res) == 1
    assert h_res[0]["chunk_id"] == "TEST_SEC_97"
