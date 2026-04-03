from __future__ import annotations
from fastapi import APIRouter, Header, HTTPException, Request
from typing import Dict, Any
import hmac, hashlib, os, json, re
from ..services.orchestrator import RUNS_DIR
from ..services.spec_loader import load_and_validate_spec
from ..services.orchestrator import execute_run, load_summary

router = APIRouter()
SECRET = lambda: os.getenv("TEAMS_OUTGOING_SECRET","")

def _verify(req_body: bytes, sig: str) -> bool:
    if not SECRET(): return False
    mac = hmac.new(SECRET().encode(), msg=req_body, digestmod=hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, sig.lower())

def _help():
    return {
      "text": "AAH commands:\n- run packs:<comma> tenant:<t> env:<e>\n- status <run_id>\n- baseline <run_id>",
      "type": "message"
    }

def _adaptive(title: str, facts: Dict[str, Any]):
    return {
      "text": title,
      "attachments": [{
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {
          "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
          "type": "AdaptiveCard",
          "version": "1.4",
          "body": [
            {"type":"TextBlock","text": title, "weight":"Bolder","size":"Medium"},
            {"type":"FactSet","facts":[{"title":k, "value":str(v)} for k,v in facts.items()]}
          ]
        }
      }]
    }

@router.post("/teams/outgoing")
async def teams_outgoing(request: Request, authorization: str | None = Header(None), hmacsha256: str | None = Header(None)):
    raw = await request.body()
    sig = (request.headers.get("HMAC") or hmacsha256 or "").strip()
    if not _verify(raw, sig):
      raise HTTPException(status_code=401, detail="HMAC verify failed")

    payload = await request.json()
    text = (payload.get("text") or "").strip()
    m = re.match(r"(?i)^help$", text)
    if m: return _help()

    m = re.match(r"(?i)^run\s+packs:(?P<packs>[a-z0-9_,.@\-~]+)(?:\s+tenant:(?P<tenant>[a-z0-9_\-]+))?(?:\s+env:(?P<env>[a-z0-9_\-]+))?$", text)
    if m:
        packs = [p.strip() for p in m.group("packs").split(",") if p.strip()]
        tenant = m.group("tenant") or "default"; env = m.group("env") or "staging"
        spec_yaml = f'agent: "support-refunds-bot"\ntenant: "{tenant}"\nenvironment: "{env}"\ninclude_packs:\n' + "\n".join([f"  - {p}" for p in packs])
        try:
            spec = load_and_validate_spec(spec_yaml)
        except Exception as e:
            return {"text": f"Spec invalid: {e}", "type":"message"}
        summary = execute_run(spec, packs=None)
        rid = summary.run_id if hasattr(summary, "run_id") else summary.get("run_id")
        return _adaptive("AAH run started",
            {"run_id": rid, "agent": summary.agent if hasattr(summary,"agent") else summary.get("agent"), "env": env, "packs": ", ".join(packs)})
    m = re.match(r"(?i)^status\s+([a-z0-9\-]+)$", text)
    if m:
        rid = m.group(1)
        try:
            s = load_summary(rid)
        except FileNotFoundError:
            return {"text":"Run not found", "type":"message"}
        return _adaptive("AAH run status", {"run_id": s.run_id, "overall": s.scores.get("overall"), "certified": s.certified})
    m = re.match(r"(?i)^baseline\s+([a-z0-9\-]+)$", text)
    if m:
        rid = m.group(1)
        try:
            s = load_summary(rid)
        except FileNotFoundError:
            return {"text":"Run not found", "type":"message"}
        from ..services.baseline import set_baseline
        data = set_baseline(s, force=True)
        return _adaptive("Baseline set", {"run_id": rid, "agent": s.agent, "env": s.environment})

    return _help()
