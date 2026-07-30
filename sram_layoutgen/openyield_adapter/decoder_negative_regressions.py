from __future__ import annotations

from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.production_negative_test_harness import (
    MutationCase,
    run_contract_mutation,
    run_determinism_mutation,
    write_negative_test_matrix,
    write_negative_test_summary,
)
from sram_layoutgen.openyield_adapter.teamb_composite_helper import read_json, write_json


def _mutate_json_value(path: Path, key: str, value: Any) -> None:
    payload = read_json(path)
    payload[key] = value
    write_json(path, payload)


def run_decoder_negative_regressions(*, repo_root: Path, bundle_dir: Path) -> dict[str, Any]:
    from sram_layoutgen.openyield_adapter.decoder_validator import validate_decoder_bundle

    work_root = bundle_dir / "negative_test_work"
    base_dir = bundle_dir

    def _validate(work_dir: Path) -> dict[str, Any]:
        return validate_decoder_bundle(repo_root, work_dir, run_determinism=False)

    rows = []
    cases = [
        (
            MutationCase("01_source_commit_mutation", "contract", "SOURCE_LOCK_FAILED", "SOURCE_COMMIT_MISMATCH", Path("DECODER_REBUILD_CONTRACT_LOCK.json"), "validate_decoder_bundle"),
            lambda d: (_mutate_json_value(d / "DECODER_REBUILD_CONTRACT_LOCK.json", "openyield_authority", {**read_json(d / "DECODER_REBUILD_CONTRACT_LOCK.json")["openyield_authority"], "commit": "deadbeef"}), d / "DECODER_REBUILD_CONTRACT_LOCK.json")[1],
            run_contract_mutation,
        ),
        (
            MutationCase("02_child_sha_mutation", "contract", "INPUT_LOCK_FAILED", "INPUT_SHA_MISMATCH", Path("DECODER_REBUILD_CONTRACT_LOCK.json"), "validate_decoder_bundle"),
            lambda d: (_mutate_json_value(d / "DECODER_REBUILD_CONTRACT_LOCK.json", "child_assets", [{**row, "gds_sha256": "00" * 32} if index == 0 else row for index, row in enumerate(read_json(d / "DECODER_REBUILD_CONTRACT_LOCK.json")["child_assets"])]), d / "DECODER_REBUILD_CONTRACT_LOCK.json")[1],
            run_contract_mutation,
        ),
        (
            MutationCase("03_missing_required_pin_contract", "contract", "TOP_PIN_CONTRACT_FAILED", "TOP_PIN_LABEL_MISSING", Path("DECODER_REBUILD_CONTRACT_LOCK.json"), "validate_decoder_bundle"),
            lambda d: (_mutate_json_value(d / "DECODER_REBUILD_CONTRACT_LOCK.json", "expected_top_pins", {**read_json(d / "DECODER_REBUILD_CONTRACT_LOCK.json")["expected_top_pins"], "inputs": read_json(d / "DECODER_REBUILD_CONTRACT_LOCK.json")["expected_top_pins"]["inputs"] + ["A99"]}), d / "DECODER_REBUILD_CONTRACT_LOCK.json")[1],
            run_contract_mutation,
        ),
        (
            MutationCase("04_hierarchy_mutation", "determinism", "PACKAGING_FAILED", "DANGLING_REFERENCE", Path("decoder_hierarchy_manifest.json"), "validate_decoder_bundle"),
            lambda d: (_mutate_json_value(d / "decoder_hierarchy_manifest.json", "unresolved_references", [{"reference_name": "fake_missing_cell"}]), d / "decoder_hierarchy_manifest.json")[1],
            run_determinism_mutation,
        ),
    ]
    for case, mutator, runner in cases:
        rows.append(
            runner(
                base_dir=base_dir,
                checkpoint_root=work_root,
                case_work_root=work_root,
                case=case,
                mutate_fn=mutator,
                validate_fn=_validate,
            )
        )
    write_negative_test_matrix(bundle_dir / "DECODER_NEGATIVE_TEST_MATRIX.csv", rows)
    summary = write_negative_test_summary(bundle_dir / "DECODER_NEGATIVE_TEST_SUMMARY.json", rows)
    return {"rows": rows, "summary": summary}
