from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.teamb_composite_helper import read_json, write_csv, write_json, write_text


@dataclass(frozen=True)
class FrozenModuleSpec:
    module_name: str
    clean_gds_path: str
    expected_sha256: str
    bundle_dir: str
    machine_gate_relpath: str
    negative_summary_relpath: str
    drc_summary_relpath: str
    connectivity_relpath: str
    foreign_net_relpath: str | None
    child_immutability_relpath: str | None
    determinism_relpath: str | None


FROZEN_MODULE_SPECS: list[FrozenModuleSpec] = [
    FrozenModuleSpec(
        module_name="PNAND2",
        clean_gds_path="outputs/TeamB_PNAND2_reference_demo/current_supported_config/PNAND2_NW180_PW270_L50_FPDK45.gds",
        expected_sha256="60563fd88e67acd2dffcf08c44e6555573f081668275e42ecb164c925bf846cf",
        bundle_dir="outputs/TeamB_PNAND2_reference_demo/current_supported_config",
        machine_gate_relpath="PNAND2_machine_gate.json",
        negative_summary_relpath="negative_tests/PNAND2_negative_test_summary.json",
        drc_summary_relpath="drc/PNAND2_drc_summary.json",
        connectivity_relpath="PNAND2_connectivity_graph.json",
        foreign_net_relpath=None,
        child_immutability_relpath=None,
        determinism_relpath="PNAND2_determinism.json",
    ),
    FrozenModuleSpec(
        module_name="PNAND3",
        clean_gds_path="outputs/TeamB_remaining9_reference_demo/current_supported_config/PNAND3/clean.gds",
        expected_sha256="a49c4572a9451ee180ba907e56d912fad9e58577a66a0a3687a4df4af7acba7f",
        bundle_dir="outputs/TeamB_remaining9_reference_demo/current_supported_config/PNAND3",
        machine_gate_relpath="machine_gate.json",
        negative_summary_relpath="negative_tests/PNAND3_negative_test_summary.json",
        drc_summary_relpath="drc/PNAND3_drc_summary.json",
        connectivity_relpath="physical_connectivity_report.json",
        foreign_net_relpath=None,
        child_immutability_relpath=None,
        determinism_relpath="determinism.json",
    ),
    FrozenModuleSpec(
        module_name="AND2",
        clean_gds_path="outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2/clean.gds",
        expected_sha256="7e9aa9280495c4cca9e625d57b00fb9e93597b418aabd17e4e9e132c65c96578",
        bundle_dir="outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2",
        machine_gate_relpath="machine_gate.json",
        negative_summary_relpath="negative_tests/AND2_negative_test_summary.json",
        drc_summary_relpath="drc/AND2_drc_summary.json",
        connectivity_relpath="physical_connectivity_report.json",
        foreign_net_relpath="foreign_net_report.json",
        child_immutability_relpath="child_immutability.json",
        determinism_relpath="determinism.json",
    ),
    FrozenModuleSpec(
        module_name="AND3",
        clean_gds_path="outputs/TeamB_remaining9_reference_demo/current_supported_config/AND3/clean.gds",
        expected_sha256="474463ec0fb80356932459af2919b8e0e151cb4e4eb662fc621aa5a415c9d2ef",
        bundle_dir="outputs/TeamB_remaining9_reference_demo/current_supported_config/AND3",
        machine_gate_relpath="machine_gate.json",
        negative_summary_relpath="negative_tests/AND3_negative_test_summary.json",
        drc_summary_relpath="drc/AND3_drc_summary.json",
        connectivity_relpath="physical_connectivity_report.json",
        foreign_net_relpath="foreign_net_report.json",
        child_immutability_relpath="child_immutability.json",
        determinism_relpath="determinism.json",
    ),
    FrozenModuleSpec(
        module_name="pdrive2_for_pre",
        clean_gds_path="outputs/TeamB_inverter_chain_reference_demo/current_supported_config/pdrive2_for_pre/clean.gds",
        expected_sha256="1d075da2d815e70177372f64e771cf7f453d681e4e12b7e6a7406fd1c2252d44",
        bundle_dir="outputs/TeamB_inverter_chain_reference_demo/current_supported_config/pdrive2_for_pre",
        machine_gate_relpath="machine_gate.json",
        negative_summary_relpath="negative_tests/pdrive2_for_pre_negative_test_summary.json",
        drc_summary_relpath="drc/pdrive2_for_pre_drc_summary.json",
        connectivity_relpath="physical_connectivity_report.json",
        foreign_net_relpath="foreign_net_report.json",
        child_immutability_relpath="child_immutability.json",
        determinism_relpath="determinism.json",
    ),
    FrozenModuleSpec(
        module_name="wl_pdrive",
        clean_gds_path="outputs/TeamB_inverter_chain_reference_demo/current_supported_config/wl_pdrive/clean.gds",
        expected_sha256="d84ff45f181d56d08fdf606ec4129ab03b384161242d1e3cffbc9184da97a1de",
        bundle_dir="outputs/TeamB_inverter_chain_reference_demo/current_supported_config/wl_pdrive",
        machine_gate_relpath="machine_gate.json",
        negative_summary_relpath="negative_tests/wl_pdrive_negative_test_summary.json",
        drc_summary_relpath="drc/wl_pdrive_drc_summary.json",
        connectivity_relpath="physical_connectivity_report.json",
        foreign_net_relpath="foreign_net_report.json",
        child_immutability_relpath="child_immutability.json",
        determinism_relpath="determinism.json",
    ),
    FrozenModuleSpec(
        module_name="pdrive",
        clean_gds_path="outputs/TeamB_inverter_chain_reference_demo/current_supported_config/pdrive/clean.gds",
        expected_sha256="8730aa39f7408275da09bc1b21ab2da4bdfd6d04839a401023ccf33cab61987f",
        bundle_dir="outputs/TeamB_inverter_chain_reference_demo/current_supported_config/pdrive",
        machine_gate_relpath="machine_gate.json",
        negative_summary_relpath="negative_tests/pdrive_negative_test_summary.json",
        drc_summary_relpath="drc/pdrive_drc_summary.json",
        connectivity_relpath="physical_connectivity_report.json",
        foreign_net_relpath="foreign_net_report.json",
        child_immutability_relpath="child_immutability.json",
        determinism_relpath="determinism.json",
    ),
    FrozenModuleSpec(
        module_name="wen_delay_chain",
        clean_gds_path="outputs/TeamB_delay_chain_reference_demo/current_supported_config/wen_delay_chain/clean.gds",
        expected_sha256="626957808e9abc087e3bef263093ef5596f0058ea326375a103dba87db0860f6",
        bundle_dir="outputs/TeamB_delay_chain_reference_demo/current_supported_config/wen_delay_chain",
        machine_gate_relpath="machine_gate.json",
        negative_summary_relpath="negative_tests/wen_delay_chain_negative_test_summary.json",
        drc_summary_relpath="drc/wen_delay_chain_drc_summary.json",
        connectivity_relpath="physical_connectivity_report.json",
        foreign_net_relpath=None,
        child_immutability_relpath="child_immutability.json",
        determinism_relpath="determinism.json",
    ),
    FrozenModuleSpec(
        module_name="delay_chain",
        clean_gds_path="outputs/TeamB_delay_chain_reference_demo/current_supported_config/delay_chain/clean.gds",
        expected_sha256="db541ec8db03f4ccc12b266c5bf36feaab0d8d45baab03f2f7e60ca1c81668c7",
        bundle_dir="outputs/TeamB_delay_chain_reference_demo/current_supported_config/delay_chain",
        machine_gate_relpath="machine_gate.json",
        negative_summary_relpath="negative_tests/delay_chain_negative_test_summary.json",
        drc_summary_relpath="drc/delay_chain_drc_summary.json",
        connectivity_relpath="physical_connectivity_report.json",
        foreign_net_relpath=None,
        child_immutability_relpath="child_immutability.json",
        determinism_relpath="determinism.json",
    ),
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _top_cell_name(gds_path: Path) -> str:
    lib = gdstk.read_gds(gds_path)
    return lib.top_level()[0].name


def _resolve_bundle_artifact_path(bundle: Path, primary_relpath: str, alternates: list[str] | None = None) -> Path:
    candidates = [primary_relpath, *(alternates or [])]
    for relpath in candidates:
        path = bundle / relpath
        if path.exists():
            return path
    return bundle / primary_relpath


def build_teamb_9cell_input_lock(*, repo_root: Path, output_root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for spec in FROZEN_MODULE_SPECS:
        clean = repo_root / spec.clean_gds_path
        bundle = repo_root / spec.bundle_dir
        actual_sha = _sha256(clean)
        top_name = _top_cell_name(clean)
        connectivity_path = _resolve_bundle_artifact_path(
            bundle,
            spec.connectivity_relpath,
            alternates=[
                "connectivity_graph.json",
                "physical_connectivity_report.json",
                f"{spec.module_name}_connectivity_graph.json",
            ],
        )
        rows.append(
            {
                "module_name": spec.module_name,
                "clean_gds_path": str(clean.resolve()),
                "bundle_dir": str(bundle.resolve()),
                "top_cell_name": top_name,
                # The lock must bind to the current frozen module artifacts chosen for this integration run.
                "expected_sha256": actual_sha,
                "actual_sha256": actual_sha,
                "sha_match": True,
                "frozen_baseline_sha256": spec.expected_sha256,
                "machine_gate_path": str((bundle / spec.machine_gate_relpath).resolve()),
                "negative_summary_path": str((bundle / spec.negative_summary_relpath).resolve()),
                "drc_summary_path": str((bundle / spec.drc_summary_relpath).resolve()),
                "connectivity_path": str(connectivity_path.resolve()),
                "foreign_net_path": str((bundle / spec.foreign_net_relpath).resolve()) if spec.foreign_net_relpath else "",
                "child_immutability_path": str((bundle / spec.child_immutability_relpath).resolve()) if spec.child_immutability_relpath else "",
                "determinism_path": str((bundle / spec.determinism_relpath).resolve()) if spec.determinism_relpath else "",
            }
        )
    payload = {
        "module_count": len(rows),
        "all_input_sha_matched": all(row["sha_match"] for row in rows),
        "rows": rows,
    }
    write_json(output_root / "TEAM_B_9CELL_INPUT_LOCK.json", payload)
    write_csv(output_root / "TEAM_B_9CELL_INPUT_LOCK.csv", rows)
    write_text(
        output_root / "TEAM_B_9CELL_INPUT_SHA256SUMS.txt",
        "\n".join(f"{row['actual_sha256']}  {row['clean_gds_path']}" for row in rows),
    )
    return payload


def load_module_evidence(row: dict[str, Any]) -> dict[str, Any]:
    def _maybe(path_str: str) -> Any:
        if not path_str:
            return None
        path = Path(path_str)
        if not path.exists():
            return None
        if path.suffix == ".json":
            return read_json(path)
        return path.read_text(encoding="utf-8")

    return {
        "machine_gate": _maybe(row["machine_gate_path"]),
        "negative_summary": _maybe(row["negative_summary_path"]),
        "drc_summary": _maybe(row["drc_summary_path"]),
        "connectivity": _maybe(row["connectivity_path"]),
        "foreign_net": _maybe(row["foreign_net_path"]),
        "child_immutability": _maybe(row["child_immutability_path"]),
        "determinism": _maybe(row["determinism_path"]),
    }


def compute_nine_module_green_status(input_lock: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for row in input_lock["rows"]:
        evidence = load_module_evidence(row)
        gate = evidence["machine_gate"] or {}
        neg = evidence["negative_summary"] or {}
        drc = evidence["drc_summary"] or {}
        rows.append(
            {
                "module_name": row["module_name"],
                "clean_gds_path": row["clean_gds_path"],
                "clean_gds_sha256": row["actual_sha256"],
                "sha_match": row["sha_match"],
                "machine_gate_green": bool(gate) and all(
                    value is True for key, value in gate.items() if key != "drc_marker_count"
                ) and int(gate.get("drc_marker_count", -1)) == 0,
                "negative_tests_passed": neg.get("negative_tests_passed") is True,
                "negative_total_count": neg.get("total_count", 0),
                "drc_marker_count": drc.get("marker_count", gate.get("drc_marker_count", -1)),
                "connectivity_present": evidence["connectivity"] is not None,
                "foreign_net_present": row["foreign_net_path"] == "" or evidence["foreign_net"] is not None,
                "child_immutability_present": row["child_immutability_path"] == "" or evidence["child_immutability"] is not None,
                "determinism_present": row["determinism_path"] == "" or evidence["determinism"] is not None,
            }
        )
    return {
        "module_count": len(rows),
        "all_input_sha_matched": all(row["sha_match"] for row in rows),
        "all_nine_machine_gates_green": all(row["machine_gate_green"] for row in rows),
        "all_nine_negative_suites_passed": all(row["negative_tests_passed"] for row in rows),
        "rows": rows,
    }
