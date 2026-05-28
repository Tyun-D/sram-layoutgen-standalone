"""Small GDS helpers used to inspect bundled OpenRAM cells."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from collections import Counter
from typing import Dict, Iterable, Optional


@dataclass(frozen=True)
class GDSBBox:
    x0: float
    y0: float
    x1: float
    y1: float
    shape_count: int

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def to_dict(self) -> Dict[str, float | int]:
        return {
            "x0": self.x0,
            "y0": self.y0,
            "x1": self.x1,
            "y1": self.y1,
            "width": self.width,
            "height": self.height,
            "shape_count": self.shape_count,
        }


def measure_gds_bbox(
    path: Path,
    boundary_layers: Optional[Iterable[int]] = None,
    ignored_layers: Optional[Iterable[int]] = None,
    ignored_lpps: Optional[Iterable[tuple[int, int]]] = None,
) -> Optional[GDSBBox]:
    """Measure a GDS bounding box in microns.

    OpenRAM's gdsMill keeps GDS coordinates in database units and converts
    using the second UNITS real: database-unit size in meters. We mirror that
    convention here. The first UNITS real is *not* the db-unit micron scale.
    """

    data = path.read_bytes()
    offset = 0
    db_unit_microns = 0.001
    boxes = []
    active_boundary = False
    current_layer = None
    current_datatype = 0
    allowed_layers = set(boundary_layers) if boundary_layers is not None else None
    skipped_layers = set(ignored_layers or [])
    skipped_lpps = set(ignored_lpps or [])

    while offset + 4 <= len(data):
        size, record_type, _data_type = struct.unpack(">HBB", data[offset : offset + 4])
        if size < 4 or offset + size > len(data):
            break
        payload = data[offset + 4 : offset + size]
        if record_type == 0x03 and len(payload) >= 16:
            db_unit_meters = _parse_gds_real8(payload[8:16])
            if db_unit_meters:
                db_unit_microns = db_unit_meters * 1e6
        elif record_type == 0x08:
            active_boundary = True
            current_layer = None
            current_datatype = 0
        elif record_type == 0x0D and active_boundary and len(payload) >= 2:
            current_layer = struct.unpack(">h", payload[:2])[0]
        elif record_type == 0x0E and active_boundary and len(payload) >= 2:
            current_datatype = struct.unpack(">h", payload[:2])[0]
        elif record_type == 0x10 and active_boundary:
            if current_layer is None:
                offset += size
                continue
            if allowed_layers is not None and current_layer not in allowed_layers:
                offset += size
                continue
            if current_layer in skipped_layers or (current_layer, current_datatype) in skipped_lpps:
                offset += size
                continue
            coords = [struct.unpack(">i", payload[i : i + 4])[0] for i in range(0, len(payload), 4)]
            xs = coords[0::2]
            ys = coords[1::2]
            boxes.append((min(xs), min(ys), max(xs), max(ys)))
        elif record_type == 0x11:
            active_boundary = False
        offset += size

    if not boxes:
        return None
    return GDSBBox(
        x0=round(min(box[0] for box in boxes) * db_unit_microns, 6),
        y0=round(min(box[1] for box in boxes) * db_unit_microns, 6),
        x1=round(max(box[2] for box in boxes) * db_unit_microns, 6),
        y1=round(max(box[3] for box in boxes) * db_unit_microns, 6),
        shape_count=len(boxes),
    )


def inspect_gds_hierarchy(path: Path) -> Dict[str, object]:
    """Return structure names and SREF counts for a GDS file."""

    data = path.read_bytes()
    offset = 0
    structures = []
    references: Dict[str, int] = {}
    text_count = 0
    labels: Dict[str, int] = {}
    current_structure = None
    in_sref = False
    in_text = False
    while offset + 4 <= len(data):
        size, record_type, _data_type = struct.unpack(">HBB", data[offset : offset + 4])
        if size < 4 or offset + size > len(data):
            break
        payload = data[offset + 4 : offset + size]
        if record_type == 0x05:
            current_structure = None
        elif record_type == 0x06:
            current_structure = payload.rstrip(b"\0").decode("ascii", errors="ignore")
            if current_structure:
                structures.append(current_structure)
        elif record_type == 0x0A:
            in_sref = True
        elif record_type == 0x0C:
            in_text = True
            text_count += 1
        elif record_type == 0x12 and in_sref:
            name = payload.rstrip(b"\0").decode("ascii", errors="ignore")
            references[name] = references.get(name, 0) + 1
        elif record_type == 0x19 and in_text:
            name = payload.rstrip(b"\0").decode("ascii", errors="ignore")
            labels[name] = labels.get(name, 0) + 1
        elif record_type == 0x11:
            in_sref = False
            in_text = False
        offset += size
    return {
        "structure_count": len(structures),
        "structures": structures,
        "reference_counts": dict(sorted(references.items())),
        "text_count": text_count,
        "labels": dict(sorted(labels.items())),
    }


def inspect_gds_layers(path: Path) -> Dict[str, Dict[str, int]]:
    """Return boundary and text layer/datatype counts for a GDS file."""

    data = path.read_bytes()
    offset = 0
    in_boundary = False
    in_text = False
    current_layer: Optional[int] = None
    current_datatype: Optional[int] = None
    boundary_counts: Counter[str] = Counter()
    text_counts: Counter[str] = Counter()

    while offset + 4 <= len(data):
        size, record_type, _data_type = struct.unpack(">HBB", data[offset : offset + 4])
        if size < 4 or offset + size > len(data):
            break
        payload = data[offset + 4 : offset + size]
        if record_type == 0x08:
            in_boundary = True
            current_layer = None
            current_datatype = None
        elif record_type == 0x0C:
            in_text = True
            current_layer = None
            current_datatype = None
        elif record_type == 0x0D and len(payload) >= 2:
            current_layer = struct.unpack(">h", payload[:2])[0]
        elif record_type in (0x0E, 0x16) and len(payload) >= 2:
            current_datatype = struct.unpack(">h", payload[:2])[0]
        elif record_type == 0x10 and in_boundary and current_layer is not None and current_datatype is not None:
            boundary_counts[f"{current_layer}/{current_datatype}"] += 1
        elif record_type == 0x19 and in_text and current_layer is not None and current_datatype is not None:
            text_counts[f"{current_layer}/{current_datatype}"] += 1
        elif record_type == 0x11:
            in_boundary = False
            in_text = False
        offset += size

    return {
        "boundary": dict(sorted(boundary_counts.items())),
        "text": dict(sorted(text_counts.items())),
    }


def inspect_gds_text_records(path: Path) -> list[dict[str, object]]:
    """Return text label records with layer/datatype and micron coordinates."""

    data = path.read_bytes()
    offset = 0
    db_unit_microns = 0.001
    in_text = False
    current_layer: Optional[int] = None
    current_texttype: Optional[int] = None
    current_xy: Optional[tuple[float, float]] = None
    text_records: list[dict[str, object]] = []

    while offset + 4 <= len(data):
        size, record_type, _data_type = struct.unpack(">HBB", data[offset : offset + 4])
        if size < 4 or offset + size > len(data):
            break
        payload = data[offset + 4 : offset + size]
        if record_type == 0x03 and len(payload) >= 16:
            db_unit_meters = _parse_gds_real8(payload[8:16])
            if db_unit_meters:
                db_unit_microns = db_unit_meters * 1e6
        elif record_type == 0x0C:
            in_text = True
            current_layer = None
            current_texttype = None
            current_xy = None
        elif record_type == 0x0D and in_text and len(payload) >= 2:
            current_layer = struct.unpack(">h", payload[:2])[0]
        elif record_type == 0x16 and in_text and len(payload) >= 2:
            current_texttype = struct.unpack(">h", payload[:2])[0]
        elif record_type == 0x10 and in_text and len(payload) >= 8:
            x, y = struct.unpack(">ii", payload[:8])
            current_xy = (round(x * db_unit_microns, 6), round(y * db_unit_microns, 6))
        elif record_type == 0x19 and in_text:
            text = payload.rstrip(b"\0").decode("ascii", errors="ignore")
            if current_layer is not None and current_texttype is not None and current_xy is not None:
                text_records.append(
                    {
                        "text": text,
                        "layer": current_layer,
                        "datatype": current_texttype,
                        "lpp": f"{current_layer}/{current_texttype}",
                        "x": current_xy[0],
                        "y": current_xy[1],
                    }
                )
        elif record_type == 0x11:
            in_text = False
        offset += size

    return text_records


def _parse_gds_real8(data: bytes) -> float:
    if data == b"\0" * 8:
        return 0.0
    sign = -1.0 if data[0] & 0x80 else 1.0
    exponent = (data[0] & 0x7F) - 64
    mantissa = int.from_bytes(data[1:], "big") / float(1 << 56)
    return sign * mantissa * (16.0**exponent)
