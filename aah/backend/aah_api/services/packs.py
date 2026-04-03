from __future__ import annotations


import hashlib, re, json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKS_DIR = REPO_ROOT / "specs" / "packs"
PACKS_DIR.mkdir(parents=True, exist_ok=True)
REG_DIR = REPO_ROOT / "specs" / "registry"
REG_INDEX = REG_DIR / "index.yaml"
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

def _semver_key(v: str):
    m = SEMVER_RE.match(v or "0.0.0")
    if not m: return (0,0,0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))

def _registry_index() -> dict:
    if not REG_INDEX.exists(): return {"packs": {}}
    return yaml.safe_load(REG_INDEX.read_text(encoding="utf-8")) or {"packs": {}}

def resolve_pack(name_spec: str) -> Dict[str, Any]:
    """
    Accepts: 'name', 'name@1.2.3', 'name@~2025.08', 'name@~2025'
    Returns dict with {name, version, sha256, data}
    """
    if "@" in name_spec:
        name, ver_spec = name_spec.split("@", 1)
    else:
        name, ver_spec = name_spec, None
    idx = _registry_index().get("packs", {}).get(name)
    if not idx:  # fallback to flat packs dir
        return {"name": name, "version": "unversioned", "sha256": "", "data": load_pack(name)}

    candidates = sorted([x["version"] for x in idx], key=_semver_key)
    pick = None
    if not ver_spec:
        pick = candidates[-1]
    elif ver_spec.startswith("~"):
        base = ver_spec[1:]
        pick = max([v for v in candidates if v.startswith(base)], key=_semver_key, default=None)
    else:
        pick = ver_spec if ver_spec in candidates else None

    if not pick:
        raise FileNotFoundError(f"No version match for {name_spec}. Available: {', '.join(candidates)}")

    file_rel = next(x["file"] for x in idx if x["version"] == pick)
    p = REG_DIR / file_rel
    raw = p.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    return {"name": data.get("name") or name, "version": pick, "sha256": _sha256_text(raw), "data": data}

def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def list_packs() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for p in sorted(PACKS_DIR.glob("*.y*ml")):
        raw = p.read_text(encoding="utf-8")
        data = yaml.safe_load(raw) or {}
        name = data.get("name") or p.stem
        version = str(data.get("version") or "unversioned")
        langs = set()
        for t in (data.get("tests") or []):
            pr = t.get("prompt")
            if isinstance(pr, dict):
                langs |= set(pr.keys())
        out.append({
            "name": name,
            "version": version,
            "file": p.name,
            "sha256": _sha256_text(raw),
            "tests": len(data.get("tests") or []),
            "languages": sorted(langs)
        })
    return out

def load_pack(name: str) -> Dict[str, Any]:
    # name may be file stem or filename
    candidate_files = [PACKS_DIR / f"{name}.yaml", PACKS_DIR / f"{name}.yml", PACKS_DIR / name]
    for c in candidate_files:
        if c.exists():
            return yaml.safe_load(c.read_text(encoding="utf-8")) or {}
    raise FileNotFoundError(f"Pack not found: {name}")
