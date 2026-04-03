from __future__ import annotations
from fastapi import APIRouter, HTTPException
from ..services.orchestrator import load_summary
from ..services.broadcast import broadcast_to_teams

router = APIRouter()

@router.post("/runs/{run_id}/broadcast")
def broadcast(run_id: str):
    try:
        summary = load_summary(run_id).model_dump()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")
    result = broadcast_to_teams(summary)
    return result
