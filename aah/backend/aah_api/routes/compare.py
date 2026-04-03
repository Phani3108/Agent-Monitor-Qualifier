from __future__ import annotations
from fastapi import APIRouter, HTTPException, Response, Query
from ..services.compare import compare_runs
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

router = APIRouter()

@router.get("/compare")
def compare_json(base: str = Query(...), head: str = Query(...)):
    try:
        return compare_runs(base, head)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/compare/html")
def compare_html(base: str, head: str):
    try:
        data = compare_runs(base, head)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    assets = Path(__file__).resolve().parents[1] / "assets"
    env = Environment(loader=FileSystemLoader(str(assets)), autoescape=select_autoescape())
    tpl = env.get_template("compare.html.j2")
    html = tpl.render(**data)
    return Response(content=html, media_type="text/html")
