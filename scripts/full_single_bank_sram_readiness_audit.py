#!/usr/bin/env python3
"""Audit whether the remaining assets can enter full single-bank SRAM layout.

The audit is intentionally conservative. It records exact files that exist and
blocks full-top generation unless every requested module has real GDS, pin
authority, DRC/connectivity/foreign-net/pin-access evidence, determinism, and a
negative suite suitable for top-level use.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs/PROJECT_full_single_bank_sram"


def sha256(path: Path | None) -> str:
    if path is None or not path.exists():
        return "NOT_FOUND"
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path | None) -> str:
    if path is None:
        return "NOT_FOUND"
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return path.as_posix()


def exists(path: str) -> Path | None:
    p = REPO / path
    return p if p.exists() else None


def git(cmd: list[str]) -> str:
    return subprocess.check_output(["git", *cmd], cwd=REPO, text=True).strip()


def load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def top_cells_from_gds(path: Path | None) -> list[str]:
    if path is None or not path.exists():
        return []
    try:
        import gdspy  # type: ignore

        lib = gdspy.GdsLibrary(infile=str(path))
        referenced = {
            ref.ref_cell.name
            for cell in lib.cells.values()
            for ref in cell.references
            if hasattr(ref, "ref_cell")
        }
        return sorted(name for name in lib.cells if name not in referenced)
    except Exception as exc:  # pragma: no cover - defensive diagnostic path
        return [f"GDS_PARSE_FAILED:{type(exc).__name__}:{exc}"]


@dataclass(frozen=True)
class ModuleSpec:
    module_id: str
    role: str
    logical_source: str
    spice: str | None
    gds: str | None
    pin_source: str | None
    evidence: list[str]
    blocker: list[str]
    ready: bool
    use_in_current_top: str
    authority_note: str


def module_specs() -> list[ModuleSpec]:
    return [
        ModuleSpec(
            "precharge",
            "column_path",
            "sram_layoutgen/netlist_writer.py; /data1/qujh/My_OpenYield/LiteRAM-Layout/literam/modules/precharge.py",
            None,
            "outputs/openyield_module_gds/precharge/precharge.gds",
            "outputs/openyield_module_gds/precharge/pins.json",
            [
                "outputs/openyield_module_gds/precharge/generator_manifest.json",
                "docs/openyield_time_control_consumer_contract_report.json",
                "/data1/qujh/PAPER_EVIDENCE_PACKAGE_20260713_043712.tar.gz",
            ],
            [
                "precharge module manifest says boundary pins are contract-backed and need L4/L5 verification",
                "no standalone DRC=0 evidence found for the current precharge_v2 top-use asset",
                "no final-GDS power endpoint coverage / foreign-net / negative-suite evidence found for precharge_v2",
            ],
            False,
            "required",
            "Physical hardmacro exists, but not qualified to this stage's top-entry gate.",
        ),
        ModuleSpec(
            "column_mux",
            "column_path",
            "sram_layoutgen/netlist_writer.py; /data1/qujh/My_OpenYield/LiteRAM-Layout/literam/modules/column_mux.py",
            None,
            "outputs/openyield_module_gds/column_mux/column_mux.gds",
            "outputs/openyield_module_gds/column_mux/pins.json",
            [
                "outputs/openyield_module_gds/column_mux/generator_manifest.json",
                "docs/openyield_columnmux_adapter_report.json",
                "outputs/M6R_reference_locked_reproduce/current_supported_config/M6R_column_mux_real_check.json",
            ],
            [
                "formal 16x16/wpr1 config has words_per_row=1, so column-mux use conflicts with current exact config unless owner redefines top contract",
                "adapter evidence reports VDD shape_source=missing for local gen_col_mux canonical pin",
                "no standalone DRC=0/connectivity/foreign-net/negative-suite evidence found for column_mux_v2 top-use asset",
            ],
            False,
            "authority_conflict_for_16x16_wpr1",
            "The user-requested column-mux path is not yet reconciled with the locked wpr1 config.",
        ),
        ModuleSpec(
            "sense_amplifier",
            "column_path",
            "sram_layoutgen/netlist_writer.py; /data1/qujh/My_OpenYield/LiteRAM-Layout/literam/modules/sense_amp.py",
            "technology/freepdk45/sp_lib/sense_amp.sp",
            "outputs/openyield_module_gds/sense_amp/sense_amp.gds",
            "outputs/openyield_module_gds/sense_amp/pins.json",
            [
                "docs/openyield_senseamp_adapter_report.json",
                "docs/M11V_routing_power_connectivity_verification_report.json",
                "outputs/openyield_module_gds/sense_amp/generator_manifest.json",
            ],
            [
                "M11V evidence is isolated substitution/risk heuristic and explicitly cannot claim routing/power/DRC/signoff ready",
                "no standalone module machine gate with DRC=0, final power endpoint coverage, foreign-net, and negative suite found",
            ],
            False,
            "required",
            "GDS and SPICE exist, but the top-use qualification gate is not closed.",
        ),
        ModuleSpec(
            "write_driver",
            "column_path",
            "sram_layoutgen/netlist_writer.py; /data1/qujh/My_OpenYield/LiteRAM-Layout/literam/modules/write_driver.py",
            "technology/freepdk45/sp_lib/write_driver.sp",
            "outputs/openyield_module_gds/write_driver/write_driver.gds",
            "outputs/openyield_module_gds/write_driver/pins.json",
            [
                "docs/openyield_writedriver_adapter_report.json",
                "outputs/openyield_module_gds/write_driver/generator_manifest.json",
            ],
            [
                "no standalone DRC=0/connectivity/foreign-net/pin-access/negative-suite machine gate found for write_driver_v2",
                "write-driver use in complete top needs BL/BR/DIN/write-enable physical route proof, which is absent",
            ],
            False,
            "required",
            "GDS and SPICE exist, but the top-use qualification gate is not closed.",
        ),
        ModuleSpec(
            "control_logic",
            "control_path",
            "/data1/qujh/My_OpenYield/LiteRAM-Layout/literam/modules/control_logic.py; sram_layoutgen/openyield_adapter/control_decomposition.py",
            None,
            "outputs/openyield_module_gds/CONTROL_LOGIC/CONTROL_LOGIC.gds",
            "outputs/openyield_module_gds/CONTROL_LOGIC/pins.json",
            [
                "docs/M12C2_control_logic_physical_library_qualification_report.json",
                "docs/openyield_time_control_placement_readiness_report.json",
                "outputs/openyield_module_gds/CONTROL_LOGIC/generator_manifest.json",
            ],
            [
                "M12C2 says can_claim_control_logic_physical_ready=false",
                "CONTROL_LOGIC generator manifest says candidate geometry does not claim final routing or signoff",
                "time/control placement readiness report marks control subblocks physical_ready=false",
            ],
            False,
            "required",
            "The source decomposition exists, but the physical top-use control asset is not ready.",
        ),
        ModuleSpec(
            "DFF",
            "control_path",
            "/data1/qujh/My_OpenYield/LiteRAM-Layout/literam/modules/dff.py; sram_layoutgen/openyield_adapter/dff_net_contract_builder.py",
            "technology/freepdk45/sp_lib/dff.sp",
            "outputs/M12C4ACH_dff_reusable_release/DFF_reusable_clean.gds",
            "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/DFF_TG4_INV7_FPDK45_26d9543b82b7/DFF_TG4_INV7_FPDK45_26d9543b82b7_pin_map.json",
            [
                "docs/M12C4AC_dff_connectivity_repair_report.json",
                "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_drc_report.json",
                "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_dff_physical_connectivity_report.json",
            ],
            [],
            True,
            "subblock_leaf",
            "Reusable DFF evidence exists, but DFF arrays still need top-level placement/routing authority.",
        ),
        ModuleSpec(
            "DFF_BUF",
            "control_path",
            "sram_layoutgen/openyield_adapter/dff_buf_composite_generator.py; /data1/qujh/My_OpenYield/LiteRAM-Layout/literam/modules/dff_buf.py",
            None,
            "outputs/Wave3_DFF_BUF_reusable_release/DFF_BUF_reusable_clean.gds",
            "outputs/Wave3_DFF_BUF_reusable_release/DFF_BUF_REUSABLE_MANIFEST.json",
            [
                "outputs/Wave3H1_DFF_BUF_release_evidence_hardening/current_supported_config/package_root/drc/DFF_BUF_reusable_clean.lyrdb",
                "outputs/Wave3_DFF_BUF_reusable_release/DFF_BUF_REUSABLE_RELEASE_CHECKS.json",
                "docs/Wave3_DFF_BUF_hierarchical_short_negative_tests.json",
            ],
            [],
            True,
            "subblock_leaf_or_wrapper",
            "Reusable DFF_BUF exists; exact top usage is still governed by TIME/control authority.",
        ),
        ModuleSpec(
            "delay_chain",
            "control_path",
            "/data1/qujh/My_OpenYield/LiteRAM-Layout/literam/modules/delay_chain.py; sram_layoutgen/openyield_adapter/delay_chain_generator.py",
            "simulation/spice/netlists/delay_chain.inc",
            "outputs/openyield_module_gds/DELAY_CHAIN/DELAY_CHAIN.gds",
            "outputs/openyield_module_gds/DELAY_CHAIN/pins.json",
            [
                "docs/DELAY_CHAIN_SPICE_VALIDATION_REPORT.json",
                "outputs/openyield_module_gds/DELAY_CHAIN/generator_manifest.json",
                "docs/openyield_time_control_placement_readiness_report.json",
            ],
            [
                "DELAY_CHAIN module manifest says candidate geometry does not claim final routing or signoff",
                "time/control placement readiness marks DELAY_CHAIN_CLUSTER physical_ready=false",
                "no standalone final-GDS connectivity/foreign-net/negative-suite top-use gate found for delay_chain_v2",
            ],
            False,
            "required_if_TIME_uses_delay",
            "SPICE proxy evidence exists; physical top-use asset is not closed.",
        ),
        ModuleSpec(
            "pdrive",
            "control_path",
            "/data1/qujh/My_OpenYield/LiteRAM-Layout/literam/modules/pdriver.py; sram_layoutgen/openyield_adapter/control_decomposition.py",
            "simulation/spice/netlists/pdrive.inc",
            None,
            None,
            [
                "simulation/spice/testbenches/pdrive_buffer.sp",
                "docs/openyield_time_control_placement_readiness_report.json",
            ],
            [
                "no pdrive_v2 GDS asset found in repo, evidence package, /data1 search, historical worktrees, or checkpoints",
                "no pdrive pin map, DRC, connectivity, power endpoint, pin-access, determinism, or negative-suite evidence found",
            ],
            False,
            "required_by_TIME_metadata",
            "Missing physical asset blocks control path integration.",
        ),
        ModuleSpec(
            "wl_pdrive",
            "control_path",
            "/data1/qujh/My_OpenYield/LiteRAM-Layout/literam/modules/pdriver.py; sram_layoutgen/openyield_adapter/control_decomposition.py",
            "simulation/spice/netlists/wl_pdrive.inc",
            None,
            None,
            [
                "simulation/spice/testbenches/wl_pdrive_buffer.sp",
                "docs/openyield_time_control_placement_readiness_report.json",
            ],
            [
                "no wl_pdrive_v2 GDS asset found in repo, evidence package, /data1 search, historical worktrees, or checkpoints",
                "no wl_pdrive pin map, DRC, connectivity, power endpoint, pin-access, determinism, or negative-suite evidence found",
            ],
            False,
            "required_by_WORDLINE_ENABLE_metadata",
            "Missing physical asset blocks control path integration.",
        ),
        ModuleSpec(
            "pdrive2_for_pre",
            "control_path",
            "/data1/qujh/My_OpenYield/LiteRAM-Layout/literam/modules/pdriver.py; sram_layoutgen/openyield_adapter/control_decomposition.py",
            "simulation/spice/netlists/pdrive2_for_pre.inc",
            None,
            None,
            [
                "simulation/spice/testbenches/pdrive2_for_pre_buffer.sp",
                "docs/openyield_time_control_placement_readiness_report.json",
            ],
            [
                "no pdrive2_for_pre_v2 GDS asset found in repo, evidence package, /data1 search, historical worktrees, or checkpoints",
                "no pdrive2_for_pre pin map, DRC, connectivity, power endpoint, pin-access, determinism, or negative-suite evidence found",
            ],
            False,
            "required_by_PRE_metadata",
            "Missing physical asset blocks control path integration.",
        ),
        ModuleSpec(
            "top_level_input_output_interface",
            "top_interface",
            "sram_layoutgen/netlist_writer.py; docs/mapping/openyield_top_bank_semantic_contract.json",
            None,
            None,
            None,
            [
                "docs/WL_TIMING_AUTHORITY_REVIEW_PACKET.json",
                "docs/openyield_time_control_consumer_contract_report.json",
            ],
            [
                "no full 16x16 SRAM top pin physical contract exists for CLK/CSB/WEB/TIME/PRE/WL_EN/S_EN/W_EN/DIN/DOUT/BL/BR/RBL",
                "TIME_schedule, write_sample_point, disabled_hold_semantics, and WL timing budget remain owner-pending",
            ],
            False,
            "required",
            "Logical interface names are known, but complete top physical Pin authority is not ready.",
        ),
    ]


def readiness_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for spec in module_specs():
        gds = exists(spec.gds) if spec.gds else None
        pins = exists(spec.pin_source) if spec.pin_source else None
        spice = exists(spec.spice) if spec.spice else None
        logical_paths = [
            p.strip()
            for p in spec.logical_source.split(";")
            if p.strip() and not p.strip().startswith("/data1/")
        ]
        logical_existing = [exists(p) for p in logical_paths]
        logical_sha = ";".join(sha256(p) for p in logical_existing if p is not None) or "EXTERNAL_OR_NOT_FOUND"
        records.append(
            {
                "module_id": spec.module_id,
                "role": spec.role,
                "logical_source_path": spec.logical_source,
                "logical_source_sha": logical_sha,
                "spice_netlist_path": rel(spice),
                "spice_netlist_sha": sha256(spice),
                "gds_path": rel(gds),
                "gds_sha": sha256(gds),
                "top_cell": ";".join(top_cells_from_gds(gds)) or "NOT_FOUND",
                "pin_source": rel(pins),
                "pin_map_sha": sha256(pins),
                "power_pin": "VDD/VSS or vdd/gnd if pin source is present",
                "orientation_legality": "NOT_VERIFIED_FOR_FULL_TOP" if not spec.ready else "R0_EVIDENCE_AVAILABLE_TOP_USE_STILL_CONTEXTUAL",
                "drc_status": "NOT_TOP_ENTRY_CLOSED" if spec.blocker else "MODULE_EVIDENCE_AVAILABLE",
                "connectivity_status": "NOT_TOP_ENTRY_CLOSED" if spec.blocker else "MODULE_EVIDENCE_AVAILABLE",
                "foreign_net_status": "NOT_TOP_ENTRY_CLOSED" if spec.blocker else "MODULE_EVIDENCE_AVAILABLE",
                "pin_access_status": "NOT_TOP_ENTRY_CLOSED" if spec.blocker else "MODULE_EVIDENCE_AVAILABLE",
                "determinism_status": "NOT_TOP_ENTRY_CLOSED" if spec.blocker else "MODULE_EVIDENCE_AVAILABLE",
                "negative_suite_status": "NOT_TOP_ENTRY_CLOSED" if spec.blocker else "MODULE_EVIDENCE_AVAILABLE",
                "ready_for_top": spec.ready,
                "use_in_current_top": spec.use_in_current_top,
                "authority_note": spec.authority_note,
                "evidence": spec.evidence,
                "blocker": spec.blocker,
            }
        )
    return records


def top_contract() -> dict[str, Any]:
    nets: list[dict[str, Any]] = []
    for i in range(16):
        nets.append(net(f"WL{i}", "wordline", "P2_REAL_ARRAY_V1.decoder_row_path", f"WL_DRIVER[{i}].Z", "array", f"WL{i}", i, "CURRENT_SOURCE_EXACT", "closed in row-path package"))
        nets.append(net(f"BL{i}", "bitline", "array", f"BL{i}", "column_path", f"BL{i}", i, "AUTHORITY_PENDING", "column path module readiness failed"))
        nets.append(net(f"BR{i}", "bitline", "array", f"BR{i}", "column_path", f"BR{i}", i, "AUTHORITY_PENDING", "column path module readiness failed"))
        nets.append(net(f"DIN{i}", "data_write", "top_pin", f"DIN{i}", "write_driver", "DIN", i, "AUTHORITY_PENDING", "write path physical contract not closed"))
        nets.append(net(f"DOUT{i}", "data_read", "sense_amplifier", "Q", "top_pin", f"DOUT{i}", i, "AUTHORITY_PENDING", "read path physical contract not closed"))
    for name, sink, note in [
        ("PRE", "precharge.ENB", "active-low precharge enable metadata exists, physical handoff not closed"),
        ("WL_EN", "wl_driver.B", "row path local proof exists, full control-source proof pending"),
        ("S_EN", "sense_amplifier.EN", "consumer metadata exists, physical handoff not closed"),
        ("W_EN", "write_driver.EN", "consumer metadata exists, physical handoff not closed"),
        ("TIME", "control_logic", "schedule authority pending"),
        ("CLK", "DFF/DFF_BUF/control_logic", "clock distribution physical contract pending"),
        ("CSB", "control_logic", "control polarity metadata only"),
        ("WEB", "control_logic", "control polarity metadata only"),
        ("RBL", "array.replica_bitline", "array pin exists, upper column/control connection pending"),
    ]:
        nets.append(net(name, "control", "top_pin", name, sink, sink.split(".")[-1], None, "AUTHORITY_PENDING", note))
    return {
        "created_at": now(),
        "git_branch": git(["branch", "--show-current"]),
        "git_head": git(["rev-parse", "HEAD"]),
        "formal_config": {
            "num_rows": 16,
            "num_cols": 16,
            "word_size": 16,
            "words_per_row": 1,
            "bank_count": 1,
            "column_mux_required_by_locked_config": False,
            "column_mux_requirement_conflict": "USER_REQUEST_REQUIRES_COLUMN_MUX_BUT_LOCKED_WPR1_CONFIG_HAS_NO_MUX",
        },
        "functional_oracle": "FUNCTIONAL_ORACLE_PENDING_OWNER_REVIEW",
        "formal_timing_authority": "FORMAL_TIMING_AUTHORITY_PENDING",
        "row_path_status": "PASS_REAL_ARRAY_PHYSICAL_CLOSURE_PENDING_NARROW_WL_TIMING_AUTHORITY",
        "net_count": len(nets),
        "nets": nets,
    }


def net(
    net_name: str,
    net_class: str,
    source_instance: str,
    source_pin: str,
    destination_instance: str,
    destination_pin: str,
    bit_index: int | None,
    authority_level: str,
    note: str,
) -> dict[str, Any]:
    return {
        "net_name": net_name,
        "net_class": net_class,
        "source_instance": source_instance,
        "source_pin": source_pin,
        "destination_instance": destination_instance,
        "destination_pin": destination_pin,
        "bit_index": bit_index,
        "direction": "source_to_destination",
        "polarity": "see_authority_note",
        "timing_class": "critical" if net_class in {"wordline", "bitline", "control"} else "data",
        "differential_pair": "BL/BR" if net_name.startswith(("BL", "BR")) else "",
        "allowed_layer_class": "UNASSIGNED_FULL_TOP_PENDING",
        "must_be_matched": net_class == "bitline",
        "must_be_shielded": False,
        "authority_source": "row-path package, OpenYield source metadata, current formal config audit",
        "authority_level": authority_level,
        "note": note,
    }


def control_authority(records: list[dict[str, Any]]) -> dict[str, Any]:
    wanted = {"control_logic", "DFF", "DFF_BUF", "delay_chain", "pdrive", "wl_pdrive", "pdrive2_for_pre"}
    items = [r for r in records if r["module_id"] in wanted]
    return {
        "created_at": now(),
        "git_head": git(["rev-parse", "HEAD"]),
        "status": "CONTROL_PATH_PHYSICAL_ASSETS_NOT_READY",
        "can_generate_control_path_candidates": False,
        "reason": "Required TIME/control physical assets are missing or only metadata/candidate geometry.",
        "records": [
            {
                "module_id": r["module_id"],
                "logical_netlist_instantiated": r["use_in_current_top"],
                "top_visible_required": r["use_in_current_top"] != "subblock_leaf",
                "ready_for_top": r["ready_for_top"],
                "blocker": r["blocker"],
                "evidence": r["evidence"],
            }
            for r in items
        ],
    }


def entry_gate(records: list[dict[str, Any]], contract: dict[str, Any]) -> dict[str, Any]:
    missing_modules = [r["module_id"] for r in records if not r["ready_for_top"]]
    return {
        "created_at": now(),
        "gate": "FULL_SINGLE_BANK_SRAM_TOP_ENTRY_GATE",
        "status": "BLOCKED_BY_MISSING_FULL_SRAM_MODULE_ASSET",
        "can_enter_column_path_integration": False,
        "can_enter_control_path_integration": False,
        "can_enter_full_floorplan": False,
        "missing_or_unready_module_count": len(missing_modules),
        "missing_or_unready_modules": missing_modules,
        "formal_config": contract["formal_config"],
        "row_path_physical_closure": "PASS",
        "authoritative_array_locked": True,
        "real_array_integration": "PASS_ROW_PATH_ONLY",
        "functional_oracle": contract["functional_oracle"],
        "formal_timing_authority": contract["formal_timing_authority"],
        "search_scope_exhausted": [
            "current repository docs/outputs/source",
            "/data1/qujh/PAPER_EVIDENCE_PACKAGE_20260713_043712.tar.gz",
            "/data1/qujh/layoutgen_array_recovery/evidence_package",
            "/data1/qujh/My_OpenYield/LiteRAM-Layout",
            "/data1/qujh/work/github_exports",
            "git history on the current branch",
        ],
        "hard_stop_reason": "Top generation would require proxy/candidate control or column assets, which is prohibited by the current task.",
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines, ""]), encoding="utf-8")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = readiness_records()
    contract = top_contract()
    control = control_authority(records)
    gate = entry_gate(records, contract)

    readiness_payload = {
        "created_at": now(),
        "git_branch": git(["branch", "--show-current"]),
        "git_head": git(["rev-parse", "HEAD"]),
        "status": gate["status"],
        "records": records,
    }
    write_json(REPO / "docs/FULL_SRAM_MODULE_READINESS_AUDIT.json", readiness_payload)
    write_csv(
        REPO / "docs/FULL_SRAM_MODULE_READINESS_AUDIT.csv",
        records,
        [
            "module_id",
            "role",
            "logical_source_path",
            "logical_source_sha",
            "spice_netlist_path",
            "spice_netlist_sha",
            "gds_path",
            "gds_sha",
            "top_cell",
            "pin_source",
            "pin_map_sha",
            "power_pin",
            "orientation_legality",
            "drc_status",
            "connectivity_status",
            "foreign_net_status",
            "pin_access_status",
            "determinism_status",
            "negative_suite_status",
            "ready_for_top",
            "use_in_current_top",
            "authority_note",
            "blocker",
        ],
    )
    md_lines = [
        f"- status: `{gate['status']}`",
        f"- git head: `{git(['rev-parse', 'HEAD'])}`",
        f"- unready module count: `{gate['missing_or_unready_module_count']}`",
        "",
        "| module | role | ready_for_top | GDS | blocker |",
        "|---|---|---:|---|---|",
    ]
    for r in records:
        md_lines.append(
            f"| `{r['module_id']}` | `{r['role']}` | `{r['ready_for_top']}` | `{r['gds_path']}` | {'; '.join(r['blocker']) or '-'} |"
        )
    write_md(REPO / "docs/FULL_SRAM_MODULE_READINESS_AUDIT.md", "Full SRAM Module Readiness Audit", md_lines)

    write_json(REPO / "docs/FULL_SRAM_TOP_LOGICAL_CONTRACT.json", contract)
    write_csv(
        REPO / "docs/FULL_SRAM_TOP_CONNECTIVITY.csv",
        contract["nets"],
        [
            "net_name",
            "net_class",
            "source_instance",
            "source_pin",
            "destination_instance",
            "destination_pin",
            "bit_index",
            "direction",
            "polarity",
            "timing_class",
            "differential_pair",
            "allowed_layer_class",
            "must_be_matched",
            "must_be_shielded",
            "authority_source",
            "authority_level",
            "note",
        ],
    )
    write_csv(
        REPO / "docs/FULL_SRAM_TOP_PIN_CONTRACT.csv",
        [n for n in contract["nets"] if n["source_instance"] == "top_pin" or n["destination_instance"] == "top_pin"],
        [
            "net_name",
            "net_class",
            "source_instance",
            "source_pin",
            "destination_instance",
            "destination_pin",
            "bit_index",
            "authority_level",
            "note",
        ],
    )
    write_md(
        REPO / "docs/FULL_SRAM_TOP_LOGICAL_CONTRACT.md",
        "Full SRAM Top Logical Contract",
        [
            f"- status: `{gate['status']}`",
            "- row path: `CURRENT_SOURCE_EXACT` for WL0-WL15 through P2/P3 real-array closure",
            "- column path: `AUTHORITY_PENDING` until precharge/sense/write/column-mux top-entry assets close",
            "- control path: `AUTHORITY_PENDING` until TIME/control physical assets close",
            "- functional oracle: `FUNCTIONAL_ORACLE_PENDING_OWNER_REVIEW`",
            "- formal timing: `FORMAL_TIMING_AUTHORITY_PENDING`",
            f"- net records: `{contract['net_count']}`",
        ],
    )

    write_json(REPO / "docs/FULL_SRAM_CONTROL_PATH_AUTHORITY.json", control)
    write_md(
        REPO / "docs/FULL_SRAM_CONTROL_PATH_AUTHORITY.md",
        "Full SRAM Control Path Authority",
        [
            f"- status: `{control['status']}`",
            f"- can generate control path candidates: `{control['can_generate_control_path_candidates']}`",
            f"- reason: {control['reason']}",
            "",
            "| module | ready_for_top | blocker |",
            "|---|---:|---|",
            *[
                f"| `{r['module_id']}` | `{r['ready_for_top']}` | {'; '.join(r['blocker']) or '-'} |"
                for r in control["records"]
            ],
        ],
    )
    write_json(OUT / "FULL_SRAM_TOP_ENTRY_GATE.json", gate)
    write_md(
        OUT / "README_BLOCKED_BY_MODULE_READINESS.md",
        "Full SRAM Top Entry Blocked",
        [
            f"- status: `{gate['status']}`",
            "- no column/control/full-top GDS was generated in this pass",
            "- reason: required real module assets are missing or unqualified for top use",
            "- existing authoritative array and P2/P3 row-path outputs were not modified",
        ],
    )
    print(json.dumps(gate, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
