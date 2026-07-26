from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.channel_length_contract import validate_supported_channel_length_nm
from sram_layoutgen.openyield_adapter.dimension_units import normalize_dimension_nm
from sram_layoutgen.openyield_adapter.parameterized_cell_naming import build_cache_key, canonical_cell_name


def main() -> int:
    report = json.loads((REPO_ROOT / "docs/M12C3R_parameter_naming_contract_correction_report.json").read_text(encoding="utf-8"))
    assert normalize_dimension_nm("0.09e-6", "METER") == 90
    assert normalize_dimension_nm("0.27e-6", "METER") == 270
    assert normalize_dimension_nm("0.05e-6", "METER") == 50
    assert normalize_dimension_nm("0.25e-6", "METER") == 250
    assert normalize_dimension_nm("0.50e-6", "METER") == 500
    assert normalize_dimension_nm("0.81e-6", "METER") == 810
    assert normalize_dimension_nm("0.91e-6", "METER") == 910
    assert normalize_dimension_nm("2.43e-6", "METER") == 2430
    assert normalize_dimension_nm("7.29e-6", "METER") == 7290
    for value in ["0.09e-6", "0.27e-6", "0.05e-6", "0.25e-6"]:
        assert normalize_dimension_nm(value, "METER") > 0

    assert report["original_zero_dimension_token_detected"] is True
    assert report["original_naming_contract_valid"] is False
    assert report["original_naming_contract_superseded"] is True
    assert report["unit_normalization_corrected"] is True
    assert report["unit_normalization_failure_count"] == 0
    assert report["nonzero_dimension_to_zero_count_after_fix"] == 0
    assert report["source_pinv_extraction_completed"] is True
    assert report["source_pinv_instance_count"] > 0
    assert report["all_source_instances_covered"] is True
    assert report["corrected_parameterized_cell_naming_contract_locked"] is True
    assert report["source_derived_variant_contract_locked"] is True
    assert report["size_alias_collision_prevented_by_corrected_contract"] is True
    assert report["deterministic_name_generation_verified"] is True
    assert report["deterministic_cache_key_verified"] is True
    assert report["all_current_v1_lengths_equal_50nm"] is True
    assert report["freepdk45_minimum_channel_length_nm"] == 50
    assert report["current_v1_channel_length_requirement_satisfied"] is True
    assert report["channel_length_blocks_M12C3A"] is False
    assert report["recommended_adapter_execution_mode"] != "NOT_CALLABLE"
    assert report["can_claim_parameterized_primitive_generator_implemented"] is False
    assert report["recommended_next_stage"] == "M12C3A_IMPLEMENT_PARAMETERIZED_DEVICE_AND_GATE_GENERATOR"

    variant_path = REPO_ROOT / "docs/mapping/M12C3R_corrected_physical_variant_matrix.csv"
    with variant_path.open("r", encoding="utf-8", newline="") as handle:
        variant_rows = list(csv.DictReader(handle))
    tuple_to_name = {}
    tuple_to_key = {}
    name_re = re.compile(r"^[A-Z0-9_]+_NW[1-9][0-9]*_PW[1-9][0-9]*_L[1-9][0-9]*$")
    for row in variant_rows:
        assert name_re.match(row["canonical_physical_cell_name"]), row["canonical_physical_cell_name"]
        assert "NW0" not in row["canonical_physical_cell_name"]
        assert "PW0" not in row["canonical_physical_cell_name"]
        assert "L0" not in row["canonical_physical_cell_name"]
        tuple_to_name.setdefault(row["canonical_parameter_tuple"], row["canonical_physical_cell_name"])
        tuple_to_key.setdefault(row["canonical_parameter_tuple"], row["cache_key"])
        assert tuple_to_name[row["canonical_parameter_tuple"]] == row["canonical_physical_cell_name"]
        assert tuple_to_key[row["canonical_parameter_tuple"]] == row["cache_key"]
    assert len(set(tuple_to_key.values())) == len(tuple_to_key)
    assert len(set(tuple_to_name.values())) == len(tuple_to_name)

    c1 = canonical_cell_name(logical_type="PINV", nmos_width_nm=90, pmos_width_nm=270, length_nm=50)
    c2 = canonical_cell_name(logical_type="PINV", nmos_width_nm=270, pmos_width_nm=810, length_nm=50)
    c3 = canonical_cell_name(logical_type="PINV", nmos_width_nm=910, pmos_width_nm=2430, length_nm=50)
    c4 = canonical_cell_name(logical_type="PINV", nmos_width_nm=2430, pmos_width_nm=7290, length_nm=50)
    c5 = canonical_cell_name(logical_type="TRANSMISSION_GATE", nmos_width_nm=250, pmos_width_nm=500, length_nm=50)
    assert c1 == "PINV_NW90_PW270_L50"
    assert c2 == "PINV_NW270_PW810_L50"
    assert c3 == "PINV_NW910_PW2430_L50"
    assert c4 == "PINV_NW2430_PW7290_L50"
    assert c5 == "TRANSMISSION_GATE_NW250_PW500_L50"

    key1 = build_cache_key(
        technology="FreePDK45",
        logical_type="PINV",
        nmos_width_nm=90,
        pmos_width_nm=270,
        channel_length_nm=50,
        finger_or_mult_policy="num=1",
        contact_policy="OpenRAM default pgate/ptx contact policy",
        rail_policy="OpenRAM row rails on vdd/gnd",
        orientation_policy="fixed row orientation",
        source_netlist_role="TIME.inv",
    )
    key1_dup = build_cache_key(
        technology="FreePDK45",
        logical_type="PINV",
        nmos_width_nm=90,
        pmos_width_nm=270,
        channel_length_nm=50,
        finger_or_mult_policy="num=1",
        contact_policy="OpenRAM default pgate/ptx contact policy",
        rail_policy="OpenRAM row rails on vdd/gnd",
        orientation_policy="fixed row orientation",
        source_netlist_role="TIME.inv",
    )
    key2 = build_cache_key(
        technology="FreePDK45",
        logical_type="PINV",
        nmos_width_nm=250,
        pmos_width_nm=500,
        channel_length_nm=50,
        finger_or_mult_policy="num=1",
        contact_policy="OpenRAM default pgate/ptx contact policy",
        rail_policy="OpenRAM row rails on vdd/gnd",
        orientation_policy="fixed row orientation",
        source_netlist_role="DFF.inv_dff",
    )
    assert key1 == key1_dup
    assert key1 != key2

    with (REPO_ROOT / "docs/mapping/M12C3R_source_derived_pinv_instances.csv").open("r", encoding="utf-8", newline="") as handle:
        pinv_source_rows = list(csv.DictReader(handle))
    assert len(pinv_source_rows) == report["source_pinv_instance_count"]
    assert report["logical_name_collision_detected"] is True
    assert report["logical_name_collision_count"] > 0
    assert "PINV1" in report["logical_names_with_multiple_parameter_sets"]

    assert validate_supported_channel_length_nm(50) == 50
    try:
        validate_supported_channel_length_nm(60)
    except ValueError:
        pass
    else:
        raise AssertionError("non-50nm channel length should be rejected")

    print("M12C3R_parameter_and_naming_contract_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
