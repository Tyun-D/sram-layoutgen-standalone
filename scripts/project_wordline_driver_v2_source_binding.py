#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
OUT_DIR = REPO_ROOT / "outputs" / "PROJECT_wordline_driver_v2_source_binding" / "current_supported_config"


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
    pinv_pinmap = read_json(
        REPO_ROOT
        / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells/PINV_NW90_PW270_L50/PINV_NW90_PW270_L50_pin_map.json"
    )
    pnand2_pinmap = read_json(
        Path("/data1/qujh/work/sram_layoutgen_step45_clean/outputs/TeamB_PNAND2_reference_demo/current_supported_config/PNAND2_pin_map.json")
    )
    binding_rows = [
        {
            "instance_name": "pnand2_stage",
            "logical_child_type": "PNAND2",
            "resolved_physical_cell_name": "PNAND2_NW180_PW270_L50_FPDK45",
            "child_pin_order": json.dumps(["VDD", "VSS", "A", "B", "Z"]),
            "parent_net_connections": json.dumps(["VDD", "VSS", "A", "B", "zb_int"]),
            "pin_map_pin_names": json.dumps(sorted(pnand2_pinmap.keys())),
            "binding_status": "APPROVED_EXACT_BINDING",
        },
        {
            "instance_name": "inv_stage",
            "logical_child_type": "PINV",
            "resolved_physical_cell_name": "PINV_NW90_PW270_L50",
            "child_pin_order": json.dumps(["VDD", "VSS", "A", "Z"]),
            "parent_net_connections": json.dumps(["VDD", "VSS", "zb_int", "Z"]),
            "pin_map_pin_names": json.dumps(sorted(pinv_pinmap.keys())),
            "binding_status": "APPROVED_EXACT_BINDING",
        },
    ]
    report = {
        "scope": "project_wordline_driver_v2_source_binding",
        "git_head": git_head(),
        "source_authority": {
            "logical_source_file": "/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/wordline_driver.py",
            "logical_commit": "1c34428d8b913963c4971d093b1a7c2df97a2509",
            "exact_leafs": [
                "PNAND2_NW180_PW270_L50_FPDK45",
                "PINV_NW90_PW270_L50",
            ],
        },
        "binding_rows": binding_rows,
        "top_ports": ["A", "B", "Z", "VDD", "VSS"],
    }
    write_json(DOCS / "WORDLINE_DRIVER_V2_SOURCE_BINDING.json", report)
    write_text(
        DOCS / "WORDLINE_DRIVER_V2_SOURCE_BINDING.md",
        "\n".join(
            [
                "# Wordline Driver V2 Source Binding",
                "",
                f"- git_head: `{report['git_head']}`",
                "- exact_topology: `PNAND2 + PINV`",
                "- top_ports: `A B Z VDD VSS`",
                "",
            ]
        ),
    )
    write_csv(DOCS / "WORDLINE_DRIVER_V2_SOURCE_BINDING.csv", binding_rows)
    write_json(OUT_DIR / "WORDLINE_DRIVER_V2_SOURCE_BINDING.json", report)


if __name__ == "__main__":
    main()
