from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import yaml, os

from ..adapters.base import AgentAdapter
from ..adapters.agent_mock import MockAgent
from ..adapters.azure_openai import AzureOpenAIAdapter
from ..adapters.openai_direct import OpenAIDirectAdapter
from ..adapters.anthropic_claude import AnthropicAdapter
from ..adapters.gemini import GeminiAdapter
from ..adapters.agent_http import AgentHTTPAdapter

REPO_ROOT = Path(__file__).resolve().parents[2]

def load_agent_cfg(agent: str, environment: str) -> Dict[str, Any]:
    p = REPO_ROOT / "agents" / agent / "agent.yaml"
    data: Dict[str, Any] = {}
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    data["environment"] = environment
    return data

def build_adapter(agent: str, environment: str) -> tuple[AgentAdapter, Dict[str, Any]]:
    cfg = load_agent_cfg(agent, environment)
    provider = str(cfg.get("provider", "mock")).lower()

    if provider == "azure_openai":
        adapter = AzureOpenAIAdapter({
            "deployment": cfg.get("azure_openai", {}).get("deployment"),
            "api_version": cfg.get("azure_openai", {}).get("api_version"),
            "endpoint": cfg.get("azure_openai", {}).get("endpoint"),
            "temperature": cfg.get("temperature", 0),
            "pricing": cfg.get("pricing", {}),
        })
        return adapter, {"provider": adapter.provider, **cfg}

    if provider == "openai":
        adapter = OpenAIDirectAdapter({
            "model": cfg.get("model", "gpt-5"),
            "temperature": cfg.get("temperature", 0),
            "pricing": cfg.get("pricing", {}),
        })
        return adapter, {"provider": adapter.provider, **cfg}

    if provider == "anthropic":
        adapter = AnthropicAdapter({
            "model": cfg.get("model", "claude-sonnet-4-20250514"),
            "temperature": cfg.get("temperature", 0),
            "max_tokens": cfg.get("max_tokens", 4096),
            "pricing": cfg.get("pricing", {}),
        })
        return adapter, {"provider": adapter.provider, **cfg}

    if provider == "gemini":
        adapter = GeminiAdapter({
            "model": cfg.get("model", "gemini-2.5-flash"),
            "temperature": cfg.get("temperature", 0),
            "pricing": cfg.get("pricing", {}),
        })
        return adapter, {"provider": adapter.provider, **cfg}

    if provider == "http":
        adapter = AgentHTTPAdapter({
            "endpoint": cfg.get("endpoint", ""),
            "auth_header": cfg.get("auth_header", "Authorization"),
            "auth_value": cfg.get("auth_value", ""),
            "timeout_s": cfg.get("timeout_s", 30),
            "response_format": cfg.get("response_format", "auto"),
        })
        return adapter, {"provider": adapter.provider, **cfg}

    # Default: mock
    adapter = MockAgent()
    return adapter, {"provider": "mock", **cfg}
