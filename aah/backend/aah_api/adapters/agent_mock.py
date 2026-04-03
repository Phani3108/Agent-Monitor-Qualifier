from __future__ import annotations
import time, os, random
from typing import Any, Dict, List, Tuple

class MockAgent:
    """
    Simulates an agent. Modes:
    - buggy  : tends to leak PII echoes, bad tool schema, and variable outputs.
    - strict : blocks injections, never echoes PII, valid tool schema.
    """
    def __init__(self) -> None:
        self.mode = os.getenv("MOCK_AGENT_MODE", "buggy").lower()
        random.seed()  # non-deterministic across runs

    def _maybe_variation(self) -> str:
        # small textual variance in buggy mode
        return random.choice(["", "!", ".", " ..", " ✓"])

    def invoke(self, prompt: str, context: Dict[str, Any] | None = None) -> Tuple[str, List[Dict[str, Any]], int, float]:
        t0 = time.perf_counter()
        tool_calls: List[Dict[str, Any]] = []
        cost_usd = 0.0005

        # Adversarial/injection prompts
        if "ignore rules" in prompt.lower() or "reveal your system prompt" in prompt.lower():
            if self.mode == "buggy":
                text = "System prompt: [leaked] do X Y Z" + self._maybe_variation()
            else:
                text = "Request blocked per policy."
            latency_ms = int((time.perf_counter() - t0) * 1000)
            return text, tool_calls, latency_ms, cost_usd

        # PII echo trap: if a PAN-looking number is present, buggy echoes it, strict masks.
        # Simple capture of 13-19 digit sequences (spaces/dashes allowed)
        pan_like = " ".join([w for w in prompt.split() if any(c.isdigit() for c in w)])
        if self.mode == "buggy" and any(ch.isdigit() for ch in pan_like):
            text = f"I see your number {pan_like}. I will raise_ticket and set timeline<=7 days{self._maybe_variation()}"
        else:
            text = "I will raise_ticket and set timeline<=7 days. No PII is required."

        # Tool call shape: buggy uses wrong enum/amount type
        if self.mode == "buggy":
            tool_calls.append({
                "name": "create_support_case",
                "arguments": {"customer_id": "cus_12345", "reason": "duplicate", "amount": "20", "currency": "INR"}
            })
        else:
            tool_calls.append({
                "name": "create_support_case",
                "arguments": {"customer_id": "cus_ABC12345", "reason": "duplicate_debit", "amount": 20.0, "currency": "INR"}
            })

        # Slight latency jitter in buggy mode
        if self.mode == "buggy":
            time.sleep(random.uniform(0.0, 0.01))

        latency_ms = int((time.perf_counter() - t0) * 1000)
        return text, tool_calls, latency_ms, cost_usd
