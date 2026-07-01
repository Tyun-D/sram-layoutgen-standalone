from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.module_semantics import build_l0_semantics_report  # noqa: E402


def main() -> int:
    payload = build_l0_semantics_report(
        repo_root=REPO_ROOT,
        openyield_root=REPO_ROOT.parent / "external" / "OpenYield",
    )
    report = payload["report"]
    module_rows = payload["module_rows"]
    parameter_rows = payload["parameter_rows"]
    connection_rows = payload["connection_rows"]
    variation_rows = payload["variation_rows"]
    mapping_rows = payload["layoutgen_mapping_rows"]

    module_by_name = {row["module"]: row for row in module_rows}
    param_by_name = {row["parameter"]: row for row in parameter_rows}
    mapping_by_name = {row["openyield_module"]: row for row in mapping_rows}

    assert report["module_count"] == 25
    assert report["parameter_count"] == 20
    assert len(connection_rows) >= 20
    assert len(variation_rows) == 7
    assert len(mapping_rows) >= 20

    assert module_by_name["bitcell_array"]["semantic_mapping_status"] == "SEMANTICS_CLOSED"
    assert module_by_name["row_decoder"]["semantic_mapping_status"] == "SEMANTICS_CLOSED"
    assert module_by_name["wordline_driver"]["semantic_mapping_status"] == "SEMANTICS_CLOSED"
    assert module_by_name["CONTROL_LOGIC"]["semantic_mapping_status"] == "SOURCE_FOUND_PORTS_PARTIAL"
    assert module_by_name["PRECHARGE_ENABLE_PATH"]["semantic_mapping_status"] == "SOURCE_FOUND_CONNECTIONS_UNRESOLVED"
    assert module_by_name["BANK"]["semantic_mapping_status"] == "LOCAL_MAPPING_UNRESOLVED"
    assert module_by_name["SRAM_TOP"]["openyield_source_found"] is True

    assert param_by_name["num_rows"]["openyield_source_path"].startswith("sram_compiler/config_yaml/global.yaml")
    assert param_by_name["word_size"]["openyield_source_path"] == "not_found_in_source"
    assert "mux_in=2" in param_by_name["column_mux_ratio"]["derivation_rule"]
    assert "num_rows=16 and num_cols=512" in param_by_name["delay_chain_related_parameters"]["derivation_rule"]

    assert mapping_by_name["sense_amp"]["mapping_type"] == "PARTIAL_MATCH"
    assert mapping_by_name["DELAY_CHAIN"]["mapping_status"] == "metadata_only"
    assert mapping_by_name["PRECHARGE_ENABLE_PATH"]["mapping_type"] == "NO_LOCAL_COUNTERPART"

    assert "bitcell_array" in report["semantics_closed_modules"]
    assert "PRECHARGE_ENABLE_PATH" in report["source_found_connections_unresolved_modules"]
    assert "BANK" in report["local_mapping_unresolved_modules"]
    assert "word_size/num_words/words_per_row" in report["l0_blocking_gaps"][1]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
