"""
Codebase split engine inspired by CocoIndex (Cerebras article).
Uses Python AST to split source files into coarse-to-fine hierarchical chunks
(Module -> Class -> Function/Method).
Supports incremental re-indexing via content SHA-256 hash tracking.
"""

import ast
import hashlib
import os
from typing import List, Dict, Any, Tuple
from Agent.knowledge_base.ingest.embeddings import EmbeddingEngine


class CodeSplitter:
    def __init__(self, embedding_engine: EmbeddingEngine):
        self.embedder = embedding_engine

    @staticmethod
    def compute_hash(file_path: str) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def process_python_file(self, file_path: str, rel_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        content_hash = self.compute_hash(file_path)

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source_code = f.read()

        lines = source_code.splitlines(keepends=True)
        total_lines = len(lines)

        chunks: List[Dict[str, Any]] = []

        module_summary = f"Module {rel_path}: Total lines={total_lines}."
        try:
            tree = ast.parse(source_code, filename=file_path)
            docstring = ast.get_docstring(tree)
            if docstring:
                module_summary += f" Docstring: {docstring[:300]}"
        except Exception:
            tree = None
            docstring = None

        chunks.append({
            "chunk_type": "module_summary",
            "parent_id": "",
            "start_line": 1,
            "end_line": min(100, total_lines),
            "raw_content": "".join(lines[:100]),
            "distilled_summary": module_summary,
            "metadata_json": {
                "file_path": rel_path,
                "total_lines": total_lines,
                "has_docstring": docstring is not None
            },
            "embedding": self.embedder.embed_text(module_summary + "\n" + "".join(lines[:50])),
            "idf_score": 1.0
        })

        if tree is None:
            chunk_size = 50
            overlap = 10
            step = max(1, chunk_size - overlap)
            for start_idx in range(0, total_lines, step):
                end_idx = min(start_idx + chunk_size, total_lines)
                block_lines = lines[start_idx:end_idx]
                block_text = "".join(block_lines)
                start_l = start_idx + 1
                end_l = end_idx
                summary = f"Line-block (syntax fallback) in {rel_path} (L{start_l}-L{end_l})"
                chunks.append({
                    "chunk_type": "line_block",
                    "parent_id": rel_path,
                    "start_line": start_l,
                    "end_line": end_l,
                    "raw_content": block_text[:3000],
                    "distilled_summary": summary,
                    "metadata_json": {
                        "file_path": rel_path,
                        "syntax_error_fallback": True
                    },
                    "embedding": self.embedder.embed_text(summary + "\n" + block_text[:1000]),
                    "idf_score": 1.0
                })
            return content_hash, chunks

        class CodeASTVisitor(ast.NodeVisitor):
            def __init__(self, lines: List[str], outer_self):
                self.lines = lines
                self.outer = outer_self
                self.found_chunks: List[Dict[str, Any]] = []
                self.current_class = ""

            def visit_ClassDef(self, node: ast.ClassDef):
                prev_class = self.current_class
                self.current_class = node.name

                start_l = node.lineno
                end_l = getattr(node, "end_lineno", start_l + 20)
                class_code = "".join(self.lines[start_l-1:end_l])

                doc = ast.get_docstring(node) or ""
                summary = f"Class {node.name} in {rel_path} (L{start_l}-L{end_l}). {doc[:200]}"

                self.found_chunks.append({
                    "chunk_type": "class",
                    "parent_id": rel_path,
                    "start_line": start_l,
                    "end_line": end_l,
                    "raw_content": class_code[:2000],
                    "distilled_summary": summary,
                    "metadata_json": {
                        "class_name": node.name,
                        "file_path": rel_path,
                        "base_classes": [b.id for b in node.bases if isinstance(b, ast.Name)]
                    },
                    "embedding": self.outer.embedder.embed_text(summary + "\n" + class_code[:1000]),
                    "idf_score": 1.5
                })

                self.generic_visit(node)
                self.current_class = prev_class

            def visit_FunctionDef(self, node: ast.FunctionDef):
                self._handle_func(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                self._handle_func(node)

            def _handle_func(self, node):
                start_l = node.lineno
                end_l = getattr(node, "end_lineno", start_l + 15)
                func_code = "".join(self.lines[start_l-1:end_l])

                args = [a.arg for a in node.args.args]
                doc = ast.get_docstring(node) or ""

                ctx_prefix = f"Class: {self.current_class} | " if self.current_class else ""
                summary = f"{ctx_prefix}Function {node.name}({', '.join(args)}) in {rel_path} (L{start_l}-L{end_l}). {doc[:200]}"

                chunk_type = "method" if self.current_class else "function"
                idf_val = 2.0 if len(node.name) > 10 or "_" in node.name else 1.0

                self.found_chunks.append({
                    "chunk_type": chunk_type,
                    "parent_id": self.current_class if self.current_class else rel_path,
                    "start_line": start_l,
                    "end_line": end_l,
                    "raw_content": func_code[:3000],
                    "distilled_summary": summary,
                    "metadata_json": {
                        "function_name": node.name,
                        "class_name": self.current_class,
                        "file_path": rel_path,
                        "args": args,
                        "line_count": end_l - start_l + 1
                    },
                    "embedding": self.outer.embedder.embed_text(summary + "\n" + func_code[:1500]),
                    "idf_score": idf_val
                })

        visitor = CodeASTVisitor(lines, self)
        visitor.visit(tree)

        chunks.extend(visitor.found_chunks)
        return content_hash, chunks
