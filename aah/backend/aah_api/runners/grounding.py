from __future__ import annotations
from typing import List, Dict, Any
from ..models.dto import TestSpec, TestResult, AssertionResult

from ..adapters.base import AgentAdapter
from ..services.connectors import get_passages
from ..utils.language import detect_lang

def _mentions_any(text: str, needles: List[str]) -> bool:
    lower = text.lower()
    for n in needles:
        n2 = str(n).strip().lower()
        if not n2: 
            continue
        if n2 in lower:
            return True
    return False

class GroundingRunner:
    name = "grounding"

    def __init__(self, adapter: AgentAdapter) -> None:
        self.agent = adapter

    def run(self, spec: TestSpec) -> List[TestResult]:
        out: List[TestResult] = []
        for t in spec.tests:
            # Only enforce on tests that specify grounded_to
            if not (t.expects and t.expects.model_dump().get("grounded_to")):
                continue
            sources = t.expects.model_dump().get("grounded_to") or []
            require_mention = bool(t.expects.model_dump().get("require_source_mentions"))
            passages = get_passages(sources)
            text, tool_calls, latency_ms, cost_usd = self.agent.invoke(t.prompt, t.context)

            asserts: List[AssertionResult] = []

            # (1) must not contradict sources: at least one phrase from the sources should appear
            has_quote = _mentions_any(text, passages)
            asserts.append(AssertionResult(type="quotes_from_sources", passed=has_quote, details={"num_passages": len(passages)}))

            # (2) if require_source_mentions, expect the source id mentions (e.g., "refund_policy_v1")
            if require_mention:
                mentions_id = _mentions_any(text, sources)
                asserts.append(AssertionResult(type="mentions_source_ids", passed=mentions_id, details={"expected_ids": sources}))

            # (3) record languages
            meta = {
                "prompt_lang": detect_lang(t.prompt or ""),
                "response_lang": detect_lang(text or ""),
                "sources": sources
            }
            passed = all(a.passed for a in asserts)
            out.append(TestResult(
                id=f"ground-{t.id}",
                pack=self.name,
                passed=passed,
                assertions=asserts,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                response_text=text,
                tool_calls=tool_calls,
                meta=meta
            ))
        return out
