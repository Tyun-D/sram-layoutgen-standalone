"""Minimal GDSII writer for rectangle-based layouts."""

from __future__ import annotations

import struct
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .geometry import LayoutDB, Rect, Shape
from .openram_placement import array_mirror, openram_sref_origin, sref_origin_for_bbox
from .stdcell import draw_generated_cell, generated_cell_pins
from .tech import Tech


class GDSWriter:
    DEFAULT_TIMESTAMP = (2026, 1, 1, 0, 0, 0)

    def __init__(
        self,
        tech: Tech,
        db_units_per_micron: int = 2000,
        timestamp: Tuple[int, int, int, int, int, int] | None = DEFAULT_TIMESTAMP,
        include_route_guides: bool = False,
        include_debug_probes: bool = False,
        include_module_overlay: bool = False,
        omit_cell_refs: bool = False,
        include_pin_shapes: bool = True,
        include_pin_labels: bool = True,
        include_cell_pin_labels: bool = True,
        strip_imported_text: bool = False,
        include_stdcell_shapes: bool = False,
    ) -> None:
        self.tech = tech
        self.db_units_per_micron = db_units_per_micron
        self.timestamp = timestamp
        self.include_route_guides = include_route_guides
        self.include_debug_probes = include_debug_probes
        self.include_module_overlay = include_module_overlay
        self.omit_cell_refs = omit_cell_refs
        self.include_pin_shapes = include_pin_shapes
        self.include_pin_labels = include_pin_labels
        self.include_cell_pin_labels = include_cell_pin_labels
        self.strip_imported_text = strip_imported_text
        self.include_stdcell_shapes = include_stdcell_shapes
        self.grid_dbu = self._manufacturing_grid_dbu()

    def write(self, layout: LayoutDB, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = bytearray()
        stamp = self._stamp()
        imported = {} if self.omit_cell_refs else self._import_cell_structures(layout)
        data += self._int2_record(0x00, [600])
        data += self._int2_record(0x01, [*stamp, *stamp])
        data += self._str_record(0x02, "SRAM_LAYOUTGEN")
        data += self._real8_record(0x03, [1.0 / self.db_units_per_micron, 1e-6 / self.db_units_per_micron])
        for _name, struct_bytes in sorted(imported.items()):
            data += struct_bytes
        data += self._int2_record(0x05, [*stamp, *stamp])
        data += self._str_record(0x06, self._clean_name(layout.top_name))
        if not self.omit_cell_refs:
            for array in layout.cell_arrays:
                if array.cell not in imported:
                    continue
                cell = self.tech.cell(array.cell)
                for row in range(array.rows):
                    for col in range(array.columns):
                        desired_x0 = array.origin.x + col * array.pitch_x
                        desired_y0 = array.origin.y + row * array.pitch_y
                        mirror = array_mirror(
                            row,
                            col,
                            array.mirror_x,
                            array.mirror_y,
                            array.row_offset,
                            array.column_offset,
                        )
                        x, y = openram_sref_origin(cell, desired_x0, desired_y0, mirror)
                        data += self._sref(
                            array.cell,
                            x,
                            y,
                            mirror,
                        )
            for instance in layout.instances:
                if instance.cell not in imported:
                    continue
                cell = self.tech.cell(instance.cell)
                if instance.placement_mode == "openram_origin" and instance.origin is not None:
                    x, y = openram_sref_origin(cell, instance.origin.x, instance.origin.y, instance.mirror)
                else:
                    x, y = sref_origin_for_bbox(cell, instance.rect.x0, instance.rect.y0, instance.mirror)
                data += self._sref(
                    instance.cell,
                    x,
                    y,
                    instance.mirror,
                )
        for shape in self._drawable_shapes(layout):
            layer = self.tech.layers.get(shape.layer)
            if layer is None or shape.rect.area <= 0:
                continue
            if shape.purpose in {"module", "well"} or (shape.purpose == "stdcell" and not self.include_stdcell_shapes):
                continue
            if shape.purpose == "route_guide" and not self.include_route_guides:
                continue
            if shape.purpose == "debug_probe" and not self.include_debug_probes:
                continue
            data += self._boundary(layer.gds_layer, layer.datatype, shape.rect)
        if self.include_module_overlay:
            data += self._module_overlay(layout)
        if self.include_pin_shapes or self.include_pin_labels:
            for pin in layout.pin_list():
                pin_layer = self.tech.layers.get(pin.layer)
                if pin_layer is None:
                    continue
                if self.include_pin_shapes:
                    data += self._boundary(pin_layer.gds_layer, 2, pin.rect)
                if self.include_pin_labels:
                    data += self._text(pin_layer.gds_layer, 1, pin.net, pin.center.x, pin.center.y)
                    text_layer = self.tech.layers.get("text")
                    if text_layer is not None:
                        data += self._text(text_layer.gds_layer, text_layer.datatype, pin.net, pin.center.x, pin.center.y)
        data += self._record(0x07, 0x00, b"")
        data += self._record(0x04, 0x00, b"")
        path.write_bytes(data)

    def _drawable_shapes(self, layout: LayoutDB) -> List[Shape]:
        shapes = [
            shape
            for shape in layout.shapes
            if not (shape.purpose == "route_guide" and not self.include_route_guides)
            and not (shape.purpose == "debug_probe" and not self.include_debug_probes)
        ]
        merged: List[Shape] = []
        buckets: Dict[Tuple[str, str | None, str], List[Rect]] = {}
        passthrough: List[Shape] = []
        for shape in shapes:
            if shape.layer in self.tech.vias:
                passthrough.append(shape)
            elif shape.purpose in {"route", "pin"} and shape.rect.area > 0:
                buckets.setdefault((shape.layer, shape.net, shape.purpose), []).append(shape.rect)
            else:
                passthrough.append(shape)
        for (layer, net, purpose), rects in buckets.items():
            for rect in _merge_rectangles(rects):
                merged.append(Shape(layer, rect, purpose, net))
        return passthrough + merged

    def _import_cell_structures(self, layout: LayoutDB) -> Dict[str, bytes]:
        needed = {array.cell for array in layout.cell_arrays}
        needed.update(instance.cell for instance in layout.instances)
        imported: Dict[str, bytes] = {}
        for name in sorted(needed):
            cell = self.tech.cells.get(name)
            if cell is None:
                continue
            if cell.gds_path is not None:
                gds_path = Path(cell.gds_path)
                imported.update(_read_gds_structures(
                    gds_path,
                    self.grid_dbu,
                    _gds_xy_scale(gds_path, self.db_units_per_micron),
                    strip_text=self.strip_imported_text,
                ))
            elif cell.role == "generated_stdcell":
                imported[name] = self._generated_cell_structure(name)
        return _structure_dependency_closure(imported, needed)

    def _generated_cell_structure(self, cell_name: str) -> bytes:
        cell = self.tech.cell(cell_name)
        temp = LayoutDB(cell_name)
        draw_generated_cell(temp, cell_name, Rect(0.0, 0.0, cell.width, cell.height), cell_name)

        stamp = self._stamp()
        data = bytearray()
        data += self._int2_record(0x05, [*stamp, *stamp])
        data += self._str_record(0x06, self._clean_name(cell_name))
        for shape in temp.shapes:
            layer = self.tech.layers.get(shape.layer)
            if layer is None or shape.rect.area <= 0:
                continue
            data += self._boundary(layer.gds_layer, layer.datatype, shape.rect)
        if self.include_cell_pin_labels:
            for pin in generated_cell_pins(cell_name, Rect(0.0, 0.0, cell.width, cell.height)):
                layer = self.tech.layers.get(str(pin["layer"]))
                if layer is None:
                    continue
                data += self._text(layer.gds_layer, layer.datatype, str(pin["name"]), float(pin["x"]), float(pin["y"]))
        data += self._record(0x07, 0x00, b"")
        return bytes(data)

    def _module_overlay(self, layout: LayoutDB) -> bytes:
        layer = self.tech.layers.get("boundary") or self.tech.layers.get("text")
        if layer is None:
            return b""
        data = bytearray()
        width = 0.045
        for shape in layout.shapes:
            if shape.purpose != "module" or shape.rect.area <= 0:
                continue
            rect = shape.rect
            edge = min(width, max(min(rect.width, rect.height) / 8.0, 0.005))
            strips = [
                Rect(rect.x0, rect.y0, rect.x1, rect.y0 + edge),
                Rect(rect.x0, rect.y1 - edge, rect.x1, rect.y1),
                Rect(rect.x0, rect.y0, rect.x0 + edge, rect.y1),
                Rect(rect.x1 - edge, rect.y0, rect.x1, rect.y1),
            ]
            for strip in strips:
                if strip.area > 0:
                    data += self._boundary(layer.gds_layer, layer.datatype, strip)
            label = shape.name or shape.net
            if label:
                data += self._text(layer.gds_layer, layer.datatype, label, rect.center.x, rect.center.y)
        return bytes(data)

    def _stamp(self) -> Tuple[int, int, int, int, int, int]:
        if self.timestamp is not None:
            return self.timestamp
        now = datetime.now()
        return (now.year, now.month, now.day, now.hour, now.minute, now.second)

    def _boundary(self, layer: int, datatype: int, rect: Rect) -> bytes:
        points = [
            (rect.x0, rect.y0),
            (rect.x1, rect.y0),
            (rect.x1, rect.y1),
            (rect.x0, rect.y1),
            (rect.x0, rect.y0),
        ]
        data = bytearray()
        data += self._record(0x08, 0x00, b"")
        data += self._int2_record(0x0D, [layer])
        data += self._int2_record(0x0E, [datatype])
        data += self._xy_record(points)
        data += self._record(0x11, 0x00, b"")
        return bytes(data)

    def _sref(self, cell_name: str, x: float, y: float, mirror: str = "") -> bytes:
        data = bytearray()
        data += self._record(0x0A, 0x00, b"")
        data += self._str_record(0x12, self._clean_name(cell_name))
        if mirror in {"MX", "MY"}:
            data += self._record(0x1A, 0x01, struct.pack(">H", 0x8000))
        if mirror in {"MY", "XY"}:
            data += self._real8_record(0x1C, [180.0])
        data += self._xy_record([(x, y)])
        data += self._record(0x11, 0x00, b"")
        return bytes(data)

    def _text(self, layer: int, texttype: int, text: str, x: float, y: float) -> bytes:
        data = bytearray()
        data += self._record(0x0C, 0x00, b"")
        data += self._int2_record(0x0D, [layer])
        data += self._int2_record(0x16, [texttype])
        data += self._xy_record([(x, y)])
        data += self._str_record(0x19, text)
        data += self._record(0x11, 0x00, b"")
        return bytes(data)

    def _xy_record(self, points: Iterable[Tuple[float, float]]) -> bytes:
        ints = []
        for x, y in points:
            ints.append(self._snap_dbu(round(x * self.db_units_per_micron)))
            ints.append(self._snap_dbu(round(y * self.db_units_per_micron)))
        return self._record(0x10, 0x03, b"".join(struct.pack(">i", value) for value in ints))

    def _manufacturing_grid_dbu(self) -> int:
        target = self.tech.manufacturing_grid * self.db_units_per_micron
        for grid_dbu in range(1, 101):
            ratio = grid_dbu / target
            if abs(ratio - round(ratio)) < 1e-9:
                return grid_dbu
        return max(1, round(target))

    def _snap_dbu(self, value: int) -> int:
        grid = self.grid_dbu
        return round(value / grid) * grid

    def _int2_record(self, record_type: int, values: Iterable[int]) -> bytes:
        return self._record(record_type, 0x02, b"".join(struct.pack(">h", value) for value in values))

    def _real8_record(self, record_type: int, values: Iterable[float]) -> bytes:
        return self._record(record_type, 0x05, b"".join(self._gds_real8(value) for value in values))

    def _str_record(self, record_type: int, value: str) -> bytes:
        payload = value.encode("ascii", errors="ignore")
        if len(payload) % 2:
            payload += b"\0"
        return self._record(record_type, 0x06, payload)

    @staticmethod
    def _record(record_type: int, data_type: int, payload: bytes) -> bytes:
        return struct.pack(">HBB", len(payload) + 4, record_type, data_type) + payload

    @staticmethod
    def _clean_name(name: str) -> str:
        cleaned = "".join(ch if ch.isalnum() or ch in "_$?" else "_" for ch in name)
        return cleaned or "SRAM_TOP"

    @staticmethod
    def _gds_real8(value: float) -> bytes:
        if value == 0:
            return b"\0" * 8
        sign = 0x80 if value < 0 else 0
        value = abs(value)
        exponent = 64
        while value >= 1.0:
            value /= 16.0
            exponent += 1
        while value < 1.0 / 16.0:
            value *= 16.0
            exponent -= 1
        mantissa = int(value * (1 << 56))
        return bytes([sign | exponent]) + mantissa.to_bytes(7, "big")


def _read_gds_structures(path: Path, grid_dbu: int = 1, scale_xy: float = 1.0, strip_text: bool = False) -> Dict[str, bytes]:
    data = path.read_bytes()
    if strip_text:
        data = _strip_gds_text_elements(data)
    structures: Dict[str, bytes] = {}
    offset = 0
    current_start = None
    current_name = None
    while offset + 4 <= len(data):
        size, record_type, _data_type = struct.unpack(">HBB", data[offset : offset + 4])
        if size < 4 or offset + size > len(data):
            break
        payload = data[offset + 4 : offset + size]
        if record_type == 0x05:
            current_start = offset
            current_name = None
        elif record_type == 0x06 and current_start is not None:
            current_name = payload.rstrip(b"\0").decode("ascii", errors="ignore")
        elif record_type == 0x07 and current_start is not None:
            if current_name:
                structures[current_name] = _snap_structure_xy(data[current_start : offset + size], grid_dbu, scale_xy)
            current_start = None
            current_name = None
        offset += size
    return structures


def _gds_xy_scale(path: Path, target_db_units_per_micron: int) -> float:
    source_dbu_microns = _gds_db_unit_microns(path)
    target_dbu_microns = 1.0 / target_db_units_per_micron
    return source_dbu_microns / target_dbu_microns


def _gds_db_unit_microns(path: Path) -> float:
    data = path.read_bytes()
    offset = 0
    while offset + 4 <= len(data):
        size, record_type, _data_type = struct.unpack(">HBB", data[offset : offset + 4])
        if size < 4 or offset + size > len(data):
            break
        payload = data[offset + 4 : offset + size]
        if record_type == 0x03 and len(payload) >= 16:
            db_unit_meters = _parse_gds_real8(payload[8:16])
            if db_unit_meters:
                return db_unit_meters * 1e6
        offset += size
    return 0.001


def _parse_gds_real8(data: bytes) -> float:
    if data == b"\0" * 8:
        return 0.0
    sign = -1.0 if data[0] & 0x80 else 1.0
    exponent = (data[0] & 0x7F) - 64
    mantissa = int.from_bytes(data[1:], "big") / float(1 << 56)
    return sign * mantissa * (16.0**exponent)


def _structure_dependency_closure(structures: Dict[str, bytes], roots: Iterable[str]) -> Dict[str, bytes]:
    """Keep root structures and recursively referenced child structures."""

    selected: Dict[str, bytes] = {}
    pending = [root for root in roots if root in structures]
    seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in seen or name not in structures:
            continue
        seen.add(name)
        selected[name] = structures[name]
        for ref in _structure_references(structures[name]):
            if ref not in seen and ref in structures:
                pending.append(ref)
    return {name: selected[name] for name in sorted(selected)}


def _structure_references(structure: bytes) -> set[str]:
    refs: set[str] = set()
    offset = 0
    in_sref = False
    while offset + 4 <= len(structure):
        size, record_type, _data_type = struct.unpack(">HBB", structure[offset : offset + 4])
        if size < 4 or offset + size > len(structure):
            break
        payload = structure[offset + 4 : offset + size]
        if record_type == 0x0A:
            in_sref = True
        elif record_type == 0x12 and in_sref:
            name = payload.rstrip(b"\0").decode("ascii", errors="ignore")
            if name:
                refs.add(name)
        elif record_type == 0x11:
            in_sref = False
        offset += size
    return refs


def _strip_gds_text_elements(data: bytes) -> bytes:
    result = bytearray()
    offset = 0
    skipping_text = False
    while offset + 4 <= len(data):
        size, record_type, data_type = struct.unpack(">HBB", data[offset : offset + 4])
        if size < 4 or offset + size > len(data):
            result += data[offset:]
            break
        record = data[offset : offset + size]
        if record_type == 0x0C:
            skipping_text = True
        if not skipping_text:
            result += record
        if skipping_text and record_type == 0x11:
            skipping_text = False
        offset += size
    return bytes(result)


def _snap_structure_xy(data: bytes, grid_dbu: int, scale_xy: float = 1.0) -> bytes:
    if grid_dbu <= 1 and abs(scale_xy - 1.0) < 1e-12:
        return data
    result = bytearray(data)
    offset = 0
    while offset + 4 <= len(result):
        size, record_type, data_type = struct.unpack(">HBB", result[offset : offset + 4])
        if size < 4 or offset + size > len(result):
            break
        payload_start = offset + 4
        payload_end = offset + size
        if record_type == 0x10 and data_type == 0x03:
            payload = result[payload_start:payload_end]
            snapped = bytearray()
            for i in range(0, len(payload), 4):
                value = round(struct.unpack(">i", payload[i : i + 4])[0] * scale_xy)
                value = round(value / grid_dbu) * grid_dbu
                snapped += struct.pack(">i", value)
            result[payload_start:payload_end] = snapped
        offset += size
    return bytes(result)


def _merge_rectangles(rects: List[Rect]) -> List[Rect]:
    merged = list(rects)
    changed = True
    while changed:
        changed = False
        next_rects: List[Rect] = []
        used = [False] * len(merged)
        for i, rect in enumerate(merged):
            if used[i]:
                continue
            current = rect
            for j in range(i + 1, len(merged)):
                if used[j]:
                    continue
                candidate = _merge_pair(current, merged[j])
                if candidate is not None:
                    current = candidate
                    used[j] = True
                    changed = True
            used[i] = True
            next_rects.append(current)
        merged = next_rects
    return merged


def _merge_pair(a: Rect, b: Rect) -> Rect | None:
    eps = 1e-9
    same_x = abs(a.x0 - b.x0) < eps and abs(a.x1 - b.x1) < eps
    same_y = abs(a.y0 - b.y0) < eps and abs(a.y1 - b.y1) < eps
    y_touch_or_overlap = not (a.y1 < b.y0 - eps or b.y1 < a.y0 - eps)
    x_touch_or_overlap = not (a.x1 < b.x0 - eps or b.x1 < a.x0 - eps)
    if same_x and y_touch_or_overlap:
        return Rect(a.x0, min(a.y0, b.y0), a.x1, max(a.y1, b.y1))
    if same_y and x_touch_or_overlap:
        return Rect(min(a.x0, b.x0), a.y0, max(a.x1, b.x1), a.y1)
    return None
