from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STANDALONE_ROOT.parents[1]
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.openyield_adapter.decoder_output_contracts import write_decoder_output_contract_reports  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit OpenYield decoder output contracts.")
    parser.add_argument("--openyield-root", default="third_party/OpenYield")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--addr-width", type=int, default=5)
    parser.add_argument("--internal-gap", type=float, default=0.2)
    parser.add_argument("--contracts", default="docs/openyield_module_contracts.json")
    parser.add_argument("--gds-pin-report", default="docs/openyield_gds_pin_audit_report.json")
    parser.add_argument("--decomposition-report", default="docs/openyield_time_control_decomposition_report.json")
    parser.add_argument("--target-envelope-report", default="docs/openyield_control_target_envelope_report.json")
    parser.add_argument("--out-json", default="docs/openyield_decoder_output_contract_report.json")
    parser.add_argument("--out-md", default="docs/openyield_decoder_output_contract_report.md")
    parser.add_argument("--out-graph", default="docs/openyield_decoder_output_contract_graph.json")
    args = parser.parse_args()

    report = write_decoder_output_contract_reports(
        openyield_root=resolve_input(args.openyield_root),
        tech_dir=resolve_input(args.tech_dir),
        addr_width=args.addr_width,
        internal_gap=args.internal_gap,
        contracts_path=resolve_input(args.contracts),
        gds_pin_report_path=resolve_input(args.gds_pin_report),
        decomposition_report_path=resolve_input(args.decomposition_report),
        target_envelope_report_path=resolve_input(args.target_envelope_report),
        out_json=resolve_output(args.out_json),
        out_md=resolve_output(args.out_md),
        out_graph=resolve_output(args.out_graph),
    )
    print(f"Wrote {resolve_output(args.out_json)}")
    print(f"Wrote {resolve_output(args.out_md)}")
    print(f"Wrote {resolve_output(args.out_graph)}")
    print(
        "decoder_output_contracts_available="
        f"{report['decoder_output_contracts_available']} "
        "generated_block_planning="
        f"{report['can_enter_decoder_generated_block_planning']} "
        "physical_decoder_placement="
        f"{report['can_enter_physical_decoder_placement']}"
    )
    return 0


def resolve_input(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() and path.exists():
        return path
    for base in (Path.cwd(), STANDALONE_ROOT, REPO_ROOT):
        candidate = base / value
        if candidate.exists():
            return candidate
    return path if path.is_absolute() else REPO_ROOT / value


def resolve_output(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else STANDALONE_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
