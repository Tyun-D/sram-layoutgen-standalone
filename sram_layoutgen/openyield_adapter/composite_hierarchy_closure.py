from __future__ import annotations

from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.gds_reference_closure_verifier import verify_gds_reference_closure, write_reference_closure_outputs


def verify_composite_hierarchy_closure(gds_path: Path, top_name: str) -> dict[str, Any]:
    return verify_gds_reference_closure(gds_path, top_name)


def write_composite_hierarchy_outputs(
    *,
    report: dict[str, Any],
    json_path: Path,
    md_path: Path,
    structure_csv_path: Path,
    reference_csv_path: Path,
) -> None:
    write_reference_closure_outputs(
        report=report,
        json_path=json_path,
        md_path=md_path,
        structure_csv_path=structure_csv_path,
        reference_csv_path=reference_csv_path,
    )
