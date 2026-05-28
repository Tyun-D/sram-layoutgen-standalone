"""Generated standard-cell style primitives for decoder/control glue."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from .geometry import Instance, LayoutDB, Point, Rect
from .gds_util import inspect_gds_text_records
from .openram_placement import (
    openram_sref_origin,
    placed_bbox_from_openram_origin,
    place_local_point,
    place_local_rect,
    sref_origin_for_bbox,
)

if TYPE_CHECKING:
    from .tech import Tech


GENERATED_CELLS = {
    "gen_inv": (1.20, 1.565, "generated_stdcell"),
    "gen_nand2": (1.65, 1.565, "generated_stdcell"),
    "gen_nand4": (2.60, 1.565, "generated_stdcell"),
    "gen_nor2": (1.65, 1.565, "generated_stdcell"),
    "gen_wl_driver": (1.55, 1.565, "generated_stdcell"),
    "gen_precharge": (0.895, 1.565, "generated_stdcell"),
    "gen_col_mux": (0.895, 1.565, "generated_stdcell"),
    "gen_delay_inv": (1.20, 1.565, "generated_stdcell"),
    "gen_well_tap": (0.895, 1.565, "generated_stdcell"),
}

_EXPECTED_PINS = {
    "gen_inv": {"A", "Z", "gnd", "vdd"},
    "gen_delay_inv": {"A", "Z", "gnd", "vdd"},
    "gen_nand2": {"A", "B", "Z", "gnd", "vdd"},
    "gen_nor2": {"A", "B", "Z", "gnd", "vdd"},
    "gen_nand4": {"A", "B", "C", "D", "Z", "gnd", "vdd"},
    "gen_wl_driver": {"A", "Z", "gnd", "vdd"},
    "gen_precharge": {"BL", "BR", "EN", "gnd", "vdd"},
    "gen_col_mux": {"BL", "BR", "OUT", "OUTB", "SEL", "gnd", "vdd"},
    "gen_well_tap": {"gnd", "vdd"},
}

_PIN_ALIASES = {
    "a": "A",
    "b": "B",
    "c": "C",
    "d": "D",
    "z": "Z",
    "bl": "BL",
    "br": "BR",
    "bl_out": "OUT",
    "br_out": "OUTB",
    "out": "OUT",
    "outb": "OUTB",
    "sel": "SEL",
    "en": "EN",
    "en_bar": "EN",
    "gnd": "gnd",
    "vdd": "vdd",
}


@lru_cache(maxsize=None)
def _gds_pin_records(gds_path: str) -> tuple[dict[str, object], ...]:
    return tuple(inspect_gds_text_records(Path(gds_path)))


def _canonical_pin_name(label: str) -> str | None:
    return _PIN_ALIASES.get(label.strip().lower())


def _layer_name_from_gds(tech: Tech, gds_layer: int, datatype: int) -> str | None:
    for name, layer in tech.layers.items():
        if layer.gds_layer == gds_layer and layer.datatype == datatype:
            return name
    return None


def _transform_gds_point(cell, x: float, y: float, origin_x: float, origin_y: float, mirror: str) -> tuple[float, float]:
    if mirror in {"MY", "XY"}:
        x = -x
    if mirror in {"MX", "XY"}:
        y = -y
    return origin_x + x, origin_y + y


def generated_instance_pins(tech: Tech, instance: Instance) -> list[dict[str, object]]:
    """Return pin access points for a placed generated macro instance.

    When a replacement GDS is available, pin coordinates are read from its
    TEXT labels and transformed with the same OpenRAM SREF origin used when
    writing the instance. This keeps routing tied to the replaceable brick
    itself instead of a stale hand-written abstract.
    """

    cell = tech.cell(instance.cell)
    expected = _EXPECTED_PINS.get(instance.cell)
    if cell.gds_path is None:
        return generated_cell_pins(instance.cell, instance.rect, instance.mirror)

    if instance.placement_mode == "openram_origin" and instance.origin is not None:
        origin_x, origin_y = openram_sref_origin(cell, instance.origin.x, instance.origin.y, instance.mirror)
    else:
        origin_x, origin_y = sref_origin_for_bbox(cell, instance.rect.x0, instance.rect.y0, instance.mirror)

    pins: dict[str, dict[str, object]] = {}
    for record in _gds_pin_records(str(cell.gds_path)):
        pin_name = _canonical_pin_name(str(record["text"]))
        if pin_name is None or (expected is not None and pin_name not in expected):
            continue
        if pin_name in pins:
            continue
        layer_name = _layer_name_from_gds(tech, int(record["layer"]), int(record["datatype"]))
        if layer_name is None:
            continue
        x, y = _transform_gds_point(
            cell,
            float(record["x"]),
            float(record["y"]),
            origin_x,
            origin_y,
            instance.mirror,
        )
        pins[pin_name] = {"name": pin_name, "layer": layer_name, "x": x, "y": y, "source": "gds_text"}

    return [pins[name] for name in sorted(pins)]

def add_generated_cell(
    db: LayoutDB,
    tech: Tech,
    name: str,
    cell_name: str,
    x: float,
    y: float,
    role: str,
    mirror: str = "R0",
    placement_mode: str = "bbox",
) -> Rect:
    cell = tech.cell(cell_name)
    effective_mode = placement_mode if cell.gds_path is not None else "bbox"
    if effective_mode == "openram_origin":
        rect = placed_bbox_from_openram_origin(cell, x, y, mirror)
        origin = Point(x, y)
    else:
        rect = Rect(x, y, x + cell.width, y + cell.height)
        origin = None
    db.add_instance(Instance(name, cell_name, rect, role, mirror, placement_mode=effective_mode, origin=origin))
    if cell.gds_path is None and cell.role == "generated_stdcell":
        draw_generated_cell(db, cell_name, rect, name, mirror)
    return rect


def generated_cell_pins(cell_name: str, rect: Rect, mirror: str = "R0") -> list[dict[str, object]]:
    x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
    w = rect.width
    h = rect.height

    def pin(name: str, layer: str, x: float, y: float) -> dict[str, object]:
        return {"name": name, "layer": layer, "x": x, "y": y}

    def local_pin(name: str, layer: str, x: float, y: float) -> dict[str, object]:
        px, py = place_local_point(x, y, rect, mirror)
        return pin(name, layer, px, py)

    pins = [
        local_pin("gnd", "m1", w * 0.50, 0.12),
        local_pin("vdd", "m1", w * 0.50, h - 0.12),
    ]
    if cell_name in {"gen_inv", "gen_delay_inv", "gen_wl_driver"}:
        pins.extend([
            local_pin("A", "m1", w * 0.28, h * 0.50),
            local_pin("Z", "m2" if cell_name == "gen_wl_driver" else "m1", w - 0.18, h * 0.50),
        ])
    elif cell_name in {"gen_nand2", "gen_nor2"}:
        pins.extend([
            local_pin("A", "m1", w * 0.34, h * 0.50),
            local_pin("B", "m1", w * 0.66, h * 0.50),
            local_pin("Z", "m1", w - 0.18, h * 0.50),
        ])
    elif cell_name == "gen_nand4":
        pins.extend([
            local_pin("A", "m1", w * 0.20, h * 0.50),
            local_pin("B", "m1", w * 0.40, h * 0.50),
            local_pin("C", "m1", w * 0.60, h * 0.50),
            local_pin("D", "m1", w * 0.80, h * 0.50),
            local_pin("Z", "m1", w - 0.18, h * 0.50),
        ])
    elif cell_name == "gen_precharge":
        pins.extend([
            local_pin("BL", "m2", 0.21, h * 0.50),
            local_pin("BR", "m2", w - 0.21, h * 0.50),
            local_pin("EN", "m1", w * 0.50, h * 0.50),
        ])
    elif cell_name == "gen_col_mux":
        pins.extend([
            local_pin("BL", "m2", 0.21, h * 0.50),
            local_pin("BR", "m2", w - 0.21, h * 0.50),
            local_pin("OUT", "m3", w * 0.50, 0.60),
            local_pin("SEL", "m1", w * 0.50, h - 0.28),
        ])
    return pins


def draw_generated_cell(db: LayoutDB, cell_name: str, rect: Rect, name: str, mirror: str = "R0") -> None:
    x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
    w = rect.width
    h = rect.height
    rail = 0.14
    well_mid = h * 0.48

    def add(layer: str, local: Rect, purpose: str = "stdcell", net: str | None = None, suffix: str = "") -> None:
        db.add_shape(layer, place_local_rect(local, rect, mirror), purpose, net=net, name=f"{name}_{suffix}" if suffix else name)

    # Wells and implants.
    add("pwell", Rect(0, 0, w, well_mid), suffix="pwell")
    add("nwell", Rect(0, well_mid, w, h), suffix="nwell")
    add("nimplant", Rect(0.08, 0.26, w - 0.08, well_mid - 0.10), suffix="nimp")
    add("pimplant", Rect(0.08, well_mid + 0.10, w - 0.08, h - 0.26), suffix="pimp")

    # Power rails.
    add("m1", Rect(0, 0.05, w, 0.05 + rail), net="gnd", suffix="gnd")
    add("m1", Rect(0, h - 0.05 - rail, w, h - 0.05), net="vdd", suffix="vdd")

    # Active regions.
    nact = Rect(0.16, 0.36, w - 0.16, well_mid - 0.18)
    pact = Rect(0.16, well_mid + 0.18, w - 0.16, h - 0.36)
    add("active", nact, suffix="nactive")
    add("active", pact, suffix="pactive")

    gate_count = 1 if cell_name in {"gen_inv", "gen_wl_driver", "gen_delay_inv", "gen_well_tap"} else 4 if cell_name == "gen_nand4" else 2
    for i in range(gate_count):
        gx = w * (i + 1) / (gate_count + 1)
        add("poly", Rect(gx - 0.035, nact.y0 - 0.12, gx + 0.035, pact.y1 + 0.12), suffix=f"poly{i}")

    # Contact/via-like landing shapes and local output trunk.
    for cx in (0.28, w - 0.28):
        ncont = Rect(cx - 0.035, nact.y0 + 0.06, cx + 0.035, nact.y0 + 0.13)
        pcont = Rect(cx - 0.035, pact.y1 - 0.13, cx + 0.035, pact.y1 - 0.06)
        add("contact", ncont, suffix="ncont")
        add("contact", pcont, suffix="pcont")
        add("m1", ncont.inflate(0.04), suffix="ncont_m1")
        add("m1", pcont.inflate(0.04), suffix="pcont_m1")
    out_x = w - 0.18
    add("m1", Rect(out_x - 0.04, nact.y0, out_x + 0.04, pact.y1), suffix="out")

    if cell_name == "gen_wl_driver":
        add("m2", Rect(0.10, h * 0.50 - 0.045, w, h * 0.50 + 0.045), suffix="wl_out")
    elif cell_name == "gen_precharge":
        mid = w / 2.0
        add("m2", Rect(0.16, 0.26, 0.26, h - 0.20), suffix="bl")
        add("m2", Rect(w - 0.26, 0.26, w - 0.16, h - 0.20), suffix="br")
        add("poly", Rect(mid - 0.035, 0.20, mid + 0.035, h - 0.20), suffix="en")
        add("m1", Rect(0.20, h - 0.25, w - 0.20, h - 0.12), net="vdd", suffix="pc_vdd")
    elif cell_name == "gen_col_mux":
        add("m2", Rect(0.16, 0.12, 0.26, h - 0.12), suffix="in0")
        add("m2", Rect(w - 0.26, 0.12, w - 0.16, h - 0.12), suffix="in1")
        add("m3", Rect(0.18, 0.55, w - 0.18, 0.65), suffix="out")
    elif cell_name == "gen_well_tap":
        add("contact", Rect(0.20, 0.30, 0.27, 0.37), suffix="ptap")
        add("contact", Rect(w - 0.27, h - 0.37, w - 0.20, h - 0.30), suffix="ntap")
        add("m1", Rect(0.14, 0.24, 0.33, 0.43), net="gnd", suffix="ptap_m1")
        add("m1", Rect(w - 0.33, h - 0.43, w - 0.14, h - 0.24), net="vdd", suffix="ntap_m1")

    pin_w = 0.10
    for pin in generated_cell_pins(cell_name, rect, mirror):
        x = float(pin["x"])
        y = float(pin["y"])
        db.add_shape(str(pin["layer"]), Rect(x - pin_w / 2, y - pin_w / 2, x + pin_w / 2, y + pin_w / 2), "stdcell", str(pin["name"]), f"{name}_{pin['name']}_pin")
