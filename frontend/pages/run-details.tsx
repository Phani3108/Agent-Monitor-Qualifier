import { useEffect, useState } from "react";
import VerifyRun from "../../aah/frontend/app/components/VerifyRun";
import DeterminismCard from "./DeterminismCard";
import TagEditor from "./run/TagEditor";
import { API_BASE } from "../lib/api";
import { fetchAuth } from "../lib/auth";

type PackScore = { name: string; score: number; tests: number; passed: number };

function ScoreRing({ score, label, size = 80 }: { score: number; label: string; size?: number }) {
  const r = (size - 8) / 2;
  const circum = 2 * Math.PI * r;
  const offset = circum - (score / 100) * circum;
  const color = score >= 90 ? "#059669" : score >= 70 ? "#d97706" : "#dc2626";
  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e5e7eb" strokeWidth={6} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={6}
          strokeDasharray={circum} strokeDashoffset={offset} strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`} />
        <text x="50%" y="50%" textAnchor="middle" dy="0.35em" className="text-lg font-bold" fill={color}>
          {score}
        </text>
      </svg>
      <span className="text-xs text-gray-500 mt-1">{label}</span>
    </div>
  );
}

function CertBadge({ certified, version }: { certified: boolean; version?: string }) {
  if (certified) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-800">
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
        Certified {version}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-700">
      Not Certified
    </span>
  );
}

export default function RunDetails({ runId }: { runId: string }) {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAuth(`${API_BASE}/runs/${runId}`)
      .then(r => r.json())
      .then(data => setSummary(data))
      .finally(() => setLoading(false));
  }, [runId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-400">Loading run details…</div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-red-500">Run not found</div>
      </div>
    );
  }

  const scores = summary.scores || {};
  const cert = summary.cert || {};

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto">
          <a href="/" className="text-sm text-gray-500 hover:text-gray-700">← All runs</a>
          <div className="flex items-center justify-between mt-2">
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                Run <span className="font-mono text-indigo-600">{runId.slice(0, 8)}</span>
              </h1>
              <p className="text-sm text-gray-500 mt-0.5">
                {summary.agent} · {summary.environment}
                {summary.created_at && ` · ${new Date(summary.created_at).toLocaleString()}`}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <CertBadge certified={summary.certified} version={cert.version} />
              <a
                href={`${API_BASE}/runs/${runId}/report`}
                target="_blank"
                className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
              >
                View Report
              </a>
              <a
                href={`${API_BASE}/runs/${runId}/badge.svg`}
                target="_blank"
                className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
              >
                Badge
              </a>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6 space-y-6">
        {/* Scores grid */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">Scores</h2>
          <div className="flex items-center justify-around flex-wrap gap-4">
            <ScoreRing score={scores.overall ?? 0} label="Overall" size={100} />
            {scores.functional !== undefined && <ScoreRing score={scores.functional} label="Functional" />}
            {scores.safety !== undefined && <ScoreRing score={scores.safety} label="Safety" />}
            {scores.determinism !== undefined && <ScoreRing score={scores.determinism} label="Determinism" />}
            {scores.compliance !== undefined && <ScoreRing score={scores.compliance} label="Compliance" />}
            {scores.tool_robustness !== undefined && <ScoreRing score={scores.tool_robustness} label="Tool Robust" />}
          </div>
        </div>

        {/* Totals + meta */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="text-2xl font-bold text-gray-900">{summary.totals?.tests ?? 0}</div>
            <div className="text-xs text-gray-500 mt-1">Total tests</div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="text-2xl font-bold text-emerald-600">{summary.totals?.passed ?? 0}</div>
            <div className="text-xs text-gray-500 mt-1">Passed</div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="text-2xl font-bold text-red-600">{summary.totals?.failed ?? 0}</div>
            <div className="text-xs text-gray-500 mt-1">Failed</div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="text-2xl font-bold text-gray-900">{summary.pass_rate ?? 0}%</div>
            <div className="text-xs text-gray-500 mt-1">Pass rate</div>
          </div>
        </div>

        {/* Certification reasons */}
        {cert.reasons?.length > 0 && (
          <div className="bg-red-50 rounded-xl border border-red-200 p-5">
            <h2 className="text-sm font-semibold text-red-800 mb-2">Certification Blockers</h2>
            <ul className="list-disc list-inside space-y-1">
              {cert.reasons.map((r: string, i: number) => (
                <li key={i} className="text-sm text-red-700">{r}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Packs executed */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">Packs Executed</h2>
          <div className="flex flex-wrap gap-2">
            {(summary.packs_executed || []).map((p: string) => (
              <span key={p} className="rounded-full bg-indigo-50 border border-indigo-200 px-3 py-1 text-xs font-medium text-indigo-700">
                {p}
              </span>
            ))}
          </div>
        </div>

        {/* Tags */}
        {summary && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <TagEditor runId={runId} initialTags={summary.tags || []} />
          </div>
        )}

        {/* Verify */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <VerifyRun runId={runId} />
        </div>

        {/* Determinism */}
        <DeterminismCard runId={runId} />

        {/* Policy / schema hashes */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Integrity</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono text-gray-600">
            <div>
              <span className="text-gray-400">policy:</span> {summary.policy_hash?.slice(0, 16)}…
            </div>
            <div>
              <span className="text-gray-400">schema:</span> {summary.spec_schema_hash?.slice(0, 16)}…
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
