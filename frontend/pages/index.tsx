import { useEffect, useMemo, useState } from "react";
import { API_BASE } from "../lib/api";
import { fetchAuth } from "../lib/auth";

type Run = {
  run_id: string;
  agent: string;
  environment: string;
  tenant?: string;
  created_at?: string;
  certified?: boolean;
  scores?: { overall: number; functional?: number; safety?: number; determinism?: number; compliance?: number; tool_robustness?: number };
  packs_executed?: string[];
  tags?: string[];
  pass_rate?: number;
};

const CERT_OPTIONS = [
  { value: "any", label: "All" },
  { value: "yes", label: "Certified" },
  { value: "no", label: "Not certified" },
];

export default function Runs() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [filter, setFilter] = useState<any>({
    q: "", certified: "any", tag: "", agent: "", env: "",
  });
  const [views, setViews] = useState<any>({ views: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchAuth(`${API_BASE}/runs`).then(r => r.json()),
      fetchAuth(`${API_BASE}/views`).then(r => r.json()),
    ])
      .then(([runsData, viewsData]) => {
        setRuns(runsData);
        setViews(viewsData);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const shown = useMemo(() => {
    return runs.filter(r => {
      if (filter.agent && r.agent !== filter.agent) return false;
      if (filter.env && r.environment !== filter.env) return false;
      if (filter.tag && !(r.tags || []).includes(filter.tag)) return false;
      if (filter.certified === "yes" && !r.certified) return false;
      if (filter.certified === "no" && r.certified) return false;
      if (filter.q && !`${r.run_id} ${r.agent}`.toLowerCase().includes(filter.q.toLowerCase())) return false;
      return true;
    });
  }, [runs, filter]);

  const agents = useMemo(() => [...new Set(runs.map(r => r.agent))], [runs]);
  const envs = useMemo(() => [...new Set(runs.map(r => r.environment))], [runs]);

  async function saveView() {
    const id = prompt("View id (slug):") || "";
    if (!id) return;
    const name = prompt("View name:") || id;
    await fetchAuth(`${API_BASE}/views`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, name, query: filter }),
    });
    const j = await (await fetchAuth(`${API_BASE}/views`)).json();
    setViews(j);
  }

  function ScorePill({ value, label }: { value?: number; label: string }) {
    if (value === undefined || value === null) return null;
    const color = value >= 90 ? "bg-emerald-100 text-emerald-800"
      : value >= 70 ? "bg-amber-100 text-amber-800"
      : "bg-red-100 text-red-800";
    return (
      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${color} mr-1`}>
        {label} {value}
      </span>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900 tracking-tight">AAH — Agent Auditor & Hardener</h1>
            <p className="text-sm text-gray-500 mt-0.5">Validate · Certify · Harden</p>
          </div>
          <a href="/new" className="inline-flex items-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition">
            + New Run
          </a>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Filters */}
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <input
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Search id / agent…"
              value={filter.q}
              onChange={e => setFilter({ ...filter, q: e.target.value })}
            />
            <select
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
              value={filter.certified}
              onChange={e => setFilter({ ...filter, certified: e.target.value })}
            >
              {CERT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <select
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
              value={filter.agent}
              onChange={e => setFilter({ ...filter, agent: e.target.value })}
            >
              <option value="">All agents</option>
              {agents.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
            <select
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
              value={filter.env}
              onChange={e => setFilter({ ...filter, env: e.target.value })}
            >
              <option value="">All environments</option>
              {envs.map(e => <option key={e} value={e}>{e}</option>)}
            </select>
            <input
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
              placeholder="Filter by tag…"
              value={filter.tag}
              onChange={e => setFilter({ ...filter, tag: e.target.value })}
            />
            <button
              className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
              onClick={saveView}
            >
              Save view
            </button>
          </div>
        </div>

        {/* Saved views */}
        {views.views?.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Views:</span>
            {views.views.map((v: any) => (
              <button
                key={v.id}
                className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-100 transition"
                onClick={() => setFilter(v.query)}
              >
                {v.name}
              </button>
            ))}
          </div>
        )}

        {/* Summary row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Total runs", value: runs.length },
            { label: "Certified", value: runs.filter(r => r.certified).length },
            { label: "Showing", value: shown.length },
            { label: "Agents", value: agents.length },
          ].map(s => (
            <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="text-2xl font-bold text-gray-900">{s.value}</div>
              <div className="text-xs text-gray-500 mt-1">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Runs table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-gray-400">Loading…</div>
          ) : shown.length === 0 ? (
            <div className="p-8 text-center text-gray-400">No runs match filters</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50/50">
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Run</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Agent</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Env</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Score</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Packs</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Cert</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Tags</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {shown.map(r => (
                  <tr key={r.run_id} className="hover:bg-gray-50/50 transition">
                    <td className="px-4 py-3">
                      <a href={`/run/${r.run_id}`} className="font-mono text-indigo-600 hover:text-indigo-800 font-medium">
                        {r.run_id.slice(0, 8)}
                      </a>
                      {r.created_at && (
                        <div className="text-xs text-gray-400 mt-0.5">{new Date(r.created_at).toLocaleDateString()}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-900">{r.agent}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                        {r.environment}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-bold text-lg">
                      {r.scores?.overall ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-0.5">
                        <ScorePill value={r.scores?.functional} label="F" />
                        <ScorePill value={r.scores?.safety} label="S" />
                        <ScorePill value={r.scores?.determinism} label="D" />
                        <ScorePill value={r.scores?.compliance} label="C" />
                        <ScorePill value={r.scores?.tool_robustness} label="T" />
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {r.certified ? (
                        <span className="inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800">
                          ✓ Certified
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-500">
                          —
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {(r.tags || []).map(t => (
                          <span key={t} className="rounded-full bg-violet-50 px-2 py-0.5 text-xs text-violet-700 border border-violet-200">
                            {t}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  );
}
