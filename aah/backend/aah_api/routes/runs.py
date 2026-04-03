from __future__ import annotations
from fastapi import APIRouter, HTTPException, Body

from pydantic import BaseModel, field_validator
from ..services.spec_loader import load_and_validate_spec, load_spec_from_file
from ..services.orchestrator import execute_run, load_summary, RUNS_DIR
from ..services.broadcast import allowed as bc_ok, post_card
import json
from typing import Literal, Optional

router = APIRouter()


class CreateRunRequest(BaseModel):
    spec_yaml: str
    packs: Optional[list[Literal["functional","safety","determinism"]]] = None

    @field_validator("packs")
    @classmethod
    def _uniq(cls, v):
        if v is None: return v
        return list(dict.fromkeys(v))


@router.post("/runs")
def create_run(req: CreateRunRequest):
    try:
        spec = load_and_validate_spec(req.spec_yaml)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Spec validation failed: {e}")
    summary = execute_run(spec, packs=req.packs)
    # Teams Adaptive Card broadcast
    if bc_ok():
        try:
            post_card("AAH run completed", {"run_id": summary["run_id"], "overall": summary["scores"]["overall"], "certified": summary["certified"]})
        except Exception:
            pass
    return summary.model_dump()



# Determinism rerun endpoint with override support
@router.post("/runs/{run_id}/determinism/rerun")
def rerun_det(run_id: str, samples: int = Body(None), concurrency: int = Body(None)):
    from ..services.orchestrator import RUNS_DIR, execute_run, load_summary
    # Load original spec YAML if stored OR read from summary.artifacts/spec.yaml if you saved it earlier.
    # If you didn’t store spec text, accept a 400 gracefully.
    summ = load_summary(run_id)
    spec_path = RUNS_DIR / run_id / "spec.yaml"
    if not spec_path.exists():
        raise HTTPException(status_code=400, detail="Original spec yaml not found for this run.")
    spec = load_spec_from_file(spec_path)
    # inject overrides
    data = spec.model_dump()
    det = data.get("determinism") or {}
    if samples: det["samples"] = samples
    if concurrency: det["concurrency"] = concurrency
    data["determinism"] = det
    # Re-validate
    from ..models.dto import TestSpec
    spec2 = TestSpec.model_validate(data)
    # Execute determinism-only
    summary = execute_run(spec2, packs=["determinism"])
    return summary.model_dump()

@router.get("/runs/{run_id}")
def get_run(run_id: str):
    try:
        summary = load_summary(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")
    return summary.model_dump()


# List all runs (summaries)
@router.get("/runs")
def list_runs():
    items = []
    for d in sorted(RUNS_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        summ = d / "summary.json"
        if not summ.exists():
            continue
        data = summ.read_text(encoding="utf-8")
        items.append(json.loads(data))
    return items

# Get results for a run and pack
@router.get("/runs/{run_id}/results")
def get_results(run_id: str, pack: Literal["functional","safety","determinism"]):
    base = RUNS_DIR / run_id
    path = base / f"results.{pack}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Results not found")
    return json.loads(path.read_text(encoding="utf-8"))
