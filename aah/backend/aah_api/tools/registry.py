from __future__ import annotations
from typing import Any, Dict, Tuple
from .schemas import SCHEMAS

def list_tools() -> Dict[str, Any]:
    return {k: {"schema": v} for k, v in SCHEMAS.items()}

def run_tool_locally(name: str, args: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Local no-op/echo runner. Replace with real integrations later."""
    if name not in SCHEMAS:
        return False, {"error": "unknown tool"}
    return True, {"ticket_id": "TCK-" + (args.get("customer_id","XXX")[-5:]), "status": "created"}
