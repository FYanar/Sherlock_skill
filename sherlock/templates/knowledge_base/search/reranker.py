"""
Reciprocal Rank Fusion (RRF) and Reranker for OneClickDock Knowledge Base.
Implements Cerebras RRF formula score = sum(weight / (60 + rank)),
per-source contribution capping, candidate cross-scoring (0-10), and
Neighbor Context Expansion.
"""

from typing import List, Dict, Any
from Agent.knowledge_base.db.store import KnowledgeStore


class Reranker:
    def __init__(self, store: KnowledgeStore, k_constant: int = 60):
        self.store = store
        self.k = k_constant

    def rerank_and_expand(
        self,
        candidates: List[Dict[str, Any]],
        query: str,
        top_k: int = 10,
        max_per_source: int = 3,
        context_expansion_lines: int = 15
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        for item in candidates:
            rrf = 0.0
            fts_rank = item.get("fts_rank", 999)
            vec_rank = item.get("vector_rank", 999)

            if fts_rank < 999:
                rrf += 1.0 / (self.k + fts_rank)
            if vec_rank < 999:
                rrf += 1.0 / (self.k + vec_rank)

            rrf *= item.get("idf_score", 1.0)
            item["rrf_score"] = rrf

        candidates.sort(key=lambda x: x["rrf_score"], reverse=True)

        source_counts: Dict[str, int] = {}
        capped_candidates = []

        for item in candidates:
            src = item.get("source_id", "unknown")
            count = source_counts.get(src, 0)
            if count < max_per_source:
                source_counts[src] = count + 1
                capped_candidates.append(item)

        query_terms = set(query.lower().split())

        for item in capped_candidates:
            score = 0.0
            raw_text = (item.get("raw_content", "") + " " + item.get("distilled_summary", "")).lower()

            matched_terms = sum(1 for term in query_terms if term in raw_text)
            term_ratio = matched_terms / max(1, len(query_terms))
            score += term_ratio * 4.0

            score += min(4.0, item.get("rrf_score", 0.0) * 100.0)
            score += item.get("age_decay", 1.0) * 2.0

            item["final_rerank_score"] = round(min(10.0, max(0.0, score)), 2)

        capped_candidates.sort(key=lambda x: x["final_rerank_score"], reverse=True)
        top_winners = capped_candidates[:top_k]

        for item in top_winners:
            src_id = item.get("source_id", "")
            start_l = item.get("start_line", 0)
            end_l = item.get("end_line", 0)

            if src_id and start_l > 0:
                expanded_context = self.store.get_neighbor_context(
                    source_id=src_id,
                    start_line=start_l,
                    end_line=end_l,
                    context_lines=context_expansion_lines
                )
                item["expanded_context"] = expanded_context
            else:
                item["expanded_context"] = item.get("raw_content", "")

        return top_winners
