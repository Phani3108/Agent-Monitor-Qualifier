import { useState, useEffect } from "react";

export default function VerifyRun({ runId }: { runId: string }) {
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const verify = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/runs/${runId}/verify`);
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    verify();
    // eslint-disable-next-line
  }, [runId]);

  if (loading) return <div>Verifying artifacts...</div>;
  if (error) return <div style={{color:'red'}}>Error: {error}</div>;
  if (!result) return null;

  return (
    <div>
      <h3>Artifact Verification</h3>
      <div>Status: {result.ok ? <b style={{color:'green'}}>OK</b> : <b style={{color:'red'}}>FAILED</b>}</div>
      <ul>
        {result.items.map((item: any) => (
          <li key={item.file}>
            {item.file}: sha_ok={String(item.sha_ok)} hmac_ok={String(item.hmac_ok)}
          </li>
        ))}
      </ul>
    </div>
  );
}
