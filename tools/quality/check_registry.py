#!/usr/bin/env python3
from pathlib import Path
import yaml, re, sys
root = Path(__file__).resolve().parents[2]
idx = root / "specs" / "registry" / "index.yaml"
if not idx.exists():
    print("No registry/index.yaml; skipping."); sys.exit(0)
data = yaml.safe_load(idx.read_text(encoding="utf-8")) or {}
packs = data.get("packs") or {}
semver = re.compile(r"^\d+\.\d+\.\d+$")
errors = []
for name, entries in packs.items():
    seen = set()
    for e in entries or []:
        v = e.get("version")
        f = e.get("file")
        if not v or not f: errors.append(f"{name}: missing version/file entry")
        if v in seen: errors.append(f"{name}: duplicate version {v}")
        seen.add(v)
        if not semver.match(v): errors.append(f"{name}: non-semver {v}")
        p = idx.parent / f
        if not p.exists(): errors.append(f"{name}: missing file {f}")
print("OK: registry") if not errors else (print("FAIL:\n - " + "\n - ".join(errors)) or sys.exit(1))
