# Khan & Associates — AI Legal Assistant API Documentation
### Version 1.0.0 | Production REST API Reference

The AI Legal Assistant provides enterprise-grade REST endpoints for bilingual legal research, knowledge graph relational queries, contract playbook auditing, version comparison, legal drafting, and security governance.

**Base URL:** `http://localhost:8000` (or `https://legal-ai.khanlaw.com.pk`)  
**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI) / `http://localhost:8000/redoc` (ReDoc)

---

## 1. System & Telemetry Endpoints

### `GET /api/health`
Retrieves live health status, component readiness, index counts, and cryptographic audit log status.

#### Response `200 OK`
```json
{
  "status": "healthy",
  "service": "Khan & Associates AI Legal Assistant",
  "version": "1.0.0",
  "timestamp": "2026-11-18T09:20:00Z",
  "components": {
    "chromadb_vector_store": {
      "status": "ready",
      "collection": "khan_associates_legal_corpus",
      "persist_dir": "outputs/indices/chromadb"
    },
    "bm25_lexical_index": {
      "status": "ready",
      "indexed_chunks": 1250
    },
    "knowledge_graph": {
      "status": "ready",
      "total_nodes": 2387,
      "total_edges": 2432,
      "cases_count": 200,
      "sections_count": 750
    },
    "security_shield": {
      "status": "active",
      "audit_chain_valid": true,
      "audit_records_verified": 68,
      "chain_status": "INTEGRITY_VERIFIED"
    }
  }
}
```

---

## 2. Grounded Legal Research

### `POST /api/research`
Executes hybrid retrieval (ChromaDB + BM25Okapi with RRF) and generates structured answers with exact statutory citations, quoted source text, and automated citation verification.

#### Request Body
```json
{
  "query": "Agar consideration unlawful ho to kya contract void hai?",
  "user_id": "usr_asc_03",
  "matter_id": "PUBLIC_LAW",
  "mode": "parent_child"
}
```

#### Response `200 OK`
```json
{
  "query": "Agar consideration unlawful ho to kya contract void hai?",
  "short_answer": "Yes, if the consideration or object of an agreement is unlawful, the contract is void ab initio under Section 23 of The Contract Act, 1872.",
  "explanation": "Under Section 23 of The Contract Act, 1872, the consideration or object of an agreement is unlawful if it is forbidden by law, defeats the provisions of any law, is fraudulent, involves injury to the person or property of another, or is regarded by the court as immoral or opposed to public policy. Section 24 further reinforces that if any part of a single consideration for one or more objects is unlawful, the entire agreement is void.",
  "exact_citations": [
    "The Contract Act, 1872 (Section 23)",
    "The Contract Act, 1872 (Section 24)"
  ],
  "quoted_source_text": "The consideration or object of an agreement is lawful, unless it is forbidden by law; or is of such a nature that, if permitted, it would defeat the provisions of any law; or is fraudulent; or involves or implies injury to the person or property of another; or the Court regards it as immoral, or opposed to public policy. In each of these cases, the consideration or object of an agreement is said to be unlawful. Every agreement of which the object or consideration is unlawful is void.",
  "verification": {
    "citations_verified": true,
    "fabricated_citations_count": 0,
    "quote_found_in_corpus": true,
    "status": "GROUNDED_AND_VERIFIED"
  },
  "latency_ms": 142.5
}
```

#### Out-of-Corpus Refusal Example
```json
{
  "query": "What are the rules of adverse possession under Section 14 of the California Civil Code?",
  "short_answer": "No sufficient source found",
  "explanation": "The query refers to legal concepts, foreign statutes (such as US, UK, or Indian law), or matters outside the indexed Pakistani statutes, Supreme Court judgments, and commercial contracts corpus.",
  "exact_citations": [],
  "quoted_source_text": "",
  "latency_ms": 45.2
}
```

---

## 3. Knowledge Graph & GraphRAG

### `POST /api/graphrag`
Executes Text-to-Cypher translations, multi-hop relationship traversals, and bad-law/overruled precedent detection across 2,387 legal entities.

#### Request Body
```json
{
  "query": "Which Supreme Court judgments interpreted Section 23 of the Contract Act, and were any of them later overruled?",
  "user_id": "usr_asc_03",
  "mode": "auto"
}
```

#### Response `200 OK`
```json
{
  "query": "Which Supreme Court judgments interpreted Section 23 of the Contract Act, and were any of them later overruled?",
  "intent": "statute_interpretation_and_overruling",
  "cypher_query": "MATCH (c:Case)-[:INTERPRETS]->(s:Section {number: '23'})<-[:CONTAINS_SECTION]-(a:Act) WHERE a.title CONTAINS 'Contract Act' OPTIONAL MATCH (overruler:Case)-[:OVERRULES]->(c) RETURN c.citation AS case_citation, c.holding AS holding, c.is_overruled AS is_overruled, overruler.citation AS overruled_by_citation",
  "selected_engine": "GRAPHRAG",
  "short_answer": "Supreme Court judgments interpreting Section 23 of the Contract Act include Civil Appeal No. 419 of 2011 and 2004 CLC 538. Crucially, 2004 CLC 538 was subsequently OVERRULED by a 3-member Supreme Court bench in 2023 SC 362, which established that agreements with unlawful consideration are void ab initio and unenforceable.",
  "overruled_precedents_detected": [
    {
      "overruled_case_id": "case_2004_clc_538",
      "overruled_citation": "2004 CLC 538",
      "overruled_by_id": "case_2023_sc_362",
      "overruling_citation": "2023 SC 362",
      "grounds": "Declared bad law by larger bench; partial enforceability rejected under Section 23"
    }
  ],
  "latency_ms": 68.4
}
```

---

## 4. Contract Intelligence

### `POST /api/review`
Evaluates contract clauses against Khan & Associates' commercial playbook. Returns risk scores (0-100), clause badges (`PASS`, `WARN`, `FAIL`), and missing mandatory clauses.

#### Request Body
```json
{
  "contract_name": "Vendor_Master_Agreement.docx",
  "contract_text": "1. Indemnification: Supplier indemnifies customer unconditionally.\n2. Limitation of Liability: Neither party's liability shall be subject to any cap.",
  "user_id": "usr_asc_03",
  "matter_id": "MAT-2024-KHI-001"
}
```

#### Response `200 OK`
```json
{
  "contract_title": "Vendor_Master_Agreement.docx",
  "overall_risk_score": 70,
  "risk_verdict": "HIGH RISK (Severe Red Flags - Do Not Sign As-Is)",
  "risk_color": "Red",
  "missing_mandatory_clauses": [
    "Data Protection & Cybersecurity",
    "Anti-Bribery & Anti-Money Laundering",
    "Severability",
    "Entire Agreement"
  ],
  "clause_reviews": [
    {
      "clause_number": "1",
      "heading": "Indemnification",
      "status": "FAIL",
      "badge": "❌ FAIL",
      "comments": "Unilateral uncapped indemnity. Firm playbook requires mutual indemnity restricted to direct claims.",
      "suggested_wording": "Each party shall indemnify, defend and hold harmless the other party against direct losses..."
    }
  ]
}
```

---

## 5. Security & Audit Logging

### `GET /api/audit`
Retrieves cryptographically verified audit records with HMAC-SHA256 signature chain verification.

#### Query Parameters
- `limit`: Number of recent events to return (default: 50).

#### Response `200 OK`
```json
{
  "chain_integrity_valid": true,
  "total_records_verified": 72,
  "verification_error": null,
  "returned_records": 10,
  "records": [
    {
      "event_id": "4b68e989-482a-416b-9c6a-6691c28c8990",
      "timestamp": "2026-11-18T09:21:15Z",
      "event_type": "PROMPT_INJECTION_BLOCKED",
      "user_id": "usr_asc_03",
      "user_role": "Associate",
      "matter_id": "PUBLIC_LAW",
      "action": "EXECUTE_RESEARCH_QUERY",
      "status": "BLOCKED",
      "details": {
        "threat": "INSTRUCTION_OVERRIDE",
        "risk_score": 0.95
      },
      "chain_hash": "a1f9e87c53d10cbe44..."
    }
  ]
}
```
