from __future__ import annotations


def dominates(a: dict, b: dict, metrics: list[str]) -> bool:
    return all(float(a[m]) <= float(b[m]) for m in metrics) and any(float(a[m]) < float(b[m]) for m in metrics)


def pareto(rows: list[dict], metrics: list[str]) -> list[dict]:
    out = []
    for row in rows:
        dominated = any(dominates(other, row, metrics) for other in rows if other is not row)
        rec = dict(row)
        rec["pareto_status"] = "DOMINATED" if dominated else "NON_DOMINATED"
        out.append(rec)
    return out

