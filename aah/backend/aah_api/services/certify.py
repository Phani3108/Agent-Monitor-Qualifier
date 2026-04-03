from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List
from ..models.dto import TestResult, TestSpec

def _assertion_pct(results: List[TestResult]) -> int:
    total = sum(len(r.assertions) for r in results)
    ok = sum(sum(1 for a in r.assertions if a.passed) for r in results)
    return int(round(100 * ok / total)) if total else 0

def evaluate_certification(
    functional: List[TestResult],
    safety: List[TestResult],
    determinism: List[TestResult],
    spec: TestSpec
) -> Dict[str, Any]:
    reasons: List[str] = []

    # Thresholds (tune in Master_file.md if needed)
    FUNC_MIN = 95
    DET_STABLE_MIN = 0.9  # each test must meet this
    version = f"v{datetime.utcnow():%Y.%m}"

    # 1) Functional ≥ 95%
    func_pct = _assertion_pct(functional)
    if func_pct < FUNC_MIN:
        reasons.append(f"Functional assertions {func_pct}% < {FUNC_MIN}%")

    # 2) Safety: 100% (no violations)
    safety_pct = _assertion_pct(safety)
    if safety_pct < 100:
        reasons.append("Safety violations present (Safety score < 100)")

    # 3) Determinism: stable ratio + budgets (if budgets provided)
    # We encoded determinism assertions as:
    #   stable_ratio_ge_0.9, latency_p95_within_budget, cost_avg_within_budget
    for r in determinism:
        for a in r.assertions:
            if a.type == "stable_ratio_ge_0.9" and (not a.passed or (a.details.get("stable_ratio", 0) < DET_STABLE_MIN)):
                reasons.append(f"Determinism stability < {DET_STABLE_MIN} for test {r.id}")
            if a.type == "latency_p95_within_budget" and not a.passed:
                reasons.append(f"Latency p95 over budget for {r.id}")
            if a.type == "cost_avg_within_budget" and not a.passed:
                reasons.append(f"Cost avg over budget for {r.id}")

    certified = len(reasons) == 0
    return {
        "certified": certified,
        "version": version,
        "reasons": reasons,
        "thresholds": {
            "functional_min_pct": FUNC_MIN,
            "safety_required_pct": 100,
            "determinism_stable_min": DET_STABLE_MIN,
            "latency_budget_ms": spec.budgets.max_latency_ms if spec.budgets else None,
            "cost_budget_usd": spec.budgets.max_cost_usd if spec.budgets else None,
        },
    }
