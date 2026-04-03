from __future__ import annotations
from pathlib import Path
import hashlib

REPO_ROOT = Path(__file__).resolve().parents[2]
TRUTH_POLICY_PATH = REPO_ROOT / "Truth_policy.md"
SPEC_SCHEMA_PATH = REPO_ROOT / "specs/schemas/test_spec.schema.json"

def _sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_policy_hash() -> str:
    if not TRUTH_POLICY_PATH.exists():
        raise RuntimeError("Truth_policy.md missing")
    return _sha256_of(TRUTH_POLICY_PATH)

def load_schema_hash() -> str:
    if not SPEC_SCHEMA_PATH.exists():
        raise RuntimeError("specs/schemas/test_spec.schema.json missing")
    return _sha256_of(SPEC_SCHEMA_PATH)
