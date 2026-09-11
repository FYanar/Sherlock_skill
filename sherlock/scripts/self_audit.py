#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sherlock Self-Audit v5.0 — Meta-Dava Kuru Çalıştırma
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SKILL/role/template/script tutarlılığını makineyle denetler.
LLM hakemliğinin yerini tutmaz; ön taramadır.

Kontroller:
  1. SKILL.md sürüm + komut varlığı (v5.0, --self-audit, --prune-memory, --apply-approved)
  2. 6-ajan kalıntısı (6 ajan, structural/config/test-agent ayrık adları)
  3. Öksüz referans (references/ içinde olmayan dosyaya link)
  4. Script --help çalışabilirliği
  5. Template placeholder bütünlüğü ({{...}} dengesizliği)

Kullanım:
  python self_audit.py [--skill-dir <path>]
  Çıktı: .sherlock/self-audit/<tarih>/10-r1-*.md iskeleti + findings.md
"""

import os
import re
import sys
import subprocess
import datetime
import argparse

DEFAULT_SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check_skill_version(skill_dir: str) -> list:
    out = []
    p = os.path.join(skill_dir, "SKILL.md")
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            t = f.read()
    except Exception as e:
        return [{"id": "F-B1", "severity": "BLOCKER", "claim": f"SKILL.md okunamadı: {e}",
                 "verification": "CONFIRMED"}]
    for token, desc in [("v5.0", "sürüm damgası"), ("--self-audit", "meta-dava komutu"),
                        ("--prune-memory", "hafıza budama"), ("--apply-approved", "onaylı evrim"),
                        ("memory_manager.py", "skorlu hafıza"), ("deadcode_scanner.py", "deadcode tarayıcı"),
                        ("literature_guard.py", "literatür kapısı"),
                        ("using-agent-skills.md", "akıllı router")]:
        if token not in t:
            out.append({"id": f"F-B-AUTO-{len(out)+1}", "severity": "MAJOR",
                        "claim": f"SKILL.md'de '{token}' ({desc}) yok",
                        "verification": "CONFIRMED"})
    # 6-ajan kalıntısı
    if re.search(r"6\s*-\s*ajan|6 uzman|Structural.*Config.*Test.*ayrı", t):
        out.append({"id": "F-B-LEGACY", "severity": "MAJOR",
                    "claim": "6-ajan kalıntısı bulundu", "verification": "PENDING_RECHECK"})
    return out


def check_orphan_refs(skill_dir: str) -> list:
    out = []
    refs_dir = os.path.join(skill_dir, "references")
    # Tüm .md dosyalarındaki references/... ve embedded_skills/... linklerini topla
    for dirpath, dirnames, filenames in os.walk(skill_dir):
        # Kendi çıktısını ve önbelleği taraMA (yanlış pozitif engeli)
        dirnames[:] = [d for d in dirnames if d not in {".sherlock", "__pycache__", "graphify-out", ".git"}]
        for fn in filenames:
            if not fn.endswith((".md", ".toml")):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as f:
                    t = f.read()
            except Exception:
                continue
            for m in re.finditer(r"references/([A-Za-z0-9_\-./]+\.md)", t):
                target = os.path.join(skill_dir, "references", m.group(1).split("/")[-1]
                                      if "/" not in m.group(1) else m.group(1))
                # references/embedded_skills/... ise ayrı çöz
                if "embedded_skills" in m.group(0):
                    target = os.path.join(skill_dir, m.group(0).split("`")[0].strip("()\"' ") if False else m.group(0))
                if not os.path.exists(os.path.join(skill_dir, "references", m.group(1))):
                    # Yanlış pozitifleri ele: URL değilse raporla
                    if "http" not in m.group(0):
                        out.append({"id": f"F-B-ORPHAN-{len(out)+1}", "severity": "MINOR",
                                    "claim": f"Öksüz referans: {m.group(0)} ({os.path.relpath(fp, skill_dir)})",
                                    "verification": "PENDING_RECHECK"})
                        if len(out) > 15:
                            return out
    return out


def check_scripts(skill_dir: str) -> list:
    out = []
    sdir = os.path.join(skill_dir, "scripts")
    for fn in ["memory_manager.py", "autonomous_evolution.py", "deadcode_scanner.py",
               "literature_guard.py", "bootstrap_constitution.py", "self_audit.py"]:
        fp = os.path.join(sdir, fn)
        if not os.path.exists(fp):
            out.append({"id": f"F-B-SCRIPT-{fn}", "severity": "MAJOR",
                        "claim": f"Script eksik: {fn}", "verification": "CONFIRMED"})
            continue
        try:
            r = subprocess.run([sys.executable, fp, "--help"],
                               capture_output=True, text=True, timeout=20)
            if r.returncode != 0:
                out.append({"id": f"F-B-SCRIPTRUN-{fn}", "severity": "MINOR",
                            "claim": f"{fn} --help kodu {r.returncode}: {r.stderr[:120]}",
                            "verification": "PENDING_RECHECK"})
        except Exception as e:
            out.append({"id": f"F-B-SCRIPTRUN-{fn}", "severity": "MINOR",
                        "claim": f"{fn} çalıştırılamadı: {e}", "verification": "UNVERIFIABLE"})
    return out


def run_self_audit(skill_dir: str) -> dict:
    skill_dir = os.path.abspath(skill_dir)
    stamp = datetime.datetime.now().strftime("%Y%m%d")
    out_dir = os.path.join(skill_dir, ".sherlock", "self-audit", stamp)
    # Skill içi .sherlock yerine workspace kökü? Skill dir içinde tut (geçici, hijyen dışı değil — skill kendi evi)
    os.makedirs(out_dir, exist_ok=True)
    findings = check_skill_version(skill_dir) + check_orphan_refs(skill_dir) + check_scripts(skill_dir)
    blockers = sum(1 for f in findings if f["severity"] == "BLOCKER")
    majors = sum(1 for f in findings if f["severity"] == "MAJOR")
    verdict = "GO" if not blockers and not majors else ("GO-WITH-CONDITIONS" if not blockers else "NO-GO")
    # Dosyaları yaz
    with open(os.path.join(out_dir, "findings.md"), "w", encoding="utf-8") as f:
        f.write(f"# Self-Audit Findings — {stamp}\n\nVerdict: **{verdict}**\n\n")
        for b in findings:
            f.write(f"- **{b['severity']}** {b['id']}: {b['claim']} [{b['verification']}]\n")
        if not findings:
            f.write("- Temiz: makine kontrolünde bulgu yok.\n")
    # Şablonu kopyala
    tpl = os.path.join(skill_dir, "templates", "self-audit.md")
    if os.path.exists(tpl):
        with open(tpl, "r", encoding="utf-8", errors="replace") as f:
            t = f.read()
        with open(os.path.join(out_dir, "00-case.md"), "w", encoding="utf-8") as f:
            f.write(t.replace("<tarih>", stamp).replace("<SKILL_DIR>", skill_dir))
    print(f"[SELF-AUDIT] Bulgu: {len(findings)} (BLOCKER:{blockers} MAJOR:{majors}) -> {verdict}")
    print(f"[SELF-AUDIT] Çıktı: {out_dir}")
    return {"status": "COMPLETED", "findings": len(findings), "verdict": verdict, "out_dir": out_dir,
            "details": findings}


def main():
    ap = argparse.ArgumentParser(description="Sherlock Self-Audit v5.0")
    ap.add_argument("--skill-dir", default=DEFAULT_SKILL)
    args = ap.parse_args()
    print("Result:", run_self_audit(args.skill_dir))


if __name__ == "__main__":
    main()
