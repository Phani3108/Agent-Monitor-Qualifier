from __future__ import annotations
from fastapi import APIRouter, HTTPException
from ..services.incidents import list_incidents, resolve_incident

router = APIRouter()

@router.get("/incidents")
def get_incidents():
    return list_incidents()

@router.post("/incidents/{inc_id}/resolve")
def resolve(inc_id: str):
    try:
        return resolve_incident(inc_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Incident not found")
