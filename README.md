# 🛡️ AAH — Agent Auditor & Hardener

CI/CD quality gate for AI agents. Validates correctness, safety, determinism, and compliance before deployment.

**Now with AgentMLOps Maturity Console** — a public-facing readiness assessment that scores organizations across 7 dimensions, generates a maturity level (L1–L5), gap analysis, and 90-day roadmap.

---

## ✨ What It Does

- 🧪 **Runs test suites** against live AI agents (chatbots, refund processors, support bots)
- 📊 **Scores on 7 dimensions** — functional, safety, determinism, compliance, tool robustness, grounding, policy lint
- ✅ **Certifies** agents that meet thresholds (95% functional, 100% safety, 90% determinism)
- 🔧 **Auto-hardens** failing agents with prompt patches + optional GitHub PR
- 📋 **Generates trust reports** (HTML, badge SVG, signed manifests)
- 🔒 **Cryptographic evidence** — SHA256 + HMAC signed run artifacts
- 📈 **Maturity Console** — 7-dimension AgentMLOps readiness quiz with gap analysis and 90-day roadmap

---

## 📈 AgentMLOps Maturity Console

A public-facing readiness assessment that scores your organization across 7 AgentMLOps dimensions — each mapping 1:1 to an AAH runner. Take the quiz, get a maturity level (L1–L5), a gap analysis, and a 90-day roadmap to production readiness.

### Maturity Levels

| Level | Name | Description |
|-------|------|-------------|
| **L1** | Ad-hoc | No formal processes. Agent behavior managed reactively. |
| **L2** | Repeatable | Basic processes exist but are manual and inconsistent. |
| **L3** | Defined | Processes documented and followed but not automated. |
| **L4** | Managed | Automated processes with monitoring and alerting. |
| **L5** | Optimized | Fully automated with continuous improvement and self-healing. |

### 7 Dimensions → AAH Runner Mapping

| Maturity Dimension | AAH Runner | What It Assesses |
|--------------------|------------|------------------|
| **Versioning** | PolicyLintRunner | Prompt versioning, config-as-code, change tracking |
| **Canary / Rollback** | FunctionalRunner | Staged rollout, regression gates, rollback automation |
| **Drift Detection** | DeterminismRunner | Output stability monitoring, behavioral drift alerting |
| **Eval Pipelines** | GroundingRunner | Automated evaluation, source-grounded verification |
| **Cost Attribution** | ComplianceRunner | Per-tenant cost tracking, budget enforcement |
| **Policy Enforcement** | SafetyRunner | Adversarial testing, PII protection, injection defense |
| **Incident Runbooks** | ToolRobustnessRunner | Error handling, chaos testing, automated incident response |

### Maturity Console Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| `GET` | `/maturity/questions` | Get the full quiz (7 dimensions × 3 questions) |
| `POST` | `/maturity/assess` | Submit answers, get scored assessment |
| `GET` | `/maturity/{id}` | Retrieve a saved assessment |
| `GET` | `/maturity/{id}/roadmap` | Get the 90-day roadmap |
| `GET` | `/maturity/{id}/report` | HTML report with radar chart, gaps, roadmap |

### How It Works

1. **Take the quiz** — 21 questions across 7 dimensions (3 per dimension), each scored L1–L5
2. **Get your score** — per-dimension scores, overall maturity level, SVG radar chart
3. **See the gaps** — any dimension at L3 or below is flagged with a specific remediation action
4. **Follow the roadmap** — 90-day week-by-week plan, prioritized by severity, each step linked to an AAH runner
5. **Close the gaps** — each "Fix with AAH" CTA links directly to the runner that addresses that dimension

---

## 🏗️ Architecture

```
Spec YAML → Orchestrator → 7 Runners → Scorer → Certifier → Report + Badge
                ↓
         Agent Adapter (mock / OpenAI / Claude / Gemini / Azure OpenAI / HTTP)
```

### Runners

| Runner | What It Tests |
|--------|--------------|
| 🎯 **Functional** | Golden-path assertions + tool-call schema validation with fix hints |
| 🛡️ **Safety** | 15 adversarial prompts — injection, PII traps, jailbreak, leakage |
| 📈 **Determinism** | N-sample stability, P50/P95/P99 latency, cost budgets, CV |
| 📋 **Compliance** | PCI card masking, PII detection (Luhn), tool allowlists |
| 💥 **Tool Robustness** | 10 chaos scenarios — 500s, timeouts, rate limits, DNS failures |
| 📚 **Grounding** | Source-of-truth adherence via TF-IDF passage matching |
| 🔍 **Policy Lint** | Static analysis of agent prompt definitions |

---

## 🔌 Supported Providers

| Provider | Models | Env Var |
|----------|--------|---------|
| **OpenAI** | GPT-5, GPT-5 Mini, GPT-5 Nano | `OPENAI_API_KEY` |
| **Anthropic** | Claude 4.6 Opus, Claude 4.6 Sonnet, Claude 3 Haiku | `ANTHROPIC_API_KEY` |
| **Google** | Gemini 3.1 Pro, Gemini 2.5 Flash, Gemini Nano | `GOOGLE_API_KEY` |
| **Azure OpenAI** | Any deployment | `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT` |
| **HTTP** | Any REST endpoint (A2A protocol) | Configured in `agent.yaml` |
| **Mock** | Buggy + strict simulation modes | Default (no key needed) |

---

## 🚀 Quickstart

```bash
git clone https://github.com/Phani3108/Agent-Monitor-Qualifier.git
cd Agent-Monitor-Qualifier/aah
cp backend/.env.example backend/.env
docker compose up --build
```

- **API:** `http://localhost:8080`
- **Frontend:** `http://localhost:3000`

### Run a test

```bash
curl -X POST http://localhost:8080/runs \
  -H "Content-Type: application/json" \
  -d '{"spec_yaml": "...", "packs": ["functional", "safety", "determinism"]}'
```

---

## 📁 Project Structure

```
├── aah/
│   ├── backend/
│   │   └── aah_api/
│   │       ├── runners/        # 7 test runners (functional, safety, determinism, ...)
│   │       ├── adapters/       # Provider adapters (OpenAI, Claude, Gemini, Azure, HTTP, Mock)
│   │       ├── services/       # Orchestrator, scoring, certification, maturity, signing
│   │       ├── routes/         # API endpoints (runs, maturity, reports, auth, ...)
│   │       ├── models/         # Pydantic DTOs (TestSpec, RunSummary, MaturityAssessment)
│   │       ├── utils/          # PII detection, stats, schema hints, diff
│   │       ├── data/           # Maturity questions bank (YAML-driven)
│   │       └── assets/         # Report templates, badge SVG, maturity report
│   └── frontend/               # Next.js dashboard
├── agents/                     # Agent definitions (agent.yaml per agent)
├── specs/
│   ├── packs/                  # Reusable test packs (functional_refunds, safety_injection, pii_traps)
│   ├── registry/               # Versioned pack registry (semver)
│   └── schemas/                # JSON Schema for test specs
├── connectors/                 # Data sources for grounding (policy docs, security redlines)
├── config/                     # Users, saved views
├── tenants/                    # Multi-tenant config (PII policy, tool allowlists, budgets)
└── frontend/                   # Standalone dashboard pages (runs, maturity quiz, results)
```

---

## 🔑 Key API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| `POST` | `/runs` | Create a validation run |
| `GET` | `/runs/{id}` | Get run summary |
| `GET` | `/runs/{id}/report` | HTML trust report |
| `GET` | `/runs/{id}/badge.svg` | Certification badge |
| `POST` | `/runs/{id}/harden` | Auto-generate hardening patches |
| `GET` | `/runs/{id}/verify` | Verify cryptographic signatures |
| `POST` | `/runs/{id}/determinism/rerun` | Re-run with different sample/concurrency |
| `GET` | `/compare?base={id}&head={id}` | Compare two runs |
| `GET` | `/maturity/questions` | Maturity quiz questions |
| `POST` | `/maturity/assess` | Submit maturity assessment |
| `GET` | `/maturity/{id}` | Get assessment results |
| `GET` | `/maturity/{id}/roadmap` | 90-day improvement roadmap |
| `GET` | `/maturity/{id}/report` | HTML maturity report with radar chart |

---

## 🧮 Scoring

| Dimension | Weight |
|-----------|--------|
| Functional | 30% |
| Safety | 25% |
| Determinism | 20% |
| Compliance | 15% |
| Tool Robustness | 10% |

**Certification thresholds:** Functional ≥ 95%, Safety = 100%, Determinism stability ≥ 90%

---

## 🔐 Security

- JWT + bcrypt authentication with role-based access (owner / maintainer / reviewer / viewer)
- SHA256 + HMAC-SHA256 signed run manifests
- Truth Policy hash verified at `/health`
- Network egress restricted to `connectors.yml` allowlist
- PII detection with Luhn card validation

---

## 📄 License

© 2026 Phani Marupaka. All rights reserved.
