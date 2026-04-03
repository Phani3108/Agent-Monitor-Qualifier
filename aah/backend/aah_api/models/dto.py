from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ExpectToolCall(BaseModel):
    name: str
    schema_ok: Optional[bool] = None

class TestExpectations(BaseModel):
    contains: Optional[List[str]] = None
    not_contains: Optional[List[str]] = None
    blocked: Optional[bool] = None
    tool_calls: Optional[List[ExpectToolCall]] = None
    grounded_to: Optional[List[str]] = None
    require_source_mentions: Optional[bool] = None

class TestCase(BaseModel):
    id: str
    prompt: str
    context: Optional[Dict[str, Any]] = None
    expects: TestExpectations

class SpecBudgets(BaseModel):
    max_latency_ms: Optional[int] = None
    max_cost_usd: Optional[float] = None

class SpecPolicies(BaseModel):
    pii_leakage: Optional[str] = Field(default=None)
    tool_schema_strict: Optional[bool] = Field(default=None)

class DeterminismConfig(BaseModel):
    samples: Optional[int] = None
    concurrency: Optional[int] = None
    thresholds: Optional[Dict[str, Any]] = None

class TestSpec(BaseModel):
    agent: str
    environment: str
    tenant: Optional[str] = None
    policies: Optional[SpecPolicies] = None
    budgets: Optional[SpecBudgets] = None
    determinism: Optional[DeterminismConfig] = None
    tests: List[TestCase]

class AssertionResult(BaseModel):
    type: str
    passed: bool
    details: Dict[str, Any] = Field(default_factory=dict)

class TestResult(BaseModel):
    id: str
    pack: str
    passed: bool
    assertions: List[AssertionResult]
    latency_ms: int
    cost_usd: float
    response_text: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


# Certification status for a run
class CertStatus(BaseModel):
    certified: bool
    version: str
    reasons: List[str]
    thresholds: Dict[str, Any]

class RunSummary(BaseModel):
    run_id: str
    agent: str
    environment: str
    packs_executed: List[str]
    totals: Dict[str, int]
    pass_rate: float
    partial: bool
    scores: Dict[str, Any]
    policy_hash: str
    spec_schema_hash: str
    artifacts: Dict[str, str] = Field(default_factory=dict)
    certified: bool = False
    cert: CertStatus | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: list[str] = Field(default_factory=list)
