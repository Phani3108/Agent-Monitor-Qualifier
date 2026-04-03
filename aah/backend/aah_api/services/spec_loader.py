from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json, yaml, hashlib
from jsonschema import validate, Draft202012Validator
from ..models.dto import TestSpec
from .policy import SPEC_SCHEMA_PATH
from .tenant import load_tenant
from .packs import resolve_pack

def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _expand_packs_and_meta(raw: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    data = dict(raw)
    tenant_name = data.get("tenant")
    tenant_cfg = load_tenant(tenant_name)
    tenant_langs: List[str] = tenant_cfg.get("languages") or ["en"]

    include: List[str] = data.get("include_packs") or []
    tests: List[Dict[str, Any]] = list(data.get("tests") or [])
    seen_ids = set(t.get("id") for t in tests if t.get("id"))
    used: List[Dict[str, Any]] = []


    for pack_name in include:
        resolved = resolve_pack(pack_name)
        pack = resolved.get("data") or {}
        used.append({
            "name": resolved["name"],
            "version": resolved.get("version", str(pack.get("version") or "unversioned")),
            "sha256": resolved["sha256"],
            "specifier": pack_name
        })
        for t in (pack.get("tests") or []):
            base_id = t["id"]
            pr = t["prompt"]
            expects = t["expects"]
            if isinstance(pr, dict):
                for lang in tenant_langs:
                    if lang in pr:
                        tid = f"{base_id}-{lang}"
                        if tid in seen_ids:
                            continue
                        tests.append({"id": tid, "prompt": pr[lang], "expects": expects})
                        seen_ids.add(tid)
            elif isinstance(pr, str):
                if base_id in seen_ids:
                    continue
                tests.append({"id": base_id, "prompt": pr, "expects": expects})
                seen_ids.add(base_id)
            else:
                raise ValueError(f"Unsupported prompt type in pack {pack_name} for test {base_id}")

    data.pop("include_packs", None)
    data["tests"] = tests
    meta = {"used_packs": used}
    return data, meta

def load_and_validate_spec_with_meta(yaml_text: str) -> Tuple[TestSpec, Dict[str, Any]]:
    raw = yaml.safe_load(yaml_text)
    if not isinstance(raw, dict):
        raise ValueError("Spec YAML must define a mapping/object at top level.")
    expanded, meta = _expand_packs_and_meta(raw)
    schema = json.loads(SPEC_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validate(instance=expanded, schema=schema)
    if not expanded.get("tests"):
        raise ValueError("No tests present after expanding include_packs.")
    return TestSpec.model_validate(expanded), meta

# keep compatibility
def load_and_validate_spec(yaml_text: str) -> TestSpec:
    spec, _ = load_and_validate_spec_with_meta(yaml_text)
    return spec

def load_spec_from_file(path: Path) -> TestSpec:
    return load_and_validate_spec(Path(path).read_text(encoding="utf-8"))
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import json, yaml
from jsonschema import validate, Draft202012Validator
from ..models.dto import TestSpec
from .policy import SPEC_SCHEMA_PATH

def load_and_validate_spec(yaml_text: str) -> TestSpec:
    data = yaml.safe_load(yaml_text)
    schema = json.loads(SPEC_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validate(instance=data, schema=schema)
    return TestSpec.model_validate(data)

def load_spec_from_file(path: Path) -> TestSpec:
    return load_and_validate_spec(Path(path).read_text(encoding="utf-8"))
