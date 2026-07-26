from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gdstk


def write_module_access_view(
    module_name: str,
    source_gds: Path,
    out_dir: Path,
    pins: list[dict[str, Any]],
    module_report: dict[str, Any],
) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_gds = out_dir / f"{module_name}_access.gds"
    pins_json = out_dir / "pins_repaired.json"
    report_json = out_dir / "pin_access_report.json"

    library = gdstk.read_gds(str(source_gds))
    top_cells = library.top_level()
    base_top = top_cells[0] if top_cells else (library.cells[0] if library.cells else library.new_cell(module_name))
    wrapper_name = f"{module_name}_access"
    existing = next((cell for cell in library.cells if cell.name == wrapper_name), None)
    if existing is not None:
        library.remove(existing)
    wrapper = library.new_cell(wrapper_name)
    wrapper.add(gdstk.Reference(base_top))
    for pin in pins:
        bbox = pin["normalized_local_bbox"]
        layer = int(pin["source_layer"] or 11)
        wrapper.add(
            gdstk.rectangle(
                (float(bbox["x0"]), float(bbox["y0"])),
                (float(bbox["x1"]), float(bbox["y1"])),
                layer=layer,
                datatype=0,
            )
        )
        center = pin["normalized_local_center"]
        wrapper.add(gdstk.Label(str(pin["pin_name"]), (float(center["x"]), float(center["y"])), layer=layer, texttype=0))
    library.write_gds(str(out_gds))
    pins_json.write_text(json.dumps({"module": module_name, "pins": pins}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_json.write_text(json.dumps(module_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "module_access_view_gds": str(out_gds),
        "pins_repaired_json": str(pins_json),
        "pin_access_report_json": str(report_json),
    }
