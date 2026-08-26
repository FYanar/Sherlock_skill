"""
Parallel Fan-out Executor and Synthesis Engine for OneClickDock Knowledge Base.
Executes tool selections, normalizes evidence bundles, and synthesizes answers.
"""

from typing import List, Dict, Any, Optional
from Agent.knowledge_base.db.store import KnowledgeStore
from Agent.knowledge_base.ingest.embeddings import EmbeddingEngine
from Agent.knowledge_base.search.hybrid_retriever import HybridRetriever
from Agent.knowledge_base.search.reranker import Reranker
from Agent.knowledge_base.agent.planner import KnowledgePlanner


class KnowledgeExecutor:
    def __init__(
        self,
        store: KnowledgeStore,
        retriever: HybridRetriever,
        reranker: Reranker
    ):
        self.store = store
        self.retriever = retriever
        self.reranker = reranker
        self.planner = KnowledgePlanner()

    def execute_and_synthesize(
        self,
        query: str,
        project_scope: str = "OneClickDock"
    ) -> Dict[str, Any]:
        plan_res = self.planner.plan(query, project_scope=project_scope)
        selected_tools = plan_res["selected_tools"]

        evidence_bundle: List[Dict[str, Any]] = []

        for tool in selected_tools:
            if tool == "search_code":
                cands = self.retriever.retrieve(query, project=project_scope, source_type="code", limit=20)
                reranked = self.reranker.rerank_and_expand(cands, query, top_k=5)
                evidence_bundle.extend(reranked)

            elif tool == "search_runs":
                cands = self.retriever.retrieve(query, project=project_scope, source_type="run_log", limit=20)
                reranked = self.reranker.rerank_and_expand(cands, query, top_k=5)
                evidence_bundle.extend(reranked)

            elif tool == "search_docs":
                cands = self.retriever.retrieve(query, project=project_scope, source_type="doc", limit=20)
                reranked = self.reranker.rerank_and_expand(cands, query, top_k=5)
                evidence_bundle.extend(reranked)

            elif tool == "subsystem_index":
                subsystems = self.store.get_subsystem_indices(project=project_scope)
                evidence_bundle.extend(subsystems[:5])

            elif tool == "who_knows":
                evidence_bundle.append({
                    "source_id": "owners://OneClickDock",
                    "distilled_summary": "OneClickDock Module Owners: Protein Prep (@F_YANAR), Ligand Prep & ZBG (@F_YANAR), Docking Execution (@F_YANAR), Consensus Benchmark (@F_YANAR).",
                    "final_rerank_score": 10.0,
                    "raw_content": "Lead Authors & Developers: F_YANAR, Daniel, Isaac, ZengHao."
                })

        seen_ids = set()
        unique_evidence = []
        for ev in evidence_bundle:
            eid = ev.get("id", ev.get("source_id"))
            if eid not in seen_ids:
                seen_ids.add(eid)
                unique_evidence.append(ev)

        unique_evidence.sort(key=lambda x: x.get("final_rerank_score", 0.0), reverse=True)
        top_evidence = unique_evidence[:10]

        synthesis = self._synthesize_answer(query, top_evidence)

        return {
            "query": query,
            "planner": plan_res,
            "evidence_count": len(top_evidence),
            "evidence": top_evidence,
            "answer": synthesis
        }

    def _synthesize_answer(self, query: str, evidence: List[Dict[str, Any]]) -> str:
        if not evidence:
            return f"No direct knowledge base matches found for '{query}' in project scope."

        lines = [f"### Knowledge Base Answer for: '{query}'\n"]

        lines.append("**Top Evidence & Citations:**\n")
        citations = []
        for idx, item in enumerate(evidence, start=1):
            src = item.get("source_id", "unknown")
            summary = item.get("distilled_summary", item.get("raw_content", ""))[:200].replace("\n", " ")
            score = item.get("final_rerank_score", 0.0)
            citations.append(f"[{idx}] `{src}` (Score: {score}/10) - {summary}")

        lines.extend([f"- {c}" for c in citations])
        lines.append("\n**Synthesized Details:**\n")

        top_item = evidence[0]
        ctx = top_item.get("expanded_context", top_item.get("raw_content", ""))
        lines.append(f"```text\n{ctx[:1200]}\n```\n")

        return "\n".join(lines)
