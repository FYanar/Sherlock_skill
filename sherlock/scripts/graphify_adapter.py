#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sherlock x Graphify Adapter
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Graphify çıktısını (graph.json / GRAPH_REPORT.md / .graphify_ast.json)
Sherlock'un 3 ajanlı (2+1 bariyerli) adli tıp protokolü için SSOT (Single Source of Truth)
olarak normalize eder.

Kullanim:
  python graphify_adapter.py --workspace <path> [--ensure] [--auto-update] [--query "soru"]
  python graphify_adapter.py --workspace <path> --export-findings
  python graphify_adapter.py --workspace <path> --inject-case <YYYYMMDD-case-slug>

Cikti:
  .sherlock/graphify-context.md  -> 00-case.md'ye inject edilecek ozet
  .sherlock/graphify-findings.json -> F-R/F-A/F-C icin ham bulgu onerileri
"""
import json
import hashlib
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _sha256(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:12]


def _get_graphify_out(workspace: Path) -> Path:
    """Agent/graphify-out tasimasi icin cozumleyici: Agent/graphify-out > GRAPHIFY_OUT env > kok/graphify-out"""
    import os
    env = os.environ.get("GRAPHIFY_OUT")
    if env:
        p = Path(env)
        if not p.is_absolute():
            p = workspace / p
        return p
    agent_candidate = workspace / "Agent" / "graphify-out"
    root_candidate = workspace / "graphify-out"
    # Tercih: Agent icindeki gercek konum varsa onu kullan
    if agent_candidate.exists():
        return agent_candidate
    # Koku yoksa veya Agent varsa Agent'i tercih et
    if not root_candidate.exists() and agent_candidate.parent.exists():
        return agent_candidate
    # Fallback: Agent tercih (yeni standart), yoksa kok
    if agent_candidate.parent.exists():
        # Proje OneClickDock gibi Agent klasoru varsa yeni standart Agent/graphify-out
        return agent_candidate
    return root_candidate


def _resolve_scan_root(workspace: Path) -> Path:
    """Graphify tarama kapsami: .graphify_root varsa onu kullan (örn. scripts-only), yoksa workspace.

    Neden: graphify `update <path>` komutundaki <path> kapsami belirler. Kapsam
    daraltildiysa (sadece scripts/) update workspace kokune verilirse graph
    sessizce full-projeye geri genisler. .graphify_root tek dogruluk kaynagidir.

    Faz D4 M3 guard: kayıtlı root workspace dışındaysa STALE SCOPE'tur
    (örn. eski projenin graph_out'una bakılıyorsa) — sessizce yanlış projeyi
    tazelemek yerine workspace'e düş, status'e not bırakılsın diye uyarı yazdır.
    """
    try:
        root_file = _get_graphify_out(workspace) / ".graphify_root"
        if root_file.exists():
            saved = root_file.read_text(encoding="utf-8").strip()
            if saved:
                p = Path(saved)
                if p.exists():
                    try:
                        ws = workspace.resolve()
                        pr = p.resolve()
                        if pr == ws or pr.is_relative_to(ws):
                            return p
                        print(f"[graphify-adapter] STALE SCOPE: .graphify_root ({pr}) workspace ({ws}) dışında — workspace kullanılıyor.")
                    except Exception:
                        return p
    except Exception:
        pass
    return workspace


def _adapter_env(workspace: Path) -> dict:
    """Subprocess icin env: GRAPHIFY_OUT her zaman absolute (relative scan-root'a yapisir, scripts/Agent/... yaratir)."""
    import os
    env = dict(os.environ)
    try:
        env["GRAPHIFY_OUT"] = str(_get_graphify_out(workspace).resolve())
    except Exception:
        pass
    return env


def _ensure_graphifyignore(workspace: Path):
    """Hiz icin .graphifyignore otomatik olustur (yoksa)."""
    gi = workspace / ".graphifyignore"
    if gi.exists():
        return
    # Sadece sherlock'un kendi onerisi — kullanici uzerine yazabilir
    content = """# Sherlock auto-generated .graphifyignore — hiz icin buyuk klasorleri atla
# Kaynak: https://github.com/Graphify-Labs/graphify
node_modules/
.git/
dist/
build/
target/
venv/
.venv/
__pycache__/
*.pyc
Agent/graphify-out/
graphify-out/
.sherlock/
backups/
.cache/
"""
    try:
        gi.write_text(content, encoding="utf-8")
    except Exception:
        pass


def _ensure_graphify_installed(python: str) -> dict:
    """
    Graphify CLI yoksa otomatik kurar.
    Kaynak: https://github.com/Graphify-Labs/graphify — PyPI adi `graphifyy` (cift y), CLI adi `graphify`.
    Kurulum: pip install graphifyy && graphify install
    Windows: pipx tercih edilir, yoksa --break-system-packages ile pip.
    """
    import shutil
    info = {"installed": False, "method": None, "version": None}

    # Zaten var mi?
    if shutil.which("graphify"):
        try:
            r = subprocess.run(["graphify", "--help"], capture_output=True, timeout=5)
            if r.returncode == 0 or b"graphify" in r.stdout + r.stderr:
                info["installed"] = True
                info["method"] = "existing CLI"
                # version
                try:
                    v = subprocess.run([python, "-m", "pip", "show", "graphifyy"], capture_output=True, text=True, timeout=5)
                    for line in v.stdout.splitlines():
                        if line.startswith("Version:"):
                            info["version"] = line.split(":", 1)[1].strip()
                except Exception:
                    pass
                return info
        except Exception:
            pass

    # python -m graphify var mi?
    try:
        r = subprocess.run([python, "-m", "graphify", "--help"], capture_output=True, timeout=5)
        if r.returncode == 0:
            info["installed"] = True
            info["method"] = "python -m graphify"
            return info
    except Exception:
        pass

    # Yok -> otomatik kur
    print("[graphify-adapter] graphify CLI bulunamadi, otomatik kuruluyor: pip install graphifyy ...")
    install_cmds = []
    # pipx var mi?
    if shutil.which("pipx"):
        install_cmds.append([python, "-m", "pipx", "install", "graphifyy"])
    # pip dene
    install_cmds.append([python, "-m", "pip", "install", "graphifyy", "-q"])
    install_cmds.append([python, "-m", "pip", "install", "graphifyy", "-q", "--break-system-packages"])
    # uv var mi?
    if shutil.which("uv"):
        install_cmds.insert(0, ["uv", "tool", "install", "graphifyy", "-q"])
        install_cmds.insert(0, ["uv", "pip", "install", "graphifyy", "-q"])

    last_err = None
    for cmd in install_cmds:
        try:
            print(f"[graphify-adapter] dene: {' '.join(cmd)}")
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                info["installed"] = True
                info["method"] = " ".join(cmd)
                # Dogrula
                if shutil.which("graphify") or subprocess.run([python, "-m", "graphify", "--help"], capture_output=True, timeout=5).returncode == 0:
                    print(f"[graphify-adapter] kurulum basarili: {' '.join(cmd)}")
                    try:
                        v = subprocess.run([python, "-m", "pip", "show", "graphifyy"], capture_output=True, text=True, timeout=5)
                        for line in v.stdout.splitlines():
                            if line.startswith("Version:"):
                                info["version"] = line.split(":", 1)[1].strip()
                    except Exception:
                        pass
                    return info
            last_err = r.stderr[-500:] if r.stderr else r.stdout[-500:]
        except Exception as e:
            last_err = str(e)
            continue

    info["error"] = last_err or "all install methods failed"
    info["hint"] = "Manuel kurulum: pip install graphifyy  veya  pipx install graphifyy  (bkz https://github.com/Graphify-Labs/graphify)"
    return info


def _is_code_only_workspace(workspace: Path) -> bool:
    """Kod disi dosya (md/pdf/png) coksa False, sadece kod varsa True."""
    try:
        from pathlib import Path as _P
        docs = list(workspace.rglob("*.md")) + list(workspace.rglob("*.pdf")) + list(workspace.rglob("*.png"))
        # graphify-out ve .git icindekileri sayma
        docs = [p for p in docs if "graphify-out" not in str(p) and ".git" not in str(p)]
        return len(docs) < 5
    except Exception:
        return True


def ensure_graphify(workspace: Path, no_viz: bool = True, use_cache: bool = True, code_only: bool = None, force_update: bool = False) -> dict:
    """
    Pre-Flight hook: graphify-out/graph.json yoksa olustur, varsa --update ile tazele.
    Hizli mod: cache varsa --update, kod-only ise --code-only (LLM yok, 0 token).
    force_update=True ise yas kontrolu atlanir, her cagrida kosulsuz `graphify update` calisir
    (sherlock AŞAMA 0 otomatik-update baglantisi). Kapsam her zaman .graphify_root'tan
    alinir (scripts-only graph full-projeye geri genislemez).
    Kaynak: https://github.com/Graphify-Labs/graphify
    """
    scan_root = _resolve_scan_root(workspace)
    env = _adapter_env(workspace)
    graph_json = _get_graphify_out(workspace) / "graph.json"
    graph_report = _get_graphify_out(workspace) / "GRAPH_REPORT.md"
    python_marker = _get_graphify_out(workspace) / ".graphify_python"

    status = {
        "graph_exists": graph_json.exists(),
        "report_exists": graph_report.exists(),
        "python_marker": python_marker.exists(),
        "action": "none",
        "graph_sha": _sha256(graph_json),
        "nodes": 0,
        "edges": 0,
        "communities": 0,
        "scan_root": str(scan_root),
        "graph_out": str(_get_graphify_out(workspace)),
    }

    # .graphifyignore otomatik olustur (yoksa) — hiz icin kritik
    _ensure_graphifyignore(workspace)

    # graph.json yoksa veya 24 saatten eskiyse tazele; force_update her cagrida tazeler
    needs_build = not graph_json.exists()
    is_incremental = False
    if force_update and graph_json.exists():
        needs_build = True
        is_incremental = True
        status["action"] = "force update (sherlock auto-update) -> incremental update"
    if graph_json.exists():
        try:
            data = _load_json(graph_json)
            if data:
                if isinstance(data, dict):
                    nodes = data.get("nodes", [])
                    edges = data.get("edges", [])
                    status["nodes"] = len(nodes) if isinstance(nodes, list) else 0
                    status["edges"] = len(edges) if isinstance(edges, list) else 0
                age_hours = (datetime.now(timezone.utc).timestamp() - graph_json.stat().st_mtime) / 3600
                if age_hours > 24:
                    needs_build = True
                    is_incremental = True  # stale ise --update yeterli
                    status["action"] = f"stale ({age_hours:.1f}h) -> incremental update"
                else:
                    # Taze ise bile manifest'e gore degisen dosya var mi kontrol et
                    if use_cache and (_get_graphify_out(workspace) / ".graphify_manifest.json").exists():
                        is_incremental = True
        except Exception:
            needs_build = True

    if needs_build:
        # Resolve python interpreter
        python = sys.executable
        marker = _get_graphify_out(workspace) / ".graphify_python"
        if marker.exists():
            try:
                python = marker.read_text(encoding="utf-8").strip() or python
            except Exception:
                pass

        # Otomatik kurulum kontrolu (https://github.com/Graphify-Labs/graphify)
        install_info = _ensure_graphify_installed(python)
        status["install_info"] = install_info
        if not install_info.get("installed"):
            status["action"] = "graphify CLI not found and auto-install failed - fallback to AST"
            status["error"] = install_info.get("error", "graphify not installed")
            status["hint"] = install_info.get("hint", "pip install graphifyy")
            return status

        # Try graphify CLI, fallback to python -m graphify
        cmd_base = None
        for candidate in [["graphify"], [python, "-m", "graphify"]]:
            try:
                r = subprocess.run(candidate + ["--help"], capture_output=True, timeout=5)
                if r.returncode == 0 or b"graphify" in (r.stdout or b"") + (r.stderr or b""):
                    cmd_base = candidate
                    break
            except Exception:
                continue

        if cmd_base is None:
            status["action"] = "graphify CLI not found after install - fallback to AST"
            status["error"] = "graphify not installed"
            return status

        # Hiz optimizasyonu: code-only + incremental + no-viz
        # Kapsam: her zaman scan_root (.graphify_root), workspace degil!
        if code_only is None:
            code_only = _is_code_only_workspace(scan_root)
        cmd = cmd_base + [str(scan_root)]
        if is_incremental and use_cache:
            # graph.json varsa --update (sadece degisen kod dosyalari, LLM yok, hizli).
            # NOT: `update` sadece --force/--no-cluster kabul eder (--code-only/--no-viz yok).
            cmd = cmd_base + ["update", str(scan_root)]
            status["mode"] = "incremental --update"
        else:
            # Ilk build
            if code_only:
                cmd.append("--code-only")
            if no_viz:
                cmd.append("--no-viz")
            status["mode"] = "full" + (" --code-only" if code_only else "")
        # Timeout: incremental 90sn, full 300sn
        build_timeout = 90 if is_incremental else 300
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=build_timeout, cwd=str(workspace), env=env)
            status["action"] = f"built: {' '.join(cmd)}"
            status["stdout_tail"] = result.stdout[-500:] if result.stdout else ""
            status["stderr_tail"] = result.stderr[-500:] if result.stderr else ""
            status["returncode"] = result.returncode
            if graph_json.exists():
                status["graph_exists"] = True
                status["graph_sha"] = _sha256(graph_json)
                data = _load_json(graph_json)
                if data and isinstance(data, dict):
                    status["nodes"] = len(data.get("nodes", []))
                    # Clustered writer `links`, raw writer `edges` kullanir
                    links = data.get("links", data.get("edges", []))
                    status["edges"] = len(links)
        except subprocess.TimeoutExpired:
            status["action"] = f"timeout ({build_timeout}s)"
            status["error"] = "graphify build timed out"
            # Incremental timeout ise fallback: full build dene
            if is_incremental:
                try:
                    fb_cmd = cmd_base + [str(scan_root), "--code-only", "--no-viz"] if _is_code_only_workspace(scan_root) else cmd_base + [str(scan_root), "--no-viz"]
                    result = subprocess.run(fb_cmd, capture_output=True, text=True, timeout=300, cwd=str(workspace), env=env)
                    status["fallback"] = f"tried full: {' '.join(fb_cmd)} -> {result.returncode}"
                except Exception:
                    pass
        except Exception as e:
            status["action"] = f"failed: {e}"
            status["error"] = str(e)
    else:
        status["action"] = "graph exists and fresh - using cached"

    # Read GRAPH_REPORT.md for community/god node summary
    if graph_report.exists():
        try:
            report_text = graph_report.read_text(encoding="utf-8")
            # Count communities from report
            import re
            communities = re.findall(r"Community\s+\d+", report_text)
            status["communities"] = len(set(communities))
            status["report_sha"] = _sha256(graph_report)
        except Exception:
            pass

    # Otomatik Tri-Report Görselleştirme Paketi (graph.html, CALLFLOW.html, pipeline_graph.html)
    if graph_json.exists():
        try:
            status["visual_reports"] = generate_visual_reports(workspace)
        except Exception as e:
            status["visual_reports_error"] = str(e)

    return status


def generate_visual_reports(workspace: Path) -> dict:
    """
    Otomatik Tri-Report Görselleştirme Paketi:
    1. graph.html (Vis.js standart kuvvet tabanlı ağ topolojisi)
    2. CALLFLOW.html (Mermaid mimari çağrı akışı, arayüz tabloları ve bileşen şeması)
    3. pipeline_graph.html (Vis.js Y-şekilli aşama akışı, filtreler ve düğüm denetçisi)
    """
    out_dir = _get_graphify_out(workspace)
    graph_json = out_dir / "graph.json"
    status = {"graph_html": None, "callflow_html": None, "pipeline_graph_html": None}
    if not graph_json.exists():
        status["error"] = "graph.json bulunamadı, görsel raporlar atlandı"
        return status

    python = sys.executable
    marker = out_dir / ".graphify_python"
    if marker.exists():
        try:
            python = marker.read_text(encoding="utf-8").strip() or python
        except Exception:
            pass

    env = _adapter_env(workspace)

    # 1. graph.html
    graph_html = out_dir / "graph.html"
    try:
        r = subprocess.run([python, "-m", "graphify", "export", "html"],
                           capture_output=True, text=True, timeout=90, cwd=str(workspace), env=env)
        if graph_html.exists():
            status["graph_html"] = f"{graph_html} ({graph_html.stat().st_size} bytes)"
        else:
            status["graph_html"] = f"exit {r.returncode}: {r.stderr[-200:] if r.stderr else 'not written'}"
    except Exception as e:
        status["graph_html"] = f"failed: {e}"

    # 2. CALLFLOW.html
    callflow_html = out_dir / "CALLFLOW.html"
    try:
        r = subprocess.run([python, "-m", "graphify", "export", "callflow-html", str(graph_json), "--output", str(callflow_html)],
                           capture_output=True, text=True, timeout=90, cwd=str(workspace), env=env)
        if callflow_html.exists():
            status["callflow_html"] = f"{callflow_html} ({callflow_html.stat().st_size} bytes)"
        else:
            status["callflow_html"] = f"exit {r.returncode}: {r.stderr[-200:] if r.stderr else 'not written'}"
    except Exception as e:
        status["callflow_html"] = f"failed: {e}"

    # 3. pipeline_graph.html
    pipeline_html = out_dir / "pipeline_graph.html"
    try:
        try:
            from pipeline_visualizer import generate_pipeline_graph
        except ImportError:
            from scripts.pipeline_visualizer import generate_pipeline_graph

        generate_pipeline_graph(graph_json, pipeline_html)
        if pipeline_html.exists():
            status["pipeline_graph_html"] = f"{pipeline_html} ({pipeline_html.stat().st_size} bytes)"
    except Exception as e:
        # Fallback: subprocess call to pipeline_visualizer.py
        try:
            vis_script = Path(__file__).parent / "pipeline_visualizer.py"
            if vis_script.exists():
                r = subprocess.run([python, str(vis_script), "--graph", str(graph_json), "--output", str(pipeline_html)],
                                   capture_output=True, text=True, timeout=60, cwd=str(workspace), env=env)
                if pipeline_html.exists():
                    status["pipeline_graph_html"] = f"{pipeline_html} ({pipeline_html.stat().st_size} bytes)"
                else:
                    status["pipeline_graph_html"] = f"exit {r.returncode}: {r.stderr[-200:] if r.stderr else str(e)}"
            else:
                status["pipeline_graph_html"] = f"failed: {e}"
        except Exception as e2:
            status["pipeline_graph_html"] = f"failed: {e2}"

    return status


def build_context_md(workspace: Path) -> Path:
    """
    graphify-out/GRAPH_REPORT.md ve graph.json'dan .sherlock/graphify-context.md uretir.
    Bu dosya 00-case.md'ye inject edilir ve tum 3 ajan tarafindan okunur.
    """
    graph_json = _get_graphify_out(workspace) / "graph.json"
    graph_report = _get_graphify_out(workspace) / "GRAPH_REPORT.md"
    analysis_json = _get_graphify_out(workspace) / ".graphify_analysis.json"
    labels_json = _get_graphify_out(workspace) / ".graphify_labels.json"

    out_dir = workspace / ".sherlock"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "graphify-context.md"

    lines = []
    lines.append(f"# Graphify SSOT Context — {workspace.name}")
    lines.append(f"> Otomatik uretildi: {datetime.now(timezone.utc).isoformat()} | Kaynak: Agent/graphify-out/graph.json")
    lines.append(f"> SHA256(graph.json): {_sha256(graph_json)}")
    lines.append("")

    data = _load_json(graph_json)
    if data is None:
        lines.append("> [!WARNING]")
        lines.append("> `Agent/graphify-out/graph.json` bulunamadi. Sherlock fallback AST taramasina gececek.")
        lines.append("> Otomatik kurulum: `pip install graphifyy && graphify install` (PyPI adi `graphifyy`, CLI `graphify`)")
        lines.append("> Kaynak: https://github.com/Graphify-Labs/graphify")
        lines.append("> Manuel: `graphify . --no-viz` veya `python scripts/graphify_adapter.py --workspace . --ensure`")
        lines.append("> Windows PATH sorunu: `%APPDATA%\\Python\\Python3xx\\Scripts` PATH'e ekle veya `pipx install graphifyy` kullan")
        lines.append("")
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path

    # Summary stats
    nodes = data.get("nodes", []) if isinstance(data, dict) else []
    edges = data.get("edges", []) if isinstance(data, dict) else []
    lines.append(f"**Graph Stats:** {len(nodes)} nodes, {len(edges)} edges")
    if graph_report.exists():
        lines.append(f"**Report SHA:** {_sha256(graph_report)}")
    lines.append("")

    # God nodes
    analysis = _load_json(analysis_json)
    if analysis and "gods" in analysis:
        gods = analysis["gods"][:10]  # top 10
        if gods:
            lines.append("## God Nodes (Yuksek Baglanti - Parcalanma Adayi)")
            lines.append("| Node | Degree | Topluluk | Risk |")
            lines.append("|---|---|---|---|")
            for g in gods:
                nid = g.get("node", g.get("id", "?"))
                deg = g.get("degree", g.get("score", "?"))
                comm = g.get("community", "?")
                risk = "CRITICAL" if isinstance(deg, int) and deg > 30 else "WARN" if isinstance(deg, int) and deg > 15 else "INFO"
                lines.append(f"| `{nid}` | {deg} | {comm} | {risk} |")
            lines.append("")
            lines.append("> F-C (Code Analyst) bu tabloyu F-C bulgularina cevirmeli: degree>30 => `F-C-GOD-01` BLOCKER")
            lines.append("")

    # Communities
    labels = _load_json(labels_json)
    if analysis and "communities" in analysis:
        comms = analysis["communities"]
        lines.append(f"## Communities ({len(comms)} adet)")
        lines.append("| ID | Label | Uye Sayisi | Cohesion |")
        lines.append("|---|---|---|---|")
        cohesion = analysis.get("cohesion", {})
        for cid, members in comms.items():
            label = labels.get(str(cid), f"Community {cid}") if labels else f"Community {cid}"
            count = len(members) if isinstance(members, list) else 0
            coh = cohesion.get(str(cid), cohesion.get(int(cid) if str(cid).isdigit() else cid, "?"))
            coh_str = f"{coh:.2f}" if isinstance(coh, float) else str(coh)
            cohesion_flag = " LOW" if isinstance(coh, float) and coh < 0.3 else ""
            lines.append(f"| {cid} | {label} | {count} | {coh_str}{cohesion_flag} |")
        lines.append("")
        lines.append("> F-C (Config) cohesion < 0.3 olan community'leri SSOT ihlali olarak isaretlemeli.")
        lines.append("")

    # Surprising connections
    if analysis and "surprises" in analysis:
        surprises = analysis["surprises"][:5]
        if surprises:
            lines.append("## Surprising Connections (Gizli Coupling)")
            for s in surprises:
                lines.append(f"- {s.get('description', s)}")
            lines.append("")
            lines.append("> F-A (Adversary) bu baglantilari ariza rotasina cevirmeli: beklenmeyen coupling = sessiz regresyon riski")
            lines.append("")

    # GRAPH_REPORT.md excerpt (God Nodes + Surprising Connections + Suggested Questions)
    if graph_report.exists():
        try:
            report_text = graph_report.read_text(encoding="utf-8")
            # Extract relevant sections
            for section in ["## God Nodes", "## Surprising", "## Suggested Questions", "# God Nodes", "# Surprising"]:
                idx = report_text.find(section)
                if idx != -1:
                    excerpt = report_text[idx:idx+2000]
                    lines.append(f"## Kaynak: GRAPH_REPORT.md excerpt ({section})")
                    lines.append("```markdown")
                    lines.append(excerpt.strip()[:1500])
                    lines.append("```")
                    lines.append("")
                    break
        except Exception:
            pass

    lines.append("---")
    lines.append("## Kullanim Talimati (Ajanlar Icin)")
    lines.append("- **F-C Code Analyst (Structural+Config+Test):** Bu dosyadaki God Node ve Community tablosunu dogrudan `finding-schema.md` formatinda F-C bulgusuna cevir. `source_location` olarak `Agent/graphify-out/graph.json#node:<id>` kullan. Dusuk cohesion'li community'leri modul siniri ihlali olarak raporla. God Node'a karsilik gelen test coverage var mi kontrol et.")
    lines.append("- **F-R Research & Verify (Literature+Verifier):** `graphify query` ile proje terminolojisini dogrula, sonra Context7 ile karsilastir. Tum bulgularin `source_location` hash'ini `graph.json` SHA ile dogrula. INFERRED edge'ler UNVERIFIABLE damgasi alir, sadece EXTRACTED edge'ler CONFIRMED olabilir.")
    lines.append("- **F-A Adversary:** God Node = SPOF, surprising edge = gizli coupling olarak ariza rotasi yaz.")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def export_findings_json(workspace: Path) -> Path:
    """
    graph.json'dan otomatik F-C/F-A/F-R bulgu onerilerini JSON olarak uretir.
    Ajanlar bunu dogrudan kullanabilir veya ilham alabilir.
    """
    graph_json = _get_graphify_out(workspace) / "graph.json"
    analysis_json = _get_graphify_out(workspace) / ".graphify_analysis.json"

    out_path = workspace / ".sherlock" / "graphify-findings.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    findings = []
    data = _load_json(graph_json)
    analysis = _load_json(analysis_json)

    if not data or not analysis:
        out_path.write_text(json.dumps({"findings": [], "note": "graph.json or analysis missing"}, indent=2, ensure_ascii=False), encoding="utf-8")
        return out_path

    gods = analysis.get("gods", [])
    for g in gods:
        deg = g.get("degree", 0)
        nid = g.get("node", g.get("id", "unknown"))
        if isinstance(deg, int) and deg > 30:
            findings.append({
                "id": f"F-C-GOD-{nid}",
                "severity": "BLOCKER",
                "agent": "code-analyst",
                "title": f"God Node: {nid} (degree {deg}) monolitik dosya/modul",
                "evidence": f"Agent/graphify-out/graph.json#{nid} degree={deg}",
                "epistemic_confidence": "CONFIRMED",
                "suggested_action": f"{nid} dosyasini alt modullere bol, facade katmani ekle. Esik: >1400 satir veya >30 edge",
                "falsifier": f"graphify query \"{nid} dependencies\" bos donerse REFUTED",
            })
        elif isinstance(deg, int) and deg > 15:
            findings.append({
                "id": f"F-C-GOD-WARN-{nid}",
                "severity": "MAJOR",
                "agent": "code-analyst",
                "title": f"Yuksek baglanti: {nid} (degree {deg}) izlenmeli",
                "evidence": f"Agent/graphify-out/graph.json#{nid} degree={deg}",
                "epistemic_confidence": "CONFIRMED",
            })

    # Low cohesion communities
    cohesion = analysis.get("cohesion", {})
    for cid, score in cohesion.items():
        if isinstance(score, (int, float)) and score < 0.3:
            findings.append({
                "id": f"F-C-COHESION-{cid}",
                "severity": "MAJOR",
                "agent": "config",
                "title": f"Community {cid} cohesion dusuk ({score:.2f}) - modul siniri daginik",
                "evidence": f"Agent/graphify-out/.graphify_analysis.json cohesion[{cid}]={score}",
                "epistemic_confidence": "CONFIRMED",
            })

    # Surprising connections -> adversary
    surprises = analysis.get("surprises", [])[:5]
    for idx, s in enumerate(surprises):
        desc = s.get("description", str(s)) if isinstance(s, dict) else str(s)
        findings.append({
            "id": f"F-A-SURPRISE-{idx+1:02d}",
            "severity": "MAJOR",
            "agent": "adversary",
            "title": f"Surprising connection: {desc[:80]}",
            "evidence": f"GRAPH_REPORT.md surprising_connections[{idx}]",
            "epistemic_confidence": "CONFIRMED",
            "failure_route": f"Beklenmeyen coupling nedeniyle degisiklik yan etkisi: {desc[:120]}",
        })

    out_path.write_text(json.dumps({"findings": findings, "graph_sha": _sha256(graph_json), "count": len(findings)}, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def inject_case(workspace: Path, case_id: str) -> Path:
    """00-case.md §9 Graphify SSOT bolumunu deterministik doldurur (LLM drift yok).

    Doldurulanlar: SHA, stats, god top5 tablosu, community sayisi, durum + kompakt
    context ozeti. Tam context `.sherlock/graphify-context.md`'de kalir; ajanlar
    SKILL.md AŞAMA 2 geregi o dosyayi dogrudan okur (case'e 9KB gomulmez).
    """
    case_path = workspace / ".sherlock" / case_id / "00-case.md"
    graph_json = _get_graphify_out(workspace) / "graph.json"
    analysis_json = _get_graphify_out(workspace) / ".graphify_analysis.json"

    data = _load_json(graph_json)
    analysis = _load_json(analysis_json)
    active = data is not None

    sha = _sha256(graph_json)
    if active:
        nodes = data.get("nodes", []) if isinstance(data, dict) else []
        links = data.get("links", data.get("edges", [])) if isinstance(data, dict) else []
        stats = f"{len(nodes)} nodes, {len(links)} edges"
        status_val = "GRAPHIFY_ACTIVE"
    else:
        stats = "MISSING"
        status_val = "GRAPHIFY_MISSING_FALLBACK"

    gods_block = "_yok_"
    comm_block = "_yok_"
    if active and analysis:
        gods = (analysis.get("gods", []) or [])[:5]
        if gods:
            rows = ["| Node | Degree |", "|---|---|"]
            for g in gods:
                rows.append(f"| `{g.get('node', g.get('id', '?'))}` | {g.get('degree', g.get('score', '?'))} |")
            gods_block = "\n".join(rows)
        comms = analysis.get("communities", {}) or {}
        comm_block = f"{len(comms)} adet"

    try:
        text = case_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"[graphify-adapter] case bulunamadi: {case_path}")

    text = text.replace("`<sha veya MISSING>`", f"`{sha}`")
    text = text.replace("`<N nodes, M edges veya MISSING>`", f"`{stats}`")
    text = text.replace("`<tablo veya yok>`", f"\n{gods_block}\n")
    text = text.replace("`<N adet veya yok>`", f"`{comm_block}`")
    text = text.replace("`GRAPHIFY_ACTIVE` | `GRAPHIFY_MISSING_FALLBACK`", f"`{status_val}`")

    summary = [
        "<!-- graphify-context.md ozeti (adapter inject, tam dosya: .sherlock/graphify-context.md) -->",
        f"- graph.json SHA: `{sha}` | Stats: `{stats}` | Durum: `{status_val}`",
    ]
    if active and analysis:
        surprises = (analysis.get("surprises", []) or [])[:5]
        for s in surprises:
            if isinstance(s, dict):
                desc = s.get("description")
                if not desc:
                    src = s.get("source", "?")
                    tgt = s.get("target", "?")
                    rel = s.get("relation", s.get("type", "--"))
                    desc = f"`{src}` {rel} `{tgt}`"
            else:
                desc = str(s)
            summary.append(f"- Surprising: {desc[:140]}")
    summary.append("- Ajan gorevi: F-C god+cohesion+coverage, F-A surprising+path, F-R query coverage+SHA dogrulama (SKILL.md ASAMA 2).")
    text = text.replace("<!-- graphify-context.md içeriği buraya inject edilir -->", "\n".join(summary))

    case_path.write_text(text, encoding="utf-8")
    return case_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sherlock x Graphify Adapter")
    parser.add_argument("--workspace", default=".", help="Workspace root (graphify-out'un oldugu yer)")
    parser.add_argument("--ensure", action="store_true", help="graph.json yoksa olustur/varsa tazele")
    parser.add_argument("--auto-update", action="store_true", help="sherlock otomatik-update: yas kontrolsuz kosulsuz `graphify update` (kapsam .graphify_root)")
    parser.add_argument("--export-findings", action="store_true", help="graphify-findings.json uret")
    parser.add_argument("--export-reports", action="store_true", help="Tri-Report (graph.html, CALLFLOW.html, pipeline_graph.html) uret")
    parser.add_argument("--inject-case", default=None, help="00-case.md §9 Graphify SSOT doldur (case_id, orn. 20260907-ornek-dava)")
    parser.add_argument("--query", default=None, help="graphify query sorusu (graph.json varsa calisir)")
    args = parser.parse_args()

    ws = Path(args.workspace).resolve()
    print(f"[graphify-adapter] Workspace: {ws}")

    if args.ensure or args.auto_update:
        status = ensure_graphify(ws, force_update=args.auto_update)
        print(f"[graphify-adapter] Ensure: {json.dumps(status, indent=2, ensure_ascii=False)}")
    elif args.export_reports:
        reports_status = generate_visual_reports(ws)
        print(f"[graphify-adapter] Visual Reports: {json.dumps(reports_status, indent=2, ensure_ascii=False)}")

    ctx_path = build_context_md(ws)
    print(f"[graphify-adapter] Context: {ctx_path} ({ctx_path.stat().st_size} bytes)")

    if args.export_findings:
        findings_path = export_findings_json(ws)
        print(f"[graphify-adapter] Findings: {findings_path}")

    if args.inject_case:
        injected = inject_case(ws, args.inject_case)
        print(f"[graphify-adapter] Injected §9: {injected}")

    if args.query:
        # Try graphify query
        try:
            result = subprocess.run(["graphify", "query", args.query], capture_output=True, text=True, timeout=30, cwd=str(ws), env=_adapter_env(ws))
            print(result.stdout[-2000:] if result.stdout else "(no output)")
            if result.stderr:
                print(f"STDERR: {result.stderr[-500:]}")
        except Exception as e:
            print(f"Query failed: {e}")
