from __future__ import annotations
from fastapi import APIRouter, HTTPException, Response
from ..services.orchestrator import load_summary
from pathlib import Path

router = APIRouter()

@router.get("/runs/{run_id}/badge.svg")
def get_badge(run_id: str):
    summary = load_summary(run_id)
    path = Path(summary.artifacts.get("badge_svg",""))
    if not path.exists():
        raise HTTPException(status_code=404, detail="Badge not found")
    return Response(content=path.read_text(encoding="utf-8"), media_type="image/svg+xml")

@router.get("/runs/{run_id}/cert")
def get_cert(run_id: str):
    summary = load_summary(run_id)
    return {
        "run_id": summary.run_id,
        "certified": summary.certified,
        "version": summary.cert.version if summary.cert else None,
        "reasons": summary.cert.reasons if summary.cert else [],
        "thresholds": summary.cert.thresholds if summary.cert else {},
        "scores": summary.scores
    }
