"""Read-only GDS label/shape and power-rail audit helpers.

The parser here is intentionally small: it extracts enough GDSII structure,
TEXT, BOUNDARY, and PATH data to audit pin labels and nearby shapes without
depending on KLayout, gdspy, or gdstk.  It never writes GDS and it does not
connect to placement or routing.
"""

from __future__ import annotations

import json
import math
import struct
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


RAIL_ABUTMENT_READY = "rail_abutment_ready"
RAIL_NEEDS_MANUAL_REVIEW = "rail_needs_manual_review"
RAIL_NOT_BOUNDARY_ALIGNED = "rail_not_boundary_aligned"
RAIL_MISSING_PIN = "rail_missing_pin"
RAIL_UNKNOWN = "rail_unknown"


@dataclass(frozen=True)
class BBox:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return max(0.0, self.x1 - self.x0)

    @property
    def height(self) -> float:
        return max(0.0, self.y1 - self.y0)

    def contains_point(self, x: float, y: float, tol: float = 0.0) -> bool:
        return self.x0 - tol <= x <= self.x1 + tol and self.y0 - tol <= y <= self.y1 + tol

    def distance_to_boundary(self, x: float, y: float) -> float:
        return min(abs(x - self.x0), abs(x - self.x1), abs(y - self.y0), abs(y - self.y1))

    def side_for_point(self, x: float, y: float) -> tuple[str, float]:
        distances = {
            "left": abs(x - self.x0),
            "right": abs(x - self.x1),
            "bottom": abs(y - self.y0),
            "top": abs(y - self.y1),
        }
        side, distance = min(distances.items(), key=lambda item: item[1])
        if distance > max(self.width, self.height, 1.0) * 0.30:
            return "internal", distance
        return side, distance

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class GdsText:
    text: str
    layer: int | None
    texttype: int | None
    x: float
    y: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GdsShape:
    kind: str
    layer: int | None
    datatype: int | None
    bbox: BBox

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["bbox"] = self.bbox.to_dict()
        return data


@dataclass(frozen=True)
class PinAudit:
    pin_name: str
    canonical_pin: str
    pin_layer: str
    pin_text_position: dict[str, float] | None
    pin_shape_bbox: dict[str, float] | None
    pin_side: str
    distance_to_boundary: float | None
    is_power_pin: bool
    is_signal_pin: bool
    pin_shape_source: str
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PowerRailAudit:
    has_vdd: bool
    has_gnd: bool
    vdd_side: str
    gnd_side: str
    vdd_boundary_touch: bool
    gnd_boundary_touch: bool
    vdd_orientation: str
    gnd_orientation: str
    can_share_left_right: bool
    can_share_top_bottom: bool
    rail_continuity_status: str
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MacroGdsAudit:
    macro_name: str
    gds_path: str | None
    spice_path: str | None
    bbox: dict[str, float] | None
    width: float | None
    height: float | None
    labels: tuple[dict[str, Any], ...]
    pins: tuple[PinAudit, ...]
    power_rail_audit: PowerRailAudit
    abutment_readiness: str
    semantic_flags: tuple[str, ...] = ()
    gds_reader_status: str = "ok"
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pins"] = [pin.to_dict() for pin in self.pins]
        data["power_rail_audit"] = self.power_rail_audit.to_dict()
        return data


@dataclass
class _Element:
    kind: str
    layer: int | None = None
    datatype: int | None = None
    xy: tuple[tuple[int, int], ...] = ()
    text: str | None = None
    texttype: int | None = None
    width: int | None = None


def audit_macros(tech_dir: str | Path, aliases_path: str | Path | None = None, focus: Iterable[str] | None = None) -> dict[str, Any]:
    tech = Path(tech_dir)
    aliases = _load_aliases(aliases_path or tech / "openyield_macro_aliases.json")
    replacement = _load_replacement_macros(tech)
    macros = _macro_inventory(tech, aliases, replacement, focus)
    audits = [audit_macro(tech, item) for item in macros]
    return {
        "tech_dir": str(tech.resolve()),
        "gds_reader": "internal_gdsii_text_boundary_parser",
        "gds_reader_limitations": [
            "Extracts TEXT, BOUNDARY, and PATH bboxes only.",
            "Does not flatten hierarchy or prove electrical connectivity.",
            "Pin shapes are inferred from same-layer shapes containing or near the TEXT label.",
        ],
        "macro_count": len(audits),
        "audited_macros": [audit.to_dict() for audit in audits],
        "summary": _summary(audits),
    }


def audit_macro(tech_dir: Path, item: dict[str, Any]) -> MacroGdsAudit:
    macro = str(item["macro_name"])
    gds_rel = item.get("gds")
    spice_rel = item.get("spice")
    expected = _expected_pin_map(item)
    gds_path = tech_dir / str(gds_rel) if gds_rel else None
    notes: list[str] = list(item.get("notes") or ())
    labels: tuple[GdsText, ...] = ()
    shapes: tuple[GdsShape, ...] = ()
    bbox: BBox | None = None
    status = "ok"
    if not gds_path or not gds_path.exists():
        status = "gds_missing"
        notes.append("GDS file is missing.")
    else:
        try:
            labels, shapes, bbox = read_gds_labels_and_shapes(gds_path)
            if not labels:
                notes.append("No TEXT labels were found in GDS; SPICE/alias metadata is used as fallback.")
        except Exception as exc:
            status = "gds_reader_unavailable"
            notes.append(f"Internal GDS parser failed: {exc}")
    if not labels:
        labels = tuple(_fallback_labels_from_spice(tech_dir / str(spice_rel) if spice_rel else None))
    if bbox is None:
        bbox = _bbox_from_replacement_or_unknown(item)
    pins = tuple(_pin_audit(pin, canonical, labels, shapes, bbox) for pin, canonical in expected.items())
    power = _power_rail_audit(pins, bbox, item)
    readiness = _abutment_readiness(macro, power, pins, item)
    semantic = _semantic_flags(macro, pins, item)
    return MacroGdsAudit(
        macro_name=macro,
        gds_path=str(gds_path) if gds_path else None,
        spice_path=str(tech_dir / str(spice_rel)) if spice_rel else None,
        bbox=bbox.to_dict() if bbox else None,
        width=bbox.width if bbox else None,
        height=bbox.height if bbox else None,
        labels=tuple(label.to_dict() for label in labels),
        pins=pins,
        power_rail_audit=power,
        abutment_readiness=readiness,
        semantic_flags=semantic,
        gds_reader_status=status,
        notes=tuple(notes),
    )


def read_gds_labels_and_shapes(path: str | Path) -> tuple[tuple[GdsText, ...], tuple[GdsShape, ...], BBox | None]:
    data = Path(path).read_bytes()
    unit_um = 0.001
    current: _Element | None = None
    labels: list[GdsText] = []
    shapes: list[GdsShape] = []
    all_points: list[tuple[float, float]] = []
    pos = 0
    while pos + 4 <= len(data):
        rec_len = int.from_bytes(data[pos:pos + 2], "big")
        if rec_len < 4:
            break
        rec_type = data[pos + 2]
        data_type = data[pos + 3]
        payload = data[pos + 4:pos + rec_len]
        pos += rec_len
        if rec_type == 0x03 and data_type == 0x05 and len(payload) >= 16:
            _uu, meter_per_dbu = _gds_real8(payload[:8]), _gds_real8(payload[8:16])
            if meter_per_dbu > 0:
                unit_um = meter_per_dbu * 1e6
        elif rec_type in {0x08, 0x09, 0x0C}:
            current = _Element({0x08: "boundary", 0x09: "path", 0x0C: "text"}[rec_type])
        elif rec_type == 0x0D and current is not None:
            current.layer = _int2(payload)
        elif rec_type in {0x0E, 0x16} and current is not None:
            value = _int2(payload)
            if rec_type == 0x16:
                current.texttype = value
            else:
                current.datatype = value
        elif rec_type == 0x0F and current is not None and len(payload) >= 4:
            current.width = int.from_bytes(payload[:4], "big", signed=True)
        elif rec_type == 0x10 and current is not None:
            current.xy = _xy(payload)
        elif rec_type == 0x19 and current is not None:
            current.text = payload.rstrip(b"\0").decode("ascii", errors="replace")
        elif rec_type == 0x11 and current is not None:
            if current.kind == "text" and current.text and current.xy:
                x, y = current.xy[0]
                labels.append(GdsText(current.text, current.layer, current.texttype, x * unit_um, y * unit_um))
                all_points.append((x * unit_um, y * unit_um))
            elif current.kind in {"boundary", "path"} and current.xy:
                pts = tuple((x * unit_um, y * unit_um) for x, y in current.xy)
                bbox = _bbox_for_points(pts)
                if current.kind == "path" and current.width:
                    half = abs(current.width * unit_um) / 2.0
                    bbox = BBox(bbox.x0 - half, bbox.y0 - half, bbox.x1 + half, bbox.y1 + half)
                shapes.append(GdsShape(current.kind, current.layer, current.datatype, bbox))
                all_points.extend(pts)
            current = None
    return tuple(labels), tuple(shapes), _bbox_for_points(all_points) if all_points else None


def _pin_audit(pin_name: str, canonical: str, labels: tuple[GdsText, ...], shapes: tuple[GdsShape, ...], bbox: BBox | None) -> PinAudit:
    label = _match_label(pin_name, canonical, labels)
    shape = _nearest_shape(label, shapes) if label else None
    side = "unknown"
    distance = None
    position = None
    shape_bbox = None
    source = "missing"
    notes: list[str] = []
    if label:
        position = {"x": label.x, "y": label.y}
        if bbox and not (math.isnan(label.x) or math.isnan(label.y)):
            side, distance = bbox.side_for_point(label.x, label.y)
        source = "text_label_only"
    else:
        notes.append("Expected pin label not found in GDS TEXT labels.")
    if shape:
        shape_bbox = shape.bbox.to_dict()
        source = "label_plus_shape"
        if side == "internal" and bbox:
            side, distance = bbox.side_for_point((shape.bbox.x0 + shape.bbox.x1) / 2.0, (shape.bbox.y0 + shape.bbox.y1) / 2.0)
    return PinAudit(
        pin_name=pin_name,
        canonical_pin=canonical,
        pin_layer=f"{label.layer}/texttype{label.texttype}" if label else "unknown",
        pin_text_position=position,
        pin_shape_bbox=shape_bbox,
        pin_side=side,
        distance_to_boundary=distance,
        is_power_pin=canonical in {"vdd", "gnd"},
        is_signal_pin=canonical not in {"vdd", "gnd"},
        pin_shape_source=source,
        notes=tuple(notes),
    )


def _power_rail_audit(pins: tuple[PinAudit, ...], bbox: BBox | None, item: dict[str, Any]) -> PowerRailAudit:
    vdd = next((pin for pin in pins if pin.canonical_pin == "vdd"), None)
    gnd = next((pin for pin in pins if pin.canonical_pin == "gnd"), None)
    expects_gnd = any(pin.canonical_pin == "gnd" for pin in pins)
    notes: list[str] = []
    if not vdd or (expects_gnd and not gnd):
        status = RAIL_MISSING_PIN
        notes.append("One or both power pins are missing from the GDS labels or expected pin map.")
    elif not expects_gnd:
        status = RAIL_NEEDS_MANUAL_REVIEW
        notes.append("This macro does not require a GND pin in the current contract; shared rail use still needs manual review.")
    elif vdd.pin_shape_source != "label_plus_shape" or gnd.pin_shape_source != "label_plus_shape":
        status = RAIL_NEEDS_MANUAL_REVIEW
        notes.append("Power pins are label-only or lack matching shapes; rail continuity is not proven.")
    elif vdd.pin_side in {"top", "bottom", "left", "right"} and gnd.pin_side in {"top", "bottom", "left", "right"}:
        status = RAIL_ABUTMENT_READY if str(item.get("aggregation_hint")) == "abutment_ready" else RAIL_NEEDS_MANUAL_REVIEW
    else:
        status = RAIL_NOT_BOUNDARY_ALIGNED
    can_lr = status == RAIL_ABUTMENT_READY and {vdd.pin_side if vdd else "", gnd.pin_side if gnd else ""} & {"left", "right"}
    can_tb = status == RAIL_ABUTMENT_READY and {vdd.pin_side if vdd else "", gnd.pin_side if gnd else ""} & {"top", "bottom"}
    return PowerRailAudit(
        has_vdd=bool(vdd and vdd.pin_shape_source != "missing"),
        has_gnd=bool(gnd and gnd.pin_shape_source != "missing"),
        vdd_side=vdd.pin_side if vdd else "missing",
        gnd_side=gnd.pin_side if gnd else "missing",
        vdd_boundary_touch=bool(vdd and vdd.pin_side != "internal" and (vdd.distance_to_boundary or 0.0) <= _boundary_tol(bbox)),
        gnd_boundary_touch=bool(gnd and gnd.pin_side != "internal" and (gnd.distance_to_boundary or 0.0) <= _boundary_tol(bbox)),
        vdd_orientation=_orientation(vdd),
        gnd_orientation=_orientation(gnd),
        can_share_left_right=bool(can_lr),
        can_share_top_bottom=bool(can_tb),
        rail_continuity_status=status,
        notes=tuple(notes),
    )


def _abutment_readiness(macro: str, power: PowerRailAudit, pins: tuple[PinAudit, ...], item: dict[str, Any]) -> str:
    hint = str(item.get("aggregation_hint") or "")
    if power.rail_continuity_status == RAIL_MISSING_PIN:
        return "not_abutment_ready"
    if hint == "abutment_ready" and power.rail_continuity_status in {RAIL_ABUTMENT_READY, RAIL_NEEDS_MANUAL_REVIEW}:
        return "unknown_need_gds_pin_audit" if power.rail_continuity_status != RAIL_ABUTMENT_READY else "abutment_ready"
    if macro.startswith(("cell_", "dummy_cell", "replica_cell")):
        return "unknown_need_gds_pin_audit"
    return "not_abutment_ready" if power.rail_continuity_status == RAIL_MISSING_PIN else "unknown_need_gds_pin_audit"


def _semantic_flags(macro: str, pins: tuple[PinAudit, ...], item: dict[str, Any]) -> tuple[str, ...]:
    flags: list[str] = []
    expected = {pin.canonical_pin: pin for pin in pins}
    if macro == "sense_amp":
        if expected.get("bl") and expected["bl"].pin_shape_source != "missing":
            flags.append("senseamp_in_to_bl_confirmed")
        if expected.get("br") and expected["br"].pin_shape_source != "missing":
            flags.append("senseamp_inb_to_br_confirmed")
        if expected.get("dout") and expected["dout"].pin_shape_source != "missing":
            flags.append("senseamp_q_to_dout_confirmed")
        if not expected.get("dout_b") or expected["dout_b"].pin_shape_source == "missing":
            flags.append("architecture_adapter_required")
            flags.append("senseamp_qb_dout_b_missing")
    if macro == "gen_wl_driver":
        if not expected.get("wordline_enable") or expected["wordline_enable"].pin_shape_source == "missing":
            flags.append("needs_semantic_confirmation")
            flags.append("wordline_driver_b_pin_missing")
    if macro == "gen_col_mux":
        if not expected.get("vdd") or expected["vdd"].pin_shape_source == "missing":
            flags.append("missing_power_metadata")
    return tuple(flags)


def _expected_pin_map(item: dict[str, Any]) -> dict[str, str]:
    macro = str(item.get("macro_name") or item.get("name") or "")
    special = {
        "gen_col_mux": {
            "VDD": "vdd",
            "gnd": "gnd",
            "BL": "bl",
            "BR": "br",
            "OUT": "mux_out",
            "OUTB": "mux_out_b",
            "SEL": "column_select",
        },
        "gen_wl_driver": {
            "vdd": "vdd",
            "gnd": "gnd",
            "A": "decoder_input",
            "B": "wordline_enable",
            "Z": "wl",
        },
        "gen_precharge": {
            "vdd": "vdd",
            "EN": "precharge_enb",
            "BL": "bl",
            "BR": "br",
        },
        "gen_nand2": {
            "vdd": "vdd",
            "gnd": "gnd",
            "A": "a",
            "B": "b",
            "Z": "z",
        },
        "gen_nand4": {
            "vdd": "vdd",
            "gnd": "gnd",
            "A": "a",
            "B": "b",
            "C": "c",
            "D": "d",
            "Z": "z",
        },
    }
    if macro in special:
        return special[macro]
    aliases = item.get("pin_aliases") or {}
    if aliases:
        result: dict[str, str] = {}
        for original, canonical in aliases.items():
            if canonical not in result.values():
                result[str(original)] = str(canonical)
        return result
    return {str(pin["name"]): _canonical_default(str(pin["name"])) for pin in item.get("pins", []) if pin.get("name")}


def _load_aliases(path: str | Path) -> dict[str, dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return {}
    payload = json.loads(p.read_text(encoding="utf-8"))
    return {str(item.get("macro_name")): item for item in payload.get("aliases", []) if item.get("macro_name")}


def _load_replacement_macros(tech_dir: Path) -> dict[str, dict[str, Any]]:
    path = tech_dir / "replacement_macros.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(item.get("name")): item for item in payload.get("macros", [])}


def _macro_inventory(tech: Path, aliases: dict[str, dict[str, Any]], replacement: dict[str, dict[str, Any]], focus: Iterable[str] | None) -> list[dict[str, Any]]:
    names = set(focus or [])
    names.update(aliases)
    names.update(replacement)
    items = []
    for name in sorted(names):
        item = dict(replacement.get(name) or {})
        item.update(aliases.get(name) or {})
        item.setdefault("macro_name", name)
        item.setdefault("gds", _find_rel(tech / "gds_lib", f"{name}.gds", tech))
        item.setdefault("spice", _find_rel(tech / "sp_lib", f"{name}.sp", tech))
        if item.get("spice") and "pin_aliases" not in item:
            item["pins"] = [{"name": pin} for pin in _spice_pins(tech / str(item["spice"]))]
        items.append(item)
    return items


def _fallback_labels_from_spice(path: Path | None) -> tuple[GdsText, ...]:
    if not path or not path.exists():
        return ()
    return tuple(GdsText(pin, None, None, math.nan, math.nan) for pin in _spice_pins(path))


def _spice_pins(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.strip().split()
        if parts and parts[0].lower() == ".subckt" and len(parts) > 2:
            return tuple(parts[2:])
    return ()


def _summary(audits: list[MacroGdsAudit]) -> dict[str, Any]:
    return {
        "rail_status_counts": _count(audits, lambda item: item.power_rail_audit.rail_continuity_status),
        "abutment_readiness_counts": _count(audits, lambda item: item.abutment_readiness),
        "macros_ready_for_aggregation": [item.macro_name for item in audits if item.abutment_readiness == "abutment_ready"],
        "macros_need_manual_confirmation": [
            item.macro_name
            for item in audits
            if item.abutment_readiness != "abutment_ready" or item.semantic_flags
        ],
        "semantic_flags": {item.macro_name: item.semantic_flags for item in audits if item.semantic_flags},
    }


def _match_label(pin_name: str, canonical: str, labels: tuple[GdsText, ...]) -> GdsText | None:
    candidates = {pin_name, canonical, pin_name.lower(), canonical.lower(), pin_name.upper(), canonical.upper()}
    aliases = {
        "gnd": {"gnd", "GND", "VSS", "vss"},
        "vdd": {"vdd", "VDD"},
        "br": {"br", "BR", "BLB", "blb"},
        "rbl": {"rbl", "RBL", "bl", "BL"},
        "rblb": {"rblb", "RBLB", "br", "BR"},
        "sense_enable": {"en", "EN", "sense_enable"},
        "write_enable": {"en", "EN", "write_enable"},
        "dout": {"dout", "DOUT", "Q", "q", "out", "OUT"},
        "dout_b": {"dout_b", "DOUT_B", "QB", "qb", "outb", "OUTB"},
        "mux_out": {"OUT", "out", "SA_IN", "sa_in", "bl_out", "BL_OUT"},
        "mux_out_b": {"OUTB", "outb", "SA_INB", "sa_inb", "br_out", "BR_OUT"},
        "column_select": {"SEL", "sel", "SEL0", "sel0"},
        "precharge_enb": {"EN", "en", "ENB", "enb", "PRE", "pre", "p_en_bar", "en_bar"},
        "wordline_enable": {"B", "b", "wl_en"},
        "decoder_input": {"A", "a"},
        "wl": {"wl", "WL", "Z", "z"},
    }.get(canonical, set())
    candidates.update(aliases)
    normalized = {name.lower() for name in candidates}
    for label in labels:
        if label.text.lower() in normalized:
            return label
    return None


def _nearest_shape(label: GdsText | None, shapes: tuple[GdsShape, ...]) -> GdsShape | None:
    if label is None or math.isnan(label.x) or math.isnan(label.y):
        return None
    same_layer = [shape for shape in shapes if shape.layer == label.layer]
    for shape in same_layer:
        if shape.bbox.contains_point(label.x, label.y, tol=0.02):
            return shape
    if same_layer:
        return min(same_layer, key=lambda shape: _bbox_point_distance(shape.bbox, label.x, label.y))
    return None


def _bbox_point_distance(bbox: BBox, x: float, y: float) -> float:
    dx = max(bbox.x0 - x, 0.0, x - bbox.x1)
    dy = max(bbox.y0 - y, 0.0, y - bbox.y1)
    return math.hypot(dx, dy)


def _bbox_for_points(points: Iterable[tuple[float, float]]) -> BBox:
    pts = tuple(points)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return BBox(min(xs), min(ys), max(xs), max(ys))


def _bbox_from_replacement_or_unknown(item: dict[str, Any]) -> BBox:
    width = float(item.get("width") or 0.0)
    height = float(item.get("height") or 0.0)
    return BBox(0.0, 0.0, width, height)


def _orientation(pin: PinAudit | None) -> str:
    if not pin or not pin.pin_shape_bbox:
        return "unknown"
    bbox = pin.pin_shape_bbox
    return "horizontal" if (bbox["x1"] - bbox["x0"]) >= (bbox["y1"] - bbox["y0"]) else "vertical"


def _boundary_tol(bbox: BBox | None) -> float:
    if not bbox:
        return 0.0
    return max(0.02, min(bbox.width, bbox.height, 1.0) * 0.05)


def _canonical_default(name: str) -> str:
    low = name.lower()
    if low == "vss":
        return "gnd"
    if low == "blb":
        return "br"
    return low


def _find_rel(root: Path, filename: str, tech: Path) -> str | None:
    matches = list(root.glob(f"**/{filename}"))
    if not matches:
        return None
    return matches[0].relative_to(tech).as_posix()


def _count(items: Iterable[MacroGdsAudit], fn: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        key = str(fn(item))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _int2(payload: bytes) -> int | None:
    if len(payload) < 2:
        return None
    return int.from_bytes(payload[:2], "big", signed=True)


def _xy(payload: bytes) -> tuple[tuple[int, int], ...]:
    points = []
    for idx in range(0, len(payload) - 7, 8):
        x = int.from_bytes(payload[idx:idx + 4], "big", signed=True)
        y = int.from_bytes(payload[idx + 4:idx + 8], "big", signed=True)
        points.append((x, y))
    return tuple(points)


def _gds_real8(data: bytes) -> float:
    if not data or data == b"\0" * 8:
        return 0.0
    b0 = data[0]
    sign = -1 if (b0 & 0x80) else 1
    exponent = (b0 & 0x7F) - 64
    mantissa = int.from_bytes(data[1:8], "big") / float(1 << 56)
    return sign * mantissa * (16 ** exponent)
