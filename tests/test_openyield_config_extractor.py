from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.openyield_config_extractor import (  # noqa: E402
    build_spec_field_source_matrix,
    build_variation_support_summary,
    list_candidate_files,
    parse_variation_text,
    variation_to_openyield_dimensions,
)


def main() -> int:
    openyield_root = Path("/data1/qujh/work/external/OpenYield")
    t1_inventory = REPO_ROOT / "outputs/T1_openyield_file_inventory/current_supported_config/openyield_full_file_inventory.csv"
    locked_spec = __import__("json").loads((REPO_ROOT / "outputs/M8_reproduce_uploaded_golden/current_supported_config/SRAM_SPEC.json").read_text(encoding="utf-8"))

    candidate_rows = list_candidate_files(openyield_root, t1_inventory)
    assert len(candidate_rows) >= 20
    assert any(row["relative_path"] == "main_sram.py" for row in candidate_rows)
    assert any(row["relative_path"] == "sram_compiler/config_yaml/global.yaml" for row in candidate_rows)

    source_matrix_rows, trace = build_spec_field_source_matrix(openyield_root=openyield_root, locked_spec=locked_spec)
    by_field = {row["spec_field"]: row for row in source_matrix_rows}
    assert by_field["num_rows"]["source_type"] == "RAW_OPENYIELD_CONFIG"
    assert by_field["num_cols"]["source_type"] == "RAW_OPENYIELD_CONFIG"
    assert by_field["word_size"]["source_type"] == "LOCKED_GOLDEN_FALLBACK"
    assert by_field["words_per_row"]["is_fallback"] is True
    assert trace["openyield_capacity_config_found"] is True
    assert trace["num_rows_source_backed"] is True
    assert trace["num_cols_source_backed"] is True
    assert trace["word_size_source_backed"] is False
    assert trace["derived_spec"]["word_size"] == 16
    assert trace["derived_spec"]["num_words"] == 16
    assert trace["derived_spec"]["words_per_row"] == 1

    variation_dims = variation_to_openyield_dimensions(4, 32, 2)
    assert variation_dims["num_rows"] == 16
    assert variation_dims["num_cols"] == 8
    assert variation_dims["choose_columnmux"] is True
    parsed = parse_variation_text("8x64_wpr4")
    assert parsed == {"word_size": 8, "num_words": 64, "words_per_row": 4}

    variation_summary = build_variation_support_summary(openyield_root)
    assert variation_summary["total_bits"] == 262144
    assert len(variation_summary["raw_variations"]) > 0
    assert any(item["rows"] == 16 and item["cols"] == 16 for item in variation_summary["raw_variations"])

    print("openyield_config_extractor_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
