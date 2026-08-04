#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import gdstk

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.verification.component_witness import (
    build_owner_index,
    build_shape_graph,
    shortest_cross_net_witness,
)
DOCS = REPO_ROOT / "docs"

TOP_CANDIDATES = [
    "baseline_v2_long_strip",
    "candidate_a_compact_folded",
    "candidate_b_wl_oriented",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


def bbox_of_gds(path: Path) -> list[float]:
    lib = gdstk.read_gds(path)
    top = lib.top_level()[0]
    bbox = top.bounding_box()
    assert bbox is not None
    return [round(float(bbox[0][0]), 6), round(float(bbox[0][1]), 6), round(float(bbox[1][0]), 6), round(float(bbox[1][1]), 6)]


def top_input_lock() -> None:
    rows = []
    for cid in TOP_CANDIDATES:
        root = REPO_ROOT / "outputs" / "PROJECT_decoder_top_v3" / cid
        gate = read_json(root / "machine_gate.json")
        pin_map = root / "pin_map.json"
        child_ids = read_json(root / "child_candidate_ids.json")
        determinism = read_json(root / "determinism.json")
        rows.append(
            {
                "candidate_id": cid,
                "top_gds_path": str((root / "clean.gds").relative_to(REPO_ROOT)),
                "top_gds_sha256": sha256_file(root / "clean.gds"),
                "top_bbox": bbox_of_gds(root / "clean.gds"),
                "pin_map_path": str(pin_map.relative_to(REPO_ROOT)),
                "pin_map_sha256": sha256_file(pin_map),
                "child_candidate_ids_path": str((root / "child_candidate_ids.json").relative_to(REPO_ROOT)),
                "child_candidate_ids_sha256": sha256_file(root / "child_candidate_ids.json"),
                "child_candidate_ids": child_ids,
                "standalone_machine_gate_path": str((root / "machine_gate.json").relative_to(REPO_ROOT)),
                "standalone_machine_gate_sha256": sha256_file(root / "machine_gate.json"),
                "standalone_drc_marker_count": gate["drc_marker_count"],
                "standalone_passed": gate["passed"],
                "determinism_path": str((root / "determinism.json").relative_to(REPO_ROOT)),
                "determinism_sha256": sha256_file(root / "determinism.json"),
                "determinism_reference_sha256": determinism.get("reference_sha256"),
            }
        )
    payload = {
        "scope": "decoder_top_v3_golden_input_lock",
        "generated_at": "2026-07-31T00:00:00Z",
        "git_head": git_head(),
        "rows": rows,
    }
    write_json(DOCS / "DECODER_TOP_V3_GOLDEN_INPUT_LOCK.json", payload)
    md = [
        "# Decoder Top V3 Golden Input Lock",
        "",
        f"- git_head: `{payload['git_head']}`",
        "",
    ]
    for row in rows:
        md.extend(
            [
                f"## {row['candidate_id']}",
                "",
                f"- top_gds_sha256: `{row['top_gds_sha256']}`",
                f"- top_bbox: `{row['top_bbox']}`",
                f"- pin_map_sha256: `{row['pin_map_sha256']}`",
                f"- child_candidate_ids_sha256: `{row['child_candidate_ids_sha256']}`",
                f"- standalone_machine_gate_sha256: `{row['standalone_machine_gate_sha256']}`",
                f"- standalone_drc_marker_count: `{row['standalone_drc_marker_count']}`",
                f"- determinism_sha256: `{row['determinism_sha256']}`",
                f"- determinism_reference_sha256: `{row['determinism_reference_sha256']}`",
                "",
            ]
        )
    write_text(DOCS / "DECODER_TOP_V3_GOLDEN_INPUT_LOCK.md", "\n".join(md))


def _route_inventory(candidate_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    top_route = read_json(REPO_ROOT / "outputs" / "PROJECT_decoder_top_v3" / candidate_id / "route_geometry.json")
    integ_route = read_json(REPO_ROOT / "outputs" / "PROJECT_decoder_wl_array_integration_shell" / candidate_id / "route_geometry.json")
    route_authority = {
        "candidate_id": candidate_id,
        "top_decoder_route_geometry_path": str((REPO_ROOT / "outputs" / "PROJECT_decoder_top_v3" / candidate_id / "route_geometry.json").relative_to(REPO_ROOT)),
        "integration_route_geometry_path": str((REPO_ROOT / "outputs" / "PROJECT_decoder_wl_array_integration_shell" / candidate_id / "route_geometry.json").relative_to(REPO_ROOT)),
        "routes": [],
    }
    track_rows: list[dict[str, Any]] = []

    def add_routes(payload: dict[str, Any], owner: str) -> None:
        for route_group, route_map in payload.items():
            if not isinstance(route_map, dict):
                continue
            for route_id, route_row in route_map.items():
                if not isinstance(route_row, dict):
                    continue
                net = route_id if route_group != "power_routes" else route_id.split("_")[-1]
                track_index = None
                for key, val in route_row.items():
                    if isinstance(val, dict) and {"lx", "by", "rx", "uy"} <= set(val):
                        layer = "m1" if "m1" in key else "m2" if "m2" in key else "m3" if "m3" in key else "via1" if "via1" in key else "via2" if "via2" in key else "unknown"
                        if layer in {"m2", "m3"} and track_index is None:
                            track_index = round((val["by"] + val["uy"]) * 0.5, 6)
                        route_authority["routes"].append(
                            {
                                "route_id": route_id,
                                "route_group": route_group,
                                "owner": owner,
                                "net": net,
                                "segment_key": key,
                                "layer": layer,
                                "segment_bbox": [val["lx"], val["by"], val["rx"], val["uy"]],
                                "via_ids": [],
                            }
                        )
                track_rows.append(
                    {
                        "route_id": route_id,
                        "route_group": route_group,
                        "owner": owner,
                        "net": net,
                        "track_index": track_index,
                    }
                )

    add_routes(top_route, "TOP_DECODER_ROUTE")
    add_routes(integ_route, "PARENT_INTEGRATION_ROUTER")
    return route_authority, track_rows


def _marker_inventory(candidate_id: str, ownership_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    lyrdb = REPO_ROOT / "outputs" / "PROJECT_decoder_wl_array_integration_shell" / candidate_id / "drc" / f"{candidate_id}_integration_shell.lyrdb"
    root = ET.fromstring(lyrdb.read_text(encoding="utf-8"))
    categories = {}
    for category in root.findall("./categories/category"):
        name = category.findtext("name")
        description = category.findtext("description")
        if name:
            categories[name] = description

    ownership_by_bbox = {}
    for row in ownership_rows:
        ownership_by_bbox.setdefault(tuple(row["shape_bbox"]), []).append(row)

    items = []
    edge_pair_re = re.compile(
        r"edge-pair:\s*\(([-0-9.]+),([-0-9.]+);([-0-9.]+),([-0-9.]+)\)\|\(([-0-9.]+),([-0-9.]+);([-0-9.]+),([-0-9.]+)\)"
    )
    for item in root.findall(".//item"):
        category = item.findtext("category")
        cell = item.findtext("cell")
        visited = []
        for value in item.findall(".//value"):
            text = (value.text or "").strip()
            if text:
                visited.append(text)
        bbox = None
        for entry in visited:
            if entry.startswith("box:"):
                coords = [float(part) for part in entry.split(":", 1)[1].split(",")]
                if len(coords) == 4:
                    bbox = coords
                    break
            match = edge_pair_re.match(entry)
            if match:
                coords = [float(value) for value in match.groups()]
                xs = [coords[0], coords[2], coords[4], coords[6]]
                ys = [coords[1], coords[3], coords[5], coords[7]]
                bbox = [min(xs), min(ys), max(xs), max(ys)]
                break
        if bbox is None:
            continue
        owners = []
        for shape_bbox, rows in ownership_by_bbox.items():
            sx0, sy0, sx1, sy1 = shape_bbox
            if not (sx1 < bbox[0] or bbox[2] < sx0 or sy1 < bbox[1] or bbox[3] < sy0):
                owners.extend(rows)
        owner_nets = sorted({row["net"] for row in owners})
        owner_routes = sorted({row["route_id"] for row in owners})
        items.append(
            {
                "candidate_id": candidate_id,
                "rule": category,
                "rule_text": categories.get(category),
                "cell": cell,
                "bbox": bbox,
                "shape_owner_count": len(owners),
                "shape_owners": owner_nets,
                "route_ids": owner_routes,
                "same_source_as_merge_witness": False,
            }
        )
    clusters: dict[str, Any] = {}
    for row in items:
        cluster = clusters.setdefault(
            row["rule"],
            {"rule": row["rule"], "rule_text": row["rule_text"], "count": 0, "route_ids": set(), "shape_owners": set()},
        )
        cluster["count"] += 1
        cluster["route_ids"].update(row["route_ids"])
        cluster["shape_owners"].update(row["shape_owners"])
    for cluster in clusters.values():
        cluster["route_ids"] = sorted(cluster["route_ids"])
        cluster["shape_owners"] = sorted(cluster["shape_owners"])
    return items, {"candidate_id": candidate_id, "clusters": sorted(clusters.values(), key=lambda row: row["rule"])}


def _write_rule_text() -> None:
    rule_lines = [
        "# Decoder Integration DRC Rule Text",
        "",
        "- `METAL1.2`: `Minimum spacing of metal1 : 65nm`",
        "- `VIA1.1`: `Minimum/Maximum width of via1 : 65nm`",
        "- `VIA1.2`: `Minimum spacing of via1 : 75nm`",
        "- `METAL2.2`: `Minimum spacing of intermediate metal2 : 70nm`",
        "- `VIA2.1`: `Minimum/Maximum width of via2 : 65nm`",
        "",
        "Source: `technology/freepdk45/tech/freepdk45.lydrc`",
    ]
    write_text(DOCS / "DECODER_INTEGRATION_DRC_RULE_TEXT.md", "\n".join(rule_lines))


def candidate_a_witness() -> None:
    candidate_id = "candidate_a_compact_folded"
    integ_root = REPO_ROOT / "outputs" / "PROJECT_decoder_wl_array_integration_shell" / candidate_id
    top_root = REPO_ROOT / "outputs" / "PROJECT_decoder_top_v3" / candidate_id
    conn = read_json(integ_root / "connectivity.json")
    top_pin_map = {name: entries[0] for name, entries in read_json(integ_root / "pin_map.json").items()}
    route_authority, track_rows = _route_inventory(candidate_id)
    rects, adjacency = build_shape_graph(conn["graph"])
    owners, ownership_rows = build_owner_index(
        rects=rects,
        top_pin_bboxes=top_pin_map,
        top_route_geometry=read_json(top_root / "route_geometry.json"),
        integration_route_geometry=read_json(integ_root / "route_geometry.json"),
    )

    merged_components = []
    for component_id, merged_nets in sorted(conn["unexpected_net_merges"].items()):
        component = next(row for row in conn["graph"]["components"] if row["component_id"] == component_id)
        witness = shortest_cross_net_witness(
            graph=conn["graph"],
            rects=rects,
            adjacency=adjacency,
            owners=owners,
            merged_nets=merged_nets,
        )
        merged_components.append(
            {
                "component_id": component_id,
                "merged_net_list": merged_nets,
                "component_bbox": component["bbox"],
                "component_layers": component["layers"],
                "member_count": len(component["members"]),
                "witness": witness,
            }
        )

    witness_json = {
        "scope": "decoder_integration_merge_witness",
        "candidate_id": candidate_id,
        "generated_at": "2026-07-31T00:00:00Z",
        "git_head": git_head(),
        "merge_component_count": len(merged_components),
        "merged_components": merged_components,
        "route_authority_path": "docs/decoder_integration_route_authority.json",
        "track_allocation_path": "docs/decoder_integration_track_allocation.csv",
    }
    write_json(DOCS / "DECODER_INTEGRATION_MERGE_WITNESS_A.json", witness_json)
    md = [
        "# Decoder Integration Merge Witness A",
        "",
        f"- candidate_id: `{candidate_id}`",
        f"- merge_component_count: `{len(merged_components)}`",
        "",
    ]
    for component in merged_components:
        md.extend(
            [
                f"## {component['component_id']}",
                "",
                f"- merged_net_list: `{component['merged_net_list']}`",
                f"- component_bbox: `{component['component_bbox']}`",
                f"- component_layers: `{component['component_layers']}`",
                f"- member_count: `{component['member_count']}`",
                f"- witness_found: `{component['witness'].get('witness_found')}`",
                f"- first_illegal_cross_net_contact: `{component['witness'].get('first_illegal_cross_net_contact')}`",
                "",
            ]
        )
    write_text(DOCS / "DECODER_INTEGRATION_MERGE_WITNESS_A.md", "\n".join(md))
    write_csv(DOCS / "DECODER_INTEGRATION_SHAPE_OWNERSHIP_A.csv", ownership_rows)
    write_json(DOCS / "decoder_integration_route_authority.json", route_authority)
    write_csv(DOCS / "decoder_integration_track_allocation.csv", track_rows)

    marker_rows, clusters = _marker_inventory(candidate_id, ownership_rows)
    write_csv(DOCS / "DECODER_INTEGRATION_DRC_MARKER_INVENTORY_A.csv", marker_rows)
    write_json(DOCS / "DECODER_INTEGRATION_DRC_MARKER_CLUSTERS_A.json", clusters)


def main() -> int:
    DOCS.mkdir(parents=True, exist_ok=True)
    top_input_lock()
    _write_rule_text()
    candidate_a_witness()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
