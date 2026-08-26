"""
Custom Data Plugin framework for OneClickDock Knowledge Base.
Allows custom domain connectors (PDB proteins, SMILES ligands, ZBG microstates)
to emit standardized rows into the shared knowledge datastore.
"""

import abc
import hashlib
import os
from typing import List, Dict, Any, Tuple
from Agent.knowledge_base.ingest.embeddings import EmbeddingEngine


class BaseKnowledgePlugin(abc.ABC):
    def __init__(self, embedding_engine: EmbeddingEngine):
        self.embedder = embedding_engine

    @property
    @abc.abstractmethod
    def plugin_name(self) -> str:
        pass

    @abc.abstractmethod
    def can_handle(self, file_path: str) -> bool:
        pass

    @abc.abstractmethod
    def process_source(self, file_path: str, rel_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        pass


class PDBStructurePlugin(BaseKnowledgePlugin):
    """Custom plugin for indexing PDB protein/ligand structure files."""

    @property
    def plugin_name(self) -> str:
        return "pdb_structure_connector"

    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith((".pdb", ".pdbqt", ".ent"))

    def process_source(self, file_path: str, rel_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        content_hash = hasher.hexdigest()

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        header_lines = [l for l in lines if l.startswith(("HEADER", "TITLE", "COMPND", "REMARK", "HETNAM"))]
        header_text = "".join(header_lines[:50])

        summary = f"PDB Structure File {rel_path} ({len(lines)} atom/record lines). Headers: {header_text[:200]}"

        chunk = {
            "chunk_type": "input_structure",
            "parent_id": rel_path,
            "start_line": 1,
            "end_line": len(lines),
            "raw_content": header_text if header_text else "".join(lines[:30]),
            "distilled_summary": summary,
            "metadata_json": {
                "file_path": rel_path,
                "atom_count": len([l for l in lines if l.startswith(("ATOM", "HETATM"))]),
                "plugin": self.plugin_name
            },
            "embedding": self.embedder.embed_text(summary),
            "idf_score": 2.0
        }

        return content_hash, [chunk]
