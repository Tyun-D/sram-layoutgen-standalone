from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import read_top_cell

EPSILON = 1e-6
SPATIAL_BUCKET_SIZE = 1.0
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
    (16, 0): "via3",
    (17, 0): "m4",
    (18, 0): "via4",
    (19, 0): "m5",
    (20, 0): "via5",
    (21, 0): "m6",
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


def _bucket_keys(rect: Rect) -> list[tuple[int, int]]:
    import math

    x0 = math.floor((rect.lx - EPSILON) / SPATIAL_BUCKET_SIZE)
    x1 = math.floor((rect.rx + EPSILON) / SPATIAL_BUCKET_SIZE)
    y0 = math.floor((rect.by - EPSILON) / SPATIAL_BUCKET_SIZE)
    y1 = math.floor((rect.uy + EPSILON) / SPATIAL_BUCKET_SIZE)
    return [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


def _spatial_index(rects: list[Rect] | tuple[Rect, ...]) -> dict[tuple[int, int], list[Rect]]:
    index: dict[tuple[int, int], list[Rect]] = defaultdict(list)
    for rect in rects:
        for key in _bucket_keys(rect):
            index[key].append(rect)
    return index


def _overlapping(rect: Rect, index: dict[tuple[int, int], list[Rect]]) -> list[Rect]:
    candidates: dict[str, Rect] = {}
    for key in _bucket_keys(rect):
        for candidate in index.get(key, []):
            candidates[candidate.rect_id] = candidate
    return [candidate for candidate in candidates.values() if candidate.rect_id != rect.rect_id and _touch_or_overlap(rect, candidate)]


def _at_point(x: float, y: float, index: dict[tuple[int, int], list[Rect]]) -> list[Rect]:
    import math

    key = (math.floor(x / SPATIAL_BUCKET_SIZE), math.floor(y / SPATIAL_BUCKET_SIZE))
    return [rect for rect in index.get(key, []) if _contains_point(rect, x, y)]


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
    poly_index = _spatial_index(poly_rects)
    for active_rect in active_rects:
        cut_intervals: list[tuple[float, float]] = []
        for poly_rect in _overlapping(active_rect, poly_index):
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
    m4_rects = rects.get("m4", [])
    m5_rects = rects.get("m5", [])
    m6_rects = rects.get("m6", [])
    contact_rects = rects.get("contact", [])
    via1_rects = rects.get("via1", [])
    via2_rects = rects.get("via2", [])
    via3_rects = rects.get("via3", [])
    via4_rects = rects.get("via4", [])
    via5_rects = rects.get("via5", [])
    active_segments, parent_to_children = _split_active_segments(active_rects, poly_rects)

    if metal_only:
        all_rects = {rect.rect_id: rect for rect in [*m1_rects, *m2_rects, *m3_rects, *m4_rects, *m5_rects, *m6_rects, *via1_rects, *via2_rects, *via3_rects, *via4_rects, *via5_rects]}
    else:
        all_rects = {rect.rect_id: rect for rect in [*m1_rects, *m2_rects, *m3_rects, *m4_rects, *m5_rects, *m6_rects, *poly_rects, *active_segments, *contact_rects, *via1_rects, *via2_rects, *via3_rects, *via4_rects, *via5_rects]}
    uf = _UnionFind()
    for rect_id in all_rects:
        uf.add(rect_id)

    layer_groups = (m1_rects, m2_rects, m3_rects, m4_rects, m5_rects, m6_rects) if metal_only else (m1_rects, m2_rects, m3_rects, m4_rects, m5_rects, m6_rects, poly_rects, active_segments)
    for layer_rects in layer_groups:
        spatial = _spatial_index(layer_rects)
        for left in layer_rects:
            for right in _overlapping(left, spatial):
                if left.rect_id < right.rect_id:
                    uf.union(left.rect_id, right.rect_id)

    contact_links: dict[str, list[str]] = {}
    if not metal_only:
        contact_targets = (*m1_rects, *poly_rects, *active_segments)
        contact_target_index = _spatial_index(contact_targets)
        for contact in contact_rects:
            linked: list[str] = []
            for target in _overlapping(contact, contact_target_index):
                uf.union(contact.rect_id, target.rect_id)
                linked.append(target.rect_id)
            contact_links[contact.rect_id] = sorted(linked)
    via1_links: dict[str, list[str]] = {}
    via1_target_index = _spatial_index((*m1_rects, *m2_rects))
    for via1 in via1_rects:
        linked: list[str] = []
        for target in _overlapping(via1, via1_target_index):
            uf.union(via1.rect_id, target.rect_id)
            linked.append(target.rect_id)
        via1_links[via1.rect_id] = sorted(linked)
    via2_links: dict[str, list[str]] = {}
    via2_target_index = _spatial_index((*m2_rects, *m3_rects))
    for via2 in via2_rects:
        linked: list[str] = []
        for target in _overlapping(via2, via2_target_index):
            uf.union(via2.rect_id, target.rect_id)
            linked.append(target.rect_id)
        via2_links[via2.rect_id] = sorted(linked)
    via3_links: dict[str, list[str]] = {}
    via3_target_index = _spatial_index((*m3_rects, *m4_rects))
    for via3 in via3_rects:
        linked = []
        for target in _overlapping(via3, via3_target_index):
            uf.union(via3.rect_id, target.rect_id)
            linked.append(target.rect_id)
        via3_links[via3.rect_id] = sorted(linked)
    via4_links: dict[str, list[str]] = {}
    via4_target_index = _spatial_index((*m4_rects, *m5_rects))
    for via4 in via4_rects:
        linked = []
        for target in _overlapping(via4, via4_target_index):
            uf.union(via4.rect_id, target.rect_id)
            linked.append(target.rect_id)
        via4_links[via4.rect_id] = sorted(linked)

    via5_links: dict[str, list[str]] = {}
    via5_target_index = _spatial_index((*m5_rects, *m6_rects))
    for via5 in via5_rects:
        linked = []
        for target in _overlapping(via5, via5_target_index):
            uf.union(via5.rect_id, target.rect_id)
            linked.append(target.rect_id)
        via5_links[via5.rect_id] = sorted(linked)

    conductor_label_index = _spatial_index((*m1_rects, *m2_rects, *m3_rects, *m4_rects, *m5_rects, *m6_rects))
    poly_label_index = _spatial_index(poly_rects)
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
        m1_hits = _at_point(float(label.origin[0]), float(label.origin[1]), conductor_label_index)
        poly_hits = [] if metal_only else _at_point(float(label.origin[0]), float(label.origin[1]), poly_label_index)
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
        nwell_index = _spatial_index(rects.get("nwell", []))
        pwell_index = _spatial_index(rects.get("pwell", []))
        nimplant_index = _spatial_index(rects.get("nimplant", []))
        pimplant_index = _spatial_index(rects.get("pimplant", []))
        contact_index = _spatial_index(contact_rects)
        for segment in active_segments:
            overlaps = {
                "nwell": bool(_overlapping(segment, nwell_index)),
                "pwell": bool(_overlapping(segment, pwell_index)),
                "nimplant": bool(_overlapping(segment, nimplant_index)),
                "pimplant": bool(_overlapping(segment, pimplant_index)),
                "contact_ids": sorted(rect.rect_id for rect in _overlapping(segment, contact_index)),
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
        "via3_links": via3_links,
        "via4_links": via4_links,
        "via5_links": via5_links,
        "components": sorted(components.values(), key=lambda item: item["component_id"]),
        "pin_labels": {key: value for key, value in sorted(pin_labels.items())},
        "label_hits": label_hits,
        "labels": labels,
        "rectangles": {
            "m1": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in m1_rects],
            "m2": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in m2_rects],
            "m3": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in m3_rects],
            "m4": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in m4_rects],
            "m5": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in m5_rects],
            "m6": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in m6_rects],
            "poly": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in poly_rects],
            "active_segments": [{"rect_id": rect.rect_id, "bbox": rect.bbox(), "source": rect.source} for rect in active_segments],
            "contact": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in contact_rects],
            "via1": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in via1_rects],
            "via2": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in via2_rects],
            "via3": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in via3_rects],
            "via4": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in via4_rects],
            "via5": [{"rect_id": rect.rect_id, "bbox": rect.bbox()} for rect in via5_rects],
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
