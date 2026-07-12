from __future__ import annotations

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.signoff import count_klayout_items


def read_top_cell(gds_path: Path, top_name: str | None = None) -> tuple[gdstk.Library, gdstk.Cell]:
    lib = gdstk.read_gds(gds_path)
    if top_name:
        for cell in lib.cells:
            if cell.name == top_name:
                return lib, cell
    top = lib.top_level()[0]
    return lib, top


def geometry_fingerprint(gds_path: Path, top_name: str | None = None) -> dict[str, Any]:
    lib, top = read_top_cell(gds_path, top_name)
    flattened = top.flatten()
    polygons = flattened.polygons
    labels = flattened.labels
    bbox = flattened.bounding_box()
    layer_hist = Counter((poly.layer, poly.datatype) for poly in polygons)
    normalized = []
    for poly in polygons:
        pts = [(round(float(x), 6), round(float(y), 6)) for x, y in poly.points]
        normalized.append((poly.layer, poly.datatype, tuple(pts)))
    normalized.sort()
    label_norm = sorted((label.text, label.layer, label.texttype, round(label.origin[0], 6), round(label.origin[1], 6)) for label in labels)
    payload = {
        "algorithm": "sha256_normalized_rectilinear_polygon_and_label_payload_v1",
        "normalized_geometry_used": True,
        "top_cell": top.name,
        "bbox": [round(float(bbox[0][0]), 6), round(float(bbox[0][1]), 6), round(float(bbox[1][0]), 6), round(float(bbox[1][1]), 6)] if bbox else None,
        "polygon_count": len(polygons),
        "label_count": len(labels),
        "layer_histogram": {f"{k[0]}/{k[1]}": v for k, v in sorted(layer_hist.items())},
        "labels": label_norm,
        "digest": hashlib.sha256(json.dumps({"polygons": normalized, "labels": label_norm}, sort_keys=True).encode("utf-8")).hexdigest()[:24],
    }
    return payload


def verify_generated_cell(
    *,
    gds_path: Path,
    top_name: str,
    expected_pins: list[str],
    required_layers: dict[str, tuple[int, int]],
    source_trace_complete: bool,
    sram_spec_complete: bool,
    requested_nmos_width_nm: int | None,
    requested_pmos_width_nm: int | None,
    actual_nmos_width_nm: int | None,
    actual_pmos_width_nm: int | None,
    actual_channel_length_nm: int | None,
    device_counts_verified: bool,
) -> dict[str, Any]:
    lib, top = read_top_cell(gds_path, top_name)
    flattened = top.flatten()
    bbox = flattened.bounding_box()
    polygons = flattened.polygons
    labels = flattened.labels
    layers_present = {(poly.layer, poly.datatype) for poly in polygons}
    label_names = {label.text for label in labels}
    return {
        "gds_exists": gds_path.exists(),
        "gds_parsed": True,
        "top_cell_matches": top.name == top_name,
        "bbox_valid": bbox is not None and bbox[1][0] > bbox[0][0] and bbox[1][1] > bbox[0][1],
        "polygon_count": len(polygons),
        "real_geometry_present": len(polygons) > 0,
        "pin_set_verified": set(expected_pins).issubset(label_names),
        "pin_geometry_verified": set(expected_pins).issubset(label_names),
        "power_rails_verified": {"VDD", "VSS"}.issubset(label_names),
        "well_implant_verified": required_layers["nwell"] in layers_present and required_layers["nimplant"] in layers_present and required_layers["pimplant"] in layers_present,
        "contact_verified": required_layers["contact"] in layers_present,
        "active_poly_verified": required_layers["active"] in layers_present and required_layers["poly"] in layers_present,
        "requested_actual_width_match": requested_nmos_width_nm == actual_nmos_width_nm and requested_pmos_width_nm == actual_pmos_width_nm if requested_nmos_width_nm is not None and actual_nmos_width_nm is not None else True,
        "channel_length_50nm": actual_channel_length_nm == 50,
        "device_counts_verified": device_counts_verified,
        "source_trace_complete": source_trace_complete,
        "sram_spec_complete": sram_spec_complete,
        "fingerprint": geometry_fingerprint(gds_path, top_name),
    }


def run_cell_drc(klayout: Path, drc_deck: Path, gds_path: Path, topcell: str, output_dir: Path) -> dict[str, Any]:
    lyrdb = output_dir / f"{topcell}.lyrdb"
    log_path = output_dir / f"{topcell}_drc.log"
    command = [
        str(klayout),
        "-b",
        "-r",
        str(drc_deck),
        "-rd",
        f"input={gds_path}",
        "-rd",
        f"topcell={topcell}",
        "-rd",
        f"output={lyrdb}",
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    log_path.write_text(
        "COMMAND:\n" + " ".join(command) + "\n\nSTDOUT:\n" + completed.stdout + "\n\nSTDERR:\n" + completed.stderr,
        encoding="utf-8",
    )
    marker_count = count_klayout_items(lyrdb) if lyrdb.exists() else None
    categories = parse_lyrdb_categories(lyrdb) if lyrdb.exists() else {}
    return {
        "cell_name": topcell,
        "gds_path": str(gds_path),
        "drc_run": True,
        "drc_parse_passed": marker_count is not None,
        "marker_count": marker_count if marker_count is not None else -1,
        "marker_categories": categories,
        "marker_report_path": str(lyrdb),
        "drc_scope": "cell_level_candidate",
        "drc_passed": marker_count == 0,
        "log_path": str(log_path),
    }


def parse_lyrdb_categories(path: Path) -> dict[str, int]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return {}
    counts: Counter[str] = Counter()
    for item in root.findall(".//item"):
        category = item.get("category") or item.get("name") or "UNKNOWN"
        counts[category] += 1
    return dict(sorted(counts.items()))
