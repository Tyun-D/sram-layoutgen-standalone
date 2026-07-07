from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract raw OpenYield config evidence and add variation support to the translator.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--m10h-report", required=True)
    parser.add_argument("--m10-report", required=True)
    parser.add_argument("--m10-dir", required=True)
    parser.add_argument("--golden-reference", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--t1-inventory", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from sram_layoutgen.openyield_adapter.M11_openyield_config_variation import run_m11_openyield_config_variation

    report = run_m11_openyield_config_variation(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        m10h_report=(repo_root / args.m10h_report).resolve(),
        m10_report=(repo_root / args.m10_report).resolve(),
        m10_dir=(repo_root / args.m10_dir).resolve(),
        golden_reference=(repo_root / args.golden_reference).resolve(),
        openyield_root=Path(args.openyield_root).resolve(),
        t1_inventory=(repo_root / args.t1_inventory).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    for key in [
        "config_candidate_count",
        "openyield_capacity_config_found",
        "word_size_source_backed",
        "num_words_source_backed",
        "words_per_row_source_backed",
        "capacity_config_fallback_used_after_M11",
        "variation_support_added",
        "gds_path",
        "reference_vs_m11_geometry_match",
    ]:
        print(f"{key}={report[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
