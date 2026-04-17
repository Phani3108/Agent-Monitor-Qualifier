import React, { useEffect, useState } from "react";
import { API_BASE } from "../lib/api";

type Option = { label: string; score: number };
type Question = { id: string; text: string; options: Option[] };
type Dimension = {
  key: string;
  label: string;
  runner: string;
  description: string;
  l5_target: string;
  questions: Question[];
};

const LEVEL_COLORS: Record<number, string> = {
  1: "#dc2626", 2: "#ea580c", 3: "#d97706", 4: "#059669", 5: "#2563eb",
};

export default function MaturityQuiz() {
  const [dimensions, setDimensions] = useState<Dimension[]>([]);
  const [levels, setLevels] = useState<Record<number, { name: string; description: string }>>({});
  const [step, setStep] = useState(0); // 0 = intro, 1-7 = dimensions, 8 = submitting
  const [answers, setAnswers] = useState<Record<string, Record<string, number>>>({});
  const [orgName, setOrgName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/maturity/questions`)
      .then(r => r.json())
      .then(data => {
        setDimensions(data.dimensions);
        setLevels(data.levels);
        const init: Record<string, Record<string, number>> = {};
        for (const dim of data.dimensions) {
          init[dim.key] = {};
        }
        setAnswers(init);
      });
  }, []);

  const currentDim = step >= 1 && step <= dimensions.length ? dimensions[step - 1] : null;

  function selectAnswer(dimKey: string, questionId: string, score: number) {
    setAnswers(prev => ({
      ...prev,
      [dimKey]: { ...prev[dimKey], [questionId]: score },
    }));
  }

  function canAdvance(): boolean {
    if (step === 0) return true;
    if (!currentDim) return false;
    const dimAnswers = answers[currentDim.key] || {};
    return currentDim.questions.every(q => dimAnswers[q.id] !== undefined);
  }

  async function submit() {
    setSubmitting(true);
    setError("");
    const payload: Record<string, { question_id: string; selected_score: number }[]> = {};
    for (const dim of dimensions) {
      payload[dim.key] = Object.entries(answers[dim.key] || {}).map(([qid, score]) => ({
        question_id: qid,
        selected_score: score,
      }));
    }
    try {
      const res = await fetch(`${API_BASE}/maturity/assess`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ org_name: orgName || null, answers: payload }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }));
        setError(body.detail || "Assessment failed");
        setSubmitting(false);
        return;
      }
      const data = await res.json();
      window.location.href = `/maturity/${data.id}`;
    } catch (e: any) {
      setError(e.message || "Network error");
      setSubmitting(false);
    }
  }

  if (!dimensions.length) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-400">Loading assessment…</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div>
            <a href="/" className="text-sm text-gray-500 hover:text-gray-700">← Back to AAH</a>
            <h1 className="text-xl font-bold text-gray-900 mt-1">AgentMLOps Maturity Assessment</h1>
          </div>
          <div className="text-sm text-gray-500">
            {step === 0 ? "Introduction" : step <= dimensions.length ? `${step} of ${dimensions.length}` : "Review"}
          </div>
        </div>
      </header>

      {/* Progress bar */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-3xl mx-auto">
          <div className="h-1 bg-gray-100 rounded-full">
            <div
              className="h-1 bg-indigo-600 rounded-full transition-all duration-300"
              style={{ width: `${(step / (dimensions.length + 1)) * 100}%` }}
            />
          </div>
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-6 py-8">
        {/* Step 0: Intro */}
        {step === 0 && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
              <div className="text-4xl mb-4">📊</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-3">How mature is your Agent Operations?</h2>
              <p className="text-gray-600 max-w-lg mx-auto">
                Assess your organization across 7 critical AgentMLOps dimensions.
                Get a maturity score (L1–L5), a gap analysis, and a 90-day roadmap to production readiness.
              </p>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Organization name <span className="text-gray-400">(optional)</span>
              </label>
              <input
                type="text"
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm
                           focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Your company or team name"
                value={orgName}
                onChange={e => setOrgName(e.target.value)}
              />
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">7 Dimensions We&apos;ll Assess</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {dimensions.map((dim, i) => (
                  <div key={dim.key} className="flex items-start gap-3 rounded-lg border border-gray-100 p-3">
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold">
                      {i + 1}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-900">{dim.label}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{dim.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Steps 1-7: Dimension questions */}
        {currentDim && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-1">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 text-sm font-bold">
                  {step}
                </span>
                <h2 className="text-lg font-bold text-gray-900">{currentDim.label}</h2>
              </div>
              <p className="text-sm text-gray-500 ml-11">{currentDim.description}</p>
              <div className="ml-11 mt-1">
                <span className="text-xs text-emerald-600 font-medium">L5 target: {currentDim.l5_target}</span>
              </div>
            </div>

            {currentDim.questions.map((q, qi) => {
              const selected = answers[currentDim.key]?.[q.id];
              return (
                <div key={q.id} className="bg-white rounded-xl border border-gray-200 p-5">
                  <h3 className="text-sm font-semibold text-gray-800 mb-3">
                    {qi + 1}. {q.text}
                  </h3>
                  <div className="space-y-2">
                    {q.options.map(opt => (
                      <label
                        key={opt.score}
                        className={`flex items-center gap-3 rounded-lg border p-3 cursor-pointer transition
                          ${selected === opt.score
                            ? "border-indigo-400 bg-indigo-50"
                            : "border-gray-200 hover:bg-gray-50"}`}
                      >
                        <input
                          type="radio"
                          className="text-indigo-600 focus:ring-indigo-500"
                          name={q.id}
                          checked={selected === opt.score}
                          onChange={() => selectAnswer(currentDim.key, q.id, opt.score)}
                        />
                        <span className="text-sm text-gray-700 flex-1">{opt.label}</span>
                        <span
                          className="text-xs font-bold px-2 py-0.5 rounded-full"
                          style={{ backgroundColor: `${LEVEL_COLORS[opt.score]}15`, color: LEVEL_COLORS[opt.score] }}
                        >
                          L{opt.score}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Step 8: Review & Submit */}
        {step > dimensions.length && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6 text-center">
              <h2 className="text-xl font-bold text-gray-900 mb-2">Review &amp; Submit</h2>
              <p className="text-sm text-gray-500">All 7 dimensions answered. Ready to calculate your maturity score.</p>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Your Answers Summary</h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 text-gray-500 font-medium">Dimension</th>
                    <th className="text-center py-2 text-gray-500 font-medium">Avg Score</th>
                  </tr>
                </thead>
                <tbody>
                  {dimensions.map(dim => {
                    const dimAnswers = answers[dim.key] || {};
                    const scores = Object.values(dimAnswers);
                    const avg = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
                    const level = Math.max(1, Math.min(5, Math.round(avg)));
                    return (
                      <tr key={dim.key} className="border-b border-gray-100">
                        <td className="py-2 text-gray-800">{dim.label}</td>
                        <td className="py-2 text-center">
                          <span
                            className="text-xs font-bold px-2 py-0.5 rounded-full"
                            style={{ backgroundColor: `${LEVEL_COLORS[level]}15`, color: LEVEL_COLORS[level] }}
                          >
                            L{level} ({avg.toFixed(1)})
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <button
            className="rounded-lg border border-gray-300 bg-white px-5 py-2.5 text-sm font-medium
                       text-gray-700 hover:bg-gray-50 disabled:opacity-40 transition"
            onClick={() => setStep(s => Math.max(0, s - 1))}
            disabled={step === 0}
          >
            Back
          </button>

          {step <= dimensions.length ? (
            <button
              className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white
                         hover:bg-indigo-700 disabled:opacity-40 transition"
              onClick={() => setStep(s => s + 1)}
              disabled={!canAdvance()}
            >
              {step === 0 ? "Start Assessment" : step < dimensions.length ? "Next Dimension" : "Review Answers"}
            </button>
          ) : (
            <button
              className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white
                         hover:bg-indigo-700 disabled:opacity-40 transition"
              onClick={submit}
              disabled={submitting}
            >
              {submitting ? "Calculating…" : "Get My Maturity Score"}
            </button>
          )}
        </div>
      </main>
    </div>
  );
}
