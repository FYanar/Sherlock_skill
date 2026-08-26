"""
Hybrid Retriever implementation for OneClickDock Knowledge Base.
Combines Lexical FTS5, Vector embeddings, IDF token rarity, and Age Decay.
"""

import math
import time
from typing import List, Dict, Any, Optional
from Agent.knowledge_base.db.store import KnowledgeStore
from Agent.knowledge_base.ingest.embeddings import EmbeddingEngine


class HybridRetriever:
    def __init__(self, store: KnowledgeStore, embedding_engine: EmbeddingEngine):
        self.store = store
        self.embedder = embedding_engine

    def retrieve(
        self,
        query: str,
        project: Optional[str] = "OneClickDock",
        source_type: Optional[str] = None,
        limit: int = 30,
        decay_half_life_days: float = 180.0
    ) -> List[Dict[str, Any]]:
        fts_results = self.store.fts_search(query, project=project, source_type=source_type, limit=limit)

        q_vec = self.embedder.embed_text(query)
        vec_results = self.store.vector_search(q_vec, project=project, source_type=source_type, limit=limit)

        now = time.time()
        sec_per_day = 86400.0

        combined_dict: Dict[int, Dict[str, Any]] = {}

        for rank, r in enumerate(fts_results, start=1):
            rid = r["id"]
            item = dict(r)
            item["fts_rank"] = rank
            item["vector_rank"] = 999
            combined_dict[rid] = item

        for rank, r in enumerate(vec_results, start=1):
            rid = r["id"]
            if rid in combined_dict:
                combined_dict[rid]["vector_rank"] = rank
                combined_dict[rid]["vector_score"] = r["vector_score"]
            else:
                item = dict(r)
                item["fts_rank"] = 999
                item["vector_rank"] = rank
                combined_dict[rid] = item

        decay_factor = math.log(2) / (decay_half_life_days * sec_per_day)

        final_candidates = []
        for item in combined_dict.values():
            created_at = item.get("created_at", now)
            age_seconds = max(0.0, now - created_at)
            age_decay = math.exp(-decay_factor * age_seconds)

            idf_score = item.get("idf_score", 1.0)
            item["age_decay"] = age_decay
            item["adjusted_score"] = (
                (item.get("lexical_score", 0.0) * 0.4 + item.get("vector_score", 0.0) * 0.6)
                * idf_score
                * age_decay
            )
            final_candidates.append(item)

        return final_candidates
