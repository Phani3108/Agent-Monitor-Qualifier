import { useState, useEffect } from "react";
import { API_BASE } from "../../lib/api";
import { fetchAuth } from "../../lib/auth";

export default function TagEditor({ runId, initialTags }: { runId: string, initialTags: string[] }) {
  const [tags, setTags] = useState<string[]>(initialTags || []);

  async function addTag(t: string) {
    const r = await fetchAuth(`${API_BASE}/runs/${runId}/tags?tag=${encodeURIComponent(t)}`, { method: "POST" });
    const j = await r.json(); setTags(j.tags);
  }
  async function delTag(t: string) {
    const r = await fetchAuth(`${API_BASE}/runs/${runId}/tags/${encodeURIComponent(t)}`, { method: "DELETE" });
    const j = await r.json(); setTags(j.tags);
  }

  return (
    <div className="card">
      <div><strong>Tags</strong></div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 6 }}>
        {tags.map(t => <span key={t} className="badge" onClick={() => delTag(t)} title="remove">{t} ✕</span>)}
        <input placeholder="add tag…" onKeyDown={e => { if (e.key === "Enter") { addTag((e.target as any).value); (e.target as any).value = ""; } }} />
      </div>
    </div>
  );
}
