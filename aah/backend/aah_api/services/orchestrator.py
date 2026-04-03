from __future__ import annotations
import os, json, uuid, time
from pathlib import Path
from typing import Dict, Any, Optional

from ..models.dto import RunSummary, TestSpec
from ..runners.functional import FunctionalRunner
from ..runners.determinism import DeterminismRunner
from ..runners.safety import SafetyRunner
from ..runners.compliance import ComplianceRunner
from ..runners.tool_robustness import ToolRobustnessRunner
from ..runners.grounding import GroundingRunner
from ..runners.policy_lint import PolicyLintRunner
from ..services.scoring import (
    score_functional, score_safety, score_determinism,
    score_compliance, score_tool_robustness, combine,
)
from .agent_factory import build_adapter
from .tenant import load_tenant
from ..services.policy import load_policy_hash, load_schema_hash
from .certify import evaluate_certification
from .badge import render_badge_svg

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

ALL_PACKS = ["functional", "safety", "determinism", "compliance",
             "tool_robustness", "grounding", "policy_lint"]


def _save_results(run_dir: Path, pack: str, results: list) -> None:
    (run_dir / f"results.{pack}.json").write_text(
        json.dumps([r.model_dump() for r in results], indent=2), encoding="utf-8"
    )


def execute_run(spec: TestSpec, packs: Optional[list[str]] = None) -> RunSummary:

    run_id = str(uuid.uuid4())
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "spec.json").write_text(spec.model_dump_json(indent=2), encoding="utf-8")

    selected = packs or ALL_PACKS
    functional = []
    safety = []
    determinism = []
    compliance = []
    toolrob = []
    grounding = []
    policy_lint = []
    packs_executed = []

    # Build agent adapter and save agent_meta
    adapter, agent_meta = build_adapter(spec.agent, spec.environment)
    (run_dir / "agent_meta.json").write_text(json.dumps(agent_meta, indent=2), encoding="utf-8")

    if "functional" in selected:
        functional = FunctionalRunner(adapter).run(spec)
        _save_results(run_dir, "functional", functional)
        if functional:
            packs_executed.append("functional")

    if "safety" in selected:
        safety = SafetyRunner(adapter).run(spec)
        _save_results(run_dir, "safety", safety)
        if safety:
            packs_executed.append("safety")

    if "compliance" in selected:
        tenant_cfg = load_tenant(spec.tenant)
        compliance = ComplianceRunner(adapter, tenant_cfg).run(spec)
        _save_results(run_dir, "compliance", compliance)
        if compliance:
            packs_executed.append("compliance")

    if "tool_robustness" in selected:
        toolrob = ToolRobustnessRunner(adapter).run(spec)
        _save_results(run_dir, "tool_robustness", toolrob)
        if toolrob:
            packs_executed.append("tool_robustness")

    if "grounding" in selected:
        grounding = GroundingRunner(adapter).run(spec)
        _save_results(run_dir, "grounding", grounding)
        if grounding:
            packs_executed.append("grounding")

    if "policy_lint" in selected:
        policy_lint = PolicyLintRunner().run(spec, REPO_ROOT)
        _save_results(run_dir, "policy_lint", policy_lint)
        if policy_lint:
            packs_executed.append("policy_lint")

    if "determinism" in selected:
        determinism = DeterminismRunner(adapter, spec.agent, spec.environment).run(spec)
        _save_results(run_dir, "determinism", determinism)
        if determinism:
            packs_executed.append("determinism")

    all_results = functional + safety + determinism + compliance + toolrob + grounding + policy_lint
    totals_tests = len(all_results)
    totals_passed = sum(1 for r in all_results if r.passed)

    scores_map = {
        "functional": score_functional(functional) if functional else 0,
        "safety": score_safety(safety) if safety else 0,
        "determinism": score_determinism(determinism) if determinism else 0,
        "compliance": score_compliance(compliance) if compliance else 0,
        "tool_robustness": score_tool_robustness(toolrob) if toolrob else 0,
    }
    overall = combine({k: v for k, v in scores_map.items() if v is not None and k in packs_executed})

    cert = evaluate_certification(functional, safety, determinism, spec)

    summary = RunSummary(
        run_id=run_id,
        agent=spec.agent,
        environment=spec.environment,
        packs_executed=packs_executed,
        totals={"tests": totals_tests, "passed": totals_passed, "failed": totals_tests - totals_passed},
        pass_rate=round(100.0 * totals_passed / max(1, totals_tests), 2),
        partial=False,
        scores={"overall": overall, **scores_map},
        policy_hash=load_policy_hash(),
        spec_schema_hash=load_schema_hash(),
    )
    summary.artifacts["agent_meta"] = str(run_dir / "agent_meta.json")

    report_path = run_dir / "report.html"
    from .report import render_report
    render_report(report_path, summary.model_dump(), {
        "functional": functional,
        "safety": safety,
        "compliance": compliance,
        "tool_robustness": toolrob,
        "grounding": grounding,
        "policy_lint": policy_lint,
        "determinism": determinism,
    })
    summary.artifacts["report_html"] = str(report_path)

    badge_path = run_dir / "badge.svg"
    render_badge_svg(badge_path, summary.certified, summary.cert["version"], summary.scores["overall"])
    summary.artifacts["badge_svg"] = str(badge_path)

    # Build and save cryptographic manifest
    from .sign import build_manifest
    build_manifest(run_dir, force_dev_key=True)

    (run_dir / "summary.json").write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    return summary


def load_summary(run_id: str) -> RunSummary:
    path = RUNS_DIR / run_id / "summary.json"
    if not path.exists():
        raise FileNotFoundError("Run not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    return RunSummary.model_validate(data)
