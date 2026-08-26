#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sherlock Knowledge Base & MCP Auto-Installer Engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Automatically provisions Agent/knowledge_base/, tools/run_mcp.py, .mcp.json,
and global MCP configs in any workspace.
"""

import sys
import os
import shutil
import json
import subprocess

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_KB_DIR = os.path.join(SKILL_DIR, "templates", "knowledge_base")
TEMPLATES_TOOLS_DIR = os.path.join(SKILL_DIR, "templates", "tools")


def install_knowledge_base(workspace_root: str) -> bool:
    workspace_root = os.path.abspath(workspace_root)
    agent_dir = os.path.join(workspace_root, "Agent")
    kb_dir = os.path.join(agent_dir, "knowledge_base")
    tools_dir = os.path.join(workspace_root, "tools")
    run_mcp_path = os.path.join(tools_dir, "run_mcp.py")
    mcp_json_path = os.path.join(workspace_root, ".mcp.json")

    print(f"[SHERLOCK-KB] Auto-installing Knowledge Base subsystem into: {workspace_root}")

    # 1. Ensure directories
    os.makedirs(agent_dir, exist_ok=True)
    os.makedirs(tools_dir, exist_ok=True)

    # 2. Copy Knowledge Base module if missing or incomplete
    if not os.path.exists(kb_dir) or not os.path.exists(os.path.join(kb_dir, "cli.py")):
        if os.path.exists(TEMPLATES_KB_DIR):
            if os.path.exists(kb_dir):
                shutil.rmtree(kb_dir)
            shutil.copytree(
                TEMPLATES_KB_DIR,
                kb_dir,
                ignore=shutil.ignore_patterns("*.db", "*.pyc", "__pycache__")
            )
            print("[SHERLOCK-KB] Agent/knowledge_base/ successfully deployed from Sherlock templates.")
        else:
            print("[SHERLOCK-KB] ERROR: Templates directory not found at", TEMPLATES_KB_DIR)
            return False

    # 3. Deploy tools/run_mcp.py
    if not os.path.exists(run_mcp_path):
        template_run_mcp = os.path.join(TEMPLATES_TOOLS_DIR, "run_mcp.py")
        if os.path.exists(template_run_mcp):
            shutil.copy2(template_run_mcp, run_mcp_path)
        else:
            # Fallback code write
            with open(run_mcp_path, "w", encoding="utf-8") as f:
                f.write('''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Agent.knowledge_base.cli import main

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.append("mcp")
    main()
''')
        print("[SHERLOCK-KB] tools/run_mcp.py deployed.")

    # 4. Generate / MERGE .mcp.json (non-destructive: preserves existing MCP servers)
    workspace_forward = workspace_root.replace("\\", "/")
    project_name = os.path.basename(workspace_root).lower().replace(" ", "-")
    server_key = f"{project_name}-knowledge-base"
    new_server = {
        "command": "python",
        "args": [f"{workspace_forward}/tools/run_mcp.py", "mcp"],
        "env": {"PYTHONPATH": workspace_forward, "PYTHONUNBUFFERED": "1"}
    }
    if os.path.exists(mcp_json_path):
        try:
            with open(mcp_json_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = {}
    else:
        existing = {}
    existing.setdefault("mcpServers", {})
    existing["mcpServers"][server_key] = new_server
    with open(mcp_json_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
    print(f"[SHERLOCK-KB] .mcp.json merged at {mcp_json_path} (server: {server_key})")

    # 5. Run initial ingestion if database doesn't exist (FAIL-CLOSED per Yasa 2)
    db_path = os.path.join(kb_dir, "knowledge_base.db")
    if not os.path.exists(db_path):
        print("[SHERLOCK-KB] Building initial knowledge base index...")
        try:
            result = subprocess.run(
                [sys.executable, run_mcp_path, "ingest"],
                cwd=workspace_root, capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"[SHERLOCK-KB] FAIL: Ingestion failed (exit {result.returncode}).")
                print(f"[SHERLOCK-KB] stderr: {result.stderr[:400]}")
                print("[SHERLOCK-KB] Manually run: python tools/run_mcp.py ingest")
                print("\n" + "=" * 70)
                print(" [MCP-SETUP] KB KURULUMU KISMI TAMAMLANDI (INGEST HATASI)")
                print(" Ingestion başarısız. MCP aktif olmayacak.")
                print("=" * 70)
                return False
            print("[SHERLOCK-KB] Initial ingestion completed.")
        except FileNotFoundError:
            print("[SHERLOCK-KB] FAIL: run_mcp.py not found.")
            return False
        except Exception as e:
            print(f"[SHERLOCK-KB] FAIL: Unexpected error: {e}")
            return False

    # 6. Inform user about session reload
    print("\n" + "=" * 70)
    print(" [MCP-SETUP] BİLGİ TABANI VE .MCP.JSON BAŞARIYLA KURULDU!")
    print(" Lütfen MCP'nin (oneclickdock-knowledge-base) devreye girmesi için")
    print(" oturumu (IDE/Agent) tekrar başlatın (Reload / Restart Session).")
    print("=" * 70 + "\n")

    return True


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    install_knowledge_base(target)
