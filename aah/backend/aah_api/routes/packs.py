from __future__ import annotations
from fastapi import APIRouter, HTTPException
from ..services.packs import list_packs, load_pack

router = APIRouter()

@router.get("/spec-packs")
def packs_list():
    return list_packs()

@router.get("/spec-packs/{name}")
def pack_detail(name: str):
    try:
        return load_pack(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Pack not found")
