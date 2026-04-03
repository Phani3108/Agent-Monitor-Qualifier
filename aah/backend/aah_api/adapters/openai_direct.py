from __future__ import annotations
import os, time, json
from typing import Any, Dict, List, Optional, Tuple
from .base import AgentAdapter, ToolCall


class OpenAIDirectAdapter:
    """Direct OpenAI API adapter — supports GPT-5, GPT-5 Mini, GPT-5 Nano.

    Uses the openai Python SDK (v1.x+).
    Env vars: OPENAI_API_KEY.
    """

    provider = "openai"

    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.model = cfg.get("model", "gpt-5")
        self.temperature = float(cfg.get("temperature", 0))
        self.pricing = cfg.get("pricing", {"input_per_1k": 0.0, "output_per_1k": 0.0})
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self._ready = False

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self._ready = True
            except Exception:
                pass

    def invoke(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[ToolCall], int, float]:
        t0 = time.perf_counter()
        if not self._ready:
            return "OpenAI adapter not configured (missing OPENAI_API_KEY).", [], 0, 0.0

        tools = context.get("tools") if context else None
        messages = [{"role": "user", "content": prompt}]
        kwargs: Dict[str, Any] = dict(
            model=self.model, temperature=self.temperature, messages=messages
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        resp = self.client.chat.completions.create(**kwargs)
        text = resp.choices[0].message.content or ""
        tool_calls: List[ToolCall] = []
        if resp.choices[0].message.tool_calls:
            for tc in resp.choices[0].message.tool_calls:
                args = tc.function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        pass
                tool_calls.append({"name": tc.function.name, "arguments": args})

        usage = getattr(resp, "usage", None)
        cost = 0.0
        if usage:
            in_k = (usage.prompt_tokens or 0) / 1000.0
            out_k = (usage.completion_tokens or 0) / 1000.0
            cost = in_k * float(self.pricing.get("input_per_1k", 0)) + out_k * float(self.pricing.get("output_per_1k", 0))

        latency_ms = int((time.perf_counter() - t0) * 1000)
        return text, tool_calls, latency_ms, cost
