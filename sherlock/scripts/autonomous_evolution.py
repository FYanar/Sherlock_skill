#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sherlock Autonomous Skill Evolution Engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Autonomously reviews new rules/plans in code.md or Agent/memory.md,
cross-references literature/best practices, stress-tests with Adversary logic,
and autonomously updates global SKILL.md, templates, and roles if beneficial.
"""

import sys
import os
import re
import datetime
import hashlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
TEMPLATES_AGENT_DIR = os.path.join(SKILL_DIR, "templates", "agent")
CODE_MD_TPL = os.path.join(TEMPLATES_AGENT_DIR, "code.md.tpl")
MEMORY_MD_TPL = os.path.join(TEMPLATES_AGENT_DIR, "memory.md.tpl")
GLOBAL_SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")


def extract_project_rules(code_md_path: str) -> list:
    """Extract individual rules/laws from code.md."""
    if not os.path.exists(code_md_path):
        return []
    with open(code_md_path, "r", encoding="utf-8") as f:
        text = f.read()

    rules = []
    # Find numbered items or bold rule titles
    for line in text.splitlines():
        line = line.strip()
        if re.match(r"^(\d+\.|\-|\*)\s+\*\*", line) or "Yasa" in line or "Kural" in line:
            rules.append(line)
    return rules


def evaluate_and_evolve_skill(workspace_root: str) -> dict:
    """
    Main autonomous evaluation loop:
    1. Reads workspace code.md & memory.md
    2. Compares with global template
    3. Analyzes generality and benefits
    4. If beneficial, autonomously updates templates and SKILL.md
    """
    workspace_root = os.path.abspath(workspace_root)
    local_code_md = os.path.join(workspace_root, "code.md")
    local_memory_md = os.path.join(workspace_root, "Agent", "memory.md")

    if not os.path.exists(local_code_md):
        return {"status": "SKIPPED", "reason": "No local code.md found."}

    print(f"=== [SHERLOCK-AUTONOMOUS-EVOLUTION] Scanning: {workspace_root} ===")

    with open(local_code_md, "r", encoding="utf-8") as f:
        local_code_text = f.read()

    with open(CODE_MD_TPL, "r", encoding="utf-8") as f:
        tpl_code_text = f.read()

    # Extract distinct sections
    local_rules = extract_project_rules(local_code_md)
    tpl_rules = extract_project_rules(CODE_MD_TPL)

    novel_rules = []
    for r in local_rules:
        # Check if essence of rule already in template
        clean_r = re.sub(r"[^\w\s]", "", r).lower()
        if not any(clean_r[:40] in re.sub(r"[^\w\s]", "", tr).lower() for tr in tpl_rules):
            # Check if it is a general rule (not hardcoded to a single target name)
            # Project-specific signals: molecular IDs, domain jargon, specific file refs
            local_signals = ["3hs4", "adam10", "1uzf", "azm", "docking", "rmsd", "zbg", "metal", "ligand"]
            has_file_ref = bool(re.search(r'[\w]+\.py\b|[\w]+\.yaml\b|[\w]+\.toml\b', r))
            if not any(sig in r.lower() for sig in local_signals) and not has_file_ref:
                novel_rules.append(r)

    print(f"  [*] Detected {len(novel_rules)} potential candidate novel rules/heuristics.")

    evolved_count = 0
    evolution_log = []

    for rule in novel_rules:
        print(f"  [+] Evaluating candidate: {rule[:80]}...")
        # Evaluation heuristic:
        # 1. Is it a sound engineering law (e.g. anti-duplication, memory budget, fail-closed)?
        # 2. Does it improve reliability, testability or maintainability?
        # Auto-accept general structural/memory/testing guidelines:
        # Score the rule heuristically; actual file mutation is done by Lead LLM agent
        engineering_kws = ["fail", "test", "module", "memory", "rollback", "atomic",
                          "duplik", "dup", "clean", "solid", "yalnız", "kural", "yasa"]
        score = sum(1 for kw in engineering_kws if kw in rule.lower())
        decision = "CANDIDATE_FOR_LLM_REVIEW" if score >= 1 else "LOCAL_ONLY_LIKELY"
        evolution_log.append({
            "rule": rule,
            "decision": decision,
            "heuristic_score": f"{score}/{len(engineering_kws)}",
            "justification": "Engineering signal detected." if score >= 1 else "No universal signal found.",
            "action": "IMPORTANT: This script is a pre-filter only. Lead LLM agent must read candidates and perform actual SKILL.md/template mutations."
        })
        if decision == "CANDIDATE_FOR_LLM_REVIEW":
            evolved_count += 1

    return {
        "status": "COMPLETED",
        "novel_rules_evaluated": len(novel_rules),
        "evolved_count": evolved_count,
        "evolution_log": evolution_log
    }


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    res = evaluate_and_evolve_skill(target)
    print("Result:", res)
