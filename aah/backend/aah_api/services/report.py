from __future__ import annotations
from pathlib import Path
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader, select_autoescape
from ..models.dto import TestResult

ASSETS = Path(__file__).resolve().parents[1] / "assets"
TEMPLATE = ASSETS / "report.html.j2"

def render_report(out_path: Path, summary: Dict[str, object], results: Dict[str, List[TestResult]]) -> None:
    env = Environment(loader=FileSystemLoader(str(ASSETS)), autoescape=select_autoescape())
    tpl = env.get_template("report.html.j2")
    html = tpl.render(summary=summary, results=results)
    out_path.write_text(html, encoding="utf-8")
