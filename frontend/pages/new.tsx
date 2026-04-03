import React, { useState } from "react";
import { API_BASE } from "../lib/api";
import { fetchAuth } from "../lib/auth";

const PACKS = [
  { id: "functional", label: "Functional", desc: "Golden-path + tool schema validation" },
  { id: "safety", label: "Safety", desc: "Injection, PII traps, jailbreak, leakage" },
  { id: "determinism", label: "Determinism", desc: "N-sample stability + latency/cost budgets" },
  { id: "compliance", label: "Compliance", desc: "PCI, PII masking, tool allowlist" },
  { id: "tool_robustness", label: "Tool Robustness", desc: "Chaos: 500s, timeouts, rate limits" },
  { id: "grounding", label: "Grounding", desc: "Source-of-truth adherence verification" },
  { id: "policy_lint", label: "Policy Lint", desc: "Static analysis of agent prompt" },
] as const;

const SAMPLE_SPEC = `agent: support-refunds-bot
environment: staging
tenant: default
policies:
  pii_leakage: block
  tool_schema_strict: true
budgets:
  max_latency_ms: 1800
  max_cost_usd: 0.02
tests:
  - id: refunds-01
    prompt: "My card was double-charged for ₹500. Please help."
    expects:
      contains: ["raise_ticket"]
      tool_calls:
        - name: create_support_case
          schema_ok: true
  - id: refunds-02
    prompt: "I need a refund for order #12345."
    expects:
      contains: ["refund", "support"]
      blocked: false
`;

export default function NewRunPage() {
  const [specYaml, setSpecYaml] = useState(SAMPLE_SPEC);
  const [cho, setCho] = useState(() => Object.fromEntries(PACKS.map(p => [p.id, true])));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    setSubmitting(true);
    setError("");
    const selectedPacks = PACKS.filter(p => cho[p.id]).map(p => p.id);
    try {
      const res = await fetchAuth(`${API_BASE}/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ spec_yaml: specYaml, packs: selectedPacks }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }));
        setError(body.detail || "Failed to create run");
        return;
      }
      const data = await res.json();
      window.location.href = `/run/${data.run_id}`;
    } catch (e: any) {
      setError(e.message || "Network error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <a href="/" className="text-sm text-gray-500 hover:text-gray-700">← Back to runs</a>
            <h1 className="text-xl font-bold text-gray-900 mt-1">New Validation Run</h1>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-6 space-y-6">
        {/* Spec YAML */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Test Specification (YAML)
          </label>
          <textarea
            className="w-full h-72 rounded-lg border border-gray-300 px-4 py-3 font-mono text-sm
                       focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-y"
            value={specYaml}
            onChange={e => setSpecYaml(e.target.value)}
            spellCheck={false}
          />
        </div>

        {/* Pack selection */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-medium text-gray-700 mb-3">Test Packs</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {PACKS.map(p => (
              <label
                key={p.id}
                className={`flex items-start gap-3 rounded-lg border p-3 cursor-pointer transition
                  ${cho[p.id] ? "border-indigo-300 bg-indigo-50/50" : "border-gray-200 bg-white hover:bg-gray-50"}`}
              >
                <input
                  type="checkbox"
                  className="mt-0.5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  checked={cho[p.id]}
                  onChange={e => setCho({ ...cho, [p.id]: e.target.checked })}
                />
                <div>
                  <div className="text-sm font-medium text-gray-900">{p.label}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{p.desc}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Submit */}
        <div className="flex justify-end">
          <button
            className="inline-flex items-center rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium
                       text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            onClick={submit}
            disabled={submitting}
          >
            {submitting ? "Running…" : "Execute Run"}
          </button>
        </div>
      </main>
    </div>
  );
}
