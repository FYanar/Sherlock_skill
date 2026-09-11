#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sherlock Deadcode & Duplication Scanner v5.1 — Cesur Ama Güvenli (Faz D4 H1 fixli)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- AST normalize ile duplikasyon tespiti (whitespace/comment bağımsız).
- Referans taraması ile ölü fonksiyon adayı (import + çağrı + bare-ref callback + AST dispatch + poliglot + dinamik).
- visit_* hook'lar whitelist (NodeTransformer dispatch).
- Graphify community bilgisi varsa güveni artırır (yoksa düşürür, bloklamaz).
- Çıktı: .sherlock/deadcode/<tarih>-report.{json,md}

Güven:
  HIGH   → BACKUP→REWIRE→DELETE→VERIFY yapılabilir (otomatik aday)
  MEDIUM → plana WP yaz, onay bekle
  LOW    → sadece raporla

Kullanım:
  python deadcode_scanner.py <workspace> [--min-lines 3] [--report-only]
"""

import os
import re
import ast
import sys
import json
import hashlib
import datetime
import argparse

try:
    from sherlock_helpers import sha12 as _sha12, utc_stamp as _utc_stamp
except ImportError:
    from scripts.sherlock_helpers import sha12 as _sha12, utc_stamp as _utc_stamp

SKIP_DIRS = {"node_modules", "__pycache__", "target", "dist", "build", "venv", ".venv",
             ".git", ".sherlock", "graphify-out", "memory_archive"}
PY_EXTS = {".py"}
GENERIC_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".cs", ".c", ".cpp"}


def iter_source_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in GENERIC_EXTS:
                yield os.path.join(dirpath, fn)


def normalize_py_func(node: ast.FunctionDef) -> str:
    """Gövdeyi normalize et: isimleri X'e indirgeme yok, sadece whitespace/comment bağımsız dump."""
    # Arg isimlerini normalize et (a0, a1...) — semantik eşdeğerlik için
    class Normalizer(ast.NodeTransformer):
        def __init__(self):
            self.map = {}
            self.counter = 0
        def visit_Name(self, n):
            if isinstance(n.ctx, (ast.Param, ast.Store)):
                if n.id not in self.map:
                    self.map[n.id] = f"v{self.counter}"
                    self.counter += 1
                n.id = self.map[n.id]
            return self.generic_visit(n)
        def visit_arg(self, n):
            if n.arg not in self.map:
                self.map[n.arg] = f"v{self.counter}"
                self.counter += 1
            n.arg = self.map[n.arg]
            return self.generic_visit(n)
    try:
        clone = ast.parse(ast.unparse(node))
        Normalizer().visit(clone)
        return ast.unparse(clone)
    except Exception:
        return ast.dump(node, annotate_fields=False)


def collect_py_functions(root: str):
    funcs = []  # {file, name, lineno, norm, sha, lines}
    for fp in iter_source_files(root):
        if not fp.endswith(".py"):
            continue
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                src = f.read()
            tree = ast.parse(src)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                try:
                    norm = normalize_py_func(node)
                except Exception:
                    norm = ""
                sha = _sha12(norm)
                funcs.append({"file": os.path.relpath(fp, root), "name": node.name,
                              "lineno": node.lineno, "async": isinstance(node, ast.AsyncFunctionDef),
                              "norm_sha": sha, "norm_len": len(norm),
                              "end": getattr(node, "end_lineno", node.lineno)})
    return funcs


def find_references(root: str, func_name: str) -> dict:
    """Çağrı noktaları: import + çağrı + bare-ref callback + AST dispatch + poliglot + dinamik + re-export."""
    hits = {"static": [], "poliglot": [], "dynamic": [], "reexport": []}
    pat_call = re.compile(rf"\b{re.escape(func_name)}\s*\(")
    pat_import = re.compile(rf"(from\s+\S+\s+import\s+[^\n]*\b{re.escape(func_name)}\b|import\s+[^\n]*\b{re.escape(func_name)}\b)")
    # H1 fix (Faz D4): parensiz callback referansı — örn. SCORE_RE.subn(repl, text)
    pat_bare = re.compile(rf"[(,]\s*{re.escape(func_name)}\s*[,)]")
    pat_dyn = re.compile(rf"(getattr|__import__|importlib|globals\(\)\[)[^\n]*{re.escape(func_name)}")
    pat_reexp = re.compile(rf"(_alias\s*=\s*{re.escape(func_name)}|__all__[^\n]*{re.escape(func_name)})")
    # H1 fix (Faz D4): AST framework dispatch — Normalizer().visit(clone) → visit_Name/visit_arg
    is_visit_hook = func_name.startswith("visit_")
    for fp in iter_source_files(root):
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except Exception:
            continue
        rel = os.path.relpath(fp, root)
        if pat_import.search(text):
            hits["static"].append(rel + ":import")
        if pat_call.search(text):
            # Tanım satırını sayma: aynı dosyada 'def func_name' varsa 1 çağrı düş
            calls = len(pat_call.findall(text))
            defs = len(re.findall(rf"def\s+{re.escape(func_name)}\b", text))
            if calls - defs > 0:
                hits["static"].append(f"{rel}:callx{calls - defs}")
        if pat_bare.search(text):
            hits["static"].append(rel + ":bare-ref")
        if is_visit_hook and ".visit(" in text:
            hits["dynamic"].append(rel + ":ast-dispatch")
        if pat_dyn.search(text):
            hits["dynamic"].append(rel)
        if pat_reexp.search(text):
            hits["reexport"].append(rel)
        ext = os.path.splitext(fp)[1].lower()
        if ext in {".bat", ".sh", ".ps1", ".cmd", ".yml", ".yaml", ".toml", ".cfg", ".ini",
                   ".json", ".Dockerfile"} or os.path.basename(fp) in {"Makefile", "Dockerfile"}:
            if func_name in text:
                hits["poliglot"].append(rel)
        # .bat/.sh/.ps1 uzantılı dosyalar iter_source_files dışında kalabilir — ek tara
    # Poliglot ek tur: script uzantıları
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in {".bat", ".sh", ".ps1", ".cmd"}:
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, "r", encoding="utf-8", errors="replace") as f:
                        t = f.read()
                    if func_name in t and os.path.relpath(fp, root) not in hits["poliglot"]:
                        hits["poliglot"].append(os.path.relpath(fp, root))
                except Exception:
                    pass
    return hits


def load_graphify_communities(root: str):
    for cand in [os.path.join(root, "Agent", "graphify-out", "graph.json"),
                 os.path.join(root, "graphify-out", "graph.json")]:
        if os.path.exists(cand):
            try:
                with open(cand, "r", encoding="utf-8", errors="replace") as f:
                    g = json.load(f)
                # Basit: node->community haritası çıkarmaya çalış
                cmap = {}
                nodes = g.get("nodes", []) if isinstance(g, dict) else []
                for n in nodes:
                    nid = n.get("id") or n.get("name")
                    com = n.get("community", n.get("module", "?"))
                    if nid:
                        cmap[str(nid)] = str(com)
                return {"graph": cand, "communities": cmap}
            except Exception:
                return {"graph": cand, "communities": {}}
    return {"graph": None, "communities": {}}


def scan_workspace(root: str, min_lines: int = 3) -> dict:
    root = os.path.abspath(root)
    funcs = collect_py_functions(root)
    # Duplikasyon: aynı norm_sha ≥2
    by_sha = {}
    for fn in funcs:
        by_sha.setdefault(fn["norm_sha"], []).append(fn)
    duplications = []
    for sha, group in by_sha.items():
        if len(group) >= 2 and all((g["end"] - g["lineno"] + 1) >= min_lines for g in group):
            # Async/sync karışık ise red flag
            kinds = {g["async"] for g in group}
            red = "async/sync karışık — SİLME" if len(kinds) > 1 else ""
            # Aynı dosyada aynı isim tekrarı (overload) ise ele
            locs = [f"{g['file']}:{g['lineno']}:{g['name']}" for g in group]
            conf = "HIGH" if not red else "LOW"
            duplications.append({"sha": sha, "confidence": conf, "locations": locs,
                                 "names": sorted({g["name"] for g in group}),
                                 "red_flag": red})
    # Ölü aday: hiç referansı olmayan fonksiyonlar (main/test hariç)
    dead = []
    for fn in funcs:
        if fn["name"].startswith("test_") or fn["name"] in {"main", "__init__"}:
            continue
        # H1 fix (Faz D4): visit_* hook'lar framework dispatch ile yaşar — raporlama, whitelist
        if fn["name"].startswith("visit_"):
            continue
        if fn["file"].startswith("tests"):
            continue
        refs = find_references(root, fn["name"])
        # Tanımın kendisi static'te sayıldıysa total>=1 olabilir; gerçek çağrı yoksa ölü
        pure_calls = [h for h in refs["static"] if "callx" in h]
        bare_refs = [h for h in refs["static"] if "bare-ref" in h]
        import_refs = [h for h in refs["static"] if "import" in h]
        if not pure_calls and not bare_refs and not import_refs and not refs["dynamic"] and not refs["poliglot"] and not refs["reexport"]:
            dead.append({"location": f"{fn['file']}:{fn['lineno']}:{fn['name']}",
                         "confidence": "MEDIUM", "refs": refs,
                         "note": "Çağrı bulunamadı — onayda silinebilir, otomatik silme YOK"})
    graph = load_graphify_communities(root)
    # Graphify yoksa güven düşür
    if graph["graph"] is None:
        for d in duplications:
            if d["confidence"] == "HIGH":
                d["confidence"] = "MEDIUM"
                d["red_flag"] = (d["red_flag"] + " | graphify yok → HIGH verilemez").strip(" |")
    return {"workspace": root, "functions": len(funcs),
            "duplications": sorted(duplications, key=lambda d: len(d["locations"]), reverse=True),
            "dead_candidates": dead, "graphify": graph["graph"]}


def write_report(root: str, result: dict) -> dict:
    out_dir = os.path.join(root, ".sherlock", "deadcode")
    os.makedirs(out_dir, exist_ok=True)
    stamp = _utc_stamp()
    jp = os.path.join(out_dir, f"{stamp}-report.json")
    mp = os.path.join(out_dir, f"{stamp}-report.md")
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    with open(mp, "w", encoding="utf-8") as f:
        f.write(f"# Deadcode & Duplikasyon Raporu — {stamp}\n\n")
        f.write(f"Fonksiyon: {result['functions']} | duplikasyon: {len(result['duplications'])} | ölü adayı: {len(result['dead_candidates'])}\n")
        f.write(f"Graphify: {result['graphify'] or 'YOK (güven düşürüldü)'}\n\n")
        f.write("## Duplikasyon (HIGH → otomatik aday, MEDIUM → onaylı)\n")
        for d in result["duplications"][:20]:
            f.write(f"- **{d['confidence']}** `{d['sha']}` {', '.join(d['locations'])} {d['red_flag']}\n")
        f.write("\n## Ölü Adaylar (otomatik silme YOK, onay şart)\n")
        for d in result["dead_candidates"][:30]:
            f.write(f"- **{d['confidence']}** `{d['location']}` — {d['note']}\n")
        f.write("\n> HIGH duplikasyon bile Brave 4 koşulunu ister: grounding + semantik kanıt + tam rewire + test.\n")
    return {"json": jp, "md": mp}


def main():
    ap = argparse.ArgumentParser(description="Sherlock Deadcode Scanner v5.0")
    ap.add_argument("workspace", nargs="?", default=".")
    ap.add_argument("--min-lines", type=int, default=3)
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    res = scan_workspace(args.workspace, min_lines=args.min_lines)
    paths = write_report(os.path.abspath(args.workspace), res)
    print(f"[DEADCODE] Fonksiyon:{res['functions']} Duplikasyon:{len(res['duplications'])} Ölü:{len(res['dead_candidates'])}")
    print(f"[DEADCODE] Rapor: {paths['md']}")
    print("Result:", json.dumps({"duplications": len(res["duplications"]),
                                 "dead": len(res["dead_candidates"]), **paths}, ensure_ascii=False))


if __name__ == "__main__":
    main()
