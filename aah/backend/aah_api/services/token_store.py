from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
import json, os, secrets, hashlib
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
TOK_FILE = REPO_ROOT / "config" / "tokens.json"
TOK_FILE.parent.mkdir(parents=True, exist_ok=True)

def _load() -> Dict[str, Any]:
    if not TOK_FILE.exists(): return {"tokens": []}
    return json.loads(TOK_FILE.read_text(encoding="utf-8"))

def _save(d: Dict[str, Any]) -> None:
    TOK_FILE.write_text(json.dumps(d, indent=2), encoding="utf-8")

def issue_token(username: str, scopes: List[str], tenants: List[str]) -> Dict[str, Any]:
    raw = secrets.token_hex(24)
    sha = hashlib.sha256(raw.encode()).hexdigest()
    d = _load()
    entry = {
        "id": secrets.token_hex(8),
        "user": username,
        "sha256": sha,
        "scopes": scopes,
        "tenants": tenants,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "revoked": False
    }
    d["tokens"].append(entry); _save(d)
    return {"token": raw, "meta": entry}

def list_tokens(username: Optional[str]=None) -> List[Dict[str, Any]]:
    d = _load()
    items = d.get("tokens") or []
    if username: items = [t for t in items if t["user"] == username]
    return items

def revoke_token(token_id: str) -> bool:
    d = _load()
    ok = False
    for t in d.get("tokens") or []:
        if t["id"] == token_id:
            t["revoked"] = True; ok = True
    _save(d); return ok

def resolve_token(raw: str) -> Optional[Dict[str, Any]]:
    sha = hashlib.sha256(raw.encode()).hexdigest()
    d = _load()
    for t in d.get("tokens") or []:
        if (t["sha256"] == sha) and (not t.get("revoked")):
            return t
    return None
