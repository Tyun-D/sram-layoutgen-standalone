from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.project_long_range import (  # noqa: E402
    build_formal_sram_config_inventory,
    build_formal_sram_config_schema,
    check_claim_policy,
    parse_sram_top_name,
    validate_formal_sram_config_inventory,
)


def main() -> int:
    schema = build_formal_sram_config_schema()
    assert schema["schema_name"] == "FORMAL_SRAM_CONFIG_SCHEMA"
    assert any(field["name"] == "addr_width" for field in schema["fields"])

    parsed = parse_sram_top_name("sram_16x32_wpr2_fd45")
    assert parsed["word_size"] == 16
    assert parsed["num_words"] == 32
    assert parsed["num_rows"] == 16
    assert parsed["num_cols"] == 32

    inventory_rows, binding_rows, summary = build_formal_sram_config_inventory(
        repo_root=REPO_ROOT,
        source_tree=Path("/data1/qujh/work/sram_layoutgen_step45_clean"),
        openyield_root=Path("/data1/qujh/work/external/OpenYield"),
    )
    assert summary["source_backed_variation_count"] >= 3
    assert any(row["config_id"] == "formal_8x64_wpr4" for row in inventory_rows)
    assert any(row["config_id"] == "cfg_64x64_wpr1" for row in inventory_rows)
    assert any(row["binding_type"] == "CANONICAL_SINGLE_BANK_CONTRACT" for row in binding_rows)

    validation = validate_formal_sram_config_inventory(inventory_rows)
    assert validation["valid"] is True

    checker = check_claim_policy(
        [
            REPO_ROOT / "docs/SIGNOFF.md",
            REPO_ROOT / "docs/PROJECT_GAP_REGISTER.md",
        ]
    )
    assert checker["passed"] is True
    print("project_long_range_support_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
