from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

ASSETS = Path(__file__).resolve().parents[1] / "assets"

def render_badge_svg(out_path: Path, certified: bool, version: str, score: int) -> None:
    env = Environment(loader=FileSystemLoader(str(ASSETS)), autoescape=select_autoescape())
    tpl = env.get_template("badge.svg.j2")
    status_text = f"CERTIFIED {version}" if certified else "NOT CERTIFIED"
    color = "#2e7d32" if certified else "#6c757d"
    svg = tpl.render(status_text=status_text, color=color, score=score)
    out_path.write_text(svg, encoding="utf-8")
