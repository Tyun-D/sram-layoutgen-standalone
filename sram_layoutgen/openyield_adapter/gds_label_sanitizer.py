from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity

GDS_LAYER_BY_NAME = {
    "m1": (11, 0),
    "poly": (9, 0),
}
INTERNAL_TERMINAL_LABELS = {"G", "S", "D"}
PINV_CANONICAL_PINS = ["VDD", "VSS", "A", "Z"]
TG_CANONICAL_PINS = ["VDD", "VSS", "IN", "OUT", "CTR_P", "CTR_N"]
CANONICAL_PINS_BY_TYPE = {
    "PINV": PINV_CANONICAL_PINS,
    "TRANSMISSION_GATE": TG_CANONICAL_PINS,
}
FORBIDDEN_ALIASES_BY_TYPE = {
    "PINV": ["vdd", "gnd"],
    "TRANSMISSION_GATE": ["vdd", "gnd", "in", "out", "ctr_p", "ctr_n"],
}


@dataclass(frozen=True)
class LabelInventoryRow:
    cell_name: str
    hierarchy_cell_name: str
    instance_path: str
    label_text: str
    label_layer: int
    label_datatype: int
    origin_x: float
    origin_y: float
    conductive_component_id: str
    is_canonical: bool
    is_lowercase_alias: bool
    is_internal_device_terminal: bool
    duplication_source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "cell_name": self.cell_name,
            "hierarchy_cell_name": self.hierarchy_cell_name,
            "instance_path": self.instance_path,
            "label_text": self.label_text,
            "label_layer": self.label_layer,
            "label_datatype": self.label_datatype,
            "origin_x": self.origin_x,
            "origin_y": self.origin_y,
            "conductive_component_id": self.conductive_component_id,
            "is_canonical": self.is_canonical,
            "is_lowercase_alias": self.is_lowercase_alias,
            "is_internal_device_terminal": self.is_internal_device_terminal,
            "duplication_source": self.duplication_source,
        }


def infer_cell_type(cell_name: str) -> str:
    if cell_name.startswith("PINV_"):
        return "PINV"
    if cell_name.startswith("TRANSMISSION_GATE_"):
        return "TRANSMISSION_GATE"
    raise ValueError(f"unsupported primitive cell type for {cell_name}")


def canonical_pin_names(cell_name: str) -> list[str]:
    return CANONICAL_PINS_BY_TYPE[infer_cell_type(cell_name)]


def _affine_identity() -> tuple[float, float, float, float, float, float]:
    return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def _compose_affine(
    left: tuple[float, float, float, float, float, float],
    right: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float, float, float]:
    la, lb, lc, ld, ltx, lty = left
    ra, rb, rc, rd, rtx, rty = right
    return (
        la * ra + lb * rc,
        la * rb + lb * rd,
        lc * ra + ld * rc,
        lc * rb + ld * rd,
        la * rtx + lb * rty + ltx,
        lc * rtx + ld * rty + lty,
    )


def _reference_affine(reference: gdstk.Reference) -> tuple[float, float, float, float, float, float]:
    magnification = float(reference.magnification or 1.0)
    rotation = float(reference.rotation or 0.0)
    cos_theta = math.cos(rotation)
    sin_theta = math.sin(rotation)
    reflect_y = -1.0 if reference.x_reflection else 1.0
    return (
        magnification * cos_theta,
        -magnification * sin_theta * reflect_y,
        magnification * sin_theta,
        magnification * cos_theta * reflect_y,
        float(reference.origin[0]),
        float(reference.origin[1]),
    )


def _apply_affine(point: tuple[float, float], affine: tuple[float, float, float, float, float, float]) -> tuple[float, float]:
    a, b, c, d, tx, ty = affine
    x, y = point
    return (a * x + b * y + tx, c * x + d * y + ty)


def _shape_component_lookup(graph: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for component in graph["components"]:
        for member in component["members"]:
            lookup[member] = component["component_id"]
    return lookup


def _component_id_for_label(graph: dict[str, Any], label_text: str, origin_x: float, origin_y: float) -> str:
    shape_lookup = _shape_component_lookup(graph)
    for hit in graph.get("label_hits", []):
        if hit["text"] != label_text:
            continue
        if abs(hit["origin"][0] - origin_x) > 1e-6 or abs(hit["origin"][1] - origin_y) > 1e-6:
            continue
        for shape_id in hit["shape_ids"]:
            component_id = shape_lookup.get(shape_id)
            if component_id:
                return component_id
    return ""


def _duplication_source(cell_name: str, hierarchy_cell_name: str, label_text: str) -> str:
    if hierarchy_cell_name == cell_name:
        return "TOP_WRAPPER_CANONICAL"
    if hierarchy_cell_name.endswith("_core"):
        return "CORE_ALIAS" if label_text != label_text.upper() else "CORE_CANONICAL_DUPLICATE"
    if label_text in INTERNAL_TERMINAL_LABELS:
        return "PTX_INTERNAL_TERMINAL"
    return "CHILD_OTHER"


def recursive_label_inventory(gds_path: Path, top_name: str) -> list[dict[str, Any]]:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    graph = extract_physical_connectivity(gds_path, top_name)
    canonical = set(canonical_pin_names(top_name))
    forbidden_aliases = set(FORBIDDEN_ALIASES_BY_TYPE[infer_cell_type(top_name)])
    rows: list[LabelInventoryRow] = []

    def visit(cell: gdstk.Cell, affine: tuple[float, float, float, float, float, float], instance_path: list[str]) -> None:
        for label in cell.labels:
            origin_x, origin_y = _apply_affine((float(label.origin[0]), float(label.origin[1])), affine)
            text = str(label.text)
            rows.append(
                LabelInventoryRow(
                    cell_name=top_name,
                    hierarchy_cell_name=cell.name,
                    instance_path="/".join(instance_path) if instance_path else top_name,
                    label_text=text,
                    label_layer=int(label.layer),
                    label_datatype=int(label.texttype),
                    origin_x=round(origin_x, 6),
                    origin_y=round(origin_y, 6),
                    conductive_component_id=_component_id_for_label(graph, text, round(origin_x, 6), round(origin_y, 6)),
                    is_canonical=text in canonical,
                    is_lowercase_alias=text in forbidden_aliases,
                    is_internal_device_terminal=text in INTERNAL_TERMINAL_LABELS,
                    duplication_source=_duplication_source(top_name, cell.name, text),
                )
            )
        for index, reference in enumerate(cell.references):
            child_affine = _compose_affine(affine, _reference_affine(reference))
            child_name = reference.cell_name or reference.cell.name
            visit(reference.cell, child_affine, [*instance_path, f"{child_name}[{index}]"])

    visit(top, _affine_identity(), [])
    raw_rows = [row.as_dict() for row in rows]
    exact_duplicate_counts: dict[tuple[Any, ...], int] = {}
    for row in raw_rows:
        key = (
            row["label_text"],
            row["label_layer"],
            row["label_datatype"],
            row["origin_x"],
            row["origin_y"],
        )
        exact_duplicate_counts[key] = exact_duplicate_counts.get(key, 0) + 1
    by_component: dict[str, set[str]] = {}
    for row in raw_rows:
        component_id = row["conductive_component_id"]
        if component_id:
            by_component.setdefault(component_id, set()).add(row["label_text"])
    for row in raw_rows:
        duplicate_key = (
            row["label_text"],
            row["label_layer"],
            row["label_datatype"],
            row["origin_x"],
            row["origin_y"],
        )
        row["exact_duplicate_count"] = exact_duplicate_counts[duplicate_key]
        component_names = sorted(by_component.get(row["conductive_component_id"], set()))
        row["same_component_distinct_label_names"] = "|".join(component_names)
    return raw_rows


def sanitize_gds_labels(
    *,
    source_gds: Path,
    source_top_name: str,
    pin_map: dict[str, list[dict[str, Any]]],
    output_gds: Path,
) -> dict[str, Any]:
    source_lib = gdstk.read_gds(source_gds)
    cell_copies: dict[str, gdstk.Cell] = {}
    sanitized_lib = gdstk.Library(unit=source_lib.unit, precision=source_lib.precision)
    for cell in source_lib.cells:
        copied = cell.copy(cell.name, deep_copy=True)
        if copied.labels:
            copied.remove(*copied.labels)
        cell_copies[cell.name] = copied
    for copied in cell_copies.values():
        for reference in copied.references:
            reference.cell = cell_copies[reference.cell_name or reference.cell.name]
        sanitized_lib.add(copied)
    top = cell_copies[source_top_name]
    for pin_name in canonical_pin_names(source_top_name):
        pin_entries = pin_map[pin_name]
        pin_entry = pin_entries[0]
        layer_name = str(pin_entry["layer"]).lower()
        layer, texttype = GDS_LAYER_BY_NAME[layer_name]
        origin = ((pin_entry["lx"] + pin_entry["rx"]) * 0.5, (pin_entry["by"] + pin_entry["uy"]) * 0.5)
        top.add(gdstk.Label(pin_name, origin, layer=layer, texttype=texttype))
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    sanitized_lib.write_gds(output_gds)
    return {
        "output_gds": str(output_gds),
        "canonical_labels_added": canonical_pin_names(source_top_name),
        "child_label_visibility_policy": "STRIP_FROM_REUSABLE_EXPORT",
    }


def load_pin_map(path: Path) -> dict[str, list[dict[str, Any]]]:
    return json.loads(path.read_text(encoding="utf-8"))
