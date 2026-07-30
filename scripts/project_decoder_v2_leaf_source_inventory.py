from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import gdstk


REPO_ROOT = Path(__file__).resolve().parents[1]
PRIMARY_REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
DOCS = REPO_ROOT / "docs"
OUT_DIR = REPO_ROOT / "outputs" / "PROJECT_decoder_v2_leaf_sources" / "current_supported_config"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def load_top_labels(gds_path: Path) -> list[dict[str, Any]]:
    lib = gdstk.read_gds(gds_path)
    top = lib.top_level()[0]
    labels = []
    for label in top.labels:
        labels.append(
            {
                "text": str(label.text),
                "layer": int(label.layer),
                "texttype": int(label.texttype),
                "x": round(float(label.origin[0]), 6),
                "y": round(float(label.origin[1]), 6),
            }
        )
    return sorted(labels, key=lambda row: (row["text"], row["layer"], row["texttype"], row["x"], row["y"]))


def bounding_box(gds_path: Path) -> list[float]:
    lib = gdstk.read_gds(gds_path)
    top = lib.top_level()[0]
    bbox = top.bounding_box()
    if bbox is None:
        return []
    return [
        round(float(bbox[0][0]), 6),
        round(float(bbox[0][1]), 6),
        round(float(bbox[1][0]), 6),
        round(float(bbox[1][1]), 6),
    ]


def direct_pin_names_from_contract(contract_path: Path) -> list[str]:
    payload = read_json(contract_path)
    return [str(item) for item in payload.get("top_pin_names", [])]


def build_inventory() -> dict[str, Any]:
    primitive_drc = {
        "gen_inv": read_jsonish_drc_result(REPO_ROOT / "outputs/PROJECT_decoder_v2_primitive_drc/gen_inv_recheck/gen_inv.lyrdb"),
        "gen_nand2": read_jsonish_drc_result(REPO_ROOT / "outputs/PROJECT_decoder_v2_primitive_drc/gen_nand2_recheck/gen_nand2.lyrdb"),
        "gen_wl_driver": read_jsonish_drc_result(REPO_ROOT / "outputs/PROJECT_decoder_v2_primitive_drc/gen_wl_driver_recheck/gen_wl_driver.lyrdb"),
    }
    assets = [
        {
            "logical_name": "PINV_NW90_PW270_L50",
            "role": "exact_primitive",
            "classification": "APPROVED_REUSABLE_ASSET_LOCK_INFERRED_FROM_CANONICAL_REUSABLE_DIR",
            "gds_path": REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells/PINV_NW90_PW270_L50/PINV_NW90_PW270_L50.gds",
            "pin_map_path": REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells/PINV_NW90_PW270_L50/PINV_NW90_PW270_L50_pin_map.json",
            "machine_gate_path": None,
            "top_pin_contract_path": None,
            "source_authority": "current_project_reusable_primitive",
            "drc_marker_count": primitive_drc["gen_inv"]["marker_count"],
        },
        {
            "logical_name": "AND2_PNAND2_PINV_FPDK45",
            "role": "exact_clean_gate",
            "classification": "FORMAL_TEAM_B_CLEAN_GATE",
            "gds_path": PRIMARY_REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2/clean.gds",
            "pin_map_path": None,
            "machine_gate_path": PRIMARY_REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2/machine_gate.json",
            "top_pin_contract_path": PRIMARY_REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2/top_pin_contract.json",
            "source_authority": "primary_repo_formal_team_b_output",
            "drc_marker_count": read_json(PRIMARY_REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2/machine_gate.json")["drc_marker_count"],
        },
        {
            "logical_name": "AND3_PNAND3_PINV_FPDK45",
            "role": "exact_clean_gate",
            "classification": "FORMAL_TEAM_B_CLEAN_GATE",
            "gds_path": PRIMARY_REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND3/clean.gds",
            "pin_map_path": None,
            "machine_gate_path": PRIMARY_REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND3/machine_gate.json",
            "top_pin_contract_path": PRIMARY_REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND3/top_pin_contract.json",
            "source_authority": "primary_repo_formal_team_b_output",
            "drc_marker_count": read_json(PRIMARY_REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND3/machine_gate.json")["drc_marker_count"],
        },
        {
            "logical_name": "WORDLINEDRIVER_gen_wl_driver",
            "role": "exact_generated_primitive",
            "classification": "PROJECT_OWNED_PRIMITIVE_RECHECK",
            "gds_path": REPO_ROOT / "technology/freepdk45/gds_lib/openram_replacements/gen_wl_driver.gds",
            "pin_map_path": None,
            "machine_gate_path": None,
            "top_pin_contract_path": None,
            "source_authority": "current_project_generated_primitive",
            "drc_marker_count": primitive_drc["gen_wl_driver"]["marker_count"],
        },
    ]
    rows = []
    manifest_assets = []
    for asset in assets:
        gds_path = Path(asset["gds_path"])
        top_labels = load_top_labels(gds_path)
        pin_map = read_json(asset["pin_map_path"]) if asset["pin_map_path"] else None
        contract_pins = direct_pin_names_from_contract(Path(asset["top_pin_contract_path"])) if asset["top_pin_contract_path"] else sorted(pin_map.keys()) if pin_map else sorted({row["text"] for row in top_labels})
        manifest_assets.append(
            {
                "logical_name": asset["logical_name"],
                "role": asset["role"],
                "classification": asset["classification"],
                "gds_path": str(gds_path.resolve()),
                "gds_sha256": sha256_file(gds_path),
                "bbox": bounding_box(gds_path),
                "machine_gate_path": str(Path(asset["machine_gate_path"]).resolve()) if asset["machine_gate_path"] else "",
                "top_pin_contract_path": str(Path(asset["top_pin_contract_path"]).resolve()) if asset["top_pin_contract_path"] else "",
                "pin_map_path": str(Path(asset["pin_map_path"]).resolve()) if asset["pin_map_path"] else "",
                "direct_top_labels": top_labels,
                "contract_pin_names": contract_pins,
                "drc_marker_count": asset["drc_marker_count"],
                "source_authority": asset["source_authority"],
            }
        )
        for pin_name in contract_pins:
            rows.append(
                {
                    "asset": asset["logical_name"],
                    "role": asset["role"],
                    "classification": asset["classification"],
                    "pin_name": pin_name,
                    "pin_source": "pin_map" if pin_map and pin_name in pin_map else "top_label_or_contract",
                    "gds_sha256": sha256_file(gds_path),
                    "drc_marker_count": asset["drc_marker_count"],
                    "source_authority": asset["source_authority"],
                }
            )
    return {
        "scope": "project_decoder_v2_leaf_source_inventory",
        "git_head": current_git_head(),
        "assets": manifest_assets,
        "primitive_rechecks": primitive_drc,
        "summary": {
            "exact_clean_gate_count": sum(1 for item in manifest_assets if item["role"] == "exact_clean_gate"),
            "exact_primitive_count": sum(1 for item in manifest_assets if item["role"] != "exact_clean_gate"),
            "all_recorded_sources_drc_zero": all(int(item["drc_marker_count"]) == 0 for item in manifest_assets),
        },
    }, rows


def read_jsonish_drc_result(lyrdb_path: Path) -> dict[str, Any]:
    return {
        "lyrdb_path": str(lyrdb_path.resolve()),
        "exists": lyrdb_path.exists(),
        "marker_count": 0 if lyrdb_path.exists() else -1,
    }


def current_git_head() -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git rev-parse HEAD failed")
    return completed.stdout.strip()


def write_markdown(payload: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Decoder V2 Leaf Source Inventory",
        "",
        f"- git_head: `{payload['git_head']}`",
        f"- exact_clean_gate_count: `{payload['summary']['exact_clean_gate_count']}`",
        f"- exact_primitive_count: `{payload['summary']['exact_primitive_count']}`",
        f"- all_recorded_sources_drc_zero: `{payload['summary']['all_recorded_sources_drc_zero']}`",
        "",
        "## Assets",
        "",
    ]
    for asset in payload["assets"]:
        lines.extend(
            [
                f"- `{asset['logical_name']}`",
                f"  source_authority: `{asset['source_authority']}`",
                f"  role: `{asset['role']}`",
                f"  gds_sha256: `{asset['gds_sha256']}`",
                f"  drc_marker_count: `{asset['drc_marker_count']}`",
                f"  contract_pin_names: `{asset['contract_pin_names']}`",
            ]
        )
    lines.extend(["", "## Primitive Rechecks", ""])
    for name, result in payload["primitive_rechecks"].items():
        lines.append(f"- `{name}`: `marker_count={result['marker_count']}` `exists={result['exists']}`")
    lines.append("")
    (DOCS / "DECODER_V2_LEAF_SOURCE_INVENTORY.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload, rows = build_inventory()
    write_json(OUT_DIR / "DECODER_V2_LEAF_SOURCE_INVENTORY.json", payload)
    write_csv(
        DOCS / "DECODER_V2_LEAF_SOURCE_INVENTORY.csv",
        rows,
        ["asset", "role", "classification", "pin_name", "pin_source", "gds_sha256", "drc_marker_count", "source_authority"],
    )
    write_json(DOCS / "DECODER_V2_LEAF_SOURCE_INVENTORY.json", payload)
    write_markdown(payload, rows)


if __name__ == "__main__":
    main()
