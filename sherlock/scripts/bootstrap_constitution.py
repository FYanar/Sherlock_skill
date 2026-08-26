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


# ── 10 Evrensel Mühendislik Yasası (ASCII-safe fingerprints) ─────────────────
# Fingerprints use ASCII-only keywords to avoid encoding issues on Windows cp1254.
# A law is "present" when its Yasa N label AND one ASCII fingerprint are both found.
_LAWS = [
    ("Yasa 1",  "Katı Hiyerarşi",               "Kullanici Talimati",   "code.md"),
    ("Yasa 2",  "Fail-Closed",                   "Fail-Closed",          "Sessiz"),
    ("Yasa 3",  "Duplikasyon Kalkani",            "AST",                  "AST"),
    ("Yasa 4",  "ACID Transaction",               "ACID",                 "Rollback"),
    ("Yasa 5",  "Sherlock",                       "Sherlock",             "6-Ajan"),
    ("Yasa 6",  "Kismi Iyilestirme",              "baseline",             "Artimli"),
    ("Yasa 7",  "Zero Workspace",                 "Zero Workspace",       "Kirliligi"),
    ("Yasa 8",  "Hedefli Olu Kod",                "FunctionDef",          "Temizlik"),
    ("Yasa 9",  "Atomik Rollback",                "Atomik",               ".bak"),
    ("Yasa 10", "Otonom Hakem",                   "Skil",                 "otonom"),
]


def audit_constitution(workspace_root: str, repair: bool = False) -> bool:
    """
    --audit-constitution: Reads code.md and checks which of the 10 Universal
    Engineering Laws are present. Reports missing/drifted laws and optionally
    repairs the laws section using the canonical template.

    Returns True if code.md is fully compliant, False otherwise.
    """
    workspace_root = os.path.abspath(workspace_root)
    code_md_path = os.path.join(workspace_root, "code.md")

    print(f"=== [SHERLOCK-AUDIT] Checking constitution: {code_md_path} ===")

    if not os.path.exists(code_md_path):
        print(f"[AUDIT] FAIL: code.md not found at {code_md_path}")
        if repair:
            print("[AUDIT] Repair requested — bootstrapping constitution from scratch.")
            detected_lang = detect_language(workspace_root)
            bootstrap_project(workspace_root, language=detected_lang)
            return True
        return False

    with open(code_md_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    missing = []
    present = []
    content_lower = content.lower()
    for entry in _LAWS:
        law_id, law_name, fp1, fp2 = entry
        # Case-insensitive ASCII match: law ID present AND at least one fingerprint found
        if law_id in content and (fp1.lower() in content_lower or fp2.lower() in content_lower):
            present.append(law_id)
        else:
            missing.append((law_id, law_name, fp1))


    print(f"\n[AUDIT] Laws present ({len(present)}/10): {', '.join(present) or 'NONE'}")

    if missing:
        print(f"\n[AUDIT] WARNING: Missing / drifted laws ({len(missing)}):")
        for law_id, law_name, fp in missing:
            print(f"  MISSING: {law_id} -- {law_name}  (expected keyword: '{fp}')")
    else:
        print("\n[AUDIT] OK: All 10 Universal Engineering Laws are present. Constitution is compliant.")
        return True

    if not repair:
        print("\n[AUDIT] Run with --audit-constitution --repair to patch missing laws.")
        return False

    # Repair: inject or replace the Laws section using the template
    print("\n[AUDIT] Repairing: patching laws section from canonical template...")
    code_md_tpl = os.path.join(TEMPLATES_AGENT_DIR, "code.md.tpl")
    if not os.path.exists(code_md_tpl):
        print(f"[AUDIT] FAIL: Template not found at {code_md_tpl}. Cannot repair.")
        return False

    with open(code_md_tpl, "r", encoding="utf-8") as f:
        tpl_content = f.read()

    # Extract the laws section from the template
    tpl_laws_start = tpl_content.find("## 7. 10 Evrensel")
    if tpl_laws_start == -1:
        print("[AUDIT] FAIL: Could not find laws section in template.")
        return False
    tpl_laws = tpl_content[tpl_laws_start:]

    # In target code.md, find and replace the laws section
    laws_start = content.find("## 7. 10 Evrensel")
    if laws_start != -1:
        next_section = content.find("\n## ", laws_start + 10)
        if next_section != -1:
            restored = content[:laws_start] + tpl_laws + "\n\n" + content[next_section:].lstrip("# ")
        else:
            restored = content[:laws_start] + tpl_laws
    else:
        restored = content.rstrip() + "\n\n" + tpl_laws

    # Atomic write with backup
    bak_path = code_md_path + ".sherlock-audit.bak"
    try:
        import shutil
        shutil.copy2(code_md_path, bak_path)
        with open(code_md_path, "w", encoding="utf-8") as f:
            f.write(restored)
        print(f"[AUDIT] OK: Laws section patched. Backup saved: {bak_path}")
        return True
    except Exception as e:
        print(f"[AUDIT] FAIL: Could not write repaired code.md: {e}")
        return False



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Sherlock Universal Phoenix Constitution Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python bootstrap_constitution.py ./my-project --name MyApp --language Rust\n"
            "  python bootstrap_constitution.py ./my-project --audit-constitution\n"
            "  python bootstrap_constitution.py ./my-project --audit-constitution --repair"
        )
    )
    parser.add_argument("target", nargs="?", default=".", help="Target workspace directory")
    parser.add_argument("--name", default=None, help="Project name (default: directory name)")
    parser.add_argument("--language", default=None, help="Primary language (auto-detected if omitted)")
    parser.add_argument("--desc", default="Universal Modular Software Project", help="Project description")
    parser.add_argument("--audit-constitution", action="store_true",
                        help="Audit code.md for the 10 Universal Engineering Laws instead of bootstrapping")
    parser.add_argument("--repair", action="store_true",
                        help="When used with --audit-constitution, patches missing laws from the canonical template")
    args = parser.parse_args()

    if args.audit_constitution:
        ok = audit_constitution(args.target, repair=args.repair)
        sys.exit(0 if ok else 1)
    else:
        detected_lang = args.language or detect_language(args.target)
        print(f"[SHERLOCK-INCEPTION] Language: {detected_lang} ({'provided' if args.language else 'auto-detected'})")
        bootstrap_project(args.target, project_name=args.name, language=detected_lang, project_desc=args.desc)

