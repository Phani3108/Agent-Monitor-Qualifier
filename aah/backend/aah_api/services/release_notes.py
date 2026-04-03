from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
from .compare import compare_runs
from .orchestrator import RUNS_DIR

def generate_release_notes(base: str, head: str) -> str:
    diff = compare_runs(base, head)
    lines = []
    lines.append(f"# Release Notes — {head}")
    lines.append("")
    lines.append(f"Compared to {base}")
    lines.append("")
    lines.append(f"**Scores**: overall Δ {diff['score_delta']['overall']}, functional Δ {diff['score_delta']['functional']}, safety Δ {diff['score_delta']['safety']}, determinism Δ {diff['score_delta']['determinism']}")
    lines.append("")
    if diff["regressions"]:
        lines.append("## Regressions")
        for r in diff["regressions"]:
            lines.append(f"- {r['test']}: {r['from']} → {r['to']} (new failing assertions: {', '.join(r['new_failures'])})")
    else:
        lines.append("## Regressions\n- None")
    if diff["improvements"]:
        lines.append("\n## Improvements")
        for r in diff["improvements"]:
            lines.append(f"- {r['test']}: {r['from']} → {r['to']}")
    else:
        lines.append("\n## Improvements\n- None")
    return "\n".join(lines)

def save_release_notes(head: str, md: str) -> str:
    path = RUNS_DIR / head / "release-notes.md"
    path.write_text(md, encoding="utf-8")
    return str(path)
