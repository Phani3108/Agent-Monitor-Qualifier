from __future__ import annotations
from typing import Sequence, Dict, Any, List
import math

def percentiles(values: Sequence[float], ps=(50,95,99)) -> Dict[str, float]:
    if not values: return {f"p{p}": 0.0 for p in ps}
    xs = sorted(values)
    out = {}
    for p in ps:
        k = (p/100)*(len(xs)-1)
        f = math.floor(k); c = math.ceil(k)
        if f == c: out[f"p{p}"] = float(xs[int(k)])
        else: out[f"p{p}"] = float(xs[f] + (xs[c]-xs[f])*(k-f))
    return out

def mean(values: Sequence[float]) -> float:
    return float(sum(values)/len(values)) if values else 0.0

def stdev(values: Sequence[float]) -> float:
    n = len(values)
    if n < 2: return 0.0
    m = mean(values)
    var = sum((v-m)*(v-m) for v in values)/(n-1)
    return math.sqrt(var)

def coeff_variation(values: Sequence[float]) -> float:
    m = mean(values)
    return (stdev(values)/m) if (m > 0 and len(values) >= 2) else 0.0

def mode_ratio(signatures: Sequence[str]) -> float:
    if not signatures: return 0.0
    from collections import Counter
    m = Counter(signatures).most_common(1)[0][1]
    return (100.0 * m) / len(signatures)

def mini_signature(text: str) -> str:
    """Stable signature: lowercase, collapse spaces, scrub digits."""
    import re
    t = (text or "").lower()
    t = re.sub(r"\d+", "<num>", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:200]  # keep small
