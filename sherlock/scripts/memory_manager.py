#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sherlock Memory Manager v5.0 — Skorlu Hafıza + FIFO Enforcement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Agent/memory.md satır bütçesini (<=1000) icra eder.
- Aşımda en eski OPERASYONEL kaydı siler; arşive taşır (asla yok etmez).
- Her ders için skor takip eder: +kullanıldı / -yanlışladı.
- 3 kez yanlışlanan ders DEPRECATED damgası yer.

Kullanım:
  python memory_manager.py <workspace> [--budget 1000] [--prune] [--report]
  python memory_manager.py <workspace> --score <ders_id> --hit   # ders doğrulandı
  python memory_manager.py <workspace> --score <ders_id> --miss  # ders yanlışlandı
"""

import os
import re
import sys
import shutil
import datetime
import argparse

try:
    from sherlock_helpers import utc_stamp as _utc_stamp
except ImportError:
    from scripts.sherlock_helpers import utc_stamp as _utc_stamp

MEMORY_BUDGET_DEFAULT = 1000
SCORE_RE = re.compile(r"<!--\s*score:(?P<id>[A-Za-z0-9\-_]+)\s+uses:(?P<uses>\d+)\s+fails:(?P<fails>\d+)\s+status:(?P<status>[A-Z_]+)\s*-->")
DEPRECATED_AFTER_FAILS = 3


def find_memory(workspace: str) -> str:
    p = os.path.join(os.path.abspath(workspace), "Agent", "memory.md")
    return p


def count_lines(path: str) -> int:
    """Public yardımcı (Faz D4 M4): workspace-içi çağrısı yok ama dış tooling için stabil uç — SİLME."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return sum(1 for _ in f)


def ensure_score_tags(text: str) -> str:
    """Skor etiketi olmayan ders başlıklarına otomatik etiket ekler."""
    lines = text.splitlines()
    out = []
    counter = 0
    for line in lines:
        out.append(line)
        # Ders başlıkları: '### BRAVE-' veya numaralı dersler
        if re.match(r"^###\s+(BRAVE-|DERS-|LESSON-)", line) and "score:" not in line:
            counter += 1
            tag = f"<!-- score:L{counter:03d} uses:0 fails:0 status:ACTIVE -->"
            # Sonraki satırda etiket yoksa ekle
            out.append(tag)
    return "\n".join(out)


def parse_scores(text: str):
    return list(SCORE_RE.finditer(text))


def apply_score_op(text: str, lesson_id: str, hit: bool) -> str:
    def repl(m):
        if m.group("id") != lesson_id:
            return m.group(0)
        uses = int(m.group("uses")) + (1 if hit else 0)
        fails = int(m.group("fails")) + (0 if hit else 1)
        status = "DEPRECATED" if fails >= DEPRECATED_AFTER_FAILS else m.group("status")
        if status == "ACTIVE" and fails >= DEPRECATED_AFTER_FAILS:
            status = "DEPRECATED"
        return f"<!-- score:{lesson_id} uses:{uses} fails:{fails} status:{status} -->"
    new_text, n = SCORE_RE.subn(repl, text)
    if n == 0:
        print(f"[MEMORY] WARN: ders bulunamadı: {lesson_id}")
    else:
        print(f"[MEMORY] {'HIT' if hit else 'MISS'} işlendi: {lesson_id}")
    return new_text


def prune_memory(workspace: str, budget: int = MEMORY_BUDGET_DEFAULT) -> dict:
    mem_path = find_memory(workspace)
    if not os.path.exists(mem_path):
        return {"status": "SKIPPED", "reason": f"memory.md yok: {mem_path}"}
    with open(mem_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    # Önce skor etiketlerini güvenceye al
    text = ensure_score_tags(text)
    lines = text.splitlines()
    total = len(lines)
    print(f"[MEMORY] Satır: {total} / bütçe: {budget}")
    if total <= budget:
        # Etiket güncellemesi varsa yaz
        with open(mem_path, "w", encoding="utf-8") as f:
            f.write(text + ("\n" if not text.endswith("\n") else ""))
        return {"status": "OK", "lines": total, "budget": budget, "pruned": 0}

    # Arşiv klasörü
    archive_dir = os.path.join(os.path.abspath(workspace), "Agent", "memory_archive")
    os.makedirs(archive_dir, exist_ok=True)
    stamp = _utc_stamp()
    archive_path = os.path.join(archive_dir, f"memory_archive_{stamp}.md")

    # Korunacak başlık: ilk 45 satır (değişmezler + şema) — geri kalan operasyonel
    header_keep = 45
    excess = total - budget
    # En eski operasyonel bloktan kes: header sonrası ilk `excess` satır
    archived = lines[header_keep:header_keep + excess]
    remaining = lines[:header_keep] + lines[header_keep + excess:]

    # DEPRECATED dersleri öncelikli buda: kalan içinde DEPRECATED varsa onları da arşive öner
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(f"# Memory Archive {stamp}\n\n")
        f.write(f"Kaynak: {mem_path}\nBudanan satır: {excess}\n\n")
        f.write("\n".join(archived) + "\n")
    with open(mem_path, "w", encoding="utf-8") as f:
        f.write("\n".join(remaining) + "\n")
    print(f"[MEMORY] Budandi: {excess} satir -> {archive_path}")
    print(f"[MEMORY] Yeni satır: {len(remaining)}")
    return {"status": "PRUNED", "lines": len(remaining), "budget": budget,
            "pruned": excess, "archive": archive_path}


def report_memory(workspace: str, budget: int = MEMORY_BUDGET_DEFAULT) -> dict:
    mem_path = find_memory(workspace)
    if not os.path.exists(mem_path):
        return {"status": "SKIPPED", "reason": "memory.md yok"}
    with open(mem_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    lines = len(text.splitlines())
    scores = parse_scores(text)
    active = sum(1 for m in scores if m.group("status") == "ACTIVE")
    deprecated = sum(1 for m in scores if m.group("status") == "DEPRECATED")
    print(f"[MEMORY-REPORT] Satır: {lines}/{budget} | ders: {len(scores)} | aktif: {active} | deprecated: {deprecated}")
    for m in scores:
        print(f"  - {m.group('id')}: uses={m.group('uses')} fails={m.group('fails')} status={m.group('status')}")
    if lines > budget:
        print(f"[MEMORY-REPORT] UYARI: bütçe aşıldı, --prune çalıştırın.")
    return {"status": "OK", "lines": lines, "budget": budget,
            "lessons": len(scores), "active": active, "deprecated": deprecated}


def main():
    ap = argparse.ArgumentParser(description="Sherlock Memory Manager v5.0")
    ap.add_argument("workspace", nargs="?", default=".", help="Hedef workspace")
    ap.add_argument("--budget", type=int, default=MEMORY_BUDGET_DEFAULT)
    ap.add_argument("--prune", action="store_true", help="Bütçe aşımını buda + arşivle")
    ap.add_argument("--report", action="store_true", help="Sadece raporla")
    ap.add_argument("--score", default=None, help="Ders ID (örn. L001)")
    ap.add_argument("--hit", action="store_true", help="Ders doğrulandı")
    ap.add_argument("--miss", action="store_true", help="Ders yanlışlandı")
    args = ap.parse_args()

    mem_path = find_memory(args.workspace)
    if args.score:
        if not os.path.exists(mem_path):
            print(f"[MEMORY] FAIL: {mem_path} yok");
            sys.exit(1)
        with open(mem_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        text = apply_score_op(text, args.score, hit=args.hit and not args.miss)
        with open(mem_path, "w", encoding="utf-8") as f:
            f.write(text)
        sys.exit(0)
    if args.prune:
        res = prune_memory(args.workspace, budget=args.budget)
        print("Result:", res)
        sys.exit(0)
    # varsayılan: rapor
    res = report_memory(args.workspace, budget=args.budget)
    print("Result:", res)


if __name__ == "__main__":
    main()
