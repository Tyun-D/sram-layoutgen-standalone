from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.gds_hierarchy_clone_renamer import clone_hierarchy_with_renamed_cells
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import non_text_geometry_fingerprint


def clone_child_for_composition(
    *,
    source_gds: Path,
    source_top_name: str,
    clone_root_name: str,
    output_gds: Path,
) -> dict[str, Any]:
    cloned_lib, renamed_root_name, name_map = clone_hierarchy_with_renamed_cells(
        source_gds=source_gds,
        root_cell_name=source_top_name,
        namespace_prefix=clone_root_name,
    )
    total_labels = 0
    for cell in cloned_lib.cells:
        total_labels += len(cell.labels)
        if cell.labels:
            cell.remove(*cell.labels)
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    cloned_lib.write_gds(output_gds)
    source_fp = non_text_geometry_fingerprint(source_gds, source_top_name)
    clone_fp = non_text_geometry_fingerprint(output_gds, renamed_root_name)
    return {
        "source_top_name": source_top_name,
        "clone_root_name": clone_root_name,
        "renamed_root_name": renamed_root_name,
        "name_map": name_map,
        "output_gds": str(output_gds),
        "source_non_text_fingerprint": source_fp,
        "clone_non_text_fingerprint": clone_fp,
        "non_text_geometry_preserved": source_fp["digest"] == clone_fp["digest"],
        "removed_label_count": total_labels,
        "internal_label_count_after_clone": sum(len(cell.labels) for cell in cloned_lib.cells),
    }


def write_child_clone_reports(
    *,
    rows: list[dict[str, Any]],
    geometry_csv_path: Path,
    label_csv_path: Path,
    contract_json_path: Path,
    contract_md_path: Path,
) -> dict[str, Any]:
    geometry_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with geometry_csv_path.open("w", encoding="utf-8", newline="") as handle:
        import csv

        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "source_top_name",
                "clone_root_name",
                "renamed_root_name",
                "output_gds",
                "source_digest",
                "clone_digest",
                "non_text_geometry_preserved",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "source_top_name": row["source_top_name"],
                    "clone_root_name": row["clone_root_name"],
                    "renamed_root_name": row["renamed_root_name"],
                    "output_gds": row["output_gds"],
                    "source_digest": row["source_non_text_fingerprint"]["digest"],
                    "clone_digest": row["clone_non_text_fingerprint"]["digest"],
                    "non_text_geometry_preserved": row["non_text_geometry_preserved"],
                }
            )
    with label_csv_path.open("w", encoding="utf-8", newline="") as handle:
        import csv

        writer = csv.DictWriter(
            handle,
            fieldnames=["source_top_name", "clone_root_name", "removed_label_count", "internal_label_count_after_clone"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "source_top_name": row["source_top_name"],
                    "clone_root_name": row["clone_root_name"],
                    "removed_label_count": row["removed_label_count"],
                    "internal_label_count_after_clone": row["internal_label_count_after_clone"],
                }
            )
    payload = {
        "child_clone_non_text_geometry_preserved": all(row["non_text_geometry_preserved"] for row in rows),
        "child_clone_internal_label_count": sum(row["internal_label_count_after_clone"] for row in rows),
        "rows": rows,
    }
    contract_json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    contract_md_path.write_text(
        "\n".join(
            [
                "# M12C4A Child Clone Contract",
                "",
                f"- child_clone_non_text_geometry_preserved: `{payload['child_clone_non_text_geometry_preserved']}`",
                f"- child_clone_internal_label_count: `{payload['child_clone_internal_label_count']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return payload
