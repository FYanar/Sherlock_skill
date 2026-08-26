"""
Planner engine for OneClickDock Knowledge Base inspired by Cerebras architecture.
Inspects query and active project scope to decide tool fan-out:
- subsystem_index: per-file module summaries
- search_code: code AST chunk search
- search_runs: execution output & benchmark log search
- search_docs: project plan & design document search
- who_knows: ownership / expertise mapping
"""

from typing import List, Dict, Any, Optional


class KnowledgePlanner:
    def __init__(self):
        self.available_tools = [
            "subsystem_index",
            "search_code",
            "search_runs",
            "search_docs",
            "who_knows"
        ]

    def plan(self, query: str, project_scope: str = "OneClickDock") -> Dict[str, Any]:
        q_lower = query.lower()
        selected_tools = []
        reasoning = []

        if any(k in q_lower for k in ["code", "func", "def ", "class", "script", "py", "utils", "zbg", "rmsd", "metal", "docking"]):
            selected_tools.append("search_code")
            reasoning.append("Code / function keywords detected -> invoking search_code")

        if any(k in q_lower for k in ["run", "metric", "score", "pass", "fail", "benchmark", "result", "log", "start.bat", "output"]):
            selected_tools.append("search_runs")
            reasoning.append("Run / metric keywords detected -> invoking search_runs")

        if any(k in q_lower for k in ["plan", "wp-", "audit", "architecture", "structure", "design", "doc"]):
            selected_tools.append("search_docs")
            reasoning.append("Documentation / plan keywords detected -> invoking search_docs")

        if any(k in q_lower for k in ["overview", "summary", "modules", "subsystem", "architecture", "what is"]):
            selected_tools.append("subsystem_index")
            reasoning.append("Overview / summary query -> invoking subsystem_index")

        if any(k in q_lower for k in ["who", "author", "owner", "expert"]):
            selected_tools.append("who_knows")
            reasoning.append("Expertise / ownership query -> invoking who_knows")

        if not selected_tools:
            selected_tools = ["search_code", "search_runs", "search_docs"]
            reasoning.append("General query -> fanning out to search_code, search_runs, search_docs")

        return {
            "query": query,
            "project_scope": project_scope,
            "selected_tools": selected_tools,
            "reasoning": reasoning
        }
