from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from typing import List
import json
from ..services.orchestrator import RUNS_DIR, load_summary
from ..deps.authz import require_auth, ensure_scopes, tenant_allowed, AuthUser

router = APIRouter()

@router.post("/runs/{run_id}/tags")
def add_tag(run_id: str, tag: str, user: AuthUser = Depends(require_auth)):
    ensure_scopes(user, ["runs:rerun"])
    s = load_summary(run_id)
    if not tenant_allowed(user, s.tenant): raise HTTPException(status_code=403, detail="Tenant not allowed")
    s.tags = sorted(set((s.tags or []) + [tag]))  # update model
    (RUNS_DIR / run_id / "summary.json").write_text(s.model_dump_json(indent=2), encoding="utf-8")
    return {"tags": s.tags}

@router.delete("/runs/{run_id}/tags/{tag}")
def del_tag(run_id: str, tag: str, user: AuthUser = Depends(require_auth)):
    ensure_scopes(user, ["runs:rerun"])
    s = load_summary(run_id)
    if not tenant_allowed(user, s.tenant): raise HTTPException(status_code=403, detail="Tenant not allowed")
    s.tags = [t for t in (s.tags or []) if t != tag]
    (RUNS_DIR / run_id / "summary.json").write_text(s.model_dump_json(indent=2), encoding="utf-8")
    return {"tags": s.tags}
