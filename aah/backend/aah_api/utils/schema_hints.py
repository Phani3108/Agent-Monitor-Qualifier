from __future__ import annotations
from typing import Any, Dict, List, Tuple

def _ptype(p: Dict[str, Any]) -> str:
    t = p.get("type")
    if isinstance(t, list): t = "/".join(t)
    return str(t or "any")

def property_hints(schema: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Return expected type/enum/example per property."""
    props = schema.get("properties") or {}
    out: Dict[str, Dict[str, Any]] = {}
    for k, v in props.items():
        hint = {"type": _ptype(v)}
        if "enum" in v: hint["enum"] = list(v["enum"])
        if "minimum" in v: hint["minimum"] = v["minimum"]
        if "maximum" in v: hint["maximum"] = v["maximum"]
        out[k] = hint
    return out

# light domain heuristics; extend as needed
_REASON_NORMALIZE = {"duplicate": "duplicate_debit", "dup": "duplicate_debit"}
def _normalize_reason(x: str) -> str: return _REASON_NORMALIZE.get(x.lower().strip(), x)

def suggest_arg_fixes(args: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Return (proposed_args, suggestions). Non-destructive casts/normalizations."""
    props = schema.get("properties") or {}
    proposed = dict(args)
    notes: List[str] = []

    for key, spec in props.items():
        if key not in proposed: continue
        val = proposed[key]
        typ = spec.get("type")

        # Cast numeric strings -> number
        if typ in ("number", "integer") and isinstance(val, str):
            try:
                n = float(val) if typ == "number" else int(val)
                proposed[key] = n
                notes.append(f"{key}: cast '{val}' → {n}")
            except Exception:
                pass

        # Uppercase currency-like fields
        if key in ("currency","iso_currency") and isinstance(val, str):
            if val.upper() != val:
                proposed[key] = val.upper()
                notes.append(f"{key}: upper '{val}' → '{val.upper()}'")

        # Enum normalization for 'reason'
        if key == "reason" and isinstance(val, str) and "enum" in spec:
            norm = _normalize_reason(val)
            if norm != val and norm in set(spec["enum"]):
                proposed[key] = norm
                notes.append(f"{key}: normalize '{val}' → '{norm}'")

    return proposed, notes
