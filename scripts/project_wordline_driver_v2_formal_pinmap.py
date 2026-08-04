#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
OUT_DIR = REPO_ROOT / "outputs" / "PROJECT_wordline_driver_v2_formal_pinmap" / "current_supported_config"
PRIMARY_REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
ALIGNMENT_CSV = PRIMARY_REPO_ROOT / "docs/mapping/M11W_wordline_driver_pin_alignment_matrix.csv"
SOURCE_GDS = PRIMARY_REPO_ROOT / "technology/freepdk45/gds_lib/openram_replacements/gen_wl_driver.gds"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def git_head() -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git rev-parse HEAD failed")
    return completed.stdout.strip()


def _parse_bbox(text: str) -> list[float]:
    text = text.strip().strip("[]")
    return [round(float(part.strip()), 6) for part in text.split(",")]


def main() -> None:
    rows = list(csv.DictReader(ALIGNMENT_CSV.open(encoding="utf-8")))
    normalized = {
        "A": "A",
        "B": "B",
        "Z": "Z",
        "VDD": "VDD",
        "vdd": "VDD",
        "gnd": "VSS",
    }
    pin_map: dict[str, list[dict[str, Any]]] = {}
    evidence: dict[str, Any] = {
        "scope": "project_wordline_driver_v2_formal_pinmap",
        "git_head": git_head(),
        "source_gds": str(SOURCE_GDS.resolve()),
        "alignment_csv": str(ALIGNMENT_CSV.resolve()),
        "pin_rows": [],
    }
    for row in rows:
        golden = row["golden_pin_name"]
        if golden not in normalized:
            continue
        bbox = _parse_bbox(row["golden_pin_bbox"])
        pin_name = normalized[golden]
        entry = {
            "layer": "m1",
            "lx": bbox[0],
            "by": bbox[1],
            "rx": bbox[2],
            "uy": bbox[3],
        }
        pin_map[pin_name] = [entry]
        evidence["pin_rows"].append(
            {
                "logical_pin": pin_name,
                "golden_pin_name": golden,
                "golden_pin_layer": row["golden_pin_layer"],
                "golden_pin_bbox": bbox,
                "alignment_status": row["pin_alignment_status"],
                "delta_x": row["pin_alignment_delta_x"],
                "delta_y": row["pin_alignment_delta_y"],
            }
        )

    write_json(DOCS / "WORDLINE_DRIVER_V2_FORMAL_PINMAP.json", {"pin_map": pin_map, "evidence": evidence})
    write_text(
        DOCS / "WORDLINE_DRIVER_V2_FORMAL_PINMAP.md",
        "\n".join(
            [
                "# Wordline Driver V2 Formal Pinmap",
                "",
                f"- git_head: `{evidence['git_head']}`",
                f"- source_gds: `{SOURCE_GDS}`",
                f"- alignment_csv: `{ALIGNMENT_CSV}`",
                "- normalized_pins: `A B Z VDD VSS`",
                "",
            ]
        ),
    )
    write_json(OUT_DIR / "gen_wl_driver_pin_map.json", pin_map)
    write_json(OUT_DIR / "gen_wl_driver_pinmap_evidence.json", evidence)


if __name__ == "__main__":
    main()
