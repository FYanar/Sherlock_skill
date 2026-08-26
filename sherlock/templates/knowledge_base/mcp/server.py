"""
Model Context Protocol (MCP) Server for the Sherlock Knowledge Base.
Provides search, context generation, and subsystem-indexing tools for any project.
"""

import sys
import json
import os
from typing import Dict, Any, List
from Agent.knowledge_base.db.store import KnowledgeStore, DEFAULT_DB_PATH
from Agent.knowledge_base.ingest.embeddings import EmbeddingEngine
from Agent.knowledge_base.search.hybrid_retriever import HybridRetriever
from Agent.knowledge_base.search.reranker import Reranker


class MCPServer:
    """Small, dependency-free stdio implementation of the MCP tools protocol."""

    _SUPPORTED_PROTOCOL_VERSIONS = {
        "2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25",
    }
    _DEFAULT_PROTOCOL_VERSION = "2025-06-18"

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.store = KnowledgeStore(db_path)
        self.embedder = EmbeddingEngine()
        self.retriever = HybridRetriever(self.store, self.embedder)
        self.reranker = Reranker(self.store)
        self._initialized = False

    @staticmethod
    def _tool_definitions() -> List[Dict[str, Any]]:
        common_query = {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "project": {"type": "string", "description": "Project scope; defaults to OneClickDock."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "description": "Maximum result count; defaults to 10."},
            },
            "required": ["query"],
            "additionalProperties": False,
        }
        return [
            {"name": "search", "description": "Search all indexed OneClickDock knowledge.", "inputSchema": common_query},
            {"name": "search_code", "description": "Search indexed source-code knowledge.", "inputSchema": common_query},
            {"name": "search_runs", "description": "Search indexed run logs and output artifacts.", "inputSchema": common_query},
            {
                "name": "context",
                "description": "Generate the required pre-edit context bundle for a file, symbol, or WP id.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "description": "Target file path, symbol, or work-package id."},
                        "project": {"type": "string", "description": "Project scope; defaults to OneClickDock."},
                    },
                    "required": ["target"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "subsystem_index",
                "description": "List indexed OneClickDock subsystems.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"project": {"type": "string", "description": "Project scope; defaults to OneClickDock."}},
                    "additionalProperties": False,
                },
            },
            {
                "name": "who_knows",
                "description": "Return ownership hints for the major OneClickDock subsystems.",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        ]

    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        query = arguments.get("query", "")
        project = arguments.get("project", "OneClickDock")
        limit = int(arguments.get("limit", 10))

        if tool_name == "search":
            cands = self.retriever.retrieve(query, project=project, limit=limit * 2)
            return {"status": "ok", "count": len(cands), "results": self.reranker.rerank_and_expand(cands, query, top_k=limit)}
        if tool_name == "search_code":
            cands = self.retriever.retrieve(query, project=project, source_type="code", limit=limit * 2)
            return {"status": "ok", "count": len(cands), "results": self.reranker.rerank_and_expand(cands, query, top_k=limit)}
        if tool_name == "search_runs":
            cands = self.retriever.retrieve(query, project=project, source_type="run_log", limit=limit * 2)
            return {"status": "ok", "count": len(cands), "results": self.reranker.rerank_and_expand(cands, query, top_k=limit)}
        if tool_name == "context":
            target = str(arguments.get("target", "")).strip()
            if not target:
                return {"status": "error", "message": "context requires a non-empty target."}
            from Agent.knowledge_base.agent.context_generator import AgentContextGenerator
            generator = AgentContextGenerator(self.store, self.retriever, self.reranker)
            return {"status": "ok", "target": target, "context": generator.generate_preflight_context(target, project_scope=project)}
        if tool_name == "subsystem_index":
            results = self.store.get_subsystem_indices(project=project)
            return {"status": "ok", "count": len(results), "results": results}
        if tool_name == "who_knows":
            # Dynamic ownership discovery: read owners.md or CODEOWNERS if present,
            # then fall back to top-level directory scan. No OneClickDock hard-coding.
            import os
            project_root = os.environ.get("SHERLOCK_PROJECT_ROOT", os.getcwd())
            owners_hints = []

            # Try reading Agent/owners.md or .github/CODEOWNERS
            for owners_file in ["Agent/owners.md", ".github/CODEOWNERS", "CODEOWNERS"]:
                full_path = os.path.join(project_root, owners_file)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith("#"):
                                    owners_hints.append({"source": owners_file, "entry": line})
                    except Exception:
                        pass
                    break

            # Fall back: top-level directories → generic hints
            if not owners_hints:
                try:
                    top_dirs = [
                        d for d in os.listdir(project_root)
                        if os.path.isdir(os.path.join(project_root, d))
                        and not d.startswith(".") and d not in {"__pycache__", "node_modules", "venv", ".venv"}
                    ]
                    for d in sorted(top_dirs)[:10]:
                        owners_hints.append({"topic": d, "owner": "unknown", "path": f"{d}/"})
                except Exception:
                    owners_hints = [{"note": "No CODEOWNERS or Agent/owners.md found. Create one to populate this tool."}]

            return {"status": "ok", "results": owners_hints}

        return {"status": "error", "message": f"Unknown MCP tool: {tool_name}"}

    @staticmethod
    def _response(request_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    @staticmethod
    def _error(request_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    @staticmethod
    def _write(payload: Dict[str, Any]) -> None:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
        sys.stdout.flush()

    def _initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        requested = params.get("protocolVersion")
        version = requested if requested in self._SUPPORTED_PROTOCOL_VERSIONS else self._DEFAULT_PROTOCOL_VERSION
        return {
            "protocolVersion": version,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "oneclickdock-knowledge-base", "version": "1.0.0"},
            "instructions": "Use context before modifying OneClickDock code or starting a work package.",
        }

    def run_stdio_loop(self) -> None:
        for line in sys.stdin:
            try:
                request = json.loads(line)
                if not isinstance(request, dict):
                    self._write(self._error(None, -32600, "Invalid Request"))
                    continue
                request_id = request.get("id")
                is_notification = "id" not in request
                method = request.get("method")
                params = request.get("params", {})
                if not isinstance(method, str) or not isinstance(params, dict):
                    if not is_notification:
                        self._write(self._error(request_id, -32600, "Invalid Request"))
                    continue
                if method == "initialize":
                    if not is_notification:
                        self._write(self._response(request_id, self._initialize(params)))
                elif method == "notifications/initialized":
                    self._initialized = True
                elif method == "ping":
                    if not is_notification:
                        self._write(self._response(request_id, {}))
                elif method == "tools/list":
                    if not is_notification:
                        self._write(self._response(request_id, {"tools": self._tool_definitions()}))
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    if not isinstance(tool_name, str) or not isinstance(arguments, dict):
                        if not is_notification:
                            self._write(self._error(request_id, -32602, "Invalid tool call parameters"))
                        continue
                    result = self.handle_tool_call(tool_name, arguments)
                    tool_result = {
                        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}],
                    }
                    if result.get("status") == "error":
                        tool_result["isError"] = True
                    if not is_notification:
                        self._write(self._response(request_id, tool_result))
                elif not is_notification:
                    self._write(self._error(request_id, -32601, "Method not found"))
            except json.JSONDecodeError:
                self._write(self._error(None, -32700, "Parse error"))
            except Exception as exc:
                print(f"[oneclickdock-knowledge-base] {exc}", file=sys.stderr, flush=True)
                if 'request_id' in locals() and not is_notification:
                    self._write(self._error(request_id, -32603, "Internal error"))
