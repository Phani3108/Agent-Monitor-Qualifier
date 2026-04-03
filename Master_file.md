# AAH (Agent Auditor & Hardener) — Master Guide

**Purpose**
This document is the canonical guide for building, testing, hardening, certifying, and operating AAH. It defines repo structure, workflows, quality bars, and release criteria. It must be **loaded and enforced** by CI on **every** PR. No change is “done” unless it passes the **Definition of Done** here.

### 0) Non-negotiables

* **Truth first:** All code must adhere to `Truth_policy.md` at build time, test time, and runtime.
* **No placeholders:** No incomplete classes/functions/folders. No “TODO/FIXME/NotImplementedError/placeholder stubs”.
* **Minimal surface:** No unnecessary files, modules, or endpoints.
* **Reproducible:** One-command bootstrap, deterministic CI, pinned deps where practical.
* **Observability:** Every critical path emits traces/metrics/logs.
* **Security by default:** Principle of least privilege, secrets in vault, network egress restricted to allow-listed connectors.

---

## 1) Repository Layout (MVP)

```
aah/
  backend/
    aah_api/
      main.py                # FastAPI app + health/SSE
      deps.py                # settings, clients, DI
      routes/                # /runs, /reports, /harden
      services/              # orchestrator, scoring, policy, remediation, report
      runners/               # functional.py, safety.py, determinism.py, base.py
      adapters/              # agent_http.py, tools_guard.py
      models/                # dto.py, db.py
      utils/                 # pii.py, json_schema.py, traces.py
      assets/                # report.html.j2, badge.svg
    alembic/                 # migrations
    pyproject.toml
    dockerfile
    docker-compose.yml
    .env.example
  frontend/                  # (thin Next.js dashboard)
  specs/
    schemas/test_spec.schema.json
    examples/refund_mvp.yaml
  tools/
    quality/no_placeholders.py
    quality/validate_spec.py
    quality/scan_external_calls.py
  .github/workflows/aah_on_pr.yml
  Master_file.md
  Truth_policy.md
  README.md
```

**No other top-level folders** may be added without justification in PR description.

---

## 2) Bootstrap

```bash
# From repo root
docker compose up --build     # brings up Postgres + API on :8080
```

Smoke test:

```bash
curl -s localhost:8080/health
```

---

## 3) How to Run a Test Pack (local)

```bash
# Create a run from a spec
curl -X POST localhost:8080/runs \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{ "spec_yaml": "$(cat specs/examples/refund_mvp.yaml | sed 's/\"/\\\"/g')" }
JSON

# Fetch report when done
curl -L localhost:8080/runs/<RUN_ID>/report > artifacts/report.html
```

---

## 4) CI/CD Flow

* Every PR that changes `agents/**` or `specs/**` triggers **AAH Gate** (GitHub Actions).
* CI steps (in order):

  1. `tools/quality/no_placeholders.py` — **fail** on any placeholder/incomplete code.
  2. `tools/quality/validate_spec.py` — JSON Schema validate all YAML specs.
  3. `tools/quality/scan_external_calls.py` — block network egress outside allow-listed connectors.
  4. `aah_api` unit tests + runners smoke tests.
  5. Run **AAH** on `specs/examples/refund_mvp.yaml`; publish **Trust Report** artifact.
  6. **Truth policy gate:** verify `Truth_policy.md` signature unchanged; verify policy is loaded by service (`/health` exposes policy version).
* PRs **may not modify** `Master_file.md` or `Truth_policy.md` unless the PR is labeled `policy-change` and approved by CODEOWNERS.

---

## 5) Quality Bars

* **Linters/formatters:** ruff, black, isort, mypy (strict mode for runners + policy engine).
* **Tests:** `pytest -q` with coverage ≥ **85%** on `services/*`, `runners/*`, `policy/*`.
* **Type safety:** no `type: ignore` without issue link.
* **Performance:** Determinism Pack p95 latency ≤ budget set in spec.
* **Security:** secrets only via env/Key Vault; no secrets in code, logs are masked.

---

## 6) Runners Overview

* **Functional Pack:** golden assertions, tool-call schema checks, output schema validation.
* **Safety Pack:** jailbreak/injection/PII traps (strict block).
* **Determinism Pack:** 10× runs; variance, latency, cost budgets.

Each runner must:

* Record traces (request/response/tool calls, timings).
* Emit structured assertions with pass/fail + reason.
* Respect `Truth_policy.md` (no external calls beyond allow-list).

---

## 7) Trust Scoring (MVP)

Weights: Correctness 30, Safety 25, Determinism 20, Tool Validity 10, Latency 10, Cost 5.
Expose sub-scores + recommendations in the report.

---

## 8) Auto-Hardening

“Harden” opens a GitHub PR that:

* Tightens prompts (role separation, IO contracts, temp schedule).
* Fixes/creates tool JSON Schemas (`additionalProperties: false`, required fields).
* Adds regression tests for every failure.
* Adds guardrails (PII masking, deny high-risk tool calls).
* Updates CHANGELOG with customer-safe notes.

---

## 9) Observability

* **Metrics:** runs_total, assertions_failed_total, safety_violations_total, cost_p95, latency_p95.
* **Logs:** JSON-structured; PII masked.
* **Traces:** flamegraph-style segments per test; persisted with run ID.
* **Health:** `/health` returns policy version, spec schema hash, DB status.

---

## 10) Definition of Done (DoD)

A change is **Done** only if:

* ✅ All CI checks green (including policy gate).
* ✅ Trust Score ≥ threshold or documented exception with owner approval.
* ✅ No placeholders; no orphan folders/files.
* ✅ Observability for new code paths is in place.
* ✅ User-facing impact captured in Trust Report / Release Note.

If any item fails, the project/change is **not complete**.

---

## 11) Governance & Protections

* **Immutable docs:** `Master_file.md` and `Truth_policy.md` are protected; edits require CODEOWNERS approval + `policy-change` label.
* **Connector allow-list:** `connectors.yml` is the single place to add/modify allowed sources.
* **Key rotation:** quarterly or on incident.
* **Incident learning:** every Sev-2+ failure becomes a new regression spec.

---

## 12) Minimal Command Cheatsheet

```bash
# Format/lint/typecheck
ruff check . && black --check . && mypy backend/aah_api

# Run quality gates locally
python tools/quality/no_placeholders.py
python tools/quality/validate_spec.py specs/
python tools/quality/scan_external_calls.py --connectors connectors.yml

# Start stack
docker compose up --build
```

---
