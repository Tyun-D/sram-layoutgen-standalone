"""Static OpenYield control/timing decomposition audit helpers.

This module stays read-only. It inspects OpenYield source files plus the local
contract bundle and emits a conservative decomposition graph for the TIME
control block and its direct consumers.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .macro_compat import load_contract_payload


@dataclass(frozen=True)
class ControlGraphNode:
    node_name: str
    node_type: str
    openyield_source: str
    role: str
    input_signals: tuple[str, ...]
    output_signals: tuple[str, ...]
    downstream_consumers: tuple[str, ...]
    candidate_local_macro: str | None
    candidate_local_gds: str | None
    candidate_local_spice: str | None
    mapping_status: str
    placement_feasibility: str
    source_contract_status: str
    source_file: str
    source_class: str
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ControlGraphEdge:
    source: str
    target: str
    relation: str
    signals: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        notes = self.notes
        if isinstance(notes, str):
            data["notes"] = [notes]
        else:
            data["notes"] = list(notes)
        return data


@dataclass(frozen=True)
class SignalAudit:
    signal_name: str
    source: str
    sinks: tuple[str, ...]
    status: str
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_time_control_decomposition_report(
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(openyield_root)
    contracts = load_contract_payload(contracts_path)
    contract_index = _build_contract_index(contracts.get("contracts", []))
    tech = Path(tech_dir) if tech_dir is not None else None

    source_files = {
        "TIME": root / "sram_compiler/subcircuits/time_generate.py",
        "DECODER": root / "sram_compiler/subcircuits/decoder.py",
        "TESTBENCH": root / "sram_compiler/testbenches/sram_6t_core_testbench.py",
    }
    source_health = {
        key: path.exists() for key, path in source_files.items()
    }

    nodes = _build_nodes(root, contract_index, tech)
    edges = _build_edges()
    signals = _build_signals()

    time_decomposition_success = bool(source_health["TIME"] and source_health["DECODER"] and source_health["TESTBENCH"])
    report = {
        "scope": "step6_1_time_control_decomposition_audit",
        "openyield_root": str(root.resolve()),
        "contracts_path": str(Path(contracts_path).resolve()),
        "tech_dir": str(Path(tech_dir).resolve()) if tech_dir is not None else None,
        "source_files": {key: str(path.resolve()) for key, path in source_files.items()},
        "source_health": source_health,
        "time_decomposition_success": time_decomposition_success,
        "time_as_single_macro_allowed": False,
        "can_enter_control_subblock_adapter_planning": time_decomposition_success,
        "can_enter_standalone_control_placement": False,
        "manual_source_review_required": False,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "signal_count": len(signals),
        "nodes": [node.to_dict() for node in nodes],
        "edges": [edge.to_dict() for edge in edges],
        "signal_audit": [signal.to_dict() for signal in signals],
        "signal_relationships": _signal_relationship_summary(),
        "source_coverage": _source_coverage_summary(source_files),
        "conclusions": {
            "time_decomposition_success": time_decomposition_success,
            "time_as_single_macro_allowed": False,
            "can_enter_control_subblock_adapter_planning": time_decomposition_success,
            "can_enter_standalone_control_placement": False,
            "manual_source_review_required": False,
        },
        "node_summary": _node_summary(nodes),
    }
    return report


def build_time_control_decomposition_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Time / Control Decomposition Audit",
        "",
        "This is a read-only source and contract audit. It does not change routing, placement, standalone.py, or the GDS writer.",
        "",
        "## Conclusions",
        "",
        f"- time decomposition success: `{report['time_decomposition_success']}`",
        f"- time as single macro allowed: `{report['time_as_single_macro_allowed']}`",
        f"- can enter control subblock adapter planning: `{report['can_enter_control_subblock_adapter_planning']}`",
        f"- can enter standalone control placement: `{report['can_enter_standalone_control_placement']}`",
        f"- manual source review required: `{report['manual_source_review_required']}`",
        "",
        "## Source Coverage",
        "",
        f"- TIME source present: `{report['source_health']['TIME']}`",
        f"- DECODER source present: `{report['source_health']['DECODER']}`",
        f"- TESTBENCH source present: `{report['source_health']['TESTBENCH']}`",
        "",
        "## Signal Audit",
        "",
        md_table(
            ["signal", "source", "sinks", "status", "notes"],
            [
                [
                    item["signal_name"],
                    item["source"],
                    ", ".join(item["sinks"]) or "-",
                    item["status"],
                    _notes_text(item["notes"]),
                ]
                for item in report["signal_audit"]
            ],
        ),
        "",
        "## Decomposition Nodes",
        "",
        md_table(
            [
                "node",
                "type",
                "source",
                "role",
                "inputs",
                "outputs",
                "consumers",
                "candidate macro",
                "local gds",
                "local spice",
                "mapping",
                "placement",
            ],
            [
                [
                    item["node_name"],
                    item["node_type"],
                    item["openyield_source"],
                    item["role"],
                    ", ".join(item["input_signals"]) or "-",
                    ", ".join(item["output_signals"]) or "-",
                    ", ".join(item["downstream_consumers"]) or "-",
                    item["candidate_local_macro"] or "-",
                    item["candidate_local_gds"] or "-",
                    item["candidate_local_spice"] or "-",
                    item["mapping_status"],
                    item["placement_feasibility"],
                ]
                for item in report["nodes"]
            ],
        ),
        "",
        "## Decomposition Edges",
        "",
        md_table(
            ["source", "target", "relation", "signals", "notes"],
            [
                [
                    item["source"],
                    item["target"],
                    item["relation"],
                    ", ".join(item["signals"]) or "-",
                    _notes_text(item["notes"]),
                ]
                for item in report["edges"]
            ],
        ),
        "",
        "## Notes",
        "",
        "- `TIME` is a composite control/timing block, not a single macro.",
        "- `ADDR_DFF` and `DATA_DFF` are hierarchical DFF arrays and should be treated as generated control subblocks.",
        "- `DFF` is the only direct hardcell leaf in this slice; the rest are logic/composite/control wrappers.",
        "- `output_enable` is not exposed as a standalone OpenYield net in the current source; the closest explicit control sink is `sense_enable` and the clock/data gating around `cs`/`cs_bar`.",
        "- `DECODER_CASCADE` remains hierarchical and should be planned as a decoder subblock, not a flat macro.",
        "",
    ]
    return "\n".join(lines)


def write_reports(
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path | None,
    out_json: str | Path,
    out_md: str | Path,
    out_graph_json: str | Path,
) -> dict[str, Any]:
    report = build_time_control_decomposition_report(openyield_root, contracts_path, tech_dir)
    graph = {
        "nodes": report["nodes"],
        "edges": report["edges"],
        "signal_audit": report["signal_audit"],
        "conclusions": report["conclusions"],
        "source_files": report["source_files"],
    }
    out_json = Path(out_json)
    out_md = Path(out_md)
    out_graph_json = Path(out_graph_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_graph_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(build_time_control_decomposition_markdown(report), encoding="utf-8")
    out_graph_json.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _build_contract_index(contracts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for contract in contracts:
        keys = {
            str(contract.get("original_module_name") or ""),
            str(contract.get("class_name") or ""),
            str(contract.get("canonical_module_name") or ""),
        }
        for key in keys:
            if key:
                index.setdefault(key, contract)
        original = str(contract.get("original_module_name") or "")
        if original.startswith("f'PINV") or original.startswith('f"PINV'):
            index.setdefault("Pinv", contract)
    return index


def _contract_lookup(contract_index: dict[str, dict[str, Any]], *keys: str) -> dict[str, Any] | None:
    for key in keys:
        if key in contract_index:
            return contract_index[key]
    return None


def _build_nodes(root: Path, contract_index: dict[str, dict[str, Any]], tech: Path | None) -> list[ControlGraphNode]:
    nodes: list[ControlGraphNode] = []
    for spec in _node_specs():
        contract = _contract_lookup(contract_index, spec["contract_key"], spec.get("class_name", ""), spec["node_name"])
        candidate_macro = spec.get("candidate_local_macro")
        if candidate_macro is None and contract:
            candidates = contract.get("gds_macro_candidates") or ()
            candidate_macro = str(candidates[0]) if candidates else None
        candidate_gds, candidate_spice = _local_macro_artifacts(tech, candidate_macro) if tech and candidate_macro else (None, None)
        if spec.get("preferred_local_file"):
            candidate_gds = _prefer_artifact(candidate_gds, tech, spec["preferred_local_file"])
            candidate_spice = _prefer_artifact(candidate_spice, tech, spec["preferred_local_file"].with_suffix(".sp") if spec["preferred_local_file"] else None)
        nodes.append(
            ControlGraphNode(
                node_name=spec["node_name"],
                node_type=spec["node_type"],
                openyield_source=spec["openyield_source"],
                role=spec["role"],
                input_signals=spec["input_signals"],
                output_signals=spec["output_signals"],
                downstream_consumers=spec["downstream_consumers"],
                candidate_local_macro=candidate_macro,
                candidate_local_gds=candidate_gds,
                candidate_local_spice=candidate_spice,
                mapping_status=spec["mapping_status"],
                placement_feasibility=spec["placement_feasibility"],
                source_contract_status=str(contract.get("implementation_status") or "unknown") if contract else "missing_contract",
                source_file=spec["source_file"],
                source_class=str(spec.get("source_class") or spec.get("class_name") or spec["node_name"]),
                notes=spec["notes"],
            )
        )
    return nodes


def _local_macro_artifacts(tech: Path, macro_name: str) -> tuple[str | None, str | None]:
    gds = _find_first(tech, "gds", macro_name)
    spice = _find_first(tech, "sp", macro_name)
    return gds, spice


def _prefer_artifact(existing: str | None, tech: Path | None, preferred: Path | None) -> str | None:
    if existing or tech is None or preferred is None:
        return existing
    candidate = tech / preferred
    return str(candidate.resolve()) if candidate.exists() else None


def _find_first(tech: Path, suffix: str, stem: str) -> str | None:
    matches = sorted(tech.glob(f"**/{stem}.{suffix}"))
    if not matches:
        return None
    return str(matches[0].resolve())


def _build_edges() -> list[ControlGraphEdge]:
    return [
        ControlGraphEdge("TIME", "ADDR_DFF", "controls", ("clk", "addr"), ("latches top-level address into addr_q.")),
        ControlGraphEdge("TIME", "DATA_DFF", "controls", ("clk", "din"), ("latches write data into din_q.")),
        ControlGraphEdge("TIME", "pdrive", "implements", ("clk",), ("clock buffer chain.")),
        ControlGraphEdge("TIME", "DFF_BUF", "uses", ("clk_buf", "addr", "din"), ("buffered flops in the control path.")),
        ControlGraphEdge("TIME", "DelayChain", "uses", ("rbl",), ("replica bitline delay chain.")),
        ControlGraphEdge("TIME", "WenDelayChain", "uses", ("rbl_delay_bar",), ("conditional write-enable delay path.")),
        ControlGraphEdge("TIME", "wl_pdrive", "implements", ("gated_clk_bar",), ("wordline enable buffer.")),
        ControlGraphEdge("TIME", "AND2", "implements", ("gated_clk_bar",), ("internal gate used in TIME.")),
        ControlGraphEdge("TIME", "AND3", "implements", ("we", "we_bar", "rbl_delay"), ("internal gate used in TIME.")),
        ControlGraphEdge("TIME", "PNAND3", "implements", ("pre_unbuf",), ("precharge gating NAND.")),
        ControlGraphEdge("ADDR_DFF", "DFF", "decomposes_into", ("A[*]", "CLK"), ("array of address flops built from a repeated DFF leaf.")),
        ControlGraphEdge("DATA_DFF", "DFF", "decomposes_into", ("DIN[*]", "CLK"), ("array of data flops built from a repeated DFF leaf.")),
        ControlGraphEdge("DFF_BUF", "DFF", "contains", ("D", "Q", "QB", "CLK"), ("buffered DFF wrapper.")),
        ControlGraphEdge("DFF_BUF", "Pinv", "contains", ("Q", "QB"), ("two output inverters after the DFF core.")),
        ControlGraphEdge("DelayChain", "Pinv", "repeats", ("in", "out"), ("nine-stage inverter delay chain with load taps.")),
        ControlGraphEdge("WenDelayChain", "Pinv", "repeats", ("in", "out"), ("configurable inverter delay chain.")),
        ControlGraphEdge("pdrive", "Pinv", "repeats", ("A", "Z"), ("four-stage inverter buffer chain.")),
        ControlGraphEdge("pdrive2_for_pre", "Pinv", "repeats", ("A", "Z"), ("two-stage precharge buffer chain.")),
        ControlGraphEdge("wl_pdrive", "Pinv", "repeats", ("A", "Z"), ("two-stage wordline buffer chain.")),
        ControlGraphEdge("AND2", "PNAND2", "contains", ("A", "B"), ("AND2 = PNAND2 + inverter.")),
        ControlGraphEdge("AND2", "Pinv", "contains", ("Z",), ("AND2 output inverter.")),
        ControlGraphEdge("AND3", "PNAND3", "contains", ("A", "B", "C"), ("AND3 = PNAND3 + inverter.")),
        ControlGraphEdge("AND3", "Pinv", "contains", ("Z",), ("AND3 output inverter.")),
        ControlGraphEdge("DECODER3_8", "Pinv", "contains", ("A0", "A1", "A2"), ("three input inverters for address decoding.")),
        ControlGraphEdge("DECODER3_8", "AND3", "contains", ("A0", "A1", "A2"), ("eight 3-input AND gates.")),
        ControlGraphEdge("DECODER3_8", "AND2", "contains", ("WL_pre", "EN"), ("eight enable AND gates.")),
        ControlGraphEdge("DECODER_CASCADE", "DECODER3_8", "repeats", ("A[*]", "WL[*]"), ("hierarchical decoder built from 3-to-8 stages.")),
        ControlGraphEdge("TIME", "PRECHARGE", "controls", ("PRE",), ("precharge enable.")),
        ControlGraphEdge("TIME", "SENSEAMP", "controls", ("s_en",), ("sense amp enable.")),
        ControlGraphEdge("TIME", "WRITEDRIVER", "controls", ("w_en",), ("write driver enable.")),
        ControlGraphEdge("TIME", "WORDLINEDRIVER", "controls", ("wl_en",), ("wordline driver enable domain.")),
        ControlGraphEdge("TIME", "COLUMNMUX*", "controls", ("column_select",), ("column select remains a separate read-path control.")),
        ControlGraphEdge("TIME", "DECODER_CASCADE", "feeds", ("A_q[*]",), ("latched address enters decoder cascade.")),
        ControlGraphEdge("ADDR_DFF", "DECODER_CASCADE", "feeds", ("addr_q[*]",), ("latched address bus.")),
        ControlGraphEdge("DATA_DFF", "WRITEDRIVER", "feeds", ("din_q[*]",), ("latched write data bus.")),
        ControlGraphEdge("SENSEAMP", "output_enable", "semantics", ("sense_enable",), ("OpenYield does not expose a literal output_enable net; sense_enable is the closest explicit control.")),
    ]


def _build_signals() -> list[SignalAudit]:
    return [
        SignalAudit(
            "clk",
            "external top-level input -> TIME.clk",
            ("TIME", "ADDR_DFF", "DATA_DFF", "DFF core clocking via clk_buf"),
            "explicit",
            ("TIME generates clk_buf/clk_bar from clk and fans out to DFF arrays.",),
        ),
        SignalAudit(
            "addr_latched",
            "TIME.ADDR_DFF.A_dff[*]",
            ("DECODER_CASCADE.A[*]",),
            "explicit",
            ("Latched address bus is the decoder input domain.",),
        ),
        SignalAudit(
            "data_latched",
            "TIME.DATA_DFF.DIN_dff[*]",
            ("WRITEDRIVER.DIN",),
            "explicit",
            ("Latched write data feeds the write driver.",),
        ),
        SignalAudit(
            "sense_enable",
            "TIME.s_en",
            ("SENSEAMP.EN",),
            "explicit",
            ("Sense amp enable is explicitly generated by TIME.",),
        ),
        SignalAudit(
            "write_enable",
            "TIME.w_en",
            ("WRITEDRIVER.EN",),
            "explicit",
            ("Write driver enable is explicitly generated by TIME.",),
        ),
        SignalAudit(
            "wordline_enable",
            "TIME.wl_en",
            ("WORDLINEDRIVER.B", "RWL AND2.B"),
            "explicit",
            ("Active-high wordline enable is produced by wl_pdrive.",),
        ),
        SignalAudit(
            "precharge_enb",
            "TIME.PRE",
            ("PRECHARGE.ENB",),
            "explicit",
            ("Active-low precharge enable feeds the precharge macro.",),
        ),
        SignalAudit(
            "column_select",
            "separate read-path select logic",
            ("COLUMNMUX*.SEL{i}",),
            "explicit_outside_time",
            ("Column select is not generated inside TIME; it is a separate read-path control signal.",),
        ),
        SignalAudit(
            "output_enable",
            "not a named OpenYield TIME net",
            ("SENSEAMP.EN", "TIME.cs/TIME.cs_bar gating"),
            "implicit",
            ("The closest explicit control is sense_enable; output_enable is handled implicitly through control gating.",),
        ),
    ]


def _signal_relationship_summary() -> dict[str, Any]:
    return {
        "addr_latched": {
            "source": "TIME.ADDR_DFF.A_dff[*]",
            "consumers": ["DECODER_CASCADE.A[*]"],
            "status": "explicit",
        },
        "data_latched": {
            "source": "TIME.DATA_DFF.DIN_dff[*]",
            "consumers": ["WRITEDRIVER.DIN"],
            "status": "explicit",
        },
        "sense_enable": {
            "source": "TIME.s_en",
            "consumers": ["SENSEAMP.EN"],
            "status": "explicit",
        },
        "write_enable": {
            "source": "TIME.w_en",
            "consumers": ["WRITEDRIVER.EN"],
            "status": "explicit",
        },
        "wordline_enable": {
            "source": "TIME.wl_en",
            "consumers": ["WORDLINEDRIVER.B", "RWL AND2.B"],
            "status": "explicit",
        },
        "precharge_enable": {
            "source": "TIME.PRE",
            "consumers": ["PRECHARGE.ENB"],
            "status": "explicit",
        },
        "column_select": {
            "source": "external read-path control",
            "consumers": ["COLUMNMUX*.SEL{i}"],
            "status": "explicit_outside_time",
        },
        "output_enable": {
            "source": "implicit via sense_enable and control gating",
            "consumers": ["SENSEAMP.EN"],
            "status": "implicit",
        },
    }


def _source_coverage_summary(source_files: dict[str, Path]) -> dict[str, Any]:
    return {key: {"path": str(path.resolve()), "present": path.exists()} for key, path in source_files.items()}


def _node_summary(nodes: list[ControlGraphNode]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for node in nodes:
        counts[node.mapping_status] = counts.get(node.mapping_status, 0) + 1
    return {
        "mapping_status_counts": dict(sorted(counts.items())),
        "direct_hardcells": [node.node_name for node in nodes if node.mapping_status == "direct_hardcell_available"],
        "composite_blocks": [node.node_name for node in nodes if node.mapping_status == "composite_required"],
        "logic_blocks": [node.node_name for node in nodes if node.mapping_status == "generated_logic_available"],
    }


def _node_specs() -> list[dict[str, Any]]:
    tech_root = "technology/freepdk45"
    return [
        {
            "node_name": "TIME",
            "node_type": "composite_control_block",
            "contract_key": "TIME",
            "class_name": "TIME",
            "openyield_source": "sram_compiler/subcircuits/time_generate.py::TIME",
            "role": "control_timing",
            "input_signals": ("clk", "csb", "web", "addr[*]", "din[*]", "rbl"),
            "output_signals": (
                "clk_buf",
                "clk_bar",
                "cs_bar",
                "cs",
                "we_bar",
                "we",
                "gated_clk_bar",
                "gated_clk_buf",
                "wl_en",
                "addr_q[*]",
                "din_q[*]",
                "rbl_delay",
                "rbl_delay_bar",
                "sense_enable",
                "write_enable",
                "precharge_enb",
            ),
            "downstream_consumers": ("ADDR_DFF", "DATA_DFF", "DECODER_CASCADE", "PRECHARGE", "SENSEAMP", "WRITEDRIVER", "WORDLINEDRIVER"),
            "candidate_local_macro": "control_logic_contract",
            "preferred_local_file": None,
            "mapping_status": "composite_required",
            "placement_feasibility": "not_placeable_as_single_macro",
            "source_file": "sram_compiler/subcircuits/time_generate.py",
            "notes": (
                "Composite control/timing module.",
                "Composed from DFF arrays, delay chains, inverter chains, and logic gates.",
                "Not a single flat physical macro.",
            ),
        },
        {
            "node_name": "ADDR_DFF",
            "node_type": "hierarchical_control_array",
            "contract_key": "ADDR_DFF",
            "class_name": "ADDR_DFF",
            "openyield_source": "sram_compiler/subcircuits/time_generate.py::ADDR_DFF",
            "role": "control_timing",
            "input_signals": ("CLK", "A[*]"),
            "output_signals": ("A_dff[*]",),
            "downstream_consumers": ("DECODER_CASCADE",),
            "candidate_local_macro": "dff",
            "preferred_local_file": Path("technology/freepdk45/gds_lib/dff.gds"),
            "mapping_status": "composite_required",
            "placement_feasibility": "row_based_generated_array",
            "source_file": "sram_compiler/subcircuits/time_generate.py",
            "notes": (
                "Address latch array built from repeated DFF leaf cells.",
                "Latched bus maps to decoder input, not to a single hard macro.",
            ),
        },
        {
            "node_name": "DATA_DFF",
            "node_type": "hierarchical_control_array",
            "contract_key": "DATA_DFF",
            "class_name": "DATA_DFF",
            "openyield_source": "sram_compiler/subcircuits/time_generate.py::DATA_DFF",
            "role": "control_timing",
            "input_signals": ("CLK", "DIN[*]"),
            "output_signals": ("DIN_dff[*]",),
            "downstream_consumers": ("WRITEDRIVER",),
            "candidate_local_macro": "dff",
            "preferred_local_file": Path("technology/freepdk45/gds_lib/dff.gds"),
            "mapping_status": "composite_required",
            "placement_feasibility": "row_based_generated_array",
            "source_file": "sram_compiler/subcircuits/time_generate.py",
            "notes": (
                "Data latch array built from repeated DFF leaf cells.",
                "Latched data bus feeds the write driver.",
            ),
        },
        {
            "node_name": "DFF",
            "node_type": "primitive_hardcell",
            "contract_key": "DFF",
            "class_name": "dff",
            "openyield_source": "sram_compiler/subcircuits/time_generate.py::dff",
            "role": "control_timing",
            "input_signals": ("D", "CLK"),
            "output_signals": ("Q",),
            "downstream_consumers": ("ADDR_DFF", "DATA_DFF", "DFF_BUF"),
            "candidate_local_macro": "dff",
            "preferred_local_file": Path("technology/freepdk45/gds_lib/dff.gds"),
            "mapping_status": "direct_hardcell_available",
            "placement_feasibility": "placeable_as_known_macro",
            "source_file": "sram_compiler/subcircuits/time_generate.py",
            "notes": (
                "Local GDS/SPICE leaf exists.",
                "Pin labels were previously audited as clk, D, Q, gnd, vdd.",
            ),
        },
        {
            "node_name": "DFF_BUF",
            "node_type": "hierarchical_buffered_flop",
            "contract_key": "DFF_BUF",
            "class_name": "DFF_BUF",
            "openyield_source": "sram_compiler/subcircuits/time_generate.py::DFF_BUF",
            "role": "support_cell",
            "input_signals": ("D", "CLK"),
            "output_signals": ("Q", "QB"),
            "downstream_consumers": ("ADDR_DFF", "DATA_DFF"),
            "candidate_local_macro": "generated_dff_buffer",
            "preferred_local_file": None,
            "mapping_status": "generated_logic_available",
            "placement_feasibility": "requires_generated_layout_or_stdcell_row",
            "source_file": "sram_compiler/subcircuits/time_generate.py",
            "notes": (
                "One DFF plus two output inverters.",
                "Acts as a buffered wrapper rather than a single hard macro.",
            ),
        },
        {
            "node_name": "delay_chain",
            "node_type": "delay_chain",
            "contract_key": "delay_chain",
            "class_name": "DelayChain",
            "openyield_source": "sram_compiler/subcircuits/time_generate.py::DelayChain",
            "role": "control_timing",
            "input_signals": ("in",),
            "output_signals": ("out",),
            "downstream_consumers": ("TIME.rbl_delay",),
            "candidate_local_macro": "generated_delay_chain",
            "preferred_local_file": None,
            "mapping_status": "generated_logic_available",
            "placement_feasibility": "requires_generated_layout_or_stdcell_row",
            "source_file": "sram_compiler/subcircuits/time_generate.py",
            "notes": (
                "Nine-stage inverter delay chain with load taps.",
                "Used to generate replica-bitline delay.",
            ),
        },
        {
            "node_name": "wen_delay_chain",
            "node_type": "delay_chain",
            "contract_key": "wen_delay_chain",
            "class_name": "WenDelayChain",
            "openyield_source": "sram_compiler/subcircuits/time_generate.py::WenDelayChain",
            "role": "control_timing",
            "input_signals": ("in",),
            "output_signals": ("out",),
            "downstream_consumers": ("TIME.w_en",),
            "candidate_local_macro": "generated_delay_chain",
            "preferred_local_file": None,
            "mapping_status": "generated_logic_available",
            "placement_feasibility": "requires_generated_layout_or_stdcell_row",
            "source_file": "sram_compiler/subcircuits/time_generate.py",
            "notes": (
                "Configurable inverter delay chain for write-enable timing.",
                "Only used in the narrow write timing path.",
            ),
        },
        {
            "node_name": "pdrive",
            "node_type": "buffer_chain",
            "contract_key": "pdrive",
            "class_name": "pdrive",
            "openyield_source": "sram_compiler/subcircuits/time_generate.py::pdrive",
            "role": "support_cell",
            "input_signals": ("A",),
            "output_signals": ("Z",),
            "downstream_consumers": ("TIME.clk_buf",),
            "candidate_local_macro": "generated_clock_buffer_chain",
            "preferred_local_file": None,
            "mapping_status": "generated_logic_available",
            "placement_feasibility": "requires_generated_layout_or_stdcell_row",
            "source_file": "sram_compiler/subcircuits/time_generate.py",
            "notes": (
                "Four-stage inverter buffer chain.",
                "Used for clock buffering before internal gating.",
            ),
        },
        {
            "node_name": "pdrive2_for_pre",
            "node_type": "buffer_chain",
            "contract_key": "pdrive2_for_pre",
            "class_name": "pdrive2_for_pre",
            "openyield_source": "sram_compiler/subcircuits/time_generate.py::pdrive2_for_pre",
            "role": "support_cell",
            "input_signals": ("A",),
            "output_signals": ("Z",),
            "downstream_consumers": ("TIME.PRE",),
            "candidate_local_macro": "generated_precharge_buffer_chain",
            "preferred_local_file": None,
            "mapping_status": "generated_logic_available",
            "placement_feasibility": "requires_generated_layout_or_stdcell_row",
            "source_file": "sram_compiler/subcircuits/time_generate.py",
            "notes": (
                "Two-stage inverter buffer chain.",
                "Drives precharge control.",
            ),
        },
        {
            "node_name": "wl_pdrive",
            "node_type": "buffer_chain",
            "contract_key": "wl_pdrive",
            "class_name": "wl_pdrive",
            "openyield_source": "sram_compiler/subcircuits/time_generate.py::wl_pdrive",
            "role": "support_cell",
            "input_signals": ("A",),
            "output_signals": ("Z",),
            "downstream_consumers": ("TIME.wl_en",),
            "candidate_local_macro": "generated_wordline_buffer_chain",
            "preferred_local_file": None,
            "mapping_status": "generated_logic_available",
            "placement_feasibility": "requires_generated_layout_or_stdcell_row",
            "source_file": "sram_compiler/subcircuits/time_generate.py",
            "notes": (
                "Two-stage inverter buffer chain for wordline enabling.",
                "OpenYield source and testbench confirm active-high semantics.",
            ),
        },
        {
            "node_name": "Pinv",
            "node_type": "primitive_standard_cell",
            "contract_key": "Pinv",
            "class_name": "Pinv",
            "openyield_source": "sram_compiler/subcircuits/standard_cell.py::Pinv",
            "role": "support_cell",
            "input_signals": ("A",),
            "output_signals": ("Z",),
            "downstream_consumers": ("DFF_BUF", "DelayChain", "WenDelayChain", "pdrive", "pdrive2_for_pre", "wl_pdrive", "AND2", "AND3", "DECODER3_8"),
            "candidate_local_macro": "stdcell_inverter",
            "preferred_local_file": None,
            "mapping_status": "generated_logic_available",
            "placement_feasibility": "stdcell_row_candidate",
            "source_file": "sram_compiler/subcircuits/standard_cell.py",
            "notes": (
                "Leaf inverter primitive used throughout control logic.",
                "No direct GDS leaf exists in the current tech bundle; it is a generated logic atom.",
            ),
        },
        {
            "node_name": "PNAND2",
            "node_type": "primitive_standard_cell",
            "contract_key": "PNAND2",
            "class_name": "PNAND2",
            "openyield_source": "sram_compiler/subcircuits/standard_cell.py::PNAND2",
            "role": "support_cell",
            "input_signals": ("A", "B"),
            "output_signals": ("Z",),
            "downstream_consumers": ("AND2", "DECODER3_8"),
            "candidate_local_macro": "stdcell_nand2",
            "preferred_local_file": None,
            "mapping_status": "generated_logic_available",
            "placement_feasibility": "stdcell_row_candidate",
            "source_file": "sram_compiler/subcircuits/standard_cell.py",
            "notes": ("Leaf NAND2 primitive.",),
        },
        {
            "node_name": "PNAND3",
            "node_type": "primitive_standard_cell",
            "contract_key": "PNAND3",
            "class_name": "PNAND3",
            "openyield_source": "sram_compiler/subcircuits/standard_cell.py::PNAND3",
            "role": "support_cell",
            "input_signals": ("A", "B", "C"),
            "output_signals": ("Z",),
            "downstream_consumers": ("AND3", "TIME"),
            "candidate_local_macro": "stdcell_nand3",
            "preferred_local_file": None,
            "mapping_status": "generated_logic_available",
            "placement_feasibility": "stdcell_row_candidate",
            "source_file": "sram_compiler/subcircuits/standard_cell.py",
            "notes": ("Leaf NAND3 primitive.",),
        },
        {
            "node_name": "AND2",
            "node_type": "composite_logic_gate",
            "contract_key": "AND2",
            "class_name": "AND2",
            "openyield_source": "sram_compiler/subcircuits/standard_cell.py::AND2",
            "role": "support_cell",
            "input_signals": ("A", "B"),
            "output_signals": ("Z",),
            "downstream_consumers": ("TIME", "DECODER3_8"),
            "candidate_local_macro": "stdcell_and2_chain",
            "preferred_local_file": None,
            "mapping_status": "generated_logic_available",
            "placement_feasibility": "stdcell_row_candidate",
            "source_file": "sram_compiler/subcircuits/standard_cell.py",
            "notes": ("PNAND2 followed by an inverter.",),
        },
        {
            "node_name": "AND3",
            "node_type": "composite_logic_gate",
            "contract_key": "AND3",
            "class_name": "AND3",
            "openyield_source": "sram_compiler/subcircuits/standard_cell.py::AND3",
            "role": "support_cell",
            "input_signals": ("A", "B", "C"),
            "output_signals": ("Z",),
            "downstream_consumers": ("TIME", "DECODER3_8"),
            "candidate_local_macro": "stdcell_and3_chain",
            "preferred_local_file": None,
            "mapping_status": "generated_logic_available",
            "placement_feasibility": "stdcell_row_candidate",
            "source_file": "sram_compiler/subcircuits/standard_cell.py",
            "notes": ("PNAND3 followed by an inverter.",),
        },
        {
            "node_name": "DECODER3_8",
            "node_type": "decoder_stage",
            "contract_key": "DECODER3_8",
            "class_name": "DECODER3_8",
            "openyield_source": "sram_compiler/subcircuits/decoder.py::DECODER3_8",
            "role": "decoder",
            "input_signals": ("EN", "A0", "A1", "A2"),
            "output_signals": ("WL0..WL7",),
            "downstream_consumers": ("DECODER_CASCADE",),
            "candidate_local_macro": "row_decoder",
            "preferred_local_file": None,
            "mapping_status": "composite_required",
            "placement_feasibility": "decoder_block_candidate",
            "source_file": "sram_compiler/subcircuits/decoder.py",
            "notes": (
                "Built from three input inverters plus eight AND3 and eight AND2 blocks.",
                "This is a decoder stage, not a single hard macro leaf.",
            ),
        },
        {
            "node_name": "DECODER_CASCADE",
            "node_type": "hierarchical_decoder",
            "contract_key": "DECODER_CASCADE",
            "class_name": "DECODER_CASCADE",
            "openyield_source": "sram_compiler/subcircuits/decoder.py::DECODER_CASCADE",
            "role": "decoder",
            "input_signals": ("A[*]",),
            "output_signals": ("WL[*]",),
            "downstream_consumers": ("ADDR_DFF",),
            "candidate_local_macro": "decoder_cascade_block",
            "preferred_local_file": None,
            "mapping_status": "composite_required",
            "placement_feasibility": "decoder_block_candidate",
            "source_file": "sram_compiler/subcircuits/decoder.py",
            "notes": (
                "Hierarchical cascade of decoder stages.",
                "Must be placed as a decoder subblock, not a single macro.",
            ),
        },
        {
            "node_name": "PRECHARGE",
            "node_type": "column_periphery_macro",
            "contract_key": "PRECHARGE",
            "class_name": "Precharge",
            "openyield_source": "sram_compiler/subcircuits/precharge_and_write_driver.py::Precharge",
            "role": "precharge",
            "input_signals": ("precharge_enb", "bl", "br"),
            "output_signals": ("bl", "br"),
            "downstream_consumers": ("time.PRE",),
            "candidate_local_macro": "gen_precharge",
            "preferred_local_file": None,
            "mapping_status": "macro_candidate",
            "placement_feasibility": "needs_gds_pin_audit",
            "source_file": "sram_compiler/subcircuits/precharge_and_write_driver.py",
            "notes": (
                "OpenYield uses ENB as active-low precharge enable.",
                "No local physical GDS leaf is bundled in the current tech directory.",
            ),
        },
        {
            "node_name": "SENSEAMP",
            "node_type": "column_periphery_macro",
            "contract_key": "SENSEAMP",
            "class_name": "SenseAmp",
            "openyield_source": "sram_compiler/subcircuits/mux_and_sa.py::SenseAmp",
            "role": "sense_amp",
            "input_signals": ("sense_enable", "bl", "br"),
            "output_signals": ("dout", "dout_b"),
            "downstream_consumers": ("readout",),
            "candidate_local_macro": "sense_amp",
            "preferred_local_file": Path("technology/freepdk45/gds_lib/sense_amp.gds"),
            "mapping_status": "direct_hardcell_available",
            "placement_feasibility": "placeable_as_known_macro",
            "source_file": "sram_compiler/subcircuits/mux_and_sa.py",
            "notes": (
                "Local GDS/SPICE leaf exists.",
                "Current architecture adapter keeps QB/dout_b as a dropped complementary output in the read path review.",
            ),
        },
        {
            "node_name": "WRITEDRIVER",
            "node_type": "column_periphery_macro",
            "contract_key": "WRITEDRIVER",
            "class_name": "WriteDriver",
            "openyield_source": "sram_compiler/subcircuits/precharge_and_write_driver.py::WriteDriver",
            "role": "write_driver",
            "input_signals": ("write_enable", "din", "bl", "br"),
            "output_signals": ("bl", "br"),
            "downstream_consumers": ("write_path",),
            "candidate_local_macro": "write_driver",
            "preferred_local_file": Path("technology/freepdk45/gds_lib/write_driver.gds"),
            "mapping_status": "direct_hardcell_available",
            "placement_feasibility": "placeable_as_known_macro",
            "source_file": "sram_compiler/subcircuits/precharge_and_write_driver.py",
            "notes": (
                "Local GDS/SPICE leaf exists.",
                "OpenYield mapping uses DIN -> din, EN -> write_enable, BL -> bl, BLB -> br.",
            ),
        },
        {
            "node_name": "WORDLINEDRIVER",
            "node_type": "row_periphery_macro",
            "contract_key": "WORDLINEDRIVER",
            "class_name": "WordlineDriver",
            "openyield_source": "sram_compiler/subcircuits/wordline_driver.py::WordlineDriver",
            "role": "wordline_driver",
            "input_signals": ("decoder_input", "wordline_enable"),
            "output_signals": ("wl",),
            "downstream_consumers": ("ROW_WL",),
            "candidate_local_macro": "gen_wl_driver",
            "preferred_local_file": None,
            "mapping_status": "macro_candidate",
            "placement_feasibility": "needs_gds_pin_audit",
            "source_file": "sram_compiler/subcircuits/wordline_driver.py",
            "notes": (
                "OpenYield source and testbench confirm A=decoder_input, B=wordline_enable, Z=wl.",
                "B is active-high.",
            ),
        },
        {
            "node_name": "COLUMNMUX*",
            "node_type": "column_periphery_macro",
            "contract_key": "COLUMNMUX*",
            "class_name": "ColumnMux",
            "openyield_source": "sram_compiler/subcircuits/mux_and_sa.py::ColumnMux",
            "role": "column_mux",
            "input_signals": ("column_select", "bl", "br"),
            "output_signals": ("mux_out", "mux_out_b"),
            "downstream_consumers": ("SENSEAMP",),
            "candidate_local_macro": "gen_col_mux",
            "preferred_local_file": None,
            "mapping_status": "macro_candidate",
            "placement_feasibility": "needs_gds_pin_audit",
            "source_file": "sram_compiler/subcircuits/mux_and_sa.py",
            "notes": (
                "Column select is a separate control signal, not generated by TIME.",
                "OpenYield adapter review keeps this as a read-path macro candidate, not a shared-rail block.",
            ),
        },
    ]


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def _notes_text(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, str):
        return value or "-"
    try:
        items = [str(item) for item in value if str(item)]
    except TypeError:
        return str(value)
    return "; ".join(items) if items else "-"
