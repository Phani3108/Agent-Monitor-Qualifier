from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Any
import yaml, hashlib

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "connectors" / "sources"
SRC_DIR.mkdir(parents=True, exist_ok=True)

def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def load_sources() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for p in SRC_DIR.glob("*.y*ml"):
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        sid = str(data.get("id") or p.stem)
        data["sha256"] = _sha256_text(p.read_text(encoding="utf-8"))
        out[sid] = data
    return out

def get_passages(ids: List[str]) -> List[str]:
    src = load_sources()
    passages: List[str] = []
    for i in ids:
        d = src.get(i)
        if not d: 
            continue
        for para in d.get("passages") or []:
            passages.append(str(para))
    return passages

def list_source_meta(ids: List[str]) -> List[Dict[str, Any]]:
    src = load_sources()
    out: List[Dict[str, Any]] = []
    for i in ids:
        if i in src:
            out.append({"id": i, "title": src[i].get("title"), "sha256": src[i]["sha256"]})
    return out
