from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from ..services.orchestrator import RUNS_DIR, load_summary
from ..services.sign import verify_manifest

router = APIRouter()

@router.get("/runs/{run_id}/verify")
def verify(run_id: str, require_hmac: bool = Query(False)):
    try:
        load_summary(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")
    return verify_manifest(RUNS_DIR / run_id, require_hmac=require_hmac)
