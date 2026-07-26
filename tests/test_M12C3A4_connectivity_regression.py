from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity
from sram_layoutgen.openyield_adapter.transmission_gate_connectivity_verifier import verify_transmission_gate_connectivity


def _graph_signature(graph: dict[str, object]) -> dict[str, object]:
    return {
        "layers_present": graph["layers_present"],
        "parent_active_to_segments": graph["parent_active_to_segments"],
        "active_segments": graph["active_segments"],
        "contact_links": graph["contact_links"],
        "components": graph["components"],
        "rectangles": graph["rectangles"],
    }


def _source_rows() -> list[tuple[str, Path, Path]]:
    pinv_root = REPO_ROOT / "outputs/M12C3A_parameterized_device_gate_generator/current_supported_config/cells"
    tg_root = REPO_ROOT / "outputs/M12C3A3_transmission_gate_adapter_repair/current_supported_config/TRANSMISSION_GATE_NW250_PW500_L50"
    reusable_root = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells"
    rows = []
    for cell_dir in sorted(pinv_root.glob("PINV_*")):
        rows.append((cell_dir.name, cell_dir / f"{cell_dir.name}.gds", reusable_root / cell_dir.name / f"{cell_dir.name}.gds"))
    rows.append(
        (
            "TRANSMISSION_GATE_NW250_PW500_L50",
            tg_root / "TRANSMISSION_GATE_NW250_PW500_L50.gds",
            reusable_root / "TRANSMISSION_GATE_NW250_PW500_L50" / "TRANSMISSION_GATE_NW250_PW500_L50.gds",
        )
    )
    return rows


def main() -> int:
    pinv_ok = True
    for cell_name, before_gds, after_gds in _source_rows():
        before_graph = extract_physical_connectivity(before_gds, cell_name)
        after_graph = extract_physical_connectivity(after_gds, cell_name)
        assert _graph_signature(before_graph) == _graph_signature(after_graph)
        if cell_name.startswith("PINV_"):
            pinv_ok &= True

    tg_gds = (
        REPO_ROOT
        / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells/TRANSMISSION_GATE_NW250_PW500_L50/TRANSMISSION_GATE_NW250_PW500_L50.gds"
    )
    _, tg_report = verify_transmission_gate_connectivity(tg_gds, "TRANSMISSION_GATE_NW250_PW500_L50")
    assert tg_report["physical_connectivity_verification_passed"] is True
    assert tg_report["connectivity_assertion_count"] == 27
    assert tg_report["connectivity_assertion_pass_count"] == 27
    assert tg_report["connectivity_assertion_failure_count"] == 0
    assert tg_report["in_connected_to_vdd_after_repair"] is False
    assert tg_report["in_connected_to_vss_after_repair"] is False
    assert tg_report["out_connected_to_vdd_after_repair"] is False
    assert tg_report["out_connected_to_vss_after_repair"] is False
    assert tg_report["vdd_connected_to_vss_after_repair"] is False
    assert tg_report["in_directly_connected_to_out_after_repair"] is False
    assert tg_report["pin_components"]["IN"] == tg_report["pmos_terminal_components"]["left"] == tg_report["nmos_terminal_components"]["left"]
    assert tg_report["pin_components"]["OUT"] == tg_report["pmos_terminal_components"]["right"] == tg_report["nmos_terminal_components"]["right"]
    assert tg_report["pin_components"]["VDD"] == tg_report["nwell_tap_component"]
    assert tg_report["pin_components"]["VSS"] == tg_report["pwell_tap_component"]
    assert tg_report["ctr_p_metal1_pin_added"] is True
    assert tg_report["ctr_n_metal1_pin_added"] is True
    assert tg_report["ctr_p_poly_contact_added"] is True
    assert tg_report["ctr_n_poly_contact_added"] is True
    assert tg_report["all_six_pins_metal_accessible"] is True
    assert pinv_ok is True

    print("M12C3A4_connectivity_regression_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
