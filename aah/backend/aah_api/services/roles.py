from __future__ import annotations
from typing import Dict, List

SCOPES = [
    "runs:read","runs:create","runs:rerun","runs:harden",
    "results:read","reports:read","badge:read","compare:read",
    "baselines:set","incidents:read","incidents:resolve",
    "sign:run","verify:run","tokens:issue","users:read"
]

ROLE_SCOPES: Dict[str, List[str]] = {
    "owner": SCOPES,
    "maintainer": [
        "runs:read","runs:create","runs:rerun","runs:harden",
        "results:read","reports:read","badge:read","compare:read",
        "baselines:set","incidents:read","incidents:resolve","sign:run","verify:run"
    ],
    "reviewer": [
        "runs:read","results:read","reports:read","badge:read","compare:read","incidents:read"
    ],
    "viewer": ["runs:read","reports:read","badge:read"]
}
