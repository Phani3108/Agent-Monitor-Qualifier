from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
INC_DIR = REPO_ROOT / "incidents"
INC_DIR.mkdir(parents=True, exist_ok=True)
INC_FILE = INC_DIR / "incidents.json"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _load_all() -> List[Dict[str, Any]]:
    if not INC_FILE.exists():
        return []
    return json.loads(INC_FILE.read_text(encoding="utf-8"))

def _save_all(items: List[Dict[str, Any]]) -> None:
    INC_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")

def create_incident(kind: str, severity: str, title: str, details: Dict[str, Any]) -> Dict[str, Any]:
    items = _load_all()
    inc = {
        "id": str(uuid.uuid4()),
        "created_at": _now(),
        "resolved_at": None,
        "kind": kind,            # e.g., "safety_violation", "not_certified", "regression"
        "severity": severity,    # e.g., "low","medium","high","critical"
        "title": title,
        "details": details
    }
    items.insert(0, inc)
    _save_all(items)
    return inc

def list_incidents() -> List[Dict[str, Any]]:
    return _load_all()

def resolve_incident(inc_id: str) -> Dict[str, Any]:
    items = _load_all()
    for it in items:
        if it["id"] == inc_id:
            it["resolved_at"] = _now()
            _save_all(items)
            return it
    raise FileNotFoundError("incident not found")
