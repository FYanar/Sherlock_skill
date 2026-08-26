"""
Execution Run & Benchmark Log Ingester for OneClickDock Knowledge Base.
Parses run state records, benchmark metrics, and execution outputs.
"""

import json
import os
import time
import hashlib
from typing import List, Dict, Any, Tuple
from Agent.knowledge_base.ingest.embeddings import EmbeddingEngine


class RunIngester:
    def __init__(self, embedding_engine: EmbeddingEngine):
        self.embedder = embedding_engine

    @staticmethod
    def compute_hash(file_path: str) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def process_run_file(self, file_path: str, rel_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        content_hash = self.compute_hash(file_path)
        filename = os.path.basename(file_path)

        chunks: List[Dict[str, Any]] = []

        if filename.endswith(".json"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = {}

            if isinstance(data, dict):
                assessment = data.get('combined_assessment', 'UNKNOWN')
                summary = f"Run Metrics JSON ({rel_path}). Assessment: {assessment}."
            elif isinstance(data, list):
                summary = f"Run Metadata List JSON ({rel_path}). Items count: {len(data)}."
            else:
                summary = f"Run Value JSON ({rel_path}). Type: {type(data).__name__}."

            raw_text = json.dumps(data, indent=2)

            chunks.append({
                "chunk_type": "run_summary",
                "parent_id": rel_path,
                "start_line": 1,
                "end_line": len(raw_text.splitlines()),
                "raw_content": raw_text[:3000],
                "distilled_summary": summary,
                "metadata_json": {
                    "file_path": rel_path,
                    "metrics": data
                },
                "embedding": self.embedder.embed_text(summary + "\n" + raw_text[:1500]),
                "idf_score": 2.5,
                "created_at": os.path.getmtime(file_path)
            })

        elif filename.endswith(".csv") or filename.endswith(".txt") or filename.endswith(".log"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            total_lines = len(lines)
            summary = f"Execution Output Log {rel_path}: {total_lines} lines recorded."
            raw_text = "".join(lines[:100])

            chunks.append({
                "chunk_type": "run_summary",
                "parent_id": rel_path,
                "start_line": 1,
                "end_line": min(100, total_lines),
                "raw_content": raw_text[:3000],
                "distilled_summary": summary,
                "metadata_json": {
                    "file_path": rel_path,
                    "line_count": total_lines
                },
                "embedding": self.embedder.embed_text(summary + "\n" + raw_text[:1000]),
                "idf_score": 1.5,
                "created_at": os.path.getmtime(file_path)
            })

        return content_hash, chunks
