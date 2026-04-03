from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, List, Tuple

REQUIRED_SECTIONS = [
    "Role", "Policies", "Tooling", "IO Contract", "Temperature Schedule", "Refusals"
]

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",             # API-like keys
    r"(?i)password\s*[:=]\s*\S+",       # password=...
    r"(?i)secret\s*[:=]\s*\S+",
    r"(?i)token\s*[:=]\s*\S+",
]

def load_prompt(agent: str, repo_root: Path) -> Tuple[Path, str]:
    path = repo_root / f"agents/{agent}/prompt.md"
    if not path.exists():
        return path, ""
    return path, path.read_text(encoding="utf-8")

def _has_section(md: str, name: str) -> bool:
    # Accept "# Name" or "## Name" etc.
    return re.search(rf"^\s*#+\s*{re.escape(name)}\s*$", md, flags=re.IGNORECASE | re.MULTILINE) is not None

def _contains(md: str, needle: str) -> bool:
    return needle.lower() in md.lower()

def _no_secrets(md: str) -> bool:
    for pat in SECRET_PATTERNS:
        if re.search(pat, md):
            return False
    return True

def lint_prompt(agent: str, repo_root: Path) -> List[Dict[str, object]]:
    path, md = load_prompt(agent, repo_root)
    checks: List[Dict[str, object]] = []
    if not md:
        checks.append({"type": "prompt_exists", "passed": False, "details": {"path": str(path)}})
        return checks

    checks.append({"type": "prompt_exists", "passed": True, "details": {"path": str(path)}})

    for sec in REQUIRED_SECTIONS:
        checks.append({"type": f"section_{sec.replace(' ','_').lower()}", "passed": _has_section(md, sec), "details": {"section": sec}})

    # IO Contract: presence of keywords we require for refunds
    checks.append({"type": "io_contains_raise_ticket", "passed": _contains(md, "raise_ticket"), "details": {}})
    checks.append({"type": "io_contains_timeline_7days", "passed": _contains(md, "timeline<=7 days"), "details": {}})

    # Tooling mentions primary tool
    checks.append({"type": "tooling_mentions_create_support_case", "passed": _contains(md, "create_support_case"), "details": {}})

    # Temp schedule includes temp 0 for structured steps
    temp_ok = ("temp 0" in md.lower()) or ("temperature≈0" in md.lower()) or ("temperature ~0" in md.lower())
    checks.append({"type": "temperature_schedule_low_for_tools", "passed": temp_ok, "details": {}})

    # Refusals phrase
    checks.append({"type": "refusals_phrase_present", "passed": _contains(md, "Request blocked per policy."), "details": {}})

    # Secrets
    checks.append({"type": "no_secrets_in_prompt", "passed": _no_secrets(md), "details": {}})

    return checks
