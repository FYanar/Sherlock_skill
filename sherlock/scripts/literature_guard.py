#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sherlock Literature Guard v5.0 — Context7 + PubMed Kapısı
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Amaç: literatüre aykırı CONFIRMED'i imkansız kılmak.
- Kod/SDK iddiası → Context7 snippet şart (yoksa UNVERIFIED + max MINOR).
- Biyomedikal iddia → PMID/DOI format + 5-yıl penceresi (dışı FOUNDATIONAL gerekçeli).
- GitHub → yıldız/son-commit/lisans/arşiv sağlığı (STALE 18ay, LOW-ADOPTION <200).
- Ağ yoksa bile çalışır: format + tarih kapısı offline, canlılık kontrolü opsiyonel.
- Çıktı: .sherlock/literature/<tarih>-guard.{json,md} + search-log iskeleti.

Kullanım:
  python literature_guard.py --check "AutoDock Vina zinc coordination" --db pubmed --year 2022
  python literature_guard.py --doi 10.1021/acs.jcim.1c00234 --year 2021
  python literature_guard.py --pmid 34567890 --year 2020
  python literature_guard.py --github owner/repo --stars 1200 --pushed 2026-05-01 --license MIT
  python literature_guard.py --context7 "/rdkit/rdkit metal coordination" --snippets 5
  python literature_guard.py --init-log <workspace>   # search-log.md iskeleti üretir
"""

import os
import re
import sys
import json
import datetime
import argparse

DOI_RE = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")
GITHUB_RE = re.compile(r"^[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+$")


def check_doi(doi: str, year: int, case_year: int) -> dict:
    ok = bool(DOI_RE.match(doi.strip()))
    age = case_year - year if year else 99
    if not ok:
        return {"verdict": "UNVERIFIED", "severity_cap": "MINOR", "reason": "DOI formatı geçersiz"}
    if age > 5:
        return {"verdict": "FOUNDATIONAL_ONLY", "severity_cap": "MAJOR",
                "reason": f"5-yıl dışı ({age}y). [FOUNDATIONAL] gerekçe şart."}
    return {"verdict": "PASS", "severity_cap": None, "reason": "DOI format + güncellik OK"}


def check_pmid(pmid: str, year: int, case_year: int) -> dict:
    ok = pmid.isdigit() and len(pmid) >= 4
    age = case_year - year if year else 99
    if not ok:
        return {"verdict": "UNVERIFIED", "severity_cap": "MINOR", "reason": "PMID sayısal değil"}
    if age > 5:
        return {"verdict": "FOUNDATIONAL_ONLY", "severity_cap": "MAJOR",
                "reason": f"5-yıl dışı ({age}y). [FOUNDATIONAL] gerekçe şart."}
    return {"verdict": "PASS", "severity_cap": None, "reason": "PMID + güncellik OK"}


def check_github(repo: str, stars: int, pushed: str, license_: str, archived: bool) -> dict:
    if not GITHUB_RE.match(repo or ""):
        return {"verdict": "UNVERIFIED", "severity_cap": "MINOR", "reason": "repo formatı owner/repo olmalı"}
    tags = []
    if archived:
        tags.append("[ARCHIVED]")
    try:
        push_d = datetime.datetime.strptime(pushed, "%Y-%m-%d").date() if pushed else None
        months = (datetime.date.today() - push_d).days / 30 if push_d else 99
        if months > 18:
            tags.append("[STALE]")
    except Exception:
        tags.append("[PUSH-DATE-UNKNOWN]")
        months = 99
    if (stars or 0) < 200:
        tags.append("[LOW-ADOPTION]")
    if not license_:
        tags.append("[NO-LICENSE]")
    if "[ARCHIVED]" in tags or "[STALE]" in tags:
        return {"verdict": "RISKY", "severity_cap": "MINOR",
                "reason": f"{' '.join(tags)} — kanıt olarak zayıf, alternatif ara", "tags": tags}
    return {"verdict": "PASS", "severity_cap": None, "reason": f"Sağlıklı {' '.join(tags) if tags else ''}".strip(),
            "tags": tags}


def check_context7(query: str, snippets: int) -> dict:
    if not query or snippets <= 0:
        return {"verdict": "UNVERIFIED", "severity_cap": "MINOR",
                "reason": "Context7 snippet yok -> atifsiz iddia en fazla MINOR"}
    return {"verdict": "PASS", "severity_cap": None,
            "reason": f"Context7 sorgusu + {snippets} snippet belgelenmeli ([CANLI ARAMA KANITI])"}


def init_search_log(workspace: str) -> str:
    d = os.path.join(os.path.abspath(workspace), ".sherlock", "literature")
    os.makedirs(d, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    p = os.path.join(d, f"{stamp}-search-log.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write(f"# Arama Kaydı — {stamp}\n\n")
        f.write("| Kaynak / Veritabanı | Arama Terimi / Sorgu | Filtre | Toplam Sonuç | İncelenen |\n")
        f.write("|:---|:---|:---|:---:|:---:|\n")
        f.write("| Context7 | `/org/proje \"sorgu\"` | latest |  |  |\n")
        f.write("| PubMed | `(\"terim\") AND (\"terim\")` | 2021-2026 |  |  |\n")
        f.write("| GitHub | `anahtar kelime` | stars>100 |  |  |\n")
        f.write("\n> R&V raporundaki tablo buradan kopyalanır. 600 kelime tavanını delmemek için tam log burada tutulur.\n")
    return p


def main():
    ap = argparse.ArgumentParser(description="Sherlock Literature Guard v5.0")
    ap.add_argument("--doi", default=None)
    ap.add_argument("--pmid", default=None)
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--case-year", type=int, default=datetime.date.today().year)
    ap.add_argument("--github", default=None)
    ap.add_argument("--stars", type=int, default=0)
    ap.add_argument("--pushed", default=None)
    ap.add_argument("--license", dest="license_", default=None)
    ap.add_argument("--archived", action="store_true")
    ap.add_argument("--context7", default=None)
    ap.add_argument("--snippets", type=int, default=0)
    ap.add_argument("--check", default=None)
    ap.add_argument("--db", default=None)
    ap.add_argument("--init-log", default=None)
    args = ap.parse_args()

    if args.init_log:
        p = init_search_log(args.init_log)
        print(f"[LITGUARD] search-log: {p}")
        print("Result:", json.dumps({"search_log": p}, ensure_ascii=False))
        return
    res = {}
    if args.doi:
        res["doi"] = check_doi(args.doi, args.year or 0, args.case_year)
    if args.pmid:
        res["pmid"] = check_pmid(args.pmid, args.year or 0, args.case_year)
    if args.github:
        res["github"] = check_github(args.github, args.stars, args.pushed, args.license_, args.archived)
    if args.context7 is not None:
        res["context7"] = check_context7(args.context7, args.snippets)
    if args.check:
        res["note"] = (f"'{args.check}' icin --db {args.db or '?'} ile arama yapip "
                       f"search-log.md'ye isleyin. Kaynaksiz iddia -> [UNVERIFIED] + max MINOR.")
    if not res:
        ap.print_help()
        sys.exit(1)
    print("Result:", json.dumps(res, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
