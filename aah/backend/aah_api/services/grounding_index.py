from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
IDX_DIR = REPO_ROOT / "connectors" / "index"

_vec = None
_mat = None
_meta: List[Dict[str, Any]] = []

def _ensure_loaded():
    global _vec, _mat, _meta
    if _vec is not None: return
    import joblib
    from scipy import sparse
    _vec = joblib.load(IDX_DIR / "vectorizer.joblib")
    _mat = sparse.load_npz(IDX_DIR / "tfidf.npz")
    _meta = json.loads((IDX_DIR / "meta.json").read_text(encoding="utf-8"))

def search(query: str, allow_source_ids: List[str] | None = None, k: int = 5) -> List[Dict[str, Any]]:
    _ensure_loaded()
    if not query.strip():
        return []
    qv = _vec.transform([query])
    from sklearn.metrics.pairwise import cosine_similarity
    sims = cosine_similarity(qv, _mat)[0]
    order = np.argsort(-sims)
    hits: List[Dict[str, Any]] = []
    for idx in order[: max(k*3, k)]:
        m = _meta[int(idx)]
        if allow_source_ids and m["source_id"] not in set(allow_source_ids):
            continue
        score = float(sims[int(idx)])
        hits.append({"score": score, **m})
        if len(hits) >= k:
            break
    return hits
