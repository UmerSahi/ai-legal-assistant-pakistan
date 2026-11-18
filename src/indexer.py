"""
Indexing & Hybrid Retrieval Engine Module
Task 5: AI Legal Assistant (Khan & Associates)
Indexes legal chunks into:
1. ChromaDB Vector Database (Dense Semantic Embeddings with SentenceTransformers)
2. BM25 Lexical Keyword Index (Sparse Term Frequency / Inverted Index)
Provides Hybrid Search combining Dense + Sparse with Reciprocal Rank Fusion (RRF)
and domain-specific metadata filtering (Act, Section, Court, Year, Page, Matter ID).
"""

import os
import re
import pickle
import string
from typing import List, Dict, Any, Optional, Tuple

import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

from src.chunker import LegalChunk


class LegalSearchTokenizer:
    """Legal-aware tokenizer preserving statutory section markers and alphanumeric codes."""

    @staticmethod
    def tokenize(text: str) -> List[str]:
        if not text:
            return []
        # Lowercase
        t = text.lower()
        # Normalize punctuation except hyphens and dots within numbers/sections
        tokens = re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b|[\u0600-\u06FF]{2,}", t)
        return tokens


class LegalIndexer:
    """Dual Vector DB + BM25 indexing engine with Hybrid Retrieval for Khan & Associates."""

    def __init__(
        self,
        chroma_persist_dir: str = "outputs/indices/chromadb",
        bm25_persist_path: str = "outputs/indices/bm25_index.pkl",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        collection_name: str = "khan_associates_legal_corpus"
    ):
        self.chroma_persist_dir = chroma_persist_dir
        self.bm25_persist_path = bm25_persist_path
        self.embedding_model_name = embedding_model_name
        self.collection_name = collection_name

        # Ensure directories exist
        os.makedirs(self.chroma_persist_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.bm25_persist_path), exist_ok=True)

        # Lazy loaded components
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None

        self.bm25 = None
        self.indexed_chunks: List[Dict[str, Any]] = []
        self.chunk_id_to_chunk: Dict[str, Dict[str, Any]] = {}

    def _init_models(self):
        """Initializes SentenceTransformers and ChromaDB."""
        if self.embedding_model is None:
            print(f"[Indexer] Loading SentenceTransformer model: {self.embedding_model_name}...")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)

        if self.chroma_client is None:
            print(f"[Indexer] Connecting to Persistent ChromaDB at {self.chroma_persist_dir}...")
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_persist_dir)
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Khan & Associates Legal Corpus Index (Statutes, Judgments, Contracts)"}
            )

    def index_chunks(self, chunks: List[LegalChunk], batch_size: int = 128) -> Dict[str, Any]:
        """
        Indexes chunks into both ChromaDB vector database and BM25 lexical index.
        Stores rich metadata on every record: act, section, court, year, page, matter_id.
        """
        self._init_models()

        if not chunks:
            return {"status": "empty", "indexed_count": 0}

        print(f"\n[Indexer] Indexing {len(chunks)} legal chunks into Dual Vector DB & BM25...")

        # Ensure 100% unique IDs across all chunks
        seen_ids = set()
        for c in chunks:
            base_id = c.chunk_id
            unique_id = base_id
            counter = 1
            while unique_id in seen_ids:
                unique_id = f"{base_id}_{counter}"
                counter += 1
            seen_ids.add(unique_id)
            c.chunk_id = unique_id

        documents = []
        metadatas = []
        ids = []
        tokenized_corpus = []

        for c in chunks:
            c_dict = c.to_dict()
            self.indexed_chunks.append(c_dict)
            self.chunk_id_to_chunk[c.chunk_id] = c_dict

            documents.append(c.text)
            ids.append(c.chunk_id)

            # Metadata sanitized for ChromaDB (no None values, only str/int/float/bool)
            meta = {
                "doc_id": str(c.doc_id or ""),
                "doc_type": str(c.doc_type or ""),
                "act": str(c.act or ""),
                "section": str(c.section or ""),
                "court": str(c.court or ""),
                "year": int(c.year) if c.year else 0,
                "page": int(c.page) if c.page else 1,
                "matter_id": str(c.matter_id or ""),
                "strategy": str(c.strategy or ""),
                "chunk_type": str(c.chunk_type or "atomic"),
                "parent_id": str(c.parent_id or "")
            }
            metadatas.append(meta)

            # Tokenize for BM25
            tokens = LegalSearchTokenizer.tokenize(c.text)
            tokenized_corpus.append(tokens)

        # 1. Vector DB Indexing with Batch Embeddings
        print(f"[Indexer] Generating dense embeddings ({self.embedding_model_name})...")
        total = len(documents)
        for i in range(0, total, batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]

            embeddings = self.embedding_model.encode(batch_docs, show_progress_bar=False).tolist()

            # Upsert into ChromaDB
            self.collection.upsert(
                ids=batch_ids,
                embeddings=embeddings,
                documents=batch_docs,
                metadatas=batch_metas
            )
            print(f"  [ChromaDB] Upserted batch {i + 1} - {min(i + batch_size, total)} of {total}")

        # 2. BM25 Lexical Indexing
        print("[Indexer] Constructing BM25 Okapi inverted index...")
        self.bm25 = BM25Okapi(tokenized_corpus)

        # Persist BM25 and chunk lookup
        with open(self.bm25_persist_path, "wb") as f:
            pickle.dump({
                "bm25": self.bm25,
                "chunks": self.indexed_chunks,
                "chunk_id_to_chunk": self.chunk_id_to_chunk
            }, f)
        print(f"[Indexer] BM25 Index persisted to {self.bm25_persist_path}")

        return {
            "status": "success",
            "indexed_count": len(chunks),
            "collection_total": self.collection.count(),
            "chroma_dir": self.chroma_persist_dir,
            "bm25_file": self.bm25_persist_path
        }

    def load_persisted_index(self):
        """Loads serialized BM25 index and connects to ChromaDB."""
        self._init_models()
        if os.path.exists(self.bm25_persist_path):
            with open(self.bm25_persist_path, "rb") as f:
                data = pickle.load(f)
                self.bm25 = data["bm25"]
                self.indexed_chunks = data["chunks"]
                self.chunk_id_to_chunk = data["chunk_id_to_chunk"]

    # =========================================================================
    # RETRIEVAL METHODS
    # =========================================================================
    def search_vector(
        self,
        query: str,
        top_k: int = 5,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Dense semantic similarity search via ChromaDB."""
        self._init_models()
        query_emb = self.embedding_model.encode([query]).tolist()

        query_args = {
            "query_embeddings": query_emb,
            "n_results": top_k
        }
        if where_filter:
            query_args["where"] = where_filter

        raw_results = self.collection.query(**query_args)
        results = []

        if raw_results and raw_results["ids"] and len(raw_results["ids"][0]) > 0:
            for i in range(len(raw_results["ids"][0])):
                chunk_id = raw_results["ids"][0][i]
                doc_text = raw_results["documents"][0][i]
                meta = raw_results["metadatas"][0][i]
                dist = raw_results["distances"][0][i] if "distances" in raw_results and raw_results["distances"] else 0.0

                results.append({
                    "chunk_id": chunk_id,
                    "score": round(1.0 - dist, 4), # approximate similarity
                    "text": doc_text,
                    "metadata": meta,
                    "retrieval_mode": "vector"
                })

        return results

    def search_bm25(
        self,
        query: str,
        top_k: int = 5,
        doc_type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Sparse lexical search via BM25 Okapi."""
        if self.bm25 is None:
            self.load_persisted_index()

        if self.bm25 is None or not self.indexed_chunks:
            return []

        query_tokens = LegalSearchTokenizer.tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        scored_pairs = list(enumerate(scores))
        scored_pairs.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scored_pairs:
            chunk_dict = self.indexed_chunks[idx]

            if doc_type_filter and chunk_dict.get("doc_type") != doc_type_filter:
                continue

            chunk_lower = chunk_dict["text"].lower()
            if not any(qt in chunk_lower for qt in query_tokens) and score <= 0:
                continue

            results.append({
                "chunk_id": chunk_dict["chunk_id"],
                "score": round(float(score), 4),
                "text": chunk_dict["text"],
                "metadata": {
                    "doc_id": chunk_dict.get("doc_id", ""),
                    "doc_type": chunk_dict.get("doc_type", ""),
                    "act": chunk_dict.get("act", ""),
                    "section": chunk_dict.get("section", ""),
                    "court": chunk_dict.get("court", ""),
                    "year": chunk_dict.get("year", 0),
                    "page": chunk_dict.get("page", 1),
                    "matter_id": chunk_dict.get("matter_id", ""),
                    "parent_id": chunk_dict.get("parent_id", "")
                },
                "retrieval_mode": "bm25"
            })
            if len(results) >= top_k:
                break

        return results

    def search_hybrid(
        self,
        query: str,
        top_k: int = 5,
        alpha: float = 0.5,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) Hybrid Search combining Dense Vector + Sparse BM25.
        Score = alpha / (60 + rank_dense) + (1 - alpha) / (60 + rank_bm25)
        """
        vector_results = self.search_vector(query, top_k=top_k * 2, where_filter=where_filter)
        doc_type_filter = where_filter.get("doc_type") if where_filter else None
        bm25_results = self.search_bm25(query, top_k=top_k * 2, doc_type_filter=doc_type_filter)

        k = 60
        rrf_scores: Dict[str, float] = {}
        chunk_data: Dict[str, Dict[str, Any]] = {}

        # 1. Vector Ranks
        for rank, res in enumerate(vector_results, 1):
            cid = res["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (alpha / (k + rank))
            chunk_data[cid] = res

        # 2. BM25 Ranks
        for rank, res in enumerate(bm25_results, 1):
            cid = res["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + ((1.0 - alpha) / (k + rank))
            if cid not in chunk_data:
                chunk_data[cid] = res

        # Sort by RRF score
        sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        final_results = []
        for cid in sorted_cids[:top_k]:
            item = chunk_data[cid]
            final_results.append({
                "chunk_id": cid,
                "rrf_score": round(rrf_scores[cid], 5),
                "text": item["text"],
                "metadata": item["metadata"],
                "retrieval_mode": "hybrid_rrf"
            })

        return final_results


if __name__ == "__main__":
    indexer = LegalIndexer()

    # Create dummy chunks to verify indexing and retrieval
    test_chunks = [
        LegalChunk(
            chunk_id="STAT_PPC_SEC_302",
            doc_id="STAT_PPC",
            text="Section 302 PPC: Punishment of qatl-i-amd. Whoever commits qatl-i-amd shall be punished with death, or imprisonment for life.",
            strategy="section_level",
            doc_type="statute",
            act="Pakistan Penal Code, 1860",
            section="302",
            court="Sessions / High Court",
            year=1860,
            matter_id="MAT_CRIMINAL_001"
        ),
        LegalChunk(
            chunk_id="STAT_CPC_SEC_97",
            doc_id="STAT_CPC",
            text="Section 97 CPC: Appeal from final decree where no appeal from preliminary decree. Where any party aggrieved by a preliminary decree does not appeal from such decree, he shall be precluded from disputing its correctness.",
            strategy="section_level",
            doc_type="statute",
            act="Code of Civil Procedure, 1908",
            section="97",
            court="Civil / Appellate Court",
            year=1908,
            matter_id="MAT_CIVIL_002"
        ),
        LegalChunk(
            chunk_id="JUDG_SC_2022_BAIL",
            doc_id="JUDG_SC_2022",
            text="IN THE SUPREME COURT OF PAKISTAN: Principles governing cancellation of pre-arrest bail under section 497(5) Cr.P.C. Relief of bail once granted cannot be cancelled routinely.",
            strategy="section_level",
            doc_type="judgment",
            court="Supreme Court of Pakistan",
            year=2022,
            matter_id="MAT_CRIM_SC_003"
        ),
        LegalChunk(
            chunk_id="CONT_COMM_LEASE_CLAUSE_7",
            doc_id="CONT_COMM_LEASE",
            text="Clause 7: Indemnification and Hold Harmless. The Tenant agrees to indemnify and hold Khan & Associates harmless against all liabilities, claims, and damages arising on the premises.",
            strategy="section_level",
            doc_type="contract",
            act="Commercial Lease Deed",
            section="7",
            court="Arbitration Lahore",
            year=2025,
            matter_id="MAT_CONTRACT_004"
        )
    ]

    res = indexer.index_chunks(test_chunks)
    print(f"Index status: {res}")

    print("\n--- 1. Vector Search Test ---")
    v_res = indexer.search_vector("death penalty murder punishment", top_k=2)
    for r in v_res:
        print(f"  [{r['score']}] {r['chunk_id']} | Act: {r['metadata']['act']} | Sec: {r['metadata']['section']}")

    print("\n--- 2. BM25 Search Test ---")
    b_res = indexer.search_bm25("preliminary decree section 97", top_k=2)
    for r in b_res:
        print(f"  [{r['score']}] {r['chunk_id']} | Act: {r['metadata']['act']} | Sec: {r['metadata']['section']}")

    print("\n--- 3. Hybrid RRF Search Test ---")
    h_res = indexer.search_hybrid("tenant indemnity lease liability", top_k=2)
    for r in h_res:
        print(f"  [RRF: {r['rrf_score']}] {r['chunk_id']} | Act: {r['metadata']['act']}")
