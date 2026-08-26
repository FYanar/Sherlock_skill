"""
SQLite Store implementation for OneClickDock Knowledge Base.
Provides FTS5 full-text search, numpy vector similarity, incremental sync metadata,
and context expansion. Default DB path is inside Agent/knowledge_base/.
"""

import sqlite3
import json
import time
import os
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from Agent.knowledge_base.db.schema import (
    CREATE_EMBEDDINGS_TABLE,
    CREATE_FTS_TABLE,
    CREATE_FTS_TRIGGERS,
    CREATE_SYNC_METADATA_TABLE,
    CREATE_INDEXES
)


# DB path anchoring: use PROJECT_ROOT (parent of Agent/knowledge_base/) to prevent
# the "different cwd creates a new empty DB" bug where MCP launched from another
# directory silently creates a second, empty database instead of using the real one.
def _get_default_db_path() -> str:
    """Compute absolute DB path anchored to the project root, regardless of cwd."""
    # This file lives at: <project_root>/Agent/knowledge_base/db/store.py
    _this_file = os.path.abspath(__file__)
    _project_root = os.path.dirname(  # <project_root>
        os.path.dirname(              # Agent/
            os.path.dirname(          # knowledge_base/
                os.path.dirname(_this_file)  # db/
            )
        )
    )
    return os.path.join(_project_root, "Agent", "knowledge_base", "knowledge_base.db")


DEFAULT_DB_PATH = _get_default_db_path()



class KnowledgeStore:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        db_dir = os.path.dirname(os.path.abspath(self.db_path))
        os.makedirs(db_dir, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(CREATE_EMBEDDINGS_TABLE)
            cursor.execute(CREATE_FTS_TABLE)
            cursor.executescript(CREATE_FTS_TRIGGERS)
            cursor.execute(CREATE_SYNC_METADATA_TABLE)
            cursor.executescript(CREATE_INDEXES)
            conn.commit()

    def is_source_current(self, source_id: str, content_hash: str) -> bool:
        """Check if source is up-to-date in sync metadata (CocoIndex style)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT content_hash FROM sync_metadata WHERE source_id = ?",
                (source_id,)
            )
            row = cursor.fetchone()
            if row and row["content_hash"] == content_hash:
                return True
            return False

    def delete_source(self, source_id: str):
        """Remove all chunks and sync metadata for a source."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM knowledge_embeddings WHERE source_id = ?", (source_id,))
            cursor.execute("DELETE FROM sync_metadata WHERE source_id = ?", (source_id,))
            conn.commit()

    def prune_obsolete_sources(self, active_source_ids: List[str]) -> int:
        """
        Purge obsolete sources from database that no longer exist on disk.
        Returns count of pruned sources.
        """
        active_set = set(active_source_ids)
        pruned_count = 0

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT source_id FROM sync_metadata")
            all_synced = [row["source_id"] for row in cursor.fetchall()]

            for src in all_synced:
                # Do not prune non-file virtual sources like slack://
                if src.startswith("slack://") or src.startswith("owners://"):
                    continue
                if src not in active_set:
                    cursor.execute("DELETE FROM knowledge_embeddings WHERE source_id = ?", (src,))
                    cursor.execute("DELETE FROM sync_metadata WHERE source_id = ?", (src,))
                    pruned_count += 1
            conn.commit()
        return pruned_count

    def clear_all_data(self):
        """Wipe all indexed data for a clean reindex."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM knowledge_embeddings")
            cursor.execute("DELETE FROM sync_metadata")
            try:
                cursor.execute("DELETE FROM fts_embeddings")
            except Exception:
                pass
            conn.commit()

    def upsert_source_chunks(
        self,
        source_id: str,
        source_type: str,
        chunks: List[Dict[str, Any]],
        content_hash: str,
        project: str = "OneClickDock"
    ):
        """
        Upsert chunks for a source file/thread.
        """
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM knowledge_embeddings WHERE source_id = ?", (source_id,))

            for chunk in chunks:
                emb = chunk.get("embedding")
                emb_blob = None
                if emb is not None:
                    arr = np.array(emb, dtype=np.float32)
                    emb_blob = arr.tobytes()

                meta = chunk.get("metadata_json", {})
                if isinstance(meta, dict):
                    meta = json.dumps(meta, ensure_ascii=False)

                cursor.execute(
                    """
                    INSERT INTO knowledge_embeddings (
                        project, source_type, source_id, chunk_type, parent_id,
                        start_line, end_line, raw_content, distilled_summary,
                        metadata_json, embedding_blob, content_hash, idf_score, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project,
                        source_type,
                        source_id,
                        chunk.get("chunk_type", "snippet"),
                        chunk.get("parent_id", ""),
                        chunk.get("start_line", 0),
                        chunk.get("end_line", 0),
                        chunk.get("raw_content", ""),
                        chunk.get("distilled_summary", ""),
                        meta,
                        emb_blob,
                        content_hash,
                        chunk.get("idf_score", 1.0),
                        chunk.get("created_at", now)
                    )
                )

            cursor.execute(
                """
                INSERT OR REPLACE INTO sync_metadata (source_id, source_type, content_hash, chunk_count, last_synced)
                VALUES (?, ?, ?, ?, ?)
                """,
                (source_id, source_type, content_hash, len(chunks), now)
            )
            conn.commit()

    def fts_search(
        self,
        query: str,
        project: Optional[str] = None,
        source_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Perform full-text lexical search using SQLite FTS5 BM25."""
        if not query or not query.strip():
            return []

        clean_terms = []
        for word in query.replace('"', ' ').replace("'", ' ').split():
            clean = "".join(c for c in word if c.isalnum() or c in ("_", "-"))
            if clean:
                clean_terms.append(f'"{clean}"')
        
        if not clean_terms:
            return []
            
        fts_query = " OR ".join(clean_terms)

        sql = """
            SELECT 
                k.id, k.project, k.source_type, k.source_id, k.chunk_type,
                k.parent_id, k.start_line, k.end_line, k.raw_content,
                k.distilled_summary, k.metadata_json, k.idf_score, k.created_at,
                bm25(fts_embeddings) as bm25_score
            FROM fts_embeddings fts
            JOIN knowledge_embeddings k ON fts.rowid = k.id
            WHERE fts_embeddings MATCH ?
        """
        params: List[Any] = [fts_query]

        if project:
            sql += " AND k.project = ?"
            params.append(project)
        if source_type:
            sql += " AND k.source_type = ?"
            params.append(source_type)

        sql += " ORDER BY bm25_score ASC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
            except sqlite3.OperationalError:
                like_sql = """
                    SELECT id, project, source_type, source_id, chunk_type, parent_id,
                           start_line, end_line, raw_content, distilled_summary,
                           metadata_json, idf_score, created_at, 1.0 as bm25_score
                    FROM knowledge_embeddings
                    WHERE raw_content LIKE ? OR distilled_summary LIKE ?
                    LIMIT ?
                """
                like_param = f"%{query}%"
                cursor.execute(like_sql, (like_param, like_param, limit))
                rows = cursor.fetchall()

            results = []
            for row in rows:
                r = dict(row)
                r["lexical_score"] = float(1.0 / (1.0 + abs(r.get("bm25_score", 0.0))))
                results.append(r)
            return results

    def vector_search(
        self,
        query_vector: np.ndarray,
        project: Optional[str] = None,
        source_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Perform cosine similarity vector search over numpy embedding blobs."""
        if query_vector is None or len(query_vector) == 0:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        norm_q = np.linalg.norm(q_vec)
        if norm_q > 0:
            q_vec = q_vec / norm_q

        sql = "SELECT id, project, source_type, source_id, chunk_type, parent_id, start_line, end_line, raw_content, distilled_summary, metadata_json, embedding_blob, idf_score, created_at FROM knowledge_embeddings WHERE embedding_blob IS NOT NULL"
        params: List[Any] = []

        if project:
            sql += " AND project = ?"
            params.append(project)
        if source_type:
            sql += " AND source_type = ?"
            params.append(source_type)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        if not rows:
            return []

        scored_results = []
        for row in rows:
            r = dict(row)
            emb_blob = r.pop("embedding_blob")
            if not emb_blob:
                continue
            doc_vec = np.frombuffer(emb_blob, dtype=np.float32)
            norm_doc = np.linalg.norm(doc_vec)
            if norm_doc > 0:
                doc_vec = doc_vec / norm_doc
                cos_sim = float(np.dot(q_vec, doc_vec))
            else:
                cos_sim = 0.0

            r["vector_score"] = max(0.0, cos_sim)
            scored_results.append(r)

        scored_results.sort(key=lambda x: x["vector_score"], reverse=True)
        return scored_results[:limit]

    def get_neighbor_context(self, source_id: str, start_line: int, end_line: int, context_lines: int = 15) -> str:
        """
        Cerebras Neighbor Context Expansion:
        Retrieves surrounding lines of code or markdown section context.
        """
        if not os.path.exists(source_id):
            return ""

        try:
            with open(source_id, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            total_lines = len(lines)
            exp_start = max(0, start_line - 1 - context_lines)
            exp_end = min(total_lines, end_line + context_lines)

            header = f"--- Context Expansion [{source_id} L{exp_start+1}-L{exp_end}] ---\n"
            content = "".join(lines[exp_start:exp_end])
            return header + content
        except Exception:
            return ""

    def get_subsystem_indices(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return module and subsystem-level summaries."""
        sql = """
            SELECT source_id, source_type, chunk_type, raw_content, distilled_summary, metadata_json
            FROM knowledge_embeddings
            WHERE chunk_type IN ('class', 'module_summary', 'subsystem_summary', 'run_summary')
        """
        params: List[Any] = []
        if project:
            sql += " AND project = ?"
            params.append(project)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_all_sources(self) -> List[Dict[str, Any]]:
        """Return all synced sources from sync_metadata."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sync_metadata ORDER BY last_synced DESC")
            return [dict(r) for r in cursor.fetchall()]
