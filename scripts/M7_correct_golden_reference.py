from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M7_correct_golden_reference import run_m7_correct_golden_reference


def main() -> int:
    parser = argparse.ArgumentParser(description="Import uploaded layoutgen golden reference zip and reset repair target.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--zip-path", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    args = parser.parse_args()

    run_m7_correct_golden_reference(
        repo_root=Path(args.repo_root),
        status_md=Path(args.status_md),
        status_json=Path(args.status_json),
        zip_path=Path(args.zip_path),
        out_dir=Path(args.out_dir),
        out_json=Path(args.out_json),
        out_report=Path(args.out_report),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
