from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.gds_pin_audit import GdsShape, GdsText, read_gds_labels_and_shapes


LAYER_NAME_TO_GDS = {
    "m1": 11,
    "m2": 13,
    "m3": 15,
    "m4": 17,
    "m5": 19,
    "m6": 21,
}


@dataclass(frozen=True)
class ModuleArtifactBundle:
    module_name: str
    module_dir: Path
    gds_path: Path
    bbox: dict[str, Any]
    rail_report: dict[str, Any]
    generator_manifest: dict[str, Any]
    raw_pins_payload: dict[str, Any]
    raw_pins: list[dict[str, Any]]
    labels: tuple[GdsText, ...]
    shapes: tuple[GdsShape, ...]
    gds_bbox: dict[str, float] | None


def load_module_artifacts(module_dir: Path) -> ModuleArtifactBundle:
    module_name = module_dir.name
    gds_path = module_dir / f"{module_name}.gds"
    bbox = json.loads((module_dir / "bbox.json").read_text(encoding="utf-8"))
    rail_report = json.loads((module_dir / "rail_report.json").read_text(encoding="utf-8"))
    generator_manifest = json.loads((module_dir / "generator_manifest.json").read_text(encoding="utf-8"))
    raw_pins_payload = json.loads((module_dir / "pins.json").read_text(encoding="utf-8"))
    raw_pins = normalize_pin_payload(raw_pins_payload)
    labels, shapes, gds_bbox = read_gds_labels_and_shapes(gds_path)
    bbox_dict = gds_bbox.to_dict() if gds_bbox else None
    return ModuleArtifactBundle(
        module_name=module_name,
        module_dir=module_dir,
        gds_path=gds_path,
        bbox=bbox,
        rail_report=rail_report,
        generator_manifest=generator_manifest,
        raw_pins_payload=raw_pins_payload,
        raw_pins=raw_pins,
        labels=labels,
        shapes=shapes,
        gds_bbox=bbox_dict,
    )


def normalize_pin_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        if isinstance(payload.get("pins"), list):
            return [dict(item) for item in payload["pins"]]
        if all(isinstance(value, dict) for value in payload.values()):
            rows: list[dict[str, Any]] = []
            for name, value in payload.items():
                row = dict(value)
                row.setdefault("name", name)
                rows.append(row)
            return rows
    if isinstance(payload, list):
        return [dict(item) for item in payload]
    return []


def parse_layer_number(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if "/" in text:
        token = text.split("/", 1)[0]
        if token.isdigit():
            return int(token)
    if text.isdigit():
        return int(text)
    return LAYER_NAME_TO_GDS.get(text)


def canonicalize_pin_name(pin_name: str) -> str:
    text = str(pin_name).strip()
    text = text.replace("[*]", "")
    text = re.sub(r"\[\d+\]", "", text)
    text = text.replace("_bar", "b")
    text = text.replace("BLB", "BR")
    text = text.replace("blb", "br")
    text = text.replace("Q_bar", "QB")
    return re.sub(r"[^A-Za-z0-9]+", "", text).lower()


def point_to_bbox_distance(bbox: dict[str, float], x: float, y: float) -> float:
    dx = 0.0 if bbox["x0"] <= x <= bbox["x1"] else min(abs(x - bbox["x0"]), abs(x - bbox["x1"]))
    dy = 0.0 if bbox["y0"] <= y <= bbox["y1"] else min(abs(y - bbox["y0"]), abs(y - bbox["y1"]))
    return math.hypot(dx, dy)


def shape_to_bbox(shape: GdsShape) -> dict[str, float]:
    bbox = shape.bbox.to_dict()
    bbox["width"] = round(bbox["x1"] - bbox["x0"], 6)
    bbox["height"] = round(bbox["y1"] - bbox["y0"], 6)
    return bbox


def find_geometry_for_pin(
    pin_name: str,
    raw_pin: dict[str, Any] | None,
    labels: tuple[GdsText, ...],
    shapes: tuple[GdsShape, ...],
    search_tol: float = 0.08,
) -> dict[str, Any] | None:
    target = canonicalize_pin_name(pin_name)
    layer = parse_layer_number((raw_pin or {}).get("layer"))
    x = float((raw_pin or {}).get("x", 0.0) or 0.0)
    y = float((raw_pin or {}).get("y", 0.0) or 0.0)
    matched_labels = [label for label in labels if canonicalize_pin_name(label.text) == target]
    candidate_shapes: list[tuple[float, GdsShape, str]] = []
    for shape in shapes:
        if layer is not None and shape.layer is not None and int(shape.layer) != layer:
            continue
        bbox = shape_to_bbox(shape)
        distance = point_to_bbox_distance(bbox, x, y)
        if distance <= search_tol:
            candidate_shapes.append((distance, shape, "shape_near_pin_coordinate"))
        for label in matched_labels:
            if point_to_bbox_distance(bbox, float(label.x), float(label.y)) <= search_tol:
                candidate_shapes.append((point_to_bbox_distance(bbox, float(label.x), float(label.y)), shape, "shape_near_matching_label"))
    if not candidate_shapes:
        return None
    candidate_shapes.sort(key=lambda item: (item[0], (item[1].bbox.width * item[1].bbox.height)))
    _, shape, reason = candidate_shapes[0]
    bbox = shape_to_bbox(shape)
    return {
        "bbox": bbox,
        "layer": shape.layer if shape.layer is not None else layer,
        "label": matched_labels[0].text if matched_labels else pin_name,
        "source_evidence": reason,
    }
