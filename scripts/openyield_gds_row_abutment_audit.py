from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.gds_row_abutment_audit import audit_gds_row_abutment, render_markdown  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit real GDS row abutment using leaf rail geometry.")
    parser.add_argument("--gds", required=True)
    parser.add_argument("--layout-json")
    parser.add_argument("--eligibility")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    report = audit_gds_row_abutment(args.gds, layout_json=args.layout_json, eligibility=args.eligibility)
    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "gds": report["gds_path"],
        "real_vertical_abutment_pass": report["real_vertical_abutment_pass"],
        "actual_interrow_rail_gap_um": report["actual_interrow_rail_gap_um"],
        "positive_overlap_count": report["positive_overlap_count"],
        "positive_overlap_depth_um": report["positive_overlap_depth_um"],
        "dff_real_abutment_pass": report["dff_real_abutment_pass"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
