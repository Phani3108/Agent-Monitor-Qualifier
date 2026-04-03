# AAH Truth & Integrity Policy (Always-On)

**Objective**
Eliminate hallucinations, enforce source-of-truth discipline, prevent premature success signals, and guarantee completeness before progress or release.

### 1) Source of Truth & Connectors

* The system may **only** read from:

  * Explicit test specs under `specs/**`
  * Agent definitions under `agents/**`
  * Tool schemas under `agents/**/tools/*.schema.json`
  * Configuration files explicitly referenced in code (e.g., `connectors.yml`)
* **Network egress is denied by default.** Any outbound call must:

  * Match an allow-listed domain/API in `connectors.yml`
  * Use a dedicated client with request/response schema validation
  * Be recorded in traces with redacted secrets
* Any data not from the above is **untrusted** and must be ignored.

### 2) No Hallucinations, No False Claims

* The system must never fabricate capabilities, results, metrics, or sources.
* All reported outcomes must be derived from:

  * Executed tests and captured traces
  * Deterministic calculations (scoring formulas)
  * Repository files at the commit under test
* If evidence is insufficient, the system must emit: **`INSUFFICIENT_EVIDENCE`** and fail the relevant assertion.

### 3) No False Celebrations / No Premature Success

* The system must not declare success, “pass,” “certified,” or “completed” unless **all** DoD criteria in `Master_file.md` are satisfied.
* Reports must display partial/failed status clearly.
* The **Certified badge** may only be produced when thresholds are met.

### 4) Completeness Enforcement (100% before move-on)

* **Prohibited markers** anywhere in tracked code:

  * `TODO`, `FIXME`, `HACK`, `WIP`, `TBD`, `NotImplementedError`, `pass  # TODO`
* **Empty constructs** are disallowed unless explicitly documented:

  * An empty `__init__.py` must include the comment: `# empty by design`
* **Orphan folders/files** (no imports/tests/references) are not allowed.
* CI must fail if any of the above are detected.

### 5) Change Safety & Minimalism

* Create only files strictly required for the change.
* Remove dead code and unused files discovered during review.
* Any new external dependency must include a rationale and security review note in the PR description.

### 6) Policy Loading & Verification

* On service start and in CI, load `Truth_policy.md`, compute a content hash, and expose:

  * `/health` field: `truth_policy_hash`
  * Runner context includes the policy text and hash (immutable during a run)
* CI must verify that the running service reports the same `truth_policy_hash` as the repo revision under test. Mismatch → fail.

### 7) Runtime Guards

* **PII Guard:** block/strip PII per policy; failing to block = Safety violation.
* **Tool Gate:** validate tool calls against JSON Schemas; deny on mismatch.
* **Determinism:** tool/structured phases must run with low temperature.

### 8) Reporting Requirements

* Every assertion failure must include:

  * The exact prompt/test ID
  * The failing check (e.g., schema field, PII class)
  * The evidence snippet (masked if sensitive)
  * A ranked fix suggestion
* Trust Report must list **all** packs executed, versions, and pass/fail counts.

### 9) Modification Rules

* This policy is **immutable** in normal PRs.
* Changes require:

  * `policy-change` label
  * Approval from CODEOWNERS
  * Version bump in report footer (e.g., `Policy v2025.08.09`)
* Runners must refuse to start if this file is missing or unreadable.

### 10) Violations & Escalation

* Any Truth Policy violation causes:

  * Run status = `failed_policy`
  * Teams/Jira notification with run ID and violation summary
  * Auto-creation of a regression test if applicable

---

## Implementation Hooks (must exist)

* **CI gates (required):**

  * `tools/quality/no_placeholders.py` – fails on prohibited markers & empty constructs.
  * `tools/quality/scan_external_calls.py` – denies non-allow-listed egress.
  * `tools/quality/validate_spec.py` – validates YAML specs.
  * `aah_api --print-policy-hash` equals repo hash of `Truth_policy.md`.

* **Runtime:**

  * Orchestrator loads the policy once per process, passes it to runners.
  * Health endpoint returns `truth_policy_hash` and `spec_schema_hash`.

* **UI/Reports:**

  * Report footer includes: `Policy <hash> • DoD check: PASS/FAIL`.

---

### Final Notes

* If there’s any conflict between this policy and other code or docs, **this policy wins**.
* Any uncertainty → prefer **blocking** over permissiveness and surface the reason in the Trust Report.

---
