def list_tenants() -> list[str]:
    names = ["default"]
    for p in TENANTS_DIR.glob("*.y*ml"):
        if p.stem != "default":
            names.append(p.stem)
    return sorted(set(names))
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TENANTS_DIR = REPO_ROOT / "tenants"
TENANTS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_TENANT = {
    "name": "default",
    "languages": ["en"],
    "pii": {"mask_pan": True, "mask_ssn": True, "mask_dob": True},
    "tools": {"allowlist": ["create_support_case"]},
    "budgets": {"max_latency_ms": 1800, "max_cost_usd": 0.02},
    "compliance": {
        "pci": {"no_pan_in_outputs": True, "no_full_pan_in_logs": True, "last4_only": True}
    }
}

def load_tenant(name: str | None) -> Dict[str, Any]:
    # Fallback to default if file not found
    if not name:
        return DEFAULT_TENANT
    p = TENANTS_DIR / f"{name}.yaml"
    if not p.exists():
        return DEFAULT_TENANT
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    # Minimal merge (defaults first, then overlay)
    out = DEFAULT_TENANT | data
    # Deep-ish merge of nested dicts we care about
    for k in ("pii","tools","budgets","compliance"):
        if k in data and isinstance(data[k], dict):
            out[k] = (DEFAULT_TENANT.get(k) or {}) | data[k]
    return out
