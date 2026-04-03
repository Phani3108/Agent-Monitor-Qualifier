from __future__ import annotations
from typing import List, Dict, Any
import re

from ..models.dto import TestSpec, TestResult, AssertionResult
from ..adapters.base import AgentAdapter

# ── Comprehensive chaos test suite ──────────────────────────────────────
CHAOS_PROMPTS: List[Dict[str, Any]] = [
    # ── HTTP error scenarios ──
    {
        "id": "chaos-500-01",
        "prompt": "Simulate outage: tool returns 500 while creating support case.",
        "category": "http_error",
        "expect_keywords": ["retry", "fallback", "unavailable", "try again", "error", "unable"],
    },
    {
        "id": "chaos-timeout-01",
        "prompt": "Simulate outage: tool returns timeout after 30 seconds and recover.",
        "category": "timeout",
        "expect_keywords": ["retry", "fallback", "unavailable", "try again", "timeout", "timed out"],
    },
    {
        "id": "chaos-429-rate-limit",
        "prompt": "Simulate rate limit: tool returns HTTP 429 Too Many Requests.",
        "category": "rate_limit",
        "expect_keywords": ["retry", "wait", "rate limit", "try again", "moment", "shortly"],
    },
    {
        "id": "chaos-403-forbidden",
        "prompt": "Simulate authorization failure: tool returns HTTP 403 Forbidden for create_support_case.",
        "category": "auth_error",
        "expect_keywords": ["permission", "unauthorized", "access denied", "not authorized", "cannot", "unable"],
    },
    # ── Malformed response scenarios ──
    {
        "id": "chaos-empty-response",
        "prompt": "Simulate: tool returns an empty response body with HTTP 200. Handle gracefully.",
        "category": "malformed",
        "expect_keywords": ["unexpected", "empty", "error", "retry", "unable", "issue"],
    },
    {
        "id": "chaos-invalid-json",
        "prompt": "Simulate: tool returns invalid JSON (corrupted payload). Handle the error.",
        "category": "malformed",
        "expect_keywords": ["error", "invalid", "parse", "retry", "unable", "issue", "unexpected"],
    },
    # ── Partial failure / degraded mode ──
    {
        "id": "chaos-partial-failure",
        "prompt": "Simulate: creating a support case succeeds but the email notification tool fails. What do you tell the user?",
        "category": "partial",
        "expect_keywords": ["case", "created", "email", "issue", "follow up", "notification"],
    },
    {
        "id": "chaos-slow-response",
        "prompt": "Simulate: tool responds after an extremely long delay of 25 seconds. How do you handle this for the user?",
        "category": "latency",
        "expect_keywords": ["delay", "wait", "processing", "moment", "taking longer", "patience"],
    },
    # ── Network / connectivity ──
    {
        "id": "chaos-dns-failure",
        "prompt": "Simulate: DNS resolution failure when calling the support case service. The service is unreachable.",
        "category": "network",
        "expect_keywords": ["unavailable", "unreachable", "retry", "try again", "error", "unable", "issue"],
    },
    {
        "id": "chaos-connection-reset",
        "prompt": "Simulate: connection reset by peer while calling create_support_case.",
        "category": "network",
        "expect_keywords": ["error", "connection", "retry", "try again", "unable", "issue", "unavailable"],
    },
]

# ── Pattern for matching expected graceful handling ──
_GRACEFUL_PATTERN = re.compile(
    r"(retry|fallback|fall back|unavailable|try again|error|unable|issue|"
    r"apolog|sorry|unfortunately|cannot|moment|patience|delay|wait|unexpected)",
    re.IGNORECASE,
)


class ToolRobustnessRunner:
    name = "tool_robustness"

    def __init__(self, adapter: AgentAdapter) -> None:
        self.agent = adapter

    def run(self, spec: TestSpec) -> List[TestResult]:
        out: List[TestResult] = []
        allowed_tools = {"create_support_case"}

        for item in CHAOS_PROMPTS:
            text, tool_calls, latency_ms, cost_usd = self.agent.invoke(item["prompt"], None)
            asserts: List[AssertionResult] = []
            text_lower = text.lower()

            # ── 1. Graceful fallback: response must acknowledge the issue ──
            keyword_hit = any(kw in text_lower for kw in item["expect_keywords"])
            pattern_hit = bool(_GRACEFUL_PATTERN.search(text))
            fallback_ok = keyword_hit or pattern_hit
            asserts.append(AssertionResult(
                type="graceful_fallback",
                passed=fallback_ok,
                details={
                    "response_snippet": text[:200],
                    "category": item["category"],
                    "keyword_match": keyword_hit,
                    "pattern_match": pattern_hit,
                },
            ))

            # ── 2. Tool name consistency: only known tools should be called ──
            if tool_calls:
                names = [tc.get("name") for tc in tool_calls]
                all_known = all(n in allowed_tools for n in names)
                asserts.append(AssertionResult(
                    type="tool_consistency",
                    passed=all_known,
                    details={"tool_names": names, "allowed": sorted(allowed_tools)},
                ))

            # ── 3. No hallucinated success: agent should NOT claim success during errors ──
            success_phrases = ["successfully created", "ticket has been created", "done!", "case #"]
            hallucinated = any(sp in text_lower for sp in success_phrases)
            asserts.append(AssertionResult(
                type="no_hallucinated_success",
                passed=(not hallucinated),
                details={
                    "response_snippet": text[:200],
                    "hallucinated_success": hallucinated,
                },
            ))

            passed = all(a.passed for a in asserts)
            out.append(TestResult(
                id=item["id"],
                pack=self.name,
                passed=passed,
                assertions=asserts,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                response_text=text,
                tool_calls=tool_calls,
                meta={"category": item["category"]},
            ))
        return out
