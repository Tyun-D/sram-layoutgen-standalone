#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.decoder_contract import build_decoder_contract_lock, build_decoder_contract_markdown
from sram_layoutgen.openyield_adapter.decoder_generator import generate_decoder_bundle
from sram_layoutgen.openyield_adapter.decoder_negative_regressions import run_decoder_negative_regressions
from sram_layoutgen.openyield_adapter.decoder_validator import validate_decoder_bundle
from sram_layoutgen.openyield_adapter.teamb_composite_helper import write_json, write_text

OUT_DIR = REPO_ROOT / "outputs" / "PROJECT_decoder_rebuild" / "current_supported_config"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    contract = build_decoder_contract_lock(REPO_ROOT)
    write_json(OUT_DIR / "DECODER_REBUILD_CONTRACT_LOCK.json", contract)
    write_text(OUT_DIR / "DECODER_REBUILD_CONTRACT_LOCK.md", build_decoder_contract_markdown(contract))
    manifest = generate_decoder_bundle(REPO_ROOT, OUT_DIR, contract)
    write_json(OUT_DIR / "decoder_bundle_manifest.json", manifest)
    gate = validate_decoder_bundle(REPO_ROOT, OUT_DIR, run_determinism=True)
    negative = run_decoder_negative_regressions(repo_root=REPO_ROOT, bundle_dir=OUT_DIR)
    write_text(
        OUT_DIR / "DECODER_REBUILD_SUMMARY.md",
        "\n".join(
            [
                "# Decoder Rebuild Summary",
                "",
                f"- top_cell_name: `{contract['top_cell_name']}`",
                f"- clean_gds_path: `{manifest['clean_gds_path']}`",
                f"- drc_marker_count: `{gate['drc']['marker_count']}`",
                f"- gate_passed: `{gate['passed']}`",
                f"- rejection_codes: `{gate.get('rejection_codes', [])}`",
                f"- negative_tests_passed: `{negative['summary']['negative_tests_passed']}`",
                "",
            ]
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
