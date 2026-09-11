#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sherlock Pipeline Visualizer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Generates an interactive, Y-shaped pipeline architecture graph (pipeline_graph.html)
using Vis.js standalone. Eliminates amorphous force-directed "hairballs" by grouping
nodes into explicit sequential stages (Stage 1A/1B -> Stage 2 -> Stage 3A/3B + Core)
with toggleable layout modes, hub-isolation switches, stage filters, and node inspectors.
"""

import json
import math
import random
import sys
from pathlib import Path


def categorize_node(node: dict) -> tuple[str, str, int, int]:
    """
    Categorizes a graph node into a pipeline stage, color, and cluster center (x, y).
    Supports bioinformatics/docking pipelines (OneClickDock) and general multi-tier applications.
    """
    sf = (node.get("source_file") or node.get("file") or "").replace("\\", "/").lower()
    nid = (node.get("id") or "").lower()
    combined = f"{sf} {nid}"

    # Stage 1A: Protein Preparation
    if any(k in combined for k in ["protein", "1prepare_protein", "receptor", "pdb_repair", "minimizer", "metal_seeds"]):
        return "STAGE 1A: Protein Preparation", "#38bdf8", -700, -380

    # Stage 1B: Ligand Preparation
    if any(k in combined for k in ["ligand", "2prepare_ligands", "sdf", "smiles", "tautomer", "conformer", "protonation", "microstates"]):
        return "STAGE 1B: Ligand Preparation", "#fb923c", -700, 380

    # Stage 2: Docking Engine / Process Center
    if any(k in combined for k in ["docking", "vina", "smina", "gnina", "qdock", "grid", "box", "3_1docking", "3_2docking", "engine"]):
        return "STAGE 2: Docking Engine", "#34d399", 0, 0

    # Stage 3A: Analysis & Verification
    if any(k in combined for k in ["analysis", "plip", "interaction", "consensus", "4consensus", "binding", "energy", "mmgbsa"]):
        return "STAGE 3A: Analysis & Verification", "#f472b6", 700, -220

    # Stage 3B: Benchmark & Quality
    if any(k in combined for k in ["benchmark", "5benchmark", "quality", "metric", "validation", "roc", "rmsd"]):
        return "STAGE 3B: Benchmark & Quality", "#a78bfa", 700, 220

    # Core / Infrastructure / Utils (SSOT)
    if any(k in combined for k in ["core", "utils", "config", "common", "constants", "logger", "paths", "helper", "base"]):
        return "CORE: Infrastructure & Utils", "#64748b", 0, 750

    # General / Other
    return "OTHER: Modules & Scripts", "#94a3b8", -300, 750


def generate_pipeline_graph(graph_json_path: Path, output_path: Path) -> Path:
    """Reads graph.json and writes an interactive pipeline_graph.html."""
    if not graph_json_path.exists():
        raise FileNotFoundError(f"graph.json not found at: {graph_json_path}")

    data = json.loads(graph_json_path.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    edges = data.get("links", data.get("edges", []))

    # Group nodes by stage
    stage_nodes: dict[str, list[dict]] = {}
    stage_meta: dict[str, dict] = {}

    for n in nodes:
        stage, color, cx, cy = categorize_node(n)
        stage_nodes.setdefault(stage, []).append(n)
        stage_meta[stage] = {"color": color, "cx": cx, "cy": cy}

    # Position each node inside its stage cloud using golden spiral
    random.seed(42)
    node_positions: dict[str, tuple[float, float]] = {}
    for stage, s_nodes in stage_nodes.items():
        cx = stage_meta[stage]["cx"]
        cy = stage_meta[stage]["cy"]
        count = len(s_nodes)
        radius_scale = math.sqrt(count) * 18
        for i, n in enumerate(s_nodes):
            theta = i * 2.399963229728653  # golden angle
            r = radius_scale * math.sqrt((i + 1) / count)
            x = cx + r * math.cos(theta) + random.uniform(-10, 10)
            y = cy + r * math.sin(theta) + random.uniform(-10, 10)
            node_positions[n["id"]] = (round(x, 1), round(y, 1))

    # Process nodes for vis-network
    processed_nodes = []
    stage_counts = {s: len(nl) for s, nl in stage_nodes.items()}

    for n in nodes:
        nid = n["id"]
        stage, color, _, _ = categorize_node(n)
        x, y = node_positions.get(nid, (0, 0))
        deg = n.get("degree", 1)

        size = max(5, min(30, 4 + math.sqrt(deg) * 2.5))
        is_god = deg >= 30

        processed_nodes.append({
            "id": nid,
            "label": n.get("label", nid),
            "stage": stage,
            "color": {
                "background": color,
                "border": "#ffffff" if is_god else color,
                "highlight": {"background": "#ffffff", "border": color}
            },
            "size": size,
            "x": x,
            "y": y,
            "orig_x": x,
            "orig_y": y,
            "font": {"size": 12 if is_god else 0, "color": "#e2e8f0"},
            "title": f"<b>{n.get('label', nid)}</b><br>Stage: {stage}<br>File: {n.get('source_file','')}<br>Degree: {deg}",
            "source_file": n.get("source_file", ""),
            "degree": deg,
            "is_core": "CORE" in stage or "OTHER" in stage
        })

    # Process edges
    processed_edges = []
    for i, e in enumerate(edges):
        src = e.get("source") or e.get("from")
        tgt = e.get("target") or e.get("to")
        rel = e.get("relation") or e.get("label") or "calls"
        processed_edges.append({
            "id": f"e_{i}",
            "from": src,
            "to": tgt,
            "color": {"color": "rgba(148, 163, 184, 0.15)", "highlight": "#38bdf8", "opacity": 0.4},
            "arrows": "to",
            "title": rel,
            "width": 1
        })

    # Pipeline Dataflow Super-Edges (Stage entrypoints)
    super_edges = [
        {"from": "1prepare_protein", "to": "3_1docking", "title": "DATAFLOW: Prepared Receptor -> Docking Engine"},
        {"from": "2prepare_ligands", "to": "3_1docking", "title": "DATAFLOW: Prepared Ligands -> Docking Engine"},
        {"from": "3_1docking", "to": "4consensus", "title": "DATAFLOW: Docking Poses -> Consensus Scoring"},
        {"from": "3_1docking", "to": "5benchmark", "title": "DATAFLOW: Docking Results -> Benchmark Suite"},
    ]

    for se in super_edges:
        if any(n["id"] == se["from"] for n in nodes) and any(n["id"] == se["to"] for n in nodes):
            processed_edges.append({
                "id": f"super_{se['from']}_{se['to']}",
                "from": se["from"],
                "to": se["to"],
                "color": {"color": "#fbbf24", "highlight": "#f59e0b", "opacity": 0.95},
                "width": 4,
                "dashes": [8, 4],
                "arrows": {"to": {"scaleFactor": 1.6}},
                "title": f"<b>{se['title']}</b>",
                "smooth": {"type": "curvedCW", "roundness": 0.2}
            })

    # Stage Legends
    stage_legends_html = ""
    for s_name, meta in stage_meta.items():
        count = stage_counts.get(s_name, 0)
        c = meta["color"]
        stage_legends_html += f"""
        <div class="legend-item" onclick="toggleStage('{s_name}')">
            <span class="legend-dot" style="background: {c};"></span>
            <span class="legend-name">{s_name}</span>
            <span class="legend-count">{count}</span>
            <input type="checkbox" checked id="chk_{s_name.replace(' ', '_').replace(':', '_')}" style="margin-left:auto;" onclick="event.stopPropagation(); toggleStage('{s_name}')">
        </div>
        """

    nodes_json = json.dumps(processed_nodes)
    edges_json = json.dumps(processed_edges)

    html_content = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OneClickDock — Y-Shape Pipeline Architecture Graph</title>
<script src="https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #090d16;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    display: flex;
    height: 100vh;
    overflow: hidden;
  }}
  #graph-container {{
    flex: 1;
    position: relative;
    height: 100%;
  }}
  #graph {{
    width: 100%;
    height: 100%;
  }}
  
  /* Top Banner Controls */
  #top-banner {{
    position: absolute;
    top: 16px;
    left: 20px;
    z-index: 10;
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(15, 23, 42, 0.88);
    backdrop-filter: blur(10px);
    border: 1px solid #334155;
    padding: 10px 18px;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  }}
  .brand-title {{
    font-size: 15px;
    font-weight: 700;
    background: linear-gradient(135deg, #38bdf8, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-right: 12px;
  }}
  .btn {{
    background: #1e293b;
    border: 1px solid #334155;
    color: #e2e8f0;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .btn:hover {{
    background: #334155;
    border-color: #38bdf8;
    color: #38bdf8;
  }}
  .btn.active {{
    background: #0284c7;
    border-color: #38bdf8;
    color: white;
  }}

  /* Search */
  .search-box {{
    position: relative;
  }}
  .search-input {{
    background: #0f172a;
    border: 1px solid #334155;
    color: #e2e8f0;
    padding: 6px 12px;
    border-radius: 8px;
    font-size: 13px;
    width: 220px;
  }}
  .search-input:focus {{
    outline: none;
    border-color: #38bdf8;
  }}
  .search-results {{
    position: absolute;
    top: 36px;
    left: 0;
    width: 280px;
    max-height: 260px;
    overflow-y: auto;
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    display: none;
    z-index: 20;
    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
  }}
  .search-item {{
    padding: 8px 12px;
    font-size: 12px;
    cursor: pointer;
    border-bottom: 1px solid #1e293b;
  }}
  .search-item:hover {{
    background: #1e293b;
    color: #38bdf8;
  }}

  /* Sidebar */
  #sidebar {{
    width: 380px;
    background: #0f172a;
    border-left: 1px solid #1e293b;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}
  .sidebar-header {{
    padding: 18px 20px;
    border-bottom: 1px solid #1e293b;
  }}
  .sidebar-header h2 {{
    font-size: 16px;
    font-weight: 700;
    color: #f8fafc;
  }}
  .sidebar-header p {{
    font-size: 12px;
    color: #94a3b8;
    margin-top: 4px;
  }}
  .sidebar-content {{
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }}

  .card {{
    background: #131d31;
    border: 1px solid #23324d;
    border-radius: 10px;
    padding: 14px 16px;
  }}
  .card-title {{
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
    margin-bottom: 12px;
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 0;
    font-size: 13px;
    cursor: pointer;
  }}
  .legend-item:hover {{
    color: #38bdf8;
  }}
  .legend-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }}
  .legend-name {{
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .legend-count {{
    color: #64748b;
    font-size: 12px;
    font-family: monospace;
  }}

  /* Node Inspector */
  #inspector {{
    display: none;
  }}
  .node-title {{
    font-size: 15px;
    font-weight: 700;
    color: #38bdf8;
    word-break: break-all;
  }}
  .node-meta {{
    font-size: 12px;
    color: #94a3b8;
    margin-top: 6px;
    line-height: 1.5;
  }}
  .node-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    margin-top: 6px;
  }}
  .connection-list {{
    margin-top: 10px;
    font-size: 12px;
    max-height: 180px;
    overflow-y: auto;
  }}
  .connection-item {{
    padding: 4px 6px;
    border-radius: 4px;
    cursor: pointer;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .connection-item:hover {{
    background: #1e293b;
    color: #38bdf8;
  }}
</style>
</head>
<body>

<div id="graph-container">
  <div id="top-banner">
    <div class="brand-title">OneClickDock Mimarisi</div>
    <button class="btn active" id="btn-yshape" onclick="setLayout('yshape')">🎯 Y-Şekli (Pipeline Akışı)</button>
    <button class="btn" id="btn-physics" onclick="setLayout('physics')">🌐 Fizik Simülasyonu</button>
    <button class="btn" id="btn-core-toggle" onclick="toggleCoreNodes()">🔌 Core Katmanını Gizle</button>
    <button class="btn" onclick="network.fit({{ animation: true }})">🔍 Görünümü Sıfırla</button>
    
    <div class="search-box">
      <input type="text" class="search-input" id="search-input" placeholder="Fonksiyon / Script ara...">
      <div class="search-results" id="search-results"></div>
    </div>
  </div>
  <div id="graph"></div>
</div>

<div id="sidebar">
  <div class="sidebar-header">
    <h2>Pipeline & Call Graph</h2>
    <p>{len(nodes)} Düğüm · {len(edges)} Bağlantı · 5 Aşama</p>
  </div>
  <div class="sidebar-content">
    
    <!-- Stage Legends -->
    <div class="card">
      <div class="card-title">Aşama Dağılımı</div>
      {stage_legends_html}
    </div>

    <!-- Inspector -->
    <div class="card" id="inspector">
      <div class="card-title">Düğüm Denetçisi</div>
      <div class="node-title" id="insp-name">-</div>
      <div class="node-badge" id="insp-stage">-</div>
      <div class="node-meta" id="insp-meta">-</div>
      
      <div style="margin-top: 12px;">
        <div class="card-title" style="font-size: 11px;">Bağlantılar (Callers & Callees)</div>
        <div class="connection-list" id="insp-conns"></div>
      </div>
    </div>

    <!-- Quick Guide -->
    <div class="card">
      <div class="card-title">Mimari Notu</div>
      <p style="font-size: 12px; color: #94a3b8; line-height: 1.6;">
        OneClickDock veri akışı Y-şekillidir: <b>Stage 1A (Protein)</b> ve <b>Stage 1B (Ligand)</b> ayrı ayrı hazırlanıp disk artefaktları üzerinden <b>Stage 2 (Docking)</b> motoruna beslenir. Sonuçlar <b>Stage 3A (Analiz)</b> ve <b>Stage 3B (Benchmark)</b> tarafından tüketilir.
      </p>
    </div>

  </div>
</div>

<script>
const RAW_NODES = {nodes_json};
const RAW_EDGES = {edges_json};

let nodesDataSet = new vis.DataSet(RAW_NODES);
let edgesDataSet = new vis.DataSet(RAW_EDGES);

const container = document.getElementById('graph');
const data = {{ nodes: nodesDataSet, edges: edgesDataSet }};

let currentLayoutMode = 'yshape';
let hideCore = false;
let hiddenStages = new Set();

const options = {{
  physics: {{
    enabled: false,
    barnesHut: {{
      gravitationalConstant: -3500,
      centralGravity: 0.15,
      springLength: 95,
      springConstant: 0.04,
      damping: 0.09
    }},
    stabilization: {{ iterations: 120 }}
  }},
  interaction: {{
    hover: true,
    tooltipDelay: 100,
    navigationButtons: true,
    keyboard: true
  }},
  nodes: {{
    shape: 'dot',
    borderWidth: 1.5,
    shadow: true
  }},
  edges: {{
    color: {{ inherit: false }},
    smooth: {{ type: 'continuous' }}
  }}
}};

const network = new vis.Network(container, data, options);

// Layout Mode Switcher
function setLayout(mode) {{
  currentLayoutMode = mode;
  document.getElementById('btn-yshape').classList.toggle('active', mode === 'yshape');
  document.getElementById('btn-physics').classList.toggle('active', mode === 'physics');
  
  if (mode === 'yshape') {{
    network.setOptions({{ physics: {{ enabled: false }} }});
    // Restore stage coordinate positions
    const updates = RAW_NODES.map(n => ({{
      id: n.id,
      x: n.orig_x,
      y: n.orig_y
    }}));
    nodesDataSet.update(updates);
    network.fit({{ animation: true }});
  }} else {{
    network.setOptions({{ physics: {{ enabled: true }} }});
  }}
}}

// Toggle Core Infrastructure nodes
function toggleCoreNodes() {{
  hideCore = !hideCore;
  document.getElementById('btn-core-toggle').classList.toggle('active', hideCore);
  document.getElementById('btn-core-toggle').innerText = hideCore ? "🔌 Core Katmanını Göster" : "🔌 Core Katmanını Gizle";
  
  refreshVisibility();
}}

// Toggle Stage Visibility
function toggleStage(stage) {{
  if (hiddenStages.has(stage)) {{
    hiddenStages.delete(stage);
  }} else {{
    hiddenStages.add(stage);
  }}
  const chk = document.getElementById('chk_' + stage.replace(/ /g, '_').replace(/:/g, '_'));
  if (chk) chk.checked = !hiddenStages.has(stage);
  
  refreshVisibility();
}}

function refreshVisibility() {{
  const updates = [];
  RAW_NODES.forEach(n => {{
    let hidden = false;
    if (hideCore && n.is_core) hidden = true;
    if (hiddenStages.has(n.stage)) hidden = true;
    
    updates.push({{ id: n.id, hidden: hidden }});
  }});
  nodesDataSet.update(updates);
}}

// Node Inspector on Click
network.on('click', function(params) {{
  if (params.nodes.length > 0) {{
    const nodeId = params.nodes[0];
    focusNode(nodeId);
  }} else {{
    document.getElementById('inspector').style.display = 'none';
    resetHighlight();
  }}
}});

function focusNode(nodeId) {{
  const node = RAW_NODES.find(n => n.id === nodeId);
  if (!node) return;
  
  const insp = document.getElementById('inspector');
  insp.style.display = 'block';
  document.getElementById('insp-name').innerText = node.label;
  const badge = document.getElementById('insp-stage');
  badge.innerText = node.stage;
  badge.style.background = node.color.background + '33';
  badge.style.color = node.color.background;
  
  document.getElementById('insp-meta').innerHTML = `
    <b>Dosya:</b> ${{node.source_file || 'N/A'}}<br>
    <b>Derece (Degree):</b> ${{node.degree}}
  `;
  
  // Find connected callers and callees
  const connContainer = document.getElementById('insp-conns');
  connContainer.innerHTML = '';
  
  const connectedNodeIds = new Set();
  RAW_EDGES.forEach(e => {{
    if (e.from === nodeId) {{
      connectedNodeIds.add(e.to);
      const targetNode = RAW_NODES.find(n => n.id === e.to);
      const div = document.createElement('div');
      div.className = 'connection-item';
      div.innerHTML = `<span style="color:#34d399">➔ calls:</span> ${{targetNode ? targetNode.label : e.to}}`;
      div.onclick = (ev) => {{ ev.stopPropagation(); focusNode(e.to); }};
      connContainer.appendChild(div);
    }}
    if (e.to === nodeId) {{
      connectedNodeIds.add(e.from);
      const sourceNode = RAW_NODES.find(n => n.id === e.from);
      const div = document.createElement('div');
      div.className = 'connection-item';
      div.innerHTML = `<span style="color:#38bdf8">⬅ called by:</span> ${{sourceNode ? sourceNode.label : e.from}}`;
      div.onclick = (ev) => {{ ev.stopPropagation(); focusNode(e.from); }};
      connContainer.appendChild(div);
    }}
  }});
  
  if (connectedNodeIds.size === 0) {{
    connContainer.innerHTML = '<div style="color:#64748b;">Doğrudan bağlantı yok.</div>';
  }}
  
  // Highlight neighborhood
  highlightNeighborhood(nodeId, connectedNodeIds);
  
  // Move camera to node
  network.focus(nodeId, {{
    scale: 1.2,
    animation: {{ duration: 500, easingFunction: 'easeInOutQuad' }}
  }});
}}

function highlightNeighborhood(selectedId, neighbors) {{
  const updates = RAW_NODES.map(n => {{
    const isNeighbor = neighbors.has(n.id) || n.id === selectedId;
    return {{
      id: n.id,
      opacity: isNeighbor ? 1.0 : 0.15
    }};
  }});
  nodesDataSet.update(updates);
  
  const edgeUpdates = RAW_EDGES.map(e => {{
    const isConn = e.from === selectedId || e.to === selectedId;
    return {{
      id: e.id,
      color: isConn ? {{ color: '#38bdf8', opacity: 1.0 }} : {{ color: 'rgba(51, 65, 85, 0.1)', opacity: 0.1 }},
      width: isConn ? 3 : 1
    }};
  }});
  edgesDataSet.update(edgeUpdates);
}}

function resetHighlight() {{
  const updates = RAW_NODES.map(n => ({{ id: n.id, opacity: 1.0 }}));
  nodesDataSet.update(updates);
  const edgeUpdates = RAW_EDGES.map(e => ({{
    id: e.id,
    color: {{ color: 'rgba(148, 163, 184, 0.15)', opacity: 0.4 }},
    width: 1
  }}));
  edgesDataSet.update(edgeUpdates);
}}

// Search Filter
const searchInput = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');

searchInput.addEventListener('input', e => {{
  const q = e.target.value.trim().toLowerCase();
  searchResults.innerHTML = '';
  if (!q) {{ searchResults.style.display = 'none'; return; }}
  const matches = RAW_NODES.filter(n => n.label.toLowerCase().includes(q)).slice(0, 15);
  if (!matches.length) {{ searchResults.style.display = 'none'; return; }}
  searchResults.style.display = 'block';
  matches.forEach(n => {{
    const el = document.createElement('div');
    el.className = 'search-item';
    el.innerHTML = `<span style="color:${{n.color.background}}">●</span> ${{n.label}}`;
    el.onclick = () => {{
      focusNode(n.id);
      searchResults.style.display = 'none';
      searchInput.value = '';
    }};
    searchResults.appendChild(el);
  }});
}});
document.addEventListener('click', e => {{
  if (!searchResults.contains(e.target) && e.target !== searchInput) {{
    searchResults.style.display = 'none';
  }}
}});

// Draw Background Phase Labels & Regions
network.on('beforeDrawing', function(ctx) {{
  if (currentLayoutMode !== 'yshape') return;
  
  const regions = [
    {{ title: 'STAGE 1A: PROTEIN PREPARATION', x: -700, y: -380, color: 'rgba(56, 189, 248, 0.05)', border: 'rgba(56, 189, 248, 0.3)', radius: 300 }},
    {{ title: 'STAGE 1B: LIGAND PREPARATION', x: -700, y: 380, color: 'rgba(251, 146, 60, 0.05)', border: 'rgba(251, 146, 60, 0.3)', radius: 280 }},
    {{ title: 'STAGE 2: DOCKING ENGINE', x: 0, y: 0, color: 'rgba(52, 211, 153, 0.05)', border: 'rgba(52, 211, 153, 0.3)', radius: 360 }},
    {{ title: 'STAGE 3A: ANALYSIS', x: 700, y: -220, color: 'rgba(244, 114, 182, 0.05)', border: 'rgba(244, 114, 182, 0.3)', radius: 300 }},
    {{ title: 'STAGE 3B: BENCHMARK', x: 700, y: 220, color: 'rgba(167, 139, 250, 0.05)', border: 'rgba(167, 139, 250, 0.3)', radius: 320 }},
    {{ title: 'INFRASTRUCTURE & CORE (SSOT)', x: 0, y: 750, color: 'rgba(100, 116, 139, 0.03)', border: 'rgba(100, 116, 139, 0.2)', radius: 380 }}
  ];
  
  regions.forEach(reg => {{
    ctx.save();
    ctx.fillStyle = reg.color;
    ctx.strokeStyle = reg.border;
    ctx.lineWidth = 1.5;
    ctx.setLineDash([6, 6]);
    ctx.beginPath();
    ctx.arc(reg.x, reg.y, reg.radius, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();
    
    ctx.font = 'bold 15px -apple-system, sans-serif';
    ctx.fillStyle = reg.border;
    ctx.textAlign = 'center';
    ctx.fillText(reg.title, reg.x, reg.y - reg.radius - 12);
    ctx.restore();
  }});
}});
</script>
</body>
</html>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate Pipeline Architecture Graph HTML")
    parser.add_argument("--graph", default="Agent/graphify-out/graph.json", help="Path to graph.json")
    parser.add_argument("--output", default="Agent/graphify-out/pipeline_graph.html", help="Path to output HTML")
    args = parser.parse_args()

    g_path = Path(args.graph)
    o_path = Path(args.output)
    out = generate_pipeline_graph(g_path, o_path)
    print(f"Pipeline graph HTML generated: {out} ({out.stat().st_size} bytes)")
