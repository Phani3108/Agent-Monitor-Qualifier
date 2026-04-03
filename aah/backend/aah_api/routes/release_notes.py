from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from ..services.release_notes import generate_release_notes, save_release_notes
from ..services.orchestrator import load_summary

router = APIRouter()

@router.get("/runs/{head}/release-notes", response_class=PlainTextResponse)
def notes(head: str, base: str = Query(...)):
    try:
        load_summary(head)
        load_summary(base)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")
    md = generate_release_notes(base, head)
    save_release_notes(head, md)
    return md
