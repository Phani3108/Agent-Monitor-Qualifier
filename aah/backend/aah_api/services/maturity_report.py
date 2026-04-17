from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from jinja2 import Environment, FileSystemLoader

from ..models.maturity import MaturityAssessment

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

_env = Environment(
    loader=FileSystemLoader(str(ASSETS_DIR)),
    autoescape=True,
)


def _radar_coords(
    scores: list, cx: int = 200, cy: int = 200, max_r: int = 150
) -> dict:
    n = len(scores)
    angle_step = 2 * math.pi / n

    def pt(i: int, r: float) -> Tuple[float, float]:
        angle = -math.pi / 2 + i * angle_step
        return round(cx + r * math.cos(angle), 1), round(cy + r * math.sin(angle), 1)

    grid_rings = []
    for lv in [1, 2, 3, 4, 5]:
        r = (lv / 5) * max_r
        grid_rings.append(" ".join(f"{pt(i, r)[0]},{pt(i, r)[1]}" for i in range(n)))

    axes = [{"x2": pt(i, max_r + 10)[0], "y2": pt(i, max_r + 10)[1]} for i in range(n)]

    data_points = []
    labels = []
    for i, ds in enumerate(scores):
        r = (ds.score / 5) * max_r
        dx, dy = pt(i, r)
        lx, ly = pt(i, max_r + 28)
        data_points.append({"x": dx, "y": dy})
        labels.append({"x": lx, "y": ly, "text": f"{ds.label} (L{ds.level})"})

    data_polygon = " ".join(f"{p['x']},{p['y']}" for p in data_points)

    return {
        "grid_rings": grid_rings,
        "axes": axes,
        "data_polygon": data_polygon,
        "data_points": data_points,
        "labels": labels,
    }


def render_maturity_report(assessment: MaturityAssessment) -> str:
    template = _env.get_template("maturity_report.html.j2")
    radar = _radar_coords(assessment.dimension_scores)
    return template.render(assessment=assessment, radar=radar)
