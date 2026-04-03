from __future__ import annotations
import os, time, json
from typing import Any, Dict, List, Optional, Tuple
from .base import AgentAdapter, ToolCall


class GeminiAdapter:
    """Google Gemini adapter — supports Gemini 3.1 Pro, Gemini 2.5 Flash, Gemini Nano.

    Uses the google-genai Python SDK.
    Env vars: GOOGLE_API_KEY or GOOGLE_APPLICATION_CREDENTIALS.
    """

    provider = "gemini"

    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.model = cfg.get("model", "gemini-2.5-flash")
        self.temperature = float(cfg.get("temperature", 0))
        self.pricing = cfg.get("pricing", {"input_per_1k": 0.0, "output_per_1k": 0.0})
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
        self._ready = False

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                self._ready = True
            except Exception:
                pass

    def invoke(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[ToolCall], int, float]:
        t0 = time.perf_counter()
        if not self._ready:
            return "Gemini adapter not configured (missing GOOGLE_API_KEY).", [], 0, 0.0

        tools_raw = context.get("tools") if context else None

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "contents": prompt,
        }

        config: Dict[str, Any] = {}
        if self.temperature >= 0:
            config["temperature"] = self.temperature
        if config:
            from google.genai import types
            kwargs["config"] = types.GenerateContentConfig(**config)

        # Convert OpenAI-format tools to Gemini function declarations
        if tools_raw:
            from google.genai import types
            declarations = []
            for t in tools_raw:
                fn = t.get("function", {})
                declarations.append(types.FunctionDeclaration(
                    name=fn.get("name", ""),
                    description=fn.get("description", ""),
                    parameters=fn.get("parameters", {}),
                ))
            kwargs["config"] = types.GenerateContentConfig(
                temperature=self.temperature,
                tools=[types.Tool(function_declarations=declarations)],
            )

        resp = self.client.models.generate_content(**kwargs)

        text = ""
        tool_calls: List[ToolCall] = []

        if resp.candidates:
            for part in resp.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    text += part.text
                if hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    tool_calls.append({
                        "name": fc.name,
                        "arguments": dict(fc.args) if fc.args else {},
                    })

        usage = getattr(resp, "usage_metadata", None)
        cost = 0.0
        if usage:
            in_k = (getattr(usage, "prompt_token_count", 0) or 0) / 1000.0
            out_k = (getattr(usage, "candidates_token_count", 0) or 0) / 1000.0
            cost = in_k * float(self.pricing.get("input_per_1k", 0)) + out_k * float(self.pricing.get("output_per_1k", 0))

        latency_ms = int((time.perf_counter() - t0) * 1000)
        return text, tool_calls, latency_ms, cost
