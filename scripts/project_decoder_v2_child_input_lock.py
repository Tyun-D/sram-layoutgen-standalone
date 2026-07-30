from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
OUT_DIR = REPO_ROOT / "outputs" / "PROJECT_decoder_v2_child_input_lock" / "current_supported_config"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
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
    leaf_inventory = read_json(DOCS / "DECODER_V2_LEAF_SOURCE_INVENTORY.json")
    bit_rows = list(csv.DictReader((DOCS / "DECODER_V2_BIT_MAPPING.csv").open(encoding="utf-8")))

    leaf_by_name = {row["logical_name"]: row for row in leaf_inventory["assets"]}
    exact_leaf_bindings = {
        "inv": leaf_by_name["PINV_NW90_PW270_L50"],
        "and2": leaf_by_name["AND2_PNAND2_PINV_FPDK45"],
        "and3": leaf_by_name["AND3_PNAND3_PINV_FPDK45"],
        "wordline_driver": leaf_by_name["WORDLINEDRIVER_gen_wl_driver"],
    }

    row_templates = {
        "decoder_gate_cells_v2": [
            ["inv", "nand3_metadata_only", "and2", "and3"],
            ["decoder_leaf_gate_v2", "and2", "inv"],
        ],
        "row_decoder_v2": [
            ["inv", "nand3_metadata_only", "and3"],
            ["decoder_leaf_gate_v2", "inv", "nand3_metadata_only"],
        ],
        "wordline_decoder_v2": [
            ["inv", "nand3_metadata_only", "and3"],
            ["wordline_decoder_leaf_gate_v2", "inv", "and3"],
        ],
    }

    child_targets = []
    matrix_rows = []
    for child in logical["v2_child_targets"]:
        module = child["module"]
        role = child["logical_role"]
        if module == "decoder_gate_cells_v2":
            required = ["inv", "and2", "and3"]
            exported_ports = ["A0", "A1", "A2", "EN"] + [f"WL{i}_pre" for i in range(8)] + [f"WL{i}" for i in range(8)] + ["VDD", "VSS"]
        elif module == "row_decoder_v2":
            required = ["inv", "and3"]
            exported_ports = ["A0", "A1", "A2", "EN"] + [f"WL{i}" for i in range(8)] + ["VDD", "VSS"]
        else:
            required = ["inv", "and3", "wordline_driver"]
            exported_ports = ["A0", "A1", "A2", "EN"] + [f"DEC_WL{i}" for i in range(8)] + ["VDD", "VSS"]

        child_targets.append(
            {
                "module": module,
                "logical_role": role,
                "required_exact_leaf_sources": {
                    name: {
                        "logical_name": exact_leaf_bindings[name]["logical_name"],
                        "gds_sha256": exact_leaf_bindings[name]["gds_sha256"],
                        "source_authority": exact_leaf_bindings[name]["source_authority"],
                        "drc_marker_count": exact_leaf_bindings[name]["drc_marker_count"],
                    }
                    for name in required
                },
                "row_templates": row_templates[module],
                "exported_ports": exported_ports,
                "generator_status": "INPUT_LOCK_ONLY",
            }
        )
        for row in bit_rows:
            if row["logical_module"] != "DECODER3_8":
                continue
            matrix_rows.append(
                {
                    "child_module": module,
                    "logical_role": role,
                    "source_output": row["logical_port"],
                    "bit_index": row["bit_index"],
                    "predecode_expression": row["predecode_expression"],
                    "enabled_expression": row["enabled_expression"],
                }
            )

    payload = {
        "scope": "project_decoder_v2_child_input_lock",
        "git_head": git_head(),
        "logical_contract_path": str((DOCS / "DECODER_V2_LOGICAL_CONTRACT.json").resolve()),
        "leaf_source_inventory_path": str((DOCS / "DECODER_V2_LEAF_SOURCE_INVENTORY.json").resolve()),
        "bit_mapping_path": str((DOCS / "DECODER_V2_BIT_MAPPING.csv").resolve()),
        "child_targets": child_targets,
        "notes": [
            "This lock upgrades decoder v2 child generation inputs from wildcard candidate assets to exact leaf source references.",
            "nand3 remains metadata-only at this stage and must not be promoted to formal child output without regenerated geometry or exact clean gate substitution.",
            "wordline_decoder_v2 still depends on exact wordline-driver semantics and A/B/Z polarity from OpenYield WORDLINEDRIVER.",
        ],
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUT_DIR / "DECODER_V2_CHILD_INPUT_LOCK.json", payload)
    write_json(DOCS / "DECODER_V2_CHILD_INPUT_LOCK.json", payload)
    write_csv(
        DOCS / "DECODER_V2_CHILD_INPUT_MATRIX.csv",
        matrix_rows,
        ["child_module", "logical_role", "source_output", "bit_index", "predecode_expression", "enabled_expression"],
    )
    md_lines = [
        "# Decoder V2 Child Input Lock",
        "",
        f"- git_head: `{payload['git_head']}`",
        f"- logical_contract_path: `{payload['logical_contract_path']}`",
        f"- leaf_source_inventory_path: `{payload['leaf_source_inventory_path']}`",
        "",
        "## Child Targets",
        "",
    ]
    for child in child_targets:
        md_lines.append(f"- `{child['module']}` role=`{child['logical_role']}`")
        md_lines.append(f"  exported_ports=`{child['exported_ports']}`")
        md_lines.append(f"  row_templates=`{child['row_templates']}`")
        md_lines.append(f"  required_exact_leaf_sources=`{sorted(child['required_exact_leaf_sources'])}`")
    md_lines.extend(["", "## Notes", ""])
    md_lines.extend(f"- {item}" for item in payload["notes"])
    md_lines.append("")
    (DOCS / "DECODER_V2_CHILD_INPUT_LOCK.md").write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
