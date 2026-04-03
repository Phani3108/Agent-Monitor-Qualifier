from __future__ import annotations
from fastapi import APIRouter
from ..services.tenant import list_tenants

router = APIRouter()

@router.get("/tenants")
def tenants_list():
    return list_tenants()
