# 🛡️ AAH — Agent Auditor & Hardener

CI/CD quality gate for AI agents. Validates correctness, safety, determinism, and compliance before deployment.

---

## ✨ What It Does

- 🧪 **Runs test suites** against live AI agents (chatbots, refund processors, support bots)
- 📊 **Scores on 5 dimensions** — functional, safety, determinism, compliance, tool robustness
- ✅ **Certifies** agents that meet thresholds (95% functional, 100% safety, 90% determinism)
- 🔧 **Auto-hardens** failing agents with prompt patches + optional GitHub PR
- 📋 **Generates trust reports** (HTML, badge SVG, signed manifests)
- 🔒 **Cryptographic evidence** — SHA256 + HMAC signed run artifacts

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
│   │       ├── services/       # Orchestrator, scoring, certification, remediation, signing
│   │       ├── routes/         # 16 API endpoints
│   │       ├── models/         # Pydantic DTOs (TestSpec, RunSummary, CertStatus)
│   │       ├── utils/          # PII detection, stats, schema hints, diff
│   │       └── assets/         # Report template, badge SVG, compare HTML
│   └── frontend/               # Next.js dashboard
├── agents/                     # Agent definitions (agent.yaml per agent)
├── specs/
│   ├── packs/                  # Reusable test packs (functional_refunds, safety_injection, pii_traps)
│   ├── registry/               # Versioned pack registry (semver)
│   └── schemas/                # JSON Schema for test specs
├── connectors/                 # Data sources for grounding (policy docs, security redlines)
├── config/                     # Users, saved views
├── tenants/                    # Multi-tenant config (PII policy, tool allowlists, budgets)
└── frontend/                   # Standalone dashboard pages
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
