#!/usr/bin/env python3
from __future__ import annotations
import re, json, sys
from pathlib import Path
from typing import List, Dict, Any
import yaml

# Optional heavy deps are imported only when running this script
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC_CFG = ROOT / "connectors" / "sources.yaml"
OUT_DIR = ROOT / "connectors" / "index"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def read_files(globs: List[str]) -> List[tuple[str,str]]:
    items = []
    for g in globs:
        for p in ROOT.glob(g):
            if p.is_file():
                items.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
    return items

def clean_text(t: str) -> str:
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def chunk(md: str, max_chars: int = 600) -> List[str]:
    paras = [p.strip() for p in re.split(r"\n{2,}", md) if p.strip()]
    out, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 1 <= max_chars:
            cur = (cur + "\n" + p).strip()
        else:
            if cur: out.append(cur)
            cur = p
    if cur: out.append(cur)
    return out

def load_sources() -> List[Dict[str, Any]]:
    cfg = yaml.safe_load(SRC_CFG.read_text(encoding="utf-8")) or {}
    return cfg.get("sources") or []

def build():
    sources = load_sources()
    docs: List[Dict[str, Any]] = []
    chunks: List[str] = []
    meta: List[Dict[str, Any]] = []
    for src in sources:
        sid = src["id"]; stype = src["type"]
        if stype == "file_glob":
            files = read_files(src.get("paths") or [])
            for fpath, raw in files:
                for i, ch in enumerate(chunk(raw)):
                    text = clean_text(ch)
                    if not text: continue
                    meta.append({"source_id": sid, "title": src.get("title") or sid, "file": str(Path(fpath).relative_to(ROOT)), "chunk": i})
                    chunks.append(text)
        else:
            # Stubs: skip at index time
            continue

    if not chunks:
        raise SystemExit("No local chunks found. Add files under connectors/docs/** or update sources.yaml.")

    vec = TfidfVectorizer(ngram_range=(1,2), max_features=50000)
    X = vec.fit_transform(chunks)

    # persist
    (OUT_DIR / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    joblib.dump(vec, OUT_DIR / "vectorizer.joblib")
    from scipy import sparse
    sparse.save_npz(OUT_DIR / "tfidf.npz", X)
    print(f"Indexed {len(chunks)} chunks from {len(set(m['source_id'] for m in meta))} sources.")

if __name__ == "__main__":
    build()
