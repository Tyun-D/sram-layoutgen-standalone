from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.physical_primitive_gap_closer import (  # noqa: E402
    close_l1_gaps,
    load_csv_rows,
    render_gap_report_md,
    update_l1_evidence,
    write_gap_closure_outputs,
)
from sram_layoutgen.openyield_adapter.primitive_composition_generators import (  # noqa: E402
    default_primitive_composition_library,
    load_primitive_composition_library,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Close OpenYield L1 primitive physical source gaps")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--in-csv", required=True)
    parser.add_argument("--in-module-deps-csv", required=True)
    parser.add_argument("--in-library-json", required=True)
    parser.add_argument("--composition-library-json", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-module-deps-csv", required=True)
    parser.add_argument("--out-module-deps-md", required=True)
    parser.add_argument("--out-library-json", required=True)
    parser.add_argument("--out-composition-contracts-csv", required=True)
    parser.add_argument("--out-composition-contracts-md", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo_root).resolve()
    comp_path = repo / args.composition_library_json
    if not comp_path.exists():
        comp_path.parent.mkdir(parents=True, exist_ok=True)
        comp_path.write_text(
            json.dumps(default_primitive_composition_library().to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    primitive_rows = load_csv_rows(repo / args.in_csv)
    module_rows = load_csv_rows(repo / args.in_module_deps_csv)
    leaf_library = json.loads((repo / args.in_library_json).read_text(encoding="utf-8"))
    composition_library = load_primitive_composition_library(comp_path)
    updated_rows, updated_modules, report, composition_rows, leaf_library_out = close_l1_gaps(
        primitive_rows,
        module_rows,
        leaf_library,
        composition_library,
    )
    write_gap_closure_outputs(
        out_csv=repo / args.out_csv,
        out_md=repo / args.out_md,
        out_module_csv=repo / args.out_module_deps_csv,
        out_module_md=repo / args.out_module_deps_md,
        out_library_json=repo / args.out_library_json,
        out_comp_csv=repo / args.out_composition_contracts_csv,
        out_comp_md=repo / args.out_composition_contracts_md,
        out_json=repo / args.out_json,
        out_report=repo / args.out_report,
        primitive_rows=updated_rows,
        module_rows=updated_modules,
        leaf_library=leaf_library_out,
        composition_rows=composition_rows,
        report=report,
    )
    update_l1_evidence(repo, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
