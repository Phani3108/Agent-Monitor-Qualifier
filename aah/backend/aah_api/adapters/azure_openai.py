from __future__ import annotations
import os, time
from typing import Any, Dict, List, Optional, Tuple
from .base import AgentAdapter, ToolCall

_OPENAI_OK = True
try:
    from openai import AzureOpenAI
except Exception:
    _OPENAI_OK = False

class AzureOpenAIAdapter:
    provider = "azure_openai"

    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.cfg = cfg
        self.deployment = cfg.get("deployment") or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.api_version = cfg.get("api_version") or os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
        self.endpoint = cfg.get("endpoint") or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")

        if not all([self.deployment, self.endpoint, self.api_version, self.api_key]) or not _OPENAI_OK:
            self._ready = False
        else:
            self._ready = True
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint
            )

        self.temperature = float(cfg.get("temperature", 0))
        self.pricing = cfg.get("pricing", {"input_per_1k": 0.0, "output_per_1k": 0.0})

    def invoke(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, List[ToolCall], int, float]:
        t0 = time.perf_counter()
        if not self._ready:
            text = "Adapter not configured (Azure OpenAI). Falling back to mock."
            return text, [], int((time.perf_counter() - t0) * 1000), 0.0

        tools = context.get("tools") if context else None
        messages = [{"role": "user", "content": prompt}]
        kwargs: Dict[str, Any] = dict(
            model=self.deployment, temperature=self.temperature, messages=messages
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
                        import json
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

        return text, tool_calls, int((time.perf_counter() - t0) * 1000), cost
