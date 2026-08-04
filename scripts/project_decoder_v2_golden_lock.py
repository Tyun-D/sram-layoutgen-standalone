#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = REPO_ROOT / "docs" / "DECODER_V2_STANDALONE_GOLDEN_LOCK.json"
OUT_MD = REPO_ROOT / "docs" / "DECODER_V2_STANDALONE_GOLDEN_LOCK.md"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


def _gate_summary(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    out: dict[str, Any] = {
        "path": str(path.relative_to(REPO_ROOT)),
        "sha256": sha256_file(path),
    }
    for key in (
        "passed",
        "routing_complete",
        "power_continuity_passed",
        "connectivity_passed",
        "foreign_net_passed",
        "pin_access_passed",
        "hierarchy_closure_passed",
        "child_immutability_passed",
        "deterministic_A_B_byte_identical",
        "negative_tests_passed",
    ):
        if key in payload:
            out[key] = payload[key]
    if "drc" in payload:
        out["drc_marker_count"] = payload["drc"].get("marker_count")
        out["drc_marker_report_path"] = payload["drc"].get("marker_report_path")
    if "geometry_fingerprint" in payload:
        out["bbox"] = payload["geometry_fingerprint"].get("bbox")
        out["geometry_digest"] = payload["geometry_fingerprint"].get("digest")
    return out


def main() -> int:
    decoder_dir = REPO_ROOT / "outputs" / "PROJECT_decoder_rebuild" / "current_supported_config"
    decoder_gds = decoder_dir / "decoder_rebuild_clean.gds"
    decoder_review = decoder_dir / "decoder_rebuild_review_atlas.gds"
    decoder_gate = decoder_dir / "DECODER_MACHINE_GATE.json"
    decoder_neg = decoder_dir / "DECODER_NEGATIVE_TEST_SUMMARY.json"
    decoder_route = decoder_dir / "decoder_route_geometry.json"
    decoder_pin_map = decoder_dir / "decoder_top_pin_map.json"
    decoder_manifest = decoder_dir / "decoder_bundle_manifest.json"
    decoder_hier = decoder_dir / "decoder_hierarchy_manifest.json"

    child_specs = [
        ("decoder_gate_cells_v2", REPO_ROOT / "outputs" / "PROJECT_decoder_gate_cells_v2_regen" / "current_supported_config", "DECODER_GATE_CELLS_V2_GATE.json"),
        ("row_decoder_v2", REPO_ROOT / "outputs" / "PROJECT_row_decoder_v2_regen" / "current_supported_config", "ROW_DECODER_V2_GATE.json"),
        ("wordline_decoder_v2", REPO_ROOT / "outputs" / "PROJECT_wordline_decoder_v2_regen" / "current_supported_config", "WORDLINE_DECODER_V2_GATE.json"),
    ]
    child_rows = []
    for name, root, gate_name in child_specs:
        gate_path = root / gate_name
        gds_candidates = sorted(root.glob("*.gds"))
        pin_contract_candidates = sorted(root.glob("*pin*.json"))
        child_rows.append(
            {
                "name": name,
                "gds_path": str(gds_candidates[0].relative_to(REPO_ROOT)) if gds_candidates else None,
                "gds_sha256": sha256_file(gds_candidates[0]) if gds_candidates else None,
                "gate": _gate_summary(gate_path),
                "pin_contract_path": str(pin_contract_candidates[0].relative_to(REPO_ROOT)) if pin_contract_candidates else None,
                "pin_contract_sha256": sha256_file(pin_contract_candidates[0]) if pin_contract_candidates else None,
            }
        )

    gate_payload = read_json(decoder_gate)
    manifest = read_json(decoder_manifest)
    route_payload = read_json(decoder_route)
    pin_payload = read_json(decoder_pin_map)
    neg_payload = read_json(decoder_neg)
    hierarchy_payload = read_json(decoder_hier)
    lock = {
        "scope": "decoder_v2_standalone_golden_lock",
        "classification": "PROJECT_DECODER_V2_STANDALONE_GOLDEN_BASELINE",
        "timestamp_utc": "2026-07-30T00:00:00Z",
        "git_head": git_head(),
        "decoder_top": {
            "gds_path": str(decoder_gds.relative_to(REPO_ROOT)),
            "gds_sha256": sha256_file(decoder_gds),
            "review_atlas_path": str(decoder_review.relative_to(REPO_ROOT)),
            "review_atlas_sha256": sha256_file(decoder_review),
            "machine_gate": _gate_summary(decoder_gate),
            "negative_summary_path": str(decoder_neg.relative_to(REPO_ROOT)),
            "negative_summary_sha256": sha256_file(decoder_neg),
            "negative_tests_passed": neg_payload.get("negative_tests_passed"),
            "negative_total_count": neg_payload.get("total_count"),
            "bbox": gate_payload.get("geometry_fingerprint", {}).get("bbox"),
            "top_pin_map_path": str(decoder_pin_map.relative_to(REPO_ROOT)),
            "top_pin_map_sha256": sha256_file(decoder_pin_map),
            "route_geometry_path": str(decoder_route.relative_to(REPO_ROOT)),
            "route_geometry_sha256": sha256_file(decoder_route),
            "bundle_manifest_path": str(decoder_manifest.relative_to(REPO_ROOT)),
            "bundle_manifest_sha256": sha256_file(decoder_manifest),
            "hierarchy_manifest_path": str(decoder_hier.relative_to(REPO_ROOT)),
            "hierarchy_manifest_sha256": sha256_file(decoder_hier),
            "stage_transforms": hierarchy_payload.get("instances", manifest.get("instances", [])),
            "route_strategy_fingerprint": hashlib.sha256(json.dumps(route_payload, sort_keys=True).encode("utf-8")).hexdigest(),
            "power_fingerprint": hashlib.sha256(json.dumps(manifest.get("endpoints_by_net", {}), sort_keys=True).encode("utf-8")).hexdigest(),
        },
        "logical_contract": {
            "path": "docs/DECODER_V2_LOGICAL_CONTRACT.json",
            "sha256": sha256_file(REPO_ROOT / "docs" / "DECODER_V2_LOGICAL_CONTRACT.json"),
        },
        "bit_mapping": {
            "path": "docs/DECODER_V2_BIT_MAPPING.csv",
            "sha256": sha256_file(REPO_ROOT / "docs" / "DECODER_V2_BIT_MAPPING.csv"),
        },
        "children": child_rows,
    }
    OUT_JSON.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Decoder V2 Standalone Golden Lock",
        "",
        f"- git_head: `{lock['git_head']}`",
        f"- decoder_gds: `{lock['decoder_top']['gds_path']}`",
        f"- decoder_gds_sha256: `{lock['decoder_top']['gds_sha256']}`",
        f"- decoder_review_atlas_sha256: `{lock['decoder_top']['review_atlas_sha256']}`",
        f"- bbox: `{lock['decoder_top']['bbox']}`",
        f"- gate_sha256: `{lock['decoder_top']['machine_gate']['sha256']}`",
        f"- route_geometry_sha256: `{lock['decoder_top']['route_geometry_sha256']}`",
        f"- top_pin_map_sha256: `{lock['decoder_top']['top_pin_map_sha256']}`",
        f"- bundle_manifest_sha256: `{lock['decoder_top']['bundle_manifest_sha256']}`",
        f"- hierarchy_manifest_sha256: `{lock['decoder_top']['hierarchy_manifest_sha256']}`",
        f"- negative_summary_sha256: `{lock['decoder_top']['negative_summary_sha256']}`",
        f"- route_strategy_fingerprint: `{lock['decoder_top']['route_strategy_fingerprint']}`",
        f"- power_fingerprint: `{lock['decoder_top']['power_fingerprint']}`",
        "",
        "## Child Locks",
        "",
    ]
    for row in child_rows:
        lines.extend(
            [
                f"### {row['name']}",
                "",
                f"- gds_path: `{row['gds_path']}`",
                f"- gds_sha256: `{row['gds_sha256']}`",
                f"- gate_path: `{row['gate']['path']}`",
                f"- gate_sha256: `{row['gate']['sha256']}`",
                f"- pin_contract_path: `{row['pin_contract_path']}`",
                f"- pin_contract_sha256: `{row['pin_contract_sha256']}`",
                "",
            ]
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
