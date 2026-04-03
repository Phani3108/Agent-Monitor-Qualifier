from __future__ import annotations
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from ..services.orchestrator import RUNS_DIR, load_summary

router = APIRouter()

@router.get("/runs/{run_id}/determinism/stats")
def det_stats(run_id: str, test_id: Optional[str] = Query(None)):
    try:
        load_summary(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")
    p = RUNS_DIR / run_id / "results.determinism.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    if test_id:
        data = [d for d in data if d.get("id") == test_id or d.get("id","").endswith(test_id)]
    # return compact view
    out = []
    for d in data:
        out.append({
            "id": d.get("id"),
            "passed": d.get("passed"),
            "latency_ms": (d.get("meta") or {}).get("latency_ms"),
            "cost_usd": (d.get("meta") or {}).get("cost_usd"),
            "determinism_pct": (d.get("meta") or {}).get("determinism_pct"),
            "pass_rate_pct": (d.get("meta") or {}).get("pass_rate_pct"),
            "samples": (d.get("meta") or {}).get("samples"),
            "concurrency": (d.get("meta") or {}).get("concurrency"),
        })
    return out
