#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sherlock Approved Evolution Engine v5.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Onaylı evrim: otomatik yazma YOK.
1. code.md + Agent/memory.md okur (memory skorları dahil).
2. Şablonla karşılaştırır, genellenebilir adayları skorlar.
3. .sherlock/evolution/<tarih>-candidates.md üretir → Lead LLM + insan onayı.
4. Onaylanan aday --apply-approved <candidate_id> ile yedekli uygulanır.

Kullanım:
  python autonomous_evolution.py <workspace>                       # aday tara + dosya üret
  python autonomous_evolution.py <workspace> --apply-approved E001  # onaylıyı uygula
  python autonomous_evolution.py <workspace> --list                 # adayları listele
"""

import sys
import os
import re
import datetime
import hashlib
import shutil

try:
    from sherlock_helpers import sha12 as _sha12, utc_stamp as _utc_stamp
except ImportError:
    from scripts.sherlock_helpers import sha12 as _sha12, utc_stamp as _utc_stamp

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
TEMPLATES_AGENT_DIR = os.path.join(SKILL_DIR, "templates", "agent")
CODE_MD_TPL = os.path.join(TEMPLATES_AGENT_DIR, "code.md.tpl")
MEMORY_MD_TPL = os.path.join(TEMPLATES_AGENT_DIR, "memory.md.tpl")
GLOBAL_SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")

ENGINEERING_KWS = ["fail", "test", "module", "memory", "rollback", "atomic",
                   "duplik", "dup", "clean", "solid", "yalnız", "kural", "yasa",
                   "ssot", "consolid", "graphify", "coverage", "falsifier", "verdict"]


def extract_project_rules(code_md_path: str) -> list:
    if not os.path.exists(code_md_path):
        return []
    with open(code_md_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    rules = []
    for line in text.splitlines():
        s = line.strip()
        if re.match(r"^(\d+\.|\-|\*)\s+\*\*", s) or "Yasa" in s or "Kural" in s:
            rules.append(s)
    return rules


def extract_memory_lessons(memory_path: str) -> list:
    """memory.md derslerini skor etiketleriyle birlikte çıkarır."""
    if not os.path.exists(memory_path):
        return []
    with open(memory_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    lessons = []
    # Başlık + skor etiketi desenini yakala
    pattern = re.compile(
        r"^(###\s+.+)$\s*^<!--\s*score:(?P<id>[A-Za-z0-9\-_]+)\s+uses:(?P<uses>\d+)\s+fails:(?P<fails>\d+)\s+status:(?P<status>[A-Z_]+)\s*-->",
        re.MULTILINE)
    for m in pattern.finditer(text):
        lessons.append({
            "title": m.group(1).strip(),
            "id": m.group("id"),
            "uses": int(m.group("uses")),
            "fails": int(m.group("fails")),
            "status": m.group("status"),
        })
    return lessons


def score_rule(rule: str, lesson_support: int = 0) -> dict:
    base = sum(1 for kw in ENGINEERING_KWS if kw in rule.lower())
    # Genellenebilirlik cezası: dosya-spesifik veya URL içeriyorsa düşür
    has_file_ref = bool(re.search(r'[\w\-\.\/\\]+\.(py|js|ts|rs|go|cpp|c|java|yaml|toml|json|md)\b', rule))
    has_local_url = bool(re.search(r'https?://|localhost|127\.0\.0\.1', rule))
    penalty = (2 if has_file_ref else 0) + (2 if has_local_url else 0)
    total = base + min(lesson_support, 3) - penalty
    if total >= 3:
        decision = "READY_FOR_APPROVAL"
    elif total >= 1:
        decision = "CANDIDATE_FOR_LLM_REVIEW"
    else:
        decision = "LOCAL_ONLY_LIKELY"
    return {"score": total, "base": base, "lesson_support": lesson_support,
            "penalty": penalty, "decision": decision}


def evaluate_and_evolve_skill(workspace_root: str) -> dict:
    workspace_root = os.path.abspath(workspace_root)
    local_code_md = os.path.join(workspace_root, "code.md")
    local_memory_md = os.path.join(workspace_root, "Agent", "memory.md")

    if not os.path.exists(local_code_md):
        return {"status": "SKIPPED", "reason": "No local code.md found."}

    print(f"=== [SHERLOCK-EVOLUTION-v5] Scanning: {workspace_root} ===")

    with open(local_code_md, "r", encoding="utf-8", errors="replace") as f:
        local_code_text = f.read()
    with open(CODE_MD_TPL, "r", encoding="utf-8", errors="replace") as f:
        tpl_code_text = f.read()

    local_rules = extract_project_rules(local_code_md)
    tpl_rules = extract_project_rules(CODE_MD_TPL)
    lessons = extract_memory_lessons(local_memory_md)
    active_lessons = [l for l in lessons if l["status"] == "ACTIVE"]

    print(f"  [*] Kurallar: {len(local_rules)} | memory dersi: {len(lessons)} (aktif: {len(active_lessons)})")

    novel_rules = []
    for r in local_rules:
        clean_r = re.sub(r"[^\w\s]", "", r).lower()
        if not any(clean_r[:40] in re.sub(r"[^\w\s]", "", tr).lower() for tr in tpl_rules):
            novel_rules.append(r)

    # Memory'den tekrar eden kalıplar: aynı anahtar kelime ≥2 derste geçiyorsa destek say
    evolution_log = []
    for idx, rule in enumerate(novel_rules, start=1):
        keywords = set(re.findall(r"[a-zçğıöşü]{4,}", rule.lower()))
        support = sum(1 for l in active_lessons
                      if any(k in l["title"].lower() for k in list(keywords)[:6]))
        s = score_rule(rule, lesson_support=support)
        cid = f"E{idx:03d}"
        evolution_log.append({
            "id": cid,
            "rule": rule,
            "memory_support": support,
            **s,
            "target": suggest_target(rule),
            "risk": assess_risk(rule),
            "hash": _sha12(rule),
        })
        print(f"  [+] {cid}: score={s['score']} decision={s['decision']} :: {rule[:90]}")

    # Aday dosyasını yaz
    evo_dir = os.path.join(workspace_root, ".sherlock", "evolution")
    os.makedirs(evo_dir, exist_ok=True)
    stamp = _utc_stamp()
    cand_path = os.path.join(evo_dir, f"{stamp}-candidates.md")
    with open(cand_path, "w", encoding="utf-8") as f:
        f.write(f"# Sherlock Evrim Adayları — {stamp}\n\n")
        f.write(f"Workspace: {workspace_root}\nKural adayı: {len(novel_rules)} | memory dersi: {len(lessons)}\n\n")
        f.write("> **Onaylı evrim:** bu dosya sadece öneridir. Hiçbir dosya otomatik yazılmaz.\n")
        f.write("> Onay için: `python autonomous_evolution.py <workspace> --apply-approved <ID>`\n\n")
        for e in evolution_log:
            f.write(f"## {e['id']} — {e['decision']} (skor {e['score']})\n")
            f.write(f"- Kural: {e['rule']}\n")
            f.write(f"- Memory desteği: {e['memory_support']} | base:{e['base']} ceza:{e['penalty']}\n")
            f.write(f"- Önerilen hedef: `{e['target']}`\n")
            f.write(f"- Risk: {e['risk']}\n")
            f.write(f"- Hash: `{e['hash']}`\n\n")

    ready = sum(1 for e in evolution_log if e["decision"] == "READY_FOR_APPROVAL")
    print(f"  [=] Aday dosyası: {cand_path}")
    return {"status": "COMPLETED", "candidates_file": cand_path,
            "novel_rules_evaluated": len(novel_rules),
            "ready_for_approval": ready,
            "evolution_log": evolution_log}


def suggest_target(rule: str) -> str:
    rl = rule.lower()
    if any(k in rl for k in ["memory", "skor", "fifo", "ders"]):
        return "templates/agent/memory.md.tpl"
    if any(k in rl for k in ["test", "coverage", "mock"]):
        return "roles/sherlock-code-analyst.toml (Lens C)"
    if any(k in rl for k in ["duplik", "dup", "consolid", "dead"]):
        return "references/brave-consolidation.md"
    if any(k in rl for k in ["literat", "pubmed", "doi", "context7"]):
        return "references/evidence-standards.md"
    if any(k in rl for k in ["graph", "god", "community"]):
        return "references/graphify-integration.md"
    return "SKILL.md (Lead Architect bölümü)"


def assess_risk(rule: str) -> str:
    rl = rule.lower()
    if any(k in rl for k in ["sil", "delete", "rollback", "otomatik"]):
        return "YÜKSEK — otomatik icra içeriyor, onayda rewire/test şartı ara"
    if len(rule) < 40:
        return "DÜŞÜK — ama çok kısa, genellenebilirliği şüpheli"
    return "ORTA — standart onay yeterli"


def list_candidates(workspace_root: str):
    evo_dir = os.path.join(os.path.abspath(workspace_root), ".sherlock", "evolution")
    if not os.path.isdir(evo_dir):
        print("[EVOLVE] Aday yok. Önce tarama yapın.");
        return
    for fn in sorted(os.listdir(evo_dir)):
        print(os.path.join(evo_dir, fn))


def apply_approved(workspace_root: str, cid: str) -> dict:
    """Onaylı adayı uygular: yedek + minimal yama. Hedef dosyayı ezberden yazmaz,
    adayı ilgili hedefin SONUNA 'Evrim Kaydı' olarak ekler (insan son rötuşu yapar)."""
    evo_dir = os.path.join(os.path.abspath(workspace_root), ".sherlock", "evolution")
    if not os.path.isdir(evo_dir):
        return {"status": "FAIL", "reason": "evolution klasörü yok, önce tarama yapın"}
    # En yeni aday dosyasını bul
    files = sorted([os.path.join(evo_dir, fn) for fn in os.listdir(evo_dir) if fn.endswith("-candidates.md")])
    if not files:
        return {"status": "FAIL", "reason": "aday dosyası yok"}
    cand_path = files[-1]
    with open(cand_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    m = re.search(rf"##\s+{re.escape(cid)}\s+—\s+(\S+).*?- Kural:\s*(.+)\n- Memory.*?`(.*?)`",
                  text, re.DOTALL)
    if not m:
        return {"status": "FAIL", "reason": f"{cid} bulunamadı ({cand_path})"}
    decision, rule, target = m.group(1), m.group(2).strip(), m.group(3).strip()
    if decision == "LOCAL_ONLY_LIKELY":
        return {"status": "REFUSED", "reason": f"{cid} genellenebilir değil ({decision})"}

    # Hedef yolu çözümle
    target_map = {
        "templates/agent/memory.md.tpl": os.path.join(TEMPLATES_AGENT_DIR, "memory.md.tpl"),
        "references/brave-consolidation.md": os.path.join(SKILL_DIR, "references", "brave-consolidation.md"),
        "references/evidence-standards.md": os.path.join(SKILL_DIR, "references", "evidence-standards.md"),
        "references/graphify-integration.md": os.path.join(SKILL_DIR, "references", "graphify-integration.md"),
    }
    dest = target_map.get(target, GLOBAL_SKILL_MD)
    # Yedek
    bak = dest + f".evolve-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
    shutil.copy2(dest, bak)
    with open(dest, "r", encoding="utf-8", errors="replace") as f:
        orig = f.read()
    stamp = datetime.datetime.now().strftime("%Y-%m-%d")
    addition = (f"\n\n<!-- SHERLOCK-EVOLVE {cid} {stamp} -->\n"
                f"> Evrim kaydı ({cid}, {decision}): {rule}\n")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(orig.rstrip() + "\n" + addition)
    print(f"[EVOLVE] Uygulandı: {cid} → {dest}\n[EVOLVE] Yedek: {bak}")
    return {"status": "APPLIED", "candidate": cid, "dest": dest, "backup": bak}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Sherlock Approved Evolution Engine v5.0")
    ap.add_argument("target", nargs="?", default=".", help="Target workspace")
    ap.add_argument("--list", dest="list_only", action="store_true")
    ap.add_argument("--apply-approved", default=None, metavar="E001")
    args = ap.parse_args()
    if args.list_only:
        list_candidates(args.target)
    elif args.apply_approved:
        print("Result:", apply_approved(args.target, args.apply_approved))
    else:
        print("Result:", {k: v for k, v in evaluate_and_evolve_skill(args.target).items()
                          if k != "evolution_log"})
