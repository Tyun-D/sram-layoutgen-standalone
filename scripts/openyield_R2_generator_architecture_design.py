from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build OpenYield R2 SRAM generator architecture artifacts.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--openram-root", required=True)
    parser.add_argument("--r0-audit-json", required=True)
    parser.add_argument("--r0-reuse-matrix", required=True)
    parser.add_argument("--r1-report-json", required=True)
    parser.add_argument("--r1-intent-dir", required=True)
    parser.add_argument("--module-gds-inventory", required=True)
    parser.add_argument("--module-generator-inventory", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-matrix-csv", required=True)
    parser.add_argument("--out-matrix-md", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def load_builder(repo_root: Path):
    module_path = repo_root / "sram_layoutgen/openyield_adapter/generator_architecture.py"
    module_name = "openyield_r2_generator_architecture"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generator architecture module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.GeneratorArchitectureBuilder


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    builder_cls = load_builder(repo_root)
    context = {
        "repo_root": repo_root,
        "openyield_root": Path(args.openyield_root).resolve(),
        "openram_root": Path(args.openram_root).resolve(),
        "r0_audit_json": repo_root / args.r0_audit_json,
        "r0_reuse_matrix": repo_root / args.r0_reuse_matrix,
        "r1_report_json": repo_root / args.r1_report_json,
        "r1_intent_dir": repo_root / args.r1_intent_dir,
        "module_gds_inventory": repo_root / args.module_gds_inventory,
        "module_generator_inventory": repo_root / args.module_generator_inventory,
        "out_dir": repo_root / args.out_dir,
        "out_matrix_csv": repo_root / args.out_matrix_csv,
        "out_matrix_md": repo_root / args.out_matrix_md,
        "out_json": repo_root / args.out_json,
        "out_report": repo_root / args.out_report,
    }
    builder_cls(context).run()


if __name__ == "__main__":
    main()
