from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def export_cell_bundle(
    *,
    cell_dir: Path,
    cell_name: str,
    cell_obj: Any,
    metadata: dict[str, Any],
    pin_map: dict[str, Any],
    source_trace: dict[str, Any],
    geometry_fingerprint: dict[str, Any],
    sram_spec: dict[str, Any],
    generation_log_lines: list[str],
) -> Path:
    cell_dir.mkdir(parents=True, exist_ok=True)
    gds_path = cell_dir / f"{cell_name}.gds"
    cell_obj.gds_write(str(gds_path))
    write_json(cell_dir / f"{cell_name}.json", metadata)
    write_text(cell_dir / f"{cell_name}.md", "\n".join([f"# {cell_name}", "", *[f"- {k}: `{v}`" for k, v in metadata.items()]]) + "\n")
    write_json(cell_dir / f"{cell_name}_pin_map.json", pin_map)
    write_json(cell_dir / f"{cell_name}_source_trace.json", source_trace)
    write_json(cell_dir / f"{cell_name}_geometry_fingerprint.json", geometry_fingerprint)
    write_text(cell_dir / f"{cell_name}_generation.log", "\n".join(generation_log_lines) + "\n")
    write_json(cell_dir / "SRAM_SPEC.json", sram_spec)
    write_text(cell_dir / "SRAM_SPEC.md", "\n".join(["# SRAM_SPEC", "", *[f"- {k}: `{v}`" for k, v in sram_spec.items()]]) + "\n")
    return gds_path
