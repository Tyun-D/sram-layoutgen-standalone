from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.layout_prototype import generate_layout_prototype  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate guarded legacy or hybrid OpenYield layout prototypes.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--mode", choices=["legacy_baseline", "hybrid_openyield_prototype"], required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--metadata-dir", default="docs")
    parser.add_argument("--enable-openyield-gate-row-packing", action="store_true")
    parser.add_argument("--enable-openyield-gate-row-vertical-abutment", action="store_true")
    args = parser.parse_args()

    result = generate_layout_prototype(
        repo_root=resolve(args.repo_root),
        mode=args.mode,
        out_dir=args.out_dir,
        metadata_dir=args.metadata_dir,
        enable_openyield_gate_row_packing=args.enable_openyield_gate_row_packing,
        enable_openyield_gate_row_vertical_abutment=args.enable_openyield_gate_row_vertical_abutment,
    )
    print(json.dumps({
        "mode": result["mode"],
        "gds_path": result["gds_path"],
        "gds_size_bytes": result["gds_size_bytes"],
        "module_coverage_json": result["module_coverage_json"],
        "openyield_driven_modules": result["openyield_driven_modules"],
        "fallback_modules": result["fallback_modules"],
    }, ensure_ascii=False, indent=2))
    return 0


def resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
