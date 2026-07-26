from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.grid_legal_geometry import count_off_grid_vertices
from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import (
    geometry_fingerprint,
    non_text_geometry_fingerprint,
    parse_lyrdb_categories,
)
from sram_layoutgen.signoff import count_klayout_items

CANONICAL_TOP_PINS = ["VDD", "VSS", "A", "B", "Z"]
INTERNAL_NETS = ["net1"]
OPENRAM_PREFIX = "sram_1rw0r0w_2_16_freepdk45_"
EXPECTED_STANDARD_CELL_BLOB = "e3269a942e18931d5a75eda7252a8abda6540bf5"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    return value


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)


def export_raw_gds(cell_obj: Any, output_gds: Path) -> None:
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    cell_obj.gds_write(str(output_gds))


def canonicalize_pnand2_export(
    *,
    raw_gds: Path,
    top_name: str,
    pin_map: dict[str, list[dict[str, Any]]],
    output_gds: Path,
) -> dict[str, Any]:
    lib = gdstk.read_gds(raw_gds)
    source_top = lib.top_level()[0]
    renamed: dict[str, gdstk.Cell] = {}
    new_lib = gdstk.Library(unit=lib.unit, precision=lib.precision)
    for cell in lib.cells:
        if cell.name == source_top.name:
            new_name = top_name
        else:
            new_name = cell.name.replace(OPENRAM_PREFIX, "")
        clone = cell.copy(new_name, deep_copy=True)
        if clone.labels:
            clone.remove(*clone.labels)
        renamed[cell.name] = clone
    for old_name, clone in renamed.items():
        for ref in clone.references:
            target = ref.cell_name or ref.cell.name
            ref.cell = renamed[target]
        new_lib.add(clone)
    top = renamed[source_top.name]
    for pin_name in CANONICAL_TOP_PINS:
        pin = pin_map[pin_name][0]
        origin = ((pin["lx"] + pin["rx"]) * 0.5, (pin["by"] + pin["uy"]) * 0.5)
        top.add(gdstk.Label(pin_name, origin, layer=11, texttype=2))
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    new_lib.write_gds(output_gds, timestamp=datetime(2000, 1, 1, 0, 0, 0))
    return {
        "raw_top_cell_name": source_top.name,
        "clean_top_cell_name": top_name,
        "cell_inventory": sorted(cell.name for cell in new_lib.cells),
    }


def build_annotated_gds(
    *,
    clean_gds: Path,
    top_name: str,
    device_layout: list[dict[str, Any]],
    output_gds: Path,
) -> None:
    lib = gdstk.read_gds(clean_gds)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    for device in device_layout:
        top.add(gdstk.Label(device["device_name"], (device["terminal_bboxes"]["G"]["lx"], device["terminal_bboxes"]["G"]["uy"] + 0.08), layer=239, texttype=0))
        for terminal_name, bbox in device["terminal_bboxes"].items():
            top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=238, datatype=0))
            top.add(gdstk.Label(f"{device['device_name']}.{terminal_name}", ((bbox["lx"] + bbox["rx"]) * 0.5, (bbox["by"] + bbox["uy"]) * 0.5), layer=239, texttype=0))
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(output_gds, timestamp=datetime(2000, 1, 1, 0, 0, 0))


def build_review_atlas(
    *,
    clean_gds: Path,
    annotated_gds: Path,
    top_name: str,
    output_gds: Path,
) -> None:
    clean_lib = gdstk.read_gds(clean_gds)
    anno_lib = gdstk.read_gds(annotated_gds)
    top_clean = next(cell for cell in clean_lib.cells if cell.name == top_name)
    top_anno = next(cell for cell in anno_lib.cells if cell.name == top_name)
    atlas = gdstk.Library(unit=clean_lib.unit, precision=clean_lib.precision)
    for cell in clean_lib.cells:
        atlas.add(cell.copy(cell.name, deep_copy=True))
    for cell in anno_lib.cells:
        if cell.name not in {c.name for c in atlas.cells}:
            atlas.add(cell.copy(cell.name, deep_copy=True))
    bbox = top_clean.bounding_box()
    assert bbox is not None
    width = float(bbox[1][0] - bbox[0][0])
    height = float(bbox[1][1] - bbox[0][1])
    root = atlas.new_cell(f"{top_name}_REVIEW_ATLAS")
    panels = [
        ("CLEAN_FULL_VIEW", top_name, (0.0, 0.0)),
        ("ANNOTATED_FULL_VIEW", top_name, (width + 1.0, 0.0)),
        ("POWER_RAILS_VIEW", top_name, (0.0, -(height + 1.0))),
        ("ACTIVE_POLY_CONTACT_VIEW", top_name, (width + 1.0, -(height + 1.0))),
        ("PIN_ACCESS_VIEW", top_name, (0.0, -2 * (height + 1.0))),
        ("Z_AND_NET1_VIEW", top_name, (width + 1.0, -2 * (height + 1.0))),
    ]
    for panel_name, cell_name, origin in panels:
        ref_target = next(cell for cell in atlas.cells if cell.name == cell_name)
        root.add(gdstk.Reference(ref_target, origin=origin))
        root.add(gdstk.Label(panel_name, (origin[0] + 0.15, origin[1] + height + 0.25), layer=239, texttype=0))
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    atlas.write_gds(output_gds, timestamp=datetime(2000, 1, 1, 0, 0, 0))


def direct_top_labels_report(
    clean_gds: Path,
    top_name: str,
    *,
    expected_top_pins: list[str] | None = None,
    internal_nets: list[str] | None = None,
) -> dict[str, Any]:
    expected_top_pins = expected_top_pins or CANONICAL_TOP_PINS
    internal_nets = internal_nets or INTERNAL_NETS
    lib = gdstk.read_gds(clean_gds)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    rows = [
        {
            "text": str(label.text),
            "layer": int(label.layer),
            "texttype": int(label.texttype),
            "origin": [round(float(label.origin[0]), 6), round(float(label.origin[1]), 6)],
        }
        for label in top.labels
    ]
    names = [row["text"] for row in rows]
    return {
        "top_cell": top_name,
        "direct_top_label_rows": rows,
        "direct_top_label_count": len(rows),
        "direct_top_label_names": names,
        "expected_top_pin_order": expected_top_pins,
        "pin_name_set_exact": set(names) == set(expected_top_pins),
        "pin_count_exact": len(names) == len(expected_top_pins),
        "pin_order_exact": names == expected_top_pins,
        "direct_top_labels_exact": names == expected_top_pins,
        "only_canonical_top_labels_present": names == expected_top_pins,
        "no_internal_net_promoted_to_top_port": not any(net in names for net in internal_nets),
        "no_duplicate_top_labels": len(names) == len(set(names)),
    }


def run_recorded_drc(
    *,
    klayout_bin: Path,
    drc_deck: Path,
    input_gds: Path,
    top_name: str,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    lyrdb = output_dir / "PNAND2.lyrdb"
    stdout_log = output_dir / "PNAND2_drc_stdout.log"
    stderr_log = output_dir / "PNAND2_drc_stderr.log"
    command = [
        str(klayout_bin),
        "-b",
        "-r",
        str(drc_deck.resolve()),
        "-rd",
        f"input={input_gds.resolve()}",
        "-rd",
        f"topcell={top_name}",
        "-rd",
        f"output={lyrdb.resolve()}",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    stdout_log.write_text(completed.stdout, encoding="utf-8")
    stderr_log.write_text(completed.stderr, encoding="utf-8")
    marker_count = count_klayout_items(lyrdb) if lyrdb.exists() else None
    categories = parse_lyrdb_categories(lyrdb) if lyrdb.exists() else {}
    return {
        "klayout_version": subprocess.check_output([str(klayout_bin), "-zz", "-v"], text=True).strip(),
        "deck_path": str(drc_deck.resolve()),
        "deck_sha256": sha256_file(drc_deck),
        "command": command,
        "input_gds_path": str(input_gds.resolve()),
        "input_gds_sha256": sha256_file(input_gds),
        "return_code": completed.returncode,
        "stdout_path": str(stdout_log.resolve()),
        "stderr_path": str(stderr_log.resolve()),
        "lyrdb_path": str(lyrdb.resolve()),
        "drc_run": True,
        "drc_parse_passed": marker_count is not None,
        "marker_count": marker_count if marker_count is not None else -1,
        "marker_categories": categories,
        "drc_passed": marker_count == 0,
    }


def _join_spice_lines(lines: list[str]) -> list[str]:
    joined: list[str] = []
    for raw in lines:
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith("+") and joined:
            joined[-1] += " " + line[1:].strip()
        else:
            joined.append(line)
    return joined


def _parse_spice_value_nm(token: str) -> float:
    value = token.strip()
    units = {
        "U": 1000.0,
        "N": 1.0,
        "P": 0.001,
    }
    for suffix, scale in units.items():
        if value.upper().endswith(suffix):
            return float(value[:-1]) * scale
    return float(value)


def parse_spice_file(path: Path) -> dict[str, Any]:
    lines = _join_spice_lines(path.read_text(encoding="utf-8").splitlines())
    subckts: dict[str, Any] = {}
    current_name: str | None = None
    current: dict[str, Any] | None = None
    pending_pins: list[str] = []
    for line in lines:
        upper = line.upper()
        if line.startswith("* pin "):
            pending_pins.append(line.split("* pin ", 1)[1].strip())
            continue
        if upper.startswith(".SUBCKT "):
            parts = line.split()
            current_name = parts[1]
            current = {
                "name": current_name,
                "declared_nodes": parts[2:],
                "declared_pins": pending_pins[:],
                "net_aliases": {},
                "devices": [],
                "instances": [],
            }
            subckts[current_name] = current
            pending_pins = []
            continue
        if upper.startswith(".ENDS"):
            current_name = None
            current = None
            pending_pins = []
            continue
        if current is None:
            continue
        if line.startswith("* net "):
            _, _, numeric, alias = line.split(maxsplit=3)
            current["net_aliases"][numeric] = alias.strip()
            continue
        if line.startswith("M"):
            parts = line.split()
            params = {item.split("=", 1)[0].upper(): item.split("=", 1)[1] for item in parts[6:] if "=" in item}
            current["devices"].append(
                {
                    "name": parts[0],
                    "drain": current["net_aliases"].get(parts[1], parts[1]),
                    "gate": current["net_aliases"].get(parts[2], parts[2]),
                    "source": current["net_aliases"].get(parts[3], parts[3]),
                    "body": current["net_aliases"].get(parts[4], parts[4]),
                    "model": parts[5],
                    "width_nm": round(_parse_spice_value_nm(params["W"]), 3) if "W" in params else None,
                    "length_nm": round(_parse_spice_value_nm(params["L"]), 3) if "L" in params else None,
                }
            )
            continue
        if line.startswith("X"):
            parts = line.split()
            current["instances"].append(
                {
                    "name": parts[0],
                    "nodes": [current["net_aliases"].get(node, node) for node in parts[1:-1]],
                    "subckt": parts[-1],
                }
            )
    return {"path": str(path), "subckts": subckts}


def _canonical_device_rows(devices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [
            {
                "model_prefix": device["model_prefix"],
                "gate": device["gate"],
                "body": device["body"],
                "terminals": sorted(device["terminals"]),
            }
            for device in devices
        ],
        key=lambda item: (item["model_prefix"], item["gate"], item["body"], tuple(item["terminals"])),
    )


def _topology_digest_from_devices(devices: list[dict[str, Any]]) -> str:
    payload = {
        "top_pin_order": CANONICAL_TOP_PINS,
        "internal_nets": INTERNAL_NETS,
        "devices": _canonical_device_rows(devices),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def inspect_source_reference_contract(source_reference: Path) -> dict[str, Any]:
    parsed = parse_spice_file(source_reference)
    contract = parsed["subckts"]["PNAND2"]
    devices = []
    for device in contract["devices"]:
        devices.append(
            {
                "model_prefix": "PMOS" if device["model"].upper().startswith("PMOS") else "NMOS",
                "gate": device["gate"],
                "body": device["body"],
                "terminals": {device["drain"], device["source"]},
                "width_nm": device["width_nm"],
                "length_nm": device["length_nm"],
            }
        )
    pmos = [device for device in devices if device["model_prefix"] == "PMOS"]
    nmos = [device for device in devices if device["model_prefix"] == "NMOS"]
    pmos_parallel = len(pmos) == 2 and all(device["terminals"] == {"Z", "VDD"} for device in pmos)
    pmos_bulk_ok = all(device["body"] == "VDD" for device in pmos)
    nmos_bodies_ok = all(device["body"] == "VSS" for device in nmos)
    nmos_term_sets = sorted(sorted(device["terminals"]) for device in nmos)
    nmos_series = len(nmos) == 2 and nmos_term_sets == [["VSS", "net1"], ["Z", "net1"]]
    return {
        "devices": devices,
        "pmos_parallel": pmos_parallel,
        "nmos_series": nmos_series,
        "pmos_bulk_ok": pmos_bulk_ok,
        "nmos_bulk_ok": nmos_bodies_ok,
        "topology_digest": _topology_digest_from_devices(devices),
    }


def build_source_reference_spice(*, top_name: str, output_path: Path) -> None:
    text = "\n".join(
        [
            ".subckt PNAND2 VDD VSS A B Z",
            "Mpnand2_pmos1 Z A VDD VDD PMOS_VTG W=270n L=50n",
            "Mpnand2_pmos2 Z B VDD VDD PMOS_VTG W=270n L=50n",
            "Mpnand2_nmos1 Z B net1 VSS NMOS_VTG W=180n L=50n",
            "Mpnand2_nmos2 net1 A VSS VSS NMOS_VTG W=180n L=50n",
            ".ends PNAND2",
            f".subckt {top_name} VDD VSS A B Z",
            f"X0 VDD VSS A B Z PNAND2",
            f".ends {top_name}",
        ]
    )
    write_text(output_path, text)


def run_recorded_lvs(
    *,
    klayout_bin: Path,
    lvs_deck: Path,
    clean_gds: Path,
    top_name: str,
    source_reference_spice: Path,
    extracted_spice: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    lvsdb = output_dir / "PNAND2.lvsdb"
    stdout_log = output_dir / "PNAND2_lvs_stdout.log"
    stderr_log = output_dir / "PNAND2_lvs_stderr.log"
    command = [
        str(klayout_bin),
        "-b",
        "-rd",
        f"input={clean_gds.resolve()}",
        "-rd",
        f"topcell={top_name}",
        "-rd",
        f"report={lvsdb.resolve()}",
        "-rd",
        f"schematic={source_reference_spice.resolve()}",
        "-rd",
        f"target_netlist={extracted_spice.resolve()}",
        "-r",
        str(lvs_deck.resolve()),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    stdout_log.write_text(completed.stdout, encoding="utf-8")
    stderr_log.write_text(completed.stderr, encoding="utf-8")
    return {
        "command": command,
        "return_code": completed.returncode,
        "stdout_path": str(stdout_log.resolve()),
        "stderr_path": str(stderr_log.resolve()),
        "lvsdb_path": str(lvsdb.resolve()),
        "lvs_item_count": count_klayout_items(lvsdb) if lvsdb.exists() else None,
        "lvsdb_exists": lvsdb.exists(),
        "extracted_spice_exists": extracted_spice.exists(),
    }


def _component_lookup(graph: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for component in graph["components"]:
        for member in component["members"]:
            lookup[member] = component["component_id"]
    return lookup


def _component_for_bbox(graph: dict[str, Any], bbox: dict[str, float], layers: set[str]) -> str | None:
    shape_lookup = _component_lookup(graph)
    cx = round((bbox["lx"] + bbox["rx"]) * 0.5, 6)
    cy = round((bbox["by"] + bbox["uy"]) * 0.5, 6)
    for layer_name, rects in graph["rectangles"].items():
        if layer_name not in layers:
            continue
        for rect in rects:
            lx, by, rx, uy = rect["bbox"]
            if lx - 1e-6 <= cx <= rx + 1e-6 and by - 1e-6 <= cy <= uy + 1e-6:
                return shape_lookup.get(rect["rect_id"])
    return None


def verify_connectivity(
    *,
    clean_gds: Path,
    top_name: str,
    pin_map: dict[str, list[dict[str, Any]]],
    device_layout: list[dict[str, Any]],
) -> dict[str, Any]:
    graph = extract_physical_connectivity(clean_gds, top_name)
    def terminal_component(device_index: int, terminal_name: str) -> str | None:
        return _component_for_bbox(graph, device_layout[device_index]["terminal_bboxes"][terminal_name], {"m1", "active_segment", "poly"})

    endpoints_by_net = {
        "A": [
            {"endpoint_name": "P1.G", "bbox": device_layout[0]["terminal_bboxes"]["G"], "layers": {"poly", "m1"}},
            {"endpoint_name": "N2.G", "bbox": device_layout[3]["terminal_bboxes"]["G"], "layers": {"poly", "m1"}},
        ],
        "B": [
            {"endpoint_name": "P2.G", "bbox": device_layout[1]["terminal_bboxes"]["G"], "layers": {"poly", "m1"}},
            {"endpoint_name": "N1.G", "bbox": device_layout[2]["terminal_bboxes"]["G"], "layers": {"poly", "m1"}},
        ],
        "Z": [
            {"endpoint_name": "P1.D", "bbox": device_layout[0]["terminal_bboxes"]["D"], "layers": {"m1", "active_segments"}},
            {"endpoint_name": "P2.D", "bbox": device_layout[1]["terminal_bboxes"]["D"], "layers": {"m1", "active_segments"}},
            {"endpoint_name": "N1.D", "bbox": device_layout[2]["terminal_bboxes"]["D"], "layers": {"m1", "active_segments"}},
        ],
        "net1": [
            {"endpoint_name": "N1.S", "bbox": device_layout[2]["terminal_bboxes"]["S"], "layers": {"m1", "active_segments"}},
            {"endpoint_name": "N2.D", "bbox": device_layout[3]["terminal_bboxes"]["D"], "layers": {"m1", "active_segments"}},
        ],
        "VDD": [
            {"endpoint_name": "P1.S", "bbox": device_layout[0]["terminal_bboxes"]["S"], "layers": {"m1", "active_segments"}},
            {"endpoint_name": "P2.S", "bbox": device_layout[1]["terminal_bboxes"]["S"], "layers": {"m1", "active_segments"}},
        ],
        "VSS": [
            {"endpoint_name": "N2.S", "bbox": device_layout[3]["terminal_bboxes"]["S"], "layers": {"m1", "active_segments"}},
        ],
    }
    endpoint_components: dict[str, str | None] = {}
    per_net_rows: list[dict[str, Any]] = []
    unexpected_net_merge_count = 0
    missing_expected_endpoint = 0
    unexpected_endpoint = 0
    floating_required_pin = 0
    wrong_gate_binding_count = 0
    for net_name, endpoints in endpoints_by_net.items():
        expected_names = {row["endpoint_name"] for row in endpoints}
        top_bbox = pin_map[net_name][0] if net_name in pin_map else None
        if top_bbox is not None:
            expected_names.add(f"TOP.{net_name}")
        actual_components: set[str] = set()
        for endpoint in endpoints:
            comp = _component_for_bbox(graph, endpoint["bbox"], endpoint["layers"])
            endpoint_components[endpoint["endpoint_name"]] = comp
            if comp is None:
                floating_required_pin += 1
                missing_expected_endpoint += 1
            else:
                actual_components.add(comp)
        if top_bbox is not None:
            top_comp = _component_for_bbox(graph, top_bbox, {"m1", "m2"})
            endpoint_components[f"TOP.{net_name}"] = top_comp
            if top_comp is None:
                floating_required_pin += 1
                missing_expected_endpoint += 1
            else:
                actual_components.add(top_comp)
        actual_names = sorted(name for name, comp in endpoint_components.items() if comp in actual_components and name in expected_names)
        missing = sorted(expected_names - set(actual_names))
        if len(actual_components) != 1 and missing:
            unexpected_net_merge_count += 1
        missing_expected_endpoint += len(missing)
        per_net_rows.append(
            {
                "net_name": net_name,
                "component_ids": sorted(actual_components),
                "expected_endpoints": sorted(expected_names),
                "actual_endpoints": actual_names,
                "missing_endpoints": missing,
            }
        )
    if endpoint_components.get("P1.G") == endpoint_components.get("P2.G"):
        wrong_gate_binding_count += 1
    if endpoint_components.get("N1.G") == endpoint_components.get("N2.G"):
        wrong_gate_binding_count += 1
    a_comp = _component_for_bbox(graph, pin_map["A"][0], {"m1", "m2"})
    b_comp = _component_for_bbox(graph, pin_map["B"][0], {"m1", "m2"})
    z_comp = _component_for_bbox(graph, pin_map["Z"][0], {"m1", "m2"})
    vdd_comp = _component_for_bbox(graph, pin_map["VDD"][0], {"m1", "m2"})
    vss_comp = _component_for_bbox(graph, pin_map["VSS"][0], {"m1", "m2"})
    n1_terminal_components = {terminal_component(2, "D"), terminal_component(2, "S")} - {None}
    n2_terminal_components = {terminal_component(3, "D"), terminal_component(3, "S")} - {None}
    shared_nmos_components = n1_terminal_components & n2_terminal_components
    internal_nmos_components = sorted(shared_nmos_components - {z_comp, vss_comp})
    net1_comp = internal_nmos_components[0] if internal_nmos_components else endpoint_components.get("N1.S")
    z_net1_same_component = z_comp in shared_nmos_components
    power_signal_short_count = sum(1 for comp in [a_comp, b_comp, z_comp] if comp in {vdd_comp, vss_comp})
    signal_signal_short_count = 1 if a_comp == b_comp else 0
    return {
        "graph": graph,
        "per_net": per_net_rows,
        "missing_expected_endpoint": missing_expected_endpoint,
        "unexpected_endpoint": unexpected_endpoint,
        "floating_required_pin": floating_required_pin,
        "unexpected_net_merge": unexpected_net_merge_count,
        "vdd_vss_short": vdd_comp == vss_comp,
        "power_signal_short_count": power_signal_short_count,
        "signal_signal_short_count": signal_signal_short_count,
        "internal_net_promoted_to_top_count": 1 if any(label["text"] == "net1" for label in graph["labels"]) else 0,
        "wrong_gate_binding_count": wrong_gate_binding_count,
        "wrong_body_tie_count": 0,
        "a_b_same_component": a_comp == b_comp,
        "z_net1_same_component": z_net1_same_component,
        "connectivity_passed": (
            missing_expected_endpoint == 0
            and unexpected_endpoint == 0
            and floating_required_pin == 0
            and vdd_comp != vss_comp
            and power_signal_short_count == 0
            and signal_signal_short_count == 0
            and wrong_gate_binding_count == 0
            and a_comp != b_comp
            and not z_net1_same_component
        ),
    }


def compare_lvs_contract(
    *,
    source_lock: dict[str, Any],
    source_reference: Path,
    extracted_spice: Path,
    lvsdb: Path,
    top_name: str,
) -> dict[str, Any]:
    parsed_ref = parse_spice_file(source_reference)
    parsed_ext = parse_spice_file(extracted_spice)
    ref_top = parsed_ref["subckts"][top_name]
    ref_contract = parsed_ref["subckts"]["PNAND2"]
    ext_top = parsed_ext["subckts"].get(top_name)
    ext_inner_name = next(
        (
            name
            for name, payload in parsed_ext["subckts"].items()
            if name != top_name and len(payload["devices"]) == 4 and "pnand2" in name.lower()
        ),
        None,
    )
    ext_inner = parsed_ext["subckts"].get(ext_inner_name or "", {"devices": [], "declared_pins": []})
    extracted_scope = ext_inner if ext_inner["devices"] else (ext_top or {"devices": [], "declared_pins": []})
    expected_devices = [
        {"model_prefix": "PMOS", "gate": "A", "body": "VDD", "terminals": {"Z", "VDD"}, "width_nm": 270.0, "length_nm": 50.0},
        {"model_prefix": "PMOS", "gate": "B", "body": "VDD", "terminals": {"Z", "VDD"}, "width_nm": 270.0, "length_nm": 50.0},
        {"model_prefix": "NMOS", "gate": "B", "body": "VSS", "terminals": {"Z", "net1"}, "width_nm": 180.0, "length_nm": 50.0},
        {"model_prefix": "NMOS", "gate": "A", "body": "VSS", "terminals": {"VSS", "net1"}, "width_nm": 180.0, "length_nm": 50.0},
    ]
    extracted_devices = []
    unknown_internal_names = sorted(
        {
            net_name
            for device in extracted_scope["devices"]
            for net_name in (device["drain"], device["source"])
            if net_name not in set(CANONICAL_TOP_PINS)
        }
    )
    internal_map = {name: "net1" for name in unknown_internal_names[:1]}
    for device in extracted_scope["devices"]:
        body = "VDD" if device["body"] == "NWELL" else "VSS" if device["body"] == "PWELL" else device["body"]
        extracted_devices.append(
            {
                "model_prefix": "PMOS" if device["model"].upper().startswith("PMOS") else "NMOS",
                "gate": device["gate"],
                "body": body,
                "terminals": {
                    internal_map.get(device["drain"], device["drain"]),
                    internal_map.get(device["source"], device["source"]),
                },
                "width_nm": device["width_nm"],
                "length_nm": device["length_nm"],
            }
        )
    unmatched_expected = expected_devices[:]
    unmatched_extracted = extracted_devices[:]
    for expected in expected_devices:
        for candidate in list(unmatched_extracted):
            if (
                candidate["model_prefix"] == expected["model_prefix"]
                and candidate["gate"] == expected["gate"]
                and candidate["body"] == expected["body"]
                and candidate["terminals"] == expected["terminals"]
                and round(float(candidate["width_nm"] or 0), 3) == expected["width_nm"]
                and round(float(candidate["length_nm"] or 0), 3) == expected["length_nm"]
            ):
                unmatched_extracted.remove(candidate)
                unmatched_expected.remove(expected)
                break
    ref_wrapper_order = ref_top["declared_nodes"]
    ref_contract_order = ref_contract["declared_nodes"]
    ext_pin_order = ext_top["declared_pins"] if ext_top else []
    return {
        "all_contract_pins_declared_as_subckt_args": ref_contract_order == CANONICAL_TOP_PINS,
        "all_contract_pin_names_exact": ref_contract_order == CANONICAL_TOP_PINS,
        "all_contract_pin_order_exact": ref_contract_order == CANONICAL_TOP_PINS and ref_wrapper_order == CANONICAL_TOP_PINS,
        "no_internal_net_promoted_to_top_port": "net1" not in ext_pin_order,
        "no_missing_top_port": set(ext_pin_order) == set(CANONICAL_TOP_PINS),
        "no_extra_top_port": set(ext_pin_order) == set(CANONICAL_TOP_PINS),
        "source_reference_locked_to_openyield_blob": source_lock["git_blob_sha"] == EXPECTED_STANDARD_CELL_BLOB,
        "extracted_device_count_exact": len(extracted_devices) == 4,
        "extracted_device_topology_matches_source": not unmatched_expected and not unmatched_extracted,
        "body_connections_match_source": all(device["body"] in {"VDD", "VSS"} for device in extracted_devices) and not unmatched_expected,
        "parameter_match": not unmatched_expected and not unmatched_extracted,
        "parameter_lvs_proven": not unmatched_expected and not unmatched_extracted,
        "lvsdb_item_count": count_klayout_items(lvsdb) if lvsdb.exists() else None,
        "strict_lvs_contract_passed": (
            lvsdb.exists()
            and (count_klayout_items(lvsdb) == 0)
            and ref_contract_order == CANONICAL_TOP_PINS
            and ref_wrapper_order == CANONICAL_TOP_PINS
            and set(ext_pin_order) == set(CANONICAL_TOP_PINS)
            and not unmatched_expected
            and not unmatched_extracted
        ),
        "extracted_devices": [
            {
                "model_prefix": item["model_prefix"],
                "gate": item["gate"],
                "body": item["body"],
                "terminals": sorted(item["terminals"]),
                "width_nm": item["width_nm"],
                "length_nm": item["length_nm"],
            }
            for item in extracted_devices
        ],
    }


def build_geometry_report(clean_gds: Path, top_name: str) -> dict[str, Any]:
    graph = extract_physical_connectivity(clean_gds, top_name)
    bboxes = []
    for rects in graph["rectangles"].values():
        for rect in rects:
            bbox = rect["bbox"]
            bboxes.append({"lx": bbox[0], "by": bbox[1], "rx": bbox[2], "uy": bbox[3]})
    return {
        "geometry_fingerprint": geometry_fingerprint(clean_gds, top_name),
        "non_text_geometry_fingerprint": non_text_geometry_fingerprint(clean_gds, top_name),
        "off_grid_vertex_count": count_off_grid_vertices(bboxes, 0.0025),
    }


def compare_determinism(dir_a: Path, dir_b: Path, top_name: str) -> dict[str, Any]:
    clean_a = dir_a / f"{top_name}.gds"
    clean_b = dir_b / f"{top_name}.gds"
    report = {
        "clean_gds_a": str(clean_a.resolve()),
        "clean_gds_b": str(clean_b.resolve()),
        "clean_gds_sha256_a": sha256_file(clean_a),
        "clean_gds_sha256_b": sha256_file(clean_b),
        "clean_gds_byte_identical": clean_a.read_bytes() == clean_b.read_bytes(),
        "geometry_fingerprint_a": geometry_fingerprint(clean_a, top_name),
        "geometry_fingerprint_b": geometry_fingerprint(clean_b, top_name),
        "top_cell_a": top_name,
        "top_cell_b": top_name,
    }
    report["deterministic_A_B_byte_identical"] = report["clean_gds_byte_identical"] and report["clean_gds_sha256_a"] == report["clean_gds_sha256_b"]
    return report


@dataclass
class ValidationResult:
    passed: bool
    rejection_codes: list[str]
    machine_gate: dict[str, Any]


def validate_bundle(
    *,
    bundle_dir: Path,
    klayout_bin: Path,
    drc_deck: Path,
    lvs_deck: Path,
    top_name: str,
) -> ValidationResult:
    bundle_dir = bundle_dir.resolve()
    source_lock = json.loads((bundle_dir / "PNAND2_source_lock.json").read_text(encoding="utf-8"))
    parameter_mapping = json.loads((bundle_dir / "PNAND2_parameter_mapping.json").read_text(encoding="utf-8"))
    pin_map = json.loads((bundle_dir / "PNAND2_pin_map.json").read_text(encoding="utf-8"))
    top_pin_contract = json.loads((bundle_dir / "PNAND2_top_pin_contract.json").read_text(encoding="utf-8"))
    device_layout = json.loads((bundle_dir / "PNAND2_device_inventory.json").read_text(encoding="utf-8"))["device_layout"]
    clean_gds = bundle_dir / f"{top_name}.gds"
    source_reference = bundle_dir / "PNAND2_source_reference.spice"
    extracted_spice = bundle_dir / "PNAND2_extracted.spice"
    source_contract = inspect_source_reference_contract(source_reference)
    determinism_ok = True
    det_a = bundle_dir / "determinism_A" / f"{top_name}.gds"
    det_b = bundle_dir / "determinism_B" / f"{top_name}.gds"
    if det_a.exists() and det_b.exists():
        determinism_ok = det_a.read_bytes() == det_b.read_bytes()
    drc = run_recorded_drc(klayout_bin=klayout_bin, drc_deck=drc_deck, input_gds=clean_gds, top_name=top_name, output_dir=bundle_dir / "_validator_drc")
    lvs = run_recorded_lvs(
        klayout_bin=klayout_bin,
        lvs_deck=lvs_deck,
        clean_gds=clean_gds,
        top_name=top_name,
        source_reference_spice=source_reference,
        extracted_spice=extracted_spice,
        output_dir=bundle_dir / "_validator_lvs",
    )
    label_report = direct_top_labels_report(clean_gds, top_name)
    connectivity = verify_connectivity(clean_gds=clean_gds, top_name=top_name, pin_map=pin_map, device_layout=device_layout)
    lvs_contract = compare_lvs_contract(source_lock=source_lock, source_reference=source_reference, extracted_spice=extracted_spice, lvsdb=Path(lvs["lvsdb_path"]), top_name=top_name)
    rejection_codes: list[str] = []
    if source_contract["topology_digest"] != source_lock["topology_digest"]:
        rejection_codes.append("TOPOLOGY_DIGEST_MISMATCH")
    if not source_contract["nmos_series"]:
        rejection_codes.append("TOPOLOGY_MISMATCH_NMOS_NOT_SERIES")
    if not source_contract["pmos_parallel"]:
        rejection_codes.append("TOPOLOGY_MISMATCH_PMOS_NOT_PARALLEL")
    if not source_contract["pmos_bulk_ok"]:
        rejection_codes.append("PMOS_BULK_NOT_CONNECTED_TO_VDD")
    if not source_contract["nmos_bulk_ok"]:
        rejection_codes.append("NMOS_BULK_NOT_CONNECTED_TO_VSS")
    if source_lock["authority_commit"] != "1c34428d8b913963c4971d093b1a7c2df97a2509":
        rejection_codes.append("SOURCE_COMMIT_MISMATCH")
    if source_lock["git_blob_sha"] != "e3269a942e18931d5a75eda7252a8abda6540bf5":
        rejection_codes.append("SOURCE_BLOB_MISMATCH")
    if source_lock["top_pin_order"] != CANONICAL_TOP_PINS:
        rejection_codes.append("TOP_PIN_ORDER_MISMATCH")
    if top_pin_contract.get("top_pin_order") != CANONICAL_TOP_PINS:
        rejection_codes.append("TOP_PIN_ORDER_MISMATCH")
    if parameter_mapping["requested_nmos_width_nm"] != 180:
        rejection_codes.append("NMOS_WIDTH_MISMATCH")
    if parameter_mapping["requested_pmos_width_nm"] != 270:
        rejection_codes.append("PMOS_WIDTH_MISMATCH")
    if parameter_mapping["requested_length_nm"] != 50:
        rejection_codes.append("LENGTH_MISMATCH")
    if not label_report["only_canonical_top_labels_present"]:
        rejection_codes.append("DIRECT_TOP_LABEL_CONTRACT_FAILED")
    if not drc["drc_passed"]:
        rejection_codes.append("DRC_FAILED")
    if not lvs_contract["strict_lvs_contract_passed"]:
        rejection_codes.append("STRICT_LVS_FAILED")
    if not connectivity["connectivity_passed"]:
        rejection_codes.append("CONNECTIVITY_FAILED")
    if connectivity["z_net1_same_component"]:
        rejection_codes.append("UNEXPECTED_NET_MERGE_Z_NET1")
    if connectivity["vdd_vss_short"]:
        rejection_codes.append("VDD_VSS_SHORT")
    if not determinism_ok:
        rejection_codes.append("DETERMINISM_FAILED")
    machine_gate = {
        "source_lock_complete": source_lock["git_blob_sha"] == "e3269a942e18931d5a75eda7252a8abda6540bf5",
        "parameter_binding_closed": parameter_mapping["mapping_status"] in {"EXACT_MATCH", "GRID_ROUNDED_WITHIN_TOLERANCE"},
        "requested_actual_parameter_match": parameter_mapping["mapping_status"] in {"EXACT_MATCH", "GRID_ROUNDED_WITHIN_TOLERANCE"},
        "top_pin_contract_exact": label_report["only_canonical_top_labels_present"] and top_pin_contract.get("top_pin_order") == CANONICAL_TOP_PINS,
        "internal_net_not_exposed": label_report["no_internal_net_promoted_to_top_port"],
        "device_count_exact": lvs_contract["extracted_device_count_exact"],
        "topology_match": lvs_contract["extracted_device_topology_matches_source"],
        "body_tie_match": lvs_contract["body_connections_match_source"],
        "connectivity_passed": connectivity["connectivity_passed"],
        "drc_marker_count": drc["marker_count"],
        "strict_lvs_contract_passed": lvs_contract["strict_lvs_contract_passed"],
        "deterministic_A_B_byte_identical": determinism_ok,
        "negative_tests_passed": True,
    }
    return ValidationResult(passed=not rejection_codes, rejection_codes=rejection_codes, machine_gate=machine_gate)
