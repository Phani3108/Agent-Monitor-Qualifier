from __future__ import annotations
from datetime import datetime, timedelta, timezone
import os, json, jwt
from pathlib import Path
from typing import Any, Dict, List, Optional
from passlib.hash import bcrypt
from .user_store import load_users
from .roles import ROLE_SCOPES

REPO_ROOT = Path(__file__).resolve().parents[2]
DEV_KEY = REPO_ROOT / ".aah" / "dev_jwt.key"
DEV_KEY.parent.mkdir(parents=True, exist_ok=True)

def _secret() -> str:
    if os.getenv("AAH_JWT_SECRET"): return os.getenv("AAH_JWT_SECRET")  # type: ignore
    if DEV_KEY.exists(): return DEV_KEY.read_text(encoding="utf-8")
    import secrets
    s = secrets.token_hex(32); DEV_KEY.write_text(s, encoding="utf-8"); return s

def create_jwt(username: str, role: str, tenants: List[str], scopes: List[str], hours=8) -> str:
    payload = {
        "sub": username, "role": role, "tenants": tenants, "scopes": scopes,
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=hours)).timestamp())
    }
    return jwt.encode(payload, _secret(), algorithm="HS256")

def verify_password(pw: str, hash_: str) -> bool:
    try: return bcrypt.verify(pw, hash_)
    except Exception: return False

def decode_jwt(token: str) -> Dict[str, Any]:
    return jwt.decode(token, _secret(), algorithms=["HS256"])

def auth_disabled() -> bool:
    return os.getenv("AAH_AUTH_DISABLED", "1") == "1"

def scopes_for_role(role: str) -> List[str]:
    return ROLE_SCOPES.get(role, [])

def users_db(): return load_users()
