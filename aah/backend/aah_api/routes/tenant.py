from __future__ import annotations
from fastapi import APIRouter
from ..services.tenant import load_tenant

router = APIRouter()

@router.get("/tenant/{name}")
def get_tenant(name: str):
    return load_tenant(name if name != "default" else None)
