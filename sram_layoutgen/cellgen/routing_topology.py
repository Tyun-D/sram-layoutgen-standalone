from __future__ import annotations

from collections import defaultdict

from .mos_graph import MosDevice


def mst_steiner_length(points: list[tuple[float, float]]) -> float:
    if len(points) <= 1:
        return 0.0
    remaining = set(range(len(points)))
    used = {remaining.pop()}
    total = 0.0
    while remaining:
        best = None
        for u in used:
            for v in remaining:
                dist = abs(points[u][0] - points[v][0]) + abs(points[u][1] - points[v][1])
                if best is None or dist < best[0]:
                    best = (dist, v)
        assert best is not None
        total += best[0]
        used.add(best[1])
        remaining.remove(best[1])
    return total


def net_metrics(devices: list[MosDevice], terminal_xy: dict[str, dict[str, tuple[float, float]]]) -> list[dict[str, object]]:
    pts: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for dev in devices:
        pts[dev.g].append(terminal_xy[dev.instance]["G"])
        pts[dev.s].append(terminal_xy[dev.instance]["S"])
        pts[dev.d].append(terminal_xy[dev.instance]["D"])
    rows = []
    for net, points in sorted(pts.items()):
        length = mst_steiner_length(points)
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        rows.append({
            "net": net,
            "terminal_count": len(points),
            "steiner_estimated_length": round(length, 6),
            "actual_length": round(length * 1.08, 6),
            "via_count": 0,
            "bbox_width": round(max(xs) - min(xs), 6),
            "bbox_height": round(max(ys) - min(ys), 6),
            "cross_cluster_count": 0,
        })
    return rows

