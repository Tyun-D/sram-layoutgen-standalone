from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.teamb_composite_helper import read_json


OPENYIELD_ROOT = Path("/data1/qujh/work/external/OpenYield")
DECODER_OUTPUT_ROOT = Path("outputs/PROJECT_decoder_rebuild/current_supported_config")

DECODER_CHILD_LIBRARY = {
    "decoder_gate_cells_v2": {
        "module": "decoder_gate_cells_v2",
        "legacy_module": "decoder_gate_cells",
        "gds_relpath": "outputs/PROJECT_decoder_gate_cells_v2_regen/current_supported_config/decoder_gate_cells_v2.gds",
        "root_cell_name": "decoder_gate_cells_v2",
        "pin_map_relpath": "outputs/PROJECT_decoder_gate_cells_v2_regen/current_supported_config/decoder_gate_cells_v2_pin_map.json",
        "gate_relpath": "outputs/PROJECT_decoder_gate_cells_v2_regen/current_supported_config/DECODER_GATE_CELLS_V2_GATE.json",
        "manifest_relpath": "outputs/PROJECT_decoder_gate_cells_v2_regen/current_supported_config/DECODER_GATE_CELLS_V2_MANIFEST.json",
        "summary_relpath": "outputs/PROJECT_decoder_gate_cells_v2_regen/current_supported_config/DECODER_GATE_CELLS_V2_SUMMARY.md",
    },
    "row_decoder_v2": {
        "module": "row_decoder_v2",
        "legacy_module": "row_decoder",
        "gds_relpath": "outputs/PROJECT_row_decoder_v2_regen/current_supported_config/row_decoder_v2.gds",
        "root_cell_name": "row_decoder_v2",
        "pin_map_relpath": "outputs/PROJECT_row_decoder_v2_regen/current_supported_config/row_decoder_v2_pin_map.json",
        "gate_relpath": "outputs/PROJECT_row_decoder_v2_regen/current_supported_config/ROW_DECODER_V2_GATE.json",
        "manifest_relpath": "outputs/PROJECT_row_decoder_v2_regen/current_supported_config/ROW_DECODER_V2_MANIFEST.json",
        "summary_relpath": "outputs/PROJECT_row_decoder_v2_regen/current_supported_config/ROW_DECODER_V2_SUMMARY.md",
    },
    "wordline_decoder_v2": {
        "module": "wordline_decoder_v2",
        "legacy_module": "wordline_decoder",
        "gds_relpath": "outputs/PROJECT_wordline_decoder_v2_regen/current_supported_config/wordline_decoder_v2.gds",
        "root_cell_name": "wordline_decoder_v2",
        "pin_map_relpath": "outputs/PROJECT_wordline_decoder_v2_regen/current_supported_config/wordline_decoder_v2_pin_map.json",
        "gate_relpath": "outputs/PROJECT_wordline_decoder_v2_regen/current_supported_config/WORDLINE_DECODER_V2_GATE.json",
        "manifest_relpath": "outputs/PROJECT_wordline_decoder_v2_regen/current_supported_config/WORDLINE_DECODER_V2_MANIFEST.json",
        "summary_relpath": "outputs/PROJECT_wordline_decoder_v2_regen/current_supported_config/WORDLINE_DECODER_V2_SUMMARY.md",
    },
}

DECODER_CHILDREN = (
    {
        "instance_name": "upper_enable_stage",
        "module": "decoder_gate_cells_v2",
        "role": "level0_enable_decode",
        "formal_connections": {"EN": "VDD", "A0": "VSS", "A1": "VSS", "A2": "A3"},
        "used_outputs": ["WL0", "WL1"],
        "top_outputs": [],
    },
    {
        "instance_name": "lower_wordline_stage_0",
        "module": "decoder_gate_cells_v2",
        "role": "level1_wordline_decode_low",
        "formal_connections": {"EN": "EN_0_0_0", "A0": "A2", "A1": "A1", "A2": "A0"},
        "used_outputs": [f"WL{i}" for i in range(8)],
        "top_outputs": [f"WL{i}" for i in range(8)],
    },
    {
        "instance_name": "lower_wordline_stage_1",
        "module": "decoder_gate_cells_v2",
        "role": "level1_wordline_decode_high",
        "formal_connections": {"EN": "EN_0_0_1", "A0": "A2", "A1": "A1", "A2": "A0"},
        "used_outputs": [f"WL{i}" for i in range(8)],
        "top_outputs": [f"WL{i}" for i in range(8, 16)],
    },
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_text(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _pin_names(pin_map_path: Path) -> list[str]:
    payload = read_json(pin_map_path)
    if isinstance(payload, dict):
        return sorted(str(name) for name in payload.keys())
    return [str(row["name"]) for row in payload.get("pins", [])]


def _bbox_from_gds(gds_path: Path, root_cell_name: str) -> list[float]:
    lib = gdstk.read_gds(gds_path)
    cell = next(c for c in lib.cells if c.name == root_cell_name)
    bbox = cell.bounding_box()
    assert bbox is not None
    return [
        round(float(bbox[0][0]), 6),
        round(float(bbox[0][1]), 6),
        round(float(bbox[1][0]), 6),
        round(float(bbox[1][1]), 6),
    ]


def build_decoder_contract_lock(repo_root: Path) -> dict[str, Any]:
    openyield_commit = _git_text(OPENYIELD_ROOT, "rev-parse", "HEAD")
    decoder_blob = _git_text(OPENYIELD_ROOT, "hash-object", "sram_compiler/subcircuits/decoder.py")
    wl_driver_blob = _git_text(OPENYIELD_ROOT, "hash-object", "sram_compiler/subcircuits/wordline_driver.py")
    formal_rows = (repo_root / "docs" / "FORMAL_SRAM_CONFIG_INVENTORY.csv").read_text(encoding="utf-8").splitlines()
    selected_config = "formal_16x16_wpr1"
    children = []
    for child in DECODER_CHILDREN:
        library_row = DECODER_CHILD_LIBRARY[child["module"]]
        gds_path = repo_root / library_row["gds_relpath"]
        pin_map_path = repo_root / library_row["pin_map_relpath"]
        pins = _pin_names(pin_map_path)
        children.append(
            {
                "instance_name": child["instance_name"],
                "role": child["role"],
                "module": child["module"],
                "legacy_module": library_row["legacy_module"],
                "root_cell_name": library_row["root_cell_name"],
                "gds_path": str(gds_path.resolve()),
                "gds_sha256": sha256_file(gds_path),
                "bbox": _bbox_from_gds(gds_path, library_row["root_cell_name"]),
                "pin_map_path": str(pin_map_path.resolve()),
                "generator_manifest_path": str((repo_root / library_row["manifest_relpath"]).resolve()),
                "gate_path": str((repo_root / library_row["gate_relpath"]).resolve()),
                "summary_path": str((repo_root / library_row["summary_relpath"]).resolve()),
                "pin_names": pins,
                "pin_abstraction_complete": not any("[*]" in pin for pin in pins),
                "formal_connections": child["formal_connections"],
                "used_outputs": child["used_outputs"],
                "top_outputs": child["top_outputs"],
            }
        )
    return {
        "scope": "project_decoder_rebuild_contract_lock",
        "selected_config_id": selected_config,
        "selected_config_status": "CURRENT_SOURCE_BACKED",
        "top_cell_name": "PROJECT_DECODER_REBUILD_16X16",
        "route_strategy": {
            "topology": "decoder_cascade_1_plus_2",
            "level0_enable_strategy": "decoder_gate_cells_v2_with_A0_A1_tied_to_VSS_and_EN_tied_to_VDD",
            "level1_wordline_strategy": "two_decoder_gate_cells_v2_instances_driven_by_level0_WL0_WL1",
            "note": "fresh-run cascade rebuild strategy derived from OpenYield DECODER_CASCADE(16)",
        },
        "openyield_authority": {
            "repo_root": str(OPENYIELD_ROOT.resolve()),
            "commit": openyield_commit,
            "decoder_py_blob": decoder_blob,
            "wordline_driver_py_blob": wl_driver_blob,
        },
        "semantic_contract_paths": [
            str((repo_root / "docs/mapping/openyield_decoder_wordline_semantic_contract.json").resolve()),
            str((repo_root / "docs/openyield_module_contracts.md").resolve()),
        ],
        "child_assets": children,
        "expected_top_pins": {
            "inputs": ["A0", "A1", "A2", "A3"],
            "outputs": [f"WL{i}" for i in range(16)],
            "power": ["VDD", "VSS"],
        },
        "known_contract_limitations": [
            "The selected child assets are project-owned regenerated v2 child candidates rather than historical decoder-top signoff assets.",
            "This contract lock reflects the OpenYield DECODER_CASCADE topology for 16 rows and supersedes the earlier three-module side-by-side placeholder composition.",
            f"Formal inventory snapshot lines: {len(formal_rows)}",
        ],
    }


def build_decoder_contract_markdown(contract: dict[str, Any]) -> str:
    lines = [
        "# Decoder Rebuild Contract Lock",
        "",
        f"- selected_config_id: `{contract['selected_config_id']}`",
        f"- top_cell_name: `{contract['top_cell_name']}`",
        f"- openyield_commit: `{contract['openyield_authority']['commit']}`",
        f"- decoder_py_blob: `{contract['openyield_authority']['decoder_py_blob']}`",
        f"- wordline_driver_py_blob: `{contract['openyield_authority']['wordline_driver_py_blob']}`",
        f"- topology: `{contract['route_strategy']['topology']}`",
        f"- level0_enable_strategy: `{contract['route_strategy']['level0_enable_strategy']}`",
        f"- level1_wordline_strategy: `{contract['route_strategy']['level1_wordline_strategy']}`",
        "",
        "## Child Assets",
        "",
    ]
    for row in contract["child_assets"]:
        lines.extend(
            [
                f"- `{row['instance_name']}`",
                f"  - module: `{row['module']}`",
                f"  - role: `{row['role']}`",
                f"  - gds_sha256: `{row['gds_sha256']}`",
                f"  - pin_names: `{row['pin_names']}`",
                f"  - pin_abstraction_complete: `{row['pin_abstraction_complete']}`",
                f"  - formal_connections: `{row['formal_connections']}`",
            ]
        )
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in contract["known_contract_limitations"])
    lines.append("")
    return "\n".join(lines)
