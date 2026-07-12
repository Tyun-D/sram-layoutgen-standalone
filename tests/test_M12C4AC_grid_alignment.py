from __future__ import annotations

import csv
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _on_grid(value: float, grid: float = 0.0025) -> bool:
    return abs(value - round(value / grid) * grid) < 1e-9


def main() -> None:
    route_rows = list(csv.DictReader((REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_route_segment_matrix.csv").open()))
    via_rows = list(csv.DictReader((REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_via_matrix.csv").open()))
    for row in route_rows:
        coords = [float(v.strip()) for v in row["start"].strip("[]").split(",")] + [float(v.strip()) for v in row["end"].strip("[]").split(",")]
        assert all(_on_grid(value) for value in coords)
        assert _on_grid(float(row["width"]))
    for row in via_rows:
        assert _on_grid(float(row["x"]))
        assert _on_grid(float(row["y"]))


if __name__ == "__main__":
    main()

