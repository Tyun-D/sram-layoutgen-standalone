from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


WORKTREE_ROOT = Path(__file__).resolve().parents[1]
MAIN_REPO_ROOT = WORKTREE_ROOT.parents[1]
if str(WORKTREE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKTREE_ROOT))

from sram_layoutgen.openyield_adapter.gds_pin_audit import BBox, GdsShape, GdsText, read_gds_labels_and_shapes  # noqa: E402


POWER_LABELS = {"vdd", "vss", "gnd", "ground"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit gen_col_mux power metadata proof without modifying layout flow.")
    parser.add_argument("--tech-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    tech_dir = resolve_existing_path(args.tech_dir)
    replacement = load_replacement_macro(tech_dir, "gen_col_mux")
    replacement_gds = tech_dir / str(replacement["gds"])
    aux_gds = tech_dir / "gds_lib" / "gen_col_mux.gds"
    aliases_path = tech_dir / "openyield_macro_aliases.json"
    sp_lib_dir = tech_dir / "sp_lib"
    local_netlist_writer = WORKTREE_ROOT / "sram_layoutgen" / "netlist_writer.py"
    openyield_root = MAIN_REPO_ROOT / "third_party" / "OpenYield"
    openyield_mux_source = openyield_root / "sram_compiler" / "subcircuits" / "mux_and_sa.py"

    replacement_gds_audit = inspect_gds(replacement_gds)
    aux_gds_audit = inspect_gds(aux_gds) if aux_gds.exists() else None
    spice_audit = inspect_spice_dir(sp_lib_dir)
    fallback_subckt = inspect_local_fallback_subckt(local_netlist_writer)
    openyield_source = inspect_openyield_source(openyield_mux_source)
    alias_audit = inspect_alias_file(aliases_path)

    generator_expects_vdd = bool(
        openyield_source["source_file_found"]
        and openyield_source["nodes_include_vdd"]
        and openyield_source["pmos_uses_vdd"]
    )
    vdd_label_present = replacement_gds_audit["vdd_label_present"]
    vdd_shape_candidate_present = bool(replacement_gds_audit["suspected_vdd_shapes"])
    spice_vdd_present = spice_audit["subckt_found"] and spice_audit["subckt_vdd_present"]
    safe_for_physical_mapping = True
    safe_for_shared_rail = False
    requires_metadata_fix = True

    if vdd_label_present:
        power_status = "vdd_label_present"
        recommended_fix = "add_metadata_alias_only"
        safe_for_shared_rail = True
        requires_metadata_fix = False
        can_enter = True
    elif vdd_shape_candidate_present and generator_expects_vdd:
        power_status = "vdd_shape_unlabeled"
        recommended_fix = "add_gds_label_required"
        can_enter = "limited_or_metadata_only"
    elif spice_vdd_present and not vdd_label_present:
        power_status = "spice_power_pin_without_gds_label"
        recommended_fix = "add_gds_label_required"
        can_enter = "limited_or_metadata_only"
    elif generator_expects_vdd:
        power_status = "missing_power_metadata"
        recommended_fix = "do_not_place_until_macro_fixed"
        can_enter = "limited_or_metadata_only"
    elif openyield_source["source_file_found"] and not openyield_source["pmos_uses_vdd"]:
        power_status = "pass_mux_no_vdd_required"
        recommended_fix = "treat_as_unpowered_pass_mux"
        can_enter = False
    else:
        power_status = "power_semantics_unknown"
        recommended_fix = "manual_layout_review_required"
        safe_for_physical_mapping = False
        can_enter = False

    report: dict[str, Any] = {
        "scope": "step5_5_columnmux_power_metadata_proof",
        "inputs": {
            "tech_dir": str(tech_dir.resolve()),
            "replacement_macros": str((tech_dir / "replacement_macros.json").resolve()),
            "openyield_macro_aliases": str(aliases_path.resolve()),
            "replacement_gds": str(replacement_gds.resolve()),
            "aux_gds": str(aux_gds.resolve()) if aux_gds.exists() else None,
            "sp_lib_dir": str(sp_lib_dir.resolve()),
            "local_netlist_writer": str(local_netlist_writer.resolve()),
            "openyield_source_root": str(openyield_root.resolve()) if openyield_root.exists() else None,
            "openyield_mux_source": str(openyield_mux_source.resolve()) if openyield_mux_source.exists() else None,
        },
        "replacement_macro_binding": {
            "macro_name": replacement["name"],
            "gds": str(replacement_gds.resolve()),
            "pins": replacement.get("pins", []),
            "has_vdd_pin_in_replacement_metadata": any(str(pin.get("name", "")).lower() == "vdd" for pin in replacement.get("pins", [])),
            "has_gnd_pin_in_replacement_metadata": any(str(pin.get("name", "")).lower() == "gnd" for pin in replacement.get("pins", [])),
        },
        "alias_metadata": alias_audit,
        "replacement_gds_audit": replacement_gds_audit,
        "aux_gds_audit": aux_gds_audit,
        "spice_audit": spice_audit,
        "local_fallback_subckt_audit": fallback_subckt,
        "openyield_source_audit": openyield_source,
        "vdd_label_present": vdd_label_present,
        "vdd_shape_candidate_present": vdd_shape_candidate_present,
        "spice_vdd_present": spice_vdd_present,
        "generator_expects_vdd": generator_expects_vdd,
        "power_status": power_status,
        "safe_for_physical_mapping": safe_for_physical_mapping,
        "safe_for_shared_rail": safe_for_shared_rail,
        "can_enter_columnmux_placement": can_enter,
        "requires_metadata_fix": requires_metadata_fix,
        "recommended_fix": recommended_fix,
        "notes": [
            "The active replacement macro is technology/freepdk45/gds_lib/openram_replacements/gen_col_mux.gds, not the separate unlabeled technology/freepdk45/gds_lib/gen_col_mux.gds.",
            "Signal semantics from Step 5.4 remain usable: OUT->mux_out and OUTB->mux_out_b are established.",
            "This report does not modify standalone placement, routing, GDS writer, or hardcell GDS.",
        ],
    }

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")
    print(
        "status={status} vdd_label={vdd_label} vdd_shape={vdd_shape} spice_vdd={spice_vdd} expects_vdd={expects} enter={enter}".format(
            status=power_status,
            vdd_label=vdd_label_present,
            vdd_shape=vdd_shape_candidate_present,
            spice_vdd=spice_vdd_present,
            expects=generator_expects_vdd,
            enter=can_enter,
        )
    )
    return 0


def resolve_existing_path(path_text: str) -> Path:
    raw = Path(path_text)
    candidates = [raw, WORKTREE_ROOT / raw]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve path: {path_text}")


def load_replacement_macro(tech_dir: Path, macro_name: str) -> dict[str, Any]:
    payload = json.loads((tech_dir / "replacement_macros.json").read_text(encoding="utf-8"))
    for item in payload.get("macros", []):
        if item.get("name") == macro_name:
            return item
    raise ValueError(f"replacement macro not found: {macro_name}")


def inspect_alias_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    matches = []
    for item in payload.get("aliases", []):
        module_name = str(item.get("openyield_module", ""))
        macro_name = str(item.get("macro_name", ""))
        if "columnmux" in module_name.lower() or macro_name == "gen_col_mux":
            matches.append(item)
    return {
        "path": str(path.resolve()),
        "matching_alias_entries": matches,
        "has_gen_col_mux_alias_entry": any(str(item.get("macro_name")) == "gen_col_mux" for item in matches),
    }


def inspect_gds(path: Path) -> dict[str, Any]:
    labels, shapes, bbox = read_gds_labels_and_shapes(path)
    label_rows = [label_dict(label) for label in labels]
    matched_shapes = match_label_shapes(labels, shapes)
    suspected_vdd_shapes = find_suspected_vdd_shapes(labels, shapes, bbox)
    return {
        "path": str(path.resolve()),
        "bbox": bbox.to_dict() if bbox else None,
        "labels": label_rows,
        "label_names": [label.text for label in labels],
        "matched_label_shapes": matched_shapes,
        "vdd_label_present": any(label.text.lower() == "vdd" for label in labels),
        "gnd_label_present": any(label.text.lower() == "gnd" for label in labels),
        "suspected_vdd_shapes": suspected_vdd_shapes,
        "shape_count": len(shapes),
    }


def label_dict(label: GdsText) -> dict[str, Any]:
    return {
        "name": label.text,
        "layer": f"{label.layer}/texttype{label.texttype}",
        "x": label.x,
        "y": label.y,
    }


def match_label_shapes(labels: tuple[GdsText, ...], shapes: tuple[GdsShape, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label in labels:
        matched = None
        for shape in shapes:
            if shape.layer != label.layer:
                continue
            if shape.bbox.contains_point(label.x, label.y, tol=0.02):
                matched = shape
                break
        rows.append(
            {
                "label": label.text,
                "layer": label.layer,
                "x": label.x,
                "y": label.y,
                "matched_shape_bbox": matched.bbox.to_dict() if matched else None,
            }
        )
    return rows


def find_suspected_vdd_shapes(labels: tuple[GdsText, ...], shapes: tuple[GdsShape, ...], bbox: BBox | None) -> list[dict[str, Any]]:
    if bbox is None:
        return []
    label_hits: list[tuple[str, GdsShape]] = []
    for label in labels:
        for shape in shapes:
            if shape.layer != label.layer:
                continue
            if shape.bbox.contains_point(label.x, label.y, tol=0.02):
                label_hits.append((label.text.lower(), shape))
                break

    def shape_has_power_label(shape: GdsShape) -> bool:
        for text, hit in label_hits:
            if hit == shape and text in POWER_LABELS:
                return True
        return False

    rows: list[dict[str, Any]] = []
    for shape in shapes:
        if shape.layer != 11:
            continue
        if shape_has_power_label(shape):
            continue
        near_top = (bbox.y1 - shape.bbox.y1) <= 0.18 or (bbox.y1 - shape.bbox.y0) <= 0.25
        long_enough = shape.bbox.width >= 0.18 or shape.bbox.height >= 0.18
        area = shape.bbox.width * shape.bbox.height
        if near_top and long_enough and area >= 0.01:
            rows.append(
                {
                    "layer": shape.layer,
                    "datatype": shape.datatype,
                    "bbox": shape.bbox.to_dict(),
                    "width": shape.bbox.width,
                    "height": shape.bbox.height,
                    "reason": "unlabeled_m1_shape_near_top_boundary",
                }
            )
    return rows


def inspect_spice_dir(sp_lib_dir: Path) -> dict[str, Any]:
    result = {
        "spice_search_root": str(sp_lib_dir.resolve()),
        "subckt_found": False,
        "subckt_file": None,
        "subckt_name": None,
        "subckt_ports": [],
        "subckt_vdd_present": False,
        "subckt_gnd_present": False,
        "status": "spice_subckt_missing",
    }
    pattern = re.compile(r"^\.subckt\s+(\S+)\s+(.*)$", re.IGNORECASE)
    for path in sorted(sp_lib_dir.glob("*.sp")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            match = pattern.match(line.strip())
            if not match:
                continue
            subckt_name = match.group(1)
            if subckt_name.lower() != "gen_col_mux":
                continue
            ports = match.group(2).split()
            result.update(
                {
                    "subckt_found": True,
                    "subckt_file": str(path.resolve()),
                    "subckt_name": subckt_name,
                    "subckt_ports": ports,
                    "subckt_vdd_present": any(port.lower() == "vdd" for port in ports),
                    "subckt_gnd_present": any(port.lower() in {"gnd", "vss"} for port in ports),
                    "status": "subckt_found",
                }
            )
            return result
    return result


def inspect_local_fallback_subckt(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    ports: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip().strip('",')
        if not line.startswith(".SUBCKT gen_col_mux "):
            continue
        ports = line.split()[2:]
        break
    device_lines = [line.strip().strip('",') for line in text.splitlines() if "Mn_bl OUT SEL BL gnd" in line or "Mn_br OUT SEL BR gnd" in line]
    return {
        "fallback_subckt_found": bool(ports),
        "fallback_subckt_ports": ports,
        "fallback_vdd_port_present": any(port.lower() == "vdd" for port in ports),
        "fallback_gnd_port_present": any(port.lower() == "gnd" for port in ports),
        "fallback_device_lines": device_lines,
        "fallback_uses_vdd_in_devices": any(" vdd " in f" {line.lower()} " for line in device_lines),
    }


def inspect_openyield_source(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "source_file_found": False,
            "nodes_include_vdd": False,
            "nodes_include_vss": False,
            "pmos_uses_vdd": False,
            "nmos_uses_vss": False,
            "has_internal_inverter": False,
            "uses_transmission_gate_pair": False,
            "g_s_d_debug_labels_explanation": "unknown",
        }
    text = path.read_text(encoding="utf-8", errors="ignore")
    return {
        "source_file_found": True,
        "source_path": str(path.resolve()),
        "nodes_include_vdd": "'VDD'" in text,
        "nodes_include_vss": "'VSS'" in text,
        "pmos_uses_vdd": "Muxp_BL_" in text and "Muxp_BLB_" in text and "'VDD'" in text,
        "nmos_uses_vss": "Muxn_BL_" in text and "Muxn_BLB_" in text and "'VSS'" in text,
        "has_internal_inverter": "Invp_" in text and "Invn_" in text,
        "uses_transmission_gate_pair": "Muxp_BL_" in text and "Muxn_BL_" in text,
        "sel_drives_transmission_gate": "sel_node = f'SEL{i}'" in text and "Muxn_BL_" in text,
        "g_s_d_debug_labels_explanation": "The replacement GDS carries local transistor terminal labels G/S/D; they are debug/device terminal labels, not exported power pins.",
    }


def render_markdown(report: dict[str, Any]) -> str:
    replacement = report["replacement_gds_audit"]
    spice = report["spice_audit"]
    fallback = report["local_fallback_subckt_audit"]
    source = report["openyield_source_audit"]
    lines = [
        "# OpenYield ColumnMux Power Metadata Report",
        "",
        "This Step 5.5 report is read-only. It audits `gen_col_mux` power metadata proof across GDS, SPICE, replacement metadata, local fallback netlist text, and OpenYield source.",
        "",
        "## Summary",
        "",
        f"- replacement GDS: `{report['inputs']['replacement_gds']}`",
        f"- `gen_col_mux` has VDD label: `{report['vdd_label_present']}`",
        f"- suspected unlabeled VDD shape present: `{report['vdd_shape_candidate_present']}`",
        f"- local SPICE subckt has VDD: `{report['spice_vdd_present']}`",
        f"- OpenYield generator expects VDD: `{report['generator_expects_vdd']}`",
        f"- power_status: `{report['power_status']}`",
        f"- safe_for_physical_mapping: `{report['safe_for_physical_mapping']}`",
        f"- safe_for_shared_rail: `{report['safe_for_shared_rail']}`",
        f"- can_enter_columnmux_placement: `{report['can_enter_columnmux_placement']}`",
        f"- requires_metadata_fix: `{report['requires_metadata_fix']}`",
        f"- recommended_fix: `{report['recommended_fix']}`",
        "",
        "## GDS Labels",
        "",
        f"- replacement GDS labels: `{replacement['label_names']}`",
        "",
        "| Label | Layer | X | Y | Matched shape bbox |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in replacement["matched_label_shapes"]:
        lines.append(
            f"| {row['label']} | {row['layer']} | {row['x']} | {row['y']} | {row['matched_shape_bbox'] or '-'} |"
        )
    lines += [
        "",
        "## Suspected Power Shapes",
        "",
        f"- suspected VDD shapes in replacement GDS: `{len(replacement['suspected_vdd_shapes'])}`",
    ]
    for item in replacement["suspected_vdd_shapes"]:
        lines.append(f"- `{item}`")
    lines += [
        "",
        "## SPICE And Source Audit",
        "",
        f"- local `sp_lib` status: `{spice['status']}`",
        f"- local `sp_lib` subckt ports: `{spice['subckt_ports']}`",
        f"- local fallback `netlist_writer.py` subckt ports: `{fallback['fallback_subckt_ports']}`",
        f"- fallback subckt uses VDD in device bodies: `{fallback['fallback_uses_vdd_in_devices']}`",
        f"- OpenYield source file found: `{source['source_file_found']}`",
        f"- OpenYield nodes include VDD/VSS: `{source['nodes_include_vdd']}` / `{source['nodes_include_vss']}`",
        f"- OpenYield uses PMOS+NMOS transmission gate pair: `{source['uses_transmission_gate_pair']}`",
        f"- OpenYield internal inverter present: `{source['has_internal_inverter']}`",
        f"- OpenYield PMOS devices use VDD: `{source['pmos_uses_vdd']}`",
        f"- `G/S/D` labels explanation: `{source['g_s_d_debug_labels_explanation']}`",
        "",
        "## Conclusion",
        "",
        f"- VDD really exists as label-backed pin: `{report['vdd_label_present']}`",
        f"- VDD may exist only as unlabeled local metal: `{report['vdd_shape_candidate_present']}`",
        f"- metadata alias alone is sufficient: `{report['recommended_fix'] == 'add_metadata_alias_only'}`",
        f"- GDS label update is required: `{report['recommended_fix'] == 'add_gds_label_required'}`",
        f"- shared rail is allowed now: `{report['safe_for_shared_rail']}`",
        f"- column mux placement can proceed now: `{report['can_enter_columnmux_placement']}`",
        "",
        "## Notes",
        "",
    ]
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
