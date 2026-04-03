from __future__ import annotations
from typing import Any, Dict
from jsonschema import validate, Draft202012Validator

def validate_spec(yaml_str, schema_path):
    pass  # ...existing code or implementation...

def validate_json(instance: Dict[str, Any], schema: Dict[str, Any]) -> None:
    Draft202012Validator.check_schema(schema)
    validate(instance=instance, schema=schema)
