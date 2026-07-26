from __future__ import annotations

import csv
import json
import math
import re
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
ARRAY_MODULES = {"bitcell_array", "dummy_array", "replica_array"}
HARDMACRO_MODULES = {"column_mux", "precharge", "sense_amp", "wordline_driver", "write_driver"}
ROOT_CAUSE_PRIORITY = {
    "CELL_NAME_OR_HIERARCHY_IMPORT_ARTIFACT": "P0",
    "LAYER_MAP_OR_DRC_DECK_INTERPRETATION": "P1",
    "TOP_LEVEL_MODULE_SPACING": "P2",
    "TOP_LEVEL_ABUTMENT_BOUNDARY": "P2",
    "POWER_RAIL_STITCH": "P2",
    "CANDIDATE_GEOMETRY_INTERNAL": "P3",
    "MODULE_INTERNAL_HARDMACRO": "P3",
    "MODULE_WRAPPER_IMPORT": "P3",
    "ARRAY_ROW_SEAM": "P3",
    "ARRAY_COLUMN_SEAM": "P3",
    "CONTRACT_PIN_GEOMETRY_PLACEHOLDER": "P4",
    "ROUTING_HANDOFF_PLACEHOLDER": "P4",
    "UNKNOWN_REQUIRES_MANUAL_REVIEW": "P5",
}
RULE_LAYER_PREFIX = {
    "WELL": "well",
    "VT": "vtg",
    "POLY": "poly",
    "ACTIVE": "active",
    "SELECT": "active",
    "CONTACT": "cont",
    "METAL1": "metal1",
    "VIA1": "via1",
    "METAL2": "metal2",
    "METAL3": "metal3",
    "METAL4": "metal4",
}


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


def _bbox_from_points(coords: list[tuple[float, float]]) -> dict[str, float]:
    xs = [xy[0] for xy in coords]
    ys = [xy[1] for xy in coords]
    x0 = min(xs)
    y0 = min(ys)
    x1 = max(xs)
    y1 = max(ys)
    return {
        "x0": x0,
        "y0": y0,
        "x1": x1,
        "y1": y1,
        "width": max(0.0, x1 - x0),
        "height": max(0.0, y1 - y0),
    }


def _bbox_center(bbox: dict[str, float]) -> tuple[float, float]:
    return ((float(bbox["x0"]) + float(bbox["x1"])) / 2.0, (float(bbox["y0"]) + float(bbox["y1"])) / 2.0)


def _bbox_area(bbox: dict[str, float]) -> float:
    return max(0.0, float(bbox["width"])) * max(0.0, float(bbox["height"]))


def _bbox_intersects(a: dict[str, float], b: dict[str, float], tol: float = 0.0) -> bool:
    return not (
        float(a["x1"]) < float(b["x0"]) - tol
        or float(b["x1"]) < float(a["x0"]) - tol
        or float(a["y1"]) < float(b["y0"]) - tol
        or float(b["y1"]) < float(a["y0"]) - tol
    )


def _point_inside_bbox(point: tuple[float, float], bbox: dict[str, float], tol: float = 0.0) -> bool:
    x, y = point
    return (
        float(bbox["x0"]) - tol <= x <= float(bbox["x1"]) + tol
        and float(bbox["y0"]) - tol <= y <= float(bbox["y1"]) + tol
    )


def _distance_to_bbox(point: tuple[float, float], bbox: dict[str, float]) -> float:
    x, y = point
    dx = max(float(bbox["x0"]) - x, 0.0, x - float(bbox["x1"]))
    dy = max(float(bbox["y0"]) - y, 0.0, y - float(bbox["y1"]))
    return math.hypot(dx, dy)


def _distance_to_bbox_boundary(point: tuple[float, float], bbox: dict[str, float]) -> float:
    x, y = point
    if not _point_inside_bbox(point, bbox):
        return _distance_to_bbox(point, bbox)
    return min(
        abs(x - float(bbox["x0"])),
        abs(x - float(bbox["x1"])),
        abs(y - float(bbox["y0"])),
        abs(y - float(bbox["y1"])),
    )


def _normalize_module_reference(name: str, required_modules: set[str]) -> str | None:
    if name in required_modules:
        return name
    for module in required_modules:
        if name == f"{module}__{module}" or name.startswith(f"{module}__"):
            return module
    return None


def _parse_rule_name(raw: str) -> str:
    return str(raw).strip().strip("'").strip()


def _infer_rule_category(rule_name: str) -> str:
    if rule_name.startswith("GRID:"):
        return "GRID"
    if "." in rule_name:
        return rule_name.split(".", 1)[0]
    return rule_name


def _infer_layer(rule_name: str, message: str) -> str | None:
    grid_match = re.search(r"layer ([A-Za-z0-9_]+)", rule_name)
    if grid_match:
        return grid_match.group(1)
    grid_match = re.search(r"layer ([A-Za-z0-9_]+)", message)
    if grid_match:
        return grid_match.group(1)
    prefix = _infer_rule_category(rule_name)
    return RULE_LAYER_PREFIX.get(prefix)


def _extract_coords(text: str) -> list[tuple[float, float]]:
    return [(float(x), float(y)) for x, y in re.findall(r"\((-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)\)", text)]


@dataclass(frozen=True)
class DrcMarkerSource:
    source_file: str
    source_deck: str | None
    field_missing_reason: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DrcMarker:
    marker_id: str
    rule_name: str
    rule_category: str
    bbox: dict[str, float]
    x0: float
    y0: float
    x1: float
    y1: float
    width: float
    height: float
    layer: str | None
    message: str
    severity: str
    source: DrcMarkerSource
    raw_cell_name: str
    raw_value: str
    geometry_type: str
    module_hint: str | None = None


@dataclass(frozen=True)
class DrcMarkerCluster:
    cluster_id: str
    marker_count: int
    bbox: dict[str, float]
    dominant_rule: str
    dominant_layer: str | None
    nearest_modules: list[str]
    nearest_boundary_type: str
    classification_hint: str


@dataclass(frozen=True)
class DrcMarkerClassification:
    marker_id: str
    root_cause_category: str
    why_likely: str
    blocks_drc_clean: bool
    blocks_lvs_clean: bool
    recommended_fix_layer: str
    recommended_next_action: str


@dataclass(frozen=True)
class DrcTriageReport:
    summary: dict[str, Any]
    matrix_rows: list[dict[str, Any]]


class DrcMarkerParser:
    def __init__(self, lyrdb_path: Path) -> None:
        self.lyrdb_path = lyrdb_path

    def parse(self) -> tuple[list[DrcMarker], dict[str, str]]:
        root = ET.parse(self.lyrdb_path).getroot()
        source = DrcMarkerSource(
            source_file=str(self.lyrdb_path),
            source_deck=self._parse_source_deck(root.findtext("generator", "")),
            field_missing_reason={},
        )
        category_descriptions: dict[str, str] = {}
        categories = root.find("categories")
        if categories is not None:
            for category in categories.findall("category"):
                name = _parse_rule_name(category.findtext("name", ""))
                category_descriptions[name] = category.findtext("description", "").strip()
        required_modules = set(L3_REQUIRED_MODULES)
        markers: list[DrcMarker] = []
        items = root.find("items")
        if items is None:
            return markers, category_descriptions
        for index, item in enumerate(items.findall("item"), start=1):
            raw_rule_name = item.findtext("category", "")
            rule_name = _parse_rule_name(raw_rule_name)
            message = category_descriptions.get(rule_name, "")
            raw_cell_name = item.findtext("cell", "").strip()
            values = item.find("values")
            raw_value = ""
            geometry_type = "unknown"
            coords: list[tuple[float, float]] = []
            if values is not None:
                value_nodes = values.findall("value")
                if value_nodes:
                    raw_value = (value_nodes[0].text or "").strip()
                    geometry_type = raw_value.split(":", 1)[0].strip() if ":" in raw_value else "unknown"
                    coords = _extract_coords(raw_value)
            if not coords:
                coords = [(0.0, 0.0), (0.0, 0.0)]
            bbox = _bbox_from_points(coords)
            layer = _infer_layer(rule_name, message or raw_value)
            markers.append(
                DrcMarker(
                    marker_id=f"M{index:05d}",
                    rule_name=rule_name,
                    rule_category=_infer_rule_category(rule_name),
                    bbox=bbox,
                    x0=bbox["x0"],
                    y0=bbox["y0"],
                    x1=bbox["x1"],
                    y1=bbox["y1"],
                    width=bbox["width"],
                    height=bbox["height"],
                    layer=layer,
                    message=message,
                    severity="ERROR",
                    source=source,
                    raw_cell_name=raw_cell_name,
                    raw_value=raw_value,
                    geometry_type=geometry_type,
                    module_hint=_normalize_module_reference(raw_cell_name, required_modules),
                )
            )
        return markers, category_descriptions

    @staticmethod
    def _parse_source_deck(generator_text: str) -> str | None:
        match = re.search(r"script='([^']+)'", generator_text or "")
        if match:
            return match.group(1)
        return None


class DrcMarkerSpatialIndexer:
    def __init__(self, tile_size: float = 2.0) -> None:
        self.tile_size = tile_size

    def cluster(self, mappings: list[dict[str, Any]]) -> list[DrcMarkerCluster]:
        grouped: dict[tuple[int, int, str], list[dict[str, Any]]] = defaultdict(list)
        for row in mappings:
            bbox = row["bbox"]
            cx, cy = _bbox_center(bbox)
            key = (
                int(cx // self.tile_size),
                int(cy // self.tile_size),
                row["mapping_type"],
            )
            grouped[key].append(row)
        clusters: list[DrcMarkerCluster] = []
        for idx, rows in enumerate(sorted(grouped.values(), key=len, reverse=True), start=1):
            bbox = _bbox_from_points(
                [(r["bbox"]["x0"], r["bbox"]["y0"]) for r in rows] + [(r["bbox"]["x1"], r["bbox"]["y1"]) for r in rows]
            )
            rules = Counter(r["rule_name"] for r in rows)
            layers = Counter(r.get("layer") or "unknown" for r in rows)
            nearest_modules = sorted({r["mapped_module"] for r in rows if r.get("mapped_module")})
            boundary_counter = Counter(r["mapping_type"] for r in rows)
            clusters.append(
                DrcMarkerCluster(
                    cluster_id=f"C{idx:04d}",
                    marker_count=len(rows),
                    bbox=bbox,
                    dominant_rule=rules.most_common(1)[0][0],
                    dominant_layer=layers.most_common(1)[0][0],
                    nearest_modules=nearest_modules[:4],
                    nearest_boundary_type=boundary_counter.most_common(1)[0][0],
                    classification_hint=f"{boundary_counter.most_common(1)[0][0]} / {rules.most_common(1)[0][0]}",
                )
            )
        return clusters


class DrcMarkerModuleMapper:
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context
        self.required_modules = set(L3_REQUIRED_MODULES)
        self.top_bbox = context["top_level_floorplan"]["floorplan_bbox"]
        self.instances = context["module_placement"]["instances"]
        self.module_generation_status = context["candidate_geometry_risk_report"]["module_generation_status"]

    def map_markers(self, markers: list[DrcMarker]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for marker in markers:
            row = self._map_one(marker)
            rows.append(row)
        return rows

    def _map_one(self, marker: DrcMarker) -> dict[str, Any]:
        center = _bbox_center(marker.bbox)
        distance_to_top_edge = min(
            abs(center[0] - float(self.top_bbox["x0"])),
            abs(center[0] - float(self.top_bbox["x1"])),
            abs(center[1] - float(self.top_bbox["y0"])),
            abs(center[1] - float(self.top_bbox["y1"])),
        )
        threshold = 0.15
        containing: list[dict[str, Any]] = []
        nearby: list[tuple[float, dict[str, Any]]] = []
        for instance in self.instances:
            bbox = instance["bbox"]
            if _point_inside_bbox(center, bbox, tol=threshold):
                containing.append(instance)
            nearby.append((_distance_to_bbox(center, bbox), instance))
        nearby.sort(key=lambda item: item[0])
        module_hint = marker.module_hint
        chosen = None
        if module_hint:
            chosen = next((inst for inst in self.instances if inst["module_name"] == module_hint), None)
        if chosen is None and containing:
            if module_hint:
                chosen = next((inst for inst in containing if inst["module_name"] == module_hint), containing[0])
            else:
                chosen = containing[0]
        if chosen is None and nearby:
            chosen = nearby[0][1]
        mapping_type = "unknown"
        nearest_neighbor_module = nearby[1][1]["module_name"] if len(nearby) > 1 else None
        distance_to_boundary = None
        if chosen is not None:
            distance_to_boundary = _distance_to_bbox_boundary(center, chosen["bbox"])
            if _point_inside_bbox(center, chosen["bbox"], tol=threshold):
                if distance_to_boundary <= threshold:
                    mapping_type = "near_module_boundary"
                else:
                    mapping_type = "inside_module"
            else:
                if len(nearby) > 1 and nearby[0][0] <= threshold and nearby[1][0] <= threshold:
                    mapping_type = "between_modules"
                elif distance_to_top_edge <= threshold:
                    mapping_type = "top_level_edge"
                elif nearby[0][0] <= threshold * 2:
                    mapping_type = "near_module_boundary"
                else:
                    mapping_type = "outside_all_modules"
        if mapping_type in {"unknown", "outside_all_modules"} and distance_to_top_edge <= threshold:
            mapping_type = "top_level_edge"
        mapped_module = chosen["module_name"] if chosen else module_hint
        module_status = self.module_generation_status.get(mapped_module or "", "")
        is_candidate = bool(chosen and chosen.get("uses_candidate_geometry")) or ("CANDIDATE" in module_status)
        is_contract = bool(chosen and chosen.get("uses_contract_pins")) or ("CONTRACT" in module_status)
        is_hardmacro = mapped_module in HARDMACRO_MODULES
        is_array = mapped_module in ARRAY_MODULES
        return {
            "marker_id": marker.marker_id,
            "rule_name": marker.rule_name,
            "rule_category": marker.rule_category,
            "bbox": marker.bbox,
            "layer": marker.layer,
            "mapped_module": mapped_module,
            "mapped_instance": chosen["instance_name"] if chosen else None,
            "mapping_type": mapping_type,
            "distance_to_module_boundary": None if distance_to_boundary is None else round(float(distance_to_boundary), 6),
            "nearest_neighbor_module": nearest_neighbor_module,
            "is_candidate_geometry_module": is_candidate,
            "is_contract_pin_module": is_contract,
            "is_hardmacro_module": is_hardmacro,
            "is_array_module": is_array,
            "raw_cell_name": marker.raw_cell_name,
            "message": marker.message,
            "raw_value": marker.raw_value,
        }


class DrcMarkerRuleClassifier:
    def summarize(self, markers: list[DrcMarker]) -> dict[str, Any]:
        by_rule = Counter(marker.rule_name for marker in markers)
        by_layer = Counter(marker.layer or "unknown" for marker in markers)
        by_rule_layer = Counter(f"{marker.rule_name}::{marker.layer or 'unknown'}" for marker in markers)
        return {
            "total_marker_count": len(markers),
            "marker_count_by_rule": dict(sorted(by_rule.items())),
            "marker_count_by_layer": dict(sorted(by_layer.items())),
            "marker_count_by_rule_and_layer": dict(sorted(by_rule_layer.items())),
            "top_10_rules_by_count": [{"rule_name": name, "count": count} for name, count in by_rule.most_common(10)],
            "top_10_layers_by_count": [{"layer": name, "count": count} for name, count in by_layer.most_common(10)],
        }


class DrcMarkerRootCauseClassifier:
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context
        self.pin_modules = {
            module
            for module, row in context["pin_accessibility_audit"]["module_pin_status"].items()
            if row.get("uses_contract_pins")
        }
        self.routing_modules = {
            item["module_name"] for item in context["module_placement"]["instances"] if item.get("routing_handoff")
        }

    def classify(self, marker: DrcMarker, mapping: dict[str, Any]) -> DrcMarkerClassification:
        rule_name = marker.rule_name
        mapping_type = mapping["mapping_type"]
        module = mapping.get("mapped_module")
        is_candidate = mapping["is_candidate_geometry_module"]
        is_contract = mapping["is_contract_pin_module"] or module in self.pin_modules
        is_hardmacro = mapping["is_hardmacro_module"]
        is_array = mapping["is_array_module"]
        layer = (marker.layer or "").lower()
        rule_prefix = marker.rule_category

        if "GRID:" in rule_name and not is_candidate:
            return self._emit(
                marker,
                "LAYER_MAP_OR_DRC_DECK_INTERPRETATION",
                "Large off-grid marker families on imported macros/arrays point to source-library grid mismatch versus the FreePDK45 deck grid.",
                "L6/L7 DRC deck and imported source geometry review",
                "Separate deck-grid/systematic imported-geometry issues from true placement violations, then decide whether source snapping or deck exceptions are appropriate.",
            )
        if is_candidate and mapping_type in {"inside_module", "near_module_boundary"}:
            return self._emit(
                marker,
                "CANDIDATE_GEOMETRY_INTERNAL",
                "Marker falls inside a candidate-geometry module that is not yet signoff-proven.",
                "L3 module generator / candidate geometry",
                "Prioritize generator-level cleanup for the affected candidate module before top-level signoff work.",
            )
        if is_contract and mapping_type in {"near_module_boundary", "top_level_edge"}:
            return self._emit(
                marker,
                "CONTRACT_PIN_GEOMETRY_PLACEHOLDER",
                "Marker is near a module boundary that still relies on contract-pin exports rather than geometry-backed access proof.",
                "L3 pin export / L4 boundary pin realization",
                "Replace contract-pin placeholders with geometry-backed pin shapes or audited boundary access shapes.",
            )
        if mapping_type == "between_modules":
            if layer in {"metal1", "metal2", "via1", "cont"}:
                return self._emit(
                    marker,
                    "POWER_RAIL_STITCH",
                    "Marker sits between neighboring modules on routing/power layers where top-level rail drops or stitch geometry are expected.",
                    "L4/L7 top-level rail stitching",
                    "Review shared rail drop geometry and seam alignment for the neighboring modules.",
                )
            return self._emit(
                marker,
                "TOP_LEVEL_MODULE_SPACING",
                "Marker falls in the inter-module gap region and is more consistent with top-level spacing/keepout than a leaf internal issue.",
                "L4/L7 top-level placement and keepout planning",
                "Audit the reported gap and introduce spacing/keepout or seam-aware wrapper geometry.",
            )
        if mapping_type == "near_module_boundary":
            if module in self.routing_modules and layer in {"metal1", "metal2", "via1"}:
                return self._emit(
                    marker,
                    "ROUTING_HANDOFF_PLACEHOLDER",
                    "Marker is on routing layers near a module with unresolved routing handoff nets.",
                    "L4/L7 routing handoff realization",
                    "Convert placeholder routing handoff regions into explicit routed geometry or validated keepouts.",
                )
            return self._emit(
                marker,
                "TOP_LEVEL_ABUTMENT_BOUNDARY",
                "Marker is concentrated at the module perimeter where abutment/seam policy applies.",
                "L4/L7 abutment boundary repair",
                "Review seam-specific spacing, enclosure, and orientation assumptions at the module boundary.",
            )
        if is_array:
            if marker.bbox["width"] >= marker.bbox["height"]:
                return self._emit(
                    marker,
                    "ARRAY_ROW_SEAM",
                    "Marker is inside an array-generated module and its horizontal extent is consistent with row seam issues.",
                    "L3 array seam generation / L7 array repair",
                    "Check alternating-row seam geometry and row-to-row rail/active/poly interactions.",
                )
            return self._emit(
                marker,
                "ARRAY_COLUMN_SEAM",
                "Marker is inside an array-generated module and its vertical extent is consistent with column seam issues.",
                "L3 array seam generation / L7 array repair",
                "Check adjacent column pitch, contact/via alignment, and column-edge keepouts.",
            )
        if is_hardmacro:
            if "__" in marker.raw_cell_name and marker.raw_cell_name.count("__") >= 2:
                return self._emit(
                    marker,
                    "MODULE_WRAPPER_IMPORT",
                    "Marker originates in a wrapped imported hardmacro hierarchy and may reflect wrapper-to-source import interaction.",
                    "L3/L4 wrapper import path",
                    "Review wrapper namespace/import behavior and distinguish true macro DRC from wrapper artifacts.",
                )
            return self._emit(
                marker,
                "MODULE_INTERNAL_HARDMACRO",
                "Marker is inside a hardmacro-derived module rather than at a top-level seam.",
                "Imported hardmacro or macro-local cleanup",
                "Audit the underlying hardmacro geometry and wrapper assumptions before top-level closure.",
            )
        if "__" in marker.raw_cell_name and marker.raw_cell_name.count("__") >= 2 and rule_prefix in {"CONTACT", "METAL1", "METAL2"}:
            return self._emit(
                marker,
                "CELL_NAME_OR_HIERARCHY_IMPORT_ARTIFACT",
                "Deeply prefixed imported cell hierarchy suggests a remaining namespace/import artifact rather than a pure placement issue.",
                "L4 hierarchy import path",
                "Check whether imported leaf naming or wrapper redirection changed geometry context for this cell family.",
            )
        if mapping_type == "top_level_edge":
            return self._emit(
                marker,
                "TOP_LEVEL_ABUTMENT_BOUNDARY",
                "Marker is adjacent to the top-level outline and is best treated as a boundary/edge integration issue.",
                "L4 top-level outline and edge keepout handling",
                "Audit top-level outline spacing and edge-adjacent power/routing shapes.",
            )
        return self._emit(
            marker,
            "UNKNOWN_REQUIRES_MANUAL_REVIEW",
            "No stronger heuristic matched this marker.",
            "Manual review",
            "Inspect the marker directly in KLayout and refine the classifier if this becomes a recurring family.",
        )

    @staticmethod
    def _emit(
        marker: DrcMarker,
        category: str,
        why_likely: str,
        recommended_fix_layer: str,
        next_action: str,
    ) -> DrcMarkerClassification:
        return DrcMarkerClassification(
            marker_id=marker.marker_id,
            root_cause_category=category,
            why_likely=why_likely,
            blocks_drc_clean=True,
            blocks_lvs_clean=category
            in {
                "CANDIDATE_GEOMETRY_INTERNAL",
                "CONTRACT_PIN_GEOMETRY_PLACEHOLDER",
                "POWER_RAIL_STITCH",
                "TOP_LEVEL_ABUTMENT_BOUNDARY",
                "TOP_LEVEL_MODULE_SPACING",
            },
            recommended_fix_layer=recommended_fix_layer,
            recommended_next_action=next_action,
        )


class DrcMarkerTriageReporter:
    def __init__(self, context: dict[str, Any], out_dir: Path) -> None:
        self.context = context
        self.out_dir = out_dir

    def emit(
        self,
        markers: list[DrcMarker],
        category_descriptions: dict[str, str],
        rule_summary: dict[str, Any],
        mappings: list[dict[str, Any]],
        clusters: list[DrcMarkerCluster],
        classifications: list[DrcMarkerClassification],
    ) -> DrcTriageReport:
        raw_extract_payload = {
            "drc_marker_total_count": len(markers),
            "source_file": str(self.context["lyrdb_path"]),
            "source_deck": self.context["drc_smoke_report"].get("deck_path"),
            "markers": [self._marker_to_payload(marker, category_descriptions) for marker in markers],
        }
        _json_dump(self.out_dir / "drc_marker_raw_extract.json", raw_extract_payload)
        _json_dump(self.out_dir / "drc_marker_rule_summary.json", rule_summary)
        _json_dump(self.out_dir / "drc_marker_spatial_clusters.json", {"clusters": [asdict(cluster) for cluster in clusters]})
        _json_dump(self.out_dir / "drc_marker_module_mapping.json", {"markers": mappings})

        classification_by_id = {item.marker_id: item for item in classifications}
        classified_rows = []
        for mapping in mappings:
            cls = classification_by_id[mapping["marker_id"]]
            row = dict(mapping)
            row.update(asdict(cls))
            classified_rows.append(row)
        root_cause_payload, matrix_rows = self._build_root_cause_payload(classified_rows)
        _json_dump(self.out_dir / "drc_marker_root_cause_classification.json", root_cause_payload)
        samples_payload = self._build_representative_samples_payload(classified_rows)
        _json_dump(self.out_dir / "drc_marker_representative_samples.json", samples_payload)
        fix_priority_payload = self._build_fix_priority_payload(root_cause_payload["root_cause_categories"])
        _json_dump(self.out_dir / "drc_marker_fix_priority.json", fix_priority_payload)

        summary = self._build_summary(rule_summary, root_cause_payload)
        summary_path = self.out_dir / "drc_triage_summary.json"
        _json_dump(summary_path, summary)
        _write_text(self.out_dir / "drc_triage_summary.md", self._build_summary_markdown(summary, rule_summary, root_cause_payload))
        return DrcTriageReport(summary=summary, matrix_rows=matrix_rows)

    @staticmethod
    def _marker_to_payload(marker: DrcMarker, category_descriptions: dict[str, str]) -> dict[str, Any]:
        payload = asdict(marker)
        payload["category_description"] = category_descriptions.get(marker.rule_name, "")
        return payload

    def _build_root_cause_payload(self, rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[row["root_cause_category"]].append(row)
        total = max(1, len(rows))
        payload_rows = []
        matrix_rows = []
        for category, items in sorted(grouped.items(), key=lambda kv: len(kv[1]), reverse=True):
            rules = Counter(item["rule_name"] for item in items)
            layers = Counter((item.get("layer") or "unknown") for item in items)
            modules = Counter(item["mapped_module"] or "unknown" for item in items)
            regions = Counter(item["mapping_type"] for item in items)
            representative_ids = [item["marker_id"] for item in items[:10]]
            why_likely = items[0]["why_likely"]
            next_action = items[0]["recommended_next_action"]
            fix_layer = items[0]["recommended_fix_layer"]
            percentage = len(items) / total
            row = {
                "root_cause_category": category,
                "marker_count": len(items),
                "percentage": round(percentage, 6),
                "affected_rules": [name for name, _ in rules.most_common(10)],
                "affected_layers": [name for name, _ in layers.most_common(10)],
                "affected_modules": [name for name, _ in modules.most_common(10)],
                "representative_marker_ids": representative_ids,
                "why_likely": why_likely,
                "blocks_drc_clean": True,
                "blocks_lvs_clean": any(item["blocks_lvs_clean"] for item in items),
                "recommended_fix_layer": fix_layer,
                "recommended_next_action": next_action,
            }
            payload_rows.append(row)
            matrix_rows.append(
                {
                    "root_cause_category": category,
                    "marker_count": len(items),
                    "percentage": round(percentage, 6),
                    "dominant_rules": "; ".join(name for name, _ in rules.most_common(5)),
                    "dominant_layers": "; ".join(name for name, _ in layers.most_common(5)),
                    "affected_modules": "; ".join(name for name, _ in modules.most_common(8)),
                    "affected_regions": "; ".join(name for name, _ in regions.most_common(5)),
                    "is_systematic": len(items) >= 20,
                    "blocks_drc_clean": True,
                    "blocks_lvs_clean": any(item["blocks_lvs_clean"] for item in items),
                    "blocks_timing_closure": category
                    in {
                        "CANDIDATE_GEOMETRY_INTERNAL",
                        "CONTRACT_PIN_GEOMETRY_PLACEHOLDER",
                        "TOP_LEVEL_MODULE_SPACING",
                        "TOP_LEVEL_ABUTMENT_BOUNDARY",
                        "POWER_RAIL_STITCH",
                    },
                    "recommended_fix_layer": fix_layer,
                    "recommended_fix_files": self._guess_fix_files(category, items),
                    "recommended_next_action": next_action,
                    "priority": ROOT_CAUSE_PRIORITY.get(category, "P5"),
                    "evidence_files": "; ".join(
                        [
                            str(self.out_dir / "drc_marker_root_cause_classification.json"),
                            str(self.out_dir / "drc_marker_module_mapping.json"),
                            str(self.out_dir / "drc_marker_rule_summary.json"),
                        ]
                    ),
                }
            )
        payload = {
            "root_cause_categories": payload_rows,
        }
        return payload, matrix_rows

    def _build_representative_samples_payload(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[row["root_cause_category"]].append(row)
        categories = []
        for category, items in sorted(grouped.items(), key=lambda kv: len(kv[1]), reverse=True):
            samples = []
            for item in sorted(items, key=lambda row: (_bbox_area(row["bbox"]), row["marker_id"]), reverse=True)[:5]:
                samples.append(
                    {
                        "marker_id": item["marker_id"],
                        "rule_name": item["rule_name"],
                        "layer": item.get("layer"),
                        "bbox": item["bbox"],
                        "mapped_module": item.get("mapped_module"),
                        "nearby_modules": [name for name in [item.get("mapped_module"), item.get("nearest_neighbor_module")] if name],
                        "root_cause_category": category,
                        "why_selected": "Largest-area or earliest representative marker in this root-cause family.",
                        "suggested_visual_check": f"Inspect {item['mapping_type']} geometry around {item.get('mapped_instance') or item.get('mapped_module') or 'unknown'} in KLayout.",
                    }
                )
            categories.append({"root_cause_category": category, "samples": samples})
        return {"representative_samples": categories}

    def _build_fix_priority_payload(self, root_cause_rows: list[dict[str, Any]]) -> dict[str, Any]:
        items = []
        for row in root_cause_rows:
            category = row["root_cause_category"]
            items.append(
                {
                    "priority": ROOT_CAUSE_PRIORITY.get(category, "P5"),
                    "root_cause_category": category,
                    "marker_count": row["marker_count"],
                    "affected_modules": row["affected_modules"],
                    "expected_fix_location": row["recommended_fix_layer"],
                    "expected_fix_files": self._guess_fix_files(category, row["affected_modules"]),
                    "suggested_fix_strategy": row["recommended_next_action"],
                    "risk": "High DRC signoff risk until this category is retired.",
                    "whether_to_fix_in_L7": True,
                }
            )
        items.sort(key=lambda item: (item["priority"], -item["marker_count"], item["root_cause_category"]))
        return {"fix_priority": items}

    def _build_summary(self, rule_summary: dict[str, Any], root_cause_payload: dict[str, Any]) -> dict[str, Any]:
        total = int(rule_summary["total_marker_count"])
        root_rows = root_cause_payload["root_cause_categories"]
        classified = sum(int(row["marker_count"]) for row in root_rows if row["root_cause_category"] != "UNKNOWN_REQUIRES_MANUAL_REVIEW")
        unclassified = total - classified
        coverage = 0.0 if total == 0 else classified / total
        top_rule = rule_summary["top_10_rules_by_count"][0] if rule_summary["top_10_rules_by_count"] else {"rule_name": None, "count": 0}
        top_root = root_rows[0] if root_rows else {"root_cause_category": None, "marker_count": 0}
        blockers = []
        if total <= 0:
            blockers.append("No DRC markers were extracted from the L5 smoke output.")
        if coverage < 0.90:
            blockers.append("Marker root-cause classification coverage is below 90%.")
        summary = {
            "L6_drc_marker_triage_available": True,
            "drc_marker_raw_extract_available": True,
            "drc_marker_rule_summary_available": True,
            "drc_marker_spatial_clusters_available": True,
            "drc_marker_module_mapping_available": True,
            "drc_marker_root_cause_classification_available": True,
            "drc_marker_representative_samples_available": True,
            "drc_marker_fix_priority_available": True,
            "drc_triage_matrix_available": True,
            "drc_marker_total_count": total,
            "drc_marker_classified_count": classified,
            "drc_marker_unclassified_count": unclassified,
            "drc_marker_classification_coverage": round(coverage, 6),
            "top_marker_rule": top_rule["rule_name"],
            "top_marker_rule_count": top_rule["count"],
            "top_root_cause_category": top_root["root_cause_category"],
            "top_root_cause_marker_count": top_root["marker_count"],
            "remaining_L6_triage_blockers": blockers,
            "remaining_L6_triage_blockers_count": len(blockers),
            "can_claim_L6_drc_triage_completed_now": len(blockers) == 0,
            "can_enter_L7_drc_repair_planning": len(blockers) == 0,
            "can_claim_drc_clean_now": False,
            "can_claim_lvs_clean_now": False,
            "can_claim_timing_closure_now": False,
            "can_claim_validated_full_openyield_gds_now": False,
        }
        return summary

    def _build_summary_markdown(self, summary: dict[str, Any], rule_summary: dict[str, Any], root_cause_payload: dict[str, Any]) -> str:
        lines = [
            "# OpenYield L6 DRC Marker Triage Summary",
            "",
            f"- drc_marker_total_count: `{summary['drc_marker_total_count']}`",
            f"- drc_marker_classified_count: `{summary['drc_marker_classified_count']}`",
            f"- drc_marker_unclassified_count: `{summary['drc_marker_unclassified_count']}`",
            f"- drc_marker_classification_coverage: `{summary['drc_marker_classification_coverage']}`",
            f"- top_marker_rule: `{summary['top_marker_rule']}`",
            f"- top_marker_rule_count: `{summary['top_marker_rule_count']}`",
            f"- top_root_cause_category: `{summary['top_root_cause_category']}`",
            f"- top_root_cause_marker_count: `{summary['top_root_cause_marker_count']}`",
            "",
            "## Top Rules",
            "",
        ]
        for row in rule_summary["top_10_rules_by_count"]:
            lines.append(f"- `{row['rule_name']}`: `{row['count']}`")
        lines.extend(["", "## Root Causes", ""])
        for row in root_cause_payload["root_cause_categories"][:10]:
            lines.append(
                f"- `{row['root_cause_category']}`: `{row['marker_count']}` markers, modules=`{', '.join(row['affected_modules'][:5])}`"
            )
        lines.extend(
            [
                "",
                "## Gates",
                "",
                f"- can_claim_L6_drc_triage_completed_now: `{summary['can_claim_L6_drc_triage_completed_now']}`",
                f"- can_enter_L7_drc_repair_planning: `{summary['can_enter_L7_drc_repair_planning']}`",
                f"- can_claim_drc_clean_now: `{summary['can_claim_drc_clean_now']}`",
                f"- can_claim_lvs_clean_now: `{summary['can_claim_lvs_clean_now']}`",
                f"- can_claim_timing_closure_now: `{summary['can_claim_timing_closure_now']}`",
                f"- can_claim_validated_full_openyield_gds_now: `{summary['can_claim_validated_full_openyield_gds_now']}`",
            ]
        )
        return "\n".join(lines) + "\n"

    def _guess_fix_files(self, category: str, items: list[Any]) -> str:
        mapping = {
            "CANDIDATE_GEOMETRY_INTERNAL": "sram_layoutgen/openyield_adapter/module_gds_generators.py",
            "CONTRACT_PIN_GEOMETRY_PLACEHOLDER": "outputs/openyield_module_gds/<module>/pins.json; sram_layoutgen/openyield_adapter/module_gds_generators.py",
            "MODULE_INTERNAL_HARDMACRO": "technology/freepdk45/gds_lib/*.gds; outputs/openyield_module_gds/<module>/generator_manifest.json",
            "MODULE_WRAPPER_IMPORT": "sram_layoutgen/openyield_adapter/gds_hierarchy_export.py; sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "TOP_LEVEL_MODULE_SPACING": "sram_layoutgen/openyield_adapter/top_level_assembly.py; outputs/openyield_top_level_assembly/current_supported_config/module_placement.json",
            "TOP_LEVEL_ABUTMENT_BOUNDARY": "sram_layoutgen/openyield_adapter/top_level_assembly.py; technology/freepdk45/openyield_L2_placement_abutment_rule_library.json",
            "POWER_RAIL_STITCH": "outputs/openyield_top_level_assembly/current_supported_config/top_level_rail_stitch_plan.json; sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "ROUTING_HANDOFF_PLACEHOLDER": "outputs/openyield_top_level_assembly/current_supported_config/top_level_routing_handoff.json; sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "ARRAY_ROW_SEAM": "sram_layoutgen/openyield_adapter/module_gds_generators.py",
            "ARRAY_COLUMN_SEAM": "sram_layoutgen/openyield_adapter/module_gds_generators.py",
            "CELL_NAME_OR_HIERARCHY_IMPORT_ARTIFACT": "sram_layoutgen/openyield_adapter/gds_hierarchy_export.py; sram_layoutgen/openyield_adapter/top_level_assembly.py",
            "LAYER_MAP_OR_DRC_DECK_INTERPRETATION": "technology/freepdk45/tech/freepdk45.lydrc; technology/freepdk45/gds_lib/*.gds",
        }
        return mapping.get(category, "Manual review")


class OpenYieldDrcMarkerTriage:
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context

    def run(self) -> DrcTriageReport:
        parser = DrcMarkerParser(self.context["lyrdb_path"])
        markers, category_descriptions = parser.parse()
        rule_summary = DrcMarkerRuleClassifier().summarize(markers)
        mapper = DrcMarkerModuleMapper(self.context)
        mappings = mapper.map_markers(markers)
        clusters = DrcMarkerSpatialIndexer().cluster(mappings)
        classifier = DrcMarkerRootCauseClassifier(self.context)
        classifications = []
        marker_lookup = {marker.marker_id: marker for marker in markers}
        for mapping in mappings:
            classifications.append(classifier.classify(marker_lookup[mapping["marker_id"]], mapping))
        reporter = DrcMarkerTriageReporter(self.context, self.context["out_dir"])
        return reporter.emit(markers, category_descriptions, rule_summary, mappings, clusters, classifications)


def emit_triage_reports(
    report: DrcTriageReport,
    *,
    out_matrix_csv: Path,
    out_matrix_md: Path,
    out_json: Path,
    out_report: Path,
    evidence_gap_summary: Path,
    evidence_timeline: Path,
    milestone_summary: Path,
) -> None:
    _json_dump(out_json, report.summary | {"matrix_rows": report.matrix_rows})
    _write_text(out_report, _build_report_markdown(report.summary, report.matrix_rows))
    _write_csv(
        out_matrix_csv,
        [
            "root_cause_category",
            "marker_count",
            "percentage",
            "dominant_rules",
            "dominant_layers",
            "affected_modules",
            "affected_regions",
            "is_systematic",
            "blocks_drc_clean",
            "blocks_lvs_clean",
            "blocks_timing_closure",
            "recommended_fix_layer",
            "recommended_fix_files",
            "recommended_next_action",
            "priority",
            "evidence_files",
        ],
        report.matrix_rows,
    )
    _write_text(out_matrix_md, _build_matrix_markdown(report.matrix_rows))
    _write_text(evidence_gap_summary, _build_gap_summary_markdown(report.summary, report.matrix_rows))
    timeline_line = (
        f"- `2026-07-03`: Completed OpenYield L6 DRC marker triage first round; "
        f"marker_count=`{report.summary['drc_marker_total_count']}`, "
        f"classification_coverage=`{report.summary['drc_marker_classification_coverage']}`, "
        f"top_root_cause=`{report.summary['top_root_cause_category']}`, "
        f"`can_claim_L6_drc_triage_completed_now={report.summary['can_claim_L6_drc_triage_completed_now']}` while all DRC/LVS/timing/full-GDS claims remain false."
    )
    _append_unique_line(evidence_timeline, timeline_line)
    milestone_line = (
        "- L6 first round: integrated KLayout DRC markers are now extracted, summarized, spatially clustered, "
        "mapped onto modules/boundaries, classified into root-cause families, and prioritized for L7 repair planning; "
        f"`can_claim_L6_drc_triage_completed_now={report.summary['can_claim_L6_drc_triage_completed_now']}` while "
        "`can_claim_drc_clean_now=False`, `can_claim_lvs_clean_now=False`, "
        "`can_claim_timing_closure_now=False`, and `can_claim_validated_full_openyield_gds_now=False`."
    )
    _append_unique_line(milestone_summary, milestone_line)


def _append_unique_line(path: Path, line: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if line in existing:
        return
    text = existing.rstrip() + "\n" + line + "\n"
    _write_text(path, text)


def _build_report_markdown(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# OpenYield L6 DRC Marker Triage Report",
        "",
        f"- drc_marker_total_count: `{summary['drc_marker_total_count']}`",
        f"- drc_marker_classified_count: `{summary['drc_marker_classified_count']}`",
        f"- drc_marker_unclassified_count: `{summary['drc_marker_unclassified_count']}`",
        f"- drc_marker_classification_coverage: `{summary['drc_marker_classification_coverage']}`",
        f"- top_marker_rule: `{summary['top_marker_rule']}`",
        f"- top_root_cause_category: `{summary['top_root_cause_category']}`",
        "",
        "## Root Cause Matrix",
        "",
    ]
    for row in rows:
        lines.append(
            f"- `{row['root_cause_category']}`: count=`{row['marker_count']}`, priority=`{row['priority']}`, modules=`{row['affected_modules']}`"
        )
    lines.extend(
        [
            "",
            "## Gates",
            "",
            f"- can_claim_L6_drc_triage_completed_now: `{summary['can_claim_L6_drc_triage_completed_now']}`",
            f"- can_enter_L7_drc_repair_planning: `{summary['can_enter_L7_drc_repair_planning']}`",
            f"- can_claim_drc_clean_now: `{summary['can_claim_drc_clean_now']}`",
            f"- can_claim_lvs_clean_now: `{summary['can_claim_lvs_clean_now']}`",
            f"- can_claim_timing_closure_now: `{summary['can_claim_timing_closure_now']}`",
            f"- can_claim_validated_full_openyield_gds_now: `{summary['can_claim_validated_full_openyield_gds_now']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def _build_matrix_markdown(rows: list[dict[str, Any]]) -> str:
    headers = [
        "root_cause_category",
        "marker_count",
        "percentage",
        "priority",
        "dominant_rules",
        "affected_modules",
        "recommended_fix_layer",
    ]
    lines = [
        "# OpenYield L6 DRC Marker Triage Matrix",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["root_cause_category"]),
                    str(row["marker_count"]),
                    str(row["percentage"]),
                    str(row["priority"]),
                    str(row["dominant_rules"]),
                    str(row["affected_modules"]),
                    str(row["recommended_fix_layer"]),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _build_gap_summary_markdown(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    top_rows = rows[:5]
    affected_modules = []
    for row in top_rows:
        for module in str(row["affected_modules"]).split(";"):
            module = module.strip()
            if module and module not in affected_modules:
                affected_modules.append(module)
    top_priority = min(rows, key=lambda row: (row["priority"], -int(row["marker_count"]))) if rows else None
    lines = [
        "# L6 DRC Marker Triage Gap Summary",
        "",
        f"1. 当前 DRC marker 总数：`{summary['drc_marker_total_count']}`。",
        "2. DRC marker 解析方式：直接解析 KLayout `.lyrdb` XML，提取 category/cell/value 几何文本并还原 bbox。",
        f"3. marker rule 分布：最高规则为 `{summary['top_marker_rule']}`，数量 `{summary['top_marker_rule_count']}`。",
        f"4. marker 空间分布：已完成 module/boundary/tile 级聚类，主导 root cause 为 `{summary['top_root_cause_category']}`。",
        f"5. marker 映射模块：主要集中在 `{', '.join(affected_modules[:10])}`。",
        f"6. 主要 root cause 分类：`{', '.join(row['root_cause_category'] for row in top_rows)}`。",
        f"7. classification coverage：`{summary['drc_marker_classification_coverage']}`。",
        f"8. 最高优先级修复对象：`{top_priority['root_cause_category']}`，优先级 `{top_priority['priority']}`。" if top_priority else "8. 最高优先级修复对象：无。",
        "9. 当前仍不能 claim DRC clean，因为 marker 总数仍然很高，且系统性 root-cause 族尚未消除。",
        f"10. 是否可以进入 L7 DRC repair planning：`{summary['can_enter_L7_drc_repair_planning']}`。",
        "",
    ]
    return "\n".join(lines)
