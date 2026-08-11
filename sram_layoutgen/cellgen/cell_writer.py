from __future__ import annotations

from pathlib import Path

import gdstk

from .mos_graph import MosDevice, TopologyLock


LAYER = {
    "active": 1,
    "pwell": 2,
    "nwell": 3,
    "nimplant": 4,
    "pimplant": 5,
    "vtg": 6,
    "poly": 9,
    "contact": 10,
    "m1": 11,
    "text": 239,
}


def _rect(cell: gdstk.Cell, layer: int, x1: float, y1: float, x2: float, y2: float) -> None:
    cell.add(gdstk.rectangle((x1, y1), (x2, y2), layer=layer, datatype=0))


def _label(cell: gdstk.Cell, text: str, x: float, y: float) -> None:
    cell.add(gdstk.Label(text, (x, y), layer=LAYER["text"], texttype=0))


def _draw_mos(cell: gdstk.Cell, dev: MosDevice, x: float, y: float) -> dict[str, tuple[float, float]]:
    implant = LAYER["pimplant"] if dev.type == "PMOS" else LAYER["nimplant"]
    width = max(0.09, dev.w_nm / 1000.0)
    active_y1 = y
    active_y2 = y + width
    active_x1 = x
    active_x2 = x + 0.60
    gate_x1 = x + 0.25
    gate_x2 = x + 0.30
    _rect(cell, LAYER["active"], active_x1, active_y1, active_x2, active_y2)
    _rect(cell, implant, active_x1, active_y1, gate_x1 - 0.09, active_y2)
    _rect(cell, implant, gate_x2 + 0.09, active_y1, active_x2, active_y2)
    _rect(cell, LAYER["poly"], gate_x1, active_y1 - 0.08, gate_x2, active_y2 + 0.08)
    sy = active_y1 + 0.5 * width - 0.0325
    dy = sy
    sx = active_x1 + 0.085
    dx = active_x2 - 0.165
    for cx in (sx, dx):
        _rect(cell, LAYER["contact"], cx, sy, cx + 0.065, sy + 0.065)
        _rect(cell, LAYER["m1"], cx - 0.04, sy - 0.04, cx + 0.105, sy + 0.105)
    gy = active_y2 + 0.16 if dev.type == "NMOS" else active_y1 - 0.225
    _rect(cell, LAYER["poly"], gate_x1, min(active_y2, gy), gate_x2, max(active_y1, gy + 0.065))
    _rect(cell, LAYER["poly"], gate_x1 - 0.02, gy, gate_x2 + 0.005, gy + 0.085)
    _label(cell, dev.g, gate_x1 + 0.0175, gy + 0.0425)
    return {
        "S": (sx + 0.0325, sy + 0.0325),
        "D": (dx + 0.0325, dy + 0.0325),
        "G": (gate_x1 + 0.0175, gy + 0.0425),
    }


def write_mos_cell(lock: TopologyLock, placements: list[dict[str, object]], out: Path, top_name: str) -> dict[str, object]:
    lib = gdstk.Library(unit=1e-6, precision=2.5e-9)
    cell = lib.new_cell(top_name)
    max_x = max(float(p["x"]) + 0.80 for p in placements) if placements else 2.0
    _rect(cell, LAYER["m1"], 0, 0, max_x + 0.80, 0.08)
    _rect(cell, LAYER["m1"], 0, 2.30, max_x + 0.80, 2.38)
    # Row-wide wells avoid artificial same-potential well slots between
    # isolated MOS devices while preserving per-device active/poly geometry.
    _rect(cell, LAYER["pwell"], 0.10, 0.17, max_x + 0.55, 0.85)
    _rect(cell, LAYER["nwell"], 0.10, 1.05, max_x + 0.55, 2.10)
    _rect(cell, LAYER["vtg"], 0.10, 0.17, max_x + 0.55, 0.85)
    _rect(cell, LAYER["vtg"], 0.10, 1.05, max_x + 0.55, 2.10)
    _label(cell, "VSS", 0.15, 0.04)
    _label(cell, "VDD", 0.15, 2.34)
    coords: dict[str, dict[str, tuple[float, float]]] = {}
    devices_by_name = {d.instance: d for d in lock.devices}
    for p in placements:
        dev = devices_by_name[str(p["instance"])]
        coords[dev.instance] = _draw_mos(cell, dev, float(p["x"]), float(p["y"]))
    # One conservative M1 horizontal bus per signal net above the devices.
    signal_nets = [n for n in lock.pins + sorted({d.g for d in lock.devices} | {d.s for d in lock.devices} | {d.d for d in lock.devices}) if n not in {"VDD", "VSS"}]
    seen: set[str] = set()
    bus_y = 2.60
    bus_map: dict[str, float] = {}
    for net in signal_nets:
        if net in seen:
            continue
        seen.add(net)
        bus_map[net] = bus_y
        _rect(cell, LAYER["m1"], 0.10, bus_y, max_x + 0.60, bus_y + 0.08)
        _label(cell, net, max_x + 0.40, bus_y + 0.04)
        bus_y += 0.22
    for dev in lock.devices:
        for terminal, net in [("S", dev.s), ("D", dev.d)]:
            if net in {"VDD", "VSS"}:
                rail_y = 2.34 if net == "VDD" else 0.04
                x, y = coords[dev.instance][terminal]
                _rect(cell, LAYER["m1"], x - 0.04, min(y, rail_y), x + 0.04, max(y, rail_y))
            else:
                x, y = coords[dev.instance][terminal]
                by = bus_map[net]
                _rect(cell, LAYER["m1"], x - 0.04, min(y, by), x + 0.04, max(y, by + 0.08))
    out.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(out)
    bbox = cell.bounding_box()
    return {
        "top_cell": top_name,
        "gds_path": str(out),
        "bbox": [float(bbox[0][0]), float(bbox[0][1]), float(bbox[1][0]), float(bbox[1][1])] if bbox else None,
        "device_coordinate_count": len(coords),
        "route_net_count": len(bus_map),
    }
