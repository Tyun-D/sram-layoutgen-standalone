from pathlib import Path

from sram_layoutgen.openyield_adapter.production_negative_test_harness import MutationCase


def test_mutation_case_dataclass_fields() -> None:
    case = MutationCase(
        test_id="t01",
        mutation_kind="contract",
        expected_rejection_code="X",
        expected_rejection_family="STRUCTURAL",
        baseline_input_path=Path("foo.json"),
        validator_name="validate",
    )
    assert case.test_id == "t01"
    assert case.baseline_input_path == Path("foo.json")
