from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import read_top_cell

EPSILON = 1e-6
LAYER_NAME_BY_GDS = {
    (1, 0): "active",
    (2, 0): "pwell",
    (3, 0): "nwell",
    (4, 0): "nimplant",
    (5, 0): "pimplant",
    (6, 0): "vtg",
    (9, 0): "poly",
    (10, 0): "contact",
    (11, 0): "m1",
    (12, 0): "via1",
    (13, 0): "m2",
    (14, 0): "via2",
    (15, 0): "m3",
    (239, 0): "text",
}


@dataclass(frozen=True)
class Rect:
    rect_id: str
    layer: str
    lx: float
    by: float
    rx: float
    uy: float
    source: str

    def bbox(self) -> list[float]:
        return [round(self.lx, 6), round(self.by, 6), round(self.rx, 6), round(self.uy, 6)]

    def center(self) -> tuple[float, float]:
        return ((self.lx + self.rx) * 0.5, (self.by + self.uy) * 0.5)


class _UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def add(self, item: str) -> None:
        self.parent.setdefault(item, item)

    def find(self, item: str) -> str:
        parent = self.parent[item]
        if parent != item:
            self.parent[item] = self.find(parent)
        return self.parent[item]

    def union(self, left: str, right: str) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left != root_right:
            self.parent[root_right] = root_left


def _touch_or_overlap(a: Rect, b: Rect) -> bool:
    return not (a.rx < b.lx - EPSILON or b.rx < a.lx - EPSILON or a.uy < b.by - EPSILON or b.uy < a.by - EPSILON)


def _contains_point(rect: Rect, x: float, y: float) -> bool:
    return rect.lx - EPSILON <= x <= rect.rx + EPSILON and rect.by - EPSILON <= y <= rect.uy + EPSILON


def _merged_intervals(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not intervals:
        return []
    intervals = sorted(intervals)
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end + EPSILON:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged


def _rect_from_polygon(poly: gdstk.Polygon, index: int) -> Rect:
    bbox = poly.bounding_box()
    layer = LAYER_NAME_BY_GDS.get((poly.layer, poly.datatype), f"{poly.layer}/{poly.datatype}")
    return Rect(
        rect_id=f"{layer}_{index}",
        layer=layer,
        lx=float(bbox[0][0]),
        by=float(bbox[0][1]),
        rx=float(bbox[1][0]),
        uy=float(bbox[1][1]),
        source="polygon_bbox",
    )


def _split_active_segments(active_rects: list[Rect], poly_rects: list[Rect]) -> tuple[list[Rect], dict[str, list[str]]]:
    segments: list[Rect] = []
    parent_to_children: dict[str, list[str]] = {}
    for active_rect in active_rects:
        cut_intervals: list[tuple[float, float]] = []
        for poly_rect in poly_rects:
            if poly_rect.uy <= active_rect.by + EPSILON or poly_rect.by >= active_rect.uy - EPSILON:
                continue
            overlap_left = max(active_rect.lx, poly_rect.lx)
            overlap_right = min(active_rect.rx, poly_rect.rx)
            if overlap_right - overlap_left > EPSILON:
                cut_intervals.append((overlap_left, overlap_right))
        merged = _merged_intervals(cut_intervals)
        child_ids: list[str] = []
        cursor = active_rect.lx
        segment_index = 0
        for cut_left, cut_right in merged:
            if cut_left - cursor > EPSILON:
                segment = Rect(
                    rect_id=f"{active_rect.rect_id}_seg{segment_index}",
                    layer="active_segment",
                    lx=cursor,
                    by=active_rect.by,
                    rx=cut_left,
                    uy=active_rect.uy,
                    source=active_rect.rect_id,
                )
                segments.append(segment)
                child_ids.append(segment.rect_id)
                segment_index += 1
            cursor = max(cursor, cut_right)
        if active_rect.rx - cursor > EPSILON:
            segment = Rect(
                rect_id=f"{active_rect.rect_id}_seg{segment_index}",
                layer="active_segment",
                lx=cursor,
                by=active_rect.by,
                rx=active_rect.rx,
                uy=active_rect.uy,
                source=active_rect.rect_id,
            )
            segments.append(segment)
            child_ids.append(segment.rect_id)
        if not merged:
            segment = Rect(
                rect_id=f"{active_rect.rect_id}_seg0",
                layer="active_segment",
                lx=active_rect.lx,
                by=active_rect.by,
                rx=active_rect.rx,
                uy=active_rect.uy,
                source=active_rect.rect_id,
            )
            segments.append(segment)
            child_ids.append(segment.rect_id)
        parent_to_children[active_rect.rect_id] = child_ids
    return segments, parent_to_children


def _rects_by_layer(flattened: gdstk.Cell) -> dict[str, list[Rect]]:
    layer_map: dict[str, list[Rect]] = defaultdict(list)
    seen: set[tuple[str, float, float, float, float]] = set()
    for index, poly in enumerate(flattened.polygons):
        rect = _rect_from_polygon(poly, index)
        key = (rect.layer, round(rect.lx, 6), round(rect.by, 6), round(rect.rx, 6), round(rect.uy, 6))
        if key in seen:
            continue
        seen.add(key)
        layer_map[rect.layer].append(rect)
    return dict(layer_map)


def extract_physical_connectivity(gds_path: Path, top_name: str | None = None, *, metal_only: bool = False) -> dict[str, Any]:
    _, top = read_top_cell(gds_path, top_name)
    flattened = top.flatten()
    rects = _rects_by_layer(flattened)
    active_rects = rects.get("active", [])
    poly_rects = rects.get("poly", [])
    m1_rects = rects.get("m1", [])
    m2_rects = rects.get("m2", [])
    m3_rects = rects.get("m3", [])
    contact_rects = rects.get("contact", [])
    via1_rects = rects.get("via1", [])
    via2_rects = rects.get("via2", [])
    active_segments, parent_to_children = _split_active_segments(active_rects, poly_rects)

    if metal_only:
        all_rects = {rect.rect_id: rect for rect in [*m1_rects, *m2_rects, *m3_rects, *via1_rects, *via2_rects]}
    else:
        all_rects = {rect.rect_id: rect for rect in [*m1_rects, *m2_rects, *m3_rects, *poly_rects, *active_segments, *contact_rects, *via1_rects, *via2_rects]}
    uf = _UnionFind()
    for rect_id in all_rects:
        uf.add(rect_id)

    layer_groups = (m1_rects, m2_rects, m3_rects) if metal_only else (m1_rects, m2_rects, m3_rects, poly_rects, active_segments)
    for layer_rects in layer_groups:
        for index, left in enumerate(layer_rects):
            for right in layer_rects[index + 1 :]:
                if _touch_or_overlap(left, right):
                    uf.union(left.rect_id, right.rect_id)

    contact_links: dict[str, list[str]] = {}
    if not metal_only:
        for contact in contact_rects:
            linked: list[str] = []
            for target in (*m1_rects, *poly_rects, *active_segments):
                if _touch_or_overlap(contact, target):
                    uf.union(contact.rect_id, target.rect_id)
                    linked.append(target.rect_id)
            contact_links[contact.rect_id] = sorted(linked)
    via1_links: dict[str, list[str]] = {}
    for via1 in via1_rects:
        linked: list[str] = []
        for target in (*m1_rects, *m2_rects):
            if _touch_or_overlap(via1, target):
                uf.union(via1.rect_id, target.rect_id)
                linked.append(target.rect_id)
        via1_links[via1.rect_id] = sorted(linked)
    via2_links: dict[str, list[str]] = {}
    for via2 in via2_rects:
        linked: list[str] = []
        for target in (*m2_rects, *m3_rects):
            if _touch_or_overlap(via2, target):
                uf.union(via2.rect_id, target.rect_id)
                linked.append(target.rect_id)
        via2_links[via2.rect_id] = sorted(linked)

    labels = []
    pin_labels: dict[str, list[dict[str, Any]]] = defaultdict(list)
    label_hits: list[dict[str, Any]] = []
    for label in flattened.labels:
        entry = {
            "text": str(label.text),
            "layer": LAYER_NAME_BY_GDS.get((label.layer, label.texttype), f"{label.layer}/{label.texttype}"),
            "origin": [round(float(label.origin[0]), 6), round(float(label.origin[1]), 6)],
        }
        labels.append(entry)
        text = str(label.text)
        m1_hits = [rect for rect in (*m1_rects, *m2_rects, *m3_rects) if _contains_point(rect, float(label.origin[0]), float(label.origin[1]))]
        poly_hits = [] if metal_only else [rect for rect in poly_rects if _contains_point(rect, float(label.origin[0]), float(label.origin[1]))]
        hit_ids = [rect.rect_id for rect in m1_hits or poly_hits]
        label_hits.append({"text": text, "origin": entry["origin"], "shape_ids": hit_ids, "layer": entry["layer"]})
        pin_labels[text].append({"origin": entry["origin"], "shape_ids": hit_ids})

    components: dict[str, dict[str, Any]] = {}
    for rect in all_rects.values():
        component_id = uf.find(rect.rect_id)
        bucket = components.setdefault(
            component_id,
            {"component_id": component_id, "members": [], "layers": set(), "bbox": [rect.lx, rect.by, rect.rx, rect.uy]},
        )
        bucket["members"].append(rect.rect_id)
        bucket["layers"].add(rect.layer)
        bucket["bbox"][0] = min(bucket["bbox"][0], rect.lx)
        bucket["bbox"][1] = min(bucket["bbox"][1], rect.by)
        bucket["bbox"][2] = max(bucket["bbox"][2], rect.rx)
        bucket["bbox"][3] = max(bucket["bbox"][3], rect.uy)

    for bucket in components.values():
        bucket["members"].sort()
        bucket["layers"] = sorted(bucket["layers"])
        bucket["bbox"] = [round(value, 6) for value in bucket["bbox"]]

    active_segment_details = []
    if not metal_only:
        for segment in active_segments:
            overlaps = {
                "nwell": any(_touch_or_overlap(segment, rect) for rect in rects.get("nwell", [])),
                "pwell": any(_touch_or_overlap(segment, rect) for rect in rects.get("pwell", [])),
                "nimplant": any(_touch_or_overlap(segment, rect) for rect in rects.get("nimplant", [])),
                "pimplant": any(_touch_or_overlap(segment, rect) for rect in rects.get("pimplant", [])),
                "contact_ids": sorted(rect.rect_id for rect in contact_rects if _touch_or_overlap(segment, rect)),
                "component_id": uf.find(segment.rect_id),
            }
            active_segment_details.append(
                {
                    "segment_id": segment.rect_id,
                    "parent_active_id": segment.source,
                    "bbox": segment.bbox(),
                    **overlaps,
                }
            )

    report = {
        "gds_path": str(gds_path),
        "top_cell": top.name,
        "extraction_mode": "metal_only" if metal_only else "full_device",
        "layers_present": {layer: len(items) for layer, items in sorted(rects.items())},
        "parent_active_to_segments": parent_to_children,
        "active_segments": active_segment_details,
        "contact_links": contact_links,
        "via1_links": via1_links,
        "via2_links": via2_links,
        "components": sorted(components.values(), key=lambda item: item["component_id"]),
        "pin_labels": {key: value for key, value in sorted(pin_labels.items())},
        "label_hits": label_hits,
        "labels": labels,
        "rectangles": {
            "m1": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in m1_rects],
            "m2": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in m2_rects],
            "m3": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in m3_rects],
            "poly": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in poly_rects],
            "active_segments": [{"rect_id": rect.rect_id, "bbox": rect.bbox(), "source": rect.source} for rect in active_segments],
            "contact": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in contact_rects],
            "via1": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in via1_rects],
            "via2": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in via2_rects],
        },
    }
    if not metal_only:
        return report
    report["active_segments"] = []
    report["contact_links"] = {}
    report["parent_active_to_segments"] = {}
    report["rectangles"]["active_segments"] = []
    report["rectangles"]["contact"] = []
    return report
