from __future__ import annotations

import json
import math
import uuid
from pathlib import Path
from typing import Any, Dict, List

import yaml

from ..models.maturity import (
    AssessmentAnswer,
    AssessmentRequest,
    DimensionScore,
    MaturityAssessment,
    MaturityDimension,
    MaturityGap,
    MaturityOption,
    MaturityQuestion,
    MaturityQuestionsResponse,
    RoadmapItem,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
QUESTIONS_PATH = DATA_DIR / "maturity_questions.yaml"

REPO_ROOT = Path(__file__).resolve().parents[3]
ASSESSMENTS_DIR = REPO_ROOT / "maturity_assessments"

_questions_cache: dict[str, Any] | None = None

# ── AAH feature mapping per dimension ────────────────────────────────────
AAH_ACTIONS: Dict[str, Dict[str, str]] = {
    "versioning": {
        "gap": "No automated prompt versioning or change tracking",
        "action": "Enable PolicyLintRunner to validate agent configs on every PR",
        "feature": "PolicyLint runner — static analysis of agent prompt definitions with schema validation",
    },
    "canary_rollback": {
        "gap": "No staged rollout or automated regression gates",
        "action": "Run FunctionalRunner packs as canary gates before promotion",
        "feature": "Functional runner — golden-path assertions and tool schema validation",
    },
    "drift_detection": {
        "gap": "No output stability monitoring or drift alerting",
        "action": "Schedule DeterminismRunner with N-sample checks and budget thresholds",
        "feature": "Determinism runner — N-sample stability, p50/p95/p99 latency, cost budgets",
    },
    "eval_pipelines": {
        "gap": "No automated evaluation grounded to source-of-truth documents",
        "action": "Add GroundingRunner to CI with connector-backed source verification",
        "feature": "Grounding runner — TF-IDF passage matching against source-of-truth connectors",
    },
    "cost_attribution": {
        "gap": "No per-tenant cost tracking or budget enforcement",
        "action": "Configure ComplianceRunner with tenant-specific cost budgets",
        "feature": "Compliance runner — PCI compliance, PII masking, tool allowlists, cost budgets",
    },
    "policy_enforcement": {
        "gap": "No automated adversarial testing or PII leak detection",
        "action": "Enable SafetyRunner adversarial packs with zero-tolerance gates",
        "feature": "Safety runner — 13+ adversarial tests, PII traps, injection defense",
    },
    "incident_runbooks": {
        "gap": "No chaos testing or automated incident response",
        "action": "Run ToolRobustnessRunner chaos scenarios and wire incident creation",
        "feature": "Tool Robustness runner — 10 chaos scenarios (500s, timeouts, rate limits)",
    },
}

LEVEL_NAMES: Dict[int, str] = {
    1: "Ad-hoc",
    2: "Repeatable",
    3: "Defined",
    4: "Managed",
    5: "Optimized",
}


def _load_questions() -> dict[str, Any]:
    global _questions_cache
    if _questions_cache is None:
        with QUESTIONS_PATH.open("r", encoding="utf-8") as f:
            _questions_cache = yaml.safe_load(f)
    return _questions_cache


def get_questions() -> MaturityQuestionsResponse:
    raw = _load_questions()
    dimensions: List[MaturityDimension] = []
    for key, dim in raw["dimensions"].items():
        questions = [
            MaturityQuestion(
                id=q["id"],
                text=q["text"],
                options=[MaturityOption(**o) for o in q["options"]],
            )
            for q in dim["questions"]
        ]
        dimensions.append(
            MaturityDimension(
                key=key,
                label=dim["label"],
                runner=dim["runner"],
                description=dim["description"],
                l5_target=dim["l5_target"],
                questions=questions,
            )
        )
    levels = {
        int(k): {"name": v["name"], "description": v["description"]}
        for k, v in raw["levels"].items()
    }
    return MaturityQuestionsResponse(dimensions=dimensions, levels=levels)


def _score_dimension(answers: List[AssessmentAnswer]) -> float:
    if not answers:
        return 1.0
    return sum(a.selected_score for a in answers) / len(answers)


def _level_from_score(score: float) -> int:
    return max(1, min(5, round(score)))


def assess(req: AssessmentRequest) -> MaturityAssessment:
    raw = _load_questions()
    dimension_scores: List[DimensionScore] = []
    gaps: List[MaturityGap] = []

    for key, dim in raw["dimensions"].items():
        answers = req.answers.get(key, [])
        score = _score_dimension(answers)
        level = _level_from_score(score)
        level_name = LEVEL_NAMES[level]

        dimension_scores.append(
            DimensionScore(
                dimension=key,
                label=dim["label"],
                runner=dim["runner"],
                score=round(score, 2),
                level=level,
                level_name=level_name,
            )
        )

        if level <= 3:
            mapping = AAH_ACTIONS[key]
            gaps.append(
                MaturityGap(
                    dimension=key,
                    label=dim["label"],
                    current_level=level,
                    current_name=level_name,
                    target_level=5,
                    gap_description=mapping["gap"],
                    aah_runner=dim["runner"],
                    aah_action=mapping["action"],
                )
            )

    total = sum(ds.score for ds in dimension_scores)
    overall = round(total / len(dimension_scores), 2) if dimension_scores else 1.0
    overall_level = _level_from_score(overall)

    roadmap = _build_roadmap(gaps)

    assessment_id = uuid.uuid4().hex[:12]
    result = MaturityAssessment(
        id=assessment_id,
        org_name=req.org_name,
        dimension_scores=dimension_scores,
        overall_score=overall,
        overall_level=overall_level,
        overall_level_name=LEVEL_NAMES[overall_level],
        gaps=gaps,
        roadmap_90d=roadmap,
    )

    _save_assessment(result)
    return result


def _build_roadmap(gaps: List[MaturityGap]) -> List[RoadmapItem]:
    if not gaps:
        return []

    sorted_gaps = sorted(gaps, key=lambda g: g.current_level)
    items: List[RoadmapItem] = []
    weeks_per_gap = max(1, 12 // len(sorted_gaps))

    for i, gap in enumerate(sorted_gaps):
        start_week = i * weeks_per_gap + 1
        end_week = min(start_week + weeks_per_gap - 1, 12)
        mapping = AAH_ACTIONS[gap.dimension]

        items.append(
            RoadmapItem(
                week_range=f"Week {start_week}-{end_week}",
                dimension=gap.dimension,
                label=gap.label,
                action=mapping["action"],
                aah_feature=mapping["feature"],
                priority=5 - gap.current_level,
            )
        )

    return items


def _save_assessment(result: MaturityAssessment) -> None:
    ASSESSMENTS_DIR.mkdir(parents=True, exist_ok=True)
    path = ASSESSMENTS_DIR / f"{result.id}.json"
    path.write_text(result.model_dump_json(indent=2), encoding="utf-8")


def load_assessment(assessment_id: str) -> MaturityAssessment:
    path = ASSESSMENTS_DIR / f"{assessment_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Assessment {assessment_id} not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    return MaturityAssessment.model_validate(data)
