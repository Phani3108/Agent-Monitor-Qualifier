from __future__ import annotations
from pathlib import Path
from typing import List
from ..models.dto import TestSpec, TestResult, AssertionResult
from ..services.lint_prompt import lint_prompt

class PolicyLintRunner:
    name = "policy_lint"

    def __init__(self) -> None:
        # no agent adapter needed
        pass

    def run(self, spec: TestSpec, repo_root: Path) -> List[TestResult]:
        checks = lint_prompt(spec.agent, repo_root)
        assertions = [AssertionResult(type=c["type"], passed=bool(c["passed"]), details=c.get("details") or {}) for c in checks]
        passed = all(a.passed for a in assertions)
        return [TestResult(
            id="policy-lint-01",
            pack=self.name,
            passed=passed,
            assertions=assertions,
            latency_ms=0,
            cost_usd=0.0,
            response_text="Agent prompt lint",
            tool_calls=[],
            meta={}
        )]
