from __future__ import annotations
import hmac, hashlib, os, json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
DEV_KEY_PATH = REPO_ROOT / ".aah" / "dev_signing.key"
DEV_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)

def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _hmac_sha256_file(p: Path, key: bytes) -> str:
    hm = hmac.new(key, digestmod=hashlib.sha256)
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hm.update(chunk)
    return hm.hexdigest()

def _load_key(force_dev_key: bool=False) -> tuple[bytes, str]:
    env = os.getenv("AAH_SIGNING_KEY", "").strip()
    if env:
        return env.encode("utf-8"), "env"
    if force_dev_key or DEV_KEY_PATH.exists():
        if not DEV_KEY_PATH.exists():
            DEV_KEY_PATH.write_text(os.urandom(32).hex(), encoding="utf-8")
        return DEV_KEY_PATH.read_text(encoding="utf-8").encode("utf-8"), "dev"
    return b"", "none"

def build_manifest(run_dir: Path, force_dev_key: bool=False) -> Dict[str, Any]:
    key, source = _load_key(force_dev_key)
    artifacts: List[Path] = []
    for p in run_dir.iterdir():
        if p.is_file() and (p.suffix in (".json",".html",".svg") or p.name.startswith("results.")):
            artifacts.append(p)

    items = []
    for p in sorted(artifacts):
        entry = {"file": p.name, "sha256": _sha256_file(p)}
        if key:
            entry["hmac_sha256"] = _hmac_sha256_file(p, key)
        items.append(entry)

    manifest = {
        "manifest_version": "aah.manifest.v1",
        "run_id": run_dir.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "signing": {"mode": source, "algo": "sha256" + (" + hmac-sha256" if key else "")},
        "artifacts": items
    }
    out = run_dir / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest

def verify_manifest(run_dir: Path, require_hmac: bool=False) -> Dict[str, Any]:
    """Recompute hashes for all artifacts listed in manifest.json."""
    man_path = run_dir / "manifest.json"
    if not man_path.exists():
        raise FileNotFoundError("manifest.json not found")
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    key, _ = _load_key(False)  # do not auto-create here

    results: List[Dict[str, Any]] = []
    all_ok = True
    hmac_used = False
    for it in manifest.get("artifacts", []):
        fname = it.get("file")
        p = run_dir / fname
        sha_expected = it.get("sha256")
        hmac_expected = it.get("hmac_sha256")
        sha_ok = p.exists() and (_sha256_file(p) == sha_expected)
        hmac_ok = None
        if hmac_expected is not None:
            hmac_used = True
            hmac_ok = (key != b"") and (_hmac_sha256_file(p, key) == hmac_expected)
        if require_hmac and not (hmac_expected and hmac_ok):
            all_ok = False
        if not sha_ok:
            all_ok = False
        if hmac_ok is False:
            all_ok = False
        results.append({
            "file": fname, "sha_ok": bool(sha_ok),
            "hmac_present": hmac_expected is not None,
            "hmac_ok": (None if hmac_ok is None else bool(hmac_ok))
        })
    return {
        "ok": bool(all_ok),
        "require_hmac": bool(require_hmac),
        "hmac_in_manifest": bool(hmac_used),
        "items": results
    }
