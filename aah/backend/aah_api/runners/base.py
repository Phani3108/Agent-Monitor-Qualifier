from __future__ import annotations
from typing import List
from ..models.dto import TestSpec, TestResult

class Runner:
    name: str = "base"
    def run(self, spec: TestSpec) -> List[TestResult]:
        raise RuntimeError("Runner must implement run()")
