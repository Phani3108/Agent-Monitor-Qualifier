from __future__ import annotations
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from .base import AgentAdapter, ToolCall


class AgentHTTPAdapter:
    """Generic HTTP adapter for remote agents exposing a chat/completions-style endpoint.

    Supports any agent that accepts a JSON body ``{"prompt": "...", "context": {...}}``
    and responds with ``{"text": "...", "tool_calls": [...]}``  (or OpenAI-compatible format).

    Works with:
      - Custom FastAPI / Flask agent services
      - OpenAI-compatible endpoints (GPT-5, GPT-5 Mini, GPT-5 Nano)
      - Anthropic Messages API proxy
      - Google Gemini REST proxy
      - Any A2A (Agent-to-Agent) protocol endpoint
    """

    provider = "http"

    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.endpoint: str = cfg["endpoint"]
        self.auth_header: str = cfg.get("auth_header", "Authorization")
        self.auth_value: str = cfg.get("auth_value", "")
        self.timeout: int = int(cfg.get("timeout_s", 30))
        self.response_format: str = cfg.get("response_format", "auto")  # auto | openai | simple

        parsed = urlparse(self.endpoint)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"AgentHTTPAdapter: invalid endpoint scheme: {parsed.scheme}")

    def invoke(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[ToolCall], int, float]:
        import urllib.request

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "aah-agent-adapter/1.0",
        }
        if self.auth_value:
            headers[self.auth_header] = self.auth_value

        body = json.dumps({"prompt": prompt, "context": context or {}}).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=body, headers=headers, method="POST")

        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read())
        except Exception as exc:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            return f"HTTP adapter error: {exc}", [], latency_ms, 0.0

        latency_ms = int((time.perf_counter() - t0) * 1000)

        # ── Parse response (supports multiple formats) ──
        text, tool_calls, cost_usd = self._parse_response(data)
        return text, tool_calls, latency_ms, cost_usd

    def _parse_response(self, data: Dict[str, Any]) -> Tuple[str, List[ToolCall], float]:
        # OpenAI-compatible format
        if "choices" in data:
            msg = data["choices"][0].get("message", {})
            text = msg.get("content", "")
            tool_calls = []
            for tc in msg.get("tool_calls", []):
                tool_calls.append({
                    "name": tc.get("function", {}).get("name", ""),
                    "arguments": tc.get("function", {}).get("arguments", {}),
                })
            usage = data.get("usage", {})
            cost = float(usage.get("total_cost", 0.0))
            return text, tool_calls, cost

        # Anthropic Messages format
        if "content" in data and isinstance(data["content"], list):
            text_parts = []
            tool_calls = []
            for block in data["content"]:
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    tool_calls.append({
                        "name": block.get("name", ""),
                        "arguments": block.get("input", {}),
                    })
            usage = data.get("usage", {})
            cost = float(usage.get("total_cost", 0.0))
            return " ".join(text_parts), tool_calls, cost

        # Simple / custom format
        text = data.get("text", "") or data.get("response", "")
        tool_calls = data.get("tool_calls", [])
        cost = float(data.get("cost_usd", 0.0))
        return text, tool_calls, cost
