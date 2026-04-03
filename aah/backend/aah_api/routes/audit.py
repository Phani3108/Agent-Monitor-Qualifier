from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends, Query
from pathlib import Path
from typing import Optional, List
import json
from ..deps.authz import require_auth, ensure_scopes, AuthUser

router = APIRouter()

@router.get("/audits")
def list_audits(month: Optional[str] = Query(None, description="YYYY-MM"), user: AuthUser = Depends(require_auth)):
    ensure_scopes(user, ["users:read"])
    from ..services.audit import AUD_DIR
    items: List[dict] = []
    files = [AUD_DIR / f for f in ( [f"audit-{month}.jsonl"] if month else sorted(p.name for p in AUD_DIR.glob("audit-*.jsonl")) )]
    for p in files:
        if not p.exists(): continue
        for line in p.read_text(encoding="utf-8").splitlines():
            try: items.append(json.loads(line))
            except Exception: pass
    return items[-1000:]  # cap
