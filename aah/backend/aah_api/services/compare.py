from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .orchestrator import RUNS_DIR

def _load_summary(run_id: str) -> Dict[str, Any]:
    p = RUNS_DIR / run_id / "summary.json"
    if not p.exists():
        raise FileNotFoundError(f"summary not found for {run_id}")
    return json.loads(p.read_text(encoding="utf-8"))

def _load_results(run_id: str, pack: str) -> List[Dict[str, Any]]:
    p = RUNS_DIR / run_id / f"results.{pack}.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))

def _index_tests(results: List[Dict[str, Any]], pack: str) -> Dict[str, Dict[str, Any]]:
    return {f"{pack}:{r['id']}": r for r in results}

def _failed_assertions(r: Dict[str, Any]) -> List[str]:
    out = []
    for a in r.get("assertions", []):
        if not a.get("passed", False):
            out.append(a.get("type", "unknown"))
    return out

def compare_runs(base_id: str, head_id: str) -> Dict[str, Any]:
    base = _load_summary(base_id)
    head = _load_summary(head_id)

    packs = ["functional","safety","determinism"]
    base_map: Dict[str, Dict[str, Any]] = {}
    head_map: Dict[str, Dict[str, Any]] = {}

    for pack in packs:
        for k,v in _index_tests(_load_results(base_id, pack), pack).items():
            base_map[k] = v
        for k,v in _index_tests(_load_results(head_id, pack), pack).items():
            head_map[k] = v

    # Score deltas
    score_delta = {
        "overall": (head["scores"].get("overall",0) - base["scores"].get("overall",0)),
        "functional": (head["scores"].get("functional",0) - base["scores"].get("functional",0)),
        "safety": (head["scores"].get("safety",0) - base["scores"].get("safety",0)),
        "determinism": (head["scores"].get("determinism",0) - base["scores"].get("determinism",0)),
    }

    # Test pass/fail deltas & regressions/improvements
    regressions, improvements, unchanged = [], [], []
    all_keys = set(base_map) | set(head_map)
    for k in sorted(all_keys):
        b = base_map.get(k)
        h = head_map.get(k)
        if not b or not h:
            continue
        if b["passed"] and not h["passed"]:
            regressions.append({
                "test": k, "from": "PASS", "to": "FAIL",
                "new_failures": _failed_assertions(h)
            })
        elif (not b["passed"]) and h["passed"]:
            improvements.append({"test": k, "from": "FAIL", "to": "PASS"})
        else:
            unchanged.append({"test": k, "status": "PASS" if h["passed"] else "FAIL"})

    return {
        "base": {
            "run_id": base["run_id"], "created_at": base["created_at"],
            "scores": base["scores"], "certified": base.get("certified", False)
        },
        "head": {
            "run_id": head["run_id"], "created_at": head["created_at"],
            "scores": head["scores"], "certified": head.get("certified", False)
        },
        "score_delta": score_delta,
        "totals": {
            "regressions": len(regressions),
            "improvements": len(improvements),
            "unchanged": len(unchanged)
        },
        "regressions": regressions[:100],
        "improvements": improvements[:100]
    }
