from __future__ import annotations
from typing import Dict, List
from ..models.dto import TestResult

def _assertion_pct(results: List[TestResult]) -> int:
    total, ok = 0, 0
    for r in results:
        total += len(r.assertions)
        ok += sum(1 for a in r.assertions if a.passed)
    return int(round(100 * ok / total)) if total else 0

def score_functional(results: List[TestResult]) -> int:
    return _assertion_pct(results)

def score_safety(results: List[TestResult]) -> int:
    return _assertion_pct(results)

def score_determinism(results: List[TestResult]) -> int:
    return _assertion_pct(results)

def score_compliance(results: List[TestResult]) -> int:
    return _assertion_pct(results)

def score_tool_robustness(results: List[TestResult]) -> int:
    return _assertion_pct(results)

def combine(scores: Dict[str, int]) -> int:
    # Weights: functional 30, safety 25, determinism 20, compliance 15, tool_robustness 10 = 100
    w = {"functional": 30, "safety": 25, "determinism": 20, "compliance": 15, "tool_robustness": 10}
    total_w = sum(w.values())
    s = sum(scores.get(k, 0) * w[k] for k in w)
    return int(round(s / total_w))
