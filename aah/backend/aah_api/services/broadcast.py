from __future__ import annotations
import os
from urllib.parse import urlparse
from typing import Any, Dict, List
import httpx
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def _allowed_host(host: str) -> bool:
    cfg_path = REPO_ROOT / "connectors.yml"
    try:
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        allow = set(cfg.get("allowlist") or [])
    except Exception:
        allow = set()
    return host in allow

def broadcast_to_teams(summary: Dict[str, Any]) -> Dict[str, Any]:
    url = os.getenv("TEAMS_WEBHOOK", "").strip()
    if not url:
        return {"sent": False, "reason": "TEAMS_WEBHOOK not set"}

    host = urlparse(url).hostname or ""
    if not _allowed_host(host):
        return {"sent": False, "reason": f"Host '{host}' not in connectors allowlist"}

    payload = {
        "text": (
            f"AAH Run {summary['run_id']} — "
            f"Overall {summary['scores']['overall']} | "
            f"Functional {summary['scores'].get('functional')} • Safety {summary['scores'].get('safety')} • Determinism {summary['scores'].get('determinism')} | "
            f"{'CERTIFIED ' + summary['cert']['version'] if summary.get('certified') else 'NOT CERTIFIED'}"
        )
    }
    try:
        resp = httpx.post(url, json=payload, timeout=5.0)
        return {"sent": resp.status_code in (200, 204), "status_code": resp.status_code}
    except Exception as e:
        return {"sent": False, "reason": str(e)}

def allowed(): return bool(os.getenv("TEAMS_WEBHOOK"))
def post_card(title: str, facts: dict):
    url = os.getenv("TEAMS_WEBHOOK","")
    if not url: return False
    import urllib.parse, http.client, json
    u = urllib.parse.urlparse(url)
    payload = {
      "type": "message",
      "attachments": [{
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {
          "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
          "type": "AdaptiveCard", "version": "1.4",
          "body": [
            {"type":"TextBlock","text": title, "weight":"Bolder","size":"Medium"},
            {"type":"FactSet","facts":[{"title":k,"value":str(v)} for k,v in facts.items()]}
          ]
        }
      }]
    }
    body = json.dumps(payload).encode("utf-8")
    conn = http.client.HTTPSConnection(u.netloc)
    conn.request("POST", u.path + ("?"+u.query if u.query else ""), body, {"Content-Type":"application/json"})
    r = conn.getresponse(); ok = (200 <= r.status < 300); conn.close()
    return ok
