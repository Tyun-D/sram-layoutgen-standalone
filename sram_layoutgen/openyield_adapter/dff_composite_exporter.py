from __future__ import annotations

import gdstk
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.gds_hierarchy_clone_renamer import clone_hierarchy_with_renamed_cells, merge_unique_cells


def build_review_atlas(
    *,
    clean_gds: Path,
    clean_top_name: str,
    annotated_gds: Path,
    annotated_top_name: str,
    output_gds: Path,
) -> str:
    atlas_lib = gdstk.Library()
    clean_lib, clean_root, _ = clone_hierarchy_with_renamed_cells(
        source_gds=clean_gds,
        root_cell_name=clean_top_name,
        namespace_prefix="CLEAN_CANDIDATE",
    )
    anno_lib, anno_root, _ = clone_hierarchy_with_renamed_cells(
        source_gds=annotated_gds,
        root_cell_name=annotated_top_name,
        namespace_prefix="ANNOTATED_REVIEW",
    )
    merge_unique_cells(atlas_lib, clean_lib)
    merge_unique_cells(atlas_lib, anno_lib)
    top = atlas_lib.new_cell("M12C4A_DFF_REVIEW_ATLAS")
    clean_cell = next(cell for cell in atlas_lib.cells if cell.name == clean_root)
    anno_cell = next(cell for cell in atlas_lib.cells if cell.name == anno_root)
    clean_bbox = clean_cell.bounding_box()
    assert clean_bbox is not None
    width = float(clean_bbox[1][0] - clean_bbox[0][0])
    top.add(gdstk.Reference(clean_cell, origin=(0, 0)))
    top.add(gdstk.Reference(anno_cell, origin=(width + 1.0, 0)))
    top.add(gdstk.Label("QUALIFICATION_CANDIDATE_CLEAN", (0.5, float(clean_bbox[1][1]) + 0.4), layer=239, texttype=0))
    top.add(gdstk.Label("ANNOTATED_REVIEW", (width + 1.5, float(clean_bbox[1][1]) + 0.4), layer=239, texttype=0))
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    atlas_lib.write_gds(output_gds)
    return top.name
