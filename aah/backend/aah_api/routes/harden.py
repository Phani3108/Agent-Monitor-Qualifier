from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from ..services.orchestrator import load_summary
from ..services.remediation import harden_run

router = APIRouter()


@router.post("/runs/{run_id}/harden")
def harden(run_id: str, create_pr: bool = Query(default=False)):
    try:
        load_summary(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")
    try:
        result = harden_run(run_id, create_pr=create_pr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Harden failed: {e}")
    return result
