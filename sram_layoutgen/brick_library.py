"""Utilities for replacement-ready helper macro contracts."""

from __future__ import annotations

import json
from pathlib import Path

from .gds_util import inspect_gds_text_records, measure_gds_bbox


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
    "sel": "SEL",
    "en": "EN",
    "en_bar": "EN",
    "gnd": "gnd",
    "vdd": "vdd",
}

_LAYER_NAMES = {
    9: "poly",
    11: "m1",
    13: "m2",
    15: "m3",
    17: "m4",
}

_EXPECTED_PINS = {
    "gen_col_mux": {"BL", "BR", "OUT", "OUTB", "SEL", "gnd", "vdd"},
    "gen_delay_inv": {"A", "Z", "gnd", "vdd"},
    "gen_inv": {"A", "Z", "gnd", "vdd"},
    "gen_nand2": {"A", "B", "Z", "gnd", "vdd"},
    "gen_precharge": {"BL", "BR", "EN", "gnd", "vdd"},
    "gen_wl_driver": {"A", "Z", "gnd", "vdd"},
}


def materialize_generated_bricks(package_root: Path, force: bool = False) -> list[Path]:
    """Ensure the replacement macro manifest exists.

    Older revisions wrote fake generated GDS into ``gds_lib`` or refreshed the
    manifest with abstract, hand-modeled cells. The strict flow only registers
    real replacement GDS macros extracted from OpenRAM-style generated cells.
    """

    return materialize_replacement_macro_manifest(package_root, force=force)


def materialize_replacement_macro_manifest(package_root: Path, force: bool = False) -> list[Path]:
    tech_root = package_root / "technology" / "freepdk45"
    path = tech_root / "replacement_macros.json"
    if path.exists() and not force:
        return []

    macros = []
    replacements = tech_root / "gds_lib" / "openram_replacements"
    for gds_path in sorted(replacements.glob("gen_*.gds")):
        bbox = measure_gds_bbox(gds_path)
        if bbox is None:
            continue
        macros.append({
            "name": gds_path.stem,
            "role": "replacement_macro",
            "width": bbox.width,
            "height": bbox.height,
            "gds": str(gds_path.relative_to(tech_root)).replace("\\", "/"),
            "spice": None,
            "pins": _pins_from_gds(gds_path),
            "source": {
                "kind": "openram_extracted_replacement_gds",
                "source_gds": str(gds_path.relative_to(package_root)).replace("\\", "/"),
            },
        })
    data = {
        "version": 2,
        "description": (
            "Replacement-ready macro contracts. Entries are real FreePDK45/OpenRAM-style "
            "GDS macros only; do not register hand-drawn fallback standard cells for signoff."
        ),
        "macros": macros,
    }
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return [path]


def _pins_from_gds(gds_path: Path) -> list[dict[str, object]]:
    pins = {}
    expected = _EXPECTED_PINS.get(gds_path.stem, set())
    for record in inspect_gds_text_records(gds_path):
        name = _PIN_ALIASES.get(str(record["text"]).strip().lower())
        if name is None or name in pins or (expected and name not in expected):
            continue
        layer = _LAYER_NAMES.get(int(record["layer"]))
        if layer is None:
            continue
        pins[name] = {
            "name": name,
            "layer": layer,
            "x": float(record["x"]),
            "y": float(record["y"]),
            "use": "POWER" if name == "vdd" else "GROUND" if name == "gnd" else "SIGNAL",
        }
    return [pins[name] for name in sorted(pins)]
