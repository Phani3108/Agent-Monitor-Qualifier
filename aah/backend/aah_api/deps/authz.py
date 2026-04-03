from __future__ import annotations
from fastapi import Depends, HTTPException, Header
from typing import List, Optional, Dict, Any
from ..services.auth import auth_disabled, decode_jwt, users_db, scopes_for_role
from ..services.token_store import resolve_token

class AuthUser(dict):
    @property
    def username(self): return self.get("sub")
    @property
    def role(self): return self.get("role")
    @property
    def tenants(self): return self.get("tenants") or ["*"]
    @property
    def scopes(self): return set(self.get("scopes") or [])

def _unauth():
    raise HTTPException(status_code=401, detail="Unauthorized")

def _forbidden():
    raise HTTPException(status_code=403, detail="Forbidden")

async def require_auth(authorization: Optional[str] = Header(None), x_api_key: Optional[str] = Header(None)) -> AuthUser:
    if auth_disabled():
        return AuthUser({"sub":"dev","role":"owner","tenants":["*"],"scopes":scopes_for_role("owner")})
    if x_api_key:
        t = resolve_token(x_api_key)
        if not t: _unauth()
        return AuthUser({"sub": t["user"], "role": "token", "tenants": t["tenants"], "scopes": t["scopes"]})
    if not authorization or not authorization.lower().startswith("bearer "):
        _unauth()
    token = authorization.split(" ",1)[1].strip()
    try:
        payload = decode_jwt(token)
        return AuthUser(payload)
    except Exception:
        _unauth()

def ensure_scopes(user: AuthUser, needed: List[str]) -> None:
    if auth_disabled(): return
    if not set(needed).issubset(user.scopes): _forbidden()

def tenant_allowed(user: AuthUser, tenant: Optional[str]) -> bool:
    ts = user.tenants
    return ("*" in ts) or (tenant in ts if tenant else ("default" in ts))
