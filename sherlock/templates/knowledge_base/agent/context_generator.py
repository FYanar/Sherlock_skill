"""
Agent Pre-Flight Context Generator for the Sherlock Knowledge Base.
Gathers high-density context (AST contracts, past audit findings, config constraints,
and run metrics) for AI agents before they write or refactor code.
"""

from typing import Dict, Any, List, Optional
from Agent.knowledge_base.db.store import KnowledgeStore
from Agent.knowledge_base.ingest.embeddings import EmbeddingEngine
from Agent.knowledge_base.search.hybrid_retriever import HybridRetriever
from Agent.knowledge_base.search.reranker import Reranker


class AgentContextGenerator:
    def __init__(self, store: KnowledgeStore, retriever: HybridRetriever, reranker: Reranker):
        self.store = store
        self.retriever = retriever
        self.reranker = reranker

    def generate_preflight_context(self, target: str, project_scope: Optional[str] = None) -> str:
        code_cands = self.retriever.retrieve(target, project=project_scope, source_type="code", limit=15)
        code_winners = self.reranker.rerank_and_expand(code_cands, target, top_k=5)

        doc_cands = self.retriever.retrieve(target, project=project_scope, source_type="doc", limit=15)
        doc_winners = self.reranker.rerank_and_expand(doc_cands, target, top_k=5)

        run_cands = self.retriever.retrieve(target, project=project_scope, source_type="run_log", limit=10)
        run_winners = self.reranker.rerank_and_expand(run_cands, target, top_k=3)

        scope_label = project_scope or "all projects"
        lines = [
            f"# 🤖 Agent Pre-Flight Knowledge Context: `{target}`",
            f"Context automatically retrieved from Knowledge Base (scope: {scope_label}) to guide code edits.",
            "---",
            "## 1. Code Contracts & Function Signatures"
        ]

        if code_winners:
            for w in code_winners:
                src = w.get("source_id", "")
                summary = w.get("distilled_summary", "")
                lines.append(f"### `{src}` (Score: {w.get('final_rerank_score', 0)}/10)")
                lines.append(f"- **Summary**: {summary}")
                ctx = w.get("expanded_context", w.get("raw_content", ""))
                lines.append(f"```\n{ctx[:1000]}\n```\n")
        else:
            lines.append("No specific code contracts matched.\n")

        lines.append("## 2. Relevant Analysis Reports & Past Audit Findings")
        if doc_winners:
            for w in doc_winners:
                src = w.get("source_id", "")
                summary = w.get("distilled_summary", "")
                lines.append(f"- **`{src}`**: {summary}")
                raw = w.get("raw_content", "")[:500].replace("\n", " ")
                lines.append(f"  > {raw}\n")
        else:
            lines.append("No historical audit findings matched.\n")

        lines.append("## 3. Configuration & Run Metrics")
        if run_winners:
            for w in run_winners:
                src = w.get("source_id", "")
                summary = w.get("distilled_summary", "")
                lines.append(f"- **`{src}`**: {summary}\n")
        else:
            lines.append("No historical run log records matched.\n")

        lines.append("---")
        lines.append(
            "⚠️ **Mandatory Protocol for AI Agent**: "
            "Ensure code edits comply with the contracts and audit rules above. "
            "Do not regress verified invariants documented in Agent/memory.md."
        )

        return "\n".join(lines)

