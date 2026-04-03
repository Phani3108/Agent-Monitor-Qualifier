from __future__ import annotations
from typing import Any, Dict, List
import re
from ..models.dto import (
    TestSpec, TestResult, AssertionResult
)

from ..adapters.base import AgentAdapter
from ..tools.registry import list_tools

from ..utils.json_schema import validate_json
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from ..utils.diff import summarize_jsonschema_error, dict_key_diff




class FunctionalRunner:
    name = "functional"

    def __init__(self, adapter: AgentAdapter):
        self.agent = adapter

    def _assert_contains(self, text: str, needles: List[str]) -> List[AssertionResult]:
        results: List[AssertionResult] = []
        lower = text.lower()
        for n in needles:
            ok = n.lower() in lower
            results.append(AssertionResult(type="contains", passed=ok, details={"needle": n}))
        return results

    def _assert_not_contains(self, text: str, needles: List[str]) -> List[AssertionResult]:
        results: List[AssertionResult] = []
        lower = text.lower()
        for n in needles:
            ok = n.lower() not in lower
            results.append(AssertionResult(type="not_contains", passed=ok, details={"needle": n}))
        return results

    def _assert_blocked(self, text: str, expected: bool) -> List[AssertionResult]:
        blocked = "blocked" in text.lower()
        return [AssertionResult(type="blocked", passed=(blocked == expected), details={"observed_blocked": blocked})]

    def _assert_tool_calls(self, tool_calls: List[Dict[str, Any]], expects: List[Dict[str, Any]], strict: bool) -> List[AssertionResult]:
        from ..utils.schema_hints import property_hints, suggest_arg_fixes
        results: List[AssertionResult] = []
        for exp in expects:
            name = exp["name"]
            matched = [tc for tc in tool_calls if tc.get("name") == name]
            ok_name = len(matched) > 0
            results.append(AssertionResult(type="tool_called", passed=ok_name, details={"name": name, "found": ok_name}))
            if ok_name and exp.get("schema_ok"):
                tool_schema_map = {n: s["schema"] for n, s in list_tools().items()}
                schema = tool_schema_map.get(name)
                if schema is None:
                    results.append(AssertionResult(type="tool_schema_known", passed=False, details={"name": name}))
                else:
                    try:
                        validate_json(matched[0].get("arguments") or {}, schema)
                        results.append(AssertionResult(type="tool_schema_valid", passed=True, details={"name": name}))
                    except ValidationError as ve:
                        details = summarize_jsonschema_error(ve)
                        keydiff = dict_key_diff(matched[0].get("arguments") or {}, schema.get("properties") or {})
                        if keydiff["missing"] or keydiff["extra"]:
                            details["key_diff"] = keydiff
                        # add hints and auto-fix suggestions
                        hints = property_hints(schema)
                        proposed, notes = suggest_arg_fixes(matched[0].get("arguments") or {}, schema)
                        details["hints"] = hints
                        if notes:
                            details["suggested_fixes"] = notes
                            details["proposed_arguments"] = proposed
                        results.append(AssertionResult(type="tool_schema_valid", passed=False, details={"name": name, **details}))
                        if strict:
                            results.append(AssertionResult(type="tool_schema_strict_block", passed=False, details={"name": name}))
                    except Exception as e:
                        results.append(AssertionResult(type="tool_schema_valid", passed=False, details={"name": name, "error": str(e)}))
                        if strict:
                            results.append(AssertionResult(type="tool_schema_strict_block", passed=False, details={"name": name}))
        return results

    def run(self, spec: TestSpec) -> List[TestResult]:
        results: List[TestResult] = []
        strict = bool(spec.policies and spec.policies.tool_schema_strict)
        tools = [{"type": "function", "function": {"name": n, "parameters": s["schema"]}} for n, s in list_tools().items()]
        for t in spec.tests:
            context = dict(t.context or {})
            context["tools"] = tools
            text, tool_calls, latency_ms, cost_usd = self.agent.invoke(t.prompt, context)
            assertions: List[AssertionResult] = []

            if t.expects.contains:
                assertions += self._assert_contains(text, t.expects.contains)
            if t.expects.not_contains:
                assertions += self._assert_not_contains(text, t.expects.not_contains)
            if t.expects.blocked is not None:
                assertions += self._assert_blocked(text, t.expects.blocked)
            if t.expects.tool_calls:
                expects_tc = [e.model_dump() for e in t.expects.tool_calls]
                assertions += self._assert_tool_calls(tool_calls, expects_tc, strict)

            passed = all(a.passed for a in assertions) if assertions else True
            results.append(TestResult(
                id=t.id,
                pack=self.name,
                passed=passed,
                assertions=assertions,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                response_text=text,
                tool_calls=tool_calls
            ))
        return results
