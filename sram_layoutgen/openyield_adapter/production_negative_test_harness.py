from __future__ import annotations

import csv
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

import gdstk

from sram_layoutgen.openyield_adapter.pnand2_verification_gate import json_safe, sha256_file, write_json
from sram_layoutgen.openyield_adapter.rejection_code_registry import code_matches, rejection_family


@dataclass(frozen=True)
class MutationCase:
    test_id: str
    mutation_kind: str
    expected_rejection_family: str
    expected_rejection_code: str
    baseline_input_path: Path
    validator_name: str


@dataclass
class MutationResult:
    test_id: str
    baseline_input_path: str
    baseline_input_sha256: str
    mutated_input_path: str
    mutated_input_sha256: str
    mutation_effective: bool
    production_validator_name: str
    production_validator_input_path: str
    production_validator_input_sha256: str
    validator_cache_disabled: bool
    expected_rejection_family: str
    expected_rejection_code: str
    actual_rejection_family: str
    actual_rejection_code: str
    family_matched: bool
    code_matched: bool
    rejected_as_expected: bool


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)


def _copy_tree(src_dir: Path, dst_dir: Path) -> None:
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir, dst_dir, ignore=shutil.ignore_patterns("negative_test_work"))


def _run_mutation_case(
    *,
    base_dir: Path,
    checkpoint_root: Path,
    case_work_root: Path,
    case: MutationCase,
    mutate_fn: Callable[[Path], Path],
    validate_fn: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    tmp_root = case_work_root / case.test_id
    _copy_tree(base_dir, tmp_root)
    baseline_input_path = tmp_root / case.baseline_input_path
    baseline_input_sha = sha256_file(baseline_input_path)
    mutated_input_path = mutate_fn(tmp_root)
    mutated_input_sha = sha256_file(mutated_input_path)
    validation = validate_fn(tmp_root)
    actual_code = ""
    codes = validation.get("rejection_codes", [])
    if codes:
        actual_code = codes[0]
    result = MutationResult(
        test_id=case.test_id,
        baseline_input_path=str(baseline_input_path),
        baseline_input_sha256=baseline_input_sha,
        mutated_input_path=str(mutated_input_path),
        mutated_input_sha256=mutated_input_sha,
        mutation_effective=baseline_input_sha != mutated_input_sha,
        production_validator_name=case.validator_name,
        production_validator_input_path=str(mutated_input_path),
        production_validator_input_sha256=mutated_input_sha,
        validator_cache_disabled=True,
        expected_rejection_family=case.expected_rejection_family,
        expected_rejection_code=case.expected_rejection_code,
        actual_rejection_family=rejection_family(actual_code),
        actual_rejection_code=actual_code,
        family_matched=case.expected_rejection_family == rejection_family(actual_code),
        code_matched=code_matches(case.expected_rejection_code, actual_code),
        rejected_as_expected=(baseline_input_sha != mutated_input_sha)
        and (not validation.get("passed", True))
        and code_matches(case.expected_rejection_code, actual_code),
    )
    payload = asdict(result)
    payload["all_actual_rejection_codes"] = "|".join(codes)
    return payload


def _checkpoint_dir(checkpoint_root: Path) -> Path:
    path = checkpoint_root / "checkpoints"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_completed_checkpoint(checkpoint_root: Path, test_id: str, baseline_sha256: str) -> dict[str, Any] | None:
    path = _checkpoint_dir(checkpoint_root) / f"{test_id}.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("completed") is True and payload.get("baseline_sha") == baseline_sha256 and payload.get("rejected_as_expected") is True:
        return payload
    return None


def write_case_checkpoint(
    *,
    checkpoint_root: Path,
    test_id: str,
    baseline_sha: str,
    mutated_sha: str,
    mutation_effective: bool,
    validator_name: str,
    validator_input_sha: str,
    expected_rejection_code: str,
    actual_rejection_code: str,
    rejected_as_expected: bool,
) -> None:
    payload = {
        "test_id": test_id,
        "baseline_sha": baseline_sha,
        "mutated_sha": mutated_sha,
        "mutation_effective": mutation_effective,
        "validator_name": validator_name,
        "validator_input_sha": validator_input_sha,
        "expected_rejection_code": expected_rejection_code,
        "actual_rejection_code": actual_rejection_code,
        "rejected_as_expected": rejected_as_expected,
        "completed": True,
    }
    tmp_path = _checkpoint_dir(checkpoint_root) / f"{test_id}.json.tmp"
    final_path = _checkpoint_dir(checkpoint_root) / f"{test_id}.json"
    tmp_path.write_text(json.dumps(json_safe(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp_path.replace(final_path)


def run_contract_mutation(
    *,
    base_dir: Path,
    checkpoint_root: Path,
    case_work_root: Path,
    case: MutationCase,
    mutate_fn: Callable[[Path], Path],
    validate_fn: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    return _run_mutation_case(
        base_dir=base_dir,
        checkpoint_root=checkpoint_root,
        case_work_root=case_work_root,
        case=case,
        mutate_fn=mutate_fn,
        validate_fn=validate_fn,
    )


def run_gds_label_mutation(
    *,
    base_dir: Path,
    checkpoint_root: Path,
    case_work_root: Path,
    case: MutationCase,
    mutate_fn: Callable[[Path], Path],
    validate_fn: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    return _run_mutation_case(
        base_dir=base_dir,
        checkpoint_root=checkpoint_root,
        case_work_root=case_work_root,
        case=case,
        mutate_fn=mutate_fn,
        validate_fn=validate_fn,
    )


def run_gds_geometry_mutation(
    *,
    base_dir: Path,
    checkpoint_root: Path,
    case_work_root: Path,
    case: MutationCase,
    mutate_fn: Callable[[Path], Path],
    validate_fn: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    return _run_mutation_case(
        base_dir=base_dir,
        checkpoint_root=checkpoint_root,
        case_work_root=case_work_root,
        case=case,
        mutate_fn=mutate_fn,
        validate_fn=validate_fn,
    )


def run_gds_short_mutation(
    *,
    base_dir: Path,
    checkpoint_root: Path,
    case_work_root: Path,
    case: MutationCase,
    mutate_fn: Callable[[Path], Path],
    validate_fn: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    return _run_mutation_case(
        base_dir=base_dir,
        checkpoint_root=checkpoint_root,
        case_work_root=case_work_root,
        case=case,
        mutate_fn=mutate_fn,
        validate_fn=validate_fn,
    )


def run_hierarchy_mutation(
    *,
    base_dir: Path,
    checkpoint_root: Path,
    case_work_root: Path,
    case: MutationCase,
    mutate_fn: Callable[[Path], Path],
    validate_fn: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    return _run_mutation_case(
        base_dir=base_dir,
        checkpoint_root=checkpoint_root,
        case_work_root=case_work_root,
        case=case,
        mutate_fn=mutate_fn,
        validate_fn=validate_fn,
    )


def run_determinism_mutation(
    *,
    base_dir: Path,
    checkpoint_root: Path,
    case_work_root: Path,
    case: MutationCase,
    mutate_fn: Callable[[Path], Path],
    validate_fn: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    return _run_mutation_case(
        base_dir=base_dir,
        checkpoint_root=checkpoint_root,
        case_work_root=case_work_root,
        case=case,
        mutate_fn=mutate_fn,
        validate_fn=validate_fn,
    )


def write_negative_test_matrix(path: Path, rows: list[dict[str, Any]]) -> None:
    _write_csv(path, [json_safe(row) for row in rows])


def write_negative_test_summary(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "total_count": len(rows),
        "mutation_effective_count": sum(1 for row in rows if row["mutation_effective"]),
        "production_validator_invoked_count": sum(
            1
            for row in rows
            if row.get("production_validator_name") or row.get("production_validator_invoked")
        ),
        "unexpected_negative_test_pass_count": sum(1 for row in rows if not row["rejected_as_expected"]),
        "negative_tests_passed": all(row["rejected_as_expected"] for row in rows),
    }
    write_json(path, summary)
    return summary


def add_label(gds_path: Path, top_name: str, text: str, origin: tuple[float, float], *, layer: int = 11, texttype: int = 2) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    top.add(gdstk.Label(text, origin, layer=layer, texttype=texttype))
    lib.write_gds(gds_path)


def remove_label(gds_path: Path, top_name: str, text: str) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    victims = [label for label in top.labels if str(label.text) == text]
    if victims:
        top.remove(*victims)
    lib.write_gds(gds_path)


def swap_labels(gds_path: Path, top_name: str, left: str, right: str) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    left_label = next(label for label in top.labels if str(label.text) == left)
    right_label = next(label for label in top.labels if str(label.text) == right)
    left_label.origin, right_label.origin = right_label.origin, left_label.origin
    lib.write_gds(gds_path)


def add_off_grid_rect(gds_path: Path, top_name: str, bbox: tuple[float, float, float, float], *, layer: int = 11) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    top.add(gdstk.rectangle((bbox[0], bbox[1]), (bbox[2], bbox[3]), layer=layer, datatype=0))
    lib.write_gds(gds_path)
