#!/usr/bin/env python3
"""Generate a standalone interactive HTML viewer for the IRE focus tree.

Usage:
    python tools/focus_tree_viewer.py
    python tools/focus_tree_viewer.py --focus <IRE_focus.txt> --out <viewer.html>

The generated page is fully self-contained (no CDN, no server) and can be
opened directly in a browser. Re-run it after editing focus coordinates.
"""
from __future__ import annotations

import argparse
import glob
import html
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path

BAND_META = {
    "M": {"label": "M 军事 / 共通", "short": "M 军事"},
    "A": {"label": "A 新世界 / 经济", "short": "A 新世界"},
    "C": {"label": "C 红线 / IRA", "short": "C 红线"},
    "B": {"label": "B 自由邦", "short": "B 自由邦"},
}
BAND_ORDER = ["M", "A", "C", "B"]


def group_of(fid: str) -> str:
    if fid.startswith("IRE_M_"):
        return "M"
    if fid.startswith(("IRE_R_", "IRE_X_", "IRE_ira_")):
        return "C"
    if fid.startswith("IRE_B_") or fid == "IRE_consolidate_free_state":
        return "B"
    return "A"


def parse_focus_file(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    nodes = []
    for m in re.finditer(r"focus\s*=\s*\{", text):
        start = m.end() - 1
        depth = 0
        i = start
        while i < len(text):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        block = text[start:i + 1]
        mid = re.search(r"^\s*id\s*=\s*(IRE_[A-Za-z0-9_]+)", block, re.M)
        if not mid:
            continue
        fid = mid.group(1)
        mx = re.search(r"^\s*x\s*=\s*(-?\d+)", block, re.M)
        my = re.search(r"^\s*y\s*=\s*(-?\d+)", block, re.M)
        if not mx or not my:
            print(f"warning: {fid} has no absolute x/y, skipped", file=sys.stderr)
            continue
        pre = []
        for pm in re.finditer(r"prerequisite\s*=\s*\{([^}]*)\}", block, re.S):
            pre += re.findall(r"focus\s*=\s*([A-Za-z0-9_]+)", pm.group(1))
        me = []
        for mm in re.finditer(r"mutually_exclusive\s*=\s*\{([^}]*)\}", block, re.S):
            me += re.findall(r"focus\s*=\s*([A-Za-z0-9_]+)", mm.group(1))
        cost = re.search(r"^\s*cost\s*=\s*(-?\d+)", block, re.M)
        nodes.append({
            "id": fid,
            "x": int(mx.group(1)),
            "y": int(my.group(1)),
            "g": group_of(fid),
            "pre": sorted(set(pre)),
            "me": sorted(set(me)),
            "cost": int(cost.group(1)) if cost else None,
        })
    ids = {n["id"] for n in nodes}
    for n in nodes:
        n["pre"] = [p for p in n["pre"] if p in ids]
        n["me"] = [p for p in n["me"] if p in ids]
    return nodes


def parse_names(loc_dir: Path):
    names = {}
    files = sorted(glob.glob(str(loc_dir / "*.yml")))
    for fp in files:
        raw = Path(fp).read_text(encoding="utf-8-sig", errors="replace")
        for line in raw.splitlines():
            m = re.match(r'^\s*([A-Za-z0-9_]+):\d*\s+"(.*)"\s*$', line)
            if not m:
                continue
            key, value = m.group(1), m.group(2)
            if key in names:
                continue
            value = value.replace('\\"', '"').replace("\\n", " ").strip()
            value = re.sub(r"§.", "", value).strip()
            if value:
                names[key] = value
    return names


def orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def strict_intersection(p1, p2, p3, p4):
    d1 = orient(p3, p4, p1)
    d2 = orient(p3, p4, p2)
    d3 = orient(p1, p2, p3)
    d4 = orient(p1, p2, p4)
    if not ((d1 > 0) != (d2 > 0) and (d3 > 0) != (d4 > 0)):
        return None
    den = (p1[0] - p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] - p4[0])
    if abs(den) < 1e-12:
        return None
    px = ((p1[0] * p2[1] - p1[1] * p2[0]) * (p3[0] - p4[0])
          - (p1[0] - p2[0]) * (p3[0] * p4[1] - p3[1] * p4[0])) / den
    py = ((p1[0] * p2[1] - p1[1] * p2[0]) * (p3[1] - p4[1])
          - (p1[1] - p2[1]) * (p3[0] * p4[1] - p3[1] * p4[0])) / den
    return (px, py)


def analyse(nodes):
    by_id = {n["id"]: n for n in nodes}
    edges = []
    for n in nodes:
        for p in n["pre"]:
            edges.append((p, n["id"]))
    edges.sort()
    crossings = []
    for i in range(len(edges)):
        a, b = edges[i]
        na, nb = by_id[a], by_id[b]
        p1, p2 = (na["x"], na["y"]), (nb["x"], nb["y"])
        for j in range(i + 1, len(edges)):
            c, d = edges[j]
            if len({a, b, c, d}) < 4:
                continue
            nc, nd = by_id[c], by_id[d]
            pt = strict_intersection(p1, p2, (nc["x"], nc["y"]), (nd["x"], nd["y"]))
            if pt:
                crossings.append({
                    "x": round(pt[0], 3),
                    "y": round(pt[1], 3),
                    "a": [a, b],
                    "b": [c, d],
                })
    crossings.sort(key=lambda z: (z["y"], z["x"]))
    same_row = []
    for n in nodes:
        for p in n["pre"]:
            if p in by_id and by_id[p]["y"] >= n["y"]:
                same_row.append({
                    "child": n["id"],
                    "parent": p,
                    "py": by_id[p]["y"],
                    "cy": n["y"],
                })
    same_row.sort(key=lambda z: (z["py"], z["child"]))
    dup = {}
    for n in nodes:
        dup.setdefault((n["x"], n["y"]), []).append(n["id"])
    duplicates = [{"x": k[0], "y": k[1], "ids": v} for k, v in dup.items() if len(v) > 1]
    bands = {}
    for g in BAND_ORDER:
        members = [n for n in nodes if n["g"] == g]
        if not members:
            continue
        roots = [n["id"] for n in members if not n["pre"]]
        bands[g] = {
            "label": BAND_META[g]["label"],
            "short": BAND_META[g]["short"],
            "count": len(members),
            "minX": min(n["x"] for n in members),
            "maxX": max(n["x"] for n in members),
            "minY": min(n["y"] for n in members),
            "maxY": max(n["y"] for n in members),
            "roots": roots,
        }
    bounds = {
        "minX": min(n["x"] for n in nodes),
        "maxX": max(n["x"] for n in nodes),
        "minY": min(n["y"] for n in nodes),
        "maxY": max(n["y"] for n in nodes),
    }
    return {
        "edges": edges,
        "crossings": crossings,
        "sameRow": same_row,
        "duplicates": duplicates,
        "bands": bands,
        "bounds": bounds,
    }


def build_payload(focus_path: Path, loc_dir: Path, repo_root: Path):
    nodes = parse_focus_file(focus_path)
    names = parse_names(loc_dir)
    for n in nodes:
        n["name"] = names.get(n["id"], n["id"])
        n["root"] = not n["pre"]
    analysis = analyse(nodes)
    try:
        source = str(focus_path.resolve().relative_to(repo_root.resolve())).replace("\\", "/")
    except ValueError:
        source = str(focus_path)
    return {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": source,
        "nodes": nodes,
        **analysis,
    }


def main():
    here = Path(__file__).resolve()
    default_root = here.parent.parent
    ap = argparse.ArgumentParser(description="Generate the IRE focus tree HTML viewer")
    ap.add_argument("--focus", type=Path,
                    default=default_root / "mods/ire_the_emerald_isle/common/national_focus/IRE_focus.txt")
    ap.add_argument("--loc", type=Path,
                    default=default_root / "mods/ire_the_emerald_isle/localisation/simp_chinese")
    ap.add_argument("--out", type=Path, default=default_root / "tools/focus_tree_viewer.html")
    args = ap.parse_args()

    if not args.focus.exists():
        sys.exit(f"focus file not found: {args.focus}")
    payload = build_payload(args.focus, args.loc, default_root)
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html_text = HTML_TEMPLATE.replace("/*__DATA__*/", data_json)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html_text, encoding="utf-8", newline="\n")

    nodes = payload["nodes"]
    print(f"wrote {args.out}")
    print(f"  focuses: {len(nodes)}  bands: " + ", ".join(f"{g}={payload['bands'][g]['count']}" for g in BAND_ORDER if g in payload['bands']))
    print(f"  crossings: {len(payload['crossings'])}  duplicates: {len(payload['duplicates'])}  same-row prereq: {len(payload['sameRow'])}")
    print(f"  size: {args.out.stat().st_size / 1024:.1f} KiB")


HTML_TEMPLATE = r'''<!doctype html>
<!-- Generated by tools/focus_tree_viewer.py. Re-run the script instead of editing this file. -->
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>翡翠岛的抉择 · 国策树布局查看器</title>
<script>
(function () {
  var theme = "light";
  try {
    var saved = localStorage.getItem("ire-focus-theme");
    if (saved === "light" || saved === "dark") theme = saved;
    else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) theme = "dark";
  } catch (err) {}
  document.documentElement.dataset.theme = theme;
})();
</script>
<style>
  :root {
    --bg: #f6f5f2;
    --panel: #fbfaf8;
    --canvas: #f1efe9;
    --text: #242522;
    --muted: #74746e;
    --line: #dedbd3;
    --edge: #8b857b;
    --accent: #3f6f5a;
    --accent-soft: #e4ece7;
    --me: #a7665b;
    --cross: #b4682f;
    --band-m: #8a6326;
    --band-a: #47704f;
    --band-c: #a35448;
    --band-b: #4e6f96;
    --tip: #2a2b27;
    --tip-text: #f5f3ee;
  }
  :root[data-theme="dark"] {
    --bg: #17181a;
    --panel: #1d1e21;
    --canvas: #141517;
    --text: #e6e3dc;
    --muted: #9a978f;
    --line: #303237;
    --edge: #55585e;
    --accent: #7fb39a;
    --accent-soft: #22332c;
    --me: #c98f84;
    --cross: #d39a62;
    --band-m: #c9a35e;
    --band-a: #7fb08f;
    --band-c: #cf8378;
    --band-b: #87a7ca;
    --tip: #ece8df;
    --tip-text: #1d1e21;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 13px;
    line-height: 1.5;
  }
  button, input { font: inherit; color: inherit; }
  .app { height: 100vh; display: flex; flex-direction: column; min-height: 0; }
  header {
    display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap;
    padding: 12px 16px 8px; border-bottom: 1px solid var(--line);
  }
  header h1 { margin: 0; font-size: 15px; font-weight: 500; letter-spacing: .01em; }
  header .sub { color: var(--muted); font-size: 12px; }
  .toolbar {
    display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    padding: 8px 16px; border-bottom: 1px solid var(--line);
  }
  .group { display: flex; align-items: center; gap: 4px; }
  .group + .group { padding-left: 8px; border-left: 1px solid var(--line); }
  .tbtn, .chip, .cross-row, .band-row, .search-result {
    border: 1px solid var(--line); background: transparent; color: var(--text);
    border-radius: 5px; padding: 4px 9px; cursor: pointer; white-space: nowrap;
  }
  .tbtn:hover, .chip:hover, .cross-row:hover, .band-row:hover, .search-result:hover { border-color: var(--accent); }
  .tbtn.active { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); }
  .tbtn.icon { min-width: 30px; padding: 4px 7px; text-align: center; }
  label.toggle { display: inline-flex; align-items: center; gap: 5px; color: var(--muted); cursor: pointer; user-select: none; white-space: nowrap; }
  label.toggle input { accent-color: var(--accent); margin: 0; }
  .search-wrap { position: relative; margin-left: auto; min-width: 210px; flex: 0 1 300px; }
  .search-wrap input {
    width: 100%; border: 1px solid var(--line); background: var(--panel); border-radius: 5px;
    padding: 5px 9px; outline: none;
  }
  .search-wrap input:focus { border-color: var(--accent); }
  .search-results {
    position: absolute; right: 0; top: calc(100% + 4px); z-index: 20; min-width: 100%;
    max-height: 270px; overflow: auto; background: var(--panel); border: 1px solid var(--line);
    border-radius: 6px; padding: 4px; box-shadow: 0 8px 24px rgba(0,0,0,.12);
  }
  .search-result { display: block; width: 100%; text-align: left; border: 0; padding: 5px 8px; }
  .search-result .id { color: var(--muted); font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 11px; margin-left: 6px; }
  .search-result.active { background: var(--accent-soft); }
  main { flex: 1; min-height: 0; display: grid; grid-template-columns: minmax(0, 1fr) 330px; }
  #viewer { position: relative; min-width: 0; min-height: 0; outline: none; overflow: hidden; background: var(--canvas); }
  #viewer:focus-visible { box-shadow: inset 0 0 0 2px var(--accent); }
  #tree { width: 100%; height: 100%; display: block; touch-action: none; }
  .band { fill-opacity: .055; stroke-opacity: .22; stroke-width: 1; vector-effect: non-scaling-stroke; }
  .band-M { fill: var(--band-m); stroke: var(--band-m); }
  .band-A { fill: var(--band-a); stroke: var(--band-a); }
  .band-C { fill: var(--band-c); stroke: var(--band-c); }
  .band-B { fill: var(--band-b); stroke: var(--band-b); }
  .band-label { font-size: 1.5px; font-weight: 500; letter-spacing: .04em; }
  .band-label-M { fill: var(--band-m); }
  .band-label-A { fill: var(--band-a); }
  .band-label-C { fill: var(--band-c); }
  .band-label-B { fill: var(--band-b); }
  #tree.detail .band-label { display: none; }
  .edge { stroke: var(--edge); stroke-width: 1; opacity: .65; vector-effect: non-scaling-stroke; }
  .edge.related { stroke: var(--accent); stroke-width: 1.6; opacity: 1; }
  .edge.dim { opacity: .12; }
  .edge.flash { stroke: var(--cross); stroke-width: 2.2; opacity: 1; }
  .me-edge { stroke: var(--me); stroke-width: 1; opacity: .45; stroke-dasharray: 4 4; vector-effect: non-scaling-stroke; }
  .me-edge.related { opacity: .95; stroke-width: 1.5; }
  .me-edge.dim { opacity: .1; }
  .crossing { fill: none; stroke: var(--cross); stroke-width: 1.4; vector-effect: non-scaling-stroke; opacity: .9; }
  #me-edges[hidden], #crossings[hidden] { display: none; }
  .node { cursor: pointer; }
  .node .hit { fill: transparent; }
  .node .node-box { stroke: var(--canvas); stroke-width: 1; vector-effect: non-scaling-stroke; }
  .node[data-band="M"] .node-box { fill: var(--band-m); }
  .node[data-band="A"] .node-box { fill: var(--band-a); }
  .node[data-band="C"] .node-box { fill: var(--band-c); }
  .node[data-band="B"] .node-box { fill: var(--band-b); }
  .node:hover .node-box { stroke: var(--accent); stroke-width: 2.2; }
  .node.root .node-box { stroke: var(--text); stroke-width: 1.8; }
  .node.related .node-box { stroke: var(--accent); stroke-width: 1.8; }
  .node.selected .node-box { stroke: var(--accent); stroke-width: 2.8; }
  .node.flash .node-box { stroke: var(--cross); stroke-width: 2.8; }
  .node.dim { opacity: .22; }
  .node-label {
    display: none; font-size: var(--label-font, .5px); fill: var(--text);
    text-anchor: start; paint-order: stroke; stroke: var(--canvas); stroke-width: .12em; stroke-linejoin: round;
    pointer-events: none;
  }
  #tree.labels-on.detail .node-label { display: block; }
  #tip {
    position: absolute; z-index: 10; pointer-events: none; max-width: 250px;
    background: var(--tip); color: var(--tip-text); border-radius: 5px; padding: 6px 8px;
    font-size: 12px; line-height: 1.45; box-shadow: 0 4px 16px rgba(0,0,0,.18);
  }
  #tip strong { display: block; font-weight: 500; }
  #tip span { display: block; opacity: .78; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 11px; }
  #panel { overflow: auto; border-left: 1px solid var(--line); background: var(--panel); padding: 12px 14px 24px; }
  #panel h2 { margin: 0 0 2px; font-size: 15px; font-weight: 500; }
  #panel h3 { margin: 16px 0 6px; font-size: 11px; font-weight: 500; letter-spacing: .08em; color: var(--muted); text-transform: uppercase; }
  .mono { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; color: var(--muted); font-size: 11px; }
  .badge { display: inline-flex; align-items: center; gap: 5px; border: 1px solid var(--line); border-radius: 999px; padding: 1px 7px; font-size: 11px; color: var(--muted); }
  .badge i { width: 7px; height: 7px; border-radius: 2px; display: inline-block; }
  .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 10px; margin-top: 10px; }
  .stat-grid div { border-top: 1px solid var(--line); padding-top: 5px; }
  .stat-grid span { display: block; color: var(--muted); font-size: 11px; }
  .stat-grid strong { font-weight: 500; font-size: 17px; font-variant-numeric: tabular-nums; }
  .stat-grid strong.warn { color: var(--cross); }
  .band-table { width: 100%; border-collapse: collapse; }
  .band-table td { padding: 3px 0; vertical-align: baseline; }
  .band-table td:last-child { text-align: right; color: var(--muted); font-variant-numeric: tabular-nums; }
  .band-row { border: 0; padding: 3px 4px; width: 100%; text-align: left; border-radius: 4px; }
  .band-row .sw { display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin-right: 6px; }
  .chips { display: flex; flex-wrap: wrap; gap: 4px; }
  .chip { padding: 3px 7px; font-size: 12px; max-width: 100%; overflow: hidden; text-overflow: ellipsis; }
  .cross-row { display: block; width: 100%; text-align: left; font-size: 12px; margin: 0 0 4px; line-height: 1.4; }
  .cross-row .dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; border: 1px solid var(--cross); margin-right: 6px; vertical-align: 1px; }
  .muted { color: var(--muted); }
  .empty { color: var(--muted); font-size: 12px; }
  .actions { display: flex; gap: 6px; margin-top: 12px; flex-wrap: wrap; }
  footer {
    display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap;
    padding: 5px 16px; border-top: 1px solid var(--line); color: var(--muted); font-size: 11px;
    font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  }
  @media (max-width: 900px) {
    .app { height: auto; min-height: 100vh; }
    main { grid-template-columns: 1fr; grid-template-rows: 62vh auto; }
    #viewer { min-height: 380px; }
    #panel { border-left: 0; border-top: 1px solid var(--line); }
    .search-wrap { margin-left: 0; flex: 1 1 100%; }
  }
  @media (max-width: 520px) {
    header, .toolbar { padding-left: 10px; padding-right: 10px; }
    .group + .group { padding-left: 4px; }
    .tbtn { padding: 4px 7px; }
    #viewer { min-height: 330px; }
  }
  @media (prefers-reduced-motion: reduce) {
    * { scroll-behavior: auto !important; transition: none !important; }
  }
</style>
</head>
<body>
<div class="app">
  <header>
    <h1>翡翠岛的抉择 · 国策树布局</h1>
    <span class="sub" id="headline"></span>
  </header>
  <div class="toolbar">
    <div class="group" id="band-buttons">
      <button class="tbtn active" data-band="all">全树</button>
      <button class="tbtn" data-band="M" title="M 军事 / 共通">M</button>
      <button class="tbtn" data-band="A" title="A 新世界 / 经济">A</button>
      <button class="tbtn" data-band="C" title="C 红线 / IRA">C</button>
      <button class="tbtn" data-band="B" title="B 自由邦">B</button>
    </div>
    <div class="group">
      <button class="tbtn icon" id="zoom-out" title="缩小" aria-label="缩小">−</button>
      <button class="tbtn icon" id="zoom-in" title="放大" aria-label="放大">+</button>
      <button class="tbtn" id="fit" title="适应全树 (0)">适应</button>
    </div>
    <div class="group">
      <label class="toggle" title="放大后显示国策名"><input type="checkbox" id="toggle-labels" checked> 名称</label>
      <label class="toggle"><input type="checkbox" id="toggle-me"> 互斥线</label>
      <label class="toggle"><input type="checkbox" id="toggle-cross" checked> 交叉点</label>
      <label class="toggle"><input type="checkbox" id="toggle-theme"> 深色</label>
    </div>
    <div class="search-wrap">
      <input id="search" type="text" placeholder="搜索国策名或 ID…" autocomplete="off" aria-label="搜索国策">
      <div class="search-results" id="search-results" hidden></div>
    </div>
  </div>
  <main>
    <div id="viewer" tabindex="0" aria-label="国策树分布图，可拖动平移，滚轮缩放">
      <svg id="tree" role="img" aria-label="爱尔兰国策树分布图"></svg>
      <div id="tip" role="tooltip" hidden></div>
    </div>
    <aside id="panel" aria-live="polite"></aside>
  </main>
  <footer>
    <span id="cursor">x — · y —</span>
    <span id="source"></span>
  </footer>
</div>
<noscript>需要启用 JavaScript 才能查看分布图。</noscript>
<script>
(function () {
  "use strict";
  const DATA = /*__DATA__*/;
  const NS = "http://www.w3.org/2000/svg";
  const $ = (sel, root) => (root || document).querySelector(sel);
  const svg = $("#tree");
  const viewer = $("#viewer");
  const tip = $("#tip");
  const panel = $("#panel");
  const cursorEl = $("#cursor");
  const byId = new Map(DATA.nodes.map(n => [n.id, n]));
  const succ = new Map(DATA.nodes.map(n => [n.id, []]));
  const mePairs = new Set();
  for (const n of DATA.nodes) {
    for (const p of n.pre) {
      if (byId.has(p)) succ.get(p).push(n.id);
    }
    for (const m of n.me) mePairs.add([n.id, m].sort().join("~"));
  }
  const bandMeta = DATA.bands;
  const bandOrder = ["M", "A", "C", "B"];
  const nodeEls = new Map();
  const edgeEls = new Map();
  const meEls = [];
  const crossingEls = [];
  let view = { x: 0, y: 0, w: 100, h: 30 };
  let selectedId = null;
  let hoverId = null;
  let drag = null;
  let moved = false;
  let flashTimer = 0;
  let activeCrossing = null;

  const esc = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const bandName = g => (bandMeta[g] && bandMeta[g].label) || g;
  const shortName = name => (name.length > 4 ? name.slice(0, 3) + "…" : name);
  const round1 = n => Math.round(n * 10) / 10;

  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    if (attrs) for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }

  function buildSvg() {
    const bandsG = el("g", { id: "bands" }, svg);
    const edgesG = el("g", { id: "edges" }, svg);
    const meG = el("g", { id: "me-edges" }, svg);
    const crossG = el("g", { id: "crossings" }, svg);
    const nodesG = el("g", { id: "nodes" }, svg);

    for (const g of bandOrder) {
      const b = bandMeta[g];
      if (!b) continue;
      el("rect", {
        x: b.minX - 0.7, y: b.minY - 0.7,
        width: b.maxX - b.minX + 1.4, height: b.maxY - b.minY + 1.4,
        rx: 0.5, "class": "band band-" + g
      }, bandsG);
      const t = el("text", { x: b.minX, y: b.minY - 1.15, "class": "band-label band-label-" + g }, bandsG);
      t.textContent = b.short;
    }

    for (const [a, b] of DATA.edges) {
      const na = byId.get(a), nb = byId.get(b);
      if (!na || !nb) continue;
      const line = el("line", {
        x1: na.x, y1: na.y, x2: nb.x, y2: nb.y,
        "class": "edge", "data-from": a, "data-to": b
      }, edgesG);
      edgeEls.set(a + ">" + b, line);
    }

    const meSeen = new Set();
    for (const n of DATA.nodes) {
      for (const m of n.me) {
        const key = [n.id, m].sort().join("~");
        if (meSeen.has(key)) continue;
        meSeen.add(key);
        const other = byId.get(m);
        if (!other) continue;
        const line = el("line", {
          x1: n.x, y1: n.y, x2: other.x, y2: other.y,
          "class": "me-edge", "data-a": n.id, "data-b": m
        }, meG);
        el("title", {}, line).textContent = "互斥：" + n.name + " / " + other.name;
        meEls.push(line);
      }
    }

    DATA.crossings.forEach((c, idx) => {
      const circle = el("circle", { cx: c.x, cy: c.y, r: 0.22, "class": "crossing" }, crossG);
      const title = el("title", {}, circle);
      title.textContent = "交叉 " + (idx + 1) + "：" + c.a[0] + " → " + c.a[1] + " × " + c.b[0] + " → " + c.b[1];
      crossingEls.push(circle);
    });

    for (const n of DATA.nodes) {
      const g = el("g", {
        "class": "node" + (n.root ? " root" : ""),
        "data-id": n.id, "data-band": n.g,
        transform: "translate(" + n.x + " " + n.y + ")"
      }, nodesG);
      el("title", {}, g).textContent = n.name + "\n" + n.id + " · " + n.g + " 线 · (" + n.x + ", " + n.y + ")";
      el("rect", { x: -0.8, y: -0.8, width: 1.6, height: 1.6, "class": "hit" }, g);
      el("rect", { x: -0.42, y: -0.42, width: 0.84, height: 0.84, rx: 0.14, "class": "node-box" }, g);
      const label = el("text", { x: 0.58, y: 0, "class": "node-label", "dominant-baseline": "middle" }, g);
      label.textContent = shortName(n.name);
      nodeEls.set(n.id, g);
      g.addEventListener("pointerenter", e => {
        hoverId = n.id;
        updateHighlight();
        showTip(n, e);
      });
      g.addEventListener("pointermove", e => { if (hoverId === n.id) moveTip(e); });
      g.addEventListener("pointerleave", () => {
        if (hoverId === n.id) hoverId = null;
        updateHighlight();
        hideTip();
      });
      g.addEventListener("click", e => {
        e.stopPropagation();
        selectNode(n.id);
      });
    }
    svg.setAttribute("data-rendered", String(DATA.nodes.length));
  }

  function svgAspect() {
    return Math.max(0.35, svg.clientWidth / Math.max(1, svg.clientHeight));
  }

  function setView(v) {
    view = v;
    clampView();
    applyView();
  }

  function clampView() {
    const b = DATA.bounds;
    const pad = 8;
    const minX = b.minX - pad, maxX = b.maxX + pad;
    const minY = b.minY - pad, maxY = b.maxY + pad;
    if (view.w >= maxX - minX) view.x = (minX + maxX - view.w) / 2;
    else view.x = Math.min(Math.max(view.x, minX), maxX - view.w);
    if (view.h >= maxY - minY) view.y = (minY + maxY - view.h) / 2;
    else view.y = Math.min(Math.max(view.y, minY), maxY - view.h);
  }

  function applyView() {
    svg.setAttribute("viewBox", round1(view.x) + " " + round1(view.y) + " " + round1(view.w) + " " + round1(view.h));
    const unitsPerPx = view.w / Math.max(1, svg.clientWidth);
    svg.style.setProperty("--label-font", (11 * unitsPerPx) + "px");
    svg.classList.toggle("detail", view.w < 55);
    svg.classList.toggle("labels-on", $("#toggle-labels").checked);
    svg.classList.toggle("zoomed-in", view.w < 90);
  }

  function fitBounds(b, pad) {
    pad = pad == null ? 2.4 : pad;
    let w = (b.maxX - b.minX) + pad * 2;
    let h = (b.maxY - b.minY) + pad * 2;
    const ar = svgAspect();
    if (w / h > ar) h = w / ar;
    else w = h * ar;
    const cx = (b.minX + b.maxX) / 2;
    const cy = (b.minY + b.maxY) / 2;
    setView({ x: cx - w / 2, y: cy - h / 2, w, h });
  }

  function fitAll() {
    fitBounds(DATA.bounds, 2.6);
    setActiveBand("all");
  }

  function centerOn(id, widthUnits) {
    const n = byId.get(id);
    if (!n) return;
    setActiveBand(null);
    const ar = svgAspect();
    const w = Math.min(Math.max(widthUnits || 34, 14), (DATA.bounds.maxX - DATA.bounds.minX) + 12);
    const h = w / ar;
    setView({ x: n.x - w / 2, y: n.y - h / 2, w, h });
  }

  function zoomAt(factor, cx, cy) {
    const ar = svgAspect();
    const minW = 12;
    const maxW = (DATA.bounds.maxX - DATA.bounds.minX) + 18;
    const w = Math.min(Math.max(view.w / factor, minW), maxW);
    const h = w / ar;
    const x = cx - (cx - view.x) * (w / view.w);
    const y = cy - (cy - view.y) * (h / view.h);
    setView({ x, y, w, h });
    setActiveBand(null);
  }

  function zoomBy(factor) {
    zoomAt(factor, view.x + view.w / 2, view.y + view.h / 2);
  }

  function svgPoint(clientX, clientY) {
    const pt = svg.createSVGPoint();
    pt.x = clientX; pt.y = clientY;
    const m = svg.getScreenCTM();
    if (!m) return { x: view.x, y: view.y };
    const p = pt.matrixTransform(m.inverse());
    return { x: p.x, y: p.y };
  }

  function setActiveBand(g) {
    document.querySelectorAll("#band-buttons .tbtn").forEach(b => {
      b.classList.toggle("active", b.dataset.band === (g || ""));
    });
  }

  function focusBand(g) {
    if (g === "all") { fitAll(); return; }
    const b = bandMeta[g];
    if (!b) return;
    fitBounds(b, 2.6);
    setActiveBand(g);
  }

  function showTip(n, e) {
    tip.innerHTML = "<strong>" + esc(n.name) + "</strong><span>" + esc(n.id) + " · " + n.g + " 线 · (" + n.x + ", " + n.y + ")</span>";
    tip.hidden = false;
    moveTip(e);
  }

  function moveTip(e) {
    if (tip.hidden) return;
    const r = viewer.getBoundingClientRect();
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    let x = e.clientX - r.left + 14;
    let y = e.clientY - r.top + 14;
    if (x + tw > r.width - 8) x = e.clientX - r.left - tw - 14;
    if (y + th > r.height - 8) y = e.clientY - r.top - th - 14;
    tip.style.left = Math.max(8, x) + "px";
    tip.style.top = Math.max(8, y) + "px";
  }

  function hideTip() { tip.hidden = true; }

  function selectNode(id, center) {
    selectedId = id;
    updateHighlight();
    renderPanel();
    if (center) centerOn(id, 32);
    hideSearch();
  }

  function clearSelection() {
    selectedId = null;
    updateHighlight();
    renderPanel();
  }

  function updateHighlight() {
    const active = hoverId || selectedId;
    const related = new Set();
    if (active) {
      related.add(active);
      const n = byId.get(active);
      if (n) {
        n.pre.forEach(p => related.add(p));
        (succ.get(active) || []).forEach(s => related.add(s));
        n.me.forEach(m => related.add(m));
      }
    }
    nodeEls.forEach((g, id) => {
      g.classList.toggle("selected", id === selectedId);
      g.classList.toggle("related", !!active && related.has(id) && id !== active);
      g.classList.toggle("dim", !!active && !related.has(id));
    });
    edgeEls.forEach((line, key) => {
      const parts = key.split(">");
      const rel = !!active && (parts[0] === active || parts[1] === active);
      line.classList.toggle("related", rel);
      line.classList.toggle("dim", !!active && !rel);
    });
    meEls.forEach(line => {
      const rel = !!active && (line.getAttribute("data-a") === active || line.getAttribute("data-b") === active);
      line.classList.toggle("related", rel);
      line.classList.toggle("dim", !!active && !rel);
    });
  }

  function chip(id, text) {
    const n = byId.get(id);
    return '<button class="chip" data-goto="' + esc(id) + '" title="' + esc(n ? n.name + " · " + id : id) + '">' + esc(text || (n ? n.name : id)) + "</button>";
  }

  function renderPanel() {
    if (selectedId) {
      renderSelected(selectedId);
    } else {
      renderOverview();
    }
  }

  function renderOverview() {
    const b = DATA.bounds;
    const warn = DATA.crossings.length;
    let bandRows = "";
    for (const g of bandOrder) {
      const band = bandMeta[g];
      if (!band) continue;
      const root = band.roots.length ? byId.get(band.roots[0]) : null;
      bandRows += '<tr><td><button class="band-row" data-band="' + g + '"><span class="sw" style="background:var(--band-' + g.toLowerCase() + ')"></span>' +
        esc(band.label) + '</button></td><td>' + band.count + " 个 · x " + band.minX + "–" + band.maxX + " · y " + band.minY + "–" + band.maxY +
        (root ? "<br><span class=\"muted\">起点：" + esc(root.name) + "</span>" : "") + "</td></tr>";
    }
    let crossRows = "";
    if (DATA.crossings.length === 0) {
      crossRows = '<div class="empty">没有线段交叉。</div>';
    } else {
      DATA.crossings.forEach((c, i) => {
        const a1 = byId.get(c.a[0]), a2 = byId.get(c.a[1]), b1 = byId.get(c.b[0]), b2 = byId.get(c.b[1]);
        crossRows += '<button class="cross-row" data-cross="' + i + '" title="定位到交叉点">' +
          '<span class="dot"></span>' + esc(a1 ? a1.name : c.a[0]) + " → " + esc(a2 ? a2.name : c.a[1]) +
          " × " + esc(b1 ? b1.name : c.b[0]) + " → " + esc(b2 ? b2.name : c.b[1]) + "</button>";
      });
    }
    let sameRows = "";
    if (!DATA.sameRow.length) {
      sameRows = '<div class="empty">没有前置与后续同排。</div>';
    } else {
      DATA.sameRow.forEach(z => {
        const child = byId.get(z.child), parent = byId.get(z.parent);
        sameRows += '<button class="cross-row" data-goto="' + esc(z.child) + '">' +
          '<span class="dot"></span>' + esc(child ? child.name : z.child) + " ← " + esc(parent ? parent.name : z.parent) +
          ' <span class="muted">（y ' + z.py + " → " + z.cy + "）</span></button>";
      });
    }
    let dupRows = "";
    if (DATA.duplicates.length) {
      for (const d of DATA.duplicates) {
        dupRows += '<div class="cross-row">(' + d.x + ", " + d.y + ")：" + d.ids.map(esc).join(", ") + "</div>";
      }
    }
    panel.innerHTML =
      '<h2>布局总览</h2>' +
      '<div class="mono">' + esc(DATA.source) + "</div>" +
      '<div class="stat-grid">' +
        "<div><span>国策</span><strong>" + DATA.nodes.length + "</strong></div>" +
        "<div><span>分线</span><strong>" + Object.keys(bandMeta).length + "</strong></div>" +
        "<div><span>连线交叉</span><strong class=\"" + (warn ? "warn" : "") + "\">" + warn + "</strong></div>" +
        "<div><span>重复坐标</span><strong class=\"" + (DATA.duplicates.length ? "warn" : "") + "\">" + DATA.duplicates.length + "</strong></div>" +
        "<div><span>同排前置</span><strong class=\"" + (DATA.sameRow.length ? "warn" : "") + "\">" + DATA.sameRow.length + "</strong></div>" +
        "<div><span>互斥</span><strong>" + mePairs.size + "</strong></div>" +
        "<div><span>坐标范围</span><strong>" + b.minX + "–" + b.maxX + "</strong></div>" +
      "</div>" +
      "<h3>分线</h3><table class=\"band-table\">" + bandRows + "</table>" +
      "<h3>交叉点</h3>" + crossRows +
      "<h3>同排前置</h3>" + sameRows +
      (dupRows ? "<h3>重复坐标</h3>" + dupRows : "") +
      '<h3>操作</h3><div class="empty">粗描边是各线起点；拖动空白处平移，滚轮缩放；点击国策查看前置、后续与互斥；上方搜索可直接定位；勾选「互斥线」可显示全部互斥关系。键盘：方向键平移，+ / − 缩放，0 适应全树。</div>';
  }

  function renderSelected(id) {
    const n = byId.get(id);
    if (!n) { renderOverview(); return; }
    const pre = n.pre.filter(p => byId.has(p));
    const next = (succ.get(id) || []).slice();
    const me = n.me.filter(p => byId.has(p));
    const chips = arr => arr.length ? '<div class="chips">' + arr.map(x => chip(x)).join("") + "</div>" : '<div class="empty">无</div>';
    panel.innerHTML =
      '<h2>' + esc(n.name) + "</h2>" +
      '<div class="mono">' + esc(n.id) + "</div>" +
      '<div style="margin-top:6px"><span class="badge"><i style="background:var(--band-' + n.g.toLowerCase() + ')"></i>' + esc(bandName(n.g)) + "</span> " +
      '<span class="badge">x ' + n.x + " · y " + n.y + "</span>" +
      (n.cost != null ? ' <span class="badge">' + n.cost + " 点 · " + (n.cost * 7) + " 天</span>" : "") +
      (n.root ? ' <span class="badge">起点</span>' : "") + "</div>" +
      "<h3>前置 · " + pre.length + "</h3>" + chips(pre) +
      "<h3>后续 · " + next.length + "</h3>" + chips(next) +
      "<h3>互斥 · " + me.length + "</h3>" + chips(me) +
      '<div class="actions"><button class="tbtn" data-center="' + esc(id) + '">居中显示</button><button class="tbtn" data-clear="1">清除选择</button></div>';
  }

  function flashCrossing(idx) {
    const c = DATA.crossings[idx];
    if (!c) return;
    const ar = svgAspect();
    const w = 16, h = w / ar;
    setView({ x: c.x - w / 2, y: c.y - h / 2, w, h });
    setActiveBand(null);
    activeCrossing = idx;
    const els = [];
    const ids = new Set([c.a[0], c.a[1], c.b[0], c.b[1]]);
    ids.forEach(id => { const g = nodeEls.get(id); if (g) els.push(g); });
    [c.a, c.b].forEach(pair => { const line = edgeEls.get(pair[0] + ">" + pair[1]); if (line) els.push(line); });
    els.forEach(e => e.classList.add("flash"));
    clearTimeout(flashTimer);
    flashTimer = setTimeout(() => { els.forEach(e => e.classList.remove("flash")); activeCrossing = null; }, 2600);
  }

  // Search
  const search = $("#search");
  const results = $("#search-results");
  let searchActive = 0;
  let searchMatches = [];

  function runSearch(q) {
    q = q.trim().toLowerCase();
    if (!q) { hideSearch(); return; }
    searchMatches = DATA.nodes.filter(n =>
      n.name.toLowerCase().includes(q) || n.id.toLowerCase().includes(q)
    ).slice(0, 8);
    if (!searchMatches.length) {
      results.innerHTML = '<div class="search-result empty">无匹配</div>';
      results.hidden = false;
      searchActive = -1;
      return;
    }
    searchActive = 0;
    results.innerHTML = searchMatches.map((n, i) =>
      '<button class="search-result' + (i === 0 ? " active" : "") + '" data-id="' + esc(n.id) + '">' +
      esc(n.name) + '<span class="id">' + esc(n.id) + "</span></button>"
    ).join("");
    results.hidden = false;
  }

  function hideSearch() {
    results.hidden = true;
    searchActive = 0;
  }

  function pickSearch(id) {
    const n = byId.get(id);
    if (!n) return;
    search.value = n.name;
    hideSearch();
    selectNode(id, true);
  }

  function moveSearch(delta) {
    if (results.hidden || !searchMatches.length) return;
    searchActive = (searchActive + delta + searchMatches.length) % searchMatches.length;
    results.querySelectorAll(".search-result").forEach((b, i) => b.classList.toggle("active", i === searchActive));
    const active = results.querySelectorAll(".search-result")[searchActive];
    if (active) active.scrollIntoView({ block: "nearest" });
  }

  // Events
  $("#zoom-in").addEventListener("click", () => zoomBy(1.35));
  $("#zoom-out").addEventListener("click", () => zoomBy(1 / 1.35));
  $("#fit").addEventListener("click", fitAll);
  $("#band-buttons").addEventListener("click", e => {
    const b = e.target.closest("[data-band]");
    if (b) focusBand(b.dataset.band);
  });
  $("#toggle-labels").addEventListener("change", applyView);
  $("#toggle-me").addEventListener("change", e => {
    $("#me-edges").hidden = !e.target.checked;
  });
  $("#toggle-cross").addEventListener("change", e => {
    $("#crossings").hidden = !e.target.checked;
  });
  const themeBox = $("#toggle-theme");
  function setTheme(theme) {
    document.documentElement.dataset.theme = theme;
    themeBox.checked = theme === "dark";
    try { localStorage.setItem("ire-focus-theme", theme); } catch (err) {}
  }
  themeBox.checked = document.documentElement.dataset.theme === "dark";
  themeBox.addEventListener("change", () => setTheme(themeBox.checked ? "dark" : "light"));

  search.addEventListener("input", () => runSearch(search.value));
  search.addEventListener("focus", () => { if (search.value.trim()) runSearch(search.value); });
  search.addEventListener("keydown", e => {
    if (e.isComposing) return;
    if (e.key === "ArrowDown") { e.preventDefault(); moveSearch(1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); moveSearch(-1); }
    else if (e.key === "Enter") {
      if (!results.hidden && searchMatches.length) {
        e.preventDefault();
        pickSearch(searchMatches[Math.max(0, searchActive)].id);
      }
    } else if (e.key === "Escape") { hideSearch(); search.blur(); }
  });
  results.addEventListener("click", e => {
    const b = e.target.closest("[data-id]");
    if (b) pickSearch(b.dataset.id);
  });
  document.addEventListener("pointerdown", e => {
    if (!e.target.closest(".search-wrap")) hideSearch();
  });

  panel.addEventListener("click", e => {
    const go = e.target.closest("[data-goto]");
    if (go) { selectNode(go.dataset.goto, true); return; }
    const band = e.target.closest("[data-band]");
    if (band) { focusBand(band.dataset.band); return; }
    const cross = e.target.closest("[data-cross]");
    if (cross) { flashCrossing(Number(cross.dataset.cross)); return; }
    const center = e.target.closest("[data-center]");
    if (center) { centerOn(center.dataset.center, 32); return; }
    if (e.target.closest("[data-clear]")) clearSelection();
  });

  // Pan / zoom
  viewer.addEventListener("wheel", e => {
    e.preventDefault();
    const p = svgPoint(e.clientX, e.clientY);
    const factor = Math.exp(-e.deltaY * 0.0015);
    zoomAt(factor, p.x, p.y);
  }, { passive: false });

  viewer.addEventListener("pointerdown", e => {
    if (e.button !== 0) return;
    if (e.target.closest(".node")) return;
    drag = { x: e.clientX, y: e.clientY, vx: view.x, vy: view.y };
    moved = false;
    viewer.setPointerCapture(e.pointerId);
  });
  viewer.addEventListener("pointermove", e => {
    if (drag) {
      const dx = e.clientX - drag.x;
      const dy = e.clientY - drag.y;
      if (Math.abs(dx) + Math.abs(dy) > 3) moved = true;
      const scale = view.w / Math.max(1, svg.clientWidth);
      setView({ x: drag.vx - dx * scale, y: drag.vy - dy * scale, w: view.w, h: view.h });
      setActiveBand(null);
      hideTip();
    } else {
      const p = svgPoint(e.clientX, e.clientY);
      cursorEl.textContent = "x " + round1(p.x) + " · y " + round1(p.y);
    }
  });
  viewer.addEventListener("pointerup", e => {
    if (drag) {
      const wasMoved = moved;
      drag = null;
      try { viewer.releasePointerCapture(e.pointerId); } catch (err) {}
      if (!wasMoved) clearSelection();
    }
  });
  viewer.addEventListener("pointercancel", () => { drag = null; });
  viewer.addEventListener("dblclick", e => {
    const p = svgPoint(e.clientX, e.clientY);
    zoomAt(1.6, p.x, p.y);
  });
  viewer.addEventListener("keydown", e => {
    if (e.key === "ArrowLeft") { e.preventDefault(); setView({ x: view.x - view.w * 0.08, y: view.y, w: view.w, h: view.h }); setActiveBand(null); }
    else if (e.key === "ArrowRight") { e.preventDefault(); setView({ x: view.x + view.w * 0.08, y: view.y, w: view.w, h: view.h }); setActiveBand(null); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setView({ x: view.x, y: view.y - view.h * 0.08, w: view.w, h: view.h }); setActiveBand(null); }
    else if (e.key === "ArrowDown") { e.preventDefault(); setView({ x: view.x, y: view.y + view.h * 0.08, w: view.w, h: view.h }); setActiveBand(null); }
    else if (e.key === "+" || e.key === "=") { e.preventDefault(); zoomBy(1.2); }
    else if (e.key === "-" || e.key === "_") { e.preventDefault(); zoomBy(1 / 1.2); }
    else if (e.key === "0") { e.preventDefault(); fitAll(); }
    else if (e.key === "Escape") { clearSelection(); }
  });

  // Init
  buildSvg();
  $("#me-edges").hidden = !$("#toggle-me").checked;
  $("#crossings").hidden = !$("#toggle-cross").checked;
  $("#headline").textContent = DATA.nodes.length + " 个国策 · " + Object.keys(bandMeta).length + " 条线 · " +
    DATA.crossings.length + " 处交叉 · " + DATA.duplicates.length + " 个重复坐标";
  $("#source").textContent = "源 " + DATA.source + " · 生成 " + DATA.generated;
  renderPanel();
  fitAll();
  requestAnimationFrame(() => {
    fitAll();
    updateHighlight();
  });
  new ResizeObserver(() => {
    const cx = view.x + view.w / 2, cy = view.y + view.h / 2;
    const h = view.w / svgAspect();
    setView({ x: cx - view.w / 2, y: cy - h / 2, w: view.w, h });
  }).observe(viewer);
  window.addEventListener("keydown", e => {
    if (e.key === "Escape" && document.activeElement === search) hideSearch();
  });
})();
</script>
</body>
</html>
'''

if __name__ == "__main__":
    main()
