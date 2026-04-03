from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    mock_agent_mode: str = os.getenv("MOCK_AGENT_MODE", "buggy").lower()
    determinism_runs: int = int(os.getenv("DETERMINISM_RUNS", "10"))

settings = Settings()
