from __future__ import annotations
import json
from fastapi import APIRouter, HTTPException
from pathlib import Path
from ..services.orchestrator import RUNS_DIR

router = APIRouter()

@router.get("/runs/{run_id}/evidence/grounding")
def grounding_evidence(run_id: str):
    p = RUNS_DIR / run_id / "results.grounding.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="No grounding results")
    data = json.loads(p.read_text(encoding="utf-8"))
    items = []
    for r in data:
        ev = (r.get("meta") or {}).get("evidence") or []
        for i, h in enumerate(ev):
            items.append({"test_id": r.get("id"), "rank": i+1, **h})
    return items
