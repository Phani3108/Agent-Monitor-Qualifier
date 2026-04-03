from __future__ import annotations
import os, time, json
from typing import Any, Dict, List, Optional, Tuple
from .base import AgentAdapter, ToolCall


class AnthropicAdapter:
    """Anthropic Claude adapter — supports Claude 4.6 Opus, Claude 4.6 Sonnet, Claude 3 Haiku.

    Uses the anthropic Python SDK.
    Env vars: ANTHROPIC_API_KEY.
    """

    provider = "anthropic"

    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.model = cfg.get("model", "claude-sonnet-4-20250514")
        self.temperature = float(cfg.get("temperature", 0))
        self.max_tokens = int(cfg.get("max_tokens", 4096))
        self.pricing = cfg.get("pricing", {"input_per_1k": 0.0, "output_per_1k": 0.0})
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self._ready = False

        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self._ready = True
            except Exception:
                pass

    def invoke(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[ToolCall], int, float]:
        t0 = time.perf_counter()
        if not self._ready:
            return "Anthropic adapter not configured (missing ANTHROPIC_API_KEY).", [], 0, 0.0

        tools_raw = context.get("tools") if context else None
        messages = [{"role": "user", "content": prompt}]

        kwargs: Dict[str, Any] = dict(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=messages,
        )
        if self.temperature > 0:
            kwargs["temperature"] = self.temperature

        # Convert OpenAI-format tools to Anthropic format
        if tools_raw:
            anthropic_tools = []
            for t in tools_raw:
                fn = t.get("function", {})
                anthropic_tools.append({
                    "name": fn.get("name", ""),
                    "description": fn.get("description", ""),
                    "input_schema": fn.get("parameters", {}),
                })
            kwargs["tools"] = anthropic_tools

        resp = self.client.messages.create(**kwargs)

        text_parts: List[str] = []
        tool_calls: List[ToolCall] = []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "name": block.name,
                    "arguments": block.input if isinstance(block.input, dict) else {},
                })

        text = " ".join(text_parts)
        usage = getattr(resp, "usage", None)
        cost = 0.0
        if usage:
            in_k = (usage.input_tokens or 0) / 1000.0
            out_k = (usage.output_tokens or 0) / 1000.0
            cost = in_k * float(self.pricing.get("input_per_1k", 0)) + out_k * float(self.pricing.get("output_per_1k", 0))

        latency_ms = int((time.perf_counter() - t0) * 1000)
        return text, tool_calls, latency_ms, cost
