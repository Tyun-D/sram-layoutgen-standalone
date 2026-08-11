from __future__ import annotations


def compact_placements(placements: list[dict], *, x_scale: float, y_scale: float) -> list[dict]:
    xs = sorted({float(p["x"]) for p in placements})
    ys = sorted({float(p["y"]) for p in placements})
    xmap = {x: i * x_scale for i, x in enumerate(xs)}
    ymap = {y: i * y_scale for i, y in enumerate(ys)}
    return [
        {
            **p,
            "x": round(xmap[float(p["x"])], 6),
            "y": round(ymap[float(p["y"])], 6),
        }
        for p in placements
    ]
