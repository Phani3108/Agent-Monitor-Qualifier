from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge

RUNS_TOTAL = Counter(
    "aah_runs_total",
    "Total number of AAH runs",
    labelnames=("agent","environment","certified")
)

ASSERTIONS_TOTAL = Counter(
    "aah_assertions_total",
    "Total assertions evaluated",
    labelnames=("pack","status")  # status: pass|fail
)

PACK_LATENCY_MS = Histogram(
    "aah_pack_latency_ms",
    "Pack execution latency in ms",
    labelnames=("pack",),
    buckets=(5,10,25,50,100,250,500,1000,1500,2000,3000,5000)
)

RUN_OVERALL_SCORE = Gauge(
    "aah_run_overall_score",
    "Overall score of the last run per agent/env",
    labelnames=("agent","environment")
)

# Per-request metrics for Determinism 2.0
REQUEST_LATENCY_MS = Histogram(
    "aah_request_latency_ms",
    "Per-model request latency in ms",
    labelnames=("pack","agent","environment"),
    buckets=(5,10,25,50,100,250,500,1000,1500,2000,3000,5000,8000)
)

REQUEST_COST_USD = Histogram(
    "aah_request_cost_usd",
    "Per-model request cost (USD)",
    labelnames=("pack","agent","environment"),
    buckets=(0.0001,0.0005,0.001,0.002,0.005,0.01,0.02,0.05,0.1)
)

REQUEST_ERRORS_TOTAL = Counter(
    "aah_request_errors_total",
    "Errors during agent invocation",
    labelnames=("pack","agent","environment")
)
