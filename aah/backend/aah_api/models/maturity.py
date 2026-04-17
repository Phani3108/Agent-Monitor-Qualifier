from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MaturityOption(BaseModel):
    label: str
    score: int


class MaturityQuestion(BaseModel):
    id: str
    text: str
    options: List[MaturityOption]


class MaturityDimension(BaseModel):
    key: str
    label: str
    runner: str
    description: str
    l5_target: str
    questions: List[MaturityQuestion]


class MaturityQuestionsResponse(BaseModel):
    dimensions: List[MaturityDimension]
    levels: Dict[int, Dict[str, str]]


class AssessmentAnswer(BaseModel):
    question_id: str
    selected_score: int = Field(ge=1, le=5)


class AssessmentRequest(BaseModel):
    org_name: Optional[str] = None
    answers: Dict[str, List[AssessmentAnswer]]  # dimension_key -> answers


class DimensionScore(BaseModel):
    dimension: str
    label: str
    runner: str
    score: float
    level: int
    level_name: str


class MaturityGap(BaseModel):
    dimension: str
    label: str
    current_level: int
    current_name: str
    target_level: int
    gap_description: str
    aah_runner: str
    aah_action: str


class RoadmapItem(BaseModel):
    week_range: str
    dimension: str
    label: str
    action: str
    aah_feature: str
    priority: int


class MaturityAssessment(BaseModel):
    id: str
    org_name: Optional[str] = None
    dimension_scores: List[DimensionScore]
    overall_score: float
    overall_level: int
    overall_level_name: str
    gaps: List[MaturityGap]
    roadmap_90d: List[RoadmapItem]
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
