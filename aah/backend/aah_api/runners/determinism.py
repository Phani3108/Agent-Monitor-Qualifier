

from __future__ import annotations
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from ..models.dto import TestSpec, TestResult, AssertionResult
from ..adapters.base import AgentAdapter
from ..utils.stats import percentiles, coeff_variation, mode_ratio, mini_signature
from ..services.metrics import REQUEST_LATENCY_MS, REQUEST_COST_USD, REQUEST_ERRORS_TOTAL

DEFAULT_SAMPLES = 10
DEFAULT_CONCURRENCY = 3

def _contains_all(text: str, needles: List[str]) -> bool:
    t = (text or "").lower()
    return all(n.lower() in t for n in needles)

def _contains_none(text: str, needles: List[str]) -> bool:
    t = (text or "").lower()
    return all(n.lower() not in t for n in needles)

class DeterminismRunner:
    name = "determinism"

    def __init__(self, adapter: AgentAdapter, agent_name: str, environment: str):
        self.agent = adapter
        self.agent_name = agent_name
        self.environment = environment

    def run(self, spec: TestSpec) -> List[TestResult]:
        cfg = (spec.model_dump() or {}).get("determinism") or {}
        samples = int(cfg.get("samples") or DEFAULT_SAMPLES)
        conc = int(cfg.get("concurrency") or DEFAULT_CONCURRENCY)
        th = cfg.get("thresholds") or {}
        min_det = float(th.get("min_determinism_pct", 90))
        max_p95_lat = th.get("max_p95_latency_ms")
        max_p95_cost = th.get("max_p95_cost_usd")
        max_cv_lat = th.get("max_cv_latency", 0.35)

        results: List[TestResult] = []

        for t in spec.tests:
            texts: List[str] = []
            sigs: List[str] = []
            lats: List[float] = []
            costs: List[float] = []
            passes: List[bool] = []

            def one_call() -> Tuple[str, float, float, bool]:
                try:
                    text, tool_calls, latency_ms, cost_usd = self.agent.invoke(t.prompt, {"tools": None})
                    # record metrics
                    REQUEST_LATENCY_MS.labels(self.name, self.agent_name, self.environment).observe(latency_ms)
                    REQUEST_COST_USD.labels(self.name, self.agent_name, self.environment).observe(cost_usd or 0.0)
                    # lightweight functional pass check (contains/not_contains)
                    ok = True
                    if t.expects:
                        e = t.expects.model_dump()
                        if "contains" in e:
                            ok = ok and _contains_all(text, e.get("contains") or [])
                        if "not_contains" in e:
                            ok = ok and _contains_none(text, e.get("not_contains") or [])
                    return text, float(latency_ms), float(cost_usd or 0.0), ok
                except Exception:
                    REQUEST_ERRORS_TOTAL.labels(self.name, self.agent_name, self.environment).inc()
                    return "", 0.0, 0.0, False

            # execute with bounded concurrency
            with ThreadPoolExecutor(max_workers=conc) as ex:
                futs = [ex.submit(one_call) for _ in range(samples)]
                for fut in as_completed(futs):
                    text, lat, cost, ok = fut.result()
                    texts.append(text)
                    sigs.append(mini_signature(text))
                    lats.append(lat)
                    costs.append(cost)
                    passes.append(ok)

            # stats
            pct = percentiles(lats)
            cv = coeff_variation(lats)
            det_pct = mode_ratio(sigs)
            pass_rate = 100.0 * (sum(1 for p in passes if p) / len(passes)) if passes else 0.0

            assertions: List[AssertionResult] = [
                AssertionResult(type="determinism_pct", passed=(det_pct >= min_det), details={"value": round(det_pct,2), "min": min_det}),
                AssertionResult(type="cv_latency", passed=(cv <= max_cv_lat), details={"value": round(cv,3), "max": max_cv_lat})
            ]
            if max_p95_lat is not None:
                assertions.append(AssertionResult(type="p95_latency", passed=(pct["p95"] <= float(max_p95_lat)), details={"value": int(pct["p95"]), "max_ms": int(max_p95_lat)}))
            if max_p95_cost is not None:
                assertions.append(AssertionResult(type="p95_cost", passed=(percentiles(costs)["p95"] <= float(max_p95_cost)), details={"value": round(percentiles(costs)["p95"],5), "max_usd": float(max_p95_cost)}))

            # flaky test (content expectations unstable)
            assertions.append(AssertionResult(type="pass_rate", passed=(pass_rate >= 100.0), details={"value_pct": round(pass_rate,1)}))

            passed = all(a.passed for a in assertions)
            results.append(TestResult(
                id=f"det-{t.id}",
                pack=self.name,
                passed=passed,
                assertions=assertions,
                latency_ms=int(pct["p95"]),
                cost_usd=percentiles(costs)["p95"],
                response_text=texts[0] if texts else "",
                tool_calls=[],
                meta={
                    "samples": samples, "concurrency": conc,
                    "latency_ms": {"p50": int(pct["p50"]), "p95": int(pct["p95"]), "p99": int(pct["p99"]), "cv": round(cv,3)},
                    "cost_usd": {"p50": round(percentiles(costs)["p50"],6), "p95": round(percentiles(costs)["p95"],6)},
                    "determinism_pct": round(det_pct,2),
                    "pass_rate_pct": round(pass_rate,1)
                }
            ))
        return results
