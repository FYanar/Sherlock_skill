"""
Documentation and Markdown Distiller for OneClickDock Knowledge Base.
Splits Markdown documents into section chunks based on headers.
Extracts structured metadata (question, summary, resolution, references)
matching Cerebras distillation specification.
"""

import hashlib
import os
import re
from typing import List, Dict, Any, Tuple
from Agent.knowledge_base.ingest.embeddings import EmbeddingEngine


class DocDistiller:
    def __init__(self, embedding_engine: EmbeddingEngine):
        self.embedder = embedding_engine

    @staticmethod
    def compute_hash(file_path: str) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def process_markdown_file(self, file_path: str, rel_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        content_hash = self.compute_hash(file_path)

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        lines = content.splitlines(keepends=True)
        total_lines = len(lines)

        chunks: List[Dict[str, Any]] = []

        header_regex = re.compile(r'^(#{1,4})\s+(.+)$')

        current_header = os.path.basename(file_path)
        current_lines: List[str] = []
        start_line = 1

        for i, line in enumerate(lines, start=1):
            match = header_regex.match(line.strip())
            if match:
                if current_lines:
                    sec_text = "".join(current_lines).strip()
                    if len(sec_text) > 20:
                        chunks.append(self._create_doc_chunk(
                            rel_path=rel_path,
                            header=current_header,
                            text=sec_text,
                            start_line=start_line,
                            end_line=i-1
                        ))
                current_header = match.group(2)
                current_lines = [line]
                start_line = i
            else:
                current_lines.append(line)

        if current_lines:
            sec_text = "".join(current_lines).strip()
            if len(sec_text) > 20:
                chunks.append(self._create_doc_chunk(
                    rel_path=rel_path,
                    header=current_header,
                    text=sec_text,
                    start_line=start_line,
                    end_line=total_lines
                ))

        return content_hash, chunks

    def _create_doc_chunk(
        self,
        rel_path: str,
        header: str,
        text: str,
        start_line: int,
        end_line: int
    ) -> Dict[str, Any]:
        lines = text.splitlines()
        first_paragraph = lines[0] if lines else ""
        summary = f"Section '{header}' in {rel_path} (L{start_line}-L{end_line}). {first_paragraph[:250]}"

        has_status = "COMPLETED" in text or "PASS" in text or "FAIL" in text or "STRICT_PASS" in text
        idf_score = 1.8 if has_status or "WP-" in text else 1.2

        return {
            "chunk_type": "doc_section",
            "parent_id": rel_path,
            "start_line": start_line,
            "end_line": end_line,
            "raw_content": text[:3000],
            "distilled_summary": summary,
            "metadata_json": {
                "header": header,
                "file_path": rel_path,
                "has_status_record": has_status
            },
            "embedding": self.embedder.embed_text(summary + "\n" + text[:1500]),
            "idf_score": idf_score
        }
