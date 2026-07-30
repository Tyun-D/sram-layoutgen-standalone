#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
OUT_DIR = REPO_ROOT / "outputs" / "PROJECT_row_decoder_v2_source_binding" / "current_supported_config"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = list(rows[0].keys()) if rows else []
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def git_head() -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git rev-parse HEAD failed")
    return completed.stdout.strip()


def main() -> None:
    logical = read_json(DOCS / "DECODER_V2_LOGICAL_CONTRACT.json")
    bit_rows = list(csv.DictReader((DOCS / "DECODER_V2_BIT_MAPPING.csv").open(encoding="utf-8")))
    pinv_pinmap = read_json(
        REPO_ROOT
        / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells/PINV_NW90_PW270_L50/PINV_NW90_PW270_L50_pin_map.json"
    )
    and2_pinmap = read_json(REPO_ROOT / "outputs/PROJECT_decoder_v2_formal_gate_pinmaps/current_supported_config/AND2_pin_map.json")
    and3_pinmap = read_json(REPO_ROOT / "outputs/PROJECT_decoder_v2_formal_gate_pinmaps/current_supported_config/AND3_pin_map.json")

    output_map = {int(row["bit_index"]): row for row in bit_rows}
    binding_rows: list[dict[str, Any]] = []

    for idx, pin_name in enumerate(["A0", "A1", "A2"]):
        binding_rows.append(
            {
                "instance_name": f"inv_{pin_name.lower()}",
                "logical_child_type": "PINV",
                "resolved_physical_cell_name": "PINV_NW90_PW270_L50",
                "child_pin_order": json.dumps(["VDD", "VSS", "A", "Z"]),
                "parent_net_connections": json.dumps(["VDD", "VSS", pin_name, f"{pin_name}b"]),
                "source_line_or_role": f"DECODER3_8.inv_{pin_name}",
                "pin_map_pin_names": json.dumps(sorted(pinv_pinmap.keys())),
                "binding_status": "APPROVED_EXACT_BINDING",
            }
        )

    for bit in range(8):
        row = output_map[bit]
        expr = row["predecode_expression"].replace(" ", "")
        terms = expr.split("&")
        binding_rows.append(
            {
                "instance_name": f"and3_pre_{bit}",
                "logical_child_type": "AND3",
                "resolved_physical_cell_name": "AND3_PNAND3_PINV_FPDK45",
                "child_pin_order": json.dumps(["VDD", "VSS", "A", "B", "C", "Z"]),
                "parent_net_connections": json.dumps(["VDD", "VSS", terms[0], terms[1], terms[2], f"WL{bit}_pre"]),
                "source_line_or_role": f"DECODER3_8.AND{bit}",
                "pin_map_pin_names": json.dumps(sorted(and3_pinmap.keys())),
                "binding_status": "APPROVED_EXACT_BINDING",
            }
        )
        binding_rows.append(
            {
                "instance_name": f"and2_en_{bit}",
                "logical_child_type": "AND2",
                "resolved_physical_cell_name": "AND2_PNAND2_PINV_FPDK45",
                "child_pin_order": json.dumps(["VDD", "VSS", "A", "B", "Z"]),
                "parent_net_connections": json.dumps(["VDD", "VSS", f"WL{bit}_pre", "EN", f"WL{bit}"]),
                "source_line_or_role": f"DECODER3_8.AND_EN{bit}",
                "pin_map_pin_names": json.dumps(sorted(and2_pinmap.keys())),
                "binding_status": "APPROVED_EXACT_BINDING",
            }
        )

    report = {
        "scope": "project_row_decoder_v2_source_binding",
        "git_head": git_head(),
        "logical_contract_path": str((DOCS / "DECODER_V2_LOGICAL_CONTRACT.json").resolve()),
        "bit_mapping_path": str((DOCS / "DECODER_V2_BIT_MAPPING.csv").resolve()),
        "physical_sources": {
            "PINV": "PINV_NW90_PW270_L50",
            "AND3": "AND3_PNAND3_PINV_FPDK45",
            "AND2": "AND2_PNAND2_PINV_FPDK45",
        },
        "decoder3_8_leaf_topology": {
            "inv_count": 3,
            "and3_count": 8,
            "and2_count": 8,
        },
        "binding_row_count": len(binding_rows),
        "top_ports": next(item["ports"] for item in logical["v2_child_targets"] if item["module"] == "row_decoder_v2"),
        "binding_rows": binding_rows,
    }
    md_lines = [
        "# Row Decoder V2 Source Binding",
        "",
        f"- git_head: `{report['git_head']}`",
        "- exact_topology: `3xINV + 8xAND3 + 8xAND2`",
        f"- binding_row_count: `{len(binding_rows)}`",
        "- source_authority: `OpenYield DECODER3_8 exact topology + exact leaf pin maps`",
        "",
    ]
    write_json(DOCS / "ROW_DECODER_V2_SOURCE_BINDING.json", report)
    write_text(DOCS / "ROW_DECODER_V2_SOURCE_BINDING.md", "\n".join(md_lines))
    write_csv(DOCS / "ROW_DECODER_V2_SOURCE_BINDING.csv", binding_rows)
    write_json(OUT_DIR / "ROW_DECODER_V2_SOURCE_BINDING.json", report)


if __name__ == "__main__":
    main()
