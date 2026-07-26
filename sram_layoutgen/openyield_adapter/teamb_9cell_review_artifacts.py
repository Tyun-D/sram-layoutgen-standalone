from __future__ import annotations

from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.teamb_composite_helper import write_csv, write_text


def write_human_review_artifacts(*, output_root: Path, gate: dict[str, Any]) -> None:
    write_text(
        output_root / "TEAM_B_9CELL_HUMAN_REVIEW_CHECKLIST.csv",
        "item,status,notes\nlibrary_packaging,PENDING,\nnamespace_closure,PENDING,\nimmutability,PENDING,\npairwise_abutment,PENDING,\npin_access,PENDING,\ncombined_drc,PENDING,\ncross_module_connectivity,PENDING,\n",
    )
    write_text(
        output_root / "TEAM_B_9CELL_HUMAN_REVIEW_REPORT_TEMPLATE.md",
        "# Team B 9-Cell Human Review\n\n- integration gate: `{}`\n".format(gate["combined_atlas_drc_passed"]),
    )
    write_csv(output_root / "TEAM_B_9CELL_HUMAN_REVIEW_SCREENSHOT_INDEX.csv", [{"artifact": "TEAM_B_9CELL_CLEAN_ATLAS.gds", "notes": "Open in KLayout"}])

