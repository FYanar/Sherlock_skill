#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sherlock Universal Phoenix Constitution & Agent Inception Engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Provisions a canonical code.md, Agent/ directory, and Knowledge Base/MCP
for ANY software, data science, AI, or biological project.
"""

import sys
import os
import datetime
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
TEMPLATES_AGENT_DIR = os.path.join(SKILL_DIR, "templates", "agent")


def render_template(tpl_path: str, context: dict) -> str:
    with open(tpl_path, "r", encoding="utf-8") as f:
        content = f.read()
    for k, v in context.items():
        content = content.replace(f"{{{{{k}}}}}", str(v))
    return content


def bootstrap_project(
    workspace_root: str,
    project_name: str = None,
    project_desc: str = "Universal Modular Software Project",
    language: str = "Python"
) -> bool:
    workspace_root = os.path.abspath(workspace_root)
    if not project_name:
        project_name = os.path.basename(workspace_root) or "NewProject"

    now = datetime.datetime.now()
    created_date = now.strftime("%Y-%m-%d")
    date_slug = now.strftime("%Y%m%d")
    timestamp = now.isoformat()

    context = {
        "PROJECT_NAME": project_name,
        "PROJECT_DESCRIPTION": project_desc,
        "LANGUAGE": language,
        "CREATED_DATE": created_date,
        "DATE_SLUG": date_slug,
        "TIMESTAMP": timestamp,
        "PROJECT_SCOPE": "Core Module & Setup",
    }

    print(f"=== [SHERLOCK-INCEPTION] Bootstrapping Universal Constitution in: {workspace_root} ===")
    os.makedirs(workspace_root, exist_ok=True)
    agent_dir = os.path.join(workspace_root, "Agent")
    os.makedirs(agent_dir, exist_ok=True)

    # 1. Generate code.md
    code_md_tpl = os.path.join(TEMPLATES_AGENT_DIR, "code.md.tpl")
    target_code_md = os.path.join(workspace_root, "code.md")
    if not os.path.exists(target_code_md):
        rendered_code_md = render_template(code_md_tpl, context)
        with open(target_code_md, "w", encoding="utf-8") as f:
            f.write(rendered_code_md)
        print(f"  [+] Created canonical code.md at {target_code_md}")
    else:
        print(f"  [*] Existing code.md found; preserving.")

    # 2. Generate Agent files
    agent_files = [
        ("plan.md.tpl", "plan.md"),
        ("run_state.md.tpl", "run_state.md"),
        ("memory.md.tpl", "memory.md"),
        ("structure.md.tpl", "structure.md"),
        ("structure_inventory.md.tpl", "structure_inventory.md"),
        ("test_scenarios.md.tpl", "test_scenarios.md"),
    ]

    for tpl_file, out_file in agent_files:
        tpl_path = os.path.join(TEMPLATES_AGENT_DIR, tpl_file)
        target_path = os.path.join(agent_dir, out_file)
        if not os.path.exists(target_path):
            rendered = render_template(tpl_path, context)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(rendered)
            print(f"  [+] Created Agent/{out_file}")
        else:
            print(f"  [*] Existing Agent/{out_file} found; preserving.")

    # 3. Call Knowledge Base & MCP Provisioner
    kb_bootstrap = os.path.join(SCRIPT_DIR, "bootstrap_knowledge_base.py")
    if os.path.exists(kb_bootstrap):
        try:
            subprocess.run([sys.executable, kb_bootstrap, workspace_root], check=True)
        except Exception as e:
            print(f"  [!] KB bootstrap note: {e}")

    print("=== [SHERLOCK-INCEPTION] Project Constitution & Agent Infrastructure Fully Deployed! ===\n")
    return True


def detect_language(workspace_root: str) -> str:
    """Auto-detect primary programming language by file extension frequency."""
    ext_map = {
        ".rs": "Rust", ".go": "Go", ".ts": "TypeScript", ".tsx": "TypeScript",
        ".js": "JavaScript", ".jsx": "JavaScript", ".java": "Java",
        ".kt": "Kotlin", ".cs": "C#", ".cpp": "C++", ".c": "C",
        ".rb": "Ruby", ".php": "PHP", ".swift": "Swift", ".py": "Python",
        ".scala": "Scala", ".zig": "Zig", ".ex": "Elixir",
    }
    skip_dirs = {"node_modules", "__pycache__", "target", "dist", "build", "venv", ".venv", ".git"}
    counts = {}
    try:
        for dirpath, dirnames, filenames in os.walk(workspace_root):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in ext_map:
                    lang = ext_map[ext]
                    counts[lang] = counts.get(lang, 0) + 1
    except Exception:
        pass
    return max(counts, key=counts.get) if counts else "Python"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Sherlock Universal Phoenix Constitution Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python bootstrap_constitution.py ./my-project --name MyApp --language Rust"
    )
    parser.add_argument("target", nargs="?", default=".", help="Target workspace directory")
    parser.add_argument("--name", default=None, help="Project name (default: directory name)")
    parser.add_argument("--language", default=None, help="Primary language (auto-detected if omitted)")
    parser.add_argument("--desc", default="Universal Modular Software Project", help="Project description")
    args = parser.parse_args()
    detected_lang = args.language or detect_language(args.target)
    print(f"[SHERLOCK-INCEPTION] Language: {detected_lang} ({'provided' if args.language else 'auto-detected'})")
    bootstrap_project(args.target, project_name=args.name, language=detected_lang, project_desc=args.desc)
