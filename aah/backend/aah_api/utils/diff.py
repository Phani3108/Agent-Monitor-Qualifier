from __future__ import annotations
from typing import Any, Dict, List, Tuple
from jsonschema.exceptions import ValidationError

def summarize_jsonschema_error(err: ValidationError) -> Dict[str, Any]:
    path = list(err.path)
    schema_path = list(err.schema_path)
    out: Dict[str, Any] = {
        "message": err.message,
        "path": path,
        "schema_path": schema_path,
        "validator": err.validator,
        "validator_value": err.validator_value,
    }
    # Pull a small excerpt of the offending value
    try:
        val = err.instance
        out["instance_excerpt"] = str(val)[:160]
        out["instance_type"] = type(val).__name__
    except Exception:
        pass
    # Helpful context for required/additionalProperties/type validators
    if err.validator == "required":
        out["missing_keys"] = err.validator_value
    if err.validator == "additionalProperties":
        out["extra_keys"] = err.instance.keys() if isinstance(err.instance, dict) else []
    if err.validator == "type":
        out["expected_type"] = err.validator_value
    if err.validator == "enum":
        out["expected_enum"] = err.validator_value
    return out

def dict_key_diff(instance: Dict[str, Any], schema_props: Dict[str, Any]) -> Dict[str, List[str]]:
    inst_keys = set(instance.keys()) if isinstance(instance, dict) else set()
    prop_keys = set(schema_props.keys()) if isinstance(schema_props, dict) else set()
    return {
        "missing": sorted(list(prop_keys - inst_keys)),
        "extra": sorted(list(inst_keys - prop_keys))
    }
