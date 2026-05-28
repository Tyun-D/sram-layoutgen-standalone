"""OpenRAM-style placement helpers.

This module intentionally ports only placement semantics from OpenRAM:
instance mirror selection, transform-origin calculation, and rectangle
mirroring inside a placed cell. Routing and device generation stay outside.
"""

from __future__ import annotations

from .geometry import Rect


def array_mirror(
    row: int,
    col: int,
    mirror_x: bool = False,
    mirror_y: bool = False,
    row_offset: int = 0,
    column_offset: int = 0,
) -> str:
    """Return OpenRAM mirror key for a tiled array element."""

    mx = mirror_x and (row + row_offset) % 2 == 1
    my = mirror_y and (col + column_offset) % 2 == 1
    if mx and my:
        return "XY"
    if mx:
        return "MX"
    if my:
        return "MY"
    return "R0"


def sref_origin_for_bbox(cell, desired_x0: float, desired_y0: float, mirror: str = "R0") -> tuple[float, float]:
    """Return the GDS SREF origin that places a cell bbox at desired lower-left.

    This follows OpenRAM/gdsMill transform semantics:
    - R0 offset is lower-left.
    - MX offset is the top-left transform origin.
    - MY offset is the bottom-right transform origin.
    - XY offset is the top-right transform origin.
    """

    if mirror == "MX":
        return desired_x0 - cell.bbox_x0, desired_y0 + cell.bbox_y1
    if mirror == "MY":
        return desired_x0 + cell.bbox_x1, desired_y0 - cell.bbox_y0
    if mirror == "XY":
        return desired_x0 + cell.bbox_x1, desired_y0 + cell.bbox_y1
    return desired_x0 - cell.bbox_x0, desired_y0 - cell.bbox_y0


def openram_sref_origin(cell, xoffset: float, yoffset: float, mirror: str = "R0") -> tuple[float, float]:
    """Return the SREF origin used by OpenRAM's ``inst.place`` semantics.

    OpenRAM tiles bitcell arrays from a design origin and the module
    width/height, not from the measured physical bbox lower-left. This is
    important for bitcells whose wells/implants intentionally extend around
    the abstract origin.
    """

    x = xoffset + (cell.width if mirror in {"MY", "XY"} else 0.0)
    y = yoffset + (cell.height if mirror in {"MX", "XY"} else 0.0)
    return x, y


def placed_bbox_from_openram_origin(cell, xoffset: float, yoffset: float, mirror: str = "R0") -> Rect:
    """Return physical bbox when a cell is placed with OpenRAM origin rules."""

    ox, oy = openram_sref_origin(cell, xoffset, yoffset, mirror)
    if mirror in {"MY", "XY"}:
        x0, x1 = ox - cell.bbox_x1, ox - cell.bbox_x0
    else:
        x0, x1 = ox + cell.bbox_x0, ox + cell.bbox_x1
    if mirror in {"MX", "XY"}:
        y0, y1 = oy - cell.bbox_y1, oy - cell.bbox_y0
    else:
        y0, y1 = oy + cell.bbox_y0, oy + cell.bbox_y1
    return Rect(x0, y0, x1, y1)


def mirror_rect_in_cell(local: Rect, cell_width: float, cell_height: float, mirror: str = "R0") -> Rect:
    """Mirror a local rectangle inside a cell-sized placement bbox."""

    x0, y0, x1, y1 = local.x0, local.y0, local.x1, local.y1
    if mirror in {"MY", "XY"}:
        x0, x1 = cell_width - x1, cell_width - x0
    if mirror in {"MX", "XY"}:
        y0, y1 = cell_height - y1, cell_height - y0
    return Rect(x0, y0, x1, y1)


def place_local_rect(local: Rect, placed: Rect, mirror: str = "R0") -> Rect:
    """Transform a local cell rectangle into absolute coordinates."""

    mirrored = mirror_rect_in_cell(local, placed.width, placed.height, mirror)
    return mirrored.shifted(placed.x0, placed.y0)


def place_local_point(x: float, y: float, placed: Rect, mirror: str = "R0") -> tuple[float, float]:
    """Transform a local cell point into absolute coordinates."""

    if mirror in {"MY", "XY"}:
        x = placed.width - x
    if mirror in {"MX", "XY"}:
        y = placed.height - y
    return placed.x0 + x, placed.y0 + y
