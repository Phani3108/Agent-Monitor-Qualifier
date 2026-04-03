from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from ..services.auth import users_db, verify_password, create_jwt, scopes_for_role, auth_disabled
from ..services.roles import ROLE_SCOPES
from ..deps.authz import require_auth, ensure_scopes, AuthUser
from ..services.token_store import issue_token, list_tokens, revoke_token

router = APIRouter()

class LoginBody(BaseModel):
    username: str
    password: str

@router.post("/auth/login")
def login(body: LoginBody):
    if auth_disabled():
        raise HTTPException(status_code=400, detail="Auth is disabled (AAH_AUTH_DISABLED=1). Unset it to enable login.")
    users = users_db()
    u = users.get(body.username)
    if not u or not verify_password(body.password, u.get("password_hash","")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    scopes = scopes_for_role(u.get("role","viewer"))
    token = create_jwt(u["username"], u.get("role","viewer"), u.get("tenants") or ["*"], scopes)
    return {"access_token": token, "token_type": "bearer", "user": {"username": u["username"], "role": u.get("role"), "tenants": u.get("tenants")}}

@router.get("/auth/me")
def me(user: AuthUser = Depends(require_auth)):
    return {"username": user.username, "role": user.role, "tenants": user.tenants, "scopes": list(user.scopes)}

class IssueTokenBody(BaseModel):
    username: str
    scopes: List[str]
    tenants: List[str]

@router.post("/auth/tokens")
def tokens_issue(body: IssueTokenBody, user: AuthUser = Depends(require_auth)):
    ensure_scopes(user, ["tokens:issue"])
    # owner can issue for anyone; non-owner can only issue for self
    if user.role != "owner" and body.username != user.username:
        raise HTTPException(status_code=403, detail="Can only issue tokens for yourself.")
    # validate scopes exist
    for s in body.scopes:
        if s not in ROLE_SCOPES["owner"]:
            raise HTTPException(status_code=400, detail=f"Unknown scope {s}")
    return issue_token(body.username, body.scopes, body.tenants)

@router.get("/auth/tokens")
def tokens_list(user: AuthUser = Depends(require_auth)):
    ensure_scopes(user, ["tokens:issue"])
    return list_tokens(None if user.role=="owner" else user.username)

@router.delete("/auth/tokens/{token_id}")
def tokens_revoke(token_id: str, user: AuthUser = Depends(require_auth)):
    ensure_scopes(user, ["tokens:issue"])
    ok = revoke_token(token_id)
    if not ok: raise HTTPException(status_code=404, detail="Token not found")
    return {"ok": True}
