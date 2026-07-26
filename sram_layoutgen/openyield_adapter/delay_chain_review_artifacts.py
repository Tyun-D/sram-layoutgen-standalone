from __future__ import annotations

from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.inverter_chain_layout_quality import build_compact_review_atlas


def build_delay_chain_review_atlases(
    *,
    clean_gds: Path,
    top_cell_name: str,
    placements: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    top_pin_bboxes: dict[str, dict[str, float]],
    floating_rows: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    role_labels = []
    role_boxes = []
    for row in placements:
        bbox = row["bbox"]
        role_boxes.append({"bbox": bbox})
        role_labels.append({"text": row["instance_name"], "x": round((bbox[0] + bbox[2]) * 0.5, 6), "y": round(bbox[3] + 0.08, 6)})
    net_labels = []
    for row in route_rows:
        if "m2_trunk_bbox" in row:
            bbox = row["m2_trunk_bbox"]
            net_labels.append({"text": row["net_name"], "x": round((bbox["lx"] + bbox["rx"]) * 0.5, 6), "y": round(bbox["uy"] + 0.06, 6)})
    floating_labels = []
    for row in floating_rows:
        bbox = row["bbox"]
        floating_labels.append({"text": row["instance_role"], "x": round((bbox["lx"] + bbox["rx"]) * 0.5, 6), "y": round(bbox["uy"] + 0.06, 6)})
    pin_labels = []
    for pin_name, bbox in top_pin_bboxes.items():
        pin_labels.append({"text": pin_name, "x": round((bbox["lx"] + bbox["rx"]) * 0.5, 6), "y": round(bbox["uy"] + 0.06, 6)})
    build_compact_review_atlas(clean_gds=clean_gds, top_cell_name=top_cell_name, output_gds=output_dir / "review_atlas.gds", labels=role_labels + net_labels + pin_labels, boxes=role_boxes)
    build_compact_review_atlas(clean_gds=clean_gds, top_cell_name=top_cell_name, output_gds=output_dir / "review_atlas_stage_roles.gds", labels=role_labels, boxes=role_boxes)
    build_compact_review_atlas(clean_gds=clean_gds, top_cell_name=top_cell_name, output_gds=output_dir / "review_atlas_stage_nets.gds", labels=net_labels, boxes=[])
    build_compact_review_atlas(clean_gds=clean_gds, top_cell_name=top_cell_name, output_gds=output_dir / "review_atlas_floating_load_outputs.gds", labels=floating_labels, boxes=[])
    build_compact_review_atlas(clean_gds=clean_gds, top_cell_name=top_cell_name, output_gds=output_dir / "review_atlas_pin_access.gds", labels=pin_labels, boxes=[])
    build_compact_review_atlas(clean_gds=clean_gds, top_cell_name=top_cell_name, output_gds=output_dir / "review_atlas_power_rails.gds", labels=[{"text": "VDD/VSS", "x": 0.2, "y": 2.1}], boxes=[])
