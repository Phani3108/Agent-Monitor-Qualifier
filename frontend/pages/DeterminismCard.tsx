import { useState, useEffect } from "react";
import { API_BASE } from "../lib/api";
import { fetchAuth } from "../lib/auth";

export default function DeterminismCard({ runId }: { runId: string }) {
  const [detStats, setDetStats] = useState<any[]>([]);
  const [reSamples, setReSamples] = useState<number>(20);
  const [reConc, setReConc] = useState<number>(5);
  const [rerunLoading, setRerunLoading] = useState(false);

  useEffect(() => {
    if (!runId) return;
    fetchAuth(`${API_BASE}/runs/${runId}/determinism/stats`)
      .then(r => r.json())
      .then(setDetStats)
      .catch(() => {});
  }, [runId]);

  async function rerunDet() {
    setRerunLoading(true);
    try {
      const res = await fetchAuth(`${API_BASE}/runs/${runId}/determinism/rerun`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ samples: reSamples, concurrency: reConc }),
      });
      if (res.ok) {
        const j = await res.json();
        window.location.href = `/run/${j.run_id}`;
      }
    } finally {
      setRerunLoading(false);
    }
  }

  if (detStats.length === 0) return null;

  function MetricCell({ value, unit, warn }: { value: any; unit?: string; warn?: boolean }) {
    return (
      <span className={`font-mono text-sm ${warn ? "text-amber-600 font-semibold" : "text-gray-700"}`}>
        {value}{unit && <span className="text-gray-400 text-xs ml-0.5">{unit}</span>}
      </span>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">
        Determinism (Load Testing)
      </h2>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="px-3 py-2 text-left font-medium text-gray-500">Test</th>
              <th className="px-3 py-2 text-center font-medium text-gray-500">Status</th>
              <th className="px-3 py-2 text-right font-medium text-gray-500">Det %</th>
              <th className="px-3 py-2 text-right font-medium text-gray-500">P50</th>
              <th className="px-3 py-2 text-right font-medium text-gray-500">P95</th>
              <th className="px-3 py-2 text-right font-medium text-gray-500">P99</th>
              <th className="px-3 py-2 text-right font-medium text-gray-500">CV</th>
              <th className="px-3 py-2 text-right font-medium text-gray-500">Pass %</th>
              <th className="px-3 py-2 text-right font-medium text-gray-500">N×C</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {detStats.map((r: any) => (
              <tr key={r.id} className={r.passed ? "" : "bg-red-50/50"}>
                <td className="px-3 py-2 font-mono text-xs text-gray-700">{r.id}</td>
                <td className="px-3 py-2 text-center">
                  {r.passed ? (
                    <span className="inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">PASS</span>
                  ) : (
                    <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">FAIL</span>
                  )}
                </td>
                <td className="px-3 py-2 text-right">
                  <MetricCell value={r.determinism_pct?.toFixed?.(1) ?? "–"} unit="%" warn={r.determinism_pct < 90} />
                </td>
                <td className="px-3 py-2 text-right">
                  <MetricCell value={r.latency_ms?.p50 ?? "–"} unit="ms" />
                </td>
                <td className="px-3 py-2 text-right">
                  <MetricCell value={r.latency_ms?.p95 ?? "–"} unit="ms" warn={r.latency_ms?.p95 > 2000} />
                </td>
                <td className="px-3 py-2 text-right">
                  <MetricCell value={r.latency_ms?.p99 ?? "–"} unit="ms" />
                </td>
                <td className="px-3 py-2 text-right">
                  <MetricCell value={r.latency_ms?.cv ?? "–"} warn={r.latency_ms?.cv > 0.35} />
                </td>
                <td className="px-3 py-2 text-right">
                  <MetricCell value={r.pass_rate_pct?.toFixed?.(1) ?? "–"} unit="%" warn={r.pass_rate_pct < 100} />
                </td>
                <td className="px-3 py-2 text-right text-xs text-gray-500">
                  {r.samples}×{r.concurrency}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Rerun controls */}
      <div className="mt-4 pt-4 border-t border-gray-100 flex items-center gap-4 flex-wrap">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Rerun:</span>
        <label className="flex items-center gap-1.5 text-sm text-gray-600">
          Samples
          <input
            type="number"
            className="w-20 rounded-lg border border-gray-300 px-2 py-1 text-sm focus:ring-2 focus:ring-indigo-500"
            value={reSamples}
            onChange={e => setReSamples(parseInt(e.target.value || "0"))}
            min={1}
            max={100}
          />
        </label>
        <label className="flex items-center gap-1.5 text-sm text-gray-600">
          Concurrency
          <input
            type="number"
            className="w-20 rounded-lg border border-gray-300 px-2 py-1 text-sm focus:ring-2 focus:ring-indigo-500"
            value={reConc}
            onChange={e => setReConc(parseInt(e.target.value || "0"))}
            min={1}
            max={20}
          />
        </label>
        <button
          className="rounded-lg bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 transition"
          onClick={rerunDet}
          disabled={rerunLoading}
        >
          {rerunLoading ? "Running…" : "Run determinism only"}
        </button>
      </div>
    </div>
  );
}
