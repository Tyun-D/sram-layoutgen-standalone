from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
OPENYIELD = Path("/data1/qujh/work/external/OpenYield")
DECODER_PY = OPENYIELD / "sram_compiler/subcircuits/decoder.py"
TB_PY = OPENYIELD / "sram_compiler/testbenches/sram_6t_core_testbench.py"
TOP_SP = REPO / "outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_16x16.sp"
DOCS = REPO / "docs"
COMMIT = "1c34428d8b913963c4971d093b1a7c2df97a2509"


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _decoder_contract() -> tuple[dict[str, Any], list[dict[str, str]]]:
    text = DECODER_PY.read_text(encoding="utf-8")
    module = ast.parse(text)
    decoder38 = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "DECODER3_8")
    cascade = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "DECODER_CASCADE")
    nodes = []
    for stmt in decoder38.body:
        if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "NODES" for t in stmt.targets):
            nodes = [elt.value for elt in stmt.value.elts]
            break
    combos: list[tuple[str, str, str]] = []
    for stmt in ast.walk(decoder38):
        if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "input_combinations" for t in stmt.targets):
            for elt in stmt.value.elts:
                combos.append(tuple(item.value for item in elt.elts))
    bit_rows: list[dict[str, str]] = []
    for idx, combo in enumerate(combos):
        bit_rows.append(
            {
                "logical_module": "DECODER3_8",
                "logical_port": f"WL{idx}",
                "bit_index": str(idx),
                "direction": "output",
                "parent_net": f"WL{idx}",
                "source_file": str(DECODER_PY),
                "source_line_or_ast_pointer": f"DECODER3_8.input_combinations[{idx}]",
                "source_commit": COMMIT,
                "predecode_expression": " & ".join(combo),
                "enabled_expression": f"({ ' & '.join(combo) }) & EN",
            }
        )
    payload = {
        "scope": "decoder_v2_logical_contract",
        "classification": "PROJECT_OWNED_REGENERATED_PHYSICAL_ASSET_INPUT_CONTRACT",
        "openyield_authority": {
            "repo_root": str(OPENYIELD),
            "commit": COMMIT,
            "source_file": str(DECODER_PY),
        },
        "decoder3_8": {
            "formal_port_order": nodes,
            "address_bit_direction": "A0/A1/A2 explicitly scalar, instantiated into cascade as address_nodes[2], address_nodes[1], address_nodes[0]",
            "enable_polarity": "active_high",
            "wordline_polarity": "active_high",
            "instance_structure": {
                "inv_count": 3,
                "and3_count": 8,
                "and2_enable_count": 8,
            },
            "predecode_outputs": [f"WL{i}_pre" for i in range(8)],
            "wordline_outputs": [f"WL{i}" for i in range(8)],
        },
        "decoder_cascade": {
            "class_name": "DECODER_CASCADE",
            "source_file": str(DECODER_PY),
            "source_line_or_ast_pointer": f"{cascade.name}",
            "topology": "cascade_of_decoder3_8_blocks",
            "enable_chain": "level0 enable_signal=VDD; later levels driven by prior level EN_* outputs",
            "address_binding": "for each 3-bit group, child A0<-address_nodes[2], A1<-address_nodes[1], A2<-address_nodes[0]",
            "output_naming": "last level outputs map to WL<row_index>; earlier levels map to EN_<level>_<decoder_idx>_<out_idx>",
        },
        "v2_child_targets": [
            {
                "module": "decoder_gate_cells_v2",
                "logical_role": "predecode_plus_enable_leaf_group",
                "ports": ["A0", "A1", "A2", "EN", "WL0_pre", "WL1_pre", "WL2_pre", "WL3_pre", "WL4_pre", "WL5_pre", "WL6_pre", "WL7_pre", "WL0", "WL1", "WL2", "WL3", "WL4", "WL5", "WL6", "WL7", "VDD", "VSS"],
            },
            {
                "module": "row_decoder_v2",
                "logical_role": "cascade_stage_decoder",
                "ports": ["A0", "A1", "A2", "EN", "WL0", "WL1", "WL2", "WL3", "WL4", "WL5", "WL6", "WL7", "VDD", "VSS"],
            },
            {
                "module": "wordline_decoder_v2",
                "logical_role": "row_decoder_to_wordline_handoff",
                "ports": ["A0", "A1", "A2", "EN", "DEC_WL0", "DEC_WL1", "DEC_WL2", "DEC_WL3", "DEC_WL4", "DEC_WL5", "DEC_WL6", "DEC_WL7", "VDD", "VSS"],
            },
        ],
    }
    return payload, bit_rows


def _top_interface_rows() -> list[dict[str, str]]:
    lines = TOP_SP.read_text(encoding="utf-8").splitlines()
    top_line = next(line for line in lines if line.startswith(".subckt OPENYIELD_SRAM_TOP_V1 "))
    parts = top_line.split()[2:]
    rows = []
    for index, pin in enumerate(parts):
        role = "signal"
        if pin in {"VDD", "VSS"}:
            role = "power"
        elif pin in {"clk", "csb", "web"}:
            role = "primary_control"
        elif pin.startswith("A"):
            role = "address"
        elif pin.startswith("DIN"):
            role = "write_data"
        elif pin.startswith("SA_Q") or pin.startswith("SA_QB"):
            role = "sense_output"
        rows.append({"index": str(index), "pin": pin, "role": role})
    return rows


def _timing_packet() -> tuple[str, dict[str, Any]]:
    questions_md = "\n".join(
        [
            "# SRAM Timing Authority Review Questions",
            "",
            "Only these three owner-review items remain for project-level functional closure.",
            "",
            "1. After `add_cs_startup_clamp`, when does the first valid functional cycle begin?",
            "   Candidate A: first cycle only after startup clamp release plus one full guard cycle.",
            "   Candidate B: first post-release low phase of `gated_clk_bar` is already functional.",
            "",
            "2. What is the reviewed top-level write success oracle?",
            "   Candidate A: write completes when internal cell `Q/QB` settles, but top-level debug must infer success through a later `SA_Q/SA_QB` readback.",
            "   Candidate B: there is an exported top-level proxy edge or window that can be frozen as the write sample point.",
            "",
            "3. Under disabled `csb/web` combinations, what observable top-level hold behavior is required?",
            "   Candidate A: preserve prior cell state and leave `SA_Q/SA_QB` unchanged until a later selected read.",
            "   Candidate B: preserve state internally, but `SA_Q/SA_QB` may legally float or refresh due to analog front-end behavior.",
            "",
        ]
    ) + "\n"
    packet = {
        "scope": "sram_timing_authority_review_packet",
        "classification": "NARROW_OWNER_REVIEW_REQUIRED",
        "source_commit": COMMIT,
        "current_top_interface": _top_interface_rows(),
        "unresolved_fields": [
            {
                "field": "TIME_schedule",
                "source_gap": "startup clamp release overlaps first candidate functional cycle; exact valid-cycle boundary is not frozen by current exact-source text",
                "sources": [
                    str(TB_PY),
                    "Sram6TCoreTestbench.add_cs_startup_clamp",
                    str(TOP_SP),
                    "TIME subckt and XTIME instantiation",
                ],
            },
            {
                "field": "write_sample_point",
                "source_gap": "upstream write proof targets internal Q/QB, but current top exports SA_Q/SA_QB only",
                "sources": [
                    str(TB_PY),
                    str(TOP_SP),
                ],
            },
            {
                "field": "disabled_hold_semantics",
                "source_gap": "upstream evidence is single-cell hold/SNM oriented rather than top-level transient oracle",
                "sources": [
                    str(TB_PY),
                    str(TOP_SP),
                ],
            },
        ],
        "exploratory_tb_policy": {
            "classification": "PROJECT_EXPLORATORY_TB",
            "claim_allowed": "engineering_debug_only",
            "guard_cycle_rule": "avoid startup-clamp overlap and begin operations only after one explicit guard cycle",
            "readback_rule": "judge writes only through later SA_Q/SA_QB readback, not through internal cell nodes",
            "disabled_hold_rule": "observe but do not claim final pass/fail without owner confirmation",
        },
    }
    return questions_md, packet


def main() -> None:
    decoder_payload, bit_rows = _decoder_contract()
    _write_json(DOCS / "DECODER_V2_LOGICAL_CONTRACT.json", decoder_payload)
    md_lines = [
        "# Decoder V2 Logical Contract",
        "",
        f"- source_commit: `{COMMIT}`",
        f"- source_file: `{DECODER_PY}`",
        f"- decoder3_8 formal_port_order: `{decoder_payload['decoder3_8']['formal_port_order']}`",
        f"- enable_polarity: `{decoder_payload['decoder3_8']['enable_polarity']}`",
        f"- wordline_polarity: `{decoder_payload['decoder3_8']['wordline_polarity']}`",
        "",
        "## Bit Mapping",
        "",
    ]
    for row in bit_rows:
        md_lines.append(f"- `{row['logical_port']}`: `{row['enabled_expression']}`")
    md_lines.append("")
    (DOCS / "DECODER_V2_LOGICAL_CONTRACT.md").write_text("\n".join(md_lines), encoding="utf-8")
    with (DOCS / "DECODER_V2_BIT_MAPPING.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(bit_rows[0].keys()))
        writer.writeheader()
        writer.writerows(bit_rows)

    review_md, review_packet = _timing_packet()
    (DOCS / "SRAM_TIMING_AUTHORITY_REVIEW_QUESTIONS.md").write_text(review_md, encoding="utf-8")
    _write_json(DOCS / "SRAM_TIMING_AUTHORITY_REVIEW_PACKET.json", review_packet)


if __name__ == "__main__":
    main()
