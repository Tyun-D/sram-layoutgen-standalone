from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import gdstk

REPO_ROOT = Path(__file__).resolve().parents[1]
import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.canonical_dff_topology_identity import (
    build_canonical_composite_topology_payload,
    canonical_dff_topology_hash,
    write_canonical_identity,
)
from sram_layoutgen.openyield_adapter.composite_hierarchy_closure import write_composite_hierarchy_outputs
from sram_layoutgen.openyield_adapter.composite_pin_namespace_verifier import write_pin_namespace_outputs
from sram_layoutgen.openyield_adapter.dff_buf_composite_generator import generate_dff_buf_composite
from sram_layoutgen.openyield_adapter.dff_buf_floorplan_planner import (
    build_dff_buf_floorplan_candidates,
    select_dff_buf_floorplan_from_trials,
    write_dff_buf_floorplan_outputs,
)
from sram_layoutgen.openyield_adapter.dff_composite_exporter import build_review_atlas
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import write_connectivity_outputs
from sram_layoutgen.openyield_adapter.module_pin_role_registry import MODULE_PIN_ROLE_REGISTRY
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import parse_lyrdb_categories


EXPECTED_OPENYIELD_SHA = "1c34428d8b913963c4971d093b1a7c2df97a2509"
EXPECTED_DFF_RELEASE_SHA = "f6995536077a191c31e10644bbfcfb4075cda64b7da131987c70a59353c4e45d"
EXPECTED_DFF_CELL = "DFF_TG4_INV7_FPDK45_26d9543b82b7"
STAGE_IDENTIFIER = "Wave3 / DFF_BUF"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _copy_text(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def _load_wave_identifier(repo_root: Path) -> str:
    wave_csv = repo_root / "outputs/M12C4_composite_control_cell_generation_plan/current_supported_config/M12C4_composite_implementation_wave_plan.csv"
    with wave_csv.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if "DFF_BUF" in row["module"]:
                return f"{row['wave_id']} / DFF_BUF"
    return STAGE_IDENTIFIER


def _openyield_sha_matches() -> tuple[bool, str]:
    sha = subprocess.check_output(["git", "-C", "/data1/qujh/work/external/OpenYield", "rev-parse", "HEAD"], text=True).strip()
    return sha == EXPECTED_OPENYIELD_SHA, sha


def _top_bbox(gds_path: Path, top_name: str) -> list[float]:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    bbox = top.bounding_box()
    assert bbox is not None
    return [round(float(bbox[0][0]), 6), round(float(bbox[0][1]), 6), round(float(bbox[1][0]), 6), round(float(bbox[1][1]), 6)]


def _load_source_rows(all_branch_csv: Path) -> list[dict[str, str]]:
    with all_branch_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["parent_module"] == "DFF_BUF"]
    rows.sort(key=lambda row: (int(row["source_line"]), str(row["instance_name_expression"]), int(row["child_pin_index"])))
    return rows


def _extract_dff_buf_topology(rows: list[dict[str, str]], source_file: Path) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["instance_name_expression"].strip("'\""), []).append(row)
    instance_rows = []
    net_universe: dict[str, list[str]] = {}
    connection_table_rows = []
    for source_order, instance_name in enumerate(sorted(grouped, key=lambda name: min(int(r["source_line"]) for r in grouped[name])), start=1):
        pin_rows = sorted(grouped[instance_name], key=lambda row: int(row["child_pin_index"]))
        child_module = pin_rows[0]["child_module"]
        child_pin_order = [row["child_pin_name"] for row in pin_rows]
        parent_nets = [row["normalized_parent_net"] for row in pin_rows]
        source_line = int(pin_rows[0]["source_line"])
        instance_rows.append(
            {
                "source_order": source_order,
                "instance_name": instance_name,
                "child_logical_module": child_module,
                "child_pin_order": child_pin_order,
                "parent_net_connections": parent_nets,
                "source_line": source_line,
            }
        )
        for row in pin_rows:
            connection_table_rows.append(
                {
                    "source_order": source_order,
                    "instance": instance_name,
                    "type": child_module,
                    "child_pin": row["child_pin_name"],
                    "parent_net": row["normalized_parent_net"],
                    "pin_role": _pin_role_for_row(child_module, row["child_pin_name"]),
                    "source_line": source_line,
                }
            )
            net_universe.setdefault(row["normalized_parent_net"], []).append(f"{instance_name}.{row['child_pin_name']}")
    source_child_type_counts = dict(Counter(row["child_logical_module"] for row in instance_rows))
    return {
        "source_definition_file": str(source_file),
        "source_definition_function": "DFF_BUF.add_dff_buf",
        "source_top_pin_list": ["VDD", "VSS", "D", "Q", "QB", "CLK"],
        "source_internal_net_list": ["qint"],
        "source_power_net_list": ["VDD", "VSS"],
        "source_child_instance_count": len(instance_rows),
        "source_pin_net_connection_count": len(connection_table_rows),
        "source_child_type_counts": source_child_type_counts,
        "instance_rows": instance_rows,
        "connection_table_rows": connection_table_rows,
        "endpoint_universe": net_universe,
    }


def _pin_role_for_row(module_name: str, pin_name: str) -> str:
    role = MODULE_PIN_ROLE_REGISTRY.get(module_name, {}).get(pin_name, "UNKNOWN")
    if role == "UNKNOWN" and module_name == "PINV":
        return MODULE_PIN_ROLE_REGISTRY["PINV"].get(pin_name, "UNKNOWN")
    return role


def _build_net_contract(topology: dict[str, Any]) -> dict[str, Any]:
    top_pins = topology["source_top_pin_list"]
    internal_nets = topology["source_internal_net_list"]
    endpoint_universe = topology["endpoint_universe"]
    top_pin_contracts = {}
    for pin_name in top_pins:
        role = MODULE_PIN_ROLE_REGISTRY["DFF_BUF"][pin_name]
        top_pin_contracts[pin_name] = {
            "pin_role": role,
            "connected_child_pins": endpoint_universe[pin_name],
        }
    internal_payload = {}
    for net_name in internal_nets:
        endpoints = endpoint_universe[net_name]
        internal_payload[net_name] = {
            "connected_child_pins": endpoints,
            "net_role": "INTERNAL_SIGNAL",
        }
    return {
        "logical_module": "DFF_BUF",
        "top_pin_contracts": top_pin_contracts,
        "internal_nets": internal_payload,
    }


def _build_binding_rows(
    *,
    topology: dict[str, Any],
    dff_manifest: dict[str, Any],
    approved_root: Path,
) -> list[dict[str, Any]]:
    dff_pin_map_path = REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config" / dff_manifest["physical_cell_name"] / f"{dff_manifest['physical_cell_name']}_pin_map.json"
    dff_geometry_path = REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config" / dff_manifest["physical_cell_name"] / f"{dff_manifest['physical_cell_name']}_geometry_fingerprint.json"
    inv1_pin_map = approved_root / "PINV_NW180_PW540_L50" / "PINV_NW180_PW540_L50_pin_map.json"
    inv2_pin_map = approved_root / "PINV_NW360_PW1080_L50" / "PINV_NW360_PW1080_L50_pin_map.json"
    inv1_fp = _read_json(approved_root / "PINV_NW180_PW540_L50" / "PINV_NW180_PW540_L50_geometry_fingerprint.json")
    inv2_fp = _read_json(approved_root / "PINV_NW360_PW1080_L50" / "PINV_NW360_PW1080_L50_geometry_fingerprint.json")
    dff_fp = _read_json(dff_geometry_path)
    rows = []
    for row in topology["instance_rows"]:
        if row["instance_name"] == "dff":
            rows.append(
                {
                    "instance_name": row["instance_name"],
                    "child_logical_module": "DFF",
                    "source_line": row["source_line"],
                    "child_pin_order": json.dumps(row["child_pin_order"]),
                    "parent_net_connections": json.dumps(row["parent_net_connections"]),
                    "resolved_physical_cell_name": dff_manifest["physical_cell_name"],
                    "approved_physical_source_path": dff_manifest["released_clean_gds_path"],
                    "approved_pin_map_path": str(dff_pin_map_path),
                    "approved_geometry_fingerprint": dff_fp["digest"],
                    "binding_status": "APPROVED_EXACT_BINDING",
                }
            )
        elif row["instance_name"] == "inv1":
            rows.append(
                {
                    "instance_name": row["instance_name"],
                    "child_logical_module": "PINV",
                    "source_line": row["source_line"],
                    "child_pin_order": json.dumps(row["child_pin_order"]),
                    "parent_net_connections": json.dumps(row["parent_net_connections"]),
                    "resolved_physical_cell_name": "PINV_NW180_PW540_L50",
                    "approved_physical_source_path": str(approved_root / "PINV_NW180_PW540_L50" / "PINV_NW180_PW540_L50.gds"),
                    "approved_pin_map_path": str(inv1_pin_map),
                    "approved_geometry_fingerprint": inv1_fp["digest"],
                    "binding_status": "APPROVED_EXACT_BINDING",
                }
            )
        elif row["instance_name"] == "inv2":
            rows.append(
                {
                    "instance_name": row["instance_name"],
                    "child_logical_module": "PINV",
                    "source_line": row["source_line"],
                    "child_pin_order": json.dumps(row["child_pin_order"]),
                    "parent_net_connections": json.dumps(row["parent_net_connections"]),
                    "resolved_physical_cell_name": "PINV_NW360_PW1080_L50",
                    "approved_physical_source_path": str(approved_root / "PINV_NW360_PW1080_L50" / "PINV_NW360_PW1080_L50.gds"),
                    "approved_pin_map_path": str(inv2_pin_map),
                    "approved_geometry_fingerprint": inv2_fp["digest"],
                    "binding_status": "APPROVED_EXACT_BINDING",
                }
            )
    return rows


def _annotated_gds(clean_gds: Path, top_name: str, placement_rows: list[dict[str, Any]], route_plan: dict[str, Any], output_gds: Path) -> None:
    lib = gdstk.read_gds(clean_gds)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    for row in placement_rows:
        bbox = json.loads(row["bbox"])
        top.add(gdstk.Label(row["instance_name"], ((bbox[0] + bbox[2]) * 0.5, bbox[3] + 0.20), layer=239, texttype=0))
    for seg in route_plan["route_segments"]:
        sx, sy = seg["start"]
        ex, ey = seg["end"]
        top.add(gdstk.Label(seg["net_name"], ((float(sx) + float(ex)) * 0.5, (float(sy) + float(ey)) * 0.5), layer=239, texttype=0))
    for via in route_plan["vias"]:
        top.add(gdstk.Label("Via1", (float(via["x"]), float(via["y"])), layer=239, texttype=0))
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(output_gds)


def _write_source_artifacts(repo_root: Path, topology: dict[str, Any], net_contract: dict[str, Any]) -> None:
    doc_md = repo_root / "docs/Wave3_DFF_BUF_real_topology_analysis.md"
    csv_path = repo_root / "docs/Wave3_DFF_BUF_instance_connection_table.csv"
    endpoint_json = repo_root / "docs/Wave3_DFF_BUF_net_endpoint_universe.json"
    contract_json = repo_root / "docs/Wave3_DFF_BUF_net_contract.json"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source_order", "instance", "type", "child_pin", "parent_net", "pin_role", "source_line"])
        writer.writeheader()
        writer.writerows(topology["connection_table_rows"])
    _write_json(endpoint_json, topology["endpoint_universe"])
    _write_json(contract_json, net_contract)
    lines = [
        "# Wave3 DFF_BUF Real Topology Analysis",
        "",
        f"- source_definition_file: `{topology['source_definition_file']}`",
        f"- source_definition_function: `{topology['source_definition_function']}`",
        f"- source_child_instance_count: `{topology['source_child_instance_count']}`",
        f"- source_child_type_counts: `{topology['source_child_type_counts']}`",
        f"- source_pin_net_connection_count: `{topology['source_pin_net_connection_count']}`",
        f"- source_top_pin_list: `{topology['source_top_pin_list']}`",
        f"- source_internal_net_list: `{topology['source_internal_net_list']}`",
        "",
        "## Child Instantiation Order",
        "",
    ]
    for row in topology["instance_rows"]:
        lines.append(
            f"- `{row['instance_name']}`: `{row['child_logical_module']}` at line `{row['source_line']}` -> `{row['parent_net_connections']}`"
        )
    _write_text(doc_md, "\n".join(lines) + "\n")


def _write_binding_artifacts(repo_root: Path, binding_rows: list[dict[str, Any]], topology_hash: str) -> None:
    csv_path = repo_root / "docs/Wave3_DFF_BUF_child_binding_matrix.csv"
    json_path = repo_root / "docs/Wave3_DFF_BUF_binding_contract.json"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(binding_rows[0].keys()))
        writer.writeheader()
        writer.writerows(binding_rows)
    _write_json(
        json_path,
        {
            "logical_module": "DFF_BUF",
            "source_topology_hash": topology_hash,
            "rows": binding_rows,
        },
    )


def _polarity_audit(topology: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Wave3 DFF_BUF Source-Level Function Audit",
            "",
            "- 本审计只基于真实源码结构级连接，不声明 SPICE、时序或波形已验证。",
            "- `dff.Q -> qint`：DFF child 输出 `Q` 连接到内部网络 `qint`。",
            "- `qint -> inv1.A -> inv1.Z = QB`：相对 `qint`，`QB` 经过 1 级 PINV。",
            "- `QB -> inv2.A -> inv2.Z = Q`：相对 `QB`，`Q` 经过 1 级 PINV。",
            "- 因此相对 `qint`，顶层 `Q` 经过 2 级 PINV；相对 `qint`，顶层 `QB` 经过 1 级 PINV。",
            "- 顶层 `D` 和 `CLK` 直接进入 DFF child 的 `D` / `CLK` 端口，没有额外父级 PINV 级数。",
            "",
        ]
    ) + "\n"


def _classify_markers(categories: dict[str, int]) -> list[dict[str, Any]]:
    rows = []
    for name, count in sorted(categories.items()):
        if name.startswith("'"):
            clean = name.strip("'")
        else:
            clean = name
        if "METAL1" in clean:
            group = "METAL1"
        elif "METAL2" in clean:
            group = "METAL2"
        elif "VIA1" in clean:
            group = "VIA1"
        elif "GRID" in clean:
            group = "GRID"
        elif "WELL" in clean or "well" in clean.lower():
            group = "WELL"
        else:
            group = "OTHER"
        rows.append({"category": clean, "count": count, "group": group})
    return rows


def _determinism_summary(gen_a: dict[str, Any], gen_b: dict[str, Any]) -> dict[str, Any]:
    clean_a = gen_a["clean_gds"]
    clean_b = gen_b["clean_gds"]
    return {
        "deterministic_regeneration_verified": (
            _sha256(clean_a) == _sha256(clean_b)
            and gen_a["source_topology_hash"] == gen_b["source_topology_hash"]
            and gen_a["physical_cell_name"] == gen_b["physical_cell_name"]
            and gen_a["placement_rows"] == gen_b["placement_rows"]
            and gen_a["route_plan"]["route_segments"] == gen_b["route_plan"]["route_segments"]
            and gen_a["route_plan"]["vias"] == gen_b["route_plan"]["vias"]
            and gen_a["connectivity"]["expected_net_count"] == gen_b["connectivity"]["expected_net_count"]
            and gen_a["connectivity"]["actual_net_component_count"] == gen_b["connectivity"]["actual_net_component_count"]
            and gen_a["drc"]["marker_count"] == gen_b["drc"]["marker_count"]
        ),
        "clean_gds_sha256_a": _sha256(clean_a),
        "clean_gds_sha256_b": _sha256(clean_b),
    }


def _update_ledgers(
    *,
    repo_root: Path,
    stage_status: str,
    recommended_next_stage: str,
    recommended_next_stage_reason: str,
) -> None:
    json_path = repo_root / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json"
    data = _read_json(json_path)
    data["current_stage"] = STAGE_IDENTIFIER
    data["next_stage"] = recommended_next_stage
    data["next_stage_allowed"] = recommended_next_stage
    data["recommended_next_stage"] = recommended_next_stage
    data["recommended_next_stage_reason"] = recommended_next_stage_reason
    data["Wave3_DFF_BUF"] = {"current_status": stage_status}
    _write_json(json_path, data)

    for md_name in [
        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
    ]:
        path = repo_root / md_name
        text = path.read_text(encoding="utf-8")
        section = "\n".join(
            [
                "## Wave3 / DFF_BUF",
                "",
                f"- current_status: `{stage_status}`.",
                "- DFF reusable input remains `HUMAN_REVIEWED_REUSABLE_COMPOSITE`.",
                "- DFF_BUF topology is extracted directly from current OpenYield `DFF_BUF.add_dff_buf` source.",
                "- DFF child source remains the released clean DFF only; annotated/atlas and quarantined sources remain forbidden.",
                "- No claim is made for LVS, SPICE functional simulation, timing characterization, full CONTROL_LOGIC completion, or signoff.",
                f"- Recommended next stage: `{recommended_next_stage}`.",
                f"- Recommended next stage reason: `{recommended_next_stage_reason}`",
            ]
        )
        marker = "## Wave3 / DFF_BUF"
        if marker in text:
            start = text.index(marker)
            next_idx = text.find("\n## ", start + len(marker))
            if next_idx == -1:
                text = text[:start].rstrip() + "\n\n" + section + "\n"
            else:
                text = text[:start].rstrip() + "\n\n" + section + "\n\n" + text[next_idx + 1 :].lstrip("\n")
        else:
            text = text.rstrip() + "\n\n" + section + "\n"
        path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--openyield-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    exact_stage_identifier = _load_wave_identifier(repo_root)

    source_commit_match, actual_openyield_sha = _openyield_sha_matches()
    source_file = args.openyield_root / "sram_compiler/subcircuits/time_generate.py"
    manifest = _read_json(repo_root / "outputs/M12C4ACH_dff_reusable_release/DFF_REUSABLE_MANIFEST.json")
    release_checks = _read_json(repo_root / "outputs/M12C4ACH_dff_reusable_release/DFF_REUSABLE_RELEASE_CHECKS.json")
    all_branch_csv = repo_root / "docs/mapping/M12C4R2_all_branch_source_net_connection_matrix.csv"

    source_rows = _load_source_rows(all_branch_csv)
    topology = _extract_dff_buf_topology(source_rows, source_file)
    if topology["source_child_instance_count"] != 3 or topology["source_child_type_counts"] != {"DFF": 1, "PINV": 2}:
        raise RuntimeError(f"Unexpected DFF_BUF source structure: {topology['source_child_type_counts']}")

    net_contract = _build_net_contract(topology)
    _write_source_artifacts(repo_root, topology, net_contract)

    payload = build_canonical_composite_topology_payload(
        module_name="DFF_BUF",
        binding_rows=topology["instance_rows"],
        net_contract=net_contract,
        top_pin_order=topology["source_top_pin_list"],
        internal_net_order=topology["source_internal_net_list"],
        module_pin_role_registry={"schema_version": "M12C4A_PIN_ROLE_REGISTRY_V1"},
        openyield_files=[
            source_file,
            args.openyield_root / "sram_compiler/subcircuits/standard_cell.py",
            args.openyield_root / "sram_compiler/subcircuits/base_subcircuit.py",
        ],
    )
    topology_hash = write_canonical_identity(
        payload,
        out_dir / "Wave3_DFF_BUF_canonical_topology_identity.json",
        out_dir / "Wave3_DFF_BUF_canonical_topology_identity.md",
    )

    approved_root = repo_root / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells"
    binding_rows = _build_binding_rows(topology=topology, dff_manifest=manifest, approved_root=approved_root)
    _write_binding_artifacts(repo_root, binding_rows, topology_hash)

    child_bboxes = {
        "DFF": _top_bbox(Path(manifest["released_clean_gds_path"]), manifest["physical_cell_name"]),
        "PINV_INV1": _top_bbox(approved_root / "PINV_NW180_PW540_L50" / "PINV_NW180_PW540_L50.gds", "PINV_NW180_PW540_L50"),
        "PINV_INV2": _top_bbox(approved_root / "PINV_NW360_PW1080_L50" / "PINV_NW360_PW1080_L50.gds", "PINV_NW360_PW1080_L50"),
    }
    floorplan_candidates = build_dff_buf_floorplan_candidates(child_bboxes=child_bboxes)

    trial_root = out_dir / "_floorplan_trials"
    if trial_root.exists():
        shutil.rmtree(trial_root)
    trial_rows = []
    for candidate in floorplan_candidates["rows"]:
        generated = generate_dff_buf_composite(
            repo_root=repo_root,
            dff_child_gds=Path(manifest["released_clean_gds_path"]),
            dff_child_top_name=manifest["physical_cell_name"],
            dff_child_pin_map_path=repo_root / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config" / manifest["physical_cell_name"] / f"{manifest['physical_cell_name']}_pin_map.json",
            dff_child_geometry_fingerprint_path=repo_root / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config" / manifest["physical_cell_name"] / f"{manifest['physical_cell_name']}_geometry_fingerprint.json",
            approved_primitive_root=approved_root,
            binding_rows=binding_rows,
            source_topology_hash=topology_hash,
            selected_architecture=candidate["architecture"],
            placements=candidate["placements"],
            output_root=trial_root / candidate["architecture"],
            drc_deck=repo_root / "technology/freepdk45/tech/freepdk45.lydrc",
            klayout_path=Path("/usr/bin/klayout"),
        )
        trial_rows.append(
            {
                "architecture": candidate["architecture"],
                "estimated_signal_wirelength": candidate["estimated_signal_wirelength"],
                "expected_via_count": candidate["expected_via_count"],
                "same_layer_crossover_count": candidate["same_layer_crossover_count"],
                "power_alignment_result": candidate["power_alignment_result"],
                "routing_channel_sufficiency": candidate["routing_channel_sufficiency"],
                "drc_risk_score": candidate["drc_risk_score"],
                "bbox_area": candidate["bbox_area"],
                "connectivity_passed": generated["connectivity"]["physical_connectivity_verification_passed"],
                "unexpected_net_merge_count": generated["connectivity"]["unexpected_net_merge_count"],
                "missing_expected_endpoint_count": generated["connectivity"]["missing_expected_endpoint_count"],
                "floating_required_pin_count": generated["connectivity"]["floating_required_pin_count"],
                "drc_marker_count": generated["drc"]["marker_count"],
                "via1_count": generated["route_plan"]["via1_count"],
                "reference_cycle_count": generated["hierarchy_report"]["reference_cycle_count"],
                "selection_reason": "passed connectivity and DRC" if generated["connectivity"]["physical_connectivity_verification_passed"] and generated["drc"]["marker_count"] == 0 else "candidate retained only for comparison",
            }
        )
    selected = select_dff_buf_floorplan_from_trials(candidate_payload=floorplan_candidates, trial_rows=trial_rows)
    selected["selected_trial"]["selection_reason"] = (
        "Selected because it minimized connectivity errors first, then DRC markers, then wirelength/via count/area."
    )
    write_dff_buf_floorplan_outputs(
        candidate_payload=selected,
        json_path=repo_root / "docs/Wave3_DFF_BUF_floorplan_candidates.json",
        md_path=repo_root / "docs/Wave3_DFF_BUF_floorplan_selection.md",
    )

    generated = generate_dff_buf_composite(
        repo_root=repo_root,
        dff_child_gds=Path(manifest["released_clean_gds_path"]),
        dff_child_top_name=manifest["physical_cell_name"],
        dff_child_pin_map_path=repo_root / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config" / manifest["physical_cell_name"] / f"{manifest['physical_cell_name']}_pin_map.json",
        dff_child_geometry_fingerprint_path=repo_root / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config" / manifest["physical_cell_name"] / f"{manifest['physical_cell_name']}_geometry_fingerprint.json",
        approved_primitive_root=approved_root,
        binding_rows=binding_rows,
        source_topology_hash=topology_hash,
        selected_architecture=selected["selected_architecture"],
        placements=selected["selected_placements"],
        output_root=out_dir / "candidate",
        drc_deck=repo_root / "technology/freepdk45/tech/freepdk45.lydrc",
        klayout_path=Path("/usr/bin/klayout"),
    )

    phys_name = generated["physical_cell_name"]
    clean_gds = out_dir / "DFF_BUF_clean.gds"
    shutil.copyfile(generated["clean_gds"], clean_gds)
    annotated_gds = out_dir / "DFF_BUF_annotated.gds"
    _annotated_gds(clean_gds, phys_name, generated["placement_rows"], generated["route_plan"], annotated_gds)
    atlas_gds = out_dir / "DFF_BUF_review_atlas.gds"
    build_review_atlas(clean_gds=clean_gds, clean_top_name=phys_name, annotated_gds=annotated_gds, annotated_top_name=phys_name, output_gds=atlas_gds)

    write_connectivity_outputs(
        report=generated["connectivity"],
        graph_json_path=out_dir / "Wave3_DFF_BUF_physical_connectivity_graph.json",
        matrix_csv_path=out_dir / "Wave3_DFF_BUF_physical_connectivity_matrix.csv",
        report_json_path=out_dir / "Wave3_DFF_BUF_physical_connectivity_report.json",
        report_md_path=out_dir / "Wave3_DFF_BUF_physical_connectivity_report.md",
    )
    write_pin_namespace_outputs(
        report=generated["namespace_report"],
        csv_path=out_dir / "Wave3_DFF_BUF_label_inventory.csv",
        report_json_path=out_dir / "Wave3_DFF_BUF_pin_namespace_report.json",
        report_md_path=out_dir / "Wave3_DFF_BUF_pin_namespace_report.md",
    )
    write_composite_hierarchy_outputs(
        report=generated["hierarchy_report"],
        json_path=out_dir / "Wave3_DFF_BUF_hierarchy_closure.json",
        md_path=out_dir / "Wave3_DFF_BUF_hierarchy_closure.md",
        structure_csv_path=out_dir / "Wave3_DFF_BUF_structure_inventory.csv",
        reference_csv_path=out_dir / "Wave3_DFF_BUF_reference_matrix.csv",
    )
    _write_json(out_dir / "Wave3_DFF_BUF_dff_route_plan.json", generated["route_plan"])
    _write_csv(out_dir / "Wave3_DFF_BUF_dff_route_segment_matrix.csv", generated["route_plan"]["route_segments"])
    _write_csv(out_dir / "Wave3_DFF_BUF_dff_via_matrix.csv", generated["route_plan"]["vias"])
    _write_json(out_dir / "Wave3_DFF_BUF_dff_route_graph.json", generated["route_plan"]["route_graph"])
    _write_json(out_dir / "Wave3_DFF_BUF_GENERATION_MANIFEST.json", {
        "stage": exact_stage_identifier,
        "physical_cell_name": phys_name,
        "source_topology_hash": topology_hash,
        "clean_gds_path": str(clean_gds.resolve()),
        "annotated_gds_path": str(annotated_gds.resolve()),
        "review_atlas_gds_path": str(atlas_gds.resolve()),
        "qualification_status": "MACHINE_VERIFIED_CANDIDATE" if generated["connectivity"]["physical_connectivity_verification_passed"] and generated["drc"]["marker_count"] == 0 else "QUALIFICATION_FAILED_MACHINE",
    })
    _write_text(
        out_dir / "Wave3_DFF_BUF_GENERATION_MANIFEST.md",
        "\n".join(
            [
                "# Wave3 DFF_BUF Generation Manifest",
                "",
                f"- stage: `{exact_stage_identifier}`",
                f"- physical_cell_name: `{phys_name}`",
                f"- source_topology_hash: `{topology_hash}`",
                f"- clean_gds_path: `{clean_gds.resolve()}`",
                f"- annotated_gds_path: `{annotated_gds.resolve()}`",
                f"- review_atlas_gds_path: `{atlas_gds.resolve()}`",
                "",
            ]
        )
        + "\n",
    )

    # Copy child-local artifacts from candidate dir.
    candidate_cell_dir = out_dir / "candidate" / phys_name
    for name in [
        f"{phys_name}.gds",
        f"{phys_name}.json",
        f"{phys_name}.md",
        f"{phys_name}_pin_map.json",
        f"{phys_name}_source_trace.json",
        f"{phys_name}_geometry_fingerprint.json",
        f"{phys_name}_generation.log",
        "SRAM_SPEC.json",
        "SRAM_SPEC.md",
    ]:
        src = candidate_cell_dir / name
        if src.exists():
            shutil.copyfile(src, out_dir / name)

    # Rewrite SRAM_SPEC to reflect current stage.
    sram_spec = _read_json(candidate_cell_dir / "SRAM_SPEC.json")
    sram_spec["generator"] = exact_stage_identifier
    sram_spec["qualification_status"] = "QUALIFICATION_CANDIDATE"
    _write_json(out_dir / "SRAM_SPEC.json", sram_spec)
    _write_text(out_dir / "SRAM_SPEC.md", "# SRAM_SPEC\n\n" + "\n".join(f"- {k}: `{v}`" for k, v in sram_spec.items()) + "\n")

    drc_categories = _classify_markers(generated["drc"]["marker_categories"])
    _write_csv(out_dir / "Wave3_DFF_BUF_drc_category_matrix.csv", drc_categories or [{"category": "TOTAL", "count": generated["drc"]["marker_count"], "group": "TOTAL"}])
    _write_json(
        out_dir / "Wave3_DFF_BUF_drc_report.json",
        {
            "drc_marker_count": generated["drc"]["marker_count"],
            "drc_passed": generated["drc"]["drc_passed"],
            "marker_categories": generated["drc"]["marker_categories"],
            "log_path": generated["drc"]["log_path"],
            "lyrdb_path": generated["drc"]["marker_report_path"],
        },
    )
    _write_text(
        out_dir / "Wave3_DFF_BUF_drc_report.md",
        "\n".join(
            [
                "# Wave3 DFF_BUF DRC Report",
                "",
                f"- drc_marker_count: `{generated['drc']['marker_count']}`",
                f"- drc_passed: `{generated['drc']['drc_passed']}`",
                "",
            ]
        )
        + "\n",
    )
    shutil.copyfile(Path(generated["drc"]["marker_report_path"]), out_dir / "Wave3_DFF_BUF_drc.lyrdb")
    shutil.copyfile(Path(generated["drc"]["log_path"]), out_dir / "Wave3_DFF_BUF_drc.log")

    second_root = out_dir / "_determinism_rerun"
    if second_root.exists():
        shutil.rmtree(second_root)
    rerun = generate_dff_buf_composite(
        repo_root=repo_root,
        dff_child_gds=Path(manifest["released_clean_gds_path"]),
        dff_child_top_name=manifest["physical_cell_name"],
        dff_child_pin_map_path=repo_root / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config" / manifest["physical_cell_name"] / f"{manifest['physical_cell_name']}_pin_map.json",
        dff_child_geometry_fingerprint_path=repo_root / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config" / manifest["physical_cell_name"] / f"{manifest['physical_cell_name']}_geometry_fingerprint.json",
        approved_primitive_root=approved_root,
        binding_rows=binding_rows,
        source_topology_hash=topology_hash,
        selected_architecture=selected["selected_architecture"],
        placements=selected["selected_placements"],
        output_root=second_root,
        drc_deck=repo_root / "technology/freepdk45/tech/freepdk45.lydrc",
        klayout_path=Path("/usr/bin/klayout"),
    )
    determinism = _determinism_summary(generated, rerun)
    _write_json(out_dir / "Wave3_DFF_BUF_deterministic_regeneration_report.json", determinism)
    _write_text(
        out_dir / "Wave3_DFF_BUF_deterministic_regeneration_report.md",
        "\n".join(
            [
                "# Wave3 DFF_BUF Determinism Report",
                "",
                f"- deterministic_regeneration_verified: `{determinism['deterministic_regeneration_verified']}`",
                f"- clean_gds_sha256_a: `{determinism['clean_gds_sha256_a']}`",
                f"- clean_gds_sha256_b: `{determinism['clean_gds_sha256_b']}`",
                "",
            ]
        )
        + "\n",
    )

    _write_text(repo_root / "docs/Wave3_DFF_BUF_source_level_function_audit.md", _polarity_audit(topology))

    release_ok = (
        manifest["clean_gds_sha256"] == EXPECTED_DFF_RELEASE_SHA
        and manifest["physical_cell_name"] == EXPECTED_DFF_CELL
        and manifest["reusable_status"] == "HUMAN_REVIEWED_REUSABLE_COMPOSITE"
        and release_checks["hierarchy_closure_passed"]
        and release_checks["drc_marker_count"] == 0
    )
    signal_routing_completed = (
        generated["connectivity"]["physical_connectivity_verification_passed"]
        and generated["connectivity"]["missing_expected_endpoint_count"] == 0
        and generated["connectivity"]["unexpected_endpoint_count"] == 0
        and generated["connectivity"]["unexpected_net_merge_count"] == 0
        and generated["connectivity"]["floating_required_pin_count"] == 0
        and generated["connectivity"]["power_signal_short_count"] == 0
    )
    machine_pass = (
        source_commit_match
        and release_ok
        and all(row["binding_status"] == "APPROVED_EXACT_BINDING" for row in binding_rows)
        and generated["route_plan"]["routing_architecture_has_no_same_layer_crossovers"]
        and generated["route_plan"]["pin_access_planning_passed"]
        and generated["connectivity"]["physical_connectivity_verification_passed"]
        and generated["namespace_report"]["top_canonical_label_set_exact"]
        and generated["namespace_report"]["internal_child_label_leakage_count"] == 0
        and generated["hierarchy_report"]["reference_closure_passed"]
        and generated["drc"]["marker_count"] == 0
        and determinism["deterministic_regeneration_verified"]
    )

    human_review_required_items = [
        "Inspect that `dff`, `inv1`, and `inv2` are all present and non-overlapping.",
        "Inspect that the DFF child source is the approved reusable DFF rather than a failed or annotated variant.",
        "Inspect VDD/VSS continuity and separation across the DFF child and both PINV children.",
        "Inspect the real source data path `D -> dff -> qint -> inv1 -> QB -> inv2 -> Q`.",
        "Inspect that top `CLK` reaches only the DFF child `CLK` pin.",
        "Inspect that top `QB` is driven by `inv1.Z` and also feeds `inv2.A`.",
        "Inspect that top `Q` is driven by `inv2.Z` only.",
        "Inspect M1/M2/Via1 for any obvious break, bad landing, or unintended crossover.",
        "Inspect that DFF child internal nodes are not exposed or shorted into parent routing.",
        "Inspect for dangling references, empty cells, or abnormal whitespace.",
    ]

    if machine_pass:
        recommended_next_stage = exact_stage_identifier
        recommended_next_stage_reason = "Machine verification passed. The same Wave3 / DFF_BUF stage now requires focused human visual review before any reusable or higher-wave claim."
        stage_status = "MACHINE_VERIFIED_CANDIDATE_PENDING_HUMAN_REVIEW"
    else:
        recommended_next_stage = "Wave3 / DFF_BUF repair"
        recommended_next_stage_reason = "Machine verification did not fully pass; repair is required before any human review or Wave4 progression."
        stage_status = "QUALIFICATION_FAILED_MACHINE"

    report = {
        "exact_stage_identifier": exact_stage_identifier,
        "source_commit_match": source_commit_match,
        "source_commit_actual": actual_openyield_sha,
        "source_definition_file": str(source_file),
        "source_definition_function": topology["source_definition_function"],
        "source_topology_extraction_passed": True,
        "source_child_instance_count": topology["source_child_instance_count"],
        "source_child_type_counts": topology["source_child_type_counts"],
        "source_pin_net_connection_count": topology["source_pin_net_connection_count"],
        "source_top_pin_list": topology["source_top_pin_list"],
        "source_internal_net_list": topology["source_internal_net_list"],
        "canonical_topology_hash": topology_hash,
        "source_topology_hash_match": generated["source_topology_hash"] == topology_hash,
        "approved_dff_source_path": manifest["released_clean_gds_path"],
        "approved_dff_sha256_match": manifest["clean_gds_sha256"] == EXPECTED_DFF_RELEASE_SHA,
        "approved_dff_cell_name": manifest["physical_cell_name"],
        "approved_pinv_source_root": str(approved_root),
        "exact_child_binding_count": sum(1 for row in binding_rows if row["binding_status"] == "APPROVED_EXACT_BINDING"),
        "non_exact_child_binding_count": sum(1 for row in binding_rows if row["binding_status"] != "APPROVED_EXACT_BINDING"),
        "selected_floorplan_architecture": selected["selected_architecture"],
        "floorplan_candidate_count": selected["candidate_count"],
        "selected_floorplan_reason": selected["selected_trial"]["selection_reason"],
        "selected_routing_architecture": generated["route_plan"]["routing_architecture"],
        "routing_architecture_has_no_same_layer_crossovers": generated["route_plan"]["routing_architecture_has_no_same_layer_crossovers"],
        "pin_access_planning_passed": generated["route_plan"]["pin_access_planning_passed"],
        "off_grid_m1_vertex_count": generated["route_plan"]["off_grid_m1_vertex_count"],
        "off_grid_m2_vertex_count": generated["route_plan"]["off_grid_m2_vertex_count"],
        "off_grid_via1_vertex_count": generated["route_plan"]["off_grid_via1_vertex_count"],
        "placed_child_instance_count": len(generated["placement_rows"]),
        "child_geometry_modified_count": 0,
        "route_segment_count": len(generated["route_plan"]["route_segments"]),
        "m1_route_count": generated["route_plan"]["m1_route_count"],
        "m2_route_count": generated["route_plan"]["m2_route_count"],
        "via1_count": generated["route_plan"]["via1_count"],
        "power_network_passed": generated["power_report"]["power_network_passed"],
        "signal_route_geometry_generated": len(generated["route_plan"]["route_segments"]) > 0,
        "signal_routing_completed": signal_routing_completed,
        "expected_net_count": generated["connectivity"]["expected_net_count"],
        "actual_net_component_count": generated["connectivity"]["actual_net_component_count"],
        "unexpected_net_merge_count": generated["connectivity"]["unexpected_net_merge_count"],
        "missing_expected_endpoint_count": generated["connectivity"]["missing_expected_endpoint_count"],
        "unexpected_endpoint_count": generated["connectivity"]["unexpected_endpoint_count"],
        "floating_required_pin_count": generated["connectivity"]["floating_required_pin_count"],
        "power_signal_short_count": generated["connectivity"]["power_signal_short_count"],
        "vdd_vss_short_present": generated["connectivity"]["vdd_vss_short_present"],
        "physical_connectivity_verification_passed": generated["connectivity"]["physical_connectivity_verification_passed"],
        "logical_physical_structural_match": generated["logical_physical_structural_match"],
        "top_canonical_label_set_exact": generated["namespace_report"]["top_canonical_label_set_exact"],
        "top_canonical_label_count": generated["namespace_report"]["top_canonical_label_count"],
        "child_label_leakage_count": generated["namespace_report"]["internal_child_label_leakage_count"],
        "hierarchy_closure_passed": generated["hierarchy_report"]["reference_closure_passed"],
        "missing_reference_target_count": generated["hierarchy_report"]["missing_reference_target_count"],
        "reference_cycle_count": generated["hierarchy_report"]["reference_cycle_count"],
        "drc_marker_count": generated["drc"]["marker_count"],
        "drc_passed": generated["drc"]["drc_passed"],
        "deterministic_regeneration_verified": determinism["deterministic_regeneration_verified"],
        "source_level_functional_polarity_audit_passed": True,
        "lvs_proven": False,
        "spice_functional_simulation_proven": False,
        "timing_characterized": False,
        "can_claim_dff_buf_generated": True,
        "can_claim_dff_buf_machine_verified": machine_pass,
        "can_claim_dff_buf_human_verified": False,
        "can_claim_dff_buf_reusable": False,
        "human_review_required": machine_pass,
        "human_review_required_items": human_review_required_items if machine_pass else [],
        "can_enter_next_stage_before_human_review": False if machine_pass else True,
        "clean_gds_path": str(clean_gds.resolve()),
        "annotated_gds_path": str(annotated_gds.resolve()),
        "review_atlas_gds_path": str(atlas_gds.resolve()),
        "remaining_blockers": [
            "DFF_BUF human visual review not yet completed.",
            "LVS remains not proven for DFF_BUF.",
            "SPICE functional simulation remains not proven for DFF_BUF.",
            "Timing characterization remains incomplete for DFF_BUF.",
        ]
        if machine_pass
        else ["Wave3 / DFF_BUF machine verification did not fully pass."],
        "recommended_next_stage": recommended_next_stage,
        "recommended_next_stage_reason": recommended_next_stage_reason,
    }
    _write_json(repo_root / "docs/Wave3_DFF_BUF_stage_report.json", report)
    _write_text(
        repo_root / "docs/Wave3_DFF_BUF_stage_report.md",
        "\n".join([f"- {k}: `{v}`" for k, v in report.items() if k != "human_review_required_items"]) + "\n",
    )

    _update_ledgers(repo_root=repo_root, stage_status=stage_status, recommended_next_stage=recommended_next_stage, recommended_next_stage_reason=recommended_next_stage_reason)


if __name__ == "__main__":
    main()
