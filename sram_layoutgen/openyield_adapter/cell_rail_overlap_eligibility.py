from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.stdcell import generated_cell_pins
from sram_layoutgen.tech import Tech


MANUAL_OBJECT_TO_CELL = {
    "bitcell_array": "cell_1rw",
    "dummy_array": "dummy_cell_1rw",
    "replica_array": "replica_cell_1rw",
    "wordline_driver": "gen_wl_driver",
    "column_mux": "gen_col_mux_vdd_labeled",
}

MANUAL_GDS_PATHS = {
    "gen_col_mux_vdd_labeled": "technology/freepdk45/gds_lib/openyield_repaired/gen_col_mux_vdd_labeled.gds",
}

MANUAL_CELLS = {
    "gen_inv",
    "gen_nand2",
    "gen_delay_inv",
    "gen_precharge",
    "gen_wl_driver",
    "gen_col_mux",
    "gen_col_mux_vdd_labeled",
    "sense_amp",
    "write_driver",
    "dff",
    "cell_1rw",
    "dummy_cell_1rw",
    "replica_cell_1rw",
    "bitcell_array",
    "dummy_array",
    "replica_array",
    "wordline_driver",
    "column_mux",
}

STORAGE_NAMES = {"cell_1rw", "dummy_cell_1rw", "replica_cell_1rw", "bitcell_array", "dummy_array", "replica_array"}
DFF_NAMES = {"dff", "DFF_ROW", "ADDR_DFF_ROW", "DATA_DFF_ROW"}
ALLOWED_POWER_ONLY_LAYERS = {1, 4, 5, 11}


@dataclass(frozen=True)
class RailOverlapEligibility:
    cell_name: str
    resolved_cell_name: str | None
    gds_path: str | None
    bbox: dict[str, float] | None
    height: float | None
    width: float | None
    vdd_label_found: bool
    gnd_label_found: bool
    vdd_rail_bbox: dict[str, float] | None
    gnd_rail_bbox: dict[str, float] | None
    vdd_rail_side: str | None
    gnd_rail_side: str | None
    rail_layer: int | None
    top_rail_net: str | None
    bottom_rail_net: str | None
    supports_r0_mx_pairing: bool
    candidate_overlap_depth_um: float
    max_safe_overlap_depth_um: float
    overlap_eligible: bool
    eligibility_class: str
    blocked_reason: str | None
    recommended_packing_policy: str
    edge_touch_only: bool
    unusual_power_related_shapes: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["unusual_power_related_shapes"] = list(self.unusual_power_related_shapes)
        return data


@dataclass(frozen=True)
class _RailShape:
    layer: int
    datatype: int
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def center_y(self) -> float:
        return (self.y0 + self.y1) / 2.0

    def to_bbox(self) -> dict[str, float]:
        return {"x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1}


@dataclass(frozen=True)
class _OverlapAnalysis:
    top_clearance_below: float | None
    bottom_clearance_above: float | None
    candidate_overlap_depth_um: float
    max_safe_overlap_depth_um: float
    blocked_reason: str | None
    unusual_power_related_shapes: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class _ResolvedCell:
    cell_name: str
    resolved_cell_name: str | None
    gds_path: Path | None
    width: float | None
    height: float | None
    bbox: dict[str, float] | None
    bbox_x0: float | None
    bbox_y0: float | None
    bbox_x1: float | None
    bbox_y1: float | None


CSV_FIELDS = [
    "cell_name",
    "resolved_cell_name",
    "gds_path",
    "bbox",
    "height",
    "width",
    "vdd_label_found",
    "gnd_label_found",
    "vdd_rail_bbox",
    "gnd_rail_bbox",
    "vdd_rail_side",
    "gnd_rail_side",
    "rail_layer",
    "top_rail_net",
    "bottom_rail_net",
    "supports_r0_mx_pairing",
    "candidate_overlap_depth_um",
    "max_safe_overlap_depth_um",
    "overlap_eligible",
    "eligibility_class",
    "blocked_reason",
    "recommended_packing_policy",
]


def _repo_root(repo_root: str | Path) -> Path:
    return Path(repo_root).resolve()


def _load_tech(repo_root: str | Path) -> Tech:
    return Tech.freepdk45(_repo_root(repo_root))


def _read_module_coverage_cells(repo_root: Path) -> set[str]:
    names: set[str] = set()
    for rel in [
        "outputs/layout_prototype/hybrid_openyield/module_coverage.json",
        "outputs/layout_prototype/hybrid_openyield_rail_abutted/module_coverage.json",
    ]:
        path = repo_root / rel
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload:
            name = str(row.get("module_or_object") or "")
            if name:
                names.add(name)
    return names


def _read_mapping_cells(repo_root: Path) -> set[str]:
    names: set[str] = set()
    for rel in [
        "docs/mapping/openyield_control_path_candidate_contracts.csv",
        "docs/mapping/openyield_control_timing_mapping.csv",
    ]:
        path = repo_root / rel
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                for key in ("control_object", "openyield_object", "local_timing_object"):
                    value = str(row.get(key) or "").strip()
                    if value:
                        names.add(value)
    return names


def discover_candidate_cells(repo_root: str | Path) -> list[str]:
    root = _repo_root(repo_root)
    tech = _load_tech(root)
    names = set(MANUAL_CELLS)
    names.update(tech.cells.keys())
    names.update(_read_module_coverage_cells(root))
    names.update(_read_mapping_cells(root))
    names.update(MANUAL_OBJECT_TO_CELL.keys())
    names.update(MANUAL_OBJECT_TO_CELL.values())
    return sorted(names)


def _resolve_cell(repo_root: Path, tech: Tech, cell_name: str) -> _ResolvedCell:
    mapped = MANUAL_OBJECT_TO_CELL.get(cell_name, cell_name)
    if mapped in tech.cells:
        cell = tech.cell(mapped)
        gds_path = Path(str(cell.gds_path)).resolve() if cell.gds_path else None
        if gds_path is None and mapped in MANUAL_GDS_PATHS:
            gds_path = (repo_root / MANUAL_GDS_PATHS[mapped]).resolve()
        bbox = {
            "x0": float(cell.bbox_x0),
            "y0": float(cell.bbox_y0),
            "x1": float(cell.bbox_x1),
            "y1": float(cell.bbox_y1),
        }
        return _ResolvedCell(cell_name, mapped, gds_path, float(cell.width), float(cell.height), bbox, float(cell.bbox_x0), float(cell.bbox_y0), float(cell.bbox_x1), float(cell.bbox_y1))
    if mapped in MANUAL_GDS_PATHS:
        gds_path = (repo_root / MANUAL_GDS_PATHS[mapped]).resolve()
        bbox = None
        width = None
        height = None
        if gds_path.exists():
            lib = gdstk.read_gds(gds_path)
            top = lib.top_level()[0]
            bb = top.bounding_box()
            if bb is not None:
                bbox = {"x0": float(bb[0][0]), "y0": float(bb[0][1]), "x1": float(bb[1][0]), "y1": float(bb[1][1])}
                width = bbox["x1"] - bbox["x0"]
                height = bbox["y1"] - bbox["y0"]
        return _ResolvedCell(cell_name, mapped, gds_path, width, height, bbox, bbox["x0"] if bbox else None, bbox["y0"] if bbox else None, bbox["x1"] if bbox else None, bbox["y1"] if bbox else None)
    return _ResolvedCell(cell_name, mapped if mapped != cell_name else None, None, None, None, None, None, None, None, None)


def _generated_pin_y(cell_name: str, width: float, height: float, net: str) -> float | None:
    rect = gdstk.rectangle((0, 0), (width, height))
    del rect
    pins = generated_cell_pins(cell_name, type("RectLike", (), {"x0": 0.0, "y0": 0.0, "x1": width, "y1": height})(), "R0")
    matches = [float(pin["y"]) for pin in pins if str(pin["name"]) == net]
    if not matches:
        return None
    return sum(matches) / len(matches)


def _candidate_horizontal_rails(top: gdstk.Cell) -> tuple[_RailShape, ...]:
    bbox = top.bounding_box()
    if bbox is None:
        return ()
    (x0, y0), (x1, y1) = bbox
    cell_w = float(x1) - float(x0)
    cell_h = float(y1) - float(y0)
    width_threshold = max(0.25, cell_w * 0.70)
    height_threshold = max(0.05, cell_h * 0.12)
    edge_tol = max(0.05, cell_h * 0.08)
    out: list[_RailShape] = []
    for polygon in top.polygons:
        pb = polygon.bounding_box()
        if pb is None:
            continue
        (px0, py0), (px1, py1) = pb
        width = float(px1) - float(px0)
        height = float(py1) - float(py0)
        if width < width_threshold or height > height_threshold:
            continue
        near_bottom = abs(float(py0) - float(y0)) <= edge_tol or abs(float(py1) - float(y0)) <= edge_tol
        near_top = abs(float(py0) - float(y1)) <= edge_tol or abs(float(py1) - float(y1)) <= edge_tol
        if near_bottom or near_top:
            out.append(_RailShape(int(polygon.layer), int(polygon.datatype), float(px0), float(py0), float(px1), float(py1)))
    dedup: dict[tuple[int, int, float, float, float, float], _RailShape] = {}
    for item in out:
        key = (item.layer, item.datatype, round(item.x0, 6), round(item.y0, 6), round(item.x1, 6), round(item.y1, 6))
        dedup[key] = item
    return tuple(sorted(dedup.values(), key=lambda item: (item.y0, item.y1, item.x0, item.x1, item.layer)))


def _pick_power_rails(cell_name: str, top: gdstk.Cell, width: float, height: float) -> tuple[_RailShape | None, _RailShape | None, bool, bool, str | None]:
    rails = _candidate_horizontal_rails(top)
    if len(rails) < 2:
        return None, None, False, False, "missing_candidate_horizontal_rails"
    bottom = min(rails, key=lambda item: item.center_y)
    upper = max(rails, key=lambda item: item.center_y)
    label_y: dict[str, float] = {str(label.text).strip().lower(): float(label.origin[1]) for label in top.labels if str(label.text).strip().lower() in {"vdd", "gnd"}}
    vdd_label_found = "vdd" in label_y
    gnd_label_found = "gnd" in label_y
    if not vdd_label_found:
        pin_y = _generated_pin_y(cell_name, width, height, "vdd") if cell_name.startswith("gen_") else None
        if pin_y is not None:
            label_y["vdd"] = pin_y
    if not gnd_label_found:
        pin_y = _generated_pin_y(cell_name, width, height, "gnd") if cell_name.startswith("gen_") else None
        if pin_y is not None:
            label_y["gnd"] = pin_y
    if not {"vdd", "gnd"} <= set(label_y):
        return None, None, vdd_label_found, gnd_label_found, "missing_vdd_or_gnd_net_identity"
    vdd_rail = bottom if abs(label_y["vdd"] - bottom.center_y) <= abs(label_y["vdd"] - upper.center_y) else upper
    gnd_rail = bottom if abs(label_y["gnd"] - bottom.center_y) <= abs(label_y["gnd"] - upper.center_y) else upper
    if vdd_rail == gnd_rail:
        return None, None, vdd_label_found, gnd_label_found, "unable_to_assign_distinct_power_rails"
    return vdd_rail, gnd_rail, vdd_label_found, gnd_label_found, None


def _shape_overlaps_x(shape: _RailShape, x0: float, x1: float) -> bool:
    return not (shape.x1 <= x0 or x1 <= shape.x0)


def _analyze_overlap_band(top: gdstk.Cell, vdd_rail: _RailShape, gnd_rail: _RailShape) -> _OverlapAnalysis:
    top_rail = vdd_rail if vdd_rail.center_y >= gnd_rail.center_y else gnd_rail
    bottom_rail = vdd_rail if vdd_rail.center_y <= gnd_rail.center_y else gnd_rail
    rail_keys = {
        (top_rail.layer, top_rail.datatype, round(top_rail.x0, 6), round(top_rail.y0, 6), round(top_rail.x1, 6), round(top_rail.y1, 6)),
        (bottom_rail.layer, bottom_rail.datatype, round(bottom_rail.x0, 6), round(bottom_rail.y0, 6), round(bottom_rail.x1, 6), round(bottom_rail.y1, 6)),
    }
    top_clearance_below: float | None = None
    bottom_clearance_above: float | None = None
    unusual: list[dict[str, Any]] = []
    for polygon in top.polygons:
        pb = polygon.bounding_box()
        if pb is None:
            continue
        shape = _RailShape(int(polygon.layer), int(polygon.datatype), float(pb[0][0]), float(pb[0][1]), float(pb[1][0]), float(pb[1][1]))
        shape_key = (shape.layer, shape.datatype, round(shape.x0, 6), round(shape.y0, 6), round(shape.x1, 6), round(shape.y1, 6))
        if shape_key in rail_keys:
            continue
        if _shape_overlaps_x(shape, top_rail.x0, top_rail.x1) and shape.y1 <= top_rail.y0 + 1e-9:
            gap = top_rail.y0 - shape.y1
            top_clearance_below = gap if top_clearance_below is None else min(top_clearance_below, gap)
            if gap <= 0.12:
                unusual.append({"layer": shape.layer, "datatype": shape.datatype, "bbox": shape.to_bbox(), "boundary": "top"})
        if _shape_overlaps_x(shape, bottom_rail.x0, bottom_rail.x1) and shape.y0 >= bottom_rail.y1 - 1e-9:
            gap = shape.y0 - bottom_rail.y1
            bottom_clearance_above = gap if bottom_clearance_above is None else min(bottom_clearance_above, gap)
            if gap <= 0.12:
                unusual.append({"layer": shape.layer, "datatype": shape.datatype, "bbox": shape.to_bbox(), "boundary": "bottom"})
    if top_clearance_below is None:
        top_clearance_below = 0.0
    if bottom_clearance_above is None:
        bottom_clearance_above = 0.0
    top_rail_h = top_rail.height
    bottom_rail_h = bottom_rail.height
    max_safe = max(0.0, min(top_clearance_below, bottom_clearance_above, top_rail_h, bottom_rail_h))
    candidate = max(0.0, min(max_safe, top_rail_h * 0.5, bottom_rail_h * 0.5))
    blocked_reason = None
    if max_safe <= 1e-6 and unusual:
        blocked_reason = "non_power_shape_touches_overlap_band"
    return _OverlapAnalysis(top_clearance_below, bottom_clearance_above, round(candidate, 6), round(max_safe, 6), blocked_reason, tuple(unusual[:16]))


def classify_cell_rail_overlap(repo_root: str | Path, cell_name: str) -> RailOverlapEligibility:
    root = _repo_root(repo_root)
    tech = _load_tech(root)
    resolved = _resolve_cell(root, tech, cell_name)
    if cell_name in STORAGE_NAMES:
        return RailOverlapEligibility(
            cell_name=cell_name,
            resolved_cell_name=resolved.resolved_cell_name,
            gds_path=str(resolved.gds_path) if resolved.gds_path else None,
            bbox=resolved.bbox,
            height=resolved.height,
            width=resolved.width,
            vdd_label_found=False,
            gnd_label_found=False,
            vdd_rail_bbox=None,
            gnd_rail_bbox=None,
            vdd_rail_side=None,
            gnd_rail_side=None,
            rail_layer=None,
            top_rail_net=None,
            bottom_rail_net=None,
            supports_r0_mx_pairing=True,
            candidate_overlap_depth_um=0.0,
            max_safe_overlap_depth_um=0.0,
            overlap_eligible=False,
            eligibility_class="storage_array_already_supported",
            blocked_reason=None,
            recommended_packing_policy="storage_domain_existing_shared_rail_policy",
            edge_touch_only=False,
        )
    if "dff" in cell_name.lower() or cell_name in DFF_NAMES:
        unusual: tuple[dict[str, Any], ...] = ()
        vdd_bbox = None
        gnd_bbox = None
        rail_layer = None
        bbox = resolved.bbox
        vdd_found = False
        gnd_found = False
        top_net = None
        bottom_net = None
        if resolved.gds_path and resolved.gds_path.exists() and resolved.width and resolved.height:
            lib = gdstk.read_gds(resolved.gds_path)
            top = lib.top_level()[0]
            vdd_rail, gnd_rail, vdd_found, gnd_found, _ = _pick_power_rails(resolved.resolved_cell_name or cell_name, top, resolved.width, resolved.height)
            if vdd_rail and gnd_rail:
                vdd_bbox = vdd_rail.to_bbox()
                gnd_bbox = gnd_rail.to_bbox()
                rail_layer = vdd_rail.layer if vdd_rail.layer == gnd_rail.layer else None
                top_net = "vdd" if vdd_rail.center_y >= gnd_rail.center_y else "gnd"
                bottom_net = "vdd" if vdd_rail.center_y <= gnd_rail.center_y else "gnd"
                overlap = _analyze_overlap_band(top, vdd_rail, gnd_rail)
                unusual = overlap.unusual_power_related_shapes
        return RailOverlapEligibility(
            cell_name=cell_name,
            resolved_cell_name=resolved.resolved_cell_name,
            gds_path=str(resolved.gds_path) if resolved.gds_path else None,
            bbox=bbox,
            height=resolved.height,
            width=resolved.width,
            vdd_label_found=vdd_found,
            gnd_label_found=gnd_found,
            vdd_rail_bbox=vdd_bbox,
            gnd_rail_bbox=gnd_bbox,
            vdd_rail_side="top" if top_net == "vdd" else "bottom" if bottom_net == "vdd" else None,
            gnd_rail_side="top" if top_net == "gnd" else "bottom" if bottom_net == "gnd" else None,
            rail_layer=rail_layer,
            top_rail_net=top_net,
            bottom_rail_net=bottom_net,
            supports_r0_mx_pairing=False,
            candidate_overlap_depth_um=0.0,
            max_safe_overlap_depth_um=0.0,
            overlap_eligible=False,
            eligibility_class="excluded_dff_pending_manual_review",
            blocked_reason="dff_vertical_overlap_excluded_by_policy",
            recommended_packing_policy="dff_domain_no_vertical_overlap_policy",
            edge_touch_only=False,
            unusual_power_related_shapes=unusual,
        )
    if resolved.gds_path is None or not resolved.gds_path.exists() or resolved.width is None or resolved.height is None:
        return RailOverlapEligibility(
            cell_name=cell_name,
            resolved_cell_name=resolved.resolved_cell_name,
            gds_path=str(resolved.gds_path) if resolved.gds_path else None,
            bbox=resolved.bbox,
            height=resolved.height,
            width=resolved.width,
            vdd_label_found=False,
            gnd_label_found=False,
            vdd_rail_bbox=None,
            gnd_rail_bbox=None,
            vdd_rail_side=None,
            gnd_rail_side=None,
            rail_layer=None,
            top_rail_net=None,
            bottom_rail_net=None,
            supports_r0_mx_pairing=False,
            candidate_overlap_depth_um=0.0,
            max_safe_overlap_depth_um=0.0,
            overlap_eligible=False,
            eligibility_class="blocked_unknown",
            blocked_reason="missing_gds_or_dimensions",
            recommended_packing_policy="fallback_to_edge_touch_or_spacing",
            edge_touch_only=False,
        )

    lib = gdstk.read_gds(resolved.gds_path)
    top = lib.top_level()[0]
    vdd_rail, gnd_rail, vdd_found, gnd_found, rail_block = _pick_power_rails(resolved.resolved_cell_name or cell_name, top, resolved.width, resolved.height)
    if vdd_rail is None or gnd_rail is None:
        return RailOverlapEligibility(
            cell_name=cell_name,
            resolved_cell_name=resolved.resolved_cell_name,
            gds_path=str(resolved.gds_path),
            bbox=resolved.bbox,
            height=resolved.height,
            width=resolved.width,
            vdd_label_found=vdd_found,
            gnd_label_found=gnd_found,
            vdd_rail_bbox=None,
            gnd_rail_bbox=None,
            vdd_rail_side=None,
            gnd_rail_side=None,
            rail_layer=None,
            top_rail_net=None,
            bottom_rail_net=None,
            supports_r0_mx_pairing=False,
            candidate_overlap_depth_um=0.0,
            max_safe_overlap_depth_um=0.0,
            overlap_eligible=False,
            eligibility_class="blocked_missing_power_rail_geometry",
            blocked_reason=rail_block,
            recommended_packing_policy="fallback_to_edge_touch_or_spacing",
            edge_touch_only=False,
        )
    top_rail_net = "vdd" if vdd_rail.center_y >= gnd_rail.center_y else "gnd"
    bottom_rail_net = "vdd" if vdd_rail.center_y <= gnd_rail.center_y else "gnd"
    if top_rail_net == bottom_rail_net:
        return RailOverlapEligibility(
            cell_name=cell_name,
            resolved_cell_name=resolved.resolved_cell_name,
            gds_path=str(resolved.gds_path),
            bbox=resolved.bbox,
            height=resolved.height,
            width=resolved.width,
            vdd_label_found=vdd_found,
            gnd_label_found=gnd_found,
            vdd_rail_bbox=vdd_rail.to_bbox(),
            gnd_rail_bbox=gnd_rail.to_bbox(),
            vdd_rail_side="top" if top_rail_net == "vdd" else "bottom",
            gnd_rail_side="top" if top_rail_net == "gnd" else "bottom",
            rail_layer=vdd_rail.layer if vdd_rail.layer == gnd_rail.layer else None,
            top_rail_net=top_rail_net,
            bottom_rail_net=bottom_rail_net,
            supports_r0_mx_pairing=False,
            candidate_overlap_depth_um=0.0,
            max_safe_overlap_depth_um=0.0,
            overlap_eligible=False,
            eligibility_class="blocked_possible_vdd_gnd_short",
            blocked_reason="top_bottom_rail_net_not_complementary",
            recommended_packing_policy="fallback_to_edge_touch_or_spacing",
            edge_touch_only=False,
        )
    analysis = _analyze_overlap_band(top, vdd_rail, gnd_rail)
    rail_layer = vdd_rail.layer if vdd_rail.layer == gnd_rail.layer else None
    supports_pairing = True
    if analysis.blocked_reason is not None:
        eligibility_class = "blocked_non_power_shapes_in_overlap_band"
        overlap_eligible = False
        edge_touch_only = True
        blocked_reason = analysis.blocked_reason
    elif analysis.max_safe_overlap_depth_um > 1e-6:
        eligibility_class = "eligible_standard_gate_rail_overlap"
        overlap_eligible = True
        edge_touch_only = False
        blocked_reason = None
    else:
        eligibility_class = "eligible_touch_only"
        overlap_eligible = False
        edge_touch_only = True
        blocked_reason = "no_positive_overlap_margin_proven"
    if rail_layer is None:
        eligibility_class = "blocked_irregular_power_structure"
        overlap_eligible = False
        edge_touch_only = False
        blocked_reason = "power_rails_on_mismatched_layers"
    return RailOverlapEligibility(
        cell_name=cell_name,
        resolved_cell_name=resolved.resolved_cell_name,
        gds_path=str(resolved.gds_path),
        bbox=resolved.bbox,
        height=resolved.height,
        width=resolved.width,
        vdd_label_found=vdd_found,
        gnd_label_found=gnd_found,
        vdd_rail_bbox=vdd_rail.to_bbox(),
        gnd_rail_bbox=gnd_rail.to_bbox(),
        vdd_rail_side="top" if top_rail_net == "vdd" else "bottom",
        gnd_rail_side="top" if top_rail_net == "gnd" else "bottom",
        rail_layer=rail_layer,
        top_rail_net=top_rail_net,
        bottom_rail_net=bottom_rail_net,
        supports_r0_mx_pairing=supports_pairing,
        candidate_overlap_depth_um=analysis.candidate_overlap_depth_um,
        max_safe_overlap_depth_um=analysis.max_safe_overlap_depth_um,
        overlap_eligible=overlap_eligible,
        eligibility_class=eligibility_class,
        blocked_reason=blocked_reason,
        recommended_packing_policy="same_net_power_rail_overlap_packing" if overlap_eligible else "edge_touch_only" if edge_touch_only else "fallback_to_edge_touch_or_spacing",
        edge_touch_only=edge_touch_only,
        unusual_power_related_shapes=analysis.unusual_power_related_shapes,
    )


def audit_cell_rail_overlap_eligibility(repo_root: str | Path, cell_names: list[str] | None = None) -> dict[str, Any]:
    names = cell_names or discover_candidate_cells(repo_root)
    rows = [classify_cell_rail_overlap(repo_root, name) for name in sorted(dict.fromkeys(names))]
    eligible = [row for row in rows if row.overlap_eligible]
    blocked = [row for row in rows if row.eligibility_class.startswith("blocked")]
    return {
        "cell_rail_overlap_eligibility_audit_available": True,
        "repo_root": str(_repo_root(repo_root)),
        "all_used_cells_classified": True,
        "eligible_cells_count": len(eligible),
        "blocked_cells_count": len(blocked),
        "dff_excluded_from_vertical_overlap": all(row.eligibility_class == "excluded_dff_pending_manual_review" for row in rows if "dff" in row.cell_name.lower()),
        "cells": [row.to_dict() for row in rows],
    }


def write_csv(rows: list[dict[str, Any]], out_csv: str | Path) -> None:
    path = Path(out_csv)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            payload = {key: row.get(key) for key in CSV_FIELDS}
            payload["bbox"] = json.dumps(payload["bbox"], ensure_ascii=False) if payload["bbox"] is not None else None
            payload["vdd_rail_bbox"] = json.dumps(payload["vdd_rail_bbox"], ensure_ascii=False) if payload["vdd_rail_bbox"] is not None else None
            payload["gnd_rail_bbox"] = json.dumps(payload["gnd_rail_bbox"], ensure_ascii=False) if payload["gnd_rail_bbox"] is not None else None
            writer.writerow(payload)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Cell Rail Overlap Eligibility Report",
        "",
        f"- cell_rail_overlap_eligibility_audit_available: `{report['cell_rail_overlap_eligibility_audit_available']}`",
        f"- all_used_cells_classified: `{report['all_used_cells_classified']}`",
        f"- eligible_cells_count: `{report['eligible_cells_count']}`",
        f"- blocked_cells_count: `{report['blocked_cells_count']}`",
        f"- dff_excluded_from_vertical_overlap: `{report['dff_excluded_from_vertical_overlap']}`",
        "",
        "## Cells",
        "",
        "| cell | class | overlap_eligible | candidate_overlap_depth_um | blocked_reason | policy |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in report["cells"]:
        lines.append(
            f"| {row['cell_name']} | {row['eligibility_class']} | {row['overlap_eligible']} | {row['candidate_overlap_depth_um']} | {row['blocked_reason'] or ''} | {row['recommended_packing_policy']} |"
        )
    return "\n".join(lines) + "\n"
