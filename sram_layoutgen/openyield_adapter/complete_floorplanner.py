from __future__ import annotations

from pathlib import Path
from typing import Any

import gdstk


GUIDE_LAYER = 201
REGION_LAYER = 202
CHANNEL_LAYER = 203
POWER_GUIDE_LAYER = 204


def build_proxy_cell(
    library: gdstk.Library,
    module_name: str,
    module_bbox: dict[str, Any],
    pins: list[dict[str, Any]],
) -> gdstk.Cell:
    cell = library.new_cell(f"{module_name}_floorplan_proxy")
    cell.add(
        gdstk.rectangle(
            (float(module_bbox["x0"]), float(module_bbox["y0"])),
            (float(module_bbox["x1"]), float(module_bbox["y1"])),
            layer=GUIDE_LAYER,
            datatype=0,
        )
    )
    for pin in pins:
        bbox = pin["normalized_local_bbox"]
        layer = int(pin.get("source_layer") or 11)
        cell.add(
            gdstk.rectangle(
                (float(bbox["x0"]), float(bbox["y0"])),
                (float(bbox["x1"]), float(bbox["y1"])),
                layer=layer,
                datatype=0,
            )
        )
    return cell


def add_region_guides(
    top: gdstk.Cell,
    regions: dict[str, dict[str, Any]],
    channels: dict[str, dict[str, Any]],
    power_regions: dict[str, dict[str, Any]],
) -> None:
    for region in regions.values():
        top.add(
            gdstk.rectangle(
                (float(region["x0"]), float(region["y0"])),
                (float(region["x1"]), float(region["y1"])),
                layer=REGION_LAYER,
                datatype=0,
            )
        )
    for region in channels.values():
        top.add(
            gdstk.rectangle(
                (float(region["x0"]), float(region["y0"])),
                (float(region["x1"]), float(region["y1"])),
                layer=CHANNEL_LAYER,
                datatype=0,
            )
        )
    for region in power_regions.values():
        top.add(
            gdstk.rectangle(
                (float(region["x0"]), float(region["y0"])),
                (float(region["x1"]), float(region["y1"])),
                layer=POWER_GUIDE_LAYER,
                datatype=0,
            )
        )


def write_floorplan_gds(
    out_path: Path,
    placements: list[dict[str, Any]],
    module_pins: dict[str, list[dict[str, Any]]],
    module_bboxes: dict[str, dict[str, Any]],
    regions: dict[str, dict[str, Any]],
    channels: dict[str, dict[str, Any]],
    power_regions: dict[str, dict[str, Any]],
) -> None:
    library = gdstk.Library()
    top = library.new_cell("openyield_complete_floorplan_sram")
    proxy_cells: dict[str, gdstk.Cell] = {}
    for placement in placements:
        module_name = placement["module_name"]
        if module_name not in proxy_cells:
            proxy_cells[module_name] = build_proxy_cell(
                library=library,
                module_name=module_name,
                module_bbox=module_bboxes[module_name],
                pins=module_pins[module_name],
            )
        origin = placement["placed_origin"]
        top.add(
            gdstk.Reference(
                proxy_cells[module_name],
                (float(origin["x"]), float(origin["y"])),
            )
        )
    add_region_guides(top, regions, channels, power_regions)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    library.write_gds(str(out_path))
