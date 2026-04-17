from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from ..models.maturity import AssessmentRequest
from ..services.maturity import assess, get_questions, load_assessment
from ..services.maturity_report import render_maturity_report

router = APIRouter(tags=["maturity"])


@router.get("/maturity/questions")
def maturity_questions():
    return get_questions().model_dump()


@router.post("/maturity/assess")
def maturity_assess(req: AssessmentRequest):
    result = assess(req)
    return result.model_dump()


@router.get("/maturity/{assessment_id}")
def maturity_get(assessment_id: str):
    try:
        result = load_assessment(assessment_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return result.model_dump()


@router.get("/maturity/{assessment_id}/roadmap")
def maturity_roadmap(assessment_id: str):
    try:
        result = load_assessment(assessment_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {
        "id": result.id,
        "overall_level": result.overall_level,
        "overall_level_name": result.overall_level_name,
        "roadmap_90d": [item.model_dump() for item in result.roadmap_90d],
    }


@router.get("/maturity/{assessment_id}/report", response_class=HTMLResponse)
def maturity_report(assessment_id: str):
    try:
        result = load_assessment(assessment_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Assessment not found")
    html = render_maturity_report(result)
    return HTMLResponse(content=html)
