"""
CLI Entrypoint for OneClickDock Knowledge Base System.
Located inside Agent/knowledge_base/.
"""

import sys
import os
import argparse
import time
from typing import List

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


from Agent.knowledge_base.db.store import KnowledgeStore, DEFAULT_DB_PATH
from Agent.knowledge_base.ingest.embeddings import EmbeddingEngine
from Agent.knowledge_base.ingest.code_splitter import CodeSplitter
from Agent.knowledge_base.ingest.doc_distiller import DocDistiller
from Agent.knowledge_base.ingest.run_ingester import RunIngester
from Agent.knowledge_base.ingest.plugins import PDBStructurePlugin
from Agent.knowledge_base.search.hybrid_retriever import HybridRetriever
from Agent.knowledge_base.search.reranker import Reranker
from Agent.knowledge_base.agent.executor import KnowledgeExecutor
from Agent.knowledge_base.agent.context_generator import AgentContextGenerator
from Agent.knowledge_base.mcp.server import MCPServer


def run_ingest(workspace_dir: str = ".", db_path: str = DEFAULT_DB_PATH):
    print(f"=== Starting Incremental Ingestion for Workspace: {os.path.abspath(workspace_dir)} ===")

    store = KnowledgeStore(db_path)
    embedder = EmbeddingEngine()
    code_splitter = CodeSplitter(embedder)
    doc_distiller = DocDistiller(embedder)
    run_ingester = RunIngester(embedder)
    pdb_plugin = PDBStructurePlugin(embedder)

    total_files_scanned = 0
    total_files_updated = 0
    total_chunks_written = 0

    start_time = time.time()

    # Universal repository scanner — covers all common project layouts:
    # Python (src/, scripts/), TypeScript/JS (src/, lib/), Rust (src/, crates/),
    # Go (cmd/, internal/, pkg/), Java (src/main/), generic (app/, lib/, core/)
    UNIVERSAL_SCAN_DIRS = [
        # Common source roots
        "src", "lib", "app", "core", "pkg", "cmd", "internal",
        "crates", "packages",
        # Python-specific
        "scripts", "utils",
        # Test directories
        "tests", "test", "spec",
        # Documentation and config
        "docs", "config",
        # Project root files
        "code.md", "README.md", "config.yaml", "config.yml",
        "utils.py", "main.py", "main.ts", "main.go", "main.rs",
        # Agent memory
        "Agent",
        # Data I/O
        "inputs", "outputs",
    ]

    # Also auto-discover top-level directories not in the explicit list
    try:
        top_entries = os.listdir(workspace_dir)
        for entry in top_entries:
            full_entry = os.path.join(workspace_dir, entry)
            # Skip hidden dirs, known non-source dirs
            skip = {".git", ".sherlock", "node_modules", "__pycache__", "venv",
                    ".venv", "target", "dist", "build", ".idea", ".vscode"}
            if entry.startswith(".") or entry in skip:
                continue
            if os.path.isdir(full_entry) and entry not in UNIVERSAL_SCAN_DIRS:
                UNIVERSAL_SCAN_DIRS.append(entry)
    except Exception:
        pass

    scan_paths = [p for p in UNIVERSAL_SCAN_DIRS]


    active_sources: List[str] = []

    for item in scan_paths:
        full_p = os.path.join(workspace_dir, item)
        if not os.path.exists(full_p):
            continue

        files_to_process: List[str] = []
        if os.path.isfile(full_p):
            files_to_process.append(full_p)
        else:
            for root, _, files in os.walk(full_p):
                for f in files:
                    files_to_process.append(os.path.join(root, f))

        for file_path in files_to_process:
            rel_path = os.path.relpath(file_path, workspace_dir).replace("\\", "/")
            total_files_scanned += 1

            if file_path.endswith((".pyc", ".png", ".jpg", ".zip", ".exe", ".dll", ".db")):
                continue

            active_sources.append(rel_path)

            try:
                if rel_path.endswith(".py"):
                    chash, chunks = code_splitter.process_python_file(file_path, rel_path)
                    if not store.is_source_current(rel_path, chash):
                        store.upsert_source_chunks(rel_path, "code", chunks, chash)
                        total_files_updated += 1
                        total_chunks_written += len(chunks)

                elif rel_path.endswith(".md"):
                    chash, chunks = doc_distiller.process_markdown_file(file_path, rel_path)
                    if not store.is_source_current(rel_path, chash):
                        store.upsert_source_chunks(rel_path, "doc", chunks, chash)
                        total_files_updated += 1
                        total_chunks_written += len(chunks)

                elif pdb_plugin.can_handle(file_path):
                    chash, chunks = pdb_plugin.process_source(file_path, rel_path)
                    if not store.is_source_current(rel_path, chash):
                        store.upsert_source_chunks(rel_path, "input_structure", chunks, chash)
                        total_files_updated += 1
                        total_chunks_written += len(chunks)

                elif rel_path.endswith((".json", ".csv", ".yaml", ".log", ".txt")):
                    chash, chunks = run_ingester.process_run_file(file_path, rel_path)
                    if not store.is_source_current(rel_path, chash):
                        store.upsert_source_chunks(rel_path, "run_log", chunks, chash)
                        total_files_updated += 1
                        total_chunks_written += len(chunks)

            except Exception as e:
                print(f"Warning: Failed to ingest {rel_path}: {e}")

    pruned_count = store.prune_obsolete_sources(active_sources)

    elapsed = time.time() - start_time
    print(f"\nIngestion Complete in {elapsed:.2f}s!")
    print(f"Scanned: {total_files_scanned} files | Updated: {total_files_updated} files | Pruned Obsolete: {pruned_count} files | New Chunks: {total_chunks_written}")


def run_reindex(workspace_dir: str = ".", db_path: str = DEFAULT_DB_PATH):
    print(f"=== Wiping Knowledge Base and Running Full Re-index ===")
    store = KnowledgeStore(db_path)
    store.clear_all_data()
    run_ingest(workspace_dir, db_path)


def run_query(query: str, db_path: str = DEFAULT_DB_PATH, project: str = "OneClickDock"):
    store = KnowledgeStore(db_path)
    embedder = EmbeddingEngine()
    retriever = HybridRetriever(store, embedder)
    reranker = Reranker(store)
    executor = KnowledgeExecutor(store, retriever, reranker)

    res = executor.execute_and_synthesize(query, project_scope=project)

    print("\n" + "="*80)
    print(f"Planner Reasoning: {res['planner']['reasoning']}")
    print("="*80)
    print(res["answer"])
    print("="*80 + "\n")


def print_status(db_path: str = DEFAULT_DB_PATH):
    store = KnowledgeStore(db_path)
    sources = store.get_all_sources()

    print(f"=== Knowledge Base Status ({db_path}) ===")
    print(f"Total Synced Sources: {len(sources)}")
    print("-" * 60)
    print(f"{'Source ID':<45} | {'Type':<12} | {'Chunks':<6}")
    print("-" * 60)
    for s in sources[:30]:
        print(f"{s['source_id']:<45} | {s['source_type']:<12} | {s['chunk_count']:<6}")
    if len(sources) > 30:
        print(f"... and {len(sources) - 30} more sources.")


def run_context(target: str, db_path: str = DEFAULT_DB_PATH, project: str = "OneClickDock"):
    store = KnowledgeStore(db_path)
    embedder = EmbeddingEngine()
    retriever = HybridRetriever(store, embedder)
    reranker = Reranker(store)
    gen = AgentContextGenerator(store, retriever, reranker)

    ctx_markdown = gen.generate_preflight_context(target, project_scope=project)
    print(ctx_markdown)


def main():
    parser = argparse.ArgumentParser(description="OneClickDock Knowledge Base CLI")
    subparsers = parser.add_subparsers(dest="command")

    ingest_p = subparsers.add_parser("ingest", help="Run incremental ingestion")
    ingest_p.add_argument("--workspace", default=".", help="Workspace root directory")
    ingest_p.add_argument("--db", default=DEFAULT_DB_PATH, help="Database file path")

    query_p = subparsers.add_parser("query", help="Query the knowledge base")
    query_p.add_argument("query_text", type=str, help="Natural language query")
    query_p.add_argument("--project", default="OneClickDock", help="Project scope")
    query_p.add_argument("--db", default=DEFAULT_DB_PATH, help="Database file path")

    context_p = subparsers.add_parser("context", help="Generate pre-flight context bundle for AI agents")
    context_p.add_argument("target", type=str, help="Target file path, function name, or WP ID")
    context_p.add_argument("--project", default="OneClickDock", help="Project scope")
    context_p.add_argument("--db", default=DEFAULT_DB_PATH, help="Database file path")

    reindex_p = subparsers.add_parser("reindex", help="Wipe database and perform a clean full re-index")
    reindex_p.add_argument("--workspace", default=".", help="Workspace root directory")
    reindex_p.add_argument("--db", default=DEFAULT_DB_PATH, help="Database file path")

    status_p = subparsers.add_parser("status", help="Print knowledge base statistics")
    status_p.add_argument("--db", default=DEFAULT_DB_PATH, help="Database file path")

    mcp_p = subparsers.add_parser("mcp", help="Run MCP stdio server")
    mcp_p.add_argument("--db", default=DEFAULT_DB_PATH, help="Database file path")

    args = parser.parse_args()

    if args.command == "ingest":
        run_ingest(args.workspace, args.db)
    elif args.command == "reindex":
        run_reindex(args.workspace, args.db)
    elif args.command == "query":
        run_query(args.query_text, args.db, args.project)
    elif args.command == "context":
        run_context(args.target, args.db, args.project)
    elif args.command == "status":
        print_status(args.db)
    elif args.command == "mcp":
        server = MCPServer(args.db)
        server.run_stdio_loop()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
