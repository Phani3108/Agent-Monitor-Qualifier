from __future__ import annotations
from typing import Dict, List, Tuple, Any, Optional, Protocol

ToolCall = Dict[str, Any]

class AgentAdapter(Protocol):
    """All adapters must implement this minimal contract."""
    provider: str

    def invoke(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, List[ToolCall], int, float]:
        """Return (text, tool_calls, latency_ms, cost_usd)."""
        ...
