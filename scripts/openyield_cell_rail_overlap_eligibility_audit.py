from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.cell_rail_overlap_eligibility import (  # noqa: E402
    audit_cell_rail_overlap_eligibility,
    render_markdown,
    write_csv,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit which OpenYield cells can safely use positive same-net rail overlap packing.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-table-md", required=True)
    args = parser.parse_args()

    report = audit_cell_rail_overlap_eligibility(args.repo_root)
    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_csv = Path(args.out_csv)
    out_table_md = Path(args.out_table_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = render_markdown(report)
    out_md.write_text(md, encoding="utf-8")
    out_table_md.write_text(md, encoding="utf-8")
    write_csv(report["cells"], out_csv)
    print(json.dumps({
        "eligible_cells_count": report["eligible_cells_count"],
        "blocked_cells_count": report["blocked_cells_count"],
        "dff_excluded_from_vertical_overlap": report["dff_excluded_from_vertical_overlap"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
