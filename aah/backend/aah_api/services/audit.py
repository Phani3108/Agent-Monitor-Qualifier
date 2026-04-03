from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
AUD_DIR = REPO_ROOT / "audits"
AUD_DIR.mkdir(parents=True, exist_ok=True)

def _file() -> Path:
    d = datetime.now(timezone.utc).strftime("%Y-%m")
    return AUD_DIR / f"audit-{d}.jsonl"

def record(actor: str, action: str, ok: bool, tenant: Optional[str], target: Dict[str, Any] | None = None, details: Dict[str, Any] | None = None) -> None:
    evt = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "actor": actor, "action": action, "ok": ok, "tenant": tenant or "default",
        "target": target or {}, "details": details or {}
    }
    _file().open("a", encoding="utf-8").write(json.dumps(evt, ensure_ascii=False) + "\n")
