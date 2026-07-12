from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.gds_label_sanitizer import recursive_label_inventory

PINV_CANONICAL = {"VDD", "VSS", "A", "Z"}
TG_CANONICAL = {"VDD", "VSS", "IN", "OUT", "CTR_P", "CTR_N"}


def _original_sources() -> list[tuple[str, Path]]:
    pinv_root = REPO_ROOT / "outputs/M12C3A_parameterized_device_gate_generator/current_supported_config/cells"
    tg_root = REPO_ROOT / "outputs/M12C3A3_transmission_gate_adapter_repair/current_supported_config/TRANSMISSION_GATE_NW250_PW500_L50"
    rows = [(cell_dir.name, cell_dir / f"{cell_dir.name}.gds") for cell_dir in sorted(pinv_root.glob("PINV_*"))]
    rows.append(("TRANSMISSION_GATE_NW250_PW500_L50", tg_root / "TRANSMISSION_GATE_NW250_PW500_L50.gds"))
    return rows


def _sanitized_sources() -> list[tuple[str, Path]]:
    root = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells"
    rows = []
    for cell_dir in sorted(root.iterdir()):
        if cell_dir.is_dir():
            rows.append((cell_dir.name, cell_dir / f"{cell_dir.name}.gds"))
    return rows


def _same_coordinate_duplicates(rows: list[dict[str, object]]) -> int:
    seen: dict[tuple[object, ...], int] = {}
    for row in rows:
        key = (row["label_text"], row["origin_x"], row["origin_y"])
        seen[key] = seen.get(key, 0) + 1
    return sum(1 for count in seen.values() if count > 1)


def main() -> int:
    pinv_duplicate_label_cell_count = 0
    transmission_gate_duplicate_label_count = 0
    internal_gsd_label_leakage_detected = False
    for cell_name, gds_path in _original_sources():
        rows = recursive_label_inventory(gds_path, cell_name)
        lowercase_alias_count = sum(1 for row in rows if row["is_lowercase_alias"])
        internal_count = sum(1 for row in rows if row["is_internal_device_terminal"])
        if cell_name.startswith("PINV_") and (len(rows) > 4 or lowercase_alias_count > 0 or internal_count > 0):
            pinv_duplicate_label_cell_count += 1
        if cell_name.startswith("TRANSMISSION_GATE_"):
            transmission_gate_duplicate_label_count = len(rows) - 6
        internal_gsd_label_leakage_detected |= internal_count > 0

    assert pinv_duplicate_label_cell_count == 9
    assert transmission_gate_duplicate_label_count == 12
    assert internal_gsd_label_leakage_detected is True

    for cell_name, gds_path in _sanitized_sources():
        rows = recursive_label_inventory(gds_path, cell_name)
        expected = TG_CANONICAL if cell_name.startswith("TRANSMISSION_GATE_") else PINV_CANONICAL
        assert len(rows) == len(expected)
        assert {row["label_text"] for row in rows} == expected
        assert all(row["hierarchy_cell_name"] == cell_name for row in rows)
        assert sum(1 for row in rows if row["is_lowercase_alias"]) == 0
        assert sum(1 for row in rows if row["is_internal_device_terminal"]) == 0
        assert sum(int(row["exact_duplicate_count"]) for row in rows) == len(rows)
        assert _same_coordinate_duplicates(rows) == 0
        assert all(row["same_component_distinct_label_names"] == row["label_text"] for row in rows)
        by_label = {}
        for row in rows:
            by_label[row["label_text"]] = by_label.get(row["label_text"], 0) + 1
        assert all(count == 1 for count in by_label.values())

        inventory_path = (
            REPO_ROOT
            / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells"
            / cell_name
            / f"{cell_name}_label_inventory.json"
        )
        assert json.loads(inventory_path.read_text()) == rows

    print("M12C3A4_label_inventory_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
