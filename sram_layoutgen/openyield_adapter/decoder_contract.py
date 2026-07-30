from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.teamb_composite_helper import read_json


OPENYIELD_ROOT = Path("/data1/qujh/work/external/OpenYield")
DECODER_OUTPUT_ROOT = Path("outputs/PROJECT_decoder_rebuild/current_supported_config")

DECODER_CHILDREN = (
    ("decoder_gate_cells", "decoder_gate_cells.gds", "decoder_gate_cells"),
    ("row_decoder", "row_decoder.gds", "row_decoder"),
    ("wordline_decoder", "wordline_decoder.gds", "wordline_decoder"),
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


def _pin_names(repo_root: Path, module: str) -> list[str]:
    payload = read_json(repo_root / "outputs" / "openyield_module_gds" / module / "pins.json")
    return [str(row["name"]) for row in payload.get("pins", [])]


def build_decoder_contract_lock(repo_root: Path) -> dict[str, Any]:
    openyield_commit = _git_text(OPENYIELD_ROOT, "rev-parse", "HEAD")
    decoder_blob = _git_text(OPENYIELD_ROOT, "hash-object", "sram_compiler/subcircuits/decoder.py")
    wl_driver_blob = _git_text(OPENYIELD_ROOT, "hash-object", "sram_compiler/subcircuits/wordline_driver.py")
    formal_rows = (repo_root / "docs" / "FORMAL_SRAM_CONFIG_INVENTORY.csv").read_text(encoding="utf-8").splitlines()
    selected_config = "formal_16x16_wpr1"
    children = []
    for module, gds_name, root_cell in DECODER_CHILDREN:
        module_dir = repo_root / "outputs" / "openyield_module_gds" / module
        gds_path = module_dir / gds_name
        pins = _pin_names(repo_root, module)
        children.append(
            {
                "module": module,
                "root_cell_name": root_cell,
                "gds_path": str(gds_path.resolve()),
                "gds_sha256": sha256_file(gds_path),
                "bbox_path": str((module_dir / "bbox.json").resolve()),
                "pin_map_path": str((module_dir / "pins.json").resolve()),
                "generator_manifest_path": str((module_dir / "generator_manifest.json").resolve()),
                "rail_report_path": str((module_dir / "rail_report.json").resolve()),
                "pin_names": pins,
                "pin_abstraction_complete": not any("[*]" in pin for pin in pins),
            }
        )
    return {
        "scope": "project_decoder_rebuild_contract_lock",
        "selected_config_id": selected_config,
        "selected_config_status": "CURRENT_SOURCE_BACKED",
        "top_cell_name": "PROJECT_DECODER_REBUILD_16X16",
        "route_strategy": {
            "en_strategy": "horizontal_m3_bus",
            "wl_pre_strategy": "vertical_m2_link",
            "note": "fresh-run rebuild strategy; not a claim of historical 24-marker equivalence",
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
            "inputs": ["A0", "A1", "A2", "A3", "EN"],
            "outputs": [f"WL{i}" for i in range(16)],
            "power": ["VDD", "VSS"],
        },
        "known_contract_limitations": [
            "All currently approved decoder child module pin maps export wildcard bus labels rather than bit-exact pins.",
            "The selected child assets are candidate module geometry, not previously closed decoder top-level routing.",
            "This contract lock is sufficient for executable rebuild/validation, but not sufficient to claim pre-validated decoder route closure.",
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
        f"- en_strategy: `{contract['route_strategy']['en_strategy']}`",
        f"- wl_pre_strategy: `{contract['route_strategy']['wl_pre_strategy']}`",
        "",
        "## Child Assets",
        "",
    ]
    for row in contract["child_assets"]:
        lines.extend(
            [
                f"- `{row['module']}`",
                f"  - gds_sha256: `{row['gds_sha256']}`",
                f"  - pin_names: `{row['pin_names']}`",
                f"  - pin_abstraction_complete: `{row['pin_abstraction_complete']}`",
            ]
        )
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in contract["known_contract_limitations"])
    lines.append("")
    return "\n".join(lines)
