import React, { useEffect, useState } from "react";
import { API_BASE } from "../lib/api";

type DimensionScore = {
  dimension: string; label: string; runner: string;
  score: number; level: number; level_name: string;
};
type Gap = {
  dimension: string; label: string; current_level: number; current_name: string;
  target_level: number; gap_description: string; aah_runner: string; aah_action: string;
};
type RoadmapItem = {
  week_range: string; dimension: string; label: string;
  action: string; aah_feature: string; priority: number;
};
type Assessment = {
  id: string; org_name: string | null;
  dimension_scores: DimensionScore[];
  overall_score: number; overall_level: number; overall_level_name: string;
  gaps: Gap[]; roadmap_90d: RoadmapItem[]; created_at: string;
};

const LEVEL_COLORS: Record<number, string> = {
  1: "#dc2626", 2: "#ea580c", 3: "#d97706", 4: "#059669", 5: "#2563eb",
};
const LEVEL_BG: Record<number, string> = {
  1: "#fee2e2", 2: "#ffedd5", 3: "#fef9c3", 4: "#d1fae5", 5: "#dbeafe",
};

function RadarChart({ scores }: { scores: DimensionScore[] }) {
  const cx = 200, cy = 200, maxR = 150;
  const n = scores.length;
  const angleStep = (2 * Math.PI) / n;

  function point(i: number, r: number): [number, number] {
    const angle = -Math.PI / 2 + i * angleStep;
    return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];
  }

  function polygon(r: number): string {
    return scores.map((_, i) => point(i, r).join(",")).join(" ");
  }

  const dataPoints = scores.map((s, i) => point(i, (s.score / 5) * maxR));

  return (
    <svg viewBox="0 0 400 400" className="w-full max-w-sm mx-auto">
      {/* Grid rings */}
      {[1, 2, 3, 4, 5].map(lv => (
        <polygon key={lv} points={polygon((lv / 5) * maxR)}
          fill="none" stroke="#e2e8f0" strokeWidth={1} />
      ))}
      {/* Axes */}
      {scores.map((_, i) => {
        const [ex, ey] = point(i, maxR + 10);
        return <line key={i} x1={cx} y1={cy} x2={ex} y2={ey} stroke="#cbd5e1" strokeWidth={1} />;
      })}
      {/* Data area */}
      <polygon points={dataPoints.map(p => p.join(",")).join(" ")}
        fill="rgba(79,70,229,0.15)" stroke="#4f46e5" strokeWidth={2} />
      {/* Dots + Labels */}
      {scores.map((s, i) => {
        const [dx, dy] = dataPoints[i];
        const [lx, ly] = point(i, maxR + 28);
        return (
          <g key={s.dimension}>
            <circle cx={dx} cy={dy} r={4} fill="#4f46e5" />
            <text x={lx} y={ly} textAnchor="middle" dy="0.35em"
              style={{ fontSize: "11px", fill: "#475569", fontFamily: "system-ui" }}>
              {s.label} (L{s.level})
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default function MaturityResults({ assessmentId }: { assessmentId: string }) {
  const [data, setData] = useState<Assessment | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/maturity/${assessmentId}`)
      .then(r => r.json())
      .then(d => setData(d))
      .finally(() => setLoading(false));
  }, [assessmentId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-400">Loading results…</div>
      </div>
    );
  }
  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-red-500">Assessment not found</div>
      </div>
    );
  }

  const overallColor = LEVEL_COLORS[data.overall_level] || "#64748b";

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div>
            <a href="/maturity" className="text-sm text-gray-500 hover:text-gray-700">← New Assessment</a>
            <h1 className="text-xl font-bold text-gray-900 mt-1">
              Maturity Results
              {data.org_name && <span className="text-gray-500 font-normal"> — {data.org_name}</span>}
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">Assessment {data.id} &middot; {new Date(data.created_at).toLocaleString()}</p>
          </div>
          <div className="flex items-center gap-3">
            <a
              href={`${API_BASE}/maturity/${assessmentId}/report`}
              target="_blank"
              className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
            >
              View Report
            </a>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-6 space-y-6">
        {/* Overall score */}
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
          <div className="text-6xl font-extrabold" style={{ color: overallColor }}>
            L{data.overall_level}
          </div>
          <div className="text-lg font-semibold text-gray-700 mt-2">{data.overall_level_name}</div>
          <div className="text-sm text-gray-400 mt-1">{data.overall_score} / 5.0 overall score</div>
        </div>

        {/* Radar chart */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">Dimension Radar</h2>
          <RadarChart scores={data.dimension_scores} />
        </div>

        {/* Dimension score cards */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">Dimension Scores</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            {data.dimension_scores.map(ds => (
              <div key={ds.dimension} className="rounded-xl border border-gray-200 p-4 text-center">
                <div className="text-2xl font-extrabold" style={{ color: LEVEL_COLORS[ds.level] }}>
                  L{ds.level}
                </div>
                <div className="text-xs font-medium text-gray-700 mt-1">{ds.label}</div>
                <div className="mt-2">
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: LEVEL_BG[ds.level], color: LEVEL_COLORS[ds.level] }}>
                    {ds.level_name}
                  </span>
                </div>
                <div className="text-xs text-gray-400 mt-1">{ds.score}/5.0</div>
              </div>
            ))}
          </div>
        </div>

        {/* Gaps */}
        {data.gaps.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">
              Gaps to Close ({data.gaps.length})
            </h2>
            <div className="space-y-3">
              {data.gaps.map(gap => (
                <div key={gap.dimension}
                  className="rounded-xl border-l-4 border-red-400 bg-red-50/30 border border-gray-200 p-4">
                  <div className="flex items-center justify-between">
                    <div className="font-semibold text-gray-900">{gap.label}</div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold px-2 py-0.5 rounded-full"
                        style={{ backgroundColor: LEVEL_BG[gap.current_level], color: LEVEL_COLORS[gap.current_level] }}>
                        L{gap.current_level}
                      </span>
                      <span className="text-gray-400">&rarr;</span>
                      <span className="text-xs font-bold px-2 py-0.5 rounded-full"
                        style={{ backgroundColor: LEVEL_BG[5], color: LEVEL_COLORS[5] }}>
                        L5
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{gap.gap_description}</p>
                  <p className="text-sm text-indigo-600 font-medium mt-2">
                    Fix with AAH: {gap.aah_action}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {data.gaps.length === 0 && (
          <div className="bg-emerald-50 rounded-xl border border-emerald-200 p-6 text-center">
            <div className="text-lg font-bold text-emerald-800">All dimensions at L4+</div>
            <p className="text-sm text-emerald-600 mt-1">Your agent operations are well-managed. Keep optimizing!</p>
          </div>
        )}

        {/* 90-Day Roadmap */}
        {data.roadmap_90d.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">90-Day Roadmap</h2>
            <div className="space-y-3">
              {data.roadmap_90d.map((item, i) => (
                <div key={i} className="rounded-xl border border-gray-200 p-4">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-bold text-indigo-600">{item.week_range}</span>
                    <span className="text-xs text-gray-400">Priority {item.priority}</span>
                  </div>
                  <div className="text-sm font-medium text-gray-900">{item.label}</div>
                  <p className="text-sm text-gray-600 mt-1">{item.action}</p>
                  <p className="text-xs text-emerald-600 mt-1">AAH Feature: {item.aah_feature}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CTAs */}
        <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 rounded-xl p-8 text-center text-white">
          <h2 className="text-xl font-bold mb-2">Ready to close the gaps?</h2>
          <p className="text-indigo-200 text-sm mb-4">
            AAH&apos;s 7 runners map directly to each maturity dimension.
            Run your first evaluation to start climbing to L5.
          </p>
          <div className="flex items-center justify-center gap-4">
            <a href="/new"
              className="inline-block bg-white text-indigo-700 rounded-lg px-6 py-2.5 text-sm font-semibold hover:bg-indigo-50 transition">
              Run First AAH Evaluation
            </a>
            <a href={`${API_BASE}/maturity/${assessmentId}/report`} target="_blank"
              className="inline-block border border-white/50 text-white rounded-lg px-6 py-2.5 text-sm font-semibold hover:bg-white/10 transition">
              Download Report
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}
