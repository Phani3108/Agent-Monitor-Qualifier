from __future__ import annotations
from fastapi import APIRouter, HTTPException, Response
from ..services.orchestrator import load_summary

router = APIRouter()

@router.get("/runs/{run_id}/badge-embed")
def badge_embed(run_id: str):
    try:
        s = load_summary(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")
    html = f'<a href="/runs/{s.run_id}/report" target="_blank" rel="noreferrer"><img alt="AAH badge" src="/runs/{s.run_id}/badge.svg"/></a>'
    return Response(content=html, media_type="text/html")
