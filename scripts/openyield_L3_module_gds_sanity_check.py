from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STANDALONE_ROOT.parents[1]
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.openyield_adapter.module_gds_sanity import run_module_gds_sanity_check  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize and verify OpenYield L3 module GDS sanity status.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--module-gds-dir", required=True)
    parser.add_argument("--inventory-csv", required=True)
    parser.add_argument("--inventory-md", required=True)
    parser.add_argument("--report-json", required=True)
    parser.add_argument("--report-md", required=True)
    parser.add_argument("--gap-summary", required=True)
    args = parser.parse_args()

    repo_root = resolve_path(args.repo_root)
    module_gds_dir = resolve_path(args.module_gds_dir)
    inventory_csv = resolve_path(args.inventory_csv)
    inventory_md = resolve_path(args.inventory_md)
    report_json = resolve_path(args.report_json)
    report_md = resolve_path(args.report_md)
    gap_summary = resolve_path(args.gap_summary)

    generated = run_module_gds_sanity_check(
        repo_root=repo_root,
        module_gds_dir=module_gds_dir,
        inventory_csv=inventory_csv,
        inventory_md=inventory_md,
        report_json=report_json,
        report_md=report_md,
        gap_summary=gap_summary,
    )
    report = generated["report"]
    print(f"Wrote {inventory_csv}")
    print(f"Wrote {inventory_md}")
    print(f"Wrote {report_json}")
    print(f"Wrote {report_md}")
    print(f"Wrote {gap_summary}")
    print(f"module_gds_sanity_failed_count={report['module_gds_sanity_failed_count']}")
    print(f"can_enter_L4_top_level_assembly={report['can_enter_L4_top_level_assembly']}")
    return 0


def resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if Path.cwd().resolve() == REPO_ROOT.resolve():
        return STANDALONE_ROOT / value
    return Path.cwd() / value


if __name__ == "__main__":
    raise SystemExit(main())
