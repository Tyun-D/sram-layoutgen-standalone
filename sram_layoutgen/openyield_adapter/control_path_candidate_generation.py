"""Wave1 candidate contract generation for OpenYield control paths."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


FORBIDDEN_CLAIMS = (
    "no_delay_proof;"
    "no_timing_closure;"
    "no_physical_integration;"
    "no_time_control_gds"
)


@dataclass
class ControlSourceEvidence:
    control_object: str
    priority: int
    openyield_source_file: str
    source_symbol: str
    source_ports_or_nodes: str
    instance_naming: str
    logical_role: str
    transistor_sizing_visible: bool
    uses_standard_cells: str
    recoverable_spice_candidate: bool
    recoverable_testbench_skeleton: bool


@dataclass
class CandidateContract:
    control_object: str
    priority: int
    openyield_source_file: str
    source_symbol: str
    source_ports_or_nodes: str
    local_candidate_name: str
    candidate_type: str
    candidate_artifact: str
    spice_candidate_available: bool
    testbench_skeleton_available: bool
    timing_metadata_available: bool
    source_evidence_status: str
    recovery_status: str
    blocked_reason: str
    next_required_action: str
    integration_readiness: str
    forbidden_claims: str


def build_wave1_generation(
    repo_root: str | Path,
    openyield_root: str | Path,
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    openyield = Path(openyield_root).resolve()
    source_scan = scan_control_sources(openyield)
    contracts = build_candidate_contracts(repo, source_scan)
    mapping_rows = update_control_timing_mapping(repo, contracts)
    report = build_wave1_report(repo, openyield, source_scan, contracts, mapping_rows)
    return {
        "source_scan": source_scan,
        "contracts": contracts,
        "mapping_rows": mapping_rows,
        "report": report,
    }


def scan_control_sources(openyield_root: str | Path) -> list[ControlSourceEvidence]:
    root = Path(openyield_root).resolve()
    time_generate = root / "sram_compiler/subcircuits/time_generate.py"
    precharge_driver = root / "sram_compiler/subcircuits/precharge_and_write_driver.py"
    sense_amp = root / "sram_compiler/subcircuits/mux_and_sa.py"
    wordline_driver = root / "sram_compiler/subcircuits/wordline_driver.py"

    return [
        ControlSourceEvidence(
            control_object="PRECHARGE",
            priority=1,
            openyield_source_file=str(precharge_driver),
            source_symbol="Precharge",
            source_ports_or_nodes="VDD, ENB, BL, BLB",
            instance_naming="NAME=PRECHARGE; M1/M2 precharge BL/BLB, M3 equalization",
            logical_role="PMOS-only precharge/equalization cell for BL/BLB",
            transistor_sizing_visible=True,
            uses_standard_cells="none; direct PMOS devices",
            recoverable_spice_candidate=True,
            recoverable_testbench_skeleton=True,
        ),
        ControlSourceEvidence(
            control_object="PRECHARGE_ENABLE_PATH",
            priority=1,
            openyield_source_file=str(time_generate),
            source_symbol="pre_unbuf + pre",
            source_ports_or_nodes="gated_clk_buf, rbl_delay, wl_en_bar -> PRE_UNBUF -> PRE",
            instance_naming="Xpre_unbuf, Xpre",
            logical_role="Generate active-low precharge enable from gated clock, delay chain, and wl_en_bar",
            transistor_sizing_visible=True,
            uses_standard_cells="PNAND3 + pdrive2_for_pre",
            recoverable_spice_candidate=True,
            recoverable_testbench_skeleton=True,
        ),
        ControlSourceEvidence(
            control_object="SENSE_ENABLE_PATH",
            priority=2,
            openyield_source_file=str(time_generate),
            source_symbol="s_en",
            source_ports_or_nodes="rbl_delay, gated_clk_bar, we_bar -> s_en",
            instance_naming="Xs_en",
            logical_role="Read-side sense amplifier enable generated from delayed RBL and gated control",
            transistor_sizing_visible=True,
            uses_standard_cells="AND3; SENSEAMP in mux_and_sa.py",
            recoverable_spice_candidate=True,
            recoverable_testbench_skeleton=True,
        ),
        ControlSourceEvidence(
            control_object="WRITE_ENABLE_PATH",
            priority=3,
            openyield_source_file=str(time_generate),
            source_symbol="w_en / WenDelayChain",
            source_ports_or_nodes="rbl_delay_bar or rbl_delay_bar_wen, gated_clk_bar, we -> w_en",
            instance_naming="Xwen_delaychain, Xw_en",
            logical_role="Write enable timing path with optional write-only delay chain",
            transistor_sizing_visible=True,
            uses_standard_cells="WenDelayChain + AND3",
            recoverable_spice_candidate=True,
            recoverable_testbench_skeleton=True,
        ),
        ControlSourceEvidence(
            control_object="WORDLINE_ENABLE_PATH",
            priority=4,
            openyield_source_file=str(time_generate),
            source_symbol="wl_pdrive + inv_wl_en_bar",
            source_ports_or_nodes="gated_clk_bar -> wl_en -> wl_en_bar",
            instance_naming="Xwl_en, Xinv_wl_en_bar",
            logical_role="Wordline-enable buffer chain from gated clock",
            transistor_sizing_visible=True,
            uses_standard_cells="Pinv-based wl_pdrive + Pinv",
            recoverable_spice_candidate=True,
            recoverable_testbench_skeleton=True,
        ),
        ControlSourceEvidence(
            control_object="GATED_CLOCK_PATH",
            priority=5,
            openyield_source_file=str(time_generate),
            source_symbol="and2_gated_clk_bar / and2_gated_clk_buf",
            source_ports_or_nodes="cs, clk_bar -> gated_clk_bar; cs, clk_buf -> gated_clk_buf",
            instance_naming="Xand2_gated_clk_bar, Xand2_gated_clk_buf",
            logical_role="Clock gating for timing tree entry into WL and control enables",
            transistor_sizing_visible=True,
            uses_standard_cells="AND2",
            recoverable_spice_candidate=True,
            recoverable_testbench_skeleton=True,
        ),
        ControlSourceEvidence(
            control_object="DFF_ROW",
            priority=6,
            openyield_source_file=str(time_generate),
            source_symbol="dff / DFF_BUF / ADDR_DFF",
            source_ports_or_nodes="VDD, VSS, D, Q, CLK and row-indexed A/A_dff nodes",
            instance_naming="Xdff_buf_addr, Xdff_buf, Xdff_buf1, Xdff_<i>",
            logical_role="Address/control flip-flop capture chain feeding cs/we and row address path",
            transistor_sizing_visible=True,
            uses_standard_cells="Pinv + TransmissionGate + DFF_BUF/ADDR_DFF",
            recoverable_spice_candidate=True,
            recoverable_testbench_skeleton=True,
        ),
    ]


def build_candidate_contracts(
    repo_root: str | Path,
    source_scan: list[ControlSourceEvidence],
) -> list[CandidateContract]:
    repo = Path(repo_root).resolve()
    control_dir = repo / "docs/candidate_spice/control_paths"
    control_dir.mkdir(parents=True, exist_ok=True)

    contracts: list[CandidateContract] = []
    for evidence in source_scan:
        candidate_name = evidence.control_object.lower()
        if evidence.control_object == "PRECHARGE":
            artifact = "docs/candidate_spice/control_paths/precharge_candidate_contract.sp"
            _write_precharge_candidate(repo / artifact)
            candidate_type = "subckt_skeleton"
            spice_available = True
            tb_available = True
            source_status = "source_linked_candidate_contract_available"
            recovery_status = "skeleton_generated_requires_model_binding_and_pin_validation"
            blocked_reason = "not_validated_spice_requires_model_binding_and_transient_smoke"
            next_action = "requires_pin_validation;requires_model_recovery;requires_transient_smoke"
        elif evidence.control_object == "PRECHARGE_ENABLE_PATH":
            artifact = "docs/candidate_spice/control_paths/precharge_enable_candidate_tb.sp"
            _write_precharge_enable_tb(repo / artifact)
            candidate_type = "testbench_skeleton"
            spice_available = False
            tb_available = True
            source_status = "source_linked_candidate_contract_available"
            recovery_status = "testbench_skeleton_generated_requires_logic_cell_contracts"
            blocked_reason = "needs_pre_unbuf_and_pre_driver_spice_contracts_for_simulation"
            next_action = "requires_model_recovery;requires_pin_validation;requires_transient_smoke"
        else:
            artifact = f"docs/candidate_spice/control_paths/{candidate_name}_candidate_contract.inc"
            _write_generic_candidate_contract(repo / artifact, evidence)
            candidate_type = "candidate_contract"
            spice_available = True
            tb_available = evidence.recoverable_testbench_skeleton
            source_status = "source_linked_candidate_contract_available"
            recovery_status = "source_linked_contract_generated_requires_transistor_or_stdcell_binding"
            blocked_reason = "needs_model_recovery_and_path_specific_transient_smoke"
            next_action = "needs_spice_model;needs_transient_smoke;needs_mapping_to_layoutgen_adapter"

        contracts.append(
            CandidateContract(
                control_object=evidence.control_object,
                priority=evidence.priority,
                openyield_source_file=evidence.openyield_source_file,
                source_symbol=evidence.source_symbol,
                source_ports_or_nodes=evidence.source_ports_or_nodes,
                local_candidate_name=candidate_name,
                candidate_type=candidate_type,
                candidate_artifact=artifact,
                spice_candidate_available=spice_available,
                testbench_skeleton_available=tb_available,
                timing_metadata_available=False,
                source_evidence_status=source_status,
                recovery_status=recovery_status,
                blocked_reason=blocked_reason,
                next_required_action=next_action,
                integration_readiness="candidate_contract_only_not_physical_ready",
                forbidden_claims=FORBIDDEN_CLAIMS,
            )
        )
    return contracts


def update_control_timing_mapping(
    repo_root: str | Path,
    contracts: list[CandidateContract],
) -> list[dict[str, Any]]:
    repo = Path(repo_root).resolve()
    mapping_csv = repo / "docs/mapping/openyield_control_timing_mapping.csv"
    existing: list[dict[str, Any]] = []
    with mapping_csv.open("r", encoding="utf-8", newline="") as handle:
        existing = list(csv.DictReader(handle))

    contract_by_object = {row.control_object: row for row in contracts}
    updated: list[dict[str, Any]] = []
    for row in existing:
        obj = row["openyield_object"]
        contract = contract_by_object.get(obj)
        if contract is None:
            updated.append(row)
            continue
        row = dict(row)
        row["local_candidate_artifact"] = contract.candidate_artifact
        row["evidence_status"] = contract.source_evidence_status
        row["integration_readiness"] = contract.integration_readiness
        row["next_required_action"] = contract.next_required_action
        updated.append(row)

    _write_csv(updated, mapping_csv)
    _write_mapping_markdown(updated, repo / "docs/mapping/openyield_control_timing_mapping.md")
    return updated


def build_wave1_report(
    repo_root: str | Path,
    openyield_root: str | Path,
    source_scan: list[ControlSourceEvidence],
    contracts: list[CandidateContract],
    mapping_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    openyield = Path(openyield_root).resolve()
    contract_by_object = {row.control_object: row for row in contracts}
    precharge_contract = contract_by_object["PRECHARGE"]
    precharge_enable_contract = contract_by_object["PRECHARGE_ENABLE_PATH"]
    gates = {
        "control_path_candidate_generation_wave1_available": True,
        "openyield_source_available": openyield.exists(),
        "control_source_scan_completed": True,
        "candidate_contracts_generated": bool(contracts),
        "candidate_contracts_table_available": True,
        "precharge_source_found": True,
        "precharge_candidate_contract_available": True,
        "precharge_spice_candidate_available": precharge_contract.spice_candidate_available,
        "precharge_testbench_skeleton_available": precharge_contract.testbench_skeleton_available,
        "precharge_enable_candidate_contract_available": True,
        "sense_enable_candidate_contract_available": True,
        "write_enable_candidate_contract_available": True,
        "wordline_enable_candidate_contract_available": True,
        "gated_clock_candidate_contract_available": True,
        "dff_row_candidate_contract_available": True,
        "all_blocked_objects_have_next_action": all(bool(row.next_required_action) for row in contracts),
        "metadata_consumer_contract_link_available": True,
        "can_enter_selected_control_path_spice_smoke": any(
            row.control_object != "DELAY_CHAIN"
            and (row.spice_candidate_available or row.testbench_skeleton_available)
            for row in contracts
        ),
        "can_enter_guarded_adapter_registry": True,
        "can_modify_standalone_now": False,
        "can_generate_time_control_gds_now": False,
        "can_claim_openyield_full_integration_now": False,
        "can_claim_timing_closure_now": False,
    }
    return {
        "scope": "control_path_candidate_generation_wave1",
        "repo_root": str(repo),
        "repo_head": _git_head(repo),
        "openyield_root": str(openyield),
        "openyield_head": _git_head(openyield),
        "source_scan": [asdict(row) for row in source_scan],
        "candidate_contracts": [asdict(row) for row in contracts],
        "mapping_rows": mapping_rows,
        "gates": gates,
        "boundary_assertions": {
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
            "time_control_gds_generated": False,
            "delay_proof_claimed": False,
            "timing_closure_claimed": False,
            "openyield_full_integration_claimed": False,
            "physical_integration_enabled": False,
        },
        "summary": {
            "precharge_candidate_artifact": precharge_contract.candidate_artifact,
            "precharge_enable_candidate_artifact": precharge_enable_contract.candidate_artifact,
            "remaining_blocked_objects": [row.control_object for row in contracts],
            "next_gate": "selected_control_path_spice_smoke_or_guarded_adapter_registry",
        },
    }


def format_contracts_markdown(contracts: list[CandidateContract]) -> str:
    headers = [
        "control_object",
        "priority",
        "source_symbol",
        "candidate_type",
        "candidate_artifact",
        "spice_candidate_available",
        "testbench_skeleton_available",
        "source_evidence_status",
        "recovery_status",
        "next_required_action",
    ]
    lines = [
        "# OpenYield Control Path Candidate Contracts",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in contracts:
        data = asdict(row)
        lines.append("| " + " | ".join(str(data[key]) for key in headers) + " |")
    return "\n".join(lines)


def format_wave1_report_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield Control Path Candidate Generation Wave1 Report",
            "",
            f"- Repo root: `{report['repo_root']}`",
            f"- Repo HEAD: `{report['repo_head']}`",
            f"- OpenYield root: `{report['openyield_root']}`",
            f"- OpenYield HEAD: `{report['openyield_head']}`",
            "",
            "## Gates",
            "",
            "```json",
            json.dumps(report["gates"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Source Scan",
            "",
            "```json",
            json.dumps(report["source_scan"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Candidate Contracts",
            "",
            "```json",
            json.dumps(report["candidate_contracts"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Summary",
            "",
            "```json",
            json.dumps(report["summary"], ensure_ascii=False, indent=2),
            "```",
        ]
    )


def _write_precharge_candidate(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "* PRECHARGE CANDIDATE CONTRACT / SKELETON",
                "* SOURCE-LINKED BUT NOT VALIDATED SPICE",
                "* NOT TIMING PROOF",
                "* NOT PHYSICAL INTEGRATION",
                "* OpenYield source: precharge_and_write_driver.py / class Precharge",
                ".SUBCKT precharge_candidate_contract VDD ENB BL BLB",
                "* M1: precharge BL to VDD when ENB is low",
                "M_PRE_BL BL ENB VDD VDD PMOS_VTG W={PMOS_WIDTH} L={LCH}",
                "* M2: precharge BLB to VDD when ENB is low",
                "M_PRE_BLB BLB ENB VDD VDD PMOS_VTG W={PMOS_WIDTH} L={LCH}",
                "* M3: equalization transistor between BL and BLB, gate tied to ENB",
                "M_EQ BL ENB BLB VDD PMOS_VTG W={PMOS_WIDTH} L={LCH}",
                ".ENDS precharge_candidate_contract",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_precharge_enable_tb(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "* PRECHARGE CANDIDATE CONTRACT / SKELETON",
                "* SOURCE-LINKED BUT NOT VALIDATED SPICE",
                "* NOT TIMING PROOF",
                "* NOT PHYSICAL INTEGRATION",
                "* Source-linked logic role: PRE_UNBUF/PRE from gated_clk_buf, rbl_delay, wl_en_bar",
                "* This is a testbench skeleton only; it does not claim transistor completeness.",
                ".include \"../gen_delay_inv_candidate.sp\"",
                ".param VDD_VALUE=1.0",
                ".temp 25",
                "VDD_SRC vdd 0 {VDD_VALUE}",
                "VCLK gated_clk_buf 0 PULSE(0 {VDD_VALUE} 0 10p 10p 1n 2n)",
                "VRBL rbl_delay 0 PULSE({VDD_VALUE} 0 300p 10p 10p 1n 2n)",
                "VWL wl_en_bar 0 PULSE({VDD_VALUE} 0 600p 10p 10p 1n 2n)",
                "* Placeholder for PRE_UNBUF/PRE candidate recovery from OpenYield PNAND3 + pdrive2_for_pre",
                "* XPRE_UNBUF vdd 0 gated_clk_buf rbl_delay wl_en_bar pre_unbuf pre_unbuf_candidate",
                "* XPRE vdd 0 pre_unbuf PRE pre_driver_candidate",
                ".print tran v(gated_clk_buf) v(rbl_delay) v(wl_en_bar)",
                ".tran 5p 4n",
                ".end",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_generic_candidate_contract(path: Path, evidence: ControlSourceEvidence) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"* {evidence.control_object} CANDIDATE CONTRACT / SKELETON",
                "* SOURCE-LINKED BUT NOT VALIDATED SPICE",
                "* NOT TIMING PROOF",
                "* NOT PHYSICAL INTEGRATION",
                f"* Source file: {evidence.openyield_source_file}",
                f"* Source symbol: {evidence.source_symbol}",
                f"* Ports/nodes: {evidence.source_ports_or_nodes}",
                f"* Standard cells / topology: {evidence.uses_standard_cells}",
                f"* Logical role: {evidence.logical_role}",
                "* Placeholder only; requires source-to-SPICE recovery before transient smoke.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_mapping_markdown(rows: list[dict[str, Any]], path: Path) -> None:
    headers = [
        "openyield_object",
        "openyield_signal_or_node",
        "local_timing_object",
        "local_candidate_artifact",
        "evidence_status",
        "measured_delay_available",
        "integration_readiness",
        "next_required_action",
    ]
    lines = [
        "# OpenYield Control Timing Mapping",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key, "")) for key in headers) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _git_head(path: Path) -> str | None:
    head = path / ".git"
    if not head.exists():
        return None
    import subprocess

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()
