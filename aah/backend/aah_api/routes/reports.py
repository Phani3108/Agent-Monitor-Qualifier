from __future__ import annotations
from fastapi import APIRouter, HTTPException, Response
from ..services.orchestrator import RUNS_DIR

router = APIRouter()

@router.get("/runs/{run_id}/report")
def get_report(run_id: str):
    report_path = RUNS_DIR / run_id / "report.html"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    html = report_path.read_text(encoding="utf-8")
    return Response(content=html, media_type="text/html")
