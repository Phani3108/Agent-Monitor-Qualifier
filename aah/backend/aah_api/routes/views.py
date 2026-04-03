from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path
from ..deps.authz import require_auth, AuthUser, ensure_scopes

REPO_ROOT = Path(__file__).resolve().parents[2]
VIEWS = REPO_ROOT / "config" / "saved_views.json"
VIEWS.parent.mkdir(parents=True, exist_ok=True)
if not VIEWS.exists(): VIEWS.write_text(json.dumps({"views":[]}, indent=2), encoding="utf-8")

class SavedView(BaseModel):
    id: str
    name: str
    query: dict   # { agent?, env?, tenant?, tags?, certified?, score_min?, score_max? }

router = APIRouter()

@router.get("/views")
def views_list(user: AuthUser = Depends(require_auth)):
    ensure_scopes(user, ["runs:read"])
    return json.loads(VIEWS.read_text(encoding="utf-8"))

@router.post("/views")
def views_save(view: SavedView, user: AuthUser = Depends(require_auth)):
    ensure_scopes(user, ["runs:read"])
    data = json.loads(VIEWS.read_text(encoding="utf-8"))
    data["views"] = [v for v in data.get("views", []) if v.get("id") != view.id] + [view.model_dump()]
    VIEWS.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"ok": True}

@router.delete("/views/{vid}")
def views_delete(vid: str, user: AuthUser = Depends(require_auth)):
    ensure_scopes(user, ["runs:read"])
    data = json.loads(VIEWS.read_text(encoding="utf-8"))
    data["views"] = [v for v in data.get("views", []) if v.get("id") != vid]
    VIEWS.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"ok": True}
