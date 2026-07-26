from __future__ import annotations

import json
import sys
from pathlib import Path

import gdstk

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.gds_label_sanitizer import recursive_label_inventory

PINV_EXPECTED = ["VDD", "VSS", "A", "Z"]
TG_EXPECTED = ["VDD", "VSS", "IN", "OUT", "CTR_P", "CTR_N"]
FORBIDDEN = {"vdd", "gnd", "in", "out", "ctr_p", "ctr_n", "G", "S", "D"}


def _sanitized_sources() -> list[tuple[str, Path]]:
    root = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells"
    rows = []
    for cell_dir in sorted(root.iterdir()):
        if cell_dir.is_dir():
            rows.append((cell_dir.name, cell_dir / f"{cell_dir.name}.gds"))
    return rows


def _label_on_pin(pin_bbox: dict[str, float], row: dict[str, object]) -> bool:
    x = float(row["origin_x"])
    y = float(row["origin_y"])
    return pin_bbox["lx"] <= x <= pin_bbox["rx"] and pin_bbox["by"] <= y <= pin_bbox["uy"]


def main() -> int:
    for cell_name, gds_path in _sanitized_sources():
        expected = TG_EXPECTED if cell_name.startswith("TRANSMISSION_GATE_") else PINV_EXPECTED
        pin_map_path = gds_path.parent / f"{cell_name}_pin_map.json"
        pin_map = json.loads(pin_map_path.read_text())
        rows = recursive_label_inventory(gds_path, cell_name)

        lib = gdstk.read_gds(gds_path)
        top = next(cell for cell in lib.cells if cell.name == cell_name)
        top_label_names = [str(label.text) for label in top.labels]
        assert sorted(top_label_names) == sorted(expected)
        assert len(top.references) > 0
        for child in lib.cells:
            if child.name != cell_name:
                assert len(child.labels) == 0

        assert all(row["label_text"] not in FORBIDDEN for row in rows if row["label_text"] not in expected)
        for label_name in expected:
            matches = [row for row in rows if row["label_text"] == label_name]
            assert len(matches) == 1
            assert _label_on_pin(pin_map[label_name][0], matches[0])
            assert pin_map[label_name][0]["layer"] == "m1"

    print("M12C3A4_canonical_pin_namespace_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
