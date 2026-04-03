#!/usr/bin/env python3
"""
Builds docs/AAH_Master_Walkthrough.html by reading real repo contents.
No external network calls. Works even if some files are missing (notes will be shown).

Usage:
  python tools/docs/build_master_walkthrough.py
Options:
  --root <path>          : repo root (defaults to script->../../)
  --out  <file.html>     : output file (defaults to docs/AAH_Master_Walkthrough.html)
"""
from __future__ import annotations
import argparse, json, os, re, sys, textwrap, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

def guess_repo_root(script_path: Path) -> Path:
    return script_path.resolve().parents[2]

HERE = Path(__file__).resolve()
DEFAULT_ROOT = guess_repo_root(HERE)

def read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None

def md_to_html(md: str) -> str:
    try:
        import markdown
        return markdown.markdown(md, extensions=["fenced_code", "tables", "toc"])
    except Exception:
        safe = (md or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<pre>{safe}</pre>"

def json_pretty(s: str) -> str:
    try:
        obj = json.loads(s)
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return s

def code_block(s: str, lang: str = "") -> str:
    safe = (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<pre class="code {lang}">{safe}</pre>'

def section(title: str, body_html: str, anchor: Optional[str] = None) -> str:
    aid = anchor or re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f'<section id="{aid}"><h2>{title}</h2>{body_html}</section>'

def list_items(items: List[str]) -> str:
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

def short(s: str, n: int = 12) -> str:
    return (s[:n] + "…") if len(s) > n else s

def load_backend_stats(repo: Path) -> Dict[str, Any]:
    sys.path.insert(0, str(repo / "aah" / "backend"))
    out: Dict[str, Any] = {"policy_hash": None, "spec_schema_hash": None, "openapi": None}
    try:
        from aah_api.services.policy import load_policy_hash, load_schema_hash  # type: ignore
        out["policy_hash"] = load_policy_hash()
        out["spec_schema_hash"] = load_schema_hash()
    except Exception:
        pass
    try:
        from aah_api.main import app  # type: ignore
        from fastapi.openapi.utils import get_openapi  # type: ignore
        out["openapi"] = get_openapi(title=getattr(app, "title", "AAH API"),
                                     version=getattr(app, "version", "0"),
                                     routes=getattr(app, "routes", []))
    except Exception:
        pass
    return out

def file_tree(repo: Path, roots: List[str]) -> str:
    ex_dirs = {".git", ".venv", "node_modules", ".next", "__pycache__", "runs", "incidents", "baselines", ".aah"}
    ex_files = {".DS_Store"}
    lines: List[str] = []
    for root in roots:
        base = repo / root
        if not base.exists():
            lines.append(f"{root}/  (missing)")
            continue
        lines.append(f"{root}/")
        for p in sorted(base.rglob("*")):
            rel = p.relative_to(repo)
            parts = rel.parts
            if any(part in ex_dirs for part in parts):
                continue
            if p.name in ex_files:
                continue
            depth = len(parts) - 1
            prefix = "  " * depth + ("└─ " if depth else "")
            lines.append(prefix + p.name + ("/" if p.is_dir() else ""))
    return "<pre class='tree'>" + "\n".join(lines) + "</pre>"

def read_yaml_files(dirpath: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for p in sorted(dirpath.glob("*.y*ml")):
        try:
            import yaml  # type: ignore
        except Exception:
            break
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            data["__file"] = str(p.relative_to(DEFAULT_ROOT))
            out.append(data)
        except Exception:
            out.append({"__file": str(p.relative_to(DEFAULT_ROOT)), "__error": "YAML parse error"})
    return out

def render_packs_table(packs: List[Dict[str, Any]]) -> str:
    if not packs:
        return "<p><em>No packs found.</em></p>"
    rows = []
    for d in packs:
        name = d.get("name") or Path(d["__file"]).stem
        ver = d.get("version", "unversioned")
        tests = len(d.get("tests") or [])
        langs = set()
        for t in (d.get("tests") or []):
            pr = (t or {}).get("prompt")
            if isinstance(pr, dict):
                langs |= set(pr.keys())
        rows.append(f"<tr><td><code>{name}</code></td><td>{ver}</td><td>{tests}</td><td>{', '.join(sorted(langs)) or 'en'}</td><td><code>{d['__file']}</code></td></tr>")
    return (
        "<table class='table'><thead><tr>"
        "<th>Pack</th><th>Version</th><th>Tests</th><th>Langs</th><th>File</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )

def render_tenants_table(items: List[Dict[str, Any]]) -> str:
    if not items:
        return "<p><em>No tenants found.</em></p>"
    rows = []
    for d in items:
        name = d.get("name", Path(d["__file"]).stem)
        langs = ", ".join(d.get("languages") or []) or "en"
        budgets = d.get("budgets") or {}
        budgets_s = ", ".join([f"{k}={v}" for k, v in budgets.items()]) or "—"
        rows.append(f"<tr><td>{name}</td><td>{langs}</td><td>{budgets_s}</td><td><code>{d['__file']}</code></td></tr>")
    return (
        "<table class='table'><thead><tr>"
        "<th>Tenant</th><th>Languages</th><th>Budgets</th><th>File</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )

def render_openapi_table(openapi: Dict[str, Any]) -> str:
    if not openapi:
        return "<p><em>OpenAPI not available (backend not importable). Start backend and re-run script to populate.</em></p>"
    rows = []
    paths = openapi.get("paths", {})
    for path, ops in sorted(paths.items()):
        methods = ", ".join(sorted(m.upper() for m in ops.keys()))
        rows.append(f"<tr><td><code>{path}</code></td><td>{methods}</td></tr>")
    return "<table class='table'><thead><tr><th>Path</th><th>Methods</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"

def render_workflows(repo: Path) -> str:
    wf_dir = repo / ".github" / "workflows"
    if not wf_dir.exists():
        return "<p><em>No workflows found.</em></p>"
    rows = []
    for p in sorted(wf_dir.glob("*.y*ml")):
        y = read_text(p) or ""
        job_names = re.findall(r"(?m)^\s{2,}([a-zA-Z0-9_-]+):\s*\n\s*runs-on:", y)
        rows.append(f"<tr><td><code>{p.name}</code></td><td>{', '.join(job_names) or '—'}</td></tr>")
    return "<table class='table'><thead><tr><th>Workflow</th><th>Jobs</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"

def build_html(repo: Path, out_file: Path) -> None:
    ts = now_iso()
    mf = read_text(repo / "Master_file.md")
    tp = read_text(repo / "Truth_policy.md")
    schema = read_text(repo / "specs" / "schemas" / "test_spec.schema.json")
    connectors_yml = read_text(repo / "connectors.yml") or "(connectors.yml missing)"
    packs = read_yaml_files(repo / "specs" / "packs")
    tenants = read_yaml_files(repo / "tenants")
    stats = load_backend_stats(repo)
    quick = []
    quick.append(f"Generated: <strong>{ts}</strong>")
    if stats.get("policy_hash"): quick.append(f"Truth policy hash: <code>{stats['policy_hash']}</code>")
    if stats.get("spec_schema_hash"): quick.append(f"Spec schema hash: <code>{stats['spec_schema_hash']}</code>")
    quick.append(f"Packs: <strong>{len(packs)}</strong>")
    quick.append(f"Tenants: <strong>{len(tenants)}</strong>")
    if stats.get("openapi"): quick.append(f"API paths: <strong>{len(stats['openapi'].get('paths', {}))}</strong>")
    parts: List[str] = []
    parts.append(f"<header><h1>AAH — Master Walkthrough</h1><p>{' • '.join(quick)}</p></header>")
    parts.append(section("Immutable Truth Docs",
                         f"<h3>Master_file.md</h3>{md_to_html(mf or '*Missing*')}"
                         f"<h3>Truth_policy.md</h3>{md_to_html(tp or '*Missing*')}"))
    parts.append(section("Getting Started (Local, no Docker)", md_to_html(textwrap.dedent("""
    ### Backend
    ```bash
    python -m venv .venv && source .venv/bin/activate
    pip install -e aah/backend
    uvicorn aah_api.main:app --host 0.0.0.0 --port 8080 --reload --app-dir aah/backend
    ```
    ### Frontend
    ```bash
    cd frontend
    npm install
    npm run dev
    # open http://localhost:3000
    ```
    """))))
    parts.append(section("Repository Tree (selected roots)", file_tree(repo, [
        "aah/backend/aah_api", "specs", "tenants", "connectors", "frontend", ".github/workflows"
    ])))
    parts.append(section("Spec Schema (test_spec.schema.json)",
                         code_block(json_pretty(schema or "{}"), "json")))
    parts.append(section("Spec Packs Library", render_packs_table(packs)))
    parts.append(section("Tenants", render_tenants_table(tenants)))
    parts.append(section("Connectors Allow-list (connectors.yml)",
                         code_block(connectors_yml, "yaml")))
    parts.append(section("API (FastAPI OpenAPI schema)", render_openapi_table(stats.get("openapi") or {})))
    parts.append(section("CI Workflows", render_workflows(repo)))
    parts.append(section("Artifacts & Endpoints",
                         md_to_html(textwrap.dedent("""
    - **HTML Trust Report**: `/runs/{run_id}/report`
    - **JSON Trust Report v1**: `/runs/{run_id}/trust-report`
    - **Badge (SVG)**: `/runs/{run_id}/badge.svg` (or `?signed=1` for signed-state overlay)
    - **Manifest**: `/runs/{run_id}/manifest` • **Sign**: `POST /runs/{run_id}/sign`
    - **Verify**: `/runs/{run_id}/verify` (use `?require_hmac=1` to enforce HMAC)
    - **Compare**: `/compare?base=<id>&head=<id>` • HTML: `/compare/html?...`
    - **Baseline**: `POST /baselines` ; `GET /baselines/{agent}/{environment}?tenant=...`
    - **Incidents**: `GET /incidents` ; resolve: `POST /incidents/{id}/resolve`
    - **Packs/Tenants index**: `/spec-packs` ; `/tenants`
    """))))
    parts.append(section("Typical Workflow",
                         md_to_html(textwrap.dedent("""
    1. Create run via UI (**+ New Run**) or `POST /runs`.
    2. Inspect failures (rich tool diffs with key/type hints + proposed fixes).
    3. Click **Harden** → proposed edits/tests.
    4. Re-run → **Certified** flips when thresholds met.
    5. **Sign** artifacts → **Verify**.
    6. **Set as baseline** → CI blocks regressions and uncertified runs.
    7. **Share** HTML/JSON report and **Badge** with stakeholders.
    """))))
    css = """
    :root { --fg:#111; --muted:#555; --border:#e6e6e9; --card:#fafafa; --link:#0b62d6; }
    *{box-sizing:border-box} body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--fg);}
    header{padding:24px 24px 0}
    h1{margin:0 0 6px 0}
    h2{border-bottom:1px solid var(--border);padding-bottom:6px;margin-top:28px}
    section{padding:12px 24px}
    pre.code{background:#f6f8fa;border:1px solid var(--border);border-radius:10px;padding:12px;overflow:auto}
    pre.tree{background:#fff;border:1px dashed var(--border);border-radius:10px;padding:12px;overflow:auto}
    .table{width:100%;border-collapse:collapse}
    .table th,.table td{border:1px solid var(--border);padding:8px;text-align:left;background:#fff}
    .table th{background:#f3f3f6}
    code{background:#f6f8fa;padding:2px 6px;border-radius:6px}
    a{color:var(--link);text-decoration:none}
    .muted{color:var(--muted)}
    footer{padding:24px;border-top:1px solid var(--border);color:var(--muted);font-size:12px}
    """
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"/>
<title>AAH — Master Walkthrough</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>{css}</style>
</head>
<body>
{''.join(parts)}
<footer>Generated {ts}. This document is derived from the working tree at build time.</footer>
</body></html>"""
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(html, encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, default=str(DEFAULT_ROOT))
    ap.add_argument("--out", type=str, default="docs/AAH_Master_Walkthrough.html")
    args = ap.parse_args()
    repo = Path(args.root).resolve()
    out = Path(args.out).resolve()
    build_html(repo, out)
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()
