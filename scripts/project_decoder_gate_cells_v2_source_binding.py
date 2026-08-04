#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
OUT_DIR = REPO_ROOT / "outputs" / "PROJECT_decoder_gate_cells_v2_source_binding" / "current_supported_config"


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
    row_binding = read_json(DOCS / "ROW_DECODER_V2_SOURCE_BINDING.json")

    output_map = {int(row["bit_index"]): row for row in bit_rows}
    binding_rows = row_binding["binding_rows"]

    report = {
        "scope": "project_decoder_gate_cells_v2_source_binding",
        "git_head": git_head(),
        "logical_contract_path": str((DOCS / "DECODER_V2_LOGICAL_CONTRACT.json").resolve()),
        "bit_mapping_path": str((DOCS / "DECODER_V2_BIT_MAPPING.csv").resolve()),
        "row_decoder_binding_reuse_path": str((DOCS / "ROW_DECODER_V2_SOURCE_BINDING.json").resolve()),
        "physical_sources": row_binding["physical_sources"],
        "decoder3_8_leaf_topology": row_binding["decoder3_8_leaf_topology"],
        "binding_row_count": len(binding_rows),
        "top_ports": next(item["ports"] for item in logical["v2_child_targets"] if item["module"] == "decoder_gate_cells_v2"),
        "binding_rows": binding_rows,
        "predecode_outputs": [
            {
                "net": f"WL{bit}_pre",
                "expression": output_map[bit]["predecode_expression"],
                "source_pointer": output_map[bit]["source_line_or_ast_pointer"],
            }
            for bit in range(8)
        ],
    }
    md_lines = [
        "# Decoder Gate Cells V2 Source Binding",
        "",
        f"- git_head: `{report['git_head']}`",
        "- exact_topology: `3xINV + 8xAND3 + 8xAND2`",
        f"- binding_row_count: `{len(binding_rows)}`",
        "- source_authority: `OpenYield DECODER3_8 exact topology + row_decoder_v2 exact instance binding + exact leaf pin maps`",
        "- exported_ports: `A0 A1 A2 EN WL0_pre..WL7_pre WL0..WL7 VDD VSS`",
        "",
    ]
    write_json(DOCS / "DECODER_GATE_CELLS_V2_SOURCE_BINDING.json", report)
    write_text(DOCS / "DECODER_GATE_CELLS_V2_SOURCE_BINDING.md", "\n".join(md_lines))
    write_csv(DOCS / "DECODER_GATE_CELLS_V2_SOURCE_BINDING.csv", binding_rows)
    write_json(OUT_DIR / "DECODER_GATE_CELLS_V2_SOURCE_BINDING.json", report)


if __name__ == "__main__":
    main()
