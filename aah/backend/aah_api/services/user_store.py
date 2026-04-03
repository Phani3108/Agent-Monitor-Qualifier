from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
USERS_FILE = REPO_ROOT / "config" / "users.yaml"

def load_users() -> Dict[str, Dict[str, Any]]:
    if not USERS_FILE.exists(): return {}
    data = yaml.safe_load(USERS_FILE.read_text(encoding="utf-8")) or {}
    out: Dict[str, Dict[str, Any]] = {}
    for u in (data.get("users") or []):
        out[str(u["username"])] = u
    return out
