"""
Automated Test Suite for Day 3: Legal Knowledge Graph & GraphRAG
Khan & Associates AI Legal Assistant
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.graph_schema import LegalGraphSchema
from src.graph_extractor import LegalGraphExtractor, EntityResolver, evaluate_extraction_on_20_judgments
from src.neo4j_graph import LegalNeo4jGraph
from src.graph_rag import LegalGraphRAG, TextToCypherTranslator
from src.rag_router import LegalQueryRouter, get_30_multihop_questions


def test_graph_schema_definition():
    """Validates schema node types, relationships, and Mermaid diagram generation."""
    nodes = LegalGraphSchema.NODES
    assert "Act" in nodes
    assert "Section" in nodes
    assert "Case" in nodes
    assert "Court" in nodes
    assert "Judge" in nodes
    assert "Party" in nodes
    assert "Contract" in nodes
    assert "Clause" in nodes

    rel_names = [r.name for r in LegalGraphSchema.RELATIONSHIPS]
    for expected_rel in ["CITES", "INTERPRETS", "OVERRULES", "FOLLOWS", "DECIDED_BY", "PRESIDED_BY", "CONTAINS_SECTION"]:
        assert expected_rel in rel_names

    mermaid = LegalGraphSchema.get_mermaid_diagram()
    assert "classDiagram" in mermaid
    assert "CONTAINS_SECTION" in mermaid
    assert "OVERRULES" in mermaid


def test_entity_resolution():
    """Validates normalization of informal legal entity mentions to canonical forms."""
    # Test Acts
    act1 = EntityResolver.resolve_act("the contract act, 1872")
    assert act1["act_id"] == "ACT_contract_act_1872"
    assert "Contract Act" in act1["title"]

    act2 = EntityResolver.resolve_act("Pakistan Penal Code (PPC)")
    assert act2["act_id"] == "ACT_pakistan_penal_code_1860"

    # Test Courts
    court1 = EntityResolver.resolve_court("Apex Court")
    assert court1["court_id"] == "COURT_sc_pakistan"

    # Test Judges
    judge1 = EntityResolver.resolve_judge("MR. JUSTICE UMAR ATA BANDIAL, HCJ")
    assert judge1["name"] == "Justice Umar Ata Bandial"

    judge2 = EntityResolver.resolve_judge("Mrs. Justice Ayesha A. Malik")
    assert judge2["name"] == "Justice Ayesha A. Malik"

    # Test Sections
    sec = EntityResolver.resolve_section("Section 23", "ACT_contract_act_1872")
    assert sec["section_id"] == "SEC_contract_act_1872_23"
    assert sec["number"] == "23"


def test_graph_extraction_performance():
    """Validates extraction across the corpus and precision/recall evaluation on 20 judgments."""
    extractor = LegalGraphExtractor()
    corpus_graph = extractor.extract_full_corpus()

    assert corpus_graph["relationship_count"] > 1000
    assert len(corpus_graph["nodes"]["Case"]) >= 25
    assert len(corpus_graph["nodes"]["Section"]) >= 100
    assert len(corpus_graph["nodes"]["Judge"]) >= 5

    # Run evaluation
    eval_res = evaluate_extraction_on_20_judgments()
    assert eval_res["benchmark_judgments_evaluated"] == 20
    assert eval_res["entity_f1"] > 70.0
    assert eval_res["relation_f1"] > 70.0


def test_neo4j_graph_pagerank_and_overruling():
    """Validates in-memory graph loading, PageRank calculation, and overruled case detection."""
    extractor = LegalGraphExtractor()
    graph = LegalNeo4jGraph()
    graph.load_from_extractor(extractor)

    # 1. Verify PageRank
    pr = graph.compute_citation_pagerank()
    assert len(pr) > 0
    top_case = max(pr, key=pr.get)
    assert pr[top_case] > 0.0

    # 2. Verify Overruled Detection
    overruled = graph.tag_overruled_cases()
    assert len(overruled) > 0
    overruled_cits = [o["overruled_citation"] for o in overruled]
    assert "2004 CLC 538" in overruled_cits

    # 3. Verify Cypher Pattern Execution
    cypher_sec23 = "MATCH (c:Case)-[:INTERPRETS]->(s:Section {number: '23'}) RETURN c"
    res1 = graph.execute_cypher(cypher_sec23)
    assert len(res1) >= 1
    found_overruled_in_sec23 = any(r.get("is_overruled", False) for r in res1)
    assert found_overruled_in_sec23 is True


def test_text_to_cypher_translation():
    """Validates natural language to Cypher translation logic."""
    q1 = "Which Supreme Court judgments interpreted Section 23 of the Contract Act, and were any of them later overruled?"
    t1 = TextToCypherTranslator.translate(q1)
    assert "INTERPRETS" in t1["cypher"]
    assert "OVERRULES" in t1["cypher"]
    assert "23" in t1["cypher"]

    q2 = "List the top landmark precedents by pagerank in the corpus."
    t2 = TextToCypherTranslator.translate(q2)
    assert "ORDER BY c.pagerank DESC" in t2["cypher"]

    q3 = "Which cases were presided over by Justice Bandial?"
    t3 = TextToCypherTranslator.translate(q3)
    assert "PRESIDED_BY" in t3["cypher"]
    assert "Justice Umar Ata Bandial" in t3["cypher"]


def test_graphrag_local_and_global_search():
    """Validates GraphRAG Local Search ego-graph extraction and Global Search community summaries."""
    grag = LegalGraphRAG()

    # Local search
    local_res = grag.local_search("Section 23 of Contract Act")
    assert local_res["total_nodes_in_subgraph"] > 5
    assert len(local_res["relational_facts"]) > 0

    # Global search
    global_res = grag.global_search("Contractual Legality and Unlawful Object")
    assert global_res["total_communities"] > 0
    assert len(global_res["top_thematic_communities"]) > 0


def test_graphrag_answers_scenario_query():
    """
    Validates end-to-end GraphRAG answer on the lawyer's prompt scenario:
    'Which Supreme Court judgments interpreted Section 23 of the Contract Act, and were any of them later overruled?'
    """
    grag = LegalGraphRAG()
    q = "Which Supreme Court judgments interpreted Section 23 of the Contract Act, and were any of them later overruled?"
    ans = grag.answer_question(q)

    assert "Section 23" in ans["short_answer"]
    assert "2004 CLC 538" in ans["short_answer"]
    assert "2023 SC 362" in ans["short_answer"]
    assert "OVERRULED" in ans["short_answer"]
    assert len(ans["overruled_warnings"]) > 0
    assert ans["overruled_warnings"][0]["citation"] == "2004 CLC 538"


def test_legal_query_router():
    """Validates automatic routing to Vector RAG, GraphRAG, and Hybrid RAG."""
    # Test GraphRAG routing (overruling / multi-hop / precedent chain)
    r1 = LegalQueryRouter.route_query("Which Supreme Court judgments interpreted Section 23 of Contract Act and were any later overruled?")
    assert r1["selected_engine"] == "GraphRAG"

    r2 = LegalQueryRouter.route_query("Was 2004 CLC 538 declared bad law by subsequent bench?")
    assert r2["selected_engine"] == "GraphRAG"

    # Test Vector RAG routing (definition / verbatim / penalty)
    r3 = LegalQueryRouter.route_query("What is the verbatim statutory text of Section 23 of the Contract Act?")
    assert r3["selected_engine"] == "Vector RAG"

    r4 = LegalQueryRouter.route_query("What is the statutory punishment for murder under Section 302 PPC?")
    assert r4["selected_engine"] == "Vector RAG"

    # Test Hybrid RAG routing (thematic synthesis / doctrine)
    r5 = LegalQueryRouter.route_query("Explain the judicial doctrine of public policy and unlawful object across Pakistani commercial cases.")
    assert r5["selected_engine"] == "Hybrid RAG"
