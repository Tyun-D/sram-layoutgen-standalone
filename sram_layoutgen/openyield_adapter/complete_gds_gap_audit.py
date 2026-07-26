from __future__ import annotations

import csv
import collections
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.gds_util import inspect_gds_hierarchy, inspect_gds_layers
from sram_layoutgen.openyield_adapter.gds_pin_audit import GdsShape, GdsText, read_gds_labels_and_shapes


TRACKED_CONTRACT_STATUSES = {
    "CONTRACT_PIN_BASED_ROUTE",
    "CONTRACT_PIN_EXPORTED_FOR_R4",
    "CONTRACT_RAIL_BASED_STITCH",
    "APPROXIMATE_GEOMETRY_FOR_R4",
    "APPROXIMATE_POWER_GEOMETRY_FOR_R4",
    "CONTRACT_PIN_BASED",
    "CONTRACT_RAIL_BASED",
}
CONTRACT_ROUTE_STATUSES = {
    "CONTRACT_PIN_BASED_ROUTE",
    "CONTRACT_PIN_EXPORTED_FOR_R4",
    "CONTRACT_PIN_BASED",
}
APPROXIMATE_ROUTE_STATUSES = {
    "APPROXIMATE_GEOMETRY_FOR_R4",
}
POWER_CONTRACT_STATUSES = {
    "CONTRACT_RAIL_BASED_STITCH",
    "CONTRACT_RAIL_BASED",
}
POWER_APPROXIMATE_STATUSES = {
    "APPROXIMATE_POWER_GEOMETRY_FOR_R4",
}
GEOMETRY_ROUTE_STATUSES = {
    "GEOMETRY_ROUTED_FOR_R4",
}
GEOMETRY_POWER_STATUSES = {
    "GEOMETRY_POWER_STITCH_FOR_R4",
}
GEOMETRY_PIN_STATUSES = {
    "GEOMETRY_PIN_EXPORTED_FOR_R4",
}
PIN_STATUS_GEOMETRY_BACKED = "GEOMETRY_BACKED_PIN"
PIN_STATUS_LABEL_ONLY = "LABEL_ONLY_PIN"
PIN_STATUS_CONTRACT_ONLY = "CONTRACT_ONLY_PIN"
PIN_STATUS_MISSING = "MISSING_PIN"
PIN_STATUS_UNKNOWN = "UNKNOWN_PIN_STATUS"

CONTRACT_CONNECTION_COLUMNS = [
    "net_name",
    "net_category",
    "source_instance",
    "source_pin",
    "target_instance",
    "target_pin",
    "route_group",
    "routing_status",
    "uses_contract_pin",
    "uses_approximate_geometry",
    "shape_bbox",
    "layer_hint",
    "why_not_complete_gds",
    "required_fix_stage",
    "recommended_fix",
]
APPROXIMATE_GEOMETRY_COLUMNS = [
    "entry_id",
    "net_name",
    "net_category",
    "shape_type",
    "shape_bbox",
    "layer_hint",
    "approximation_type",
    "affected_modules",
    "why_approximate",
    "blocks_complete_gds",
    "required_fix_stage",
    "recommended_fix",
]
CONTRACT_POWER_COLUMNS = [
    "net_name",
    "net_category",
    "source_instance",
    "source_pin",
    "target_instance",
    "target_pin",
    "route_group",
    "routing_status",
    "uses_contract_pin",
    "uses_approximate_geometry",
    "shape_bbox",
    "layer_hint",
    "why_not_complete_gds",
    "required_fix_stage",
    "recommended_fix",
]
MISSING_PIN_COLUMNS = [
    "module_name",
    "instance_name",
    "pin_name",
    "pin_category",
    "current_pin_status",
    "has_pins_json_entry",
    "has_label",
    "has_shape_bbox",
    "has_layer",
    "can_extract_from_gds",
    "can_synthesize_for_current_generator",
    "blocks_wl_bl_control_power_or_top_pin",
    "required_fix_stage",
    "recommended_fix",
]
REAL_GEOMETRY_COLUMNS = [
    "net_name",
    "net_category",
    "shape_type",
    "shape_bbox",
    "layer_hint",
    "source_instance",
    "target_instance",
    "is_pin_to_pin_geometry",
    "is_power_geometry",
    "is_top_pin_geometry",
    "is_visual_placeholder",
    "complete_gds_ready",
    "evidence_source",
]
BLOCKER_COLUMNS = [
    "blocker_id",
    "blocker_category",
    "affected_net_or_module",
    "evidence_source",
    "current_status",
    "why_blocks_complete_gds",
    "required_fix_stage",
    "priority",
    "recommended_fix",
    "blocks_C1",
    "blocks_C2",
    "blocks_C3",
    "blocks_C4",
    "blocks_C5",
    "blocks_C6",
]


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _md_table(columns: list[str], rows: list[dict[str, Any]]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        rendered = []
        for column in columns:
            value = row.get(column, "")
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            rendered.append(str(value).replace("\n", "<br>"))
        lines.append("| " + " | ".join(rendered) + " |")
    return "\n".join(lines) + "\n"


def _round(value: float) -> float:
    return round(float(value), 6)


def _bbox_from_obj(value: Any) -> dict[str, float] | None:
    if value is None:
        return None
    if isinstance(value, dict) and {"x0", "y0", "x1", "y1"}.issubset(value):
        return {
            "x0": _round(value["x0"]),
            "y0": _round(value["y0"]),
            "x1": _round(value["x1"]),
            "y1": _round(value["y1"]),
            "width": _round(value.get("width", value["x1"] - value["x0"])),
            "height": _round(value.get("height", value["y1"] - value["y0"])),
        }
    if isinstance(value, (tuple, list)) and len(value) == 2 and len(value[0]) == 2 and len(value[1]) == 2:
        (x0, y0), (x1, y1) = value
        x0f, x1f = min(float(x0), float(x1)), max(float(x0), float(x1))
        y0f, y1f = min(float(y0), float(y1)), max(float(y0), float(y1))
        return {
            "x0": _round(x0f),
            "y0": _round(y0f),
            "x1": _round(x1f),
            "y1": _round(y1f),
            "width": _round(x1f - x0f),
            "height": _round(y1f - y0f),
        }
    return None


def _bbox_area(bbox: dict[str, float] | None) -> float:
    if not bbox:
        return 0.0
    width = float(bbox.get("width", float(bbox["x1"]) - float(bbox["x0"])))
    height = float(bbox.get("height", float(bbox["y1"]) - float(bbox["y0"])))
    return _round(max(0.0, width) * max(0.0, height))


def _bbox_close(lhs: dict[str, float] | None, rhs: dict[str, float] | None, tol: float = 0.01) -> bool:
    if lhs is None or rhs is None:
        return False
    keys = ("x0", "y0", "x1", "y1")
    return all(abs(float(lhs[key]) - float(rhs[key])) <= tol for key in keys)


def _bbox_contains_point(bbox: dict[str, float], x: float, y: float, tol: float = 0.0) -> bool:
    return bbox["x0"] - tol <= x <= bbox["x1"] + tol and bbox["y0"] - tol <= y <= bbox["y1"] + tol


def _status_from_entry(entry: dict[str, Any]) -> str:
    for key in ("routing_status", "power_status", "pin_status", "status"):
        value = entry.get(key)
        if value:
            return str(value)
    return "UNKNOWN"


def _module_labels_by_name(labels: tuple[GdsText, ...]) -> dict[str, list[GdsText]]:
    grouped: dict[str, list[GdsText]] = {}
    for label in labels:
        grouped.setdefault(str(label.text), []).append(label)
    return grouped


def _layer_token(value: Any) -> str:
    return str(value).strip().lower().replace("metal", "m")


def _layer_matches(module_layer: str | None, shape_layer: int | None) -> bool:
    if not module_layer:
        return True
    token = _layer_token(module_layer)
    mapping = {
        "m1": {1, 11},
        "m2": {2, 12},
        "m3": {3, 13},
        "m4": {4, 14},
        "m5": {5, 15},
        "m6": {6, 16},
    }
    allowed = mapping.get(token)
    if allowed is None or shape_layer is None:
        return True
    return int(shape_layer) in allowed


def _normalize_pin_name(pin_name: str) -> str:
    text = str(pin_name).strip()
    return text.replace("<", "[").replace(">", "]")


def _pin_name_matches(query: str, candidate: str) -> bool:
    lhs = _normalize_pin_name(query)
    rhs = _normalize_pin_name(candidate)
    if lhs == rhs:
        return True
    if rhs.endswith("[*]") and lhs.startswith(rhs[:-3] + "["):
        return True
    if lhs.endswith("[*]") and rhs.startswith(lhs[:-3] + "["):
        return True
    if "/" in lhs:
        return any(_pin_name_matches(part.strip(), rhs) for part in lhs.split("/"))
    if ";" in lhs:
        return any(_pin_name_matches(part.strip(), rhs) for part in lhs.split(";"))
    aliases = {
        "bl/br": {"bl", "br"},
        "bl": {"bl", "bl[*]"},
        "br": {"br", "br[*]"},
        "wl": {"wl", "wl[*]"},
        "rbl": {"rbl", "rbl[*]"},
    }
    lhs_key = lhs.lower()
    rhs_key = rhs.lower()
    if lhs_key in aliases and rhs_key in aliases[lhs_key]:
        return True
    return False


def _infer_pin_category(net_name: str, net_category: str, pin_name: str) -> str:
    category = str(net_category or "").upper()
    if category:
        return category
    name = str(net_name or pin_name).upper()
    if name.startswith("WL"):
        return "WORDLINE"
    if name.startswith("BL") or name.startswith("BR"):
        return "BITLINE"
    if name in {"VDD", "GND"}:
        return "POWER" if name == "VDD" else "GROUND"
    if name.startswith("A["):
        return "ADDRESS"
    if name.startswith("DIN["):
        return "DATA_IN"
    if name.startswith("DOUT["):
        return "DATA_OUT"
    return "CONTROL"


def _route_bucket(net_category: str, route_group: str) -> str:
    text = f"{net_category}|{route_group}".upper()
    if "WORDLINE" in text:
        return "WORDLINE"
    if "BITLINE" in text or "COLUMN" in text:
        return "BITLINE"
    if "POWER" in text or "GROUND" in text:
        return "POWER"
    if "TOP_PIN" in text or "ADDRESS" in text or "DATA_" in text or "CLOCK_CONTROL" in text:
        return "TOP_PIN"
    return "CONTROL"


def _is_large_placeholder_bbox(bbox: dict[str, float] | None, top_bbox: dict[str, float] | None) -> bool:
    if bbox is None or top_bbox is None:
        return False
    width_ratio = bbox["width"] / max(top_bbox["width"], 1e-6)
    height_ratio = bbox["height"] / max(top_bbox["height"], 1e-6)
    area_ratio = _bbox_area(bbox) / max(_bbox_area(top_bbox), 1e-6)
    return (
        area_ratio >= 0.015
        or width_ratio >= 0.45
        or height_ratio >= 0.45
        or (width_ratio >= 0.20 and height_ratio <= 0.02)
        or (height_ratio >= 0.20 and width_ratio <= 0.02)
    )


def _approximation_type(entry: dict[str, Any], top_bbox: dict[str, float] | None) -> str | None:
    status = _status_from_entry(entry)
    shape_type = str(entry.get("shape_type", ""))
    bbox = _bbox_from_obj(entry.get("shape_bbox") or entry.get("geometry_bbox") or entry.get("route_geometry_bbox"))
    if status in POWER_APPROXIMATE_STATUSES:
        return "APPROXIMATE_POWER_GEOMETRY"
    if status in APPROXIMATE_ROUTE_STATUSES:
        return "APPROXIMATE_GEOMETRY"
    if _is_large_placeholder_bbox(bbox, top_bbox):
        if shape_type == "power_segment":
            return "LARGE_RECTANGLE_POWER_PLACEHOLDER"
        return "BBOX_ONLY_ROUTE"
    if entry.get("uses_approximate_geometry"):
        return "PROTOTYPE_ONLY_GEOMETRY"
    return None


def _git_commit(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


@dataclass(frozen=True)
class CompleteGdsGapAuditConfig:
    repo_root: Path
    r5_report_json: Path
    r4_routing_dir: Path
    r5_final_dir: Path
    module_gds_dir: Path
    out_dir: Path
    out_matrix_csv: Path
    out_matrix_md: Path
    out_json: Path
    out_report: Path


@dataclass(frozen=True)
class ContractConnectionEntry:
    net_name: str
    net_category: str
    source_instance: str
    source_pin: str
    target_instance: str
    target_pin: str
    route_group: str
    routing_status: str
    uses_contract_pin: bool
    uses_approximate_geometry: bool
    shape_bbox: dict[str, float] | None
    layer_hint: str
    why_not_complete_gds: str
    required_fix_stage: str
    recommended_fix: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApproximateGeometryEntry:
    entry_id: str
    net_name: str
    net_category: str
    shape_type: str
    shape_bbox: dict[str, float] | None
    layer_hint: str
    approximation_type: str
    affected_modules: tuple[str, ...]
    why_approximate: str
    blocks_complete_gds: bool
    required_fix_stage: str
    recommended_fix: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ContractPowerEntry:
    net_name: str
    net_category: str
    source_instance: str
    source_pin: str
    target_instance: str
    target_pin: str
    route_group: str
    routing_status: str
    uses_contract_pin: bool
    uses_approximate_geometry: bool
    shape_bbox: dict[str, float] | None
    layer_hint: str
    why_not_complete_gds: str
    required_fix_stage: str
    recommended_fix: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MissingPinGeometryEntry:
    module_name: str
    instance_name: str
    pin_name: str
    pin_category: str
    current_pin_status: str
    has_pins_json_entry: bool
    has_label: bool
    has_shape_bbox: bool
    has_layer: bool
    can_extract_from_gds: bool
    can_synthesize_for_current_generator: bool
    blocks_wl_bl_control_power_or_top_pin: str
    required_fix_stage: str
    recommended_fix: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RealGeometryEntry:
    net_name: str
    net_category: str
    shape_type: str
    shape_bbox: dict[str, float] | None
    layer_hint: str
    source_instance: str
    target_instance: str
    is_pin_to_pin_geometry: bool
    is_power_geometry: bool
    is_top_pin_geometry: bool
    is_visual_placeholder: bool
    complete_gds_ready: bool
    evidence_source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompleteGdsBlocker:
    blocker_id: str
    blocker_category: str
    affected_net_or_module: str
    evidence_source: str
    current_status: str
    why_blocks_complete_gds: str
    required_fix_stage: str
    priority: str
    recommended_fix: str
    blocks_C1: bool
    blocks_C2: bool
    blocks_C3: bool
    blocks_C4: bool
    blocks_C5: bool
    blocks_C6: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompleteGdsGapAuditResult:
    report: dict[str, Any]
    contract_connection_inventory: tuple[ContractConnectionEntry, ...]
    approximate_geometry_inventory: tuple[ApproximateGeometryEntry, ...]
    contract_power_inventory: tuple[ContractPowerEntry, ...]
    missing_pin_geometry_inventory: tuple[MissingPinGeometryEntry, ...]
    real_geometry_inventory: tuple[RealGeometryEntry, ...]
    blocker_matrix: tuple[CompleteGdsBlocker, ...]


class CompleteGdsGapAuditor:
    def __init__(self, config: CompleteGdsGapAuditConfig) -> None:
        self.config = config
        self._required_inputs = {
            "r5_report_json": config.r5_report_json,
            "r5_report_md": config.repo_root / "docs/openyield_R5_final_validation_handoff_report.md",
            "r4_gds": config.r4_routing_dir / "openyield_routed_power_pin_sram.gds",
            "net_to_shape_map_json": config.r4_routing_dir / "net_to_shape_map.json",
            "net_to_shape_map_csv": config.r4_routing_dir / "net_to_shape_map.csv",
            "instance_mapping_json": config.r4_routing_dir / "instance_mapping.json",
            "wordline_routing_report_json": config.r4_routing_dir / "wordline_routing_report.json",
            "bitline_routing_report_json": config.r4_routing_dir / "bitline_routing_report.json",
            "control_routing_report_json": config.r4_routing_dir / "control_routing_report.json",
            "power_routing_report_json": config.r4_routing_dir / "power_routing_report.json",
            "top_pin_export_report_json": config.r4_routing_dir / "top_pin_export_report.json",
            "final_risk_register_json": config.r5_final_dir / "final_risk_register.json",
            "final_gds_sanity_report_json": config.r5_final_dir / "final_gds_sanity_report.json",
            "final_hierarchy_validation_report_json": config.r5_final_dir / "final_hierarchy_validation_report.json",
            "final_topology_validation_report_json": config.r5_final_dir / "final_topology_validation_report.json",
            "final_routing_completeness_audit_json": config.r5_final_dir / "final_routing_completeness_audit.json",
            "final_power_continuity_audit_json": config.r5_final_dir / "final_power_continuity_audit.json",
            "final_pin_export_audit_json": config.r5_final_dir / "final_pin_export_audit.json",
            "final_net_mapping_audit_json": config.r5_final_dir / "final_net_mapping_audit.json",
            "final_gds_comparison_report_json": config.r5_final_dir / "final_gds_comparison_report.json",
        }

    def run(self) -> CompleteGdsGapAuditResult:
        missing_inputs = [name for name, path in self._required_inputs.items() if not path.exists()]
        if missing_inputs:
            raise FileNotFoundError(f"C0 input files missing: {', '.join(missing_inputs)}")

        payloads = {name: _load_json(path) for name, path in self._required_inputs.items() if path.suffix == ".json"}
        gds_analysis = self._analyze_top_gds(self._required_inputs["r4_gds"])
        module_metadata = self._load_module_metadata()

        net_entries = list(payloads["net_to_shape_map_json"]["entries"])
        instance_mapping = list(payloads["instance_mapping_json"]["entries"])
        instance_to_module = {row["layout_instance_name"]: row["openyield_module_name"] for row in instance_mapping}

        contract_connections = self._build_contract_connections(net_entries)
        approximate_geometry = self._build_approximate_geometry(net_entries, gds_analysis["top_bbox"])
        contract_power = self._build_contract_power(net_entries)
        missing_pins = self._build_missing_pin_inventory(net_entries, payloads["top_pin_export_report_json"], instance_to_module, module_metadata)
        real_geometry = self._build_real_geometry_inventory(net_entries, gds_analysis)
        blockers = self._build_blocker_matrix(contract_connections, approximate_geometry, contract_power, missing_pins, real_geometry, payloads, gds_analysis)

        report = self._build_report(contract_connections, approximate_geometry, contract_power, missing_pins, real_geometry, blockers, payloads, gds_analysis)
        self._write_outputs(report, contract_connections, approximate_geometry, contract_power, missing_pins, real_geometry, blockers, gds_analysis)
        return CompleteGdsGapAuditResult(
            report=report,
            contract_connection_inventory=tuple(contract_connections),
            approximate_geometry_inventory=tuple(approximate_geometry),
            contract_power_inventory=tuple(contract_power),
            missing_pin_geometry_inventory=tuple(missing_pins),
            real_geometry_inventory=tuple(real_geometry),
            blocker_matrix=tuple(blockers),
        )

    def _load_module_metadata(self) -> dict[str, dict[str, Any]]:
        metadata: dict[str, dict[str, Any]] = {}
        module_dirs = sorted(path for path in self.config.module_gds_dir.iterdir() if path.is_dir())
        for module_dir in module_dirs:
            pins_path = module_dir / "pins.json"
            bbox_path = module_dir / "bbox.json"
            rail_path = module_dir / "rail_report.json"
            if not pins_path.exists() or not bbox_path.exists() or not rail_path.exists():
                raise FileNotFoundError(f"module metadata missing in {module_dir}")
            gds_candidates = sorted(module_dir.glob("*.gds"))
            if not gds_candidates:
                raise FileNotFoundError(f"module GDS missing in {module_dir}")
            labels, shapes, bbox = read_gds_labels_and_shapes(gds_candidates[0])
            metadata[module_dir.name] = {
                "pins": _load_json(pins_path).get("pins", []),
                "bbox_json": _load_json(bbox_path),
                "rail_report": _load_json(rail_path),
                "gds_path": gds_candidates[0],
                "labels": labels,
                "labels_by_name": _module_labels_by_name(labels),
                "shapes": shapes,
                "gds_bbox": _bbox_from_obj(bbox.to_dict() if bbox else _load_json(bbox_path)),
            }
        return metadata

    def _analyze_top_gds(self, gds_path: Path) -> dict[str, Any]:
        lib = gdstk.read_gds(gds_path)
        cells = list(lib.cells)
        cell_map = {str(cell.name): cell for cell in cells}
        top = next((cell for cell in cells if str(cell.name) == "openyield_routed_power_pin_sram"), cells[0] if cells else None)
        if top is None:
            raise RuntimeError("top cell missing in routed power/pin GDS")
        top_bbox = _bbox_from_obj(top.bounding_box())
        recursive_count = 0

        def visit(cell: gdstk.Cell) -> None:
            nonlocal recursive_count
            for ref in cell.references:
                recursive_count += 1
                child = cell_map.get(str(ref.cell_name))
                if child is not None:
                    visit(child)

        visit(top)
        shape_rows: list[dict[str, Any]] = []
        for index, polygon in enumerate(top.polygons):
            bbox = _bbox_from_obj(polygon.bounding_box())
            shape_rows.append(
                {
                    "shape_id": f"top_poly_{index}",
                    "layer_hint": f"{polygon.layer}/{polygon.datatype}",
                    "bbox": bbox,
                    "area": _bbox_area(bbox),
                    "is_rectangle": True,
                    "is_suspicious": _is_large_placeholder_bbox(bbox, top_bbox),
                }
            )
        shape_rows.sort(key=lambda row: row["area"], reverse=True)
        return {
            "top_cell_name": str(top.name),
            "cell_count": len(cells),
            "recursive_instance_count": recursive_count,
            "top_bbox": top_bbox,
            "layer_summary": inspect_gds_layers(gds_path),
            "hierarchy_summary": inspect_gds_hierarchy(gds_path),
            "top_shapes": shape_rows,
            "largest_shapes": shape_rows[:10],
            "suspicious_shapes": [row for row in shape_rows if row["is_suspicious"]],
            "top_label_count": len(top.labels),
            "top_polygon_count": len(top.polygons),
        }

    def _build_contract_connections(self, net_entries: list[dict[str, Any]]) -> list[ContractConnectionEntry]:
        rows: list[ContractConnectionEntry] = []
        for entry in net_entries:
            status = _status_from_entry(entry)
            if status not in TRACKED_CONTRACT_STATUSES and not entry.get("uses_contract_pin"):
                continue
            if str(entry.get("route_group")) == "POWER":
                continue
            rows.append(
                ContractConnectionEntry(
                    net_name=str(entry.get("net_name", "")),
                    net_category=str(entry.get("net_category", "")),
                    source_instance=str(entry.get("source_instance", entry.get("source_module", ""))),
                    source_pin=str(entry.get("source_pin", "")),
                    target_instance=str(entry.get("target_instance", entry.get("target_module", ""))),
                    target_pin=str(entry.get("target_pin", "")),
                    route_group=str(entry.get("route_group", "")),
                    routing_status=status,
                    uses_contract_pin=bool(entry.get("uses_contract_pin", False)),
                    uses_approximate_geometry=bool(entry.get("uses_approximate_geometry", False)),
                    shape_bbox=_bbox_from_obj(entry.get("shape_bbox") or entry.get("geometry_bbox") or entry.get("route_geometry_bbox")),
                    layer_hint=str(entry.get("layer_hint", "")),
                    why_not_complete_gds="Route terminates on contract pin ownership or prototype-only handoff instead of module pin geometry.",
                    required_fix_stage="C2/C4",
                    recommended_fix=str(entry.get("next_required_action", "Extract real source/target access geometry and re-route pin-to-pin.")),
                )
            )
        return rows

    def _build_approximate_geometry(self, net_entries: list[dict[str, Any]], top_bbox: dict[str, float] | None) -> list[ApproximateGeometryEntry]:
        rows: list[ApproximateGeometryEntry] = []
        seen: set[tuple[str, str, str]] = set()
        for index, entry in enumerate(net_entries):
            approximation_type = _approximation_type(entry, top_bbox)
            if approximation_type is None:
                continue
            affected_modules = tuple(
                item.strip()
                for item in str(entry.get("target_instance", entry.get("target_module", ""))).replace("_inst", "").split(";")
                if item.strip()
            )
            row = ApproximateGeometryEntry(
                entry_id=f"approx_{index:03d}",
                net_name=str(entry.get("net_name", "")),
                net_category=str(entry.get("net_category", "")),
                shape_type=str(entry.get("shape_type", "route_segment")),
                shape_bbox=_bbox_from_obj(entry.get("shape_bbox") or entry.get("geometry_bbox") or entry.get("route_geometry_bbox")),
                layer_hint=str(entry.get("layer_hint", "")),
                approximation_type=approximation_type,
                affected_modules=affected_modules,
                why_approximate=str(entry.get("next_required_action", "Prototype geometry uses bbox-only ownership and not extracted route access points.")),
                blocks_complete_gds=True,
                required_fix_stage="C3/C4/C5" if "POWER" in approximation_type else "C2/C4",
                recommended_fix="Replace bbox-only stripe/strap with real pin-to-pin or rail-to-pin geometry.",
            )
            key = (row.net_name, row.layer_hint, json.dumps(row.shape_bbox, sort_keys=True))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
        return rows

    def _build_contract_power(self, net_entries: list[dict[str, Any]]) -> list[ContractPowerEntry]:
        rows: list[ContractPowerEntry] = []
        for entry in net_entries:
            if str(entry.get("route_group")) != "POWER":
                continue
            status = _status_from_entry(entry)
            if status not in POWER_CONTRACT_STATUSES and status not in POWER_APPROXIMATE_STATUSES:
                continue
            rows.append(
                ContractPowerEntry(
                    net_name=str(entry.get("net_name", "")),
                    net_category=str(entry.get("net_category", "")),
                    source_instance=str(entry.get("source_instance", "")),
                    source_pin=str(entry.get("source_pin", "")),
                    target_instance=str(entry.get("target_instance", "")),
                    target_pin=str(entry.get("target_pin", "")),
                    route_group=str(entry.get("route_group", "")),
                    routing_status=status,
                    uses_contract_pin=bool(entry.get("uses_contract_pin", False)),
                    uses_approximate_geometry=bool(entry.get("uses_approximate_geometry", False)),
                    shape_bbox=_bbox_from_obj(entry.get("shape_bbox")),
                    layer_hint=str(entry.get("layer_hint", "")),
                    why_not_complete_gds="Power connection is still contract-rail stitching or approximate strap geometry, not per-module rail access and via connection.",
                    required_fix_stage="C2/C5",
                    recommended_fix=str(entry.get("next_required_action", "Extract real VDD/GND pin geometry and synthesize explicit taps/continuity.")),
                )
            )
        return rows

    def _build_missing_pin_inventory(
        self,
        net_entries: list[dict[str, Any]],
        top_pin_report: dict[str, Any],
        instance_to_module: dict[str, str],
        module_metadata: dict[str, dict[str, Any]],
    ) -> list[MissingPinGeometryEntry]:
        pin_refs: dict[tuple[str, str, str, str], dict[str, str]] = {}

        def add_pin(instance_name: str, pin_name: str, net_name: str, net_category: str) -> None:
            if not instance_name or not pin_name:
                return
            bucket = _route_bucket(net_category, net_category)
            key = (instance_name, pin_name, bucket, net_name)
            pin_refs.setdefault(
                key,
                {
                    "instance_name": instance_name,
                    "pin_name": pin_name,
                    "pin_category": _infer_pin_category(net_name, net_category, pin_name),
                    "bucket": bucket,
                },
            )

        for entry in net_entries:
            route_group = str(entry.get("route_group", ""))
            net_name = str(entry.get("net_name", ""))
            net_category = str(entry.get("net_category", ""))
            source_instance = str(entry.get("source_instance", ""))
            if source_instance != "SRAM_TOP":
                add_pin(source_instance, str(entry.get("source_pin", "")), net_name, net_category)
            if route_group == "POWER":
                for module_name in str(entry.get("target_instance", "")).split(";"):
                    module_name = module_name.strip()
                    if module_name:
                        add_pin(module_name + "_inst", str(entry.get("target_pin", "")), net_name, net_category)
            else:
                add_pin(str(entry.get("target_instance", "")), str(entry.get("target_pin", "")), net_name, net_category)

        for entry in top_pin_report.get("entries", []):
            add_pin("TOP_PIN", str(entry.get("pin_name", "")), str(entry.get("connected_internal_net", entry.get("pin_name", ""))), str(entry.get("pin_category", "")))

        rows: list[MissingPinGeometryEntry] = []
        for item in pin_refs.values():
            instance_name = item["instance_name"]
            pin_name = item["pin_name"]
            bucket = item["bucket"]
            if instance_name == "TOP_PIN":
                rows.append(
                    MissingPinGeometryEntry(
                        module_name="SRAM_TOP",
                        instance_name="TOP_PIN",
                        pin_name=pin_name,
                        pin_category=item["pin_category"],
                        current_pin_status=PIN_STATUS_GEOMETRY_BACKED,
                        has_pins_json_entry=True,
                        has_label=True,
                        has_shape_bbox=True,
                        has_layer=True,
                        can_extract_from_gds=True,
                        can_synthesize_for_current_generator=True,
                        blocks_wl_bl_control_power_or_top_pin=bucket,
                        required_fix_stage="NONE",
                        recommended_fix="Keep exported top pin geometry but align it to real internal access routes later.",
                    )
                )
                continue

            module_name = instance_to_module.get(instance_name, instance_name.replace("_inst", ""))
            metadata = module_metadata.get(module_name)
            pins = list(metadata.get("pins", [])) if metadata else []
            matches = [pin for pin in pins if _pin_name_matches(pin_name, str(pin.get("name", "")))]
            has_pins_json_entry = bool(matches)
            labels_by_name = metadata.get("labels_by_name", {}) if metadata else {}
            shapes = metadata.get("shapes", ()) if metadata else ()
            module_bbox = metadata.get("gds_bbox") if metadata else None
            has_label = False
            raw_shape_hit = False
            localized_shape_hit = False
            has_layer = False
            for match in matches:
                has_layer = has_layer or bool(match.get("layer"))
                x = float(match.get("x", 0.0))
                y = float(match.get("y", 0.0))
                name = str(match.get("name", ""))
                if labels_by_name.get(name):
                    has_label = True
                for shape in shapes:
                    shape_bbox = shape.bbox.to_dict()
                    if not _layer_matches(str(match.get("layer", "")), shape.layer):
                        continue
                    if not _bbox_contains_point(shape_bbox, x, y, tol=0.03):
                        continue
                    raw_shape_hit = True
                    if module_bbox and _bbox_area(shape_bbox) <= 0.50 * max(_bbox_area(module_bbox), 1e-9):
                        localized_shape_hit = True
            if localized_shape_hit:
                status = PIN_STATUS_GEOMETRY_BACKED
            elif has_label:
                status = PIN_STATUS_LABEL_ONLY
            elif has_pins_json_entry:
                status = PIN_STATUS_CONTRACT_ONLY
            elif metadata is None:
                status = PIN_STATUS_MISSING
            else:
                status = PIN_STATUS_MISSING

            if bucket == "WORDLINE":
                fix_stage = "C2/C4"
                fix_text = "Extract wordline driver/array WL access geometry and rebuild true row access routes."
            elif bucket == "BITLINE":
                fix_stage = "C2/C4"
                fix_text = "Extract BL/BR, mux, sense amp, and write-driver access shapes and replace aggregate bitline contracts."
            elif bucket == "POWER":
                fix_stage = "C2/C5"
                fix_text = "Extract module VDD/GND rail geometry and replace rail-contract stitching with explicit taps."
            elif bucket == "TOP_PIN":
                fix_stage = "C4/C6"
                fix_text = "Tie top IO metal to real internal routes rather than prototype net-map ownership."
            else:
                fix_stage = "C2/C4"
                fix_text = "Extract control pin geometry and rebuild true control spine access."

            rows.append(
                MissingPinGeometryEntry(
                    module_name=module_name,
                    instance_name=instance_name,
                    pin_name=pin_name,
                    pin_category=item["pin_category"],
                    current_pin_status=status,
                    has_pins_json_entry=has_pins_json_entry,
                    has_label=has_label,
                    has_shape_bbox=localized_shape_hit,
                    has_layer=has_layer,
                    can_extract_from_gds=raw_shape_hit or has_label,
                    can_synthesize_for_current_generator=has_pins_json_entry,
                    blocks_wl_bl_control_power_or_top_pin=bucket,
                    required_fix_stage=fix_stage,
                    recommended_fix=fix_text,
                )
            )
        rows.sort(key=lambda row: (row.blocks_wl_bl_control_power_or_top_pin, row.instance_name, row.pin_name))
        return rows

    def _build_real_geometry_inventory(self, net_entries: list[dict[str, Any]], gds_analysis: dict[str, Any]) -> list[RealGeometryEntry]:
        rows: list[RealGeometryEntry] = []
        top_shapes = gds_analysis["top_shapes"]
        shape_counter = collections.Counter(
            (
                json.dumps(row["bbox"], sort_keys=True),
                row["layer_hint"],
            )
            for row in top_shapes
        )
        unmatched_entries: list[str] = []
        for entry in net_entries:
            bbox = _bbox_from_obj(entry.get("shape_bbox") or entry.get("geometry_bbox") or entry.get("route_geometry_bbox"))
            layer_hint = str(entry.get("layer_hint", ""))
            matched_key = None
            for row in top_shapes:
                if not _bbox_close(bbox, row["bbox"], tol=0.02):
                    continue
                candidate_key = (json.dumps(row["bbox"], sort_keys=True), row["layer_hint"])
                if shape_counter[candidate_key] <= 0:
                    continue
                matched_key = candidate_key
                break
            shape_match = matched_key is not None
            if not shape_match:
                unmatched_entries.append(entry.get("net_name", ""))
            else:
                shape_counter[matched_key] -= 1
            status = _status_from_entry(entry)
            route_group = str(entry.get("route_group", ""))
            visual_placeholder = _is_large_placeholder_bbox(bbox, gds_analysis["top_bbox"]) or status in POWER_APPROXIMATE_STATUSES
            is_top_pin = route_group == "TOP_PIN"
            is_power = route_group == "POWER"
            is_pin_to_pin = status in GEOMETRY_ROUTE_STATUSES and not visual_placeholder and not entry.get("uses_contract_pin", False)
            rows.append(
                RealGeometryEntry(
                    net_name=str(entry.get("net_name", "")),
                    net_category=str(entry.get("net_category", "")),
                    shape_type=str(entry.get("shape_type", "")),
                    shape_bbox=bbox,
                    layer_hint=layer_hint,
                    source_instance=str(entry.get("source_instance", "")),
                    target_instance=str(entry.get("target_instance", "")),
                    is_pin_to_pin_geometry=is_pin_to_pin,
                    is_power_geometry=is_power,
                    is_top_pin_geometry=is_top_pin,
                    is_visual_placeholder=visual_placeholder,
                    complete_gds_ready=shape_match and not visual_placeholder and not entry.get("uses_contract_pin", False) and status not in TRACKED_CONTRACT_STATUSES,
                    evidence_source="outputs/openyield_routing_power_pin/current_supported_config/net_to_shape_map.json;outputs/openyield_routing_power_pin/current_supported_config/openyield_routed_power_pin_sram.gds",
                )
            )
        gds_analysis["entries_without_shape_match"] = unmatched_entries
        gds_analysis["shapes_without_net_entry"] = [
            row for row in top_shapes if shape_counter[(json.dumps(row["bbox"], sort_keys=True), row["layer_hint"])] > 0
        ]
        return rows

    def _build_blocker_matrix(
        self,
        contract_connections: list[ContractConnectionEntry],
        approximate_geometry: list[ApproximateGeometryEntry],
        contract_power: list[ContractPowerEntry],
        missing_pins: list[MissingPinGeometryEntry],
        real_geometry: list[RealGeometryEntry],
        payloads: dict[str, Any],
        gds_analysis: dict[str, Any],
    ) -> list[CompleteGdsBlocker]:
        blockers: list[CompleteGdsBlocker] = []
        counter = 1

        def add(category: str, affected: str, evidence: str, status: str, why: str, stage: str, priority: str, fix: str, c2: bool, c3: bool, c4: bool, c5: bool, c6: bool) -> None:
            nonlocal counter
            blockers.append(
                CompleteGdsBlocker(
                    blocker_id=f"BLK_{counter:03d}",
                    blocker_category=category,
                    affected_net_or_module=affected,
                    evidence_source=evidence,
                    current_status=status,
                    why_blocks_complete_gds=why,
                    required_fix_stage=stage,
                    priority=priority,
                    recommended_fix=fix,
                    blocks_C1=False,
                    blocks_C2=c2,
                    blocks_C3=c3,
                    blocks_C4=c4,
                    blocks_C5=c5,
                    blocks_C6=c6,
                )
            )
            counter += 1

        for row in contract_connections:
            add(
                "CONTRACT_ROUTE",
                row.net_name,
                "outputs/openyield_routing_power_pin/current_supported_config/net_to_shape_map.json",
                row.routing_status,
                row.why_not_complete_gds,
                row.required_fix_stage,
                "P0" if row.route_group in {"BITLINE", "CONTROL"} else "P1",
                row.recommended_fix,
                True,
                False,
                True,
                False,
                True,
            )
        for row in approximate_geometry:
            category = "APPROXIMATE_POWER_GEOMETRY" if "POWER" in row.approximation_type else "APPROXIMATE_ROUTE"
            if "LARGE_RECTANGLE" in row.approximation_type or "BBOX_ONLY_ROUTE" in row.approximation_type:
                category = "PLACEHOLDER_VISUAL_GEOMETRY"
            add(
                category,
                row.net_name,
                "outputs/openyield_routing_power_pin/current_supported_config/net_to_shape_map.json;outputs/openyield_routing_power_pin/current_supported_config/openyield_routed_power_pin_sram.gds",
                row.approximation_type,
                row.why_approximate,
                row.required_fix_stage,
                "P0" if category in {"APPROXIMATE_ROUTE", "APPROXIMATE_POWER_GEOMETRY"} else "P1",
                row.recommended_fix,
                "POWER" not in row.approximation_type,
                "LARGE_RECTANGLE" in row.approximation_type or "BBOX_ONLY_ROUTE" in row.approximation_type,
                "POWER" not in row.approximation_type,
                "POWER" in row.approximation_type,
                True,
            )
        for row in contract_power:
            add(
                "CONTRACT_POWER_STITCH" if row.routing_status in POWER_CONTRACT_STATUSES else "APPROXIMATE_POWER_GEOMETRY",
                f"{row.net_name}:{row.target_instance}",
                "outputs/openyield_routing_power_pin/current_supported_config/power_routing_report.json",
                row.routing_status,
                row.why_not_complete_gds,
                row.required_fix_stage,
                "P0",
                row.recommended_fix,
                True,
                False,
                False,
                True,
                True,
            )
        for row in missing_pins:
            if row.current_pin_status == PIN_STATUS_GEOMETRY_BACKED:
                continue
            category = "MISSING_TOP_PIN_GEOMETRY" if row.blocks_wl_bl_control_power_or_top_pin == "TOP_PIN" else "MISSING_PIN_GEOMETRY"
            add(
                category,
                f"{row.module_name}:{row.pin_name}",
                f"outputs/openyield_module_gds/{row.module_name}/pins.json;outputs/openyield_module_gds/{row.module_name}",
                row.current_pin_status,
                "Pin metadata exists without localized geometry, or pin is absent from module metadata entirely.",
                row.required_fix_stage,
                "P0" if row.blocks_wl_bl_control_power_or_top_pin in {"WORDLINE", "BITLINE", "POWER"} else "P1",
                row.recommended_fix,
                True,
                False,
                True,
                row.blocks_wl_bl_control_power_or_top_pin == "POWER",
                True,
            )
        if payloads["final_topology_validation_report_json"].get("approximate_alignment_count", 0) > 0:
            add(
                "FLOORPLAN_NOT_SRAM_LIKE",
                "top_level_floorplan",
                "outputs/openyield_final_validation/current_supported_config/final_topology_validation_report.json",
                "APPROXIMATE_ALIGNMENT_PRESENT",
                "Prototype placement still relies on approximate region alignment, which contributes to the non-SRAM-like visual impression.",
                "C3",
                "P1",
                "Rebuild array/row/column/control floorplan from real macro access, channels, and abutment rules.",
                False,
                True,
                False,
                False,
                True,
            )
        if payloads["final_net_mapping_audit_json"].get("entries_missing_required_for_lvs_later") == []:
            add(
                "MISSING_LVS_READY_NET_MAPPING",
                "net_to_shape_map",
                "outputs/openyield_final_validation/current_supported_config/final_net_mapping_audit.json",
                "MAP_ONLY_NOT_EXTRACTION_READY",
                "Current mapping is an audit map and not an LVS-extracted connectivity proof.",
                "C6",
                "P1",
                "Preserve semantic net naming through extraction-ready geometry and compare against SRAM netlist after real routing.",
                False,
                False,
                False,
                False,
                True,
            )
        return blockers

    def _build_report(
        self,
        contract_connections: list[ContractConnectionEntry],
        approximate_geometry: list[ApproximateGeometryEntry],
        contract_power: list[ContractPowerEntry],
        missing_pins: list[MissingPinGeometryEntry],
        real_geometry: list[RealGeometryEntry],
        blockers: list[CompleteGdsBlocker],
        payloads: dict[str, Any],
        gds_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        route_audit = payloads["final_routing_completeness_audit_json"]
        power_audit = payloads["final_power_continuity_audit_json"]
        pin_audit = payloads["final_pin_export_audit_json"]
        net_map_audit = payloads["final_net_mapping_audit_json"]
        top_bbox = gds_analysis["top_bbox"]
        placeholder_shapes = [row for row in real_geometry if row.is_visual_placeholder]
        missing_non_geometry = [row for row in missing_pins if row.current_pin_status != PIN_STATUS_GEOMETRY_BACKED]
        missing_by_bucket = {
            bucket: sum(1 for row in missing_non_geometry if row.blocks_wl_bl_control_power_or_top_pin == bucket)
            for bucket in {"WORDLINE", "BITLINE", "CONTROL", "POWER", "TOP_PIN"}
        }
        contract_by_bucket = {
            bucket: sum(1 for row in contract_connections if _route_bucket(row.net_category, row.route_group) == bucket)
            for bucket in {"WORDLINE", "BITLINE", "CONTROL", "TOP_PIN"}
        }
        report = {
            "C0_complete_gds_gap_audit_available": True,
            "contract_connection_inventory_available": True,
            "approximate_geometry_inventory_available": True,
            "contract_power_inventory_available": True,
            "missing_pin_geometry_inventory_available": True,
            "real_geometry_inventory_available": True,
            "geometry_connection_gap_summary_available": True,
            "complete_gds_blocker_matrix_available": True,
            "gds_parse_success": True,
            "gds_top_cell_name": gds_analysis["top_cell_name"],
            "gds_cell_count": gds_analysis["cell_count"],
            "gds_recursive_instance_count": gds_analysis["recursive_instance_count"],
            "gds_top_bbox": top_bbox,
            "gds_layer_summary": gds_analysis["layer_summary"],
            "contract_pin_based_route_count": int(route_audit.get("contract_pin_based_route_count", sum(1 for row in contract_connections if row.routing_status in CONTRACT_ROUTE_STATUSES))),
            "approximate_geometry_route_count": int(route_audit.get("approximate_geometry_for_r4_count", sum(1 for row in contract_connections if row.routing_status in APPROXIMATE_ROUTE_STATUSES))),
            "contract_rail_based_stitch_count": int(power_audit.get("contract_rail_based_stitch_count", sum(1 for row in contract_power if row.routing_status in POWER_CONTRACT_STATUSES))),
            "approximate_power_geometry_count": int(power_audit.get("approximate_power_geometry_for_r4_count", sum(1 for row in contract_power if row.routing_status in POWER_APPROXIMATE_STATUSES))),
            "geometry_routed_count": int(route_audit.get("geometry_routed_for_r4_count", sum(1 for row in real_geometry if row.is_pin_to_pin_geometry))),
            "geometry_power_stitch_count": int(power_audit.get("geometry_power_stitch_for_r4_count", sum(1 for row in real_geometry if row.is_power_geometry and row.complete_gds_ready))),
            "contract_pin_entry_count": int(net_map_audit.get("contract_pin_entry_count", sum(1 for row in contract_connections if row.uses_contract_pin))),
            "geometry_backed_pin_entry_count": sum(1 for row in missing_pins if row.current_pin_status == PIN_STATUS_GEOMETRY_BACKED),
            "label_only_pin_entry_count": sum(1 for row in missing_pins if row.current_pin_status == PIN_STATUS_LABEL_ONLY),
            "missing_pin_entry_count": len(missing_non_geometry),
            "wordline_contract_route_count": contract_by_bucket["WORDLINE"],
            "bitline_contract_route_count": contract_by_bucket["BITLINE"],
            "control_contract_route_count": contract_by_bucket["CONTROL"],
            "top_io_contract_route_count": contract_by_bucket["TOP_PIN"],
            "power_contract_connection_count": len(contract_power),
            "wordline_missing_pin_count": missing_by_bucket["WORDLINE"],
            "bitline_missing_pin_count": missing_by_bucket["BITLINE"],
            "control_missing_pin_count": missing_by_bucket["CONTROL"],
            "power_missing_pin_count": missing_by_bucket["POWER"],
            "top_pin_missing_geometry_count": missing_by_bucket["TOP_PIN"],
            "large_placeholder_shape_count": len(gds_analysis["suspicious_shapes"]),
            "large_placeholder_shape_area_total": _round(sum(float(row["area"]) for row in gds_analysis["suspicious_shapes"])),
            "suspected_visual_placeholder_geometry_count": len(placeholder_shapes),
            "largest_shapes_by_area": gds_analysis["largest_shapes"],
            "shapes_without_any_net_to_shape_entry_count": len(gds_analysis.get("shapes_without_net_entry", [])),
            "shapes_without_any_net_to_shape_entry": gds_analysis.get("shapes_without_net_entry", []),
            "net_to_shape_entries_without_gds_shape_match_count": len(gds_analysis.get("entries_without_shape_match", [])),
            "net_to_shape_entries_without_gds_shape_match": gds_analysis.get("entries_without_shape_match", []),
            "complete_gds_blocker_count": len(blockers),
            "remaining_C0_blockers": [],
            "remaining_C0_blockers_count": 0,
            "can_claim_C0_gap_audit_completed_now": True,
            "can_claim_complete_gds_now": False,
            "can_enter_C1_physical_rule_extraction": True,
            "repo_git_commit": _git_commit(self.config.repo_root),
            "source_r5_report_json": str(self.config.r5_report_json),
        }
        return report

    def _write_outputs(
        self,
        report: dict[str, Any],
        contract_connections: list[ContractConnectionEntry],
        approximate_geometry: list[ApproximateGeometryEntry],
        contract_power: list[ContractPowerEntry],
        missing_pins: list[MissingPinGeometryEntry],
        real_geometry: list[RealGeometryEntry],
        blockers: list[CompleteGdsBlocker],
        gds_analysis: dict[str, Any],
    ) -> None:
        out_dir = self.config.out_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        contract_rows = [row.to_dict() for row in contract_connections]
        approximate_rows = [row.to_dict() for row in approximate_geometry]
        contract_power_rows = [row.to_dict() for row in contract_power]
        missing_rows = [row.to_dict() for row in missing_pins]
        real_rows = [row.to_dict() for row in real_geometry]
        blocker_rows = [row.to_dict() for row in blockers]

        _json_dump(out_dir / "complete_gds_gap_audit_report.json", report)
        _write_text(out_dir / "complete_gds_gap_audit_report.md", self._render_main_report_md(report))
        _write_csv(out_dir / "contract_connection_inventory.csv", CONTRACT_CONNECTION_COLUMNS, contract_rows)
        _write_text(out_dir / "contract_connection_inventory.md", "# Contract Connection Inventory\n\n" + _md_table(CONTRACT_CONNECTION_COLUMNS, contract_rows))
        _write_csv(out_dir / "approximate_geometry_inventory.csv", APPROXIMATE_GEOMETRY_COLUMNS, approximate_rows)
        _write_text(out_dir / "approximate_geometry_inventory.md", "# Approximate Geometry Inventory\n\n" + _md_table(APPROXIMATE_GEOMETRY_COLUMNS, approximate_rows))
        _write_csv(out_dir / "contract_power_inventory.csv", CONTRACT_POWER_COLUMNS, contract_power_rows)
        _write_text(out_dir / "contract_power_inventory.md", "# Contract Power Inventory\n\n" + _md_table(CONTRACT_POWER_COLUMNS, contract_power_rows))
        _write_csv(out_dir / "missing_pin_geometry_inventory.csv", MISSING_PIN_COLUMNS, missing_rows)
        _write_text(out_dir / "missing_pin_geometry_inventory.md", "# Missing Pin Geometry Inventory\n\n" + _md_table(MISSING_PIN_COLUMNS, missing_rows))
        _write_csv(out_dir / "real_geometry_inventory.csv", REAL_GEOMETRY_COLUMNS, real_rows)
        _write_text(out_dir / "real_geometry_inventory.md", "# Real Geometry Inventory\n\n" + _md_table(REAL_GEOMETRY_COLUMNS, real_rows))
        gap_summary = self._render_gap_summary_md(report, blockers, gds_analysis)
        _json_dump(
            out_dir / "geometry_connection_gap_summary.json",
            {
                "summary_markdown_path": str(out_dir / "geometry_connection_gap_summary.md"),
                "why_not_complete_gds": gap_summary,
            },
        )
        _write_text(out_dir / "geometry_connection_gap_summary.md", gap_summary)
        _write_csv(out_dir / "complete_gds_blocker_matrix.csv", BLOCKER_COLUMNS, blocker_rows)
        _write_text(out_dir / "complete_gds_blocker_matrix.md", "# Complete GDS Blocker Matrix\n\n" + _md_table(BLOCKER_COLUMNS, blocker_rows))

        _json_dump(self.config.out_json, report)
        _write_text(self.config.out_report, self._render_main_report_md(report))
        _write_csv(self.config.out_matrix_csv, BLOCKER_COLUMNS, blocker_rows)
        _write_text(self.config.out_matrix_md, "# OpenYield C0 Complete GDS Gap Matrix\n\n" + _md_table(BLOCKER_COLUMNS, blocker_rows))
        _write_text(self.config.repo_root / "docs/evidence/C0_complete_gds_gap_summary.md", gap_summary)

    def _render_main_report_md(self, report: dict[str, Any]) -> str:
        lines = [
            "# OpenYield C0 Complete GDS Gap Audit",
            "",
            "## Audit Gate",
            f"- C0_complete_gds_gap_audit_available: `{report['C0_complete_gds_gap_audit_available']}`",
            f"- can_claim_C0_gap_audit_completed_now: `{report['can_claim_C0_gap_audit_completed_now']}`",
            f"- can_claim_complete_gds_now: `{report['can_claim_complete_gds_now']}`",
            f"- can_enter_C1_physical_rule_extraction: `{report['can_enter_C1_physical_rule_extraction']}`",
            "",
            "## Key Counts",
            f"- contract_pin_based_route_count: `{report['contract_pin_based_route_count']}`",
            f"- approximate_geometry_route_count: `{report['approximate_geometry_route_count']}`",
            f"- contract_rail_based_stitch_count: `{report['contract_rail_based_stitch_count']}`",
            f"- approximate_power_geometry_count: `{report['approximate_power_geometry_count']}`",
            f"- geometry_routed_count: `{report['geometry_routed_count']}`",
            f"- geometry_power_stitch_count: `{report['geometry_power_stitch_count']}`",
            f"- missing_pin_entry_count: `{report['missing_pin_entry_count']}`",
            f"- complete_gds_blocker_count: `{report['complete_gds_blocker_count']}`",
            "",
            "## GDS Parse",
            f"- gds_parse_success: `{report['gds_parse_success']}`",
            f"- gds_top_cell_name: `{report['gds_top_cell_name']}`",
            f"- gds_cell_count: `{report['gds_cell_count']}`",
            f"- gds_recursive_instance_count: `{report['gds_recursive_instance_count']}`",
            f"- large_placeholder_shape_count: `{report['large_placeholder_shape_count']}`",
            f"- suspected_visual_placeholder_geometry_count: `{report['suspected_visual_placeholder_geometry_count']}`",
            "",
        ]
        return "\n".join(lines) + "\n"

    def _render_gap_summary_md(self, report: dict[str, Any], blockers: list[CompleteGdsBlocker], gds_analysis: dict[str, Any]) -> str:
        highest = blockers[:8]
        lines = [
            "# Geometry Connection Gap Summary",
            "",
            "## 1. Why current R5 GDS is not a complete SRAM GDS",
            f"- The top GDS still contains `{report['contract_pin_based_route_count']}` contract-pin-based signal routes, `{report['contract_rail_based_stitch_count']}` contract rail stitches, and `{report['approximate_power_geometry_count']}` approximate power straps.",
            f"- Only `{report['geometry_routed_count']}` entries are geometry-routed, while `{report['missing_pin_entry_count']}` referenced pins are not geometry-backed at the module boundary.",
            f"- Visual audit found `{report['large_placeholder_shape_count']}` suspicious large rectangles and `{report['suspected_visual_placeholder_geometry_count']}` geometry entries that behave like placeholder stripes/straps rather than exact access routing.",
            "",
            "## 2. Which connections are still contract-only",
            f"- Wordline contract routes: `{report['wordline_contract_route_count']}`.",
            f"- Bitline contract routes: `{report['bitline_contract_route_count']}`.",
            f"- Control contract routes: `{report['control_contract_route_count']}`.",
            f"- Top IO contract routes: `{report['top_io_contract_route_count']}`.",
            "",
            "## 3. Which connections are approximate-only",
            f"- Approximate route count from R5 audits: `{report['approximate_geometry_route_count']}`.",
            f"- Approximate power geometry count: `{report['approximate_power_geometry_count']}`.",
            f"- Placeholder bbox-only geometry detected in top-level rectangles, especially long WL/BL/rail stripes that dominate the visible macro silhouette.",
            "",
            "## 4. Which power connections are still contract / approximate",
            f"- Contract rail stitches remain on `{report['contract_rail_based_stitch_count']}` entries.",
            f"- Geometry power stitch count is only `{report['geometry_power_stitch_count']}`, so there is no evidence of real per-instance VDD/GND tap closure yet.",
            "",
            "## 5. Which pins still lack real geometry",
            f"- Wordline missing pin count: `{report['wordline_missing_pin_count']}`.",
            f"- Bitline missing pin count: `{report['bitline_missing_pin_count']}`.",
            f"- Control missing pin count: `{report['control_missing_pin_count']}`.",
            f"- Power missing pin count: `{report['power_missing_pin_count']}`.",
            f"- Top pin missing geometry count: `{report['top_pin_missing_geometry_count']}`.",
            "",
            "## 6. Why KLayout does not look like a real SRAM macro",
            "- The top cell adds long, simple rectangles for routing/power/pin proof over a referenced R3 structure, so the visible overlay looks like stripes, straps, and label-aligned blocks instead of dense access-aware routing.",
            "- The largest visible polygons are wide rails or long channels rather than detailed via ladders, jogs, and exact module landing shapes.",
            "",
            "## 7. What C1-C6 must add",
            "- C1: extract OpenRAM / SRAM baseline physical rules, legal layers, pitch, access, rail, and wrapper assumptions needed for real closure.",
            "- C2: replace contract or label-only module pins with real pin geometry and access metadata for WL / BL / BR / control / VDD / GND / top IO.",
            "- C3: rebuild array / row / column / control floorplan around actual access windows and routing channels so the macro shape becomes SRAM-like.",
            "- C4: replace bbox-only stripes with real WL / BL / BR / control / IO routing between extracted source/target geometries.",
            "- C5: replace contract rail stitching and approximate straps with explicit VDD/GND taps, continuity, and per-module geometry.",
            "- C6: run full GDS completeness verification, attempt DRC/LVS on the repaired geometry, and deliver evidence without upgrading signoff claims prematurely.",
            "",
            "## 8. Highest priority blockers",
        ]
        for blocker in highest:
            lines.append(f"- {blocker.blocker_id} `{blocker.blocker_category}` on `{blocker.affected_net_or_module}`: {blocker.why_blocks_complete_gds}")
        lines.extend(
            [
                "",
                "## GDS Visual Audit",
                f"- top_cell_name: `{gds_analysis['top_cell_name']}`",
                f"- cell_count: `{gds_analysis['cell_count']}`",
                f"- recursive_instance_count: `{gds_analysis['recursive_instance_count']}`",
                f"- shapes_without_any_net_to_shape_entry_count: `{report['shapes_without_any_net_to_shape_entry_count']}`",
                f"- net_to_shape_entries_without_gds_shape_match_count: `{report['net_to_shape_entries_without_gds_shape_match_count']}`",
            ]
        )
        return "\n".join(lines) + "\n"
