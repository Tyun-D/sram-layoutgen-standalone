from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import run_cell_drc


def _load_cell(cell_dir: Path) -> tuple[str, gdstk.Library, gdstk.Cell, dict[str, list[dict[str, Any]]], list[float]]:
    cell_name = cell_dir.name
    lib = gdstk.read_gds(cell_dir / f"{cell_name}.gds")
    top = next(cell for cell in lib.cells if cell.name == cell_name)
    bbox = top.bounding_box()
    return cell_name, lib, top, json.loads((cell_dir / f"{cell_name}_pin_map.json").read_text(encoding="utf-8")), [float(bbox[0][0]), float(bbox[0][1]), float(bbox[1][0]), float(bbox[1][1])]


def _pin_entry(pin_map: dict[str, list[dict[str, Any]]], pin_name: str) -> dict[str, Any]:
    return dict(pin_map[pin_name][0])


def _shift_pin(pin: dict[str, Any], dx: float, dy: float, x0: float, y0: float) -> dict[str, float]:
    return {
        "lx": round(float(pin["lx"]) - x0 + dx, 6),
        "by": round(float(pin["by"]) - y0 + dy, 6),
        "rx": round(float(pin["rx"]) - x0 + dx, 6),
        "uy": round(float(pin["uy"]) - y0 + dy, 6),
        "cx": round((float(pin["lx"]) + float(pin["rx"])) * 0.5 - x0 + dx, 6),
        "cy": round((float(pin["by"]) + float(pin["uy"])) * 0.5 - y0 + dy, 6),
    }


def _add_label(cell: gdstk.Cell, text: str, box: dict[str, float]) -> None:
    cell.add(gdstk.Label(text, (box["cx"], box["cy"]), layer=11, texttype=0))


def _add_stitch(cell: gdstk.Cell, left: dict[str, float], right: dict[str, float]) -> None:
    cell.add(gdstk.rectangle((left["rx"], left["by"]), (right["lx"], left["uy"]), layer=11, datatype=0))


def _candidate_spec(name: str, spacing: float, with_wrapper: bool) -> dict[str, Any]:
    return {"name": name, "spacing": spacing, "with_wrapper": with_wrapper}


def _component_for_label(graph: dict[str, Any], label: str) -> str | None:
    hits = graph["pin_labels"].get(label, [])
    if not hits or not hits[0]["shape_ids"]:
        return None
    shape_id = hits[0]["shape_ids"][0]
    for component in graph["components"]:
        if shape_id in component["members"]:
            return component["component_id"]
    return None


def _write_sram_spec(out_dir: Path, top_name: str, generator: str) -> None:
    spec = {
        "word_size": 0,
        "num_words": 0,
        "words_per_row": 0,
        "rows": 0,
        "cols": 0,
        "tech": "FreePDK45",
        "mux": 1,
        "power": {"vdd": "m1", "vss": "m1"},
        "generator": generator,
        "output": top_name,
        "diagnostic_only": True,
        "not_reusable_composite": True,
        "approved_child_geometry_modified": False,
    }
    (out_dir / "SRAM_SPEC.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    (out_dir / "SRAM_SPEC.md").write_text("# SRAM_SPEC\n\n- diagnostic_only: `True`\n- not_reusable_composite: `True`\n", encoding="utf-8")


def qualify_pinv_tg_interfaces(reusable_root: Path, out_dir: Path, drc_deck: Path, klayout: Path) -> dict[str, Any]:
    pinv_dir = reusable_root / "PINV_NW250_PW500_L50"
    tg_dir = reusable_root / "TRANSMISSION_GATE_NW250_PW500_L50"
    pinv_name, pinv_lib, pinv_cell, pinv_pin_map, pinv_bbox = _load_cell(pinv_dir)
    tg_name, tg_lib, tg_cell, tg_pin_map, tg_bbox = _load_cell(tg_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    candidates = [
        _candidate_spec("DIRECT_BOUNDARY_ABUTMENT", 0.0, False),
        _candidate_spec("RAIL_ALIGNED_SPACED_ROW_WITH_POWER_STITCH", 0.14, False),
        _candidate_spec("COMMON_WRAPPER_ENVELOPE_WITH_SPACED_CHILDREN", 0.14, True),
    ]
    rows: list[dict[str, Any]] = []
    drc_rows: list[dict[str, Any]] = []
    pinv_width = round(pinv_bbox[2] - pinv_bbox[0], 6)
    pinv_height = round(pinv_bbox[3] - pinv_bbox[1], 6)
    tg_height = round(tg_bbox[3] - tg_bbox[1], 6)
    height_delta = round(abs(pinv_height - tg_height), 6)
    for candidate in candidates:
        candidate_dir = out_dir / candidate["name"].lower()
        candidate_dir.mkdir(parents=True, exist_ok=True)
        top_name = f"M12C4R_{candidate['name']}"
        lib = gdstk.Library(unit=pinv_lib.unit, precision=pinv_lib.precision)
        top = lib.new_cell(top_name)
        imported_names = set()
        for source_lib in (pinv_lib, tg_lib):
            for cell in source_lib.cells:
                if cell.name in imported_names:
                    continue
                imported_names.add(cell.name)
                lib.add(cell.copy(cell.name))
        pinv_dx = 0.0
        pinv_dy = 0.0
        tg_dx = pinv_width + candidate["spacing"]
        tg_dy = 0.0
        top.add(gdstk.Reference(pinv_cell.name, origin=(pinv_dx - pinv_bbox[0], pinv_dy - pinv_bbox[1])))
        top.add(gdstk.Reference(tg_cell.name, origin=(tg_dx - tg_bbox[0], tg_dy - tg_bbox[1])))

        pinv_vdd = _shift_pin(_pin_entry(pinv_pin_map, "VDD"), pinv_dx, pinv_dy, pinv_bbox[0], pinv_bbox[1])
        pinv_vss = _shift_pin(_pin_entry(pinv_pin_map, "VSS"), pinv_dx, pinv_dy, pinv_bbox[0], pinv_bbox[1])
        tg_vdd = _shift_pin(_pin_entry(tg_pin_map, "VDD"), tg_dx, tg_dy, tg_bbox[0], tg_bbox[1])
        tg_vss = _shift_pin(_pin_entry(tg_pin_map, "VSS"), tg_dx, tg_dy, tg_bbox[0], tg_bbox[1])
        _add_stitch(top, pinv_vdd, tg_vdd)
        _add_stitch(top, pinv_vss, tg_vss)
        if candidate["with_wrapper"]:
            wrapper_x1 = max(pinv_width, tg_dx + (tg_bbox[2] - tg_bbox[0])) + 0.055
            wrapper_y1 = max(pinv_height, tg_height)
            top.add(gdstk.rectangle((0.0, 0.0), (wrapper_x1, wrapper_y1), layer=239, datatype=0))

        for label_name, box in {
            "PINV_VDD": pinv_vdd,
            "PINV_VSS": pinv_vss,
            "PINV_A": _shift_pin(_pin_entry(pinv_pin_map, "A"), pinv_dx, pinv_dy, pinv_bbox[0], pinv_bbox[1]),
            "PINV_Z": _shift_pin(_pin_entry(pinv_pin_map, "Z"), pinv_dx, pinv_dy, pinv_bbox[0], pinv_bbox[1]),
            "TG_VDD": tg_vdd,
            "TG_VSS": tg_vss,
            "TG_IN": _shift_pin(_pin_entry(tg_pin_map, "IN"), tg_dx, tg_dy, tg_bbox[0], tg_bbox[1]),
            "TG_OUT": _shift_pin(_pin_entry(tg_pin_map, "OUT"), tg_dx, tg_dy, tg_bbox[0], tg_bbox[1]),
        }.items():
            _add_label(top, label_name, box)

        gds_path = candidate_dir / f"M12C4R_{candidate['name'].lower()}.gds"
        lib.write_gds(gds_path)
        _write_sram_spec(candidate_dir, top_name, "M12C4R_pinv_tg_interface_qualifier")
        graph = extract_physical_connectivity(gds_path, top_name)
        pinv_vdd_comp = _component_for_label(graph, "PINV_VDD")
        tg_vdd_comp = _component_for_label(graph, "TG_VDD")
        pinv_vss_comp = _component_for_label(graph, "PINV_VSS")
        tg_vss_comp = _component_for_label(graph, "TG_VSS")
        pinv_a_comp = _component_for_label(graph, "PINV_A")
        tg_in_comp = _component_for_label(graph, "TG_IN")
        drc = run_cell_drc(klayout, drc_deck, gds_path, top_name, candidate_dir)
        connectivity_passed = (
            pinv_vdd_comp is not None
            and pinv_vdd_comp == tg_vdd_comp
            and pinv_vss_comp is not None
            and pinv_vss_comp == tg_vss_comp
            and pinv_vdd_comp != pinv_vss_comp
            and pinv_a_comp != tg_in_comp
        )
        rows.append(
            {
                "candidate_name": candidate["name"],
                "gds_path": str(gds_path),
                "spacing_um": candidate["spacing"],
                "uses_wrapper": candidate["with_wrapper"],
                "drc_passed": drc["drc_passed"],
                "marker_count": drc["marker_count"],
                "power_connectivity_passed": connectivity_passed,
            }
        )
        drc_rows.append(
            {
                "candidate_name": candidate["name"],
                "marker_count": drc["marker_count"],
                "drc_passed": drc["drc_passed"],
                "lyrdb_path": drc["marker_report_path"],
                "connectivity_passed": connectivity_passed,
                "graph_path": str(candidate_dir / "connectivity.json"),
            }
        )
        (candidate_dir / "connectivity.json").write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        (candidate_dir / "drc_report.json").write_text(json.dumps(drc, indent=2) + "\n", encoding="utf-8")

    pass_map = {row["candidate_name"]: bool(row["drc_passed"] and row["power_connectivity_passed"]) for row in rows}
    selected = "BLOCKING_INCOMPATIBLE"
    interface_status = "BLOCKING_INCOMPATIBLE"
    primitive_geometry_normalization_required = True
    if pass_map["DIRECT_BOUNDARY_ABUTMENT"]:
        selected = "DIRECT_BOUNDARY_ABUTMENT"
        interface_status = "LOCKED_COMPOSITION_COMPATIBLE_V1"
        primitive_geometry_normalization_required = False
    elif pass_map["RAIL_ALIGNED_SPACED_ROW_WITH_POWER_STITCH"]:
        selected = "RAIL_ALIGNED_SPACED_ROW_WITH_POWER_STITCH"
        interface_status = "COMPATIBLE_WITH_SPACER_AND_RAIL_STITCH"
        primitive_geometry_normalization_required = False
    elif pass_map["COMMON_WRAPPER_ENVELOPE_WITH_SPACED_CHILDREN"]:
        selected = "COMMON_WRAPPER_ENVELOPE_WITH_SPACED_CHILDREN"
        interface_status = "COMPATIBLE_WITH_SPACER_AND_RAIL_STITCH"
        primitive_geometry_normalization_required = False
    return {
        "rows": rows,
        "drc_rows": drc_rows,
        "summary": {
            "pinv_height_um": pinv_height,
            "transmission_gate_height_um": tg_height,
            "height_delta_um": height_delta,
            "height_delta_source_layer": "N_WELL_AND_VTG_TOP_EDGE",
            "direct_abutment_drc_passed": pass_map["DIRECT_BOUNDARY_ABUTMENT"],
            "spaced_power_stitch_drc_passed": pass_map["RAIL_ALIGNED_SPACED_ROW_WITH_POWER_STITCH"],
            "common_wrapper_drc_passed": pass_map["COMMON_WRAPPER_ENVELOPE_WITH_SPACED_CHILDREN"],
            "selected_interface_architecture": selected,
            "interface_compatibility_status": interface_status,
            "primitive_geometry_normalization_required": primitive_geometry_normalization_required,
            "actual_well_spacing_risk_detected": interface_status == "BLOCKING_INCOMPATIBLE",
        },
    }
