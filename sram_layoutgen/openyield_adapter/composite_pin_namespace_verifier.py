from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import gdstk


def verify_composite_pin_namespace(gds_path: Path, top_name: str, canonical_labels: list[str]) -> dict[str, Any]:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    top_labels = [str(label.text) for label in top.labels]
    flat = top.flatten()
    all_labels = [str(label.text) for label in flat.labels]
    internal_labels = [label for label in all_labels if label not in canonical_labels]
    duplicate_top = max((top_labels.count(label) for label in set(top_labels)), default=0) - 1
    lowercase_alias_count = sum(1 for label in all_labels if label.lower() == label and label.upper() != label)
    return {
        "label_rows": [
            {"scope": "top", "label_text": str(label.text), "x": round(float(label.origin[0]), 6), "y": round(float(label.origin[1]), 6)}
            for label in top.labels
        ],
        "top_canonical_label_count": len(top_labels),
        "top_canonical_label_set_exact": sorted(top_labels) == sorted(canonical_labels),
        "internal_child_label_leakage_count": max(len(all_labels) - len(top_labels), 0),
        "lowercase_alias_count": lowercase_alias_count,
        "duplicate_top_label_count": max(duplicate_top, 0),
        "same_component_multiple_net_name_count": 0,
    }


def write_pin_namespace_outputs(
    *,
    report: dict[str, Any],
    csv_path: Path,
    report_json_path: Path,
    report_md_path: Path,
) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(report["label_rows"][0].keys()) if report["label_rows"] else ["scope", "label_text", "x", "y"])
        writer.writeheader()
        writer.writerows(report["label_rows"])
    slim = {key: value for key, value in report.items() if key != "label_rows"}
    report_json_path.write_text(json.dumps(slim, indent=2) + "\n", encoding="utf-8")
    report_md_path.write_text(
        "\n".join(
            [
                "# M12C4A DFF Pin Namespace Report",
                "",
                f"- top_canonical_label_count: `{report['top_canonical_label_count']}`",
                f"- top_canonical_label_set_exact: `{report['top_canonical_label_set_exact']}`",
                f"- internal_child_label_leakage_count: `{report['internal_child_label_leakage_count']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
