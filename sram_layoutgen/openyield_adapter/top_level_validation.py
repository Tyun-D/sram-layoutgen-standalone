from __future__ import annotations

import csv
import json
import math
import os
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


L3_REQUIRED_MODULES = [
    "bitcell_array",
    "dummy_array",
    "replica_array",
    "row_decoder",
    "wordline_decoder",
    "decoder_gate_cells",
    "wordline_driver",
    "wordline_driver_gate_cells",
    "column_mux",
    "sense_amp",
    "write_driver",
    "precharge",
    "DELAY_CHAIN",
    "PRECHARGE_ENABLE_PATH",
    "SENSE_ENABLE_PATH",
    "WRITE_ENABLE_PATH",
    "WORDLINE_ENABLE_PATH",
    "GATED_CLOCK_PATH",
    "DFF_ROW",
    "CONTROL_LOGIC",
]

ALLOWED_ORIENTATIONS = {"R0", "R90", "R180", "R270", "MX", "MY", "MXR90", "MYR90"}
POWER_NETS = {"VDD", "GND", "VSS"}
TOP_LEVEL_REQUIRED_PINS = {"A[*]", "DIN[*]", "DOUT[*]", "clk", "csb", "web", "VDD", "GND"}


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _canonical_token(text: str) -> str:
    cleaned = (
        str(text)
        .replace("[i]", "")
        .replace("[*]", "")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
        .replace(";", "_")
        .replace("-", "_")
        .replace(" ", "")
        .lower()
    )
    alias = {
        "a": "a",
        "addr": "a",
        "bl": "bl",
        "blb": "br",
        "br": "br",
        "clk": "clk",
        "clkbuf": "clk_buf",
        "cs": "cs",
        "csb": "cs",
        "decout": "dec_wl",
        "dec_wl": "dec_wl",
        "delayin": "delay_in",
        "delayout": "delay_out",
        "din": "din",
        "dout": "dout",
        "en": "en",
        "enb": "en_bar",
        "gatedclkbar": "gated_clk_bar",
        "gatedclkbuf": "gated_clk_buf",
        "gnd": "gnd",
        "in": "input",
        "out": "output",
        "pre": "pre",
        "prechargeen": "pre",
        "q": "q",
        "qbar": "q_bar",
        "rbl": "rbl",
        "rbldelay": "rbl_delay",
        "rbldelaybar": "rbl_delay_bar",
        "s_en": "s_en",
        "senseen": "s_en",
        "vdd": "vdd",
        "vss": "gnd",
        "we": "we",
        "web": "we",
        "wl": "wl",
        "wlen": "wl_en",
        "writeen": "w_en",
        "z": "z",
    }
    return alias.get(cleaned, cleaned)


def _extract_signal_tokens(value: str) -> set[str]:
    if not value:
        return set()
    separators = [";", "/", ",", " or "]
    tokens = {value}
    for separator in separators:
        expanded: set[str] = set()
        for token in tokens:
            expanded.update(part.strip() for part in token.split(separator) if part.strip())
        tokens = expanded
    return {_canonical_token(token) for token in tokens if token}


def _bbox_width_height_ok(bbox: dict[str, Any]) -> bool:
    try:
        return float(bbox["width"]) >= 0 and float(bbox["height"]) >= 0 and float(bbox["x1"]) >= float(bbox["x0"]) and float(bbox["y1"]) >= float(bbox["y0"])
    except Exception:
        return False


def _bbox_inside(inner: dict[str, Any], outer: dict[str, Any], tol: float = 1e-6) -> bool:
    return (
        float(inner["x0"]) >= float(outer["x0"]) - tol
        and float(inner["y0"]) >= float(outer["y0"]) - tol
        and float(inner["x1"]) <= float(outer["x1"]) + tol
        and float(inner["y1"]) <= float(outer["y1"]) + tol
    )


def normalize_top_gds_module_reference(
    ref_name: str,
    required_modules: set[str],
    manifest_cell_renaming_map: dict[str, str] | None = None,
) -> str | None:
    text = str(ref_name)
    if text in required_modules:
        return text
    for module in required_modules:
        if text == f"{module}__{module}":
            return module
        if text.startswith(f"{module}__"):
            return module
    if manifest_cell_renaming_map:
        for _, renamed_cell in manifest_cell_renaming_map.items():
            if renamed_cell != text:
                continue
            for module in required_modules:
                if text == f"{module}__{module}" or text.startswith(f"{module}__"):
                    return module
    return None


def _normalize_top_module_reference(name: str) -> str:
    normalized = normalize_top_gds_module_reference(name, set(L3_REQUIRED_MODULES))
    return normalized or str(name)


def _bboxes_overlap(a: dict[str, Any], b: dict[str, Any], tol: float = 1e-9) -> bool:
    return not (
        float(a["x1"]) <= float(b["x0"]) + tol
        or float(b["x1"]) <= float(a["x0"]) + tol
        or float(a["y1"]) <= float(b["y0"]) + tol
        or float(b["y1"]) <= float(a["y0"]) + tol
    )


def _find_first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


@dataclass(frozen=True)
class ValidationCheckResult:
    check_name: str
    check_category: str
    status: str
    summary: str
    evidence_file: str
    is_blocking_basic_validation: bool = False
    is_blocking_drc_clean: bool = False
    is_blocking_lvs_clean: bool = False
    is_blocking_timing_closure: bool = False
    blocking_gap: str = ""
    next_required_action: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_matrix_row(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "check_category": self.check_category,
            "status": self.status,
            "is_blocking_basic_validation": self.is_blocking_basic_validation,
            "is_blocking_drc_clean": self.is_blocking_drc_clean,
            "is_blocking_lvs_clean": self.is_blocking_lvs_clean,
            "is_blocking_timing_closure": self.is_blocking_timing_closure,
            "evidence_file": self.evidence_file,
            "summary": self.summary,
            "blocking_gap": self.blocking_gap,
            "next_required_action": self.next_required_action,
        }


@dataclass(frozen=True)
class TopLevelValidationReport:
    checks: tuple[ValidationCheckResult, ...]
    summary: dict[str, Any]


class BaseValidator:
    check_name = ""
    check_category = ""
    output_filename = ""

    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context

    def output_path(self) -> Path:
        return self.context["out_dir"] / self.output_filename

    def run(self) -> ValidationCheckResult:
        raise NotImplementedError


class TopLevelGdsSanityValidator(BaseValidator):
    check_name = "top_gds_sanity"
    check_category = "gds"
    output_filename = "top_gds_sanity_report.json"

    def run(self) -> ValidationCheckResult:
        top_gds = self.context["top_gds"]
        exists = top_gds.exists()
        size_bytes = top_gds.stat().st_size if exists else 0
        parser_attempts: list[dict[str, Any]] = []
        status = "FAILED"
        summary = "Top-level GDS is missing."
        top_cell_name = None
        top_bbox: dict[str, Any] = {}
        top_instance_count = 0
        top_cell_count = 0
        layer_summary: dict[str, int] = {}
        if exists and size_bytes > 0:
            parsers = [
                ("gdstk", self._parse_with_gdstk_subprocess),
                ("gdspy", self._parse_with_gdspy_subprocess),
                ("klayout_cli", self._parse_with_klayout_cli),
            ]
            for parser_name, parser in parsers:
                parsed = parser(top_gds)
                parser_attempts.append(parsed["attempt"])
                if parsed["success"]:
                    status = "PASSED"
                    summary = f"Parsed top-level GDS with {parser_name}."
                    top_cell_name = parsed["top_cell_name"]
                    top_bbox = parsed["top_bbox"]
                    top_instance_count = parsed["top_instance_count"]
                    top_cell_count = parsed["top_cell_count"]
                    layer_summary = parsed["layer_summary"]
                    break
            if status != "PASSED" and not any(item["available"] for item in parser_attempts):
                status = "SKIPPED_TOOL_UNAVAILABLE"
                summary = "No supported Python GDS parser is available."
            elif status != "PASSED":
                summary = "All available GDS parsers failed to parse the top-level candidate."
        payload = {
            "top_gds_path": str(top_gds),
            "gds_exists": exists,
            "gds_size_bytes": size_bytes,
            "parser_attempts": parser_attempts,
            "top_cell_name": top_cell_name,
            "top_bbox": top_bbox,
            "top_instance_count": top_instance_count,
            "top_cell_count": top_cell_count,
            "layer_summary": layer_summary,
            "top_gds_sanity_status": status,
        }
        _json_dump(self.output_path(), payload)
        return ValidationCheckResult(
            check_name=self.check_name,
            check_category=self.check_category,
            status=status,
            summary=summary,
            evidence_file=str(self.output_path()),
            is_blocking_basic_validation=status != "PASSED",
            is_blocking_drc_clean=status != "PASSED",
            is_blocking_lvs_clean=status != "PASSED",
            is_blocking_timing_closure=status != "PASSED",
            blocking_gap="" if status == "PASSED" else "Top-level GDS could not be parsed into a trustworthy validation view.",
            next_required_action="" if status == "PASSED" else "Repair the top-level GDS export or parser compatibility before further validation.",
            details=payload,
        )

    @staticmethod
    def _parse_with_gdstk_subprocess(path: Path) -> dict[str, Any]:
        script = """
import json
import sys
try:
    import gdstk
except ModuleNotFoundError:
    print(json.dumps({"available": False, "success": False}))
    raise SystemExit(0)
lib = gdstk.read_gds(sys.argv[1])
top_cells = lib.top_level()
top = top_cells[0] if top_cells else lib.cells[0]
bbox = top.bounding_box()
layer_summary = {}
for cell in lib.cells:
    for polygon in cell.polygons:
        key = f"{polygon.layer}/{polygon.datatype}"
        layer_summary[key] = layer_summary.get(key, 0) + 1
print(json.dumps({
    "available": True,
    "success": True,
    "top_cell_name": top.name,
    "top_bbox": {
        "x0": float(bbox[0][0]),
        "y0": float(bbox[0][1]),
        "x1": float(bbox[1][0]),
        "y1": float(bbox[1][1]),
        "width": float(bbox[1][0] - bbox[0][0]),
        "height": float(bbox[1][1] - bbox[0][1]),
    },
    "top_instance_count": len(top.references),
    "top_cell_count": len(lib.cells),
    "layer_summary": dict(sorted(layer_summary.items())),
}))
"""
        return _run_parser_subprocess("gdstk", ["python", "-c", script, str(path)])

    @staticmethod
    def _parse_with_gdspy_subprocess(path: Path) -> dict[str, Any]:
        script = """
import json
import sys
try:
    import gdspy
except ModuleNotFoundError:
    print(json.dumps({"available": False, "success": False}))
    raise SystemExit(0)
lib = gdspy.GdsLibrary(infile=sys.argv[1])
top_cells = lib.top_level()
top = top_cells[0] if top_cells else next(iter(lib.cells.values()))
bbox = top.get_bounding_box()
layer_summary = {}
for cell in lib.cells.values():
    for polygon_set in cell.polygons:
        for layer, datatype in zip(polygon_set.layers, polygon_set.datatypes):
            key = f"{layer}/{datatype}"
            layer_summary[key] = layer_summary.get(key, 0) + len(polygon_set.polygons)
print(json.dumps({
    "available": True,
    "success": True,
    "top_cell_name": top.name,
    "top_bbox": {
        "x0": float(bbox[0][0]),
        "y0": float(bbox[0][1]),
        "x1": float(bbox[1][0]),
        "y1": float(bbox[1][1]),
        "width": float(bbox[1][0] - bbox[0][0]),
        "height": float(bbox[1][1] - bbox[0][1]),
    },
    "top_instance_count": len(getattr(top, "references", [])),
    "top_cell_count": len(lib.cells),
    "layer_summary": dict(sorted(layer_summary.items())),
}))
"""
        return _run_parser_subprocess("gdspy", ["python", "-c", script, str(path)])

    @staticmethod
    def _parse_with_klayout_cli(path: Path) -> dict[str, Any]:
        klayout = shutil_which("klayout")
        if not klayout:
            return {"attempt": {"parser": "klayout_cli", "available": False, "success": False}, "success": False}
        ruby = """
require 'json'
layout = RBA::Layout::new
layout.read($input)
top = layout.top_cell
bbox = top.bbox
layer_summary = {}
layout.layer_indexes.each do |layer_index|
  info = layout.get_info(layer_index)
  layer_summary["#{info.layer}/#{info.datatype}"] = top.begin_shapes_rec(layer_index).size
end
File.write($out_json, JSON.generate({
  top_cell_name: top.name,
  top_bbox: {
    x0: bbox.left * layout.dbu,
    y0: bbox.bottom * layout.dbu,
    x1: bbox.right * layout.dbu,
    y1: bbox.top * layout.dbu,
    width: bbox.width * layout.dbu,
    height: bbox.height * layout.dbu,
  },
  top_instance_count: top.each_inst.to_a.length,
  top_cell_count: layout.cells,
  layer_summary: layer_summary.sort.to_h,
}))
"""
        tmp_dir = _temp_work_dir(path)
        tmp_dir.mkdir(parents=True, exist_ok=True)
        script_path = tmp_dir / "klayout_parse.rb"
        out_json = tmp_dir / "klayout_parse.json"
        script_path.write_text(ruby, encoding="utf-8")
        completed = subprocess.run(
            [klayout, "-b", "-r", str(script_path), "-rd", f"input={path}", "-rd", f"out_json={out_json}"],
            text=True,
            capture_output=True,
            check=False,
        )
        attempt = {
            "parser": "klayout_cli",
            "available": True,
            "success": completed.returncode == 0 and out_json.exists(),
            "returncode": completed.returncode,
            "stdout": completed.stdout[-800:],
            "stderr": completed.stderr[-800:],
        }
        if completed.returncode == 0 and out_json.exists():
            payload = json.loads(out_json.read_text(encoding="utf-8"))
            payload["attempt"] = attempt
            payload["success"] = True
            return payload
        return {"attempt": attempt, "success": False}


class ModuleCompletenessValidator(BaseValidator):
    check_name = "module_completeness"
    check_category = "topology"
    output_filename = "module_completeness_report.json"

    def run(self) -> ValidationCheckResult:
        placement = self.context["module_placement"]
        l4_report = self.context["l4_report"]
        inventory_rows = self.context["module_gds_inventory_rows"]
        manifest = self.context["top_level_generator_manifest"]
        manifest_cell_renaming_map = manifest.get("hierarchy_export", {}).get("cell_renaming_map", {})
        present = {item["module_name"] for item in placement["instances"]}
        required = set(L3_REQUIRED_MODULES)
        placement_missing = sorted(required - present)
        placement_extra = sorted(present - required)
        top_refs_raw = list(self.context["gds_sanity_result"].details.get("module_references", []))
        if not top_refs_raw:
            top_refs_raw = list(l4_report.get("module_references", []))
        top_refs_normalized = {
            normalized
            for name in top_refs_raw
            for normalized in [normalize_top_gds_module_reference(name, required, manifest_cell_renaming_map)]
            if normalized is not None
        }
        top_missing = sorted(required - top_refs_normalized)
        inventory_required = {
            row["module"]
            for row in inventory_rows
            if str(row.get("is_L3_target", "")).strip().lower() == "true" and str(row.get("gds_generated", "")).strip().lower() == "true"
        }
        report_count = int(l4_report.get("required_l3_modules_count", len(required)))
        status = "PASSED"
        blockers: list[str] = []
        if placement_missing:
            blockers.append(f"Missing from module_placement.json: {', '.join(placement_missing)}")
        if top_missing:
            blockers.append(f"Missing from top GDS references: {', '.join(top_missing)}")
        if int(placement.get("instance_count", -1)) != report_count:
            blockers.append("Placement instance_count does not match L4 required_l3_modules_count.")
        if len(placement["instances"]) != report_count:
            blockers.append("Placement instance list length does not match L4 required_l3_modules_count.")
        if sorted(l4_report.get("required_l3_modules_missing_from_top", [])):
            blockers.append("L4 report still records missing required modules.")
        if required != inventory_required:
            blockers.append("Module GDS inventory L3 target set does not match expected required L3 modules.")
        if blockers:
            status = "FAILED"
        payload = {
            "required_l3_modules_count": len(required),
            "placement_instance_count": len(placement["instances"]),
            "placement_declared_instance_count": placement.get("instance_count"),
            "l4_report_required_count": report_count,
            "required_modules_present_in_placement": sorted(present & required),
            "required_modules_missing_from_placement": placement_missing,
            "required_modules_missing_from_top_gds_references": top_missing,
            "required_modules_present_in_top_gds_references": sorted(top_refs_normalized & required),
            "required_modules_missing_from_l4_report": l4_report.get("required_l3_modules_missing_from_top", []),
            "placement_extra_modules": placement_extra,
            "module_references_seen_raw": sorted(top_refs_raw),
            "module_references_normalized": sorted(top_refs_normalized),
            "module_references_seen": sorted(top_refs_normalized),
            "module_completeness_status": status,
            "blocking_gaps": blockers,
        }
        _json_dump(self.output_path(), payload)
        return ValidationCheckResult(
            check_name=self.check_name,
            check_category=self.check_category,
            status=status,
            summary="All 20 required L3 modules are present in placement and top-level references." if status == "PASSED" else "; ".join(blockers),
            evidence_file=str(self.output_path()),
            is_blocking_basic_validation=status != "PASSED",
            is_blocking_drc_clean=status != "PASSED",
            is_blocking_lvs_clean=status != "PASSED",
            is_blocking_timing_closure=status != "PASSED",
            blocking_gap="" if status == "PASSED" else "; ".join(blockers),
            next_required_action="" if status == "PASSED" else "Regenerate L4 top-level assembly after restoring the missing or inconsistent module instances.",
            details=payload,
        )


class PlacementConsistencyValidator(BaseValidator):
    check_name = "placement_consistency"
    check_category = "placement"
    output_filename = "placement_consistency_report.json"

    def run(self) -> ValidationCheckResult:
        placement = self.context["module_placement"]
        floorplan = self.context["top_level_floorplan"]
        zones = floorplan.get("zones", [])
        floorplan_bbox = floorplan["floorplan_bbox"]
        fatal_issues: list[str] = []
        overlap_risks: list[dict[str, Any]] = []
        zone_mismatches: list[str] = []
        for item in placement["instances"]:
            module = item["module_name"]
            bbox = item.get("bbox", {})
            if item.get("orientation") not in ALLOWED_ORIENTATIONS:
                fatal_issues.append(f"{module}: invalid orientation {item.get('orientation')}")
            for axis in ("origin_x", "origin_y"):
                value = item.get(axis)
                if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                    fatal_issues.append(f"{module}: non-numeric {axis}")
            if not _bbox_width_height_ok(bbox):
                fatal_issues.append(f"{module}: illegal bbox {bbox}")
                continue
            for key in ("x0", "y0", "x1", "y1", "width", "height"):
                if not math.isfinite(float(bbox[key])):
                    fatal_issues.append(f"{module}: non-finite bbox field {key}")
            if not _bbox_inside(bbox, floorplan_bbox):
                fatal_issues.append(f"{module}: bbox escapes top floorplan bbox")
            zone = next((entry for entry in zones if module in entry.get("modules", [])), None)
            if zone and not _bbox_inside(bbox, zone["bbox"], tol=1e-3):
                zone_mismatches.append(f"{module}: bbox not fully inside declared zone {zone['name']}")
        instances = placement["instances"]
        for index, left in enumerate(instances):
            for right in instances[index + 1 :]:
                if _bboxes_overlap(left["bbox"], right["bbox"]):
                    overlap_risks.append(
                        {
                            "left_module": left["module_name"],
                            "right_module": right["module_name"],
                            "left_instance": left["instance_name"],
                            "right_instance": right["instance_name"],
                        }
                    )
        status = "PASSED" if not fatal_issues else "FAILED"
        payload = {
            "placement_consistency_status": status,
            "fatal_issues": fatal_issues,
            "zone_mismatches": zone_mismatches,
            "overlap_risks": overlap_risks,
            "instance_count": len(instances),
            "floorplan_bbox": floorplan_bbox,
        }
        _json_dump(self.output_path(), payload)
        summary = "Placement metadata is numerically consistent with the top-level floorplan."
        if fatal_issues:
            summary = "; ".join(fatal_issues[:4])
        elif zone_mismatches or overlap_risks:
            summary = "Placement has no fatal issues but records zone mismatch or overlap risk for follow-up."
        return ValidationCheckResult(
            check_name=self.check_name,
            check_category=self.check_category,
            status=status,
            summary=summary,
            evidence_file=str(self.output_path()),
            is_blocking_basic_validation=status != "PASSED",
            blocking_gap="" if status == "PASSED" else "; ".join(fatal_issues),
            next_required_action="" if status == "PASSED" else "Fix placement metadata or floorplan generator inconsistencies before re-running L5.",
            details=payload,
        )


class PinMetadataValidator(BaseValidator):
    check_name = "pin_accessibility"
    check_category = "pins"
    output_filename = "pin_accessibility_audit.json"

    def run(self) -> ValidationCheckResult:
        top_pin_map = self.context["top_level_pin_map"]
        placement = self.context["module_placement"]
        module_pin_rows = self.context["pin_access_rule_rows"]
        pin_rules = {row["object_name"]: row for row in module_pin_rows}
        top_pins = top_pin_map.get("top_level_pins", [])
        top_pin_names = {entry["top_pin_name"] for entry in top_pins}
        missing_top = sorted(TOP_LEVEL_REQUIRED_PINS - top_pin_names)
        module_pin_status: dict[str, Any] = {}
        missing_module_pin_metadata: list[str] = []
        contract_pin_modules: list[str] = []
        geometry_followup: list[str] = []
        for item in placement["instances"]:
            module = item["module_name"]
            pins_path = self.context["module_gds_dir"] / module / "pins.json"
            if not pins_path.exists():
                missing_module_pin_metadata.append(module)
                continue
            pin_payload = _load_json(pins_path)
            pins = pin_payload.get("pins", [])
            pin_names = {entry.get("name", "") for entry in pins}
            has_power = bool(pin_names & POWER_NETS)
            uses_contract = bool(item.get("uses_contract_pins"))
            if uses_contract:
                contract_pin_modules.append(module)
            if any("contract" in str(entry.get("pin_source", "")).lower() for entry in pins):
                geometry_followup.append(module)
            module_pin_status[module] = {
                "pins_path": str(pins_path),
                "pin_count": len(pins),
                "has_power_pin": has_power,
                "uses_contract_pins": uses_contract,
                "pin_sources": sorted({str(entry.get("pin_source", "")) for entry in pins}),
                "pin_access_rule_status": pin_rules.get(module, pin_rules.get(_primitive_alias(module), {})).get("pin_access_rule_status"),
            }
        status = "PASSED" if top_pins and not missing_module_pin_metadata else "FAILED"
        payload = {
            "pin_accessibility_status": status,
            "top_level_pin_count": len(top_pins),
            "top_level_pin_names": sorted(top_pin_names),
            "missing_required_top_level_pins": missing_top,
            "module_pin_status": module_pin_status,
            "missing_module_pin_metadata": missing_module_pin_metadata,
            "modules_using_contract_pins": sorted(set(contract_pin_modules)),
            "modules_needing_pin_geometry_followup": sorted(set(geometry_followup)),
        }
        _json_dump(self.output_path(), payload)
        return ValidationCheckResult(
            check_name=self.check_name,
            check_category=self.check_category,
            status=status,
            summary="Pin metadata audit emitted with contract-pin risks recorded." if status == "PASSED" else "Missing top-level pins or module pin metadata.",
            evidence_file=str(self.output_path()),
            is_blocking_basic_validation=status != "PASSED",
            is_blocking_drc_clean=True,
            is_blocking_lvs_clean=True,
            blocking_gap="" if status == "PASSED" else "Top-level or module-level pin metadata is incomplete.",
            next_required_action="Preserve contract-pin classifications and promote geometry-backed pin proof in later L5/L6." if status == "PASSED" else "Restore missing pin metadata exports before re-running L5.",
            details=payload,
        )


class RailStitchPlanValidator(BaseValidator):
    check_name = "rail_stitch_audit"
    check_category = "power"
    output_filename = "rail_stitch_audit.json"

    def run(self) -> ValidationCheckResult:
        placement = self.context["module_placement"]
        stitch_plan = self.context["top_level_rail_stitch_plan"]
        rail_rule_rows = self.context["rail_rule_rows"]
        rule_lookup = {row["object_name"]: row for row in rail_rule_rows}
        entries = stitch_plan.get("entries", [])
        nets = {entry.get("power_net") for entry in entries}
        modules = {item["module_name"] for item in placement["instances"]}
        missing_nets = sorted({"VDD", "GND"} - nets)
        missing_modules_by_net: dict[str, list[str]] = {}
        contract_rail_modules: list[str] = []
        geometry_followup: list[str] = []
        for entry in entries:
            power_net = entry["power_net"]
            involved = set(entry.get("modules_involved", []))
            missing_modules_by_net[power_net] = sorted(modules - involved)
            for module in entry.get("modules_involved", []):
                rail_path = self.context["module_gds_dir"] / module / "rail_report.json"
                if rail_path.exists():
                    rail_report = _load_json(rail_path)
                    rail_status = str(rail_report.get("rail_status", ""))
                    if "contract" in rail_status.lower():
                        contract_rail_modules.append(module)
                    if "candidate" in rail_status.lower() or "contract" in rail_status.lower():
                        geometry_followup.append(module)
                else:
                    geometry_followup.append(module)
                _ = rule_lookup.get(_primitive_alias(module), {})
        blockers = []
        if missing_nets:
            blockers.append(f"Missing power nets in stitch plan: {', '.join(missing_nets)}")
        for power_net, missing_modules in missing_modules_by_net.items():
            if missing_modules:
                blockers.append(f"{power_net} stitch plan excludes modules: {', '.join(missing_modules)}")
        status = "PASSED" if not blockers else "FAILED"
        payload = {
            "rail_stitch_audit_status": status,
            "plan_entry_count": len(entries),
            "power_nets_present": sorted(nets),
            "missing_power_nets": missing_nets,
            "missing_modules_by_net": missing_modules_by_net,
            "modules_using_contract_rail": sorted(set(contract_rail_modules)),
            "modules_needing_rail_geometry_followup": sorted(set(geometry_followup)),
            "entries": entries,
        }
        _json_dump(self.output_path(), payload)
        return ValidationCheckResult(
            check_name=self.check_name,
            check_category=self.check_category,
            status=status,
            summary="Rail stitch plan covers VDD/GND and all modules." if status == "PASSED" else "; ".join(blockers),
            evidence_file=str(self.output_path()),
            is_blocking_basic_validation=status != "PASSED",
            is_blocking_drc_clean=True,
            is_blocking_lvs_clean=True,
            blocking_gap="" if status == "PASSED" else "; ".join(blockers),
            next_required_action="Keep rail stitch plan as completeness proof only; later passes must prove geometry continuity." if status == "PASSED" else "Repair missing power-net/module entries in the top-level rail stitch plan.",
            details=payload,
        )


class RoutingHandoffValidator(BaseValidator):
    check_name = "routing_handoff_audit"
    check_category = "routing"
    output_filename = "routing_handoff_audit.json"

    def run(self) -> ValidationCheckResult:
        handoff = self.context["top_level_routing_handoff"]
        matrix_rows = self.context["module_connection_matrix_rows"]
        control_rows = self.context["control_contract_rows"]
        entries = handoff.get("entries", [])
        net_names = {entry["net_name"] for entry in entries}
        required_from_matrix = {row["signal_name"] for row in matrix_rows if str(row.get("is_power", "")).lower() != "true"}
        missing_from_handoff = sorted(required_from_matrix - net_names)
        missing_source_or_target = [
            entry["net_name"]
            for entry in entries
            if not entry.get("source_module") or not entry.get("target_module")
        ]
        category_stats = Counter(entry.get("net_category", "unknown") for entry in entries)
        contract_only = sorted(entry["net_name"] for entry in entries if entry.get("routing_status") == "CONTRACT_NET_ONLY")
        detailed_routing_needed = sorted(entry["net_name"] for entry in entries if entry.get("routing_required_in_L5"))
        timing_expected = set()
        for row in control_rows:
            timing_expected.update(_extract_signal_tokens(row.get("output_signals", "")))
        timing_trace = {
            signal: any(_canonical_token(entry["net_name"]) == signal for entry in entries)
            for signal in sorted(token for token in timing_expected if "rbl" in token or token in {"pre", "s_en", "w_en", "wl_en"})
        }
        blockers = []
        if missing_from_handoff:
            blockers.append(f"Missing required semantic nets in routing handoff: {', '.join(missing_from_handoff)}")
        if missing_source_or_target:
            blockers.append(f"Routing entries missing source/target ownership: {', '.join(missing_source_or_target)}")
        status = "PASSED" if not blockers else "FAILED"
        payload = {
            "routing_handoff_audit_status": status,
            "entry_count": len(entries),
            "required_semantic_nets_missing": missing_from_handoff,
            "entries_missing_source_or_target": missing_source_or_target,
            "contract_net_only": contract_only,
            "detailed_routing_needed": detailed_routing_needed,
            "net_category_stats": dict(sorted(category_stats.items())),
            "timing_trace_expected_signals": timing_trace,
        }
        _json_dump(self.output_path(), payload)
        return ValidationCheckResult(
            check_name=self.check_name,
            check_category=self.check_category,
            status=status,
            summary="Routing handoff captures semantic net ownership and unresolved detailed-routing items." if status == "PASSED" else "; ".join(blockers),
            evidence_file=str(self.output_path()),
            is_blocking_basic_validation=status != "PASSED",
            is_blocking_drc_clean=True,
            is_blocking_lvs_clean=True,
            is_blocking_timing_closure=True,
            blocking_gap="" if status == "PASSED" else "; ".join(blockers),
            next_required_action="Use this audit as the L5 routing handoff baseline; later routing closure must consume the unresolved top-level nets." if status == "PASSED" else "Repair missing routing handoff coverage or ownership metadata.",
            details=payload,
        )


class CandidateGeometryRiskClassifier(BaseValidator):
    check_name = "candidate_geometry_risk"
    check_category = "risk"
    output_filename = "candidate_geometry_risk_report.json"

    def run(self) -> ValidationCheckResult:
        placement = self.context["module_placement"]
        inventory_rows = {row["module"]: row for row in self.context["module_gds_inventory_rows"]}
        l4_report = self.context["l4_report"]
        candidate_modules = sorted(set(l4_report.get("modules_instantiated_with_candidate_geometry", [])))
        contract_pin_modules = sorted(set(l4_report.get("modules_instantiated_with_contract_pins", [])))
        hardmacro_modules = sorted(
            row["module"]
            for row in self.context["module_gds_inventory_rows"]
            if str(row.get("uses_hardmacro", "")).strip().lower() == "true"
        )
        array_modules = sorted(
            row["module"]
            for row in self.context["module_gds_inventory_rows"]
            if str(row.get("uses_array_packer", "")).strip().lower() == "true"
        )
        risk_items = [
            {
                "risk_type": "candidate_geometry_modules",
                "affected_modules": candidate_modules,
                "why_it_matters": "Candidate geometry is not signoff-proven for detailed routing, DRC, LVS, or timing.",
                "blocks_current_L5_basic_validation": False,
                "blocks_DRC": True,
                "blocks_LVS": True,
                "blocks_timing": True,
                "recommended_next_action": "Promote candidate modules to geometry-backed routing/pin/rail proof before any signoff claim.",
            },
            {
                "risk_type": "contract_pin_modules",
                "affected_modules": contract_pin_modules,
                "why_it_matters": "Contract pins preserve semantic connectivity but do not yet prove physical accessibility or LVS pin mapping.",
                "blocks_current_L5_basic_validation": False,
                "blocks_DRC": True,
                "blocks_LVS": True,
                "blocks_timing": False,
                "recommended_next_action": "Replace contract-only pins with geometry-backed pin proof or audited pin export.",
            },
            {
                "risk_type": "hardmacro_modules",
                "affected_modules": hardmacro_modules,
                "why_it_matters": "Hardmacro wrappers reduce generation risk but still depend on top-level stitch and routing proof.",
                "blocks_current_L5_basic_validation": False,
                "blocks_DRC": False,
                "blocks_LVS": False,
                "blocks_timing": False,
                "recommended_next_action": "Keep hardmacros in DRC/LVS scope and verify wrapper pin/rail consistency.",
            },
            {
                "risk_type": "array_generated_modules",
                "affected_modules": array_modules,
                "why_it_matters": "Array-generated modules are deterministic but still rely on later top-level routing and stitch closure.",
                "blocks_current_L5_basic_validation": False,
                "blocks_DRC": False,
                "blocks_LVS": False,
                "blocks_timing": False,
                "recommended_next_action": "Preserve current array metadata and only expand signoff claims after integrated DRC/LVS evidence.",
            },
        ]
        payload = {
            "candidate_geometry_risk_status": "PASSED",
            "risk_items": risk_items,
            "module_generation_status": {module: inventory_rows[module]["generation_status"] for module in sorted(inventory_rows)},
            "instantiated_modules": sorted(item["module_name"] for item in placement["instances"]),
        }
        _json_dump(self.output_path(), payload)
        return ValidationCheckResult(
            check_name=self.check_name,
            check_category=self.check_category,
            status="PASSED",
            summary="Candidate-geometry and contract-pin risk classes recorded for downstream DRC/LVS/timing gates.",
            evidence_file=str(self.output_path()),
            is_blocking_drc_clean=True,
            is_blocking_lvs_clean=True,
            is_blocking_timing_closure=True,
            next_required_action="Keep all full-GDS/DRC/LVS/timing claims false until these risk classes are retired.",
            details=payload,
        )


class OptionalDrcSmokeValidator(BaseValidator):
    check_name = "drc_smoke"
    check_category = "drc"
    output_filename = "drc_smoke_report.json"

    def run(self) -> ValidationCheckResult:
        klayout = shutil_which("klayout")
        deck = _find_first_existing([self.context["repo_root"] / "technology/freepdk45/tech/freepdk45.lydrc"])
        out_dir = self.context["out_dir"]
        lyrdb = out_dir / "top_level_candidate_drc.lyrdb"
        log_path = out_dir / "top_level_candidate_drc.log"
        marker_count = None
        marker_categories: dict[str, int] = {}
        command: list[str] | None = None
        status = "SKIPPED_TOOL_OR_DECK_UNAVAILABLE"
        summary = "KLayout or DRC deck is unavailable."
        if klayout and deck:
            topcell = self.context["gds_sanity_result"].details.get("top_cell_name") or self.context["l4_report"].get("top_cell_name")
            command = [
                klayout,
                "-b",
                "-r",
                str(deck),
                "-rd",
                f"input={self.context['top_gds']}",
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
            if completed.returncode == 0 and lyrdb.exists():
                markers = parse_lyrdb(lyrdb)
                marker_count = len(markers)
                marker_categories = dict(sorted(Counter(marker["rule_name"] for marker in markers).items()))
                status = "DRC_SMOKE_RAN_WITH_MARKERS" if marker_count else "DRC_SMOKE_RAN_NO_MARKERS"
                summary = f"DRC smoke ran with {marker_count} markers."
            else:
                status = "FAILED"
                summary = "KLayout DRC smoke command failed."
        payload = {
            "drc_smoke_status": status,
            "klayout_path": klayout,
            "deck_path": str(deck) if deck else None,
            "command": command,
            "log_path": str(log_path) if log_path.exists() else None,
            "lyrdb_path": str(lyrdb) if lyrdb.exists() else None,
            "marker_count": marker_count,
            "marker_categories": marker_categories,
        }
        _json_dump(self.output_path(), payload)
        return ValidationCheckResult(
            check_name=self.check_name,
            check_category=self.check_category,
            status=status,
            summary=summary,
            evidence_file=str(self.output_path()),
            is_blocking_drc_clean=True,
            blocking_gap="" if status != "FAILED" else "The optional DRC smoke could not complete successfully.",
            next_required_action="Do not claim DRC clean unless the correct deck runs with zero markers." if status != "FAILED" else "Inspect the DRC smoke log and deck/topcell assumptions before any DRC claim.",
            details=payload,
        )


class OptionalLvsFeasibilityValidator(BaseValidator):
    check_name = "lvs_feasibility"
    check_category = "lvs"
    output_filename = "lvs_feasibility_report.json"

    def run(self) -> ValidationCheckResult:
        repo_root = self.context["repo_root"]
        openyield_root = self.context["openyield_root"]
        placement = self.context["module_placement"]
        module_netlists = []
        for module in sorted({item["module_name"] for item in placement["instances"]}):
            netlist = _find_first_existing(
                [
                    repo_root / "outputs/openyield_module_gds" / module / "netlist.sp",
                    repo_root / "outputs/openyield_module_gds" / module / f"{module}.sp",
                    repo_root / "outputs/openyield_module_gds" / module / "source_netlist.sp",
                ]
            )
            module_netlists.append({"module": module, "netlist_path": str(netlist) if netlist else None})
        openyield_netlist_candidates = list(openyield_root.rglob("*.sp"))[:20] if openyield_root.exists() else []
        source_netlist_candidates = list((repo_root / "sram_compiler").rglob("*.py"))[:20] if (repo_root / "sram_compiler").exists() else []
        candidate_geometry_modules = self.context["l4_report"].get("modules_instantiated_with_candidate_geometry", [])
        contract_pin_modules = self.context["l4_report"].get("modules_instantiated_with_contract_pins", [])
        generated_top_netlist = _find_first_existing(
            [
                repo_root / "outputs/openyield_top_level_assembly/current_supported_config/openyield_top_level_candidate.sp",
                repo_root / "outputs/openyield_top_level_assembly/current_supported_config/top_level_netlist.sp",
                repo_root / "outputs/openyield_validation/current_supported_config/top_level_netlist.sp",
            ]
        )
        status = "LVS_NOT_ATTEMPTED"
        summary = "LVS was not attempted; this is a feasibility audit only."
        if not generated_top_netlist:
            status = "LVS_BLOCKED_BY_MISSING_NETLIST"
            summary = "No generated top-level netlist is available for LVS."
        elif contract_pin_modules:
            status = "LVS_BLOCKED_BY_PIN_MAPPING"
            summary = "Contract-pin modules still block trustworthy LVS pin mapping."
        elif candidate_geometry_modules:
            status = "LVS_BLOCKED_BY_CANDIDATE_GEOMETRY"
            summary = "Candidate-geometry modules still block trustworthy LVS."
        else:
            status = "LVS_FEASIBLE_WITH_ADDITIONAL_NETLIST_EXPORT"
            summary = "LVS could become feasible after consistent netlist export and pin mapping."
        payload = {
            "lvs_feasibility_status": status,
            "generated_top_level_netlist_path": str(generated_top_netlist) if generated_top_netlist else None,
            "openyield_source_netlist_candidates": [str(path) for path in openyield_netlist_candidates],
            "local_source_reference_candidates": [str(path) for path in source_netlist_candidates],
            "module_level_netlist_candidates": module_netlists,
            "candidate_geometry_modules": candidate_geometry_modules,
            "contract_pin_modules": contract_pin_modules,
            "pin_mapping_available": not bool(contract_pin_modules),
        }
        _json_dump(self.output_path(), payload)
        return ValidationCheckResult(
            check_name=self.check_name,
            check_category=self.check_category,
            status=status,
            summary=summary,
            evidence_file=str(self.output_path()),
            is_blocking_lvs_clean=True,
            next_required_action="Keep can_claim_lvs_clean_now=False; export a consistent top-level netlist and retire contract-pin/candidate-geometry blockers before LVS." if status != "LVS_FEASIBLE_WITH_ADDITIONAL_NETLIST_EXPORT" else "Export the final top-level netlist and consistent pin mapping before attempting LVS.",
            details=payload,
        )


class TimingMetadataConsistencyValidator(BaseValidator):
    check_name = "timing_metadata_consistency"
    check_category = "timing"
    output_filename = "timing_metadata_consistency_report.json"

    def run(self) -> ValidationCheckResult:
        timing_report = self.context["timing_metadata_report"]
        handoff = self.context["top_level_routing_handoff"]
        placement = self.context["module_placement"]
        instantiated_modules = {item["module_name"] for item in placement["instances"]}
        timing_object = timing_report.get("timing_metadata", {}).get("timing_object")
        routing_entries = handoff.get("entries", [])
        net_names = {entry["net_name"] for entry in routing_entries}
        required_nets = {"rbl", "rbl_delay", "rbl_delay_bar"}
        missing_nets = sorted(required_nets - net_names)
        status = "PASSED" if timing_object == "DELAY_CHAIN" and "DELAY_CHAIN" in instantiated_modules else "FAILED"
        if missing_nets:
            status = "FAILED"
        payload = {
            "timing_metadata_consistency_status": status,
            "timing_object": timing_object,
            "delay_chain_instantiated": "DELAY_CHAIN" in instantiated_modules,
            "routing_handoff_nets_present": sorted(net_names),
            "missing_required_timing_nets": missing_nets,
            "timing_metadata_summary_available": self.context["timing_metadata_summary_path"].exists(),
            "timing_closure_claimed": False,
            "timing_metadata_report_repo_head": timing_report.get("repo_head"),
            "current_repo_head": self.context["repo_head"],
        }
        _json_dump(self.output_path(), payload)
        return ValidationCheckResult(
            check_name=self.check_name,
            check_category=self.check_category,
            status=status,
            summary="Timing metadata remains traceable from DELAY_CHAIN into routing handoff." if status == "PASSED" else "Timing metadata is missing DELAY_CHAIN instantiation or required timing nets.",
            evidence_file=str(self.output_path()),
            is_blocking_timing_closure=True,
            blocking_gap="" if status == "PASSED" else "Timing handoff is incomplete or inconsistent with DELAY_CHAIN metadata.",
            next_required_action="Keep timing metadata as smoke-only evidence; do not claim timing closure." if status == "PASSED" else "Repair DELAY_CHAIN instantiation or timing net handoff before timing review.",
            details=payload,
        )


class OpenYieldL5Validator:
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context

    def run(self) -> TopLevelValidationReport:
        results: list[ValidationCheckResult] = []
        gds_result = TopLevelGdsSanityValidator(self.context).run()
        self.context["gds_sanity_result"] = gds_result
        gds_details = dict(gds_result.details)
        gds_details["module_references"] = self.context["l4_report"].get("module_references", [])
        self.context["gds_sanity_result"] = ValidationCheckResult(
            check_name=gds_result.check_name,
            check_category=gds_result.check_category,
            status=gds_result.status,
            summary=gds_result.summary,
            evidence_file=gds_result.evidence_file,
            is_blocking_basic_validation=gds_result.is_blocking_basic_validation,
            is_blocking_drc_clean=gds_result.is_blocking_drc_clean,
            is_blocking_lvs_clean=gds_result.is_blocking_lvs_clean,
            is_blocking_timing_closure=gds_result.is_blocking_timing_closure,
            blocking_gap=gds_result.blocking_gap,
            next_required_action=gds_result.next_required_action,
            details=gds_details,
        )
        results.append(self.context["gds_sanity_result"])
        for validator_cls in [
            ModuleCompletenessValidator,
            PlacementConsistencyValidator,
            PinMetadataValidator,
            RailStitchPlanValidator,
            RoutingHandoffValidator,
            CandidateGeometryRiskClassifier,
            OptionalDrcSmokeValidator,
            OptionalLvsFeasibilityValidator,
            TimingMetadataConsistencyValidator,
        ]:
            results.append(validator_cls(self.context).run())
        summary = self._build_summary(results)
        return TopLevelValidationReport(checks=tuple(results), summary=summary)

    def _build_summary(self, results: list[ValidationCheckResult]) -> dict[str, Any]:
        lookup = {result.check_name: result for result in results}
        blockers = [result.check_name for result in results if result.is_blocking_basic_validation]
        basic_pass = (
            lookup["top_gds_sanity"].status == "PASSED"
            and lookup["module_completeness"].status == "PASSED"
            and lookup["placement_consistency"].status == "PASSED"
            and lookup["pin_accessibility"].status in {"PASSED"}
            and lookup["rail_stitch_audit"].status in {"PASSED"}
            and lookup["routing_handoff_audit"].status in {"PASSED"}
            and lookup["candidate_geometry_risk"].status == "PASSED"
            and not blockers
        )
        recommended = []
        if lookup["drc_smoke"].status != "DRC_SMOKE_RAN_NO_MARKERS":
            recommended.append("Run or review integrated KLayout DRC smoke and triage all reported markers before any DRC claim.")
        recommended.append("Promote contract-pin modules to geometry-backed pin accessibility proof.")
        recommended.append("Promote candidate-geometry modules to routing/power/LVS-capable proof before any full-GDS claim.")
        if lookup["lvs_feasibility"].status != "LVS_FEASIBLE_WITH_ADDITIONAL_NETLIST_EXPORT":
            recommended.append("Export a consistent top-level netlist and module pin mapping for future LVS.")
        recommended.append("Keep timing evidence at metadata/smoke scope; do not claim timing closure.")
        return {
            "L5_validation_available": True,
            "top_gds_sanity_check_available": True,
            "module_completeness_check_available": True,
            "placement_consistency_check_available": True,
            "pin_accessibility_audit_available": True,
            "rail_stitch_audit_available": True,
            "routing_handoff_audit_available": True,
            "candidate_geometry_risk_report_available": True,
            "drc_smoke_report_available": True,
            "lvs_feasibility_report_available": True,
            "timing_metadata_consistency_report_available": True,
            "validation_matrix_available": True,
            "top_gds_sanity_status": lookup["top_gds_sanity"].status,
            "module_completeness_status": lookup["module_completeness"].status,
            "placement_consistency_status": lookup["placement_consistency"].status,
            "pin_accessibility_status": lookup["pin_accessibility"].status,
            "rail_stitch_audit_status": lookup["rail_stitch_audit"].status,
            "routing_handoff_audit_status": lookup["routing_handoff_audit"].status,
            "candidate_geometry_risk_status": lookup["candidate_geometry_risk"].status,
            "drc_smoke_status": lookup["drc_smoke"].status,
            "lvs_feasibility_status": lookup["lvs_feasibility"].status,
            "timing_metadata_consistency_status": lookup["timing_metadata_consistency"].status,
            "remaining_L5_basic_validation_blockers": blockers,
            "remaining_L5_basic_validation_blockers_count": len(blockers),
            "can_claim_L5_basic_validation_passed_now": basic_pass,
            "can_claim_validated_full_openyield_gds_now": False,
            "can_claim_drc_clean_now": False,
            "can_claim_lvs_clean_now": False,
            "can_claim_timing_closure_now": False,
            "recommended_next_validation_tasks": recommended,
        }


def emit_validation_reports(
    report: TopLevelValidationReport,
    out_dir: Path,
    out_matrix_csv: Path,
    out_matrix_md: Path,
    out_json: Path,
    out_report: Path,
    evidence_gap_summary: Path,
    evidence_timeline: Path,
    milestone_summary: Path,
) -> None:
    rows = [check.to_matrix_row() for check in report.checks]
    _write_csv(
        out_matrix_csv,
        [
            "check_name",
            "check_category",
            "status",
            "is_blocking_basic_validation",
            "is_blocking_drc_clean",
            "is_blocking_lvs_clean",
            "is_blocking_timing_closure",
            "evidence_file",
            "summary",
            "blocking_gap",
            "next_required_action",
        ],
        rows,
    )
    _write_text(out_matrix_md, _format_matrix_markdown(rows))
    _json_dump(out_dir / "validation_summary.json", report.summary)
    _write_text(out_dir / "validation_summary.md", _format_summary_markdown(report))
    payload = dict(report.summary)
    payload["checks"] = [asdict(check) for check in report.checks]
    _json_dump(out_json, payload)
    _write_text(out_report, _format_summary_markdown(report))
    _write_text(evidence_gap_summary, _format_gap_summary(report))
    _write_text(evidence_timeline, _append_line(evidence_timeline, _timeline_line(report.summary)))
    _write_text(milestone_summary, _append_line(milestone_summary, _milestone_line(report.summary)))


def parse_lyrdb(path: Path) -> list[dict[str, Any]]:
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    categories = {
        category.attrib.get("id"): category.findtext("name", default="")
        for category in root.findall(".//categories/category")
    }
    items = []
    for index, item in enumerate(root.findall(".//items/item"), start=1):
        category_id = item.findtext("category")
        values = item.find("values")
        if values is None:
            continue
        text = "".join(values.itertext()).strip()
        numbers = [float(token) for token in text.replace("polygon:", "").replace("/", ";").replace(",", ";").replace(";", " ").split() if _is_float(token)]
        xs = numbers[0::2]
        ys = numbers[1::2]
        if not xs or not ys:
            continue
        items.append(
            {
                "marker_id": index,
                "rule_name": categories.get(category_id, str(category_id)),
                "bbox": {"x0": min(xs), "y0": min(ys), "x1": max(xs), "y1": max(ys)},
            }
        )
    return items


def _format_matrix_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# OpenYield L5 Validation Matrix",
        "",
        "| Check | Category | Status | Basic Blocker | DRC Blocker | LVS Blocker | Timing Blocker | Evidence | Summary |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['check_name']} | {row['check_category']} | {row['status']} | {row['is_blocking_basic_validation']} | "
            f"{row['is_blocking_drc_clean']} | {row['is_blocking_lvs_clean']} | {row['is_blocking_timing_closure']} | "
            f"{row['evidence_file']} | {row['summary']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _format_summary_markdown(report: TopLevelValidationReport) -> str:
    summary = report.summary
    lines = [
        "# OpenYield L5 Validation Report",
        "",
        "## Summary",
        "",
        f"- top_gds_sanity_status: `{summary['top_gds_sanity_status']}`",
        f"- module_completeness_status: `{summary['module_completeness_status']}`",
        f"- placement_consistency_status: `{summary['placement_consistency_status']}`",
        f"- pin_accessibility_status: `{summary['pin_accessibility_status']}`",
        f"- rail_stitch_audit_status: `{summary['rail_stitch_audit_status']}`",
        f"- routing_handoff_audit_status: `{summary['routing_handoff_audit_status']}`",
        f"- candidate_geometry_risk_status: `{summary['candidate_geometry_risk_status']}`",
        f"- drc_smoke_status: `{summary['drc_smoke_status']}`",
        f"- lvs_feasibility_status: `{summary['lvs_feasibility_status']}`",
        f"- timing_metadata_consistency_status: `{summary['timing_metadata_consistency_status']}`",
        f"- remaining_L5_basic_validation_blockers_count: `{summary['remaining_L5_basic_validation_blockers_count']}`",
        f"- can_claim_L5_basic_validation_passed_now: `{summary['can_claim_L5_basic_validation_passed_now']}`",
        f"- can_claim_validated_full_openyield_gds_now: `{summary['can_claim_validated_full_openyield_gds_now']}`",
        f"- can_claim_drc_clean_now: `{summary['can_claim_drc_clean_now']}`",
        f"- can_claim_lvs_clean_now: `{summary['can_claim_lvs_clean_now']}`",
        f"- can_claim_timing_closure_now: `{summary['can_claim_timing_closure_now']}`",
        "",
        "## Check Results",
        "",
    ]
    for check in report.checks:
        lines.append(f"- `{check.check_name}`: `{check.status}`. {check.summary}")
    lines.extend(["", "## Recommended Next Validation Tasks", ""])
    for task in summary["recommended_next_validation_tasks"]:
        lines.append(f"- {task}")
    lines.append("")
    return "\n".join(lines)


def _format_gap_summary(report: TopLevelValidationReport) -> str:
    summary = report.summary
    passed = [check.check_name for check in report.checks if check.status in {"PASSED", "DRC_SMOKE_RAN_NO_MARKERS"}]
    skipped = [check for check in report.checks if check.status.startswith("SKIPPED")]
    failed = [check for check in report.checks if check.is_blocking_basic_validation]
    lines = [
        "# L5 Validation Gap Summary",
        "",
        "## Checks Run",
        "",
        "- top-level GDS sanity verification",
        "- module completeness verification",
        "- placement consistency verification",
        "- pin metadata / accessibility audit",
        "- rail stitch plan completeness audit",
        "- routing handoff consistency audit",
        "- candidate geometry / contract risk classification",
        "- optional DRC smoke",
        "- optional LVS feasibility audit",
        "- timing metadata consistency audit",
        "",
        "## Passed",
        "",
    ]
    lines.extend(f"- {item}" for item in passed)
    lines.extend(
        [
            "",
            "## Skipped",
            "",
        ]
    )
    lines.extend(f"- {item.check_name}: {item.summary}" for item in skipped)
    lines.extend(
        [
            "",
            "## Candidate Geometry And Contract Pin Impact",
            "",
            "- Candidate geometry and contract pins do not necessarily block first-pass L5 basic validation.",
            "- They still block any claim of full validated GDS, DRC clean, LVS clean, and timing closure.",
            "",
            "## Current Gate",
            "",
            f"- can_claim_L5_basic_validation_passed_now: `{summary['can_claim_L5_basic_validation_passed_now']}`",
            f"- can_claim_validated_full_openyield_gds_now: `{summary['can_claim_validated_full_openyield_gds_now']}`",
            f"- can_claim_drc_clean_now: `{summary['can_claim_drc_clean_now']}`",
            f"- can_claim_lvs_clean_now: `{summary['can_claim_lvs_clean_now']}`",
            f"- can_claim_timing_closure_now: `{summary['can_claim_timing_closure_now']}`",
            "",
            "## Remaining Blockers",
            "",
        ]
    )
    if failed:
        lines.extend(f"- {item.check_name}: {item.blocking_gap or item.summary}" for item in failed)
    else:
        lines.append("- No remaining basic-validation blockers.")
    lines.extend(
        [
            "",
            "## Why Full Validated GDS Is Still Not Claimable",
            "",
            "- Candidate-geometry modules remain in the integrated top-level candidate.",
            "- Contract-pin modules still need geometry-backed accessibility/LVS proof.",
            "- DRC/LVS/timing closure are not fully proven in this pass.",
            "",
            "## Next Priority",
            "",
        ]
    )
    lines.extend(f"- {task}" for task in summary["recommended_next_validation_tasks"])
    lines.append("")
    return "\n".join(lines)


def _append_line(path: Path, line: str) -> str:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    return existing.rstrip() + ("\n" if existing.strip() else "") + line + "\n"


def _timeline_line(summary: dict[str, Any]) -> str:
    return (
        f"- `2026-07-02`: Completed OpenYield L5 validation first round; "
        f"basic_validation_passed=`{summary['can_claim_L5_basic_validation_passed_now']}`, "
        f"top_gds_sanity=`{summary['top_gds_sanity_status']}`, "
        f"module_completeness=`{summary['module_completeness_status']}`, "
        f"drc_smoke=`{summary['drc_smoke_status']}`; "
        "all full-GDS/DRC/LVS/timing signoff claims remain false."
    )


def _milestone_line(summary: dict[str, Any]) -> str:
    return (
        "- L5 first round: top-level candidate GDS validation artifacts are now generated across sanity, completeness, "
        "placement, pins, rail, routing, risk, DRC smoke, LVS feasibility, and timing metadata; "
        f"`can_claim_L5_basic_validation_passed_now={summary['can_claim_L5_basic_validation_passed_now']}` while "
        "`can_claim_validated_full_openyield_gds_now=False`, `can_claim_drc_clean_now=False`, "
        "`can_claim_lvs_clean_now=False`, and `can_claim_timing_closure_now=False`."
    )


def _primitive_alias(module: str) -> str:
    aliases = {
        "bitcell_array": "bitcell",
        "dummy_array": "dummy_cell",
        "replica_array": "replica_cell",
        "precharge": "precharge_cell",
        "decoder_gate_cells": "decoder_leaf_gate",
        "wordline_driver_gate_cells": "wordline_driver_leaf_gate",
        "wordline_decoder": "wordline_decoder_leaf_gate",
        "row_decoder": "decoder_leaf_gate",
        "CONTROL_LOGIC": "control_logic_leaf_gate",
        "GATED_CLOCK_PATH": "gated_clock_leaf_gate",
        "DELAY_CHAIN": "delay_inv",
        "PRECHARGE_ENABLE_PATH": "enable_path_leaf_gate",
        "SENSE_ENABLE_PATH": "enable_path_leaf_gate",
        "WORDLINE_ENABLE_PATH": "enable_path_leaf_gate",
        "WRITE_ENABLE_PATH": "enable_path_leaf_gate",
        "DFF_ROW": "dff_cell",
    }
    return aliases.get(module, module)


def _normalize_bbox(bbox: Any) -> dict[str, float]:
    x0, y0 = bbox[0]
    x1, y1 = bbox[1]
    return {"x0": float(x0), "y0": float(y0), "x1": float(x1), "y1": float(y1), "width": float(x1 - x0), "height": float(y1 - y0)}


def _run_parser_subprocess(parser_name: str, command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    attempt = {
        "parser": parser_name,
        "available": completed.returncode != 127,
        "success": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-800:],
        "stderr": completed.stderr[-800:],
    }
    if completed.returncode != 0:
        return {"attempt": attempt, "success": False}
    try:
        payload = json.loads(completed.stdout.strip().splitlines()[-1])
    except Exception as exc:
        attempt["success"] = False
        attempt["parse_error"] = str(exc)
        return {"attempt": attempt, "success": False}
    if not payload.get("available", True):
        attempt["available"] = False
        attempt["success"] = False
        return {"attempt": attempt, "success": False}
    payload["attempt"] = attempt
    payload["success"] = bool(payload.get("success"))
    return payload


def _temp_work_dir(path: Path) -> Path:
    stem = path.stem.replace(".", "_")
    return Path("/tmp") / f"openyield_l5_{stem}"


def _is_float(token: str) -> bool:
    try:
        float(token)
    except ValueError:
        return False
    return True


def shutil_which(binary: str) -> str | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / binary
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None
